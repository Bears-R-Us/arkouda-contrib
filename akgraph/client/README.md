# `akgraph`

A library for manipulating graphs in `arkouda`.

##  About

`akgraph` contains a growing list of graph algorithms implemented using
`arkouda` operations. The algorithms typically assume that graphs are simple
directed-graph, unweighted and lacking self loops.  Unless otherwise specified,
all algorithms take arrays representing source and destination nodes of each
edge. Node labels must be consecutive integers in [0..n-1].  Other algorithms
will only work with undirected graphs (represented by symmetric edge-lists).
Some algorithms may have more or fewer requirements as indicated by module or
function docstrings.

`akgraph` also contains scripts for munging data

## Installation & Updates

These instructions assume you already have `arkouda` and `akutil` installed
on your system.

todo: install instructions

## Tests

`akgraph`'s test suite is rudimentary.  To perform the tests one executes
the individual module and provides a valid `arkouda` host name.  Some test
require significant memory so make sure you have enough.

## Future Work

`akgraph` currently uses edge-lists as the fundamental data structure for
representing graphs.  It may be worth codifying this in a `Graph` class with
relevant methods.  Integration with `aksparse` is also necessary to expand
functionality.  Input Validation in the various functions.  Moving more general
or tangential tools to a different repository.  Adding support for weighted,
directed and multi-graphs as appropriate.
