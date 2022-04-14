#!/usr/bin/env python3
"""Community detection algorithms.

Edges must be symmetric (u, v) <==> (v, u).
"""
__all__ = ['cdlp']


from typing import Optional, Tuple, Union
from warnings import warn

import arkouda as ak
import akutil as aku

from akgraph.util import get_perm


def cdlp(
    V: ak.pdarray,
    U: ak.pdarray,
    initial_labels: Optional[ak.pdarray] = None,
    immune_nodes: Optional[ak.pdarray] = None,
    randomize: bool = True,
    max_iter: Union[int, None] = 20
) -> Tuple[int, ak.pdarray]:
    """
    Perform community detection via label propagation.

    At each iteration, a node is assigned the most common label of its
    neighbors, ties are broken deterministically by chosing the minimal mode
    value.  Stop when labels are stable or after set number of iterations.

    Parameters
    ----------
    V : ak.pdarray[int64]
        out nodes
    U : ak.pdarray[int64]
        in nodes
    initial_labels: ak.pdarray[int64] (optional)
        array containing starting labels for each node. `None` means zero-up
        labels will be used (see `randomize`).
    immune_nodes: ak.pdarray[bool] (optional)
        mask where True nodes will never update their label
    randomize : bool (default True)
        begin with randomly permuted labels. if `initial_labels` is not `None`,
        ignore `randomize`
    max_iter : {int | None} (default 100)
        number of iterations to attempt. `None` indicates continue until
        completion (which can be a long time).

    Return
    ------
    k : int
        number of iterations performed
    n_comms : int
        number of communities discovered
    converged : int
        did algorithm complete
    C : ak.pdarray[int64]
        community label for each node

    Notes
    -----
    The algorithm may not terminate in a reasonable number of steps.  Even so,
    many of the communities may be stable (and therefore useful) after just a
    few steps, hence the default of 20.  Tune and re-run as dictated by your use
    case.

    References
    ----------
    Near linear time algorithm to detect community structures in large-scale
        networks. Usha Raghavan, Reka Alber, and Soundar Kumara. Physical Review
        E 76.3 (2007) https://arxiv.org/abs/0709.2938
    """
    n = V.max() + 1
    if immune_nodes is not None and immune_nodes.size != n:
        raise ValueError('immune_nodes incompatible size: '
                         f'{immune_nodes.size} != {n}')

    newC = ak.zeros(n, 'int64')
    curC = ak.zeros(n, 'int64')
    oldC = ak.zeros(n, 'int64')

    if initial_labels is not None:
        if initial_labels.size != n:
            raise ValueError('initial_labels incompatible size: '
                             f'{initial_labels.size} != {n}')
        newC[:] = initial_labels[:]
        curC[:] = initial_labels[:]
    else:
        _labels = get_perm(n) if randomize else ak.arange(n)
        newC[:] = _labels[:]
        curC[:] = _labels[:]

    if not V.is_sorted():
       pi = ak.argsort(V)
       V, U = V[pi], U[pi]

    gV = ak.GroupBy(V, assume_sorted=True)
    n_comms = ak.unique(curC).size
    k, converged = 0, False
    while not converged and k < max_iter:
        k += 1
        curC[:], oldC[:] = newC[:], curC[:]

        # determine the minimal mode of labels among in-neigbbors
        outC = gV.broadcast(curC, permute=False)
        gUC = ak.GroupBy([U, outC])
        (dst, nbr_comm), count = gUC.count()
        gDst = ak.GroupBy(dst, assume_sorted=True)
        nodes, idx_comm = gDst.argmax(count)
        newC[nodes] = nbr_comm[idx_comm]
        if immune_nodes is not None:
            newC[immune_nodes] = curC[immune_nodes]

        # check convergence (and catch oscillations)
        n_comms = ak.unique(newC).size
        converged = ak.all(newC == curC) or ak.all(newC == oldC) or n_comms == 1

    return (k, n_comms, converged, newC)


if __name__ == '__main__':
    from akgraph.generators import complete_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Community Detection via Label Propagation ====')
    # test single edge
    V, U = ak.array([0, 1]), ak.array([1, 0])
    k, nc, c, C = cdlp(V, U, randomize=False)
    assert k == 2
    assert nc == 2
    assert c == True
    assert ak.all(C == V)

    # test disconnected communities
    V = ak.array([0, 2, 0, 3, 2, 3, 1, 4, 1, 5, 4, 5])
    U = ak.array([2, 0, 3, 0, 3, 2, 4, 1, 5, 1, 5, 4])
    k, nc, c, C = cdlp(V, U, randomize=False)
    assert k == 3
    assert nc == 2
    assert c == True
    assert ak.all(C == ak.array([0, 1, 0, 0, 1, 1]))

    # test connected communities
    A, B = complete_graph(5)
    X, Y = A + 5, B + 5
    V = ak.concatenate([A, X, ak.array([0, 5])], ordered=False)
    U = ak.concatenate([B, Y, ak.array([5, 0])], ordered=False)
    k, nc, c, C = cdlp(V, U, randomize=False)
    assert k == 3
    assert nc == 2
    assert c == True
    assert ak.all(C == ak.array([0, 0, 0, 0, 0, 5, 5, 5, 5, 5]))

    # test big clique
    V, U = complete_graph(10000)
    k, nc, c, C = cdlp(V, U, randomize=False)
    assert k == 2
    assert nc == 1
    #assert c == True
    assert ak.all(C == 0)

    print('##############')
    print('# YOU PASSED #')
    print('##############')
