import arkouda as ak
from typing import cast
import math

def dot(u: ak.pdarray, v: ak.pdarray):
    repMsg = ak.generic_msg(cmd='dot', args=f"{u.name} {v.name}")
    return ak.parse_single_value(cast(str, repMsg))


# magnitude/L_2-norm of arkouda pdarray
def magnitude(u: ak.pdarray):
    return math.sqrt(dot(u, u))


# cosine distance of two arkouda pdarrays
# should function similarly to scipy.spatial.distance.cosine
def cosine(u: ak.pdarray, v: ak.pdarray):
    return 1.0 - dot(u, v) / (magnitude(u) * magnitude(v))


# euclidean distance of two arkouda pdarrays
# should function similarly to scipy.spatial.distance.euclidean
def euclidean(u: ak.pdarray, v: ak.pdarray):
    return math.sqrt(dot(u, u) + dot(v, v) - 2*dot(u, v))