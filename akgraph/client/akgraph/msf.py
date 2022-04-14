#!/usr/bin/env python3
"""Algorithm for calculating a minimum spanning forest on graphs."""
__all__ = ["msf_boruvka"]


from typing import Optional, Tuple

import arkouda as ak

from akgraph.util import maximum, minimum, remove_duplicates


def msf_boruvka(
    V: ak.pdarray,
    U: ak.pdarray,
    W: ak.pdarray,
    verbose: bool = False
) -> Tuple[ak.pdarray]:
    """
    Calculate the minimum spanning forest of a weighted, undirected graph.

    Edges must be symmetric (v, u, w) <==> (u, v, w).

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : ak.pdarray
        edge weights
    verbose : bool (default False)
        print progress

    Returns
    -------
    c : ak.pdarray[int64]
        connected component of each node
    vF : ak.pdarray[int64]
        out nodes of MSF
    uF : ak.pdarray[int64]
        in nodes of MSF
    wF : ak.pdarray[int64]
        edge weights of MSF

    Notes
    -----
    Based vaguely on Boruvka's algorithm. 
    """
    n, m, inf = V.max() + 1, V.size, 2 * W.max()
    if not V.is_sorted():
        pi = ak.argsort(V)
        V, U, W = V[pi], U[pi], W[pi]
    g = ak.GroupBy(U, assume_sorted=False)

    # Initialize the forest F
    c = ak.arange(n)         # components
    d = ak.arange(n)         # next components
    F = ak.zeros(m, 'bool')  # edges in forest

    k = 0
    while True:
        k += 1

        # Find edges between different components
        cV = g.broadcast(c, permute=False)
        cU = cV[g.permutation]
        active_edge = (cV != cU)
        m_active = active_edge.sum()        

        # terminate if there's no remaining edges between forests
        if m_active == 0: break

        # Find minimum weight edge from each component
        gcU = ak.GroupBy(cU)
        W_active = W * active_edge + inf * (~active_edge)
        node, idx_nbr = gcU.argmin(W_active)
        w_nbr = W_active[idx_nbr]
        d[node] = cV[idx_nbr] # this attaches the root to it's neighbor

        # add valid edges to the forest
        # valid edges have weight < inf
        valid = (w_nbr < inf)
        F[idx_nbr] = valid

        # connect components
        valid = (d != c)
        d = d * valid + c * (~valid)
        c_max, c_min = maximum(c, d), minimum(c, d)
        gc_max = ak.GroupBy(c_max)
        _, comps = gc_max.min(c_min)
        d = gc_max.broadcast(comps, permute=True)

        # "pointer jump"
        while ak.any(c != d):
            d, c = d[d], d

        if verbose:
            print(f'   k = {k}\n'
                  f' |E| = {m_active}\n')

    # remove "return" edges
    vF, uF, wF = V[F], U[F], W[F]
    vF, uF = minimum(vF, uF), maximum(vF, uF)
    vF, uF, wF = remove_duplicates(vF, uF, wF)

    return c, vF, uF, wF


if __name__ == '__main__':
    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Minimum Spanning Forest ====')
    V = ak.array([0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 3,
                  3, 4, 4, 4, 4, 4, 5, 5, 5, 6, 6])
    U = ak.array([1, 3, 0, 2, 3, 4, 1, 4, 0, 1, 4,
                  5, 1, 2, 3, 5, 6, 3, 4, 6, 4, 5])
    W = ak.array([7, 5, 7, 8, 9, 7, 8, 5, 5, 9, 15,
                  6, 7, 5, 15, 8, 9, 6, 8, 11, 9, 11])
    c, vF, uF, wF = msf_boruvka(V, U, W)
    assert ak.all(c == 0)
    assert ak.all(vF == ak.array([0, 0, 1, 2, 3, 4]))
    assert ak.all(uF == ak.array([1, 3, 4, 4, 5, 6]))
    assert ak.all(wF == ak.array([7, 5, 7, 5, 6, 9]))    

    print('##############')
    print('# YOU PASSED #')
    print('##############')
