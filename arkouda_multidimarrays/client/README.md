# Arkouda Multi Dimensional Arrays

This is an implementation of multi dimensional pdarrays in Arkouda.

## Functionality implemented

- random array generation
  - ak2d.randint2d(0,10,2,2)
    - generates a random 2x2 array with random element values ranging from 0-10
  - ak2d.reshape(my4ElemPdarray, (2,2))
    - reshapes a flat, 4 element pdarray to be a 2d array of size 2x2
  - my2DPdarray[1] (also, my2DPdarray[1][3])
    - returns the row of index 1 in the pdarray (which can then be indexed)
  - my2DPdarray + my2DPdarray
    - binary operations are supported on multi dimensional pdarrays

## Usage

```commandline
pip install arkouda
```

In your code:

```python
import arkouda_multidimarrays as ak2d
```