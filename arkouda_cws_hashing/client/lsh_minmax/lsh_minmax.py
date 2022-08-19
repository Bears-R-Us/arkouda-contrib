from typeguard import typechecked
from arkouda import pdarray
from arkouda.client import generic_msg
from arkouda.pdarrayclass import parse_single_value
from typing import cast
import math

@typechecked
def lshMinMax(o: pdarray, s: pdarray, w: pdarray, h: uint(8)):
    repMsg = generic_msg(cmd='lshMinMax', args=f"{o.name} {s.name} {w.name} {h.name}")
    return parse_single_value(cast(str, repMsg))
