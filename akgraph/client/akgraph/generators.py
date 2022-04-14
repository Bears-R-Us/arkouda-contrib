#!/usr/bin/env python3
"""Algorithms to create (random) graphs."""
__all__ = [
    "complete_graph",
    "gnp",
    "karate_club_graph",
    "random_tree",
    "rmat",
    "path_graph",
    "watts_strogatz_graph"
]


from typing import Tuple, Union

import numpy as np

import arkouda as ak

from akgraph.util import get_perm, sort_edges, standardize_edges


def complete_graph(n: int) -> Tuple[ak.pdarray]:
    """
    Generate the complete graph on n nodes.

    Parameters
    ----------
    n : int
      number of nodes

    Returns
    -------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    """
    V = ak.broadcast(ak.arange(0, n * n, n), ak.arange(n), n * n)
    U = ak.arange(V.size) % n

    return standardize_edges(V, U)


def gnp(n: int, p: float) -> Tuple[ak.pdarray]:
    """
    Generate a random binomial graph.

    Also known as an  Erdos-Renyi or completely random graph.

    Strip out isolates, self-loops and duplicate edges so n_out <= n.

    Parameters
    ----------
    n : int
        number of nodes
    p : float in [0, 1]
        probability of edge formation

    Returns
    -------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    """
    m = np.random.binomial(n * (n - 1) // 2, p)  # determine number of edges
    V, U = ak.randint(0, n, m), ak.randint(0, n, m)  # random pairs of nodes

    return standardize_edges(V, U)


def karate_club_graph() -> Tuple[ak.pdarray]:
    """
    Return's Zachary's Karate Club Graph

    Each node of the 34 nodes is labelled with a ground truth community.

    Returns
    -------
    C : ak.pdarray[int64] (34 elements)
        community label
    V : ak.pdarray[int64] (156 elements)
        out nodes
    U : ak.pdarray[int64] (156 elements)
        in nodes

    References
    ----------
    An Information Flow Model for Conflict and Fission in Small Groups.
        Wayne W. Zachary. Journal of Anthropological Research, 33, 452-473
        (1977)
    """
    C = ak.array([ 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1,
                   0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ])
    V = ak.array([ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
                   1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3,
                   3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8,
                   8, 9, 9, 10, 10, 10, 11, 12, 12, 13, 13, 13, 13, 13, 14, 14,
                   15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 19, 20, 20, 21, 21,
                   22, 22, 23, 23, 23, 23, 23, 24, 24, 24, 25, 25, 25, 26, 26,
                   27, 27, 27, 27, 28, 28, 28, 29, 29, 29, 29, 30, 30, 30, 30,
                   31, 31, 31, 31, 31, 31, 32, 32, 32, 32, 32, 32, 32, 32, 32,
                   32, 32, 32, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33, 33,
                   33, 33, 33, 33, 33 ])
    U = ak.array([ 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 17, 19, 21, 31, 0, 2,
                   3, 7, 13, 17, 19, 21, 30, 0, 1, 3, 7, 8, 9, 13, 27, 28, 32,
                   0, 1, 2, 7, 12, 13, 0, 6, 10, 0, 6, 10, 16, 0, 4, 5, 16, 0,
                   1, 2, 3, 0, 2, 30, 32, 33, 2, 33, 0, 4, 5, 0, 0, 3, 0, 1, 2,
                   3, 33, 32, 33, 32, 33, 5, 6, 0, 1, 32, 33, 0, 1, 33, 32, 33,
                   0, 1, 32, 33, 25, 27, 29, 32, 33, 25, 27, 31, 23, 24, 31, 29,
                   33, 2, 23, 24, 33, 2, 31, 33, 23, 26, 32, 33, 1, 8, 32, 33,
                   0, 24, 25, 28, 32, 33, 2, 8, 14, 15, 18, 20, 22, 23, 29, 30,
                   31, 33, 8, 9, 13, 14, 15, 18, 19, 20, 22, 23, 26, 27, 28, 29,
                   30, 31, 32 ])
    return (C, V, U)


def random_tree(n: int) -> Tuple[ak.pdarray]:
    """
    Generate a random tree.

    Parameters
    ----------
    n : int
        number of nodes

    Returns
    -------
    V : ak.pdarray[int64] (2 * n elements)
        out nodes
    U : ak.pdarray[int64] (2 * n elements)
        in nodes
    """
    V = ak.arange(n)
    U = ak.randint(0, n, n)
    U = U % V

    return standardize_edges(V, U)


def rmat(
    scale: int,
    edge_factor: int = 16,
    p: Union[float, Tuple[float]] = (0.57, 0.19, 0.19, 0.05),
    weighted: bool = False,
    permute: bool = True,
    standardize: bool = True
) -> Tuple[ak.pdarray]:
    """
    Recursive MATrix random graph generator.

    Parameters
    ----------
    scale : int
        number of nodes = 2 ** scale
    edge_factor : int
        each node has this many edges
    p : { float | Tuple[float] }
        link-formation probabilites. Single float interpreted as upper-left
        quadrant probability with other quadrants equally sharing the
        complement. Tuples will be intepreted as (a, b, c, d) as described in
        the reference. Defaults to specification from Graph500.
    weighted : bool (default False)
        output uniformly random weights in [0, 1] for each edge.
    permute : bool (default True)
        randomly relabel nodes and permute edges
    standardize : bool (default True)
        standardize edges afterwards

    Returns
    -------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : ak.pdarray[float64] (optional)
        edge weights

    References
    ----------
    R-MAT: A Recursive Model for Graph Mining.
        Deepayan Chakrabarti, Yiping Zhan and Christos Faloutsos.
        Proceedings of the Fourth SIAM International Conference on Data Mining.
        Apr 22-24 2004

    Notes
    -----
    Stolen brazenly from arkouda/toys/connected_components.py and the Graph500
    benchmark description.
    """
    n = 2 ** scale              # number nodes
    m = n * edge_factor         # number edges

    if isinstance(p, float) and 0 <= p <= 1:
        a = p
        b = c = d = (1.0 - p) / 3.0
    elif isinstance(p, tuple) and all(0 <= x <= 1 for x in p) and sum(p) == 1:
        a, b, c, d = p
    else:
        raise ValueError(f"p = {p} doesn't represent valid probability for RMAT.")
    ab, cNorm, aNorm = a + b, c / (c + d), a / (a + b)

    V, U = ak.zeros(m, dtype='int64'), ak.zeros(m, dtype='int64')
    for i in range(scale):
        vMask = ak.randint(0, 1, m, dtype='float64') > ab
        uMask = (ak.randint(0, 1, m, dtype='float64')
                 > (cNorm * vMask + aNorm * (~vMask)))
        V += vMask * (2 ** i)
        U += uMask * (2 ** i)

    if permute:
        # permute vertex labels
        pi = get_perm(n)
        V, U = pi[V], pi[U]

        # permute edges
        pi = get_perm(m)
        V, U = V[pi], U[pi]

    if weighted:
        W = ak.uniform(V.size)
        if standardize: V, U, W = standardize_edges(V, U, W)
        return V, U, W
    else:
        if standardize: V, U = standardize_edges(V, U)
        return (V, U)


def path_graph(n: int) -> Tuple[ak.pdarray]:
    """Generate the sequential path with n nodes on nodes [0..n-1]."""
    V = ak.arange(n - 1)
    U = V + 1
    V, U = (ak.concatenate([V, U], ordered=False),
            ak.concatenate([U, V], ordered=False))
    return sort_edges(V, U)


def watts_strogatz_graph(n: int, k: int, p: float) -> Tuple[ak.pdarray]:
    """
    Generate a small-world network on n nodes.

    Based on the Watts-Strogatz model.

    No self loops or duplicate edges allowed.

    This probably isn't exactly the same as the academic definition
    but it's fast in arkouda.

    Parameters
    ----------
    n : int
        number of nodes to create
    k : int
        average degree of the graph
    p : float
        probability to rewire edges

    Return
    ------
    ak.pdarray(s) :
        two m-long arrays holding source and destination nodes of each edge
    """
    # create initial sources
    V = ak.broadcast(ak.arange(0, n * k, k), ak.arange(n), n * k)

    # each source is connected to it's k closest neighbors (alphabetically)
    krange = ak.arange(-k // 2, k // 2)
    krange[k // 2 :] += 1
    idx = ak.arange(V.size) % krange.size
    U = krange[idx]
    U[U < 0] = U[U < 0] + n

    # pick some random subset of edges to alter
    changes = ak.randint(0, 1, U.size, dtype=ak.float64) < p
    n_changes = changes.sum()
    U[changes] = ak.randint(0, n, n_changes)

    return standardize_edges(V, U)


if __name__ == '__main__':
    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Complete Graph ====')
    V, U = complete_graph(9)
    assert V.size == U.size == 72
    gv = ak.GroupBy(V)
    _, deg = gv.count()
    assert ak.all(deg == 8)

    print('==== Testing Path Graph ====')
    V, U = path_graph(5)
    assert V.size == U.size == 8
    assert V.min() == U.min() == 0
    assert V.max() == U.max() == 4

    print('##############')
    print('# YOU PASSED #')
    print('##############')
