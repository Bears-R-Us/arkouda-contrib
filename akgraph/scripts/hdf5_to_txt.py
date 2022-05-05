#!/usr/bin/env python3
"""Translate HDF5 files into text.

You should only use this with HDF5 files holding columnar data of the same length.
"""
from typing import Dict
import argparse
import os
import sys

import h5py
import numpy as np


def parse_args() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('FILE', type=os.path.abspath,
                        help='file to translate.')
    parser.add_argument('-o', '--out', type=str, default='',
                        help='output file or directory (default FILE.txt)')
    parser.add_argument('-c', '--columns', type=str, nargs='+',
                        help=('columns to load and print, in order. '
                              'default to all in sorted order'))
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='print destination and exit')
    parser.add_argument('-l', '--labels', action='store_true',
                        help='print column keys on the first line of output')
    args = parser.parse_args()
    if not os.path.isfile(args.FILE):
        print(f"{args.FILE} not found.")
        sys.exit(2)

    if not args.out:
        f = args.FILE
        args.out = f[:-5] + '.txt' if f.endswith('hdf5') else f + '.txt'
    elif os.path.isdir(args.out):
        f = os.path.basename(args.FILE)
        f = f[:-5] + '.txt' if f.endswith('hdf5') else f + '.txt'
        args.out = os.path.join(args.out, f)

    return args


def read_hdf5(args: argparse.Namespace) -> Dict[str, np.ndarray]:
    """Load specified columns from the hdf5 file."""
    with h5py.File(args.FILE, 'r') as f:
        data = {
            key: arr[:]
            for key, arr in f.items()
            if key in args.columns
        } if args.columns else {
            key: arr[:] for key, arr in f.items()
        }

    if args.columns and not all(c in data for c in args.columns):
        print(f"error: trouble finding columns:\n    {args.columns}\n"
              f"found:\n    {data.keys()}")
        sys.exit(1)

    return data


def write_txt(args: argparse.Namespace, data: Dict[str, np.ndarray]):
    """Save the specified columns in a tabular text file."""
    header = ' '.join(args.columns) if args.labels else ''
    cols = args.columns if args.columns else sorted(data)
    X = np.column_stack([data[col] for col in cols])
    fmt = ' '.join(
        '%d' if np.issubdtype(data[col].dtype, np.integer) else '%.15e'
        for col in cols)
    np.savetxt(args.out, X, fmt=fmt, header=header)


def main():
    """Translate hdf5 files into txt files."""
    args = parse_args()
    if args.dry_run:
        print(args.out)
        sys.exit(0)

    data = read_hdf5(args)
    write_txt(args, data)


if __name__ == '__main__':
    main()
