#!/usr/bin/env python3
"""Algorithms to compute centrality measures on graphs."""
__all__ = ["eigenvector_centrality", "hub_auth", "pagerank"]


from typing import Optional, Tuple
from warnings import warn

import numpy as np

import arkouda as ak


def eigenvector_centrality(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    max_iter: int = 100,
    tol: float = 1e-08,
) -> Tuple[float, ak.pdarray]:
    """
    Compute the eigenvector centrality a graph.

    Eigenvector centrality computers the centrality for a node based on the
    centrality of its neighbors. The eigenvector centrality for a node i is
    the i-th element of the vector x which solves

        A @ x = c x

    where A is the adjacency matrix of the graph and c is the largest
    (magnitude) eigenvalue. By virtue of the Perron-Frobenius theorem, there
    is a unique solution which has entirely positive entries.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : ak.pdarray (optional)
        edge weights
    max_iter : int (default 100)
        maximum number of iterations in power method
    tol : float (default 1.0e-8)
        tolerance for convergence test

    Returns
    -------
    c : float
        largest (absolute value) eigenvalue of A
    e : ap.pdarray[float64]
        dominant eigenvector of A

    See Also
    --------
    pagerank()
    hub_auth()

    Notes
    -----
    Values are computed with the power iteration method. The code will emit a
    warning if it does not converge.

    References
    ----------
    Power and Centrality: A Family of Measures.
        Phillip Bonacich. American Journal of Sociology 92(5):1170-1182, 1986
    """
    n = max(V.max(), U.max()) + 1

    v_sorted, u_sorted = V.is_sorted(), U.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=v_sorted)
    gU = ak.GroupBy(U, assume_sorted=u_sorted)
    v_nodes, u_nodes = gV.unique_keys, gU.unique_keys

    e = ak.ones(n, 'float64') / np.sqrt(n)
    e_prev = ak.zeros_like(e)

    for _ in range(max_iter):
        e_prev[:] = e[:]
        e[:] = 0

        # e = A @ e
        e_edge = gU.broadcast(e_prev[u_nodes], permute=(not u_sorted))
        _, new_e = gV.sum(W * e_edge) if W is not None else gV.sum(e_edge)
        e[v_nodes] = new_e

        # calculate eigenvalue and normalize
        # assuming e_prev == e and |e| == 1 ==> e.T @ A @ e = lambda
        c = ak.sum(e_prev * e)
        e /= np.sqrt(ak.sum(e * e))

        # check convergence
        delta = ak.abs(e - e_prev).sum()
        if delta < tol * n:
            break
    else:
        warn(f"did not converge in {max_iter} steps, beware...")

    return (c, e)


