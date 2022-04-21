#!/usr/bin/env python3
"""Functions with utility outside of akgraph.

The functions here are candidates to move to akutil or even arkouda proper after
appropriate generalizaion and testing.

TODOS
-----
The numpy-like functions can probably be combined with functions in the scripts
and generalized.
"""
__all__ = [
    "canonize_partition",
    "from_numpy",
    "get_nids",
    "get_perm",
    "is_perm",
    "is_refinement",
    "maximum",
    "minimum",
    "numpy_edges_to_hdf5",
    "to_numpy",
]


from typing import List
import os
import subprocess

import h5py
import numpy as np

import arkouda as ak


def canonize_partition(A: ak.pdarray) -> ak.pdarray:
    """
    Treat an array of integers as labels for the indices.

    Re-label using the lowest index for each label.
    """
    ga = ak.GroupBy(A)
    _, new_labels = ga.argmin(A)
    return ga.broadcast(new_labels, permute=True)


def is_refinement(A: ak.pdarray, B: ak.pdarray) -> bool:
    """
    Determine if A is a refinement of B.

    A is a refinment of B if, for every unique value in A, all indices
    with that value have the same value in B
    """
    ga = ak.GroupBy(A)
    _, uniqBs = ga.nunique(B)
    return ak.all(uniqBs == 1)


def get_nids(
    user: str = os.environ["USER"],
    proc_name: str = "CHPL-arkouda_se"
) -> List[str]:
    """Find nodes on which arkouda servers are running for a given user."""
    slist = (
        subprocess.run(
            ["squeue", "-u", user, "-O", "NODELIST", "-n", proc_name],
            capture_output=True,
        )
        .stdout.decode("ascii")
        .split()
    )
    nidstrs = [s for s in slist if s.startswith("nid")]
    nids = []
    for nidstr in nidstrs:
        a, b = nidstr.split("[")[:2]
        nids.append(a + b.split(",")[0].split("-")[0])

    return nids


def get_perm(n: int) -> ak.pdarray:
    """Create random permutation of [0..n-1]."""
    randnums = ak.randint(0, 1, n, dtype=ak.float64)
    return ak.argsort(randnums)


def is_perm(A: ak.pdarray) -> bool:
    """Is A a permutation of [0..n-1]?"""
    n = A.size
    return ak.unique(A).size == n and A.min() == 0 and A.max() == n - 1


def minimum(A: ak.pdarray, B: ak.pdarray) -> ak.pdarray:
    """Calculate element-wise minimum of two arrays."""
    return ak.where(A <= B, A, B)


def maximum(A: ak.pdarray, B: ak.pdarray) -> ak.pdarray:
    """Calculate element-wise maximum of two arrays."""
    return ak.where(A <= B, B, A)


def to_numpy(A: ak.pdarray, tmp_dir: str = '') -> np.ndarray:
    """
    Transfer an arkouda array to numpy using HDF5 on disk.

    TODOS
    -----
    Test for resulting size (make sure you don't overload a worker node.
    """
    rng = np.random.randint(2 ** 64, dtype=np.uint64)
    tmp_dir = os.getcwd() if not tmp_dir else tmp_dir
    A.save(f"{tmp_dir}/{rng}")
    files = sorted(f"{tmp_dir}/{f}"
                   for f in os.listdir(tmp_dir) if f.startswith(str(rng)))

    B = np.zeros(A.size, dtype=np.int64)
    i = 0
    for file in files:
        with h5py.File(file, 'r') as hf:
            a = hf["array"]
            B[i : i + a.size] = a[:]
            i += a.size
        os.remove(file)

    return B


def from_numpy(A: np.ndarray, tmp_dir: str = '') -> ak.pdarray:
    """Transfer a numpy array to arkouda using HDF5."""
    rng = np.random.randint(2**64, dtype=np.uint64)
    tmp_dir = os.getcwd() if not tmp_dir else tmp_dir
    with h5py.File(f'{tmp_dir}/{rng}.hdf5', 'w') as f:
        arr = f.create_dataset('arr', data=A)

    B = ak.read_hdf('arr', f'{tmp_dir}/{rng}.hdf5')
    os.remove(f'{tmp_dir}/{rng}.hdf5')

    return B


def numpy_edges_to_hdf5(V: np.ndarray, U: np.ndarray, file: str):
    """Save numpy arrays as an HDF5 file."""
    with h5py.File(file, 'w') as f:
        src = f.create_dataset('src', data=V)
        dst = f.create_dataset('dst', data=U)


