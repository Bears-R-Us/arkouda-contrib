import pdb

import pandas as pd
import numpy as np
import h5py
import os, json
from glob import glob
import warnings
import multiprocessing as mp
from itertools import repeat
from tqdm import tqdm
from threading import Thread
from copy import deepcopy
from functools import lru_cache, partial
from time import sleep
from ipaddress import ip_address
from numba import jit


##########
# Converting CSV to HDF5

def identity(x):
    return x

class Converter:
    def __init__(self, dtype, NAval=None, preprocessor=identity):
        self.dtype = np.dtype(dtype)
        self.preprocessor = preprocessor
        # Convert user-specified NA value to dtype
        if NAval is not None:
            self.NAval = self.dtype.type(NAval)
        # Default NA for signed integer is -1 in dtype
        elif self.dtype.kind == 'i':
            self.NAval = self.dtype.type(-1)
        # Default NA for unsigned integer is high-bit set, other bits 0
        elif self.dtype.kind == 'u':
            self.NAval = self.dtype.type(1 << (8*self.dtype.itemsize - 1))
        # Default NA for floats is NaN
        elif self.dtype.kind == 'f':
            self.NAval = self.dtype.type(np.nan)
        else:
            raise ValueError(f"Undefined NA value for {dtype}")

    def __call__(self, val):
        try:
            return self.dtype.type(self.preprocessor(val))
        except:
            return self.NAval

def u2i(pyint):
    i64 = pd.Series(data=np.zeros(pyint.shape[0], dtype=np.int64), index=pyint.index)
    needsoffset = pyint >= 2**63
    i64.loc[~needsoffset] = pyint.loc[~needsoffset].astype(np.int64)
    i64.loc[needsoffset] = (pyint.loc[needsoffset] - 2**64).astype(np.int64)
    return i64

def pyIP2np(intip):
    ip1 = pd.Series(data=np.zeros(intip.shape[0], dtype=np.int64), index=intip.index)
    ip2 = pd.Series(data=np.zeros(intip.shape[0], dtype=np.int64), index=intip.index)
    isv6 = intip > 2**32
    isv4 = (intip > 0) & (~isv6)
    ip1.loc[isv4] = intip.loc[isv4].astype(np.int64)
    ip1.loc[isv6] = u2i(intip.loc[isv6].apply(lambda x: x >> 64))
    ip2.loc[isv6] = u2i(intip.loc[isv6].apply(lambda x: x & (2**64 - 1)))
    return ip1, ip2

def split_IP(df, IPcolumns, suffix1='', suffix2='2'):
    outcols = set()
    for col in IPcolumns:
        hi, lo = pyIP2np(df[col].apply(lambda x:int(ip_address(x.strip()))))
        df[col+suffix1] = hi
        df[col+suffix2] = lo
        outcols.add(col+suffix1)
        outcols.add(col+suffix2)
    return df, outcols

# Encodes string w/UTF-8 to get an accurate byte count
def to_bytes(string, encoding="utf-8"):
    return string.encode(encoding=encoding)

def pack_strings(column, encoding="utf-8"):
    ''' Takes pandas column w/ data of type str, converts it into two arrays:
        an array of null-separated 'strings', and an array of associated
        offsets. Assumes strings are encoded in utf-8, can be altered if
        necessary using the `encoding` arg.
    '''
    try:
        _to_bytes = partial(to_bytes, encoding=encoding)
        lengths = column.apply(_to_bytes).apply(len).values
        offsets = lengths.cumsum() + np.arange(lengths.shape[0]) - lengths
        totalbytes = lengths.sum() + lengths.shape[0]
        packed = np.zeros(shape=(totalbytes,), dtype=np.uint8)
        for (o, s) in zip(offsets, column.values):
            for i, b in enumerate(s.encode()):
                packed[o+i] = b

    except Exception as e:
        raise e
    return packed, offsets

def write_strings(f, group, packed, offsets, compression=None,  mode='w'):
    ''' Stores strings as encoded in packed, offsets in hdf5 group.
    '''
    try:
        g = f.create_group(group)
        g.attrs["segmented_string"] = np.bool(True)
        g.create_dataset('values', data=packed, compression=compression)
        g.create_dataset('segments', data=offsets, compression=compression)
        g['values'].attrs['dtype'] = np.string_(np.dtype(np.uint8).str)
        g['segments'].attrs['dtype'] = np.string_(np.dtype(np.int64).str)
        # There's not really an easy NA value to encode, so passing on that.
    except TypeError as e:
        print(f"Error creating group {group} in file {f.filename}")
        print(e)