def hub_auth(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    max_iter: int = 100,
    tol: float = 1.0e-8
) -> Tuple[ak.pdarray]:
    """
    Returns HITS hubs and authorities values for nodes.

    The HITS algorithm computes two numbers for each node.
    Authorities estimates the node value based on the incoming links.
    Hubs estimates the node value based on outgoing links.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : ak.pdarray (optional)
        edge weights
    max_iter : int (default 100)
        maximum number of iterations in power method
    tol : float (default 1.0e-8)
        tolerance for convergence test

    Returns
    -------
    h : ak.pdarray[float64]
        hub values for each node
    a : ak.pdarray[float64]
        authority values for each node

    Notes
    -----
    The values are computed using the power iteration method discussed in the
    reference. The code will emit a warning if it does not converge. The
    resulting vectors h and a are the principal eigenvectors of (A.T @ A) and
    (A @ A.T) respectively, where A is the adjacency matrix.

    The HITS algorithm was designed for unweighted, directed graphs. It will
    produce results similar to eigenvector centrality if given a symmetric
    graph. On weighted graphs it perfoms the principal eigenvector calculation
    discussed above.

    This implementation uses different normalization (L2) compared to NetworkX
    (L1) so answers will differ.

    See Also
    --------
    eigenvector_centrality()
    pagerank()

    References
    ----------
    Authoritative Sources in a Hyperlinked Environment
        Jon M. Kleinberg, Journal of the ACM 46 (5): 604-32, 1999.
        doi:10.1145/324133.324140.
        http://www.cs.cornell.edu/home/kleinber/auth.pdf.
    """
    n = max(V.max(), U.max()) + 1

    v_sorted, u_sorted = V.is_sorted(), U.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=v_sorted)
    gU = ak.GroupBy(U, assume_sorted=u_sorted)
    v_nodes, u_nodes = gV.unique_keys, gU.unique_keys

    h, a_prev = ak.zeros(n, 'float64'), ak.zeros(n, 'float64')
    a = ak.ones(n, 'float64') / np.sqrt(n)

    for _ in range(max_iter):
        a_prev[:] = a[:]
        a[:] = 0
        h[:] = 0

        # O operation: h = A @ a
        a_edge = gU.broadcast(a_prev[u_nodes], permute=(not u_sorted))
        _, new_h = gV.sum(W * a_edge) if W is not None else gV.sum(a_edge)
        h[v_nodes] = new_h

        # I operation: a = A.T @ h
        h_edge = gV.broadcast(h[v_nodes], permute=(not v_sorted))
        _, new_a = gU.sum(W * h_edge) if W is not None else gU.sum(h_edge)
        a[u_nodes] = new_a

        # normalize results
        a_norm, h_norm = np.sqrt(ak.sum(a * a)), np.sqrt(ak.sum(h * h))
        a, h = a / a_norm, h / h_norm

        # check convergence
        delta = ak.abs(a - a_prev).sum()
        if delta < tol * n:
            break
    else:
        warn(f"did not converge in {max_iter} steps, beware...")

    return (h, a)


def pagerank(
    V: ak.pdarray,
    U: ak.pdarray,
    W: Optional[ak.pdarray] = None,
    p_vec: Optional[ak.pdarray] = None,
    x_start: Optional[ak.pdarray] = None,
    max_iter: int = 100,
    alpha: float = 0.85,
    tol: float = 1.0e-8
) -> ak.pdarray:
    """
    Compute the PageRank centrality for all nodes.

    PageRank estimates the probability of ending up at a given node when
    starting from a set of input nodes and walking randomly along edges while
    also allowing for jumping to another starting location.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    W : ak.pdarray (optional)
        edge weights
    p_vec : ak.pdarray[float64] (optional)
      'personalization' vector representing probabilies for starting on a node
      or landing when 'jumping'. If not None, must be a vector of length n with
      at least one non-zero entry. If None, a uniform distribution is used.
    x_start : ak.pdarray[float64] (optional)
       starting PageRank for each node
    max_iter : int (default 100)
        maximum_number of iterations in power method
    alpha : float (default 0.85)
        damping factor
    tol : float (default 1.0e-8)
        tolerance for convergance test

    Return
    ------
    x : ak.pdarray[float64]
        PageRank centrality for each node

    Notes
    -----
    Values are computed with the power iteration method. The code will emit a
    warning if it does not converge.

    See Also
    --------
    eigenvector_centrality()
    hub_auth()

    References
    ----------
    Approximating Personalized PageRank with Minimal Use of Web Graph Data.
        David Gleich and Marzia Polito. Internet Mathematics Vol. 3, No. 3: 257
        - 294. (2006)
    """
    n = max(ak.max(V), ak.max(U)) + 1

    if p_vec is None:
        p = ak.ones(n, 'float64') / n
    else:
        if p_vec.size != n:
            raise ValueError(f'Bad personalization vector.')
        p = p_vec / p_vec.sum()

    if x_start is None:
        y = ak.ones(n, 'float64') / n
    else:
        if x_start.size != n:
            raise ValueError(f'Bad starting vector.')
        y = x_start / x_start.sum()

    v_sorted = V.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=v_sorted)
    gU = ak.GroupBy(U, assume_sorted=U.is_sorted())
    if W is None:
        v_nodes, deg = gV.count()
        W = gV.broadcast(1.0 / deg, permute=(not v_sorted))
    else:
        v_nodes, deg = gV.sum(W)
        W = W * gV.broadcast(1.0 / deg, permute=(not v_sorted))
    is_dangling = ak.ones(n, 'bool')
    is_dangling[v_nodes] = 0

    x = ak.zeros_like(y)
    for _ in range(max_iter):
        x[:] = y[:]
        y[:] = 0

        # y = a * x @ L_rw
        x_edge = gV.broadcast(x[v_nodes], permute=(not v_sorted))
        u_nodes, xu = gU.sum(x_edge * W)
        y[u_nodes] = xu
        y *= alpha

        # y += a * w_dangling * p  - (1 - a) * p
        y += alpha * x[is_dangling].sum() * p
        y += (1 - alpha) * p

        y /= y.sum()
        # check convergence
        delta = ak.abs(y - x).sum()
        if delta < tol * n:
            break
    else:
        warn(f"did not converge in {max_iter} steps beware...")

    return y


