#!/usr/bin/env python3
"""Functions for performing degree calculations on edgelists."""
__all__ = [
    'degree_order',
    'degree',
    'in_degree',
    'out_degree',
]


from typing import Optional, Tuple

import arkouda as ak


def _dir_deg(
    inout: str,
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray],
    normalize,
) -> ak.pdarray:
    """Compute in or out degree."""
    if inout != 'in' and inout != 'out':
        raise ValueError(f'error: invalid inout value {inout}')

    n = max(V.max(), U.max()) + 1
    d = ak.zeros(n, dtype='int64')
    g = ak.GroupBy(U) if inout == 'in' else ak.GroupBy(V)
    node, deg = g.sum(W) if W is not None else g.count()
    d[node] += deg
    return d / d.sum() if normalize else d


def in_degree(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    normalize: bool = False,
    symmetric: bool = False
) -> ak.pdarray:
    """
    Compute the in-degree for each node.

    For unweighted graphs, this is the number of in-neighbors. For weighted
    graphs, it's the sum of in-edge weights.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : { ak.pdarray | None } (default None)
        edge weights
    normalize : bool (default False)
        output sums to one
    symmetric : bool (default False)
        assume graph is symmetric (save a little work)

    Returns
    -------
    d : ak.pdarray
        in-degree for each node
    """
    if symmetric:
        return degree(V, U, W, normalize, True)
    else:
        return _dir_deg('in', V, U, W, normalize)


def out_degree(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    normalize: bool = False,
    symmetric: bool = False
) -> ak.pdarray:
    """
    Compute the out-degree for each node.

    For unweighted graphs, this is the number of out-neighbors. For weighted
    graphs, it's the sum of out-edge weights.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : { ak.pdarray | None } (default None)
        edge weights
    normalize : bool (default False)
        output sums to one
    symmetric : bool (default False)
        assume graph is symmetric (save a little work)

    Returns
    -------
    d : ak.pdarray
        in-degree for each node
    """
    if symmetric:
        return degree(V, U, W, normalize, True)
    else:
        return _dir_deg('out', V, U, W, normalize)


def degree(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    normalize: bool = False,
    symmetric: bool = False
) -> ak.pdarray:
    """
    Compute the degree for each node.

    For unweighted graphs, this is the number of neighbors. For weighted
    graphs, it's the sum of incident edge weights.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : { ak.pdarray | None } (default None)
        edge weights
    normalize : bool (default False)
        output sums to one
    symmetric : bool (default False)
        assume graph is symmetric (save a little work)

    Returns
    -------
    d : ak.pdarray
        degree for each node
    """
    if symmetric:
        g = ak.GroupBy(V, assume_sorted=V.is_sorted())
        _, d = g.sum(W) if W is not None else g.count()
    else:
        V, U = (ak.concatenate([V, U], ordered=False),
                ak.concatenate([U, V], ordered=False))
        g = ak.GroupBy(V)

        if W is not None:
            W = ak.concatenate([W, W], ordered=False)
            _, d = g.sum(W)
        else:
            _, d = g.nunique(U)

    return d / d.sum() if normalize else d


def degree_order(V: ak.pdarray, U: ak.pdarray) -> Tuple[ak.pdarray]:
    """
    Relabel nodes and place edges in degree order.

    We define a degree ordering permutation pi such that pi[u] < pi[v] if deg(u)
    < deg(v) or (deg(u) == deg(v) and u < v).  We relabel the nodes according to
    this permutation, filter out edges preserving only those with destination
    above the source and sort the edges.

    Assumes edges are symmetric.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes

    Return
    ------
    pi : ak.pdarray[int64]
        pi[i] is the new label of node i in degree-order
    X : ak.pdarray[int64]
        degree-ordered out nodes
    Y : ak.pdarray[int64]
        degree-ordered in nodes
    """
    g = ak.GroupBy(V)
    node, deg = g.count()
    pi = ak.argsort(ak.coargsort([deg, node]))

    X, Y = pi[V], pi[U]
    mask = X < Y
    X, Y = X[mask], Y[mask]
    edge_perm = ak.coargsort([X, Y])
    X, Y = X[edge_perm], Y[edge_perm]

    return (pi, X, Y)


