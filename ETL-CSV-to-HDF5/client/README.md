# hdflow: Convert CSV to HDF5

Converting CSV to HDF5 can save a lot of IO time and significant storage space.

## Installation

```bash
pip install [insert git path here]
```

## Using the Converter

Run `csv2hdf` from the command line to convert CSV files to HDF5 files in parallel. Sample usage:

```bash
csv2hdf --format=tag --outdir=/path/to/output/dir/ --extension=.hdf /path/to/csv/input/*.csv
```

The converter will automatically run in parallel using all available cores, unless you specify otherwise using the `--jobs` option.

### Specifying Input Format

The `--format` option selects from a set of formats. There are some predefined formats in `hdflow/example_formats.py`. Using that file as a template, you can add new formats in a local file and pass it on the command line with `--formats-file`.

The only rules that a formats file must follow are:
1. For each format, it must create a dictionary, which will be passed to pandas.read_csv as keyword arguments (see the pandas documentation for a list of available keyword arguments)
2. It must declare a module-level dictionary called "OPTIONS", whose keys are the names of the formats to be defined, and whose values are they corresponding dictionaries of keyword arguments.

A trivial example:

`./myformats.py`
```python
tab_dict = {'delimiter': '\t'}
gzip_dict = {'compression': 'gzip'}
OPTIONS = {'tabbed': tab_dict,
           'gzipped': gzip_dict}
```
With this file, you could call the converter on tab-delimited data like:
```bash
csv2hdf --formats-file=./myformats.py --format=tabbed --outdir=/path/to/output/dir/ /path/to/csv/data/*.csv
```

## Reading HDF5 Files into Pandas

Use `hdflow` to read in files output by the converter as follows:

```python
import hdflow
from glob import glob

hdffiles = glob('/path/to/hdf5/data/*.hdf')
df = hdflow.read_hdf(hdffiles)
```

Pandas already supports reading from a single HDF5 file into a DataFrame, but the method for reading multiple HDF5 files into a single DataFrame (`pd.concat`) is sub-optimal. Using `hdflow` is faster and much more memory efficient.
