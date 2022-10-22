from typeguard import typechecked
from arkouda import pdarray
from arkouda.client import generic_msg
from arkouda.pdarrayclass import pdarray, create_pdarray
from arkouda.strings import Strings
from typing import cast, Tuple, Union
import math

@typechecked
def lshMinMax(offsets: pdarray, elts: pdarray, weights: pdarray, zbit: bool, hashes: int(64)) -> Union[Strings, Tuple]:
    repMsg = generic_msg(cmd='lshMinMax',
                         args={"offsets": offsets,
                               "elts": elts,
                               "weights": weights,
                               "zbit": zbit,
                               "hashes": hashes})
    if zbit:
        arrays = repMsg.split("+", maxsplit=1)
        return create_pdarray(arrays[0]), create_pdarray(arrays[1])
    else:
        return Strings.from_return_msg(repMsg)
