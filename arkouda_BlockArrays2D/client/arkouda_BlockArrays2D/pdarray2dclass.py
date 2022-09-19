from arkouda.pdarrayclass import *
from typing import cast, List, Sequence
import itertools
import numpy as np # type: ignore
import pandas as pd # type: ignore
from typing import cast, Iterable, Optional, Union
from typeguard import typechecked
from arkouda.client import generic_msg
from arkouda.dtypes import NUMBER_FORMAT_STRINGS, float64, int64, \
     DTypes, isSupportedInt, isSupportedNumber, NumericDTypes, SeriesDTypes,\
    int_scalars, numeric_scalars, get_byteorder, get_server_byteorder
from arkouda.dtypes import dtype as akdtype
from arkouda.pdarrayclass import pdarray, create_pdarray
from arkouda.strings import Strings
from arkouda.logger import getArkoudaLogger

from typeguard import typechecked
import json
import numpy as np # type: ignore
from arkouda.client import generic_msg
from arkouda.dtypes import dtype, DTypes, resolve_scalar_dtype, \
     translate_np_dtype, NUMBER_FORMAT_STRINGS, \
     int_scalars, numeric_scalars, numeric_and_bool_scalars, numpy_scalars, get_server_byteorder
from arkouda.dtypes import int64 as akint64
from arkouda.dtypes import str_ as akstr_
from arkouda.dtypes import bool as npbool
from arkouda.dtypes import isSupportedInt
from arkouda.logger import getArkoudaLogger
from arkouda.infoclass import list_registry, information, pretty_print_information

logger = getArkoudaLogger(name='pdarrayclass')

__all__ = ['array2D', 'randint2D', 'reshape']

class pdarray2D(pdarray):
    objtype = 'pdarray2D'

    def __getitem__(self, key):
        if np.isscalar(key) and resolve_scalar_dtype(key) == 'int64':
            orig_key = key
            if key < 0:
                # Interpret negative key as offset from end of array
                key += self.size
            if (key >= 0 and key < self.size):
                repMsg = generic_msg(cmd="[int2d]", args="{} {}".format(self.name, key))
                return create_pdarray(repMsg)
            else:
                raise IndexError("[int] {} is out of bounds with size {}".format(orig_key,self.size))
        raise TypeError("Unhandled key type: {} ({})".format(key, type(key)))
    
    def _binop(self, other, op : str) -> pdarray:
        """
        Executes binary operation specified by the op string

        Parameters
        ----------
        other : pdarray
        The pdarray upon which the binop is to be executed
        op : str
        The binop to be executed

        Returns
        -------
        pdarray
        A pdarray2D encapsulating the binop result

        Raises
        ------
        ValueError
        Raised if the op is not within the pdarray.BinOps set, or if the
        pdarray sizes don't match
        TypeError
        Raised if other is not a pdarray or the pdarray.dtype is not
        a supported dtype

        """
        # For pdarray subclasses like ak.Datetime and ak.Timedelta, defer to child logic
        if type(other) != pdarray2D:
            return NotImplemented
        if op not in self.BinOps:
            raise ValueError("bad operator {}".format(op))
        # pdarray binop pdarray
        if isinstance(other, pdarray2D):
            if self.size != other.size:
                raise ValueError("size mismatch {} {}".format(self.size,other.size))
            cmd = "binopvv2d"
            args= "{} {} {}".format(op, self.name, other.name)
            repMsg = generic_msg(cmd=cmd,args=args)
            return create_pdarray2D(repMsg)
        # pdarray binop scalar
        dt = resolve_scalar_dtype(other)
        if dt not in DTypes:
            raise TypeError("Unhandled scalar type: {} ({})".format(other, 
                                                                type(other)))

def create_pdarray2D(repMsg : str) -> pdarray2D:
    try:
        fields = repMsg.split()
        name = fields[1]
        mydtype = fields[2]
        size = int(fields[3])
        ndim = int(fields[4])
        # remove comma from 1 tuple with trailing comma
        if fields[5][len(fields[5]) - 2] == ",":
            fields[5] = fields[5].replace(",", "")
        shape = [int(el) for el in fields[5][1:-1].split(',')]
        itemsize = int(fields[6])
    except Exception as e:
        raise ValueError(e)
    logger.debug(("created Chapel array with name: {} dtype: {} size: {} ndim: {} shape: {} " +
                  "itemsize: {}").format(name, mydtype, size, ndim, shape, itemsize))
    return pdarray2D(name, dtype(mydtype), size, ndim, shape, itemsize)

