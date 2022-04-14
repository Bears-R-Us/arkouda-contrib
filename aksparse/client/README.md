# aksparse

A python package that uses arkouda to perform sparse matrix operations.

## Features

`aksparse` contains classes for representing  several common sparse matrix formats (namely CSR, CSC and COO). 
Objects made with these classes can be used to perform basic matrix arithmetic,
including scalar multiplication, sparse matrix-dense vector multiplication, and 
sparse matrix-sparse matrix multiplication and addition.

These classes are backed by `arkouda` GroupBy objects and arrays, and despite some key differences, 
are effectively a pared-down, distributed version of scipy's sparse matrices.

Further development to bring it a little closer to parity with scipy's feature offering is hoped for, if not
presently planned.


## Getting Started

This explains how to use `aksparse`.

### Installing

The `aksparse` package may recieve updates from the community, so to ensure you can get those updates easily, the best way to install it is by cloning the repository and installing it in editable, or development, mode with `-e`. If you are using a shared python distribution that you do not administer, you will also need to specify the `--user` option to install locally. The pip command will install all dependencies except `arkouda`. If needed, be sure to load the correct Python modules, say `module load conda` for example.


### Updating

To apply the latest updates to the `aksparse` package, simply pull the repository:

```bash
cd aksparse
git pull
```

New or modified code will automatically be available when you restart Python and `import aksparse`.

### Usage

Once you have installed `aksparse`, you can simply

`import aksparse as aksp`

Don't forget to also import `arkouda`:

`import arkouda as ak`

## Contributing

For new features, create an appropriately named branch for the feature you want to implement. Once you've written and tested it, submit a merge request. Once it goes through a code review, and assuming it's a useful feature, it will get merged.

If you want to make big changes that will not play well with the main branch, you are welcome to fork the repository.

## Dependencies

Except for `arkouda`, all of these dependencies will be automatically installed, if not already present, by the `pip` command above.

* `pandas`
* `numpy`
* `arkouda`