def read_strings(group):
    if not isinstance(group, h5py.Group):
        raise TypeError(f"String array must be an HDF5 group; got {type(group)}")
    if 'segments' not in group or 'values' not in group:
        raise ValueError(f"String group must contain 'segments' and 'values' datasets; got {group.keys()}")
    values = group['values']
    offsets = np.hstack((group['segments'], values.shape[0]))
    lengths = np.diff(offsets) - 1
    res = [''.join(chr(b) for b in values[o:o+l]) for (o, l) in zip(offsets, lengths)]
    return res

def _normalize_dtype(col, dtype, typeonly=False):
    ''' Transforms data to <dtype> specified. If dtype is a Converter, 
        transforms data to match desired type (as described in Converter).
        If data is string data, then packs strings into custom format before
        returning.
    '''
    dtypes, data = None, None
    if isinstance(dtype, Converter):
        if typeonly:
            dtypes = (dtype.dtype,)
        else:
            data = col.astype(dtype.dtype).values
        pdstr = dtype.dtype.str
        NAvalue = dtype.NAval
    # pack_strings returns uint8s and int64s.
    elif dtype == np.str_ or (dtype is None and col.dtype == 'O'):
        if typeonly:
            dtypes = (np.uint8().dtype, np.int64().dtype)
        else:
            data = pack_strings(col)
        pdstr = 'str'
        NAvalue = ""
    elif dtype is not None:
        try:
            if typeonly:
                dtypes = (col.astype(dtype).values.dtype,)
            else:
                data = col.astype(dtype).values
        except Exception as e:
            print(f"Could not coerce {col.name} to {dtype}\n{col}")
            raise e
        if callable(dtype):
            pdstr = dtype().dtype.str
        else:
            pdstr = dtype.str
        NAvalue = np.nan
    # Convert datetime64 to int64 values, but preserve the original
    # dtype so that it can survive a round-trip
    elif col.dtype.kind == 'M':
        if typeonly:
            dtypes = (np.int64().dtype,)
        else:
            data = col.astype(np.int64).values
        pdstr = col.dtype.str
        NAvalue = pd.NaT.value
    else:
        if typeonly:
            dtypes = (col.values.dtype,)
        else:
            data = col.values
        pdstr = col.dtype.str
        NAvalue = np.nan
    return dtypes or data, pdstr, NAvalue

def col2dset(name, col, f, dtype=None, compression=None):
    '''Write a pandas Series <col> to dataset <name> in HDF5 file <f>.
    Optionally, specify a dtype to convert to before writing. Compression
    with gzip is also supported.'''
    data, pdstr, NAvalue = _normalize_dtype(col, dtype)
    # Write the dataset to the file
    if dtype == np.str_ or (dtype is None and col.dtype == 'O'):
        write_strings(f, name, data[0], data[1], compression=compression)
    else:
        try:
            dset = f.create_dataset(name, data=data, compression=compression)
            # Store the normalized dtype as an attribute of the dataset
            dset.attrs['dtype'] = np.string_(pdstr)
            dset.attrs['NAvalue'] = NAvalue
        except TypeError as e:
            print(f"Error creating dataset {name} in file {f.filename}")
            print(e)

def df2hdf(filename, df, internal_dtypes={}, compression=None, attempts=10, interval=30, raise_errors=False):
    '''Write a pandas DataFrame <df> to a HDF5 file <filename>. Optionally,
    specify internal_dtypes for converting the columns and a compression to use.'''
    for _ in range(attempts):
        try:
            with h5py.File(filename, 'w') as f:
                for colname in df.columns:
                    col2dset(colname, df[colname], f, dtype=internal_dtypes.get(colname, None), compression=compression)
            return
        except Exception as e:
            print(e)
            if raise_errors:
                raise e
            else:
                sleep(interval)
    # If here, then saving to HDF5 failed
    if os.path.exists(filename):
        os.remove(filename)
    print(f"Error saving converted file to HDF5 {filename}:")

 
