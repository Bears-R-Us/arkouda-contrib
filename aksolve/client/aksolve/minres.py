#!/usr/bin/env python3
"""MINimum RESidual iterative solver for Ax = b"""
__all__ = ['minres']


from typing import Optional, Tuple

import numpy as np

import arkouda as ak

from aksolve.util import eye, EPS, FMAX, inner, norm, Operator


def minres(
    matvec: Operator,
    b: ak.pdarray,
    x_start: Optional[ak.pdarray] = None,
    precon: Operator = eye,
    max_iter: int = 100,
    tol: float = 1.0e-6,
    verbose: bool = False
) -> Tuple[ak.pdarray, int, int, float]:
    """
    Use MINimum RESidual iteration to solve Ax=b.

    MINRES minimizes norm(A*x - b) for a real symmetric matrix A.  Unlike the
    Conjugate Gradient method, A can be indefinite or singular.

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
    verbose : bool (default False)
        print a summary of iterations

    Returns
    -------
    x : ak.pdarray
        computed solution
    istop : int
        reason for termination
    niter : int
        number of iterations
    rnorm : float
        norm of final residual vector

    References
    ----------
    Solution of sparse indefinite systems of linear equations,
        C. C. Paige and M. A. Saunders (1975),
        SIAM J. Numer. Anal. 12(4), pp. 617-629.
        https://web.stanford.edu/group/SOL/software/minres/

    This file is a translation of the following SciPy implementation:
        https://github.com/scipy/scipy/blob/master/scipy/sparse/linalg/isolve/minres.py
    Which is a translation of the following MATLAB implementation:
        https://web.stanford.edu/group/SOL/software/minres/minres-matlab.zip
    """
    stop_status = {
        -1 : 'beta2 = 0. If M == I, b and x are eigenvectors',
         0 : 'beta1 = 0. the exact solution is x_start',
         1 : 'solution found within specified tolerance',
         2 : 'least-squared solution within specified tolerance',
         3 : 'converged within machine precision',
         4 : 'converged to an eigenvector',
         5 : 'estimated cond(A) exceeds machine precision',
         6 : 'iteration limit reached',
         7 : 'A not symmetric',
         8 : 'preconditioner not symmetric',
         9 : 'preconditioner not positive-definite'}

    n = b.size
    if verbose:
        print('\nEnter MINimum RESidual Solver.\n')
        print(f"            n = {n}\n"
              f"     max_iter = {max_iter}\n"
              f"    tolerance = {tol}\n")

    istop = niter = 0
    Anorm = Acond = rnorm = ynorm = 0.0

    x = ak.zeros(n)
    if x_start is not None:
        x[:] = x_start[:]
    r1 = b - matvec(x)
    y = precon(r1)
    beta1 = inner(r1, y)

    if beta1 < 0:
        istop = 9
        print(beta1)
        if verbose: print(f'exiting: {stop_status[istop]}')
        return (b, istop, niter, rnorm)
    elif beta1 == 0:
        if verbose: print(f'exiting: {stop_status[istop]}')
        return (x, istop, niter, rnorm)

    beta1 = np.sqrt(beta1)

    #####################
    # check symmetric A #
    #####################
    w = matvec(y)
    r2 = matvec(w)
    s, t = inner(w, w), inner(y, r2)
    z = abs(s - t)
    epsa = (s + EPS) * EPS ** (1.0 / 3.0)
    if z > epsa:
        istop = 7
        if verbose: print(f'exiting: {stop_status[istop]}')
        return (x, istop, niter, rnorm)

    #####################
    # check symmetric P #
    #####################
    r2 = precon(y)
    s, t = inner(y, y), inner(r1,r2)
    z = abs(s - t)
    epsa = (s + EPS) * EPS ** (1.0 / 3.0)
    if z > epsa:
        istop = 8
        if verbose: print(f'exiting: {stop_status[istop]}')
        return (x, istop, niter, rnorm)

    ###################################
    # initialize remaining quantities #
    ###################################
    oldb = 0
    beta = beta1
    dbar = 0
    epsln = 0
    qrnorm = beta1
    phibar = beta1
    rhs1 = beta1
    rhs2 = 0
    tnorm2 = 0
    gmax = 0
    gmin = FMAX
    cs = -1
    sn = 0
    w = ak.zeros(n)
    w2 = ak.zeros(n)
    r2 = r1

    if verbose:
        columns = ['niter', 'rnorm', 'x[0]', 'Comp. LS',
                   'norm(A)', 'cond(A)', 'gbar/|A|']
        print(' '.join(f'{c:>10}' for c in columns))

    #######################
    # main iteration loop #
    #######################
    while niter < max_iter:
        niter += 1

        s = 1.0 / beta
        v = s * y

        y = matvec(v)

        if niter >= 2:
            y = y - (beta / oldb)*r1

        alfa = inner(v, y)
        y = y - (alfa / beta) * r2
        r1 = r2
        r2 = y
        y = precon(r2)
        oldb = beta
        beta = inner(r2 , y)

        if beta < 0:
            istop = 7
            if verbose: print(f'exiting: {stop_status[istop]}')
            return (x, istop, niter, rnorm)

        beta = np.sqrt(beta)
        tnorm2 += alfa**2 + oldb**2 + beta**2

        if niter == 1 and beta / beta1 <= 10 * EPS: istop = -1 # end later

        ################################
        # apply current plane rotation #
        ################################
        oldeps = epsln
        delta = cs * dbar + sn * alfa # delta1 = 0         deltak
        gbar = sn * dbar - cs * alfa  # gbar 1 = alfa1     gbar k
        epsln = sn * beta             # epsln2 = 0         epslnk+1
        dbar = - cs * beta            # dbar 2 = beta2     dbar k+1
        root = np.sqrt(gbar ** 2 + dbar ** 2)
        Arnorm = phibar * root

        ###############################
        # compute next plane rotation #
        ###############################
        gamma = np.sqrt(gbar ** 2 + beta ** 2) # gammak
        gamma = max(gamma, EPS)
        cs = gbar / gamma       # ck
        sn = beta / gamma       # sk
        phi = cs * phibar       # phik
        phibar = sn * phibar    # phibark+1

        ############
        # update x #
        ############
        w1, w2 = w2, w
        w = (v - oldeps * w1 - delta * w2) / gamma
        x = x + phi * w

        ##############################
        # prepare for next iteration #
        ##############################
        gmax = max(gmax, gamma)
        gmin = min(gmin, gamma)
        z = rhs1 / gamma
        rhs1 = rhs2 - delta * z
        rhs2 = - epsln * z

        ##################################
        # estimate norms and convergence #
        ##################################
        Anorm = np.sqrt(tnorm2)
        ynorm = norm(x)
        epsa = Anorm * EPS
        epsx = Anorm * ynorm * EPS
        epsr = Anorm * ynorm * tol
        diag = epsa if gbar == 0 else gbar
        qrnorm = phibar
        rnorm = qrnorm
        if ynorm == 0 or Anorm == 0:
            test1 = np.inf
        else:
            test1 = rnorm / (Anorm * ynorm) # ||r||  / (||A|| ||x||)
        if Anorm == 0:
            test2 = np.inf
        else:
            test2 = root / Anorm # ||Ar|| / (||A|| ||r||)
        Acond = gmax / gmin     # estimate cond(A)

        ##########################
        # test stopping criteria #
        ##########################
        if istop == 0:
            t1, t2 = 1 + test1, 1 + test2 # These tests work if tol < EPS
            if niter >= max_iter      : istop = 6
            if Acond >= 0.1 / EPS     : istop = 4
            if epsx >= beta1          : istop = 3            
            if test2 <= tol or t1 <= 1: istop = 2
            if test1 <= tol or t2 <= 1: istop = 1

        if verbose:
            print(f"{niter:10} {x[0]:10.2e} {test1:10.2e} {test2:10.2e}"
                  f"{Anorm:10.2e} {Acond:10.2e} {gbar / Anorm:10.2e}")

        if istop != 0: break

    if verbose:
        print('\nExit MINimum RESidual Solver.\n')
        print(f"Status: {stop_status[istop]}")
        print(f"  niter = {niter}\n"
              f"  Anorm = {Anorm:.4e}\n"
              f"  Acond = {Acond:.4e}\n"
              f"  rnorm = {rnorm:.4e}\n"
              f"  ynorm = {ynorm:.4e}\n"
              f" Arnorm = {Arnorm:.4e}\n")

    return (x, istop, niter, rnorm)


