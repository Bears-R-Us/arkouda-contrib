#!/usr/bin/env python3
"""Algorithms for determining connected components of graphs.

Edges must be symmetric (u, v) <==> (v, u).

TODOS
-----
- Allow user input 'seed' labels
- Create generic `concomp` method (maybe use fast_sv for a few iterations then
  seed that to bfs_lp_rs).
"""
__all__ = ["bfs_lp", "bfs_lp_rs", "fast_sv", "lps"]


from typing import Tuple, Union
from warnings import warn

import numpy as np

import arkouda as ak

from akgraph.util import get_perm, minimum


_WARN = ("Componenents likely incorrect.\n"
         "Try again with `max_steps=None` or a higher value.\n"
         "Or try a different algorithm.")


def bfs_lp(
    V: ak.pdarray,
    U: ak.pdarray,
    randomize: bool = False,
    shortcut: bool = False,
    max_steps: Union[None, int] = 100,
    verbose: bool = False
) -> Tuple[int, ak.pdarray]:
    """
    Calculate connected components of a graph.

    Uses a parallel breadth-first search and label propogation with
    optional randomization and shortcutting.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    randomized : bool (default False)
        start with randomly permuted labels on each node
    shortcut : bool (default False)
        perform a label propogation through known components at each step
    max_steps :  Union[int, None] (default 100)
        quit after this many steps
    verbose : bool (default False)
        print progress

    Returns
    -------
    k : int
        number of steps to converge
    c : ak.pdarray[int64]
        component label for each node
    """
    n = V.max() + 1
    if not V.is_sorted():
      pi = ak.argsort(V)
      V, U = V[pi], U[pi]

    g = ak.GroupBy(U, assume_sorted=False)
    c = get_perm(n) if randomize else ak.arange(n)
    c_prev = ak.zeros_like(c)

    k = 0
    converged, n_comps = False, c.size
    while not converged and n_comps > 1:
        k += 1
        if max_steps is not None and k > max_steps:
            warn(f"Exceeded max_steps={max_steps} iterations.\n" + _WARN)
            break

        c_prev[:] = c[:]

        cV = g.broadcast(c_prev, permute=False)
        cU = cV[g.permutation]
        C = minimum(cV, cU)
        _, c = g.min(C)

        if shortcut:
            gl = ak.GroupBy(c_prev)
            _, comp_labels = gl.min(c)
            c = gl.broadcast(comp_labels, permute=True)

        converged = (c == c_prev).all()
        n_comps = ak.unique(c).size

        if verbose:
            print(f'   k = {k}\n'
                  f' |C| = {ak.unique(c).size}\n')

    return (k, c)


def bfs_lp_rs(V: ak.pdarray, U: ak.pdarray, max_steps=100) -> Tuple[int, ak.pdarray]:
    """BFS connected components algorithm with randomization and shortcutting."""
    return bfs_lp(V, U, randomize=True, shortcut=True, max_steps=max_steps)


def fast_sv(
    V: ak.pdarray,
    U: ak.pdarray,
    max_steps: Union[int, None] = 100
) -> Tuple[int, ak.pdarray]:
    """
    Calculate connected components of a graph.

    Distributed Shiloach-Vishkin inspired algorithm.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    max_steps :  Union[int, None] (default 100)
        quit after this many steps

    Returns
    -------
    k : int
        number of steps to converge
    L : ak.pdarray[int64]
        component label for each node (minimal node in connected component)

    References
    ----------
    FastSV: a distributed-memory connected component algorithm with Fast
        convergenceYongzhe Zhang, Ariful Azad, Zhenjiang Hu. arXiv1910.05971v2
        (2020)

    Parallel algorithms for finding connected components using linear
        algebra. Yongzhe Zhang, Ariful Azad, Aydin Buluc.  Journal of Parallel
        and Distributed Computing, Volume 144, 2020, pp. 14-27.
    """
    n = ak.max(V) + 1
    nf, ng = ak.arange(n), ak.arange(n)
    f, g = ak.zeros_like(nf), ak.zeros_like(ng)

    if not V.is_sorted():
        pi = ak.argsort(V)
        V, U = V[pi], U[pi]

    gV = ak.GroupBy(V, assume_sorted=True)
    gU = ak.GroupBy(U, assume_sorted=False)

    k = 0
    converged, n_comps = False, nf.size
    while not converged and n_comps > 1:
        k += 1
        if max_steps is not None and k > max_steps:
            warn(f"Exceeded max_steps={max_steps} iterations.\n" + _WARN)
            break

        g[:] = ng[:]
        f[:] = nf[:]

        # hooking phase
        # f_k = A @ g using (Select2nd, min) semiring
        grand_U = gU.broadcast(g, permute=True)
        _, f_k = gV.min(grand_U)
        f[f] = f_k              # stochastic hooking
        f = minimum(f, f_k)     # aggressive hooking

        nf = minimum(f, g)      # shortcutting

        ng = nf[nf]             # calculate grandparents

        converged = (ng == g).all()
        n_comps = ak.unique(nf).size

    return (k, nf)


