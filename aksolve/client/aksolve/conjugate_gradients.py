#!/usr/bin/env python3
"""Iterative Conjugate Gradients Method solver sparse Ax = b."""
__all__ = ['cg']


from typing import Optional, Tuple

import numpy as np

import arkouda as ak

from aksolve.util import eye, EPS, inner, norm, Operator


def cg(
    matvec: Operator,
    b: ak.pdarray,
    x_start: Optional[ak.pdarray] = None,
    precon: Operator = eye,
    max_iter: int = 100,
    tol: float = 1.0e-6,
    irestart: Optional[int] = None,
    verbose: bool = False,
) -> Tuple[ak.pdarray, int, int, float]:
    """
    Solve Ax = b by conjugate gradients.

    A must be a symmetric, positive-definite matrix.

    Parameters
    ----------
    matvec : Operator
        function returning the product Ay for a given y
    b : ak.pdarray
        right hand side of desired equation
    x_start : { ak.pdarray | None }
        initial guess at solution
    precon : Operator (default `eye`)
        preconditioner for A.  This should approximate the inverse of A.
        Effective preconditioning dramatically improves the rate of
        convergence.  Default to identity
    max_iter : int (default 100)
        number of iterations to perform
    tol : float (default 1.0e-6)
        relative stopping tolerance
    irestart : int (default log2(b.size))
        iterations between exact residual recalculation
    verbose : bool (default False)
        print a summary of iterations

    Return
    ------
    x : ak.pdarray
        computed solution
    istop : int
        reason for termination (istop == 4 --> not converged)
    niter : int
        number of iterations
    rnorm : float
        norm of final residual vector

    References
    ----------
    An Introduction to the Conjugate Gradient Method without the Agonizing Pain.
        Jonathan Richard Shewchuk. Edition 1 1/4. 1994-08-04

    https://en.wikipedia.org/wiki/Conjugate_gradient_method
    """
    stop_status = {
        0 : 'RHS is zero vector. x = 0.',
        1 : 'lucky guess, x = x_start.',
        2 : 'converged within machine precision',
        3 : 'converged within specified tolerance',
        4 : 'iteration limit reached. not converged'}

    n = b.size
    if irestart is None: irestart = int(np.log2(n))
    if verbose:
        print('\nEnter Conjugate Gradient Solver.\n')
        print(f"            n = {n}\n"
              f"     max_iter = {max_iter}\n"
              f"     irestart = {irestart}\n"
              f"    tolerance = {tol}\n")

    istop = niter = 0
    rnorm = 0.0 

    if norm(b) < EPS:
        if verbose: print(f'exiting: {stop_status[istop]}')
        return (b, istop, niter, rnorm)

    x = ak.zeros(n)
    if x_start is not None:
        x[:] = x_start[:]
    r = b - matvec(x)
    p = precon(r)
    rnorm = norm(r)
    numer = denom = inner(p, r)

    if rnorm < EPS:
        istop = 1
        if verbose: print(f'exiting: {stop_status[istop]}')
        return (x, istop, niter, rnorm)

    if verbose:
        columns = ['niter', 'rnorm']
        print(' '.join(f'{c:>10}' for c in columns))

    while niter < max_iter and rnorm >= tol and rnorm >= EPS:
        Ap = matvec(p)
        alfa = numer / inner(p, Ap)

        x = x + alfa * p

        if niter % irestart == 0:
            r = b - matvec(x)
        else:
            r = r - alfa * Ap

        rnorm = norm(r)
        s = precon(r)
        numer, denom = inner(r, s), numer
        p = s + (numer / denom) * p
        niter += 1

        if verbose: print(f'{niter:>10} {rnorm:>10.2e}')

    if niter >= max_iter : istop = 4
    if rnorm < tol       : istop = 3
    if rnorm < EPS       : istop = 2

    if verbose:
        print('\nExit Conjugate Gradient Solver.\n')
        print(f'Status: {stop_status[istop]}')
        print(f' niter = {niter}\n'
              f' rnorm = {rnorm:0.3e}\n')

    return (x, istop, niter, rnorm)


