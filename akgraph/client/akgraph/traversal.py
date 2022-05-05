#!/usr/bin/env python3
"""Algorithms for traversing graphs."""
__all__ = ["bfs_reachable", "bfs_distance", "bfs_forest"]


from typing import Optional, Tuple, Union

import arkouda as ak


def traversal_prep(V: ak.pdarray, U: ak.pdarray):
    """
    Extract needed information for traversal from edge-list.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes

    Returns
    -------
    N : int
        number of nodes in the graph
    n : int
        number of non-isolated nodes in graph
    vNodes : ak.pdarray[int64]
        nodes with out edges
    uNodes : ak.pdarray[int64]
        nodes with in edges
    vSort : bool
        is V sorted?
    uSort : bool
        is U sorted?
    gV : ak.GroupBy
        GroupBy over out nodes
    gU : ak.GroupBy 
        GroupBy over in nodes
    """
    N = max(V.max(), U.max()) + 1
    vSort, uSort = V.is_sorted(), U.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=vSort)
    gU = ak.GroupBy(U, assume_sorted=uSort)
    vNodes, uNodes = gV.unique_keys, gU.unique_keys
    nodes = ak.union1d(vNodes, uNodes)
    n = nodes.size

    return N, n, nodes, vNodes, uNodes, vSort, uSort, gV, gU


def bfs_reachable(
    V: ak.pdarray,
    U: ak.pdarray,
    source: Union[int, ak.pdarray],
    depth_limit: Optional[int] = None,
    verbose: bool = False
) -> ak.pdarray:
    """
    Perform a breadth-first search to determine reachability from `source`.

    Parameters
    ----------
    V : ak.pdarray[int64]
        source nodes for each edge
    U : ak.pdarray[int64]
        destination nodes for each edge
    source : { int | ak.pdarray[int64] }
        source node(s)
    depth_limit : int, optional (default n)
        only traverse this many levels
    assume_standard : bool (default False)
        assumes the edge list is sorted (by source vertex) and symmetric
    verbose : bool (default False)
        display progress

    Return
    ------
    reached : ak.pdarray[bool]
        True if node is reachable from source node(s) else false

    Notes
    -----
    May take too long on high-diameter graphs.
    Nodes need not be consecutively labelled (still must be non-negative).
    """
    N, n, nodes, vNodes, uNodes, vSort, uSort, gV, gU = traversal_prep(V, U)
    depth_limit = n if depth_limit is None else depth_limit

    depth = count = 0
    if isinstance(source, int):
        reachable = (nodes == source)
    else:
        reachable = ak.in1d(nodes, source)

    while count < reachable.sum() and depth < depth_limit:
        depth += 1
        count = reachable.sum()
        reachable_edge = gV.broadcast(reachable[vNodes], permute=bool(1 - vSort))
        _, reachable_nbr = gU.any(reachable_edge)
        reachable[uNodes] |= reachable_nbr

        if verbose:
            print(f' depth = {depth}')
            print(f'   |F| = {reachable.sum() - count:,d}\n')

    out = ak.zeros(N, 'bool')
    out[nodes] = reachable
    return out


def bfs_distance(
    V: ak.pdarray,
    U: ak.pdarray,
    source: Union[int, ak.pdarray],
    depth_limit: Optional[int] = None,
    verbose: bool = False
) -> ak.pdarray:
    """
    Perform a breadth first search to determine distances from `source`.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    source : { int | ak.pdarray[int64] }
        source node(s)
    depth_limit : int, optional (default n)
        only traverse this many levels
    verbose : bool (default False)
        display progress

    Return
    ------
    out : ak.pdarray[int64]
        distance from source nodes if visited, else -1

    Notes
    -----
    May take too long on high-diameter graphs.
    Nodes need not be consecutively labelled (still must be non-negative).
    """
    N, n, nodes, vNodes, uNodes, vSort, uSort, gV, gU = traversal_prep(V, U)
    depth_limit = n if depth_limit is None else depth_limit

    depth = 0
    dist = ak.zeros_like(nodes) - 1
    if isinstance(source, int):
        dist[nodes == source] = depth
    else:
        dist[ak.in1d(nodes, source)] = depth
    frontier = (dist == depth)

    while frontier.sum() > 0 and depth < depth_limit:
        depth += 1
        frontier_edge = gV.broadcast(frontier[vNodes], permute=bool(1 - vSort))
        _, frontier_nbr = gU.any(frontier_edge)
        frontier[:] = 0
        frontier[uNodes] = frontier_nbr & (dist[uNodes] < 0)
        dist[frontier] = depth

        if verbose:
            print(f' depth = {depth}')
            print(f'   |F| = {frontier.sum():,d}\n')

    out = ak.zeros(N, 'int64') - 1
    out[nodes] = dist
    return out


def bfs_forest(
    V: ak.pdarray,
    U: ak.pdarray,
    source: Union[int, ak.pdarray],
    depth_limit: Optional[int] = None,
    verbose: bool = False
) -> ak.pdarray:
    """
    Perform a breadth first search to construct a forest from `source`.

    Return an array representing the parent of each node in the forest.  Roots
    are fixed points (a root is its own parent).  Useful for single point(s)
    shortest paths.  If a node has two possible parents, default to the maximal
    parent.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    source : { int | ak.pdarray[int64] }
        source node(s), sorted
    depth_limit : int, optional (default n)
        only traverse this many levels
    verbose : bool (default False)
        display progress

    Return
    ------
    tree : ak.pdarray[int64]
        parent of each node if visited, else -1

    Notes
    -----
    May take too long on high-diameter graphs.
    Nodes need not be consecutively labelled (still must be non-negative).
    """
    N, n, nodes, vNodes, uNodes, vSort, uSort, gV, gU = traversal_prep(V, U)
    depth_limit = n if depth_limit is None else depth_limit

    depth = 0
    tree = ak.zeros(N, 'int64') - 1
    tent = ak.zeros_like(tree)
    if isinstance(source, int):
        tree[source] = source
    else:
        tree[ak.in1d(nodes, source)] = source
    frontier = (tree > -1)

    while frontier.sum() > 0 and depth < depth_limit:
        depth += 1
        frontier_edge = gV.broadcast(frontier[vNodes], permute=bool(1 - vSort))
        frontier_parent = (V * frontier_edge) - (~frontier_edge)
        _, idx = gU.argmax(frontier_parent)
        tent[:] = -1
        tent[uNodes] = frontier_parent[idx]
        frontier = (tent > -1) & (tree == -1)
        tree[frontier] = tent[frontier]

        if verbose:
            print(f' depth = {depth}')
            print(f'   |F| = {frontier.sum()}\n')

    out = ak.zeros(N, 'int64') - 1
    out[nodes] = tree 
    return out


def sssp_bf(
    V: ak.pdarray,
    U: ak.pdarray,
    W: ak.pdarray,
    source: int,
    verbose: bool = False
) -> Tuple[ak.pdarray]:
    """
    Calculate single-source shortest paths using the Bellman-Ford Algorihtm.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : ak.pdarray
        non-negative edge weights. integers or floats
    source : int
        source node
    verbose : bool (default False)
        display progress

    Returns
    -------
    tree : ak.pdarray[int64]
        parent of each node on SP
    dist : ak.pdarray
        distance to source

    Notes
    -----
    Takes only sorted edges representing simple graphs (symmetric with no loops).
    May take too long on high-diameter graphs.
    """
    inf = W.sum()  # Arbitrary large value (potential overflow)
    gU = ak.GroupBy(U, assume_sorted=False)
    n = gU.ngroups

    tree = ak.zeros(n, 'int64') - 1
    dist = ak.zeros(n, W.dtype) - 1
    changed = ak.zeros(n, 'bool')
    tree[source] = source
    dist[source] = 0
    changed[source] = True
    
    k = 0
    while changed.sum() > 0 and k < n:
        k += 1

        dist_nbr = gU.broadcast(dist, permute=False)
        mask = (dist_nbr >= 0)
        dist_nbr = (dist_nbr + W) * mask + inf * (~mask)

        _, idx_min = gU.argmin(dist_nbr)
        tent_dist  = dist_nbr[idx_min]
        tent_tree  = V[idx_min]

        changed = (tent_dist < dist) | ((dist < 0) & (tent_dist < inf))
        dist[changed] = tent_dist[changed]
        tree[changed] = tent_tree[changed]

        if verbose:
            print(f' round = {k}')
            print(f' d_max = {dist.max()}')
            print(f'   |C| = {changed.sum():,d}\n')

    if k == n:
        print('negative-weight cycle')

    return (tree, dist)