def lps(
    V: ak.pdarray,
    U: ak.pdarray,
    max_steps: Union[int, None] = 100
) -> Tuple[int, ak.pdarray]:
    """
    Calculate connected components of a graph.

    Label propagation + symmetrization algorithm.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    max_steps :  Union[int, None] (default 100)
        quit after this many steps

    Returns
    -------
    k : int
        number of steps to converge
    L : ak.pdarray[int64]
        component label for each node (minimal node in connected component)

    References
    ----------
    Graph connectivity in log steps using label propagation.
        Burkhardt, Paul. arXiv1808:06705v4 (2021)
    """
    perm = ak.argsort(V)
    X, Y = V[perm], U[perm]
    gy = ak.GroupBy(X, assume_sorted=True)
    lbl_nxt = minimum(*gy.min(Y))
    lbl_cur = ak.zeros_like(lbl_nxt)

    Y_nxt = ak.zeros_like(Y)
    X, Y, Y_nxt = Y_nxt, X, Y

    k = 0
    converged, n_comps = False, lbl_nxt.size
    while not converged and n_comps > 1:
        k += 1
        if max_steps is not None and k > max_steps:
            warn(f"Exceeded max_steps={max_steps} iterations.\n" + _WARN)
            break

        lbl_cur[:] = lbl_nxt[:]
        X, Y, Y_nxt = Y, Y_nxt, X
        gx, gy = gy, ak.GroupBy(Y)

        Lx = gx.broadcast(lbl_cur[gx.unique_keys], permute=True)
        Ly = gy.broadcast(lbl_cur[gy.unique_keys], permute=True)

        Y_nxt[:] = X[:]                            # Symmetrization
        prop_mask = Y != Lx                        # Label Propagation
        Y_nxt[prop_mask] = Lx[prop_mask]           # Label Propagation
        Ly[prop_mask] = minimum(Lx, Ly)[prop_mask] # Label Propagation

        y, ly = gy.min(Ly)
        lbl_nxt[y] = ly

        converged = (lbl_nxt == lbl_cur).all()
        n_comps = ak.unique(lbl_nxt).size

    return (k, lbl_nxt)


if __name__ == '__main__':
    from akgraph.generators import path_graph, complete_graph, karate_club_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    n = 5
    pV, pU = path_graph(n)
    cV, cU = complete_graph(n)
    pcV, pcU = (ak.concatenate([pV, cV + n], ordered=False),
                ak.concatenate([pU, cU + n], ordered=False))
    pcC = ak.array([0] * n + [n] * n)
    comms, kV, kU = karate_club_graph()
    kC = ak.zeros_like(comms)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing BFS+LP Algorithm ====')
    _, C = bfs_lp(pcV, pcU)
    assert ak.all(C == pcC)
    _, C = bfs_lp(kV, kU)
    assert ak.all(C == kC)

    print('==== Testing FastSV Algorithm ====')
    _, C = fast_sv(pcV, pcU)
    assert ak.all(C == pcC)
    _, C = fast_sv(kV, kU)
    assert ak.all(C == kC)

    print('==== Testing LPS Algorithm ====')
    _, C = lps(pcV, pcU)
    assert ak.all(C == pcC)
    _, C = lps(kV, kU)
    assert ak.all(C == kC)

    print('##############')
    print('# YOU PASSED #')
    print('##############')
