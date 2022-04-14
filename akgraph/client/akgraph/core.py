#!/usr/bin/env python3
"""Algorithms for finding dense subgraphs.

Edges must be symmetric (u, v) <==> (v, u).

TODOS
-----
- These are naive implementations. I believe a better implementation of Core
  number is possible. See https://arxiv.org/pdf/1103.5320 for inspiration (or
  just google distributed k-core).
- These take a few minutes on reasonable (> 1 billion) edge graphs. The work for
  core_number is just too much.
"""
__all__ = ['k_core', 'k_core_decomp', 'core_number']


from typing import Optional, Tuple
from warnings import warn

import arkouda as ak

from akgraph.util.general import minimum


def k_core(
    V: ak.pdarray,
    U: ak.pdarray,
    k: int,
    verbose: bool = False
) -> ak.pdarray:
    """
    Returns the k-core of a graph.

    A k-core is a maximal subgraph that contains nodes of degree k or more.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    k : int
        order of the core (must be greater than one)
    verbose : bool (default False)
        display progress

    Returns
    -------
    core : ak.pdarray[bool]
        core[i] is True if node i in k-Core
    """
    # necessaries
    n = V.max() + 1
    g = ak.GroupBy(V)

    # intialize
    i = 0                        # iterator
    _, deg = g.count()           # node degree
    core = ak.ones(n, 'bool')    # nodes in the core

    while True:
        F = core & (deg < k)     # nodes to prune this round
        cardF = ak.sum(F)
        core[F] = False
        i += 1

        if verbose:
            print(f'   i = {i}\n'
                  f' |F| = {cardF:,}\n'
                  f' |K| = {ak.sum(core):,}\n')

        if cardF > 0:
            _, num_peeled_nbrs = g.sum(F[U])
            deg[F] = 0                       # peeled vertices get zero degree
            deg[~F] -= num_peeled_nbrs[~F]   # remaining vertices loose peeled neighbors
        else:
            break

    return core


def k_core_decomp(
    V: ak.pdarray,
    U: ak.pdarray,
    k_max: int = 0,
    verbose: bool = True
) -> Tuple[int, ak.pdarray]:
    """
    Return the maximal k-core of a graph.

    The maximal k-core is the k-core with the highest k value.

    Edges must be symmetric (u, v) <==> (v, u).

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    k_max : int
        maximum core value to consider
    verbose : bool (default False)
        display progress

    Returns
    -------
    i : int
        number of iterations
    k : int
        order of maximal core
    core : ak.pdarray[int64]
        core number of each vertex

    References
    ----------
    Scalable K-Core Decomposition for Static Graphs Using a Dynamic Graph Data
        Structure. Alok Tripathy, Fred Hohman, Duen Horng Chau, and Oded Green
        2018 IEEE International Conference on Big Data (2018) pp. 1135-1141
    """
    # necessaries
    n = V.max() + 1
    g = ak.GroupBy(V)

    # initializations
    i = 0                              # iterators
    k, num_active = 1, n               # core number, count of active nodes
    color = ak.zeros(n, dtype='bool')  # node has been examined
    _, deg = g.count()                 # node degree
    core = ak.ones_like(deg)           # core numbers ??

    while True:
        # Examine unseen vertices with small enough degree
        F = ~color & (deg <= k)
        cardF = ak.sum(F)
        color[F] = True
        num_active -= cardF
        i += 1

        if num_active == 0:
            break
        elif cardF > 0:
            _, num_peeled_nbrs = g.sum(F[U])
            deg[F] = 0                       # peeled vertices get zero degree
            deg[~F] -= num_peeled_nbrs[~F]   # remaining vertices loose peeled neighbors
        else:
            # mark core and move to a higer degree
            core[~color] += 1
            k += 1
            if k_max > 0 and k > k_max:
                break

        if verbose:
            if cardF:
                print('.', end='')
            else:
                print()
                print(f'          i = {i}\n'
                      f'          k = {k}\n'
                      f' num_active = {num_active}')

    if verbose: print()
    return (i, k, core)


