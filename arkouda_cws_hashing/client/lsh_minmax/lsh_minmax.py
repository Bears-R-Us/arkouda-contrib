from typeguard import typechecked
from arkouda import pdarray
from arkouda.client import generic_msg
from arkouda.pdarrayclass import parse_single_value
from arkouda.strings import Strings
from typing import cast, Tuple, Union
import math

@typechecked
def lshMinMax(offsets: pdarray, elts: pdarray, weights: pdarray, zbit: bool, hashes: int(64)) -> Union[Strings, Tuple]:
    repMsg = generic_msg(cmd='lshMinMax', args=f"{offsets.name} {elts.name} {weights.name} {zbit} {hashes}")
    if zbit:
        arrays = repMsg.split("+", maxsplit=2)
        return Strings.from_return_msg("+".join(arrays[0:2])), create_pdarray(arrays[2])
    else:
        return Strings.from_return_msg(repMsg)
