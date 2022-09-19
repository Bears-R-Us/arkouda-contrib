from typeguard import typechecked
from arkouda import pdarray
from arkouda.client import generic_msg
from arkouda.pdarrayclass import parse_single_value
from typing import cast
import math

@typechecked
def dot(u: pdarray, v: pdarray):
    repMsg = generic_msg(cmd='dot', args={"array": u, "vector": v})
    return parse_single_value(cast(str, repMsg))


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