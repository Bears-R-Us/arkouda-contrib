#!/usr/bin/env python3
"""Concatenate compatible HDF5 files together."""
from collections import defaultdict
from typing import List
import argparse
import os
import sys

import h5py


def parse_args():
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog="Assumes 1D arrays.")
    parser.add_argument('FILE', type=str, nargs='+',
                        help='files to concatenate')
    parser.add_argument('-o', '--output', required=True,
                        type=os.path.abspath, help='ouput file')
    args = parser.parse_args()

    if len(args.FILE) == 1:
        print("error: only one FILE")
        sys.exit(2)

    for f in args.FILE:
        if not os.path.isfile(f):
            print(f"error: {f} not found")
            sys.exit(2)

    return args


def concat_hdf5(srcs: List[str], dest: str):
    """Concatenate `srcs` into `dest` sequentially."""
    n = len(srcs)

    # find array sizes and types to allocate
    sizes, types = defaultdict(int), dict()
    for i in range(n):
        with h5py.File(srcs[i]) as fin:
            for key, arr in fin.items():
                sizes[key] += arr.size
                if i == 0:
                    types[key] = arr.dtype
                else:
                    if arr.dtype != types[key]:
                        print(f"clashing types in column {key}")
                        sys.exit(2)

    # copy data, keeping track of `head` of each array
    with h5py.File(dest, 'w') as fout:
        for key, size in sizes.items():
            fout.create_dataset(key, shape=(size,), dtype=types[key])

        istarts = defaultdict(int)
        for i in range(n):
            with h5py.File(srcs[i]) as fin:
                for key, arr in fin.items():
                    i, m = istarts[key], arr.size
                    fout[key][i:i + m] = arr[:]
                    istarts[key] += m


if __name__ == "__main__":
    args = parse_args()
    concat_hdf5(args.FILE, args.output)
