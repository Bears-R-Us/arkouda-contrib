#!/usr/bin/env python3
"""Functions for helping solve sparse matrix equations."""
__all__ = [
    'diagonal_preconditioner',
    'eye',
    'EPS',
    'FMAX',
    'inner',
    'matvec_from_coo',
    'norm',
    'Operator',
]


from typing import Callable, Optional, Tuple

import numpy as np

import arkouda as ak


# floating point arithmetic constants for this platform
EPS = np.finfo(np.float64).eps
FMAX = np.finfo(np.float64).max
Operator = Callable[[ak.pdarray], ak.pdarray]


def inner(u: ak.pdarray, v: ak.pdarray) -> float:
    """Inner product of two vectors."""
    return ak.sum(u * v)


def norm(v: ak.pdarray) -> float:
    """Length of vector."""
    return np.sqrt(inner(v, v))


def eye(x: ak.pdarray) -> ak.pdarray:
    """Identity operator."""
    return x[:]


def diagonal_preconditioner(
    R: ak.pdarray,
    C: ak.pdarray,
    V: Optional[ak.pdarray],
) -> Operator:
    """
    Create a preconditing operator based on the diagonals.

    This is useful when you're trying to solve systems involving diagonal
    dominant matrices (like graph Laplacians).

    Parameters
    ----------
    R : ak.pdarray
        row indices, non-negative integers
    C : ak.pdarray
        column indices, non-negative integers
    V : ak.pdarray (optional)
        values (default to 1)

    Return
    ------
    P : Operator
        like getting multiplied by the inverse diagonals of the matrix
    """
    mask = (R == C)
    r, c, v = R[mask], C[mask], 1.0 / V[mask]
    def inv_diag(x: ak.pdarray) -> ak.pdarray:
        """Jacobi preconditioner."""
        return x * v

    return inv_diag


def matvec_from_coo(
    R: ak.pdarray,
    C: ak.pdarray,
    V: Optional[ak.pdarray] = None,
    shape: Optional[Tuple[int, int]] = None
) -> Operator:
    """
    Return an operator representing matrix-vector multiplication by A.

    Input are arrays representing COO format of a sparse matrix.

    Parameters
    ----------
    R : ak.pdarray
        row indices, non-negative integers
    C : ak.pdarray
        column indices, non-negative integers
    V : ak.pdarray (optional)
        values (default to 1)
    shape : (int, int) Optional
        number of (rows, columns) in matrix. default to square matrix based on
        max value in R, C.

    Return
    ------
    matvec : Operator
        function calculating y = Ax for arbitrary commensurate x
    """
    if R.min() < 0 or C.min() < 0:
        raise ValueError(f"row and column indices must be non-negative")

    if shape is not None:
        if R.max() >= shape[0] or C.max() >= shape[1]:
            raise ValueError(f"bad shape: ({R.max()},{C.max()}) >= {shape}")
        else:
            n, m = shape
    else:
        n = m = max(R.max(), C.max()) + 1

    if V is None:
        V = ak.zeros(R.size, dtype='float') + 1

    gr = ak.GroupBy(R)

    def matvec(x: ak.pdarray) -> ak.pdarray:
        """Compute matrix-vector product, y = Ax."""
        if x.size != m:
            raise ValueError(f"size mismatch: ({n}, {m}) x ({x.size}, 1)")
        y = ak.zeros(n)
        y[gr.unique_keys] = gr.sum(x[C] * V)[1]
        return y

    return matvec

