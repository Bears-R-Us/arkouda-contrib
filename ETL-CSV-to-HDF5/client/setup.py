#!/usr/bin/env python3

from distutils.core import setup

setup(name='hdflow',
      version='1.0',
      requires=['h5py', 'pandas', 'numpy', 'tqdm'],
      description='Converter (CSV to HDF5) and Reader',
      author='U.S. Government',
      author_email='',
      url='',
      packages=['hdflow'],
      scripts=['hdflow/scripts/csv2hdf'])

