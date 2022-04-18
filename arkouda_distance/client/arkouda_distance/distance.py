#!/usr/bin/env python3

from arkouda import pdarray
from arkouda.pdarrayclass import sum

import math
from typeguard import typechecked


# dot product or two arkouda pdarrays
@typechecked
def dot(u: pdarray, v: pdarray):
    return sum(u * v)


# magnitude/L_2-norm of arkouda pdarray
@typechecked
def magnitude(u: pdarray):
    return math.sqrt(dot(u, u))


# cosine distance of two arkouda pdarrays
# should function similarly to scipy.spatial.distance.cosine
@typechecked
def cosine(u: pdarray, v: pdarray):
    return 1.0 - dot(u, v) / (magnitude(u) * magnitude(v))


# euclidean distance of two arkouda pdarrays
# should function similarly to scipy.spatial.distance.euclidean
@typechecked
def euclidean(u: pdarray, v: pdarray):
    return math.sqrt(dot(u, u) + dot(v, v) - 2*dot(u, v))