def convert_file(args):
    '''Convert one file from CSV to HDF5.'''
    filename, outdir, extension, options, internal_dtypes, compression, transforms = args
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            transformer = options.get('transformer', lambda x:x)
            df = transformer(pd.read_csv(filename, **options))
    except Exception as e:
        print(f"Error converting {filename}:")
        print(e)
        return
    for transform in transforms:
        df, _ = transform(df)
    newname = os.path.splitext(os.path.basename(filename))[0] + extension
    df2hdf(os.path.join(outdir, newname), df, internal_dtypes, compression)

def _get_valid_columns(filename, options, internal_dtypes, transforms):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=pd.errors.ParserWarning)
            predf = pd.read_csv(filename, nrows=1000, **options)
    except Exception as e:
        print(f"Error reading sample DataFrame:")
        print(e)
        return []
    required = set()
    df = predf.copy()
    for transform in transforms:
        # Transforms must 1) append columns to end, and 2) return names of columns added/altered
        df, outcols = transform(df)
        required |= outcols
    validcols = []
    pdstrs = []
    hdftypes = []
    NAvalues = []
    for i, col in enumerate(df.columns):
        dt = internal_dtypes.get(col, None)
        dtypes, pdstr, NAvalue = _normalize_dtype(df[col], dt, typeonly=True)
        try:
            for dtype in dtypes:
                h5py.h5t.py_create(dtype, logical=True)
        except TypeError as e:
            if col in required:
                raise TypeError(f'Column {col} is required but dtype "{df[col].values.dtype}" has no HDF5 equivalent.') from e
            else:
                print(f'Ignoring column {col} because dtype "{df[col].values.dtype}" has no HDF5 equivalent.')
                continue
        validcols.append(i)
        pdstrs.append(pdstr)
        for dtype in dtypes:
            hdftypes.append(dtype.str)
        NAvalues.append(NAvalue)
    validnames = df.columns[validcols]
    print("Columns to be extracted:")
    maxname = max(map(len, validnames))
    maxnorm = max(map(len, pdstrs))
    maxhdf = max(map(len, hdftypes))
    rowfmt = f"{{:<{maxname}}} {{:<{maxnorm}}} {{:<{maxhdf}}} {{}}"
    print(rowfmt.format('Column', 'pd type', 'hdf5 type', 'NA val'))
    for name, norm, hdf, NA in zip(validnames, pdstrs, hdftypes, NAvalues):
        print(rowfmt.format(name, norm, hdf, NA))
    #print(df[df.columns[validcols]].info())
    used = options.get('usecols', list(range(predf.shape[1])))
    if len(used) > 0 and isinstance(used[0], int):
        used = [predf.columns[u] for u in used]
    new_usecols = [used[v] for v in validcols[:predf.shape[1]]]
    return new_usecols, set(validnames)


def convert_files(filenames, outdir, extension, options, compression, pool):
    '''Convert all CSV files in <filenames> to HDF5 files, replacing their
    extensions with <extension> and saving them in <outdir>. Formatting
    and dtype information for the data source is in <options>.
    Conversion runs in parallel unless pool=None.'''
    if not os.path.isdir(outdir) or not os.access(outdir, os.W_OK):
        raise OSError(f"Permission denied: {outdir}")
    internal_dtypes = options.get('dtype', {})
    converters = options.get('converters', {})
    if 'transforms' in options:
        transforms = options['transforms']
        del options['transforms']
    else:
        transforms = []
    for field, conv in converters.items():
        if isinstance(conv, Converter):
            internal_dtypes[field] = conv
    usecols, validnames = _get_valid_columns(filenames[0], options, internal_dtypes, transforms)
    if len(usecols) == 0:
        raise TypeError("No columns found with HDF5-compatible dtype")
    options['usecols'] = usecols
    # LTL: Seems like we're preserving internal_dtypes, but, unfortunately, not the data we just created. This might need to be figured out.
    arglist = zip(filenames, repeat(outdir), repeat(extension), repeat(options), repeat(internal_dtypes), repeat(compression), repeat(transforms))
    if pool is None:
        _ = list(tqdm(map(convert_file, arglist), total=len(filenames)))
    elif hasattr(pool, 'imap_unordered'):
        _ = list(tqdm(pool.imap_unordered(convert_file, arglist), total=len(filenames)))
    else:
        _ = list(pool.map(convert_file, arglist))