def core_number(
    V: ak.pdarray,
    U: ak.pdarray,
    max_iter: int = 0,
    verbose: bool = False
) -> ak.pdarray:
    """
    WARNING: THIS DOESNT WORK.

    Return the core number for each node.

    The core number of a node is the largest value, k, of a k-core containing
    that node.  A k-core is a maximal subgraph that contains nodes of degree k
    or more.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    max_iter : int (default 0)
        maximum number of iterations to perform (default runs to completion)
    verbose : bool (default False)
        display progress

    Returns
    -------
    cores : ak.pdarray[int64]
        core number of each node

    References
    ----------
    An O(m) Algorithm for Cores Decomposition of Networks.
        Vladimir Batagelj, Matjaz Zaversnik. (2003)
        https://arxiv.org/pdf/cs/0310049.pdf

    Distributed k-Core Decomposition.
        Alberto Montresor, Francesco De Pellegrini and Daniel Miorandi.
        CoRR (2011) http://arxiv.org/pdf/1103.5320.pdf

    Notes
    -----
    Emprical study has shown that the a majority of graphs converge to their
    correct core number in a few tens of rounds. So running to completion may
    not be desirable in all circumstances.
    """
    warn("BE WARNED:\n"
         "core_number() is not exact.\n"
         "It is not accurate in all cases.\n"
         "It may underestimate the coreness of nodes.\n"
         "YOU HAVE BEEN WARNED.")

    # Make initial guess at core number
    # core(v) <= min(deg(v), max(deg(u) for u in N(v)))
    g = ak.GroupBy(V)
    _, degree = g.count()
    _, max_deg_nbr = g.max(degree[U])
    core = minimum(degree, max_deg_nbr)

    # determine number of ordered neighbors here or above
    degV = degree[V]
    nbr_idx = ak.arange(V.size) - g.broadcast(g.segments, permute=False)
    num_nbr_geq = degV - nbr_idx

    i, n_changed = core.size, False
    while n_changed > 0:
        prev_core = core
        prev_converged = converged

        # Update core numbers
        # find largest k(v) such that k or more neighbors have k(u) >= k
        coreU = core[U]
        pi = ak.coargsort([V, coreU])
        coreU = coreU[pi]
        valid = (num_nbr_geq >= coreU)
        coreU *= valid
        _, core = g.max(coreU)
        mask = (core == 0)      # all neighbors have higher core number
        core[mask] = prev_core[mask]

        converged = (prev_core == core)
        n_changed = ak.sum(~converd_nodes)
        i += 1

        if verbose:
            n_unconverged = ak.sum(prev_converged & ~converged)
            print(f'Complete round {i}:\n'
                  f'    {n_changed} core numbers changed\n'
                  f'    {n_unconverged} nodes changed after stabilizing')

    return core


if __name__ == '__main__':
    from akgraph.generators import path_graph, complete_graph, karate_club_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing k-Core ====')
    # path
    V, U = path_graph(10)
    core = k_core(V, U, 2)
    assert core.sum() == 0
    core = k_core(V, U, 1)
    assert core.sum() == 10

    # clique
    V, U = complete_graph(10)
    core = k_core(V, U, 9)
    assert core.sum() == 10
    core = k_core(V, U, 10)
    assert core.sum() == 0

    # karate
    n = 34
    _, V, U = karate_club_graph()
    core = k_core(V, U, 1)
    assert core.sum() == n
    core = k_core(V, U, 2)
    assert ak.all(core == ak.array([i != 11 for i in range(n)]))
    core = k_core(V, U, 3)
    assert ak.all(core == ak.array( [True, True, True, True, True, True, True,
                                     True, True, False, True, False, False,
                                     True, False, False, False, False, False,
                                     True, False, False, False, True, True,
                                     True, False, True, True, True, True, True,
                                     True, True] ))
    core = k_core(V, U, 4)
    assert ak.all(core == ak.array( [True, True, True, True, False, False,
                                     False, True, True, False, False, False,
                                     False, True, False, False, False, False,
                                     False, False, False, False, False, False,
                                     False, False, False, False, False, False,
                                     True, False, True, True] ))
    core = k_core(V, U, 5)
    assert core.sum() == 0

    print('==== Testing Core Numbers ====')
    cores = core_number(V, U)
    assert ak.all(cores == ak.array([4, 4, 4, 4, 3, 3, 3, 4, 4, 2, 3, 1, 2, 4,
                                     2, 2, 2, 2, 2, 3, 2, 2, 2, 3, 3, 3, 2, 3,
                                     3, 3, 4, 3, 4, 4]))

    print('##############')
    print('# YOU PASSED #')
    print('##############')
