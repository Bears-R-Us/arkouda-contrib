#!/usr/bin/env python3
"""Algorithms to compute things with triangles.

TODO: Make this module do anything. It's currently a placeholder.
"""
__all__ = ["triangle_centrality"]


from typing import Optional, Tuple
from warnings import warn

import arkouda as ak


def count_triangles(V: ak.pdarray, U: ak.pdarray) -> Tuple[int, ak.pdarray):
    """
    Count all triangles in a graph.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes

    Return
    ------
    num_triangles : int
        number of triangles in a graph
    T : ak.pdarray[int64]
        T[i] is the number of triangles containing node i
    """
    raise RuntimeError("count_triangles() is not implemented")


def triangle_centrality(V: ak.pdarray, U: ak.pdarray) -> ak.pdarray:
    """
    Compute centrality based on vertex and neighborhood triangle participation.

    Triangle centrality is based on the sum of triangle counts for a vertex and
    its neighbors normalized over the total triangle count in the graph.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes

    Return
    ------
    x : ak.pdarray[float64]
        triangle centrality for each node

    References
    ----------
    Triangle Centrality. Paul Burkhardt. (2021) https://arxiv.org/abs/2105.00110
    """
    raise RuntimeError("traingle_centrality() is not implemented")


if __name__ == '__main__':
    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Triangle Centrality ====')
    assert True

    print('##############')
    print('# YOU PASSED #')
    print('##############')