#############
# Reading HDF5 data into a DataFrame
def read_hdf(filenames, columns=None, progbar=True):
    '''Read many HDF5 files into one DataFrame. All HDF5 files must 
    have the same schema: i.e. the number, names, and dtypes of the 
    constituent datasets must match. Each HDF5 dataset will create 
    a column of the same name in the DataFrame. If the HDF5 dataset 
    has a string attribute named 'dtype', it will be used as the 
    column dtype. Otherwise, the dtype will be inferred from the 
    native HDF5 type.

    This function is faster and more memory efficient than reading 
    each HDF5 file into its own DataFrame and calling pandas.concat, 
    because this function does not incur any copies.'''

    if isinstance(filenames, str) or isinstance(filenames, bytes):
        filenames = glob(filenames)
    # Allocate an empty dataframe and get the row offsets of each file
    df, offsets, lengths = _hdf_alloc(filenames, columns)
    if progbar:
        iterator = tqdm(zip(filenames, offsets), total=len(filenames))
    else:
        iterator = zip(filenames, offsets)
    for fname, ind in iterator:
        # Read the data directly into the empty dataframe
        _hdf_insert(fname, df, ind)
    if columns is not None:
        return df[columns]
    else:
        return df

# Threading does not get any speedup, so this function is not exposed
def _read_hdf_multithreaded(df, filenames, offsets):
    jobs = [Thread(target=_hdf_insert, args=(fname, df, ind)) for fname, ind in zip(filenames, offsets)]
    for j in jobs:
        j.start()
    for j in tqdm(jobs):
        j.join()
    
def _hdf_alloc(filenames, columns):
    if len(filenames) == 0:
        raise ValueError("Need at least one file to allocate a DataFrame")
    # Get the reference dtypes from the first file
    dtypes, _, NAvalues = _get_column_metadata(filenames[0], columns)
    offsets = [0]
    lengths = []
    for fn in filenames:
        # Ensure each file has same number of columns and same dtypes as reference
        thisdtypes, thislength, _ = _get_column_metadata(fn, columns)
        if len(thisdtypes) != len(dtypes):
            raise ValueError("Number of columns must be constant across all files")
        if thisdtypes != dtypes:
            raise ValueError("Columns have inhomogenous names or dtypes across files")
        offsets.append(offsets[-1] + thislength)
        lengths.append(thislength)
    # last entry is total length, remove it so it won't be used as offset
    total = offsets.pop()
    # Allocate uninitialized memory for columns
    column_dict = {col:pd.Series(np.empty(shape=(total,), dtype=dtypes[col])) for col in dtypes}
    df = pd.DataFrame(column_dict)
    df.NAvalues = NAvalues

    return df, offsets, lengths

def _get_column_metadata(filename, columns):
    dtypes = {}
    length = -1
    NAvalues = {}
    with h5py.File(filename, 'r') as f:
        if columns is None:
            # Use HDF5 dataset names as column names
            columns = set(f.keys())
        else:
            columns = set(columns) & set(f.keys())
        for colname in columns:
            dset = f[colname]
            if isinstance(dset, h5py.Group):
                dtypes[colname] = 'str'
                assert 'segments' in dset and 'values' in dset, "Column is HDF5 Group but does not have segments and values like a string"
                thislen = dset['segments'].shape[0]
            else:
                # Check for user-specified dtype in dset attribute,
                # otherwise use native HDF5 dtype.
                dt = dset.attrs.get('dtype', dset.dtype).decode()
                if dt == 'category':
                    dtypes[colname] = dset.dtype
                    relpath = os.path.join(os.path.dirname(filename), dset.attrs['codemap_relpath'].decode())
                    codemaps[colname] = os.path.realpath(relpath)
                else:
                    dtypes[colname] = dt
                thislen = dset.shape[0]
            # Set length on the first column, and test that
            # all other columns have the same length
            if length == -1:
                length = thislen
            else:
                assert length == thislen, f'Columns of unequal length in {filename}'
            NAvalues[colname] = dset.attrs.get('NAvalue', np.nan)
    return dtypes, length, NAvalues

def _hdf_insert(filename, df, index):
    with h5py.File(filename, 'r') as f:
        # _hdf_alloc has already guaranteed that file has correct column names
        for colname in df.columns:
            if df[colname].dtype.name == 'object':
                size = f[colname]['segments'].shape[0]
                df.loc[index:index+size, colname] = read_strings(f[colname])
            else:
                dset = f[colname]
                size = dset.shape[0]
                # Read the dataset directly into the uninitialized column
                df[colname].values[index:index+size] = dset[:]
            
