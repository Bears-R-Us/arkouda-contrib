# Arkouda Distance

This is a client only implementation of distance functionality using Arkouda. Thus, all code is python and uses only server elements currently included in the main arkouda repository. 

## Functionality Implemented

- `dot()` - Compute the dot product of 2 Arkouda `pdarrays`.
- `magnitude()` - Compute the magnitude/l2-norm of Arkouda `pdarray`.
- `cosine()` - Compute the cosine distance of 2 Arkouda `pdarrays`.
- `euclidean()` - Compute the Euclidean distance of 2 Arkouda `pdarrays`.

## Usage

Arkouda must be installed prior to utilization.

```commandline
pip install arkouda
```

In your code,

```python
import arkouda_distance
```