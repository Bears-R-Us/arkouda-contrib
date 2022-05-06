def symmlq(
    matvec: Callable[[ak.pdarray], ak.pdarray],
    b: ak.pdarray,
    max_iter: int = 100,
    tolerance: float = 1.0e-9,
    verbose: bool = False,
) -> Tuple[ak.pdarray, int, int, float, float, float, float]:
    """
    Solve a sparse, symmetric matrix equation Ax = b.

    Parameters
    ----------
    matvec : Callable[[ak.pdarray], ak.pdarray]
        function returning the product Ay for a given y
    b : ak.pdarray
        right hand side of desired equation
    max_iter : int (default 100)
        number of iterations to perform
    tol : float (default 1.0e-9)
        relative stopping tolerance
    verbose : bool (default False)
        print a summary of iterations

    Return
    ------
    x : ak.pdarray
        computed solution
    istop : int
        reason for termination
        istop >= 3 implies final x may not be acceptable
    num_matvec : int
        number of matvec iterations
    anorm : float
        estimate of the norm of the matrix operator
    acond : float
        (usually substantial under-)estimate of the condition of operator
    rnorm : float
        norm of final residual vector
    xnorm : float
        norm of final solutoin vector

    Notes
    -----
    This is based on https://web.stanford.edu/group/SOL/software/symmlq/
    and github.com/PythonOptimizers/pykrylov
    """
    eps = np.finfo(np.float64).eps # machine precision
    stop_condition = {
        -1: 'matvec appears ot be multiple of I',
        0 : 'RHS is zero vector. x = 0.',
        1 : 'converged within specified tolerance',
        2 : 'converged within machine precision',
        3 : 'x converged to an eigenvector',
        4 : 'iteration limit reached. not converged',
        5 : 'acond has exceeded threshold, matrix is ill-conditioned',
        6 : 'matvec not symmetric'}

    n = b.size                  # dimension of the problem
    if verbose:
        print('\nEnter SYMMLQ: Solution of symmetric Ax = b.\n')
        print(f"        n = {n}\n"
              f" max_iter = {max_iter}\n"
              f"tolerance = {tolerance}\n")

    num_matvec = istop = 0
    anorm = acond = rnorm = xnorm = ynorm = 0.0
    x, v, w = ak.zeros(n), ak.zeros(n), ak.zeros(n)

    y, r1 = ak.zeros(n), ak.zeros(n)
    y[:], r1[:] = b[:], b[:]

    b1 = y[0]
    beta1 = ak.sum(r1 * y)

    if beta1 == 0:
        if verbose: print(f'exiting: {stop_condition[istop]}')
        return (x, istop, num_matvec, anorm, acond, rnorm, xnorm)

    # perform initial orthoganalization
    beta1 = np.sqrt(beta1)
    s = 1.0 / beta1
    v += s * y
    y = matvec(y)
    num_matvec += 1

    # check for symmetric operator
    r2 = matvec(y)          # don't count this toward the total
    s, t = ak.sum(y * y), ak.sum(v * r2)
    if np.abs(s - t) > (s + eps) * eps ** (1.0 / 3.0):
        istop = 4
        if verbose: print(f'exiting: {stop_condition[istop]}')
        return (x, istop, num_matvec, anorm, acond, rnorm, xnorm)

    alfa = ak.sum(v * y)
    y -= (alfa / beta) * r1

    # make sure r2 orthogonal v
    z, s = ak.sum(v * y), ak.sum(v * v)
    y -= (z / s) * v
    r2[:] = y[:]

    oldb, beta = beta1, ak.sum(r2 * y)
    beta = np.sqrt(beta)
    if beta <= eps:
        istop = -1
        if verbose: print('exiting: {stop_condition[istop]}')
        return (x, istop, num_matvec, anorm, acond, rnorm, xnorm)

    # initialize other quantities
    cgnorm = qrnorm = rhs1 = beta1
    x1gc = rhs2 = bstep = ynorm2 = 0
    gbar = alfa
    snprod = 1
    tnorm = alfa ** 2 + beta ** 2
    gmin = gmax = np.abs(alfa) + eps

    if verbose:
        print(f'beta1  = {beta1:10.2e}\nalpha1 = {alpha1:10.2e}')
        print('(v1, v2) before and after local reorthogonalization '
              f'({s:.2e}, {t:.2e})\n')

        columns = ['num_matvec', 'x(1)(cg)', 'normr(cg)',
                   'r(minres)',  'bstep', 'anorm', 'acond']
        header = ' '.join(f'{c: >12}' for c in columns)
        print(header)
        print(f'{num_matvec:>12g} {x1cg:>12.3e} {cgnorm:>12.3e} '
              f'{qrnorm:>12.3e} {bstep / beta1:>12.3e}')

    #######################
    # main iteration loop #
    #######################
    done = False
    while True:
        num_matvec += 1
        anorm = np.sqrt(tnorm)
        ynorm = np.sqrt(ynorm2)
        epsa = anorm * eps
        epsx = anorm * ynorm * eps
        epsr = anorm * ynorm * tol
        diag = gbar if gbar != 0 else epsa

        lqnorm = np.sqrt(rhs1 ** 2 + rhs2 ** 2)
        qrnorm = snprod * beta1
        cgnorm = qrnorm * beta / np.abs(diag)

        # Estimate cond(A)
        if lqnorm < cgnorm:
            acond = gmax / gmin
        else:
            denom = min(gmin, np.abs(diag))
            acond = gmax / denom

        zbar = rhs1 / diag
        z = (snprod * zbar + bstep) / beta1
        x1lq = x[0] + b1 * bstep / beta1
        x1cg = x[0] + w[0] * zbar + b1 * z

        #check for stopping conditions
        if num_matvec >= max_iter : istop, done = 5, True
        if acond >= 0.1 / eps     : istop, done = 4, True
        if epsx >= beta1          : istop, done = 3, True
        if cgnorm <= epsx         : istop, done = 2, True
        if cgnorm <= epsr         : istop, done = 1, True

        if verbose:
            print(header)
            print(f'{num_matvec:>12g} {x1cg:>12.3e} {cgnorm:>12.3e} '
                  f'{qrnorm:>12.3e} {bstep / beta1:>12.3e} '
                  f'{anorm:>12.1e} {acond:>12.1e}')

        if done: break

        # find current Lanczos vector v = (1 / beta) * y
        s = 1 / beta
        v = s * y
        y = matvec(y)
        num_matvec += 1
        y -= (beta / oldb) * r1
        alfa = ak.sum(v * y)
        y -= (alva / beta) * r2
        r1[:], r2[:] = r2[:], y[:]
        oldb, beta = beta, ak.sum(r2, y)

        if beta < 0:
            istop = 6
            break

        beta = np.sqrt(beta)
        tnorm += alfa ** 2 + oldb ** 2 + beta ** 2

        # compute next plane rotation for Q
        gamma = np.sqrt(gbar ** 2 + oldb ** 2)
        cos, sin = gbar / gamma, oldb / gamma
        delta = cos * gbar + sin * alfa
        gbar = sin * dbar - cos * alfa
        epsilon = sin * beta
        dbar = - cos * beta

        # update x
        z = rhs1 / gamma
        s, t = z * cos, z * sin
        x += s * w + t * v
        w *= sin
        w -= cos * v

        # accumulate step along the direction b
        bstep += snprod * cos * z
        snprod *= sin
        gmax = max(gmax, gamma)
        gmin = min(gmin, gamma)
        ynorm2 += z ** 2
        rhs1 = rs2 - detla * z
        rhs2 = - epsilon * z

        if cgnorm < lqnorm:
            zbar = rhs1 / diag
            bstep += snprod * zbar
            ynorm = np.sqrt(ynorm2 + zbar ** 2)
            x += zbar * w

        # take last step along b
        bstep /= beta1
        y[:] = rhs[:]
        x += bstep * y

        # compute final residual
        y = matvec(x)
        num_matvec += 1
        r1 = rhs - y
        rnorm = np.sqrt(ak.sum(r1 * r1))
        xnorm = np.sqrt(ak.sum(x * x))

        if verbose:
            print('\nExit SYMMLQ.')
            print(stop_condition[istop])
            print(f" num_matvec = {num_matvec}")
            print(f" anorm = {anorm:12.4e}")
            print(f" acond = {acond:12.4e}")
            print(f" rnorm = {rnorm:12.4e}")
            print(f" xnorm = {xnorm:12.4e}")

    return (x, istop, num_matvec, anorm, acond, rnorm, xnorm)
