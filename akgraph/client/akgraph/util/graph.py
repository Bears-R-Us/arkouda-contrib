#!/usr/bin/env python3
"""Graph-specific utility functions."""
__all__ = [
    "edges_from_dataframe",
    "pack_edges",
    "relabel_nodes",
    "remove_duplicates",
    "remove_loops",
    "sort_edges",
    "standardize_edges",
    "subgraph",
    "symmetrize_egdes",
    "unpack_edges",
]


from typing import List, Optional, Tuple, Union

import arkouda as ak

from akgraph.util.general import minimum, maximum


def remove_loops(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None
) -> Tuple[ak.pdarray]:
    """Remove self-loops from an edgelist."""
    not_loop = V != U
    V, U = V[not_loop], U[not_loop]
    if W is not None: W = W[not_loop]

    return (V, U, W) if W is not None else (V, U)


def remove_duplicates(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None
) -> Tuple[ak.pdarray]:
    """Remove duplicates and sort an edgelist faster + smaller than GroupBy."""
    # sort to allow duplicate removal
    pi = ak.coargsort([V, U])
    V, U = V[pi], U[pi]
    if W is not None:
        W = W[pi]

    # find unique elements
    dV = (V[1:] - V[:-1]) != 0
    dU = (U[1:] - U[:-1]) != 0
    uniq = ak.zeros(V.size, 'bool')
    uniq[0]  = 1
    uniq[1:] = (dV | dU)

    # keep only one copy
    V, U = V[uniq], U[uniq]
    if W is not None:
        W = W[uniq]

    return (V, U, W) if W is not None else (V, U)


def relabel_nodes(
    V: ak.pdarray,
    U: ak.pdarray,
) -> Tuple[ak.pdarray]:
    """Relabel nodes consecutively in [0..n-1].

    Return relabeled edges and array of old labels.
    """
    sortedV, sortedU = V.is_sorted(), U.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=sortedV)
    gU = ak.GroupBy(U, assume_sorted=sortedU)
    v, u = gV.unique_keys, gU.unique_keys
    labels = ak.union1d(v, u)
    new = ak.arange(labels.size)
    in_v, in_u = ak.in1d(labels, v), ak.in1d(labels, u)
    V = gV.broadcast(new[in_v], permute=(not sortedV))
    U = gU.broadcast(new[in_u], permute=(not sortedU))

    return (V, U, labels)


def symmetrize_egdes(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None
) -> Tuple[ak.pdarray]:
    """Add return edges to the edgelist.

    Expects edges are already unique and loop-less.
    """
    V, U = (ak.concatenate([V, U], ordered=False),
            ak.concatenate([U, V], ordered=False))
    if W is not None:
        W = ak.concatenate([W, W], ordered=False)

    return (V, U, W) if W is not None else (V, U)


def sort_edges(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None
) -> Tuple[ak.pdarray]:
    """Sort edges by out node then in node."""
    pi = ak.coargsort([V, U])
    V, U = V[pi], U[pi]
    if W is not None:
        W = W[pi]

    return (V, U, W) if W is not None else (V, U)


def edges_from_dataframe(
    df,
    source: Union[str, int] = 'source',
    target: Union[str, int] = 'target',
    weight: Optional[Union[str, int]] = None,
    weight_reduce: Optional[str] = None,
    symmetric: bool = True,
    sort: bool = True,
    return_labels: bool = False
) -> List[ak.pdarray]:
    """
    Return edges compatible with akgraph algorithms from akutil.DataFrame.

    Do the following things:
        Remove duplicate edges and self loops
        Relabel nodes as zero-up integers
        Symmetrize edges (optional)
        Sort (optional)
        Return original labels (optional)

    Parameters
    ----------
    df : { aku.dataFrame | dict }
        data to translate
    source : { str | int }
        valid column name for the source nodes, column must be int64 compatible
    target : { str | int }
        valid column name for the target nodes, column must be int64 compatible
    weight : { str | int | None } (optional)
        valid column name for the edge weights, column must be int64 or float64
    weight_reduce : { str | None } (optional)
        reduction operator to apply to weight column in case of duplicate
        edges. If weight is None, weight_reduce must be 'count' or None. If
        weight is not None, weight_reduce must be a member of
        arkouda.GROUPBY_REDUCTION_TYPES.
    symmetric : bool (default True)
        ensure all edges go both directions
    sort : bool (default True)
        sort the returned array. Only necessary if symmetric == True.
    return_labels : bool (default False)
        return original node labels

    Returns
    -------
    V : ak.pdarray[int64]
        standardized out nodes
    U : ak.pdarray[int64]
        standardized in nodes
    W : ak.pdarray[int64] (optional)
        weights of standardized edges if result is weighted
    labels : ak.pdarray[int64] (optional)
        labels[i] is the orignal label of node i

    Notes
    -----
    If weight is not None, weight_reduce is None and there are duplicate
    edges, an arbitrary value from the weight column will be chosen
    within each (source, target) pair.

    See Also
    --------
    standardize_edges()
    """
    V, U = df[source], df[target]
    W = df[weight] if weight is not None else None
    return standardize_edges(V, U, W, weight_reduce,
                             symmetric, sort, return_labels)