if __name__ == '__main__':
    from akgraph.generators import path_graph, complete_graph, karate_club_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Degree Centrality ====')
    # one edge
    V, U = ak.array([0]), ak.array([1])
    assert ak.all(in_degree(V, U) == ak.array([0, 1]))
    assert ak.all(out_degree(V, U) == ak.array([1, 0]))
    assert ak.all(degree(V, U) == ak.array([1, 1]))

    # complete graph
    V, U = complete_graph(5)
    assert ak.all(in_degree(V, U) == out_degree(V, U))
    assert ak.all(degree(V, U, symmetric=True) == 4)

    # path graph
    V, U = path_graph(3)
    d = degree(V, U, symmetric=True, normalize=True)
    x = ak.array([1/4, 1/2, 1/4])
    assert ak.all(ak.abs(d - x) < 1e-9)

    # directed graph
    V = ak.array([0, 1, 2, 3, 4, 5, 5, 5])
    U = ak.array([5, 5, 5, 5, 5, 6, 7, 8])
    out_deg = ak.array([1, 1, 1, 1, 1, 3, 0, 0, 0])
    in_deg = ak.array([0, 0, 0, 0, 0, 5, 1, 1, 1])
    deg = ak.array([1, 1, 1, 1, 1, 8, 1, 1, 1])
    assert ak.all(out_degree(V, U) == out_deg)
    assert ak.all(in_degree(V, U) == in_deg)
    assert ak.all(degree(V, U, normalize=True) == deg / 16)

    # weighted graph
    W = ak.array([1, 2, 3, 4, 5, 6, 7, 8])
    out_deg = ak.array([1, 2, 3, 4, 5, 21, 0, 0, 0])
    in_deg = ak.array([0, 0, 0, 0, 0, 15, 6, 7, 8])
    deg = ak.array([1, 2, 3, 4, 5, 36, 6, 7, 8])
    assert ak.all(out_degree(V, U, W) == out_deg)
    assert ak.all(in_degree(V, U, W) == in_deg)
    assert ak.all(degree(V, U, W) == deg)

    print('==== Testing Degree Ordering ====')
    # 4-path
    V, U = path_graph(4)
    L, X, Y = degree_order(V, U)
    assert ak.all(L == ak.array([0, 2, 3, 1]))
    assert ak.all(X == ak.array([0, 1, 2]))
    assert ak.all(Y == ak.array([2, 3, 3]))

    # 4-clique
    V, U = complete_graph(4)
    L, X, Y = degree_order(V, U)
    assert ak.all(L == ak.arange(4))
    assert ak.all(X == ak.array([0, 0, 0, 1, 1, 2]))
    assert ak.all(Y == ak.array([1, 2, 3, 2, 3, 3]))

    # karate-club
    _, V, U = karate_club_graph()
    L, X, Y = degree_order(V, U)
    assert ak.all(L == ak.array([32, 29, 30, 27, 12, 18, 19, 20, 24, 1, 13, 0,
                                 2, 25, 3, 4, 5, 6, 7, 14, 8, 9, 10, 26, 15, 16,
                                 11, 21, 17, 22, 23, 28, 31, 33]))
    assert ak.all(X == ak.array([0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8,
                                 8, 9, 9, 10, 10, 11, 11, 12, 12, 12, 13, 13,
                                 14, 14, 14, 15, 15, 15, 16, 16, 17, 17, 17, 18,
                                 18, 19, 20, 20, 20, 20, 21, 21, 21, 22, 22, 22,
                                 23, 23, 23, 23, 24, 24, 24, 24, 25, 25, 25, 25,
                                 25, 26, 26, 27, 27, 27, 28, 28, 28, 29, 29, 30,
                                 30, 31]))
    assert ak.all(Y == ak.array([32, 30, 33, 27, 32, 31, 33, 31, 33, 18, 19, 29,
                                 32, 31, 33, 31, 33, 29, 32, 31, 33, 22, 33, 13,
                                 19, 32, 18, 32, 29, 32, 33, 16, 21, 28, 26, 28,
                                 28, 30, 33, 19, 32, 32, 27, 29, 30, 32, 26, 30,
                                 33, 26, 31, 33, 24, 29, 31, 33, 30, 31, 32, 33,
                                 27, 29, 30, 32, 33, 31, 33, 29, 30, 32, 31, 32,
                                 33, 30, 32, 31, 32, 33]))

    print('##############')
    print('# YOU PASSED #')
    print('##############')
