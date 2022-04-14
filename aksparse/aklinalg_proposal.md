# Linear Algebra Package for Arkouda

None of these ideas should be groundbreaking to the readers but I thought they
should be put in one place for reference and refinement by whoever takes up this
project.

We should have another arkouda package called `aklinalg`

## General Functionality

Basically, I think we should try to recreate as much of `scipy.sparse`
functionality as we can in Arkouda and have some facilities for dense matrices
as well. The `aksparse` library is a good first step towards this but I'm
envisioning something a lot more mature. The basic data structures would be.

- [ ] CSR matrix class
- [ ] CSC matrix
- [ ] COO matrix
- [ ] Diagonal Formats
- [ ] Dense Matrices - in the use cases I envision. These will typically be
  skinny matrices (10 ** 9, 10-100)

These formats should all implement the following binary operations

- [ ] `dot(A, B)` (or `A @ B`) Matrix multiplicaiton
- [ ] `mult(A, B)` (or `A * B`) Elementwise Matrix Multiplication aka Hadamard Product
- [ ] `add(A, B)` (or `A + B`) Elementwise Addition

The binary operators should work when the operands are compatibly shaped members of

- [ ] numpy.ndarrays
- [ ] ak.pdarrays
- [ ] AK Dense Matrices
- [ ] AK Sparse Matrices

or scalars in the case of `mult()` and `add()`.

I also think there should be an investigation of how much of the indexing and
slicing that `scipy.sparse` has could be ported to these different formats. It's
often the case in graph algorithms that you only need to do a few whole graph
operations before focusing on denser subgraphs.

## Equation Solving

In addition to these basic elements, I suggest merging in the `aksolve` library
which has a bunch of functions (that can definitely be improved and expanded) for
solving
```
  A @ x == b
```
With a few extra bells and whistles. Some work will have to be done to prove
whether or not these methods are actually computationally feasible for the data
we have, but if so, that'd be neat! If it's not feasible, we'll have to look at
approximation methods. Or if there are special classes of matrices that work
well (Graph Laplacians jump to mind).

## Eigenvalue Problems a.k.a. Arkouda ARPACK

The next class of problems, I'm more sure is within the reach of Arkouda's
capabilities. That is eigenvalue problem:
```
  A @ x == c * x
```
This has immediate uses in the form of spectral graph clustering, PCA and SVD.
The reason I'm so confident that this works is that Power Iteration methods like
PageRank, and Eigenvector Centrality are among the fastest (and best scaling)
methods in the akgraph library. If you just have to do a few 10s of
SparseMatXVec operations, you can be reasonably sure that the algorithm will
complete in human time. Using Arnoldi or Lanzcos methods, it should be possible
to do exactly this.

A third and even more immediate application would be calculating Triangle
Centrality for a graph. The computational heart of this algorithm could be
accomplished with.
```
  (A @ A) * A
```

## Doing Funky Algebra

Finally, as a stretch goal, The utility of the whole library could probably be
expanded if we investigated how to generalize the algebras that we're using for
our operations (a la GraphBLAS) some of the algorithms in `akgraph` take exactly
this approach. If it was available more trivially in `aklinalg` by calling
```
  dot(A, B, 'mult_op', 'add_op')
```
We'd be cooking. A lot of that functionality is already sort of built into
Arkouda's binops and reductions (but we can always make it easier to use and ask
for more).