def standardize_edges(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    weight_reduce: Optional[str] = None,
    symmetric: bool = True,
    sort: bool = True,
    return_labels: bool = False
) -> List[ak.pdarray]:
    """
    Make edgelist compatible with akgraph algorithms.

    Do the following things:
        Remove duplicate edges and self loops
        Relabel nodes as zero-up integers
        Symmetrize edges (optional)
        Sort (optional for symmetrized results)
        Return original labels (optional)

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : { ak.pdarray | None } (default None)
        edge weights
    weight_reduce : { str | None } (default None)
        reduction operator to apply to W in case of duplicate edges. If W is
        None, weight_reduce must be 'count' or None. If W is not None,
        weight_reduce must be in arkouda.GROUPBY_REDUCTION_TYPES.
    symmetric : bool (default True)
        ensure all edges go both directions
    sort : bool (default True)
        sort the returned array. Only used if symmetric == True.
    return_labels : bool (default False)
        return original node labels

    Returns
    -------
    V : ak.pdarray[int64]
        standardized out nodes
    U : ak.pdarray[int64]
        standardized in nodes
    W : ak.pdarray[int64] (optional)
        weights of standardized edges if result is weighted
    labels : ak.pdarray[int64] (optional)
        labels[i] is the orignal label of node i

    Notes
    -----
    If W is not None and weight_reduce is None and there are duplicate edges, an
    arbitrary value from W will be chosen from within each (v, u) pair.
    """
    if V.size != U.size:
        raise ValueError('V and U not the same size.')
    if W is not None and W.size != V.size:
        raise ValueError('Weight dimensions do not match.')

    # must do this before deduplicating/relabeling
    if symmetric:
        V, U = minimum(V, U), maximum(V, U)

    # remove loops
    if W is None:
        V, U = remove_loops(V, U)
    else:
        V, U, W = remove_loops(V, U, W)

    # deduplicate edges and apply requested aggregation
    if W is None and weight_reduce is None:
        V, U = remove_duplicates(V, U)
    elif W is None and weight_reduce == 'count':
        g = ak.GroupBy([V, U])
        (V, U), W = g.count()
    elif W is not None and weight_reduce is None:
        V, U, W = remove_duplicates(V, U, W)
    elif W is not None and weight_reduce in ak.GROUPBY_REDUCTION_TYPES:
        g = ak.GroupBy([V, U])
        (V, U), W = g.aggregate(W, weight_reduce)
    else:
        raise ValueError('invalid combination of weight and weight_reduce:\n'
                         f'weight = {weight}\nweight_reduce = {weight_reduce}')

    # perform relabeling
    V, U, labels = relabel_nodes(V, U)

    # perform remaining steps
    if W is None:
        if symmetric:          V, U = symmetrize_egdes(V, U)
        if sort and symmetric: V, U = sort_edges(V, U)
    else:
        if symmetric:          V, U, W = symmetrize_egdes(V, U, W)
        if sort and symmetric: V, U, W = sort_edges(V, U, W)

    # return necessary output
    out = [V, U]
    if W is not None: out.append(W)
    if return_labels: out.append(labels)

    return out


def pack_edges(
    V: ak.pdarray,
    U: ak.pdarray,
    forward_only: bool = True,
    sort: bool = True,
) -> ak.pdarray:
    """
    Smush edges for storage.

    Defaults assume that you get symmetric edges with all nodes labeled with
    uint32s and put V and U into a single int64, dropping return edges and
    sorting.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    forward_only : bool (default True)
        drop edges with V >= U
    sort : bool (default True)
        sort packed array

    Return
    ------
    E : ak.pdarray[int64]
        packed edges
    """
    if V.min() < 0 or 2 ** 32 - 1 < V.max():
        raise ValueError('V is not uint32 compatible')
    if U.min() < 0 or 2 ** 32 - 1 < U.max():
        raise ValueError('U is not uint32 compatible')
    if V.size != U.size:
        raise ValueError('V and U not the same size')

    if forward_only:
        I = (V < U)
        V, U = V[I], U[I]

    E = (V << 32) | U

    if sort: E = ak.sort(E)

    return E


def unpack_edges(
    E: ak.pdarray,
    symmetric: bool = True,
    sort: bool = True
) -> Tuple[ak.pdarray]:
    """
    Rebiggen packed edges.

    Assume E represents output of successful pack_edges().

    Returned edges may be permuted from their original order.

    Parameters
    ----------
    E : ak.pdarray[int64]
        array in packed format
    symmetric : bool (default True)
        return symmetric arrays
    sort : bool (default True)
        return sorted arrays

    Return
    ------
    V (U) : akpdarray[int64]
        first (last) 32 bits of E
    """
    if E.dtype != ak.dtype('int64'):
        raise ValueError('E must be an int64 array')

    V = E >> 32
    I = (V < 0)
    V[I] += 2 ** 32
    U = E & 0xFFFFFFFF

    if symmetric: V, U = symmetrize_egdes(V, U)
    if sort:      V, U = sort_edges(V, U)
    
    return V, U


