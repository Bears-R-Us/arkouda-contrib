#!/usr/bin/env python3
"""Benchmark algorithms for scaling tests."""
from time import time
from statistics import mean, stdev
import argparse
import random

import numpy as np

import arkouda as ak
import akgraph as akg


def generate_graph(scale):
    """Generate a weighted-undirected RMAT graph."""
    V, U = akg.rmat(scale, weighted=False)
    assert V.max() == U.max()
    n = V.max() + 1
    assert V.is_sorted()
    gV = ak.GroupBy(V, assume_sorted=True)
    gU = ak.GroupBy(U, assume_sorted=False)
    return {'n': n, 'V': V, 'U': U, 'gV': gV, 'gU': gU}


def bfs(G, source):
    """Perform a breadth first search from source. Return distances."""
    n, gV, gU = G['n'], G['gV'], G['gU']

    t0 = time()
    depth = 0
    d = ak.zeros(n, 'int64') - 1
    d[source] = depth
    f = (d == depth)

    while f.sum() > 0:
        depth += 1
        f_edge = gV.broadcast(f, permute=False)
        _, f_nbr = gU.any(f_edge)
        f = f_nbr & (d < 0)
        d[f] = depth

    return (time() - t0, d)


def concomp(G):
    """Calculate the connected components of a graph."""
    n, gV, gU = G['n'], G['gV'], G['gU']

    t0 = time()
    
    nf, ng = ak.arange(n), ak.arange(n)
    f, g = ak.zeros_like(nf), ak.zeros_like(ng)
    while ak.any(ng != g):
        g[:], f[:] = ng[:], nf[:]
        g_dst = gU.broadcast(g, permute=True)
        _, g_min = gV.min(g_dst)
        f[f] = g_min
        f = ak.where(f < g_min, f, g_min)
        nf = ak.where(f < g, f, g)
        ng = nf[nf]
    
    return (time() - t0, nf)


def pagerank(G):
    """Perform PageRank on a graph."""
    n, gV, gU = G['n'], G['gV'], G['gU']
    max_iter, alpha, tol = 5, 0.85, 1.0e-6

    p = ak.ones(n, 'float64') / n
    y = ak.ones(n, 'float64') / n
    _, deg = gV.count()
    W = gV.broadcast(1.0 / deg, permute=False)

    times = []
    for _ in range(max_iter):
        t0 = time()
        x = y
        x_edge = gV.broadcast(x, permute=False)
        _, y = gU.sum(x_edge * W)
        y *= alpha
        y += (1 - alpha) * p
        y /= y.sum()
        delta = ak.abs(y - x).sum()
        times.append(time() - t0)
        if delta < tol * n: break

    return (times, y)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('SCALE', type=int, help='scale of graph to generate')
    parser.add_argument('-t', '--num_trials', type=int, default=16,
                        help='number of trials for each algorithm')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print progress')
    parser.add_argument('-b', '--skip_bfs', action='store_true',
                        help='skip breadth-first search algorithm')
    parser.add_argument('-c', '--skip_cc', action='store_true',
                        help='skip connected components algorithm')
    parser.add_argument('-p', '--skip_pr', action='store_true',
                        help='skip pagerank algorithm')
    args = parser.parse_args()

    ak.connect(akg.get_nids()[0])

    t = time()
    G = generate_graph(args.SCALE)
    print('Graph Generated:\n'
          f'k = {args.SCALE:,}\n'
          f'n = {G["n"]:,}\n'
          f'm = {G["V"].size:,}\n'
          f't = {time()-t:0.0f} s')

    # bfs
    if not args.skip_bfs:
        times = []
        d_max = []
        for i in range(args.num_trials):
            source = random.randint(0, G['n'] - 1)
            t, d = bfs(G, source)
            times.append(t)
            d_max.append(d.max())
            if args.verbose:
                print(f'{i:3} {t:0.1f} {d_max[-1]}')
        print(f"BFS: {mean(times):0.1f} +/- {stdev(times):0.1f} s")
        print(f"D(G) in [{max(d_max)}, {2 * min(d_max)}]")

    # connected components
    if not args.skip_cc:
        times = []
        for i in range(args.num_trials):
            t, c = concomp(G)
            nc = ak.unique(c).size
            times.append(t)
            if args.verbose:
                print(f'{i:3} {t:0.1f} {nc}')
        print(f"Connected Components: {mean(times):0.1f} +/- {stdev(times):0.1f} s")
        print(f"|C| = {nc}")

    # pagerank
    if not args.skip_pr:
        times = []
        for i in range(args.num_trials):
            t, x = pagerank(G)
            times.extend(t)
            if args.verbose:
                print(f'{i:3} {sum(t):0.1f} {len(t)}')
        print(f"PageRank: {mean(times):0.1f} +/- {stdev(times):0.1f} s")

    ak.clear()


if __name__ == '__main__':
    main()
