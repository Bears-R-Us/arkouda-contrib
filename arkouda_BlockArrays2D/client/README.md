# Arkouda 2 Dimensional Arrays

This is an implementation of 2 dimensional pdarrays in Arkouda.

## Functionality implemented

- random array generation
  - ak2d.randint2D(0,10,2,2)
    - generates a random 2x2 array with random element values ranging from 0-10
  - ak2d.reshape(my4ElemPdarray, (2,2))
    - reshapes a flat, 4 element pdarray to be a 2d array of size 2x2
  - my2DPdarray[1]
    - returns the row of index 1 in the pdarray (which can then be indexed, i.e., my2DPdarray[1][3])
  - my2DPdarray + my2DPdarray
    - binary operations are supported on multi dimensional pdarrays

## Usage

```commandline
pip install arkouda
```

In your code:

```python
import arkouda_BlockArrays2D as ak2d
```