if __name__ == '__main__':
    from aksolve.util import matvec_from_coo

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('==== Testing MINRES ====')
    # A = [[ 6.,  3.,  0.],
    #      [ 3., -2.,  5.],
    #      [ 0.,  5.,  2.]]
    R = ak.array([0, 0, 0, 1,  1, 1, 2, 2, 2])
    C = ak.array([0, 1, 2, 0,  1, 2, 2, 1, 2])
    V = ak.array([6, 3, 0, 3, -2, 5, 0, 5, 2])

    x = ak.array([2., -2., 9.])
    b = ak.array([6., 55., 8.])

    matvec = matvec_from_coo(R, C, V)
    assert ak.all(matvec(x) == b)
    
    print('\n--> RHS == 0\n')
    ans = minres(matvec, ak.zeros(3), verbose=True)
    assert ans[1] == 0

    print('\n--> Ax == b\n')
    ans = minres(matvec, b, x, verbose=True)
    assert ans[1] == 0 and ak.all(ans[0] == x)

    print('\n--> Typical Solving\n')
    ans = minres(matvec, b, max_iter=3, verbose=True)
    print(ans)
    assert ak.all(ak.abs(ans[0] - x) < 1.0e-4)
    assert ans[3] < 1.0e-6
    assert ans[2] == 3
    assert ans[1] == 1

    print('\n--> Solve with Preconditioning\n')
    invV = ak.array([0.15104167, 0.03125, -0.078125, 0.03125, -0.0625,
                     0.15625, -0.078125, 0.15625, 0.109375])
    precon = matvec_from_coo(R, C, invV)
    ans = minres(matvec, b, precon=precon, verbose=True)
    print(ans)
    assert ak.all(ak.abs(ans[0] - x) < 1.0e-4)
    assert ans[3] <= 1.0e-6
    assert ans[2] == 2
    assert ans[1] == 2

    print('\n--> Solve: Large Diagonal matrix with Diagonal Preconditioning\n')
    D = ak.randint(1, 1000, 2 ** 32, dtype='float64')
    matvec = lambda x: x * D
    x = ak.randint(0, 1, 2 ** 32, dtype='float64')
    P = lambda x: x * (1.0 / D)
    b = matvec(x)
    ans = minres(matvec, b, precon=P, verbose=True)
    assert ak.all(ak.abs(ans[0] - x) < 1.0e-4)
    assert ans[3] < 1.0e-6
    assert ans[2] == 1
    assert ans[1] == 3

    print('##############')
    print('# YOU PASSED #')
    print('##############')