def array2D(val, m, n) -> Union[pdarray, Strings]:
    """
    Generate a 2D pdarray that is of size `m x n` and initialized to the
    value `val`.

    Parameters
    ----------
    val : numeric_and_bool_scalars
        The value to initialize all elements of the 2D array to
    m :  int_scalars
        The `m` dimension of the array to create
    n : int_scalars
        The `n` dimension of the array to create

    Returns
    -------
    pdarray
        A pdarray instance stored on arkouda server
        
    Raises
    ------
    TypeError
        Raised if a is not a pdarray, np.ndarray, or Python Iterable such as a
        list, array, tuple, or deque

    See Also
    --------
    ak.array

    Notes
    -----
    We cannot pass the binary data back for this function since it is optional
    on the server side, which means that its signature must be identical to 
    the regular Arkouda message. Could possibly add a second map that was like
    "arrayCreationMap" or something that handled signatures of that type.    

    Examples
    --------
    >>> ak.array2D(5, 2, 2)
    array([[5, 5],
           [5, 5]])
    
    >>> ak.array2D(True, 3, 3)
    array([[True, True, True],
           [True, True, True],
           [True, True, True]])
    """
    args = ""
    from arkouda.client import maxTransferBytes
    # Only rank 2 arrays currently supported
    if isinstance(val, bool):
        args = f"bool {val} {m} {n}"
    elif isinstance(val, int):
        args = f"int64 {val} {m} {n}"
    elif isinstance(val, float):
        args = f"float64 {val} {m} {n}"

    rep_msg = generic_msg(cmd='array2d', args=args)
    return create_pdarray2D(rep_msg)


def randint2D(low : numeric_scalars, high : numeric_scalars, 
              m : int_scalars, n : int_scalars, dtype=int64, seed : int_scalars=None) -> pdarray:
    """
    Generate a 2 dimensional pdarray of randomized int, float, or bool values in a 
    specified range bounded by the low and high parameters.

    Parameters
    ----------
    low : numeric_scalars
        The low value (inclusive) of the range
    high : numeric_scalars
        The high value (exclusive for int, inclusive for float) of the range
    m :  int_scalars
        The `m` dimension of the array to create
    n : int_scalars
        The `n` dimension of the array to create
    dtype : Union[int64, float64, bool]
        The dtype of the array
    seed : int_scalars
        Index for where to pull the first returned value
        
    Returns
    -------
    pdarray
        Values drawn uniformly from the specified range having the desired dtype
        
    Raises
    ------
    TypeError
        Raised if dtype.name not in DTypes, size is not an int, low or high is
        not an int or float, or seed is not an int
    ValueError
        Raised if size < 0 or if high < low

    Notes
    -----
    Calling randint with dtype=float64 will result in uniform non-integral
    floating point values.

    Examples
    --------
    >>> ak.randint2D(0, 10, 2, 2)
    array([[3, 6],
           [8, 4]])
    >>> ak.randint2D(0, 1, 2, 2, dtype=ak.bool)
    array([[True, True],
           [False, True]])
    >>> ak.randint2D(0, 1, 2, 2, dtype=ak.float64)
    array([[0.3793842821625909, 0.97508925511529132],
           [0.12608488822540775, 0.23591727525338338]])    
    """
    if high < low:
        raise ValueError("size must be > 0 and high > low")
    dtype = akdtype(dtype) # normalize dtype
    # check dtype for error
    if dtype.name not in DTypes:
        raise TypeError("unsupported dtype {}".format(dtype))
    lowstr = NUMBER_FORMAT_STRINGS[dtype.name].format(low)
    highstr = NUMBER_FORMAT_STRINGS[dtype.name].format(high)

    repMsg = generic_msg(cmd='randint2d', args='{} {} {} {} {} {}'.\
                         format(dtype.name, lowstr, highstr, m, n, seed))
    return create_pdarray2D(repMsg)

def reshape(obj : pdarray, newshape : Union[numeric_scalars, tuple]) -> pdarray:
    """
    Reshape

    Parameters
    ----------
    obj : pdarray
        The pdarray to reshape.
    newshape : Union[numeric_scalars, tuple]
        The shape to resize the array to. This could either be a single
        value to reshape to a 1D array or a tuple of 2 values to reshape 
        to a 2D array.
        
    Returns
    -------
    pdarray
        A new pdarray containing the same elements of `obj`, but with a
        new domain.
        
    Raises
    ------
    ValueError
        Raised if `newshape` contains more than 2 elements or the supplied
        new shape can't fit all elements of original array.

    Notes
    -----
    Setting one of the values in `newshape` to `-1` will infer the correct
    length to pass to ensure that the new array fits the correct number of
    elements.

    Examples
    --------
    >>> a = ak.array([1,2,3,4])
    >>> ak.reshape(a, (2,2))
    array([[1, 2],
           [3, 4]])
    >>> ak.reshape(a, (-1,1))
    array([[1],
           [2],
           [3],
           [4]]))
    """
    initial_size = obj.size
    m = 0
    n = 0

    if isinstance(newshape, tuple):
        if len(newshape) != 2:            
            raise ValueError("more than 2 dimensions provided for newshape: {}".format(len(newshape)))
        m = newshape[0]
        n = newshape[1]
        if m == -1:
            m = int(initial_size/n)
        if n == -1:
            n = int(initial_size/m)
        if m*n != initial_size:
            raise ValueError("size mismatch, 2D dimensions must result in array of equivalent size: {} != {}".format(obj.size,m*n))
        rep_msg = generic_msg(cmd='reshape2D', args=f"{obj.name} {m} {n}")
        return create_pdarray2D(rep_msg)
    else:
        if newshape == -1 or newshape == initial_size:
            rep_msg = generic_msg(cmd='reshape1D', args=f"{obj.name}")
            return create_pdarray2D(rep_msg)
        else:
            raise ValueError("size mismatch, resizing to 1D must either be -1 or array size: provided: {} array size: {}".format(newshape, obj.size))