if __name__ == '__main__':
    from akgraph.generators import path_graph, complete_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    # generate data
    V = ak.array([1, 1, 3, 3, 3, 4, 4, 5, 5, 6]) - 1
    U = ak.array([2, 3, 1, 2, 5, 5, 6, 4, 6, 4]) - 1
    W = ak.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 1])
    c4V, c4U = complete_graph(4)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Eigenvector Centrality ====')
    # unweighted
    c, e = eigenvector_centrality(V, U)
    e_ans = ak.array([0.3185602 , 0., 0.5154412 , 0.51544117, 0.51544117,
                      0.31856016])
    assert np.abs(c - 1.61803397) < 1e-4
    assert ak.all(ak.abs(e - e_ans) < 1e-4)

    # weighted
    c, e = eigenvector_centrality(V, U, W, tol=1e-6)
    e_ans = ak.array([0.11856115, 0., 0.46627055, 0.56972278, 0.66234765,
                      0.07243326])
    assert np.abs(c - 7.86545993) < 1e-4
    assert ak.all(ak.abs(e - e_ans) < 1e-4)

    print('==== Testing HITS ====')
    # unweighted
    h, a = hub_auth(V, U)
    h_ans = ak.array( [0.35468849, 0., 0.75013338, 0.48164091, 0.26849258,
                       0.08619601])
    a_ans = ak.array( [0.3697928 , 0.54464337, 0.17485057, 0.17485062,
                       0.60722703, 0.36979285])
    assert ak.all(ak.abs(h - h_ans) < 1e-4)
    assert ak.all(ak.abs(a - a_ans) < 1e-4)

    # weighted
    h, a = hub_auth(V, U, W)
    h_ans = ak.array([0.00263481, 0., 0.119855 , 0.54681211, 0.82786225,
                      0.03561533])
    a_ans = ak.array([2.62970646e-02, 3.52554515e-02, 3.85397440e-04,
                      4.86975543e-01, 2.83777614e-01, 8.24857839e-01])
    assert ak.all(ak.abs(h - h_ans) < 1e-4)
    assert ak.all(ak.abs(a - a_ans) < 1e-4)

    print('==== Testing PageRank ====')
    # unweighted
    pr = ak.array([0.03721197, 0.05395736, 0.04150566,
                   0.3750808 , 0.20599833, 0.28624587])
    x = pagerank(V, U, alpha=0.9, tol=1.0e-08)
    assert ak.all(ak.abs(x - pr) <= 1e-4)

    # weighted
    pr = ak.array([0.04711131, 0.06477131, 0.06087235,
                   0.35146311, 0.19361657, 0.28216535])
    x = pagerank(V, U, W)
    assert ak.all(ak.abs(x - pr) <= 1e-4)

    # complete graph with differing personalizations
    p_vec = ak.array([1, 1, 4, 4])
    pr = ak.array([0.23246, 0.23246, 0.26753, 0.26753])
    x = pagerank(c4V, c4U, p_vec=p_vec)
    assert ak.all(ak.abs(x - pr) <= 1e-4)

    p_vec = ak.array([0, 0, 0, 1])
    pr = ak.array([0.22077, 0.22077, 0.22077, 0.33766])
    x = pagerank(c4V, c4U, p_vec=p_vec)
    assert ak.all(ak.abs(x - pr) <= 1e-4)

    print('##############')
    print('# YOU PASSED #')
    print('##############')