def subgraph(
    V: ak.pdarray,
    U: ak.pdarray,
    nodes: ak.pdarray,
    one_hop: bool = False
) -> Tuple[ak.pdarray]:
    """
    Returns the subgraph induced on nodes.

    The returned edges are all edges with both ends in `nodes`.  If `one_hop` is
    True, return all edges where *either* end is in `nodes`.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    nodes : ak.pdarray[int64]
        vertices to seed subgraph
    one_hop : bool (default False)
        return edges to or from `nodes`

    Returns
    -------
    A : ak.pdarray[int64]
        induced out nodes
    B : ak.pdarray[int64]
        induced in nodes
    """
    if one_hop:
        mask = ak.in1d(V, nodes) | ak.in1d(U, nodes)
    else:
        mask = ak.in1d(V, nodes) & ak.in1d(U, nodes)

    return V[mask], U[mask]


if __name__ == '__main__':
    from akgraph.generators import path_graph, complete_graph, karate_club_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    A = ak.array([1, 1, 1, 3, 3, 8, 8, 1])
    B = ak.array([1, 2, 3, 1, 4, 8, 5, 2])

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Loop Removal ====')
    X, Y = remove_loops(A, B)
    X_ans = ak.array([1, 1, 3, 3, 8, 1])
    Y_ans = ak.array([2, 3, 1, 4, 5, 2])
    assert ak.all(X == X_ans)
    assert ak.all(Y == Y_ans)

    print('==== Testing Duplicate Removal ====')
    X, Y = remove_duplicates(A, B)
    X_ans = ak.array([1, 1, 1, 3, 3, 8, 8])
    Y_ans = ak.array([1, 2, 3, 1, 4, 5, 8])
    assert ak.all(X == X_ans)
    assert ak.all(Y == Y_ans)

    print('==== Testing Symmetrize ====')
    X, Y = symmetrize_egdes(A, B)
    X_ans = ak.array([1, 1, 1, 2, 1, 3, 3, 1, 3, 4, 8, 8, 8, 5, 1, 2])
    Y_ans = ak.array([1, 1, 2, 1, 3, 1, 1, 3, 4, 3, 8, 8, 5, 8, 2, 1])
    assert ak.all(X == X_ans)
    assert ak.all(Y == Y_ans)

    print('==== Testing Edge Standardization ====')
    V, U, L = standardize_edges(A, B, symmetric=False, return_labels=True)
    assert ak.all(L == ak.array([1, 2, 3, 4, 5, 8]))
    assert ak.all(V == ak.array([0, 0, 2, 2, 5]))
    assert ak.all(U == ak.array([1, 2, 0, 3, 4]))

    V, U = standardize_edges(A, B)
    assert ak.all(V == ak.array([0, 0, 1, 2, 2, 3, 4, 5]))
    assert ak.all(U == ak.array([1, 2, 0, 0, 3, 2, 5, 4]))

    print('==== Testing Edge Packing ====')
    V = ak.randint(0, 2 ** 8, 2 ** 16, dtype='int64')
    U = ak.randint(0, 2 ** 8, 2 ** 16, dtype='int64')
    V, U = standardize_edges(V, U)
    E = pack_edges(V, U)
    X, Y = unpack_edges(E)
    F = pack_edges(X, Y)
    assert ak.all(V == X)
    assert ak.all(U == Y)
    assert ak.all(E == F)

    print('==== Testing Induced Subgraphs ====')
    # path graph
    V, U = path_graph(4)
    pi = ak.coargsort([V, U])
    V, U = V[pi], U[pi]
    nodes = ak.array([0, 1, 2])
    A, B = subgraph(V, U, nodes)
    assert ak.all(A == ak.array([0, 1, 1, 2]))
    assert ak.all(B == ak.array([1, 0, 2, 1]))
    C, D = subgraph(V, U, nodes, True) # one-hop
    assert ak.all(C == ak.array([0, 1, 1, 2, 2, 3]))
    assert ak.all(D == ak.array([1, 0, 2, 1, 3, 2]))

    # complete graph
    V, U = complete_graph(5)
    A, B = complete_graph(3)
    C, D = subgraph(V, U, ak.array([0, 1, 2]))
    assert ak.all(A == C) and ak.all(B == D)
    C, D = subgraph(V, U, ak.array([0, 1, 2]), True) # one-hop
    assert ak.all(C == ak.array(
        [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4]))
    assert ak.all(D == ak.array(
        [1, 2, 3, 4, 0, 2, 3, 4, 0, 1, 3, 4, 0, 1, 2, 0, 1, 2]))

    print('##############')
    print('# YOU PASSED #')
    print('##############')
