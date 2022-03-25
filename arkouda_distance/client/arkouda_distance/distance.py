#!/usr/bin/env python3

import arkouda as ak
import math


# dot product or two arkouda pdarrays
def dot(u, v):
    if isinstance(u, ak.pdarray) and isinstance(v, ak.pdarray):
        return ak.sum(u * v)
    else:
        raise TypeError("u and v must be pdarrays")


# magnitude/L_2-norm of arkouda pdarray
def magnitude(u):
    if isinstance(u, ak.pdarray):
        return math.sqrt(dot(u, u))
    else:
        raise TypeError("u must be a pdarray")


# cosine distance of two arkouda pdarrays
# should function similarly to scipy.spatial.distance.cosine
def cosine(u, v):
    if isinstance(u, ak.pdarray) and isinstance(v, ak.pdarray):
        return 1.0 - dot(u, v) / (magnitude(u) * magnitude(v))
    else:
        raise TypeError("u and v must be pdarrays")

# euclidean distance of two arkouda pdarrays
# should function similarly to scipy.spatial.distance.euclidean
def euclidean(u, v):
    if isinstance(u, ak.pdarray) and isinstance(v, ak.pdarray):
        return math.sqrt(dot(u, u) + dot(v, v) - 2*dot(u, v))
    else:
        raise TypeError("u and v must be pdarrays")