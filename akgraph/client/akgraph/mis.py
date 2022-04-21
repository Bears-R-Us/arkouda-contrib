#!/usr/bin/env python3
"""Algorithm for calculating a maximal independent set on graphs."""
__all__ = ["valid_mis", "maximal_independent_set"]


from typing import Optional

import arkouda as ak
from akgraph.util.general import get_perm, is_perm


def valid_mis(
    V: ak.pdarray,
    U: ak.pdarray,
    I: ak.pdarray
) -> bool:
    """
    Decide if I represents a valid maximal independent set.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    I : ak.pdarray[bool] (n elements)
        I[v] == True if v in maximal independent set

    Returns
    -------
    bool : I is maximal independent set.
    
    Notes
    -----
    Assumes edges are symmetric.
    """
    n = V.max() + 1
    if I.size != n:
        raise ValueError('error: invalid MIS size: {I.size} != {n}')

    v_sorted, u_sorted = V.is_sorted(), U.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=v_sorted)
    gU = ak.GroupBy(U, assume_sorted=u_sorted)
    
    I_edge = gV.broadcast(I, permute=(not v_sorted))
    _, N = gU.any(I_edge)
    
    return ak.all(I ^ N)


def maximal_independent_set(
    V: ak.pdarray,
    U: ak.pdarray,
    pi: Optional[ak.pdarray] = None,
    verbose: bool = False
) -> ak.pdarray:
    """
    Return a random maximal independent set.

    An independent set is a set of nodes such the subgraph induced on these
    nodes contains no edges. A maximal independent set is an independent set
    such that it is not possible to add a new node and maintain independence.

    The permutation `pi` is used to determine an ordering on the nodes. Each
    ordering leads to exactly one output. Selecting an independent set of nodes
    to appear first in `pi` ensures their inclusion in the result.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    pi : ak.pdarray[int64]
        node permutation
    verbose : bool (default False)
        print progress

    Returns
    -------
    I : ak.pdarray[bool] (n elements)
        I[v] == True if v in maximal independent set

    Notes
    -----
    Assumes edges are symmetric.

    This algorithm does not solve the __maximum__ independent set problem.

    References
    ----------
    Theoretically Efficient Parallel Graph Algorithms Can be Fast and Scalable.
        Laxman Dulipala, Guy E. Blelloch, Julian Shun. CoRR (2018)
        https://arxiv.org/abs/1805.05208
    """
    n = V.max() + 1
    v_sorted, u_sorted = V.is_sorted(), U.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=v_sorted)
    gU = ak.GroupBy(U, assume_sorted=u_sorted)

    if pi is None:
        pi = get_perm(n)
    elif pi.size != n or not is_perm(pi):
        raise ValueError(f'error: invalid permutation pi={pi}')

    piV = gV.broadcast(pi, permute=(not v_sorted))
    piU = gU.broadcast(pi, permute=(not u_sorted))
    back_edge = piU < piV               # edges (v, u) with pi[u] < pi[v]

    _, priority = gV.sum(back_edge)  # neighbors before v in pi
    I = ak.zeros(n, 'bool')          # output mask
    roots = (priority == 0)          # initial ind. set
    available = ~roots               # remaining nodes
    num_remaining = available.sum()   
    k = 0
    while num_remaining > 0:
        k += 1
        I |= roots
        available &= ~roots         

        # find neigbors of roots
        root_edge = gV.broadcast(roots, permute=(not v_sorted))
        _, nbrs = gU.any(root_edge)

        # remove neighbors and reduce priority to zero
        removed = nbrs & available
        available &= ~removed
        priority[removed] = 0
        num_remaining = available.sum()

        # determine new priority for edges (v, u) where:
        # v in {removed} and pi[v] < pi[u]
        removed_edge = gV.broadcast(removed, permute=(not v_sorted))
        minus_edge = removed_edge & ~back_edge
        _, priority_loss = gU.sum(minus_edge)
        
        # decrement priority
        # roots are the newly zeroed elements
        priority -= priority_loss
        priority *= (priority > 0)
        roots = (priority == 0) & available

        if verbose:
            print(f'       round = {k}')
            print(f'     |roots| = {roots.sum()}')
            print(f' |available| = {num_remaining}')

    return I


