from base_test import ArkoudaTest
import arkouda as ak
import aksolve as aks

from aksolve.util import matvec_from_coo

class aksolveTest(ArkoudaTest):
    
    def test_conjugate_gradient(self):
        
        # A = [[4, 1],
        #      [1, 3]]
        R = ak.array([0, 0, 1, 1])
        C = ak.array([0, 1, 0, 1])
        V = ak.array([4, 1, 1, 3])

        x = ak.array([1/11, 7/11])  # true answer
        b = ak.array([1, 2])        # RHS

        matvec = matvec_from_coo(R, C, V)

        ans = aks.cg(matvec, ak.zeros(2), verbose=True)
        self.assertEqual(ans[1], 0)

    
        ans = aks.cg(matvec, b, x)
        self.assertEqual(ans[1], 1)
        self.assertTrue(ak.all(ans[0] == x))

        ans = aks.cg(
            matvec,
            b,
            x_start=ak.array([2, 1]),
            max_iter=5,
            verbose=True)
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], 1.0e-6)
        self.assertEqual(ans[2], 2)
        self.assertEqual(ans[1], 3)

   
        ans = aks.cg(
            matvec,
            b,
            x_start=ak.array([2, 1]),
            tol=EPS,
            max_iter=5,
            verbose=True)
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], EPS)
        self.assertEqual(ans[2], 3)
        self.assertEqual(ans[1], 2)

        P = lambda x: ak.array([1/4, 1/3]) * x
        ans = qks.cg(matvec, b, precon=P, verbose=True)
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], EPS)
        self.assertEqual(ans[2], 2)
        self.assertEqual(ans[1], 2)


        D = ak.randint(1, 1000, 2 ** 32, dtype='float64')
        matvec = lambda x: x * D
        x = ak.randint(0, 1, 2 ** 32, dtype='float64')
        P = lambda x: x * (1.0 / D)
        b = matvec(x)
        ans = aks.cg(matvec, b, precon=P, verbose=True)
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], 1.0e-6)
        self.assertEqual(ans[2], 1)
        self.assertEqual(ans[1], 3)


    #minres tests
    def test_MINRES(self):
        # A = [[ 6.,  3.,  0.],
        #      [ 3., -2.,  5.],
        #      [ 0.,  5.,  2.]]
        R = ak.array([0, 0, 0, 1,  1, 1, 2, 2, 2])
        C = ak.array([0, 1, 2, 0,  1, 2, 2, 1, 2])
        V = ak.array([6, 3, 0, 3, -2, 5, 0, 5, 2])

        x = ak.array([2., -2., 9.])
        b = ak.array([6., 55., 8.])

        matvec = matvec_from_coo(R, C, V)
        self.assertTrue(ak.all(matvec(x) == b))
        

        ans = aks.minres(matvec, ak.zeros(3), verbose=True)
        self.assertEqual(ans[1], 0)

        ans = aks.minres(matvec, b, x, verbose=True)
        self.assertEqual(ans[1], 0)
        self.assertTrue(ak.all(ans[0] == x))

        ans = aks.minres(matvec, b, max_iter=3, verbose=True)
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], 1.0e-6)
        self.assertEqual(ans[2], 3)
        self.assertEqual(ans[1], 1)

    
        invV = ak.array([0.15104167, 0.03125, -0.078125, 0.03125, -0.0625,
                         0.15625, -0.078125, 0.15625, 0.109375])
        precon = matvec_from_coo(R, C, invV)
        ans = aks.minres(matvec, b, precon=precon, verbose=True)
    
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], 1.0e-6)
        self.assertEqual(ans[2], 2)
        self.assertEqual(ans[1], 2)

        D = ak.randint(1, 1000, 2 ** 32, dtype='float64')
        matvec = lambda x: x * D
        x = ak.randint(0, 1, 2 ** 32, dtype='float64')
        P = lambda x: x * (1.0 / D)
        b = matvec(x)
        ans = aks.minres(matvec, b, precon=P, verbose=True)
        self.assertTrue(ak.all(ak.abs(ans[0] - x) < 1.0e-4))
        self.assertLess(ans[3], 1.0e-6)
        self.assertEqual(ans[2], 1)
        self.assertEqual(ans[1], 3)


#TODO: finish converting these
'''
#util.py tests
if __name__ == '__main__':
    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('==== Testing Inner Product ====')
    
    x = ak.array([1, 2, 3])
    y = ak.array([2, 3, 4])
    assert inner(x, y) == 20

    print('=== Testing Vector norms ====')

    assert norm(x) == np.sqrt(14)
    assert norm(y) == np.sqrt(29)
    
    print('==== Testing Identity Operator ====')

    x = ak.randint(0, 1, 10 ** 8, dtype='float64')
    assert ak.all(x == eye(x))

    print('==== Testing Matrix-Vector Operators ====')
    # M = [[4, 1],
    #      [1, 3]]
    R = ak.array([0, 0, 1, 1])
    C = ak.array([0, 1, 0, 1])
    V = ak.array([4, 1, 1, 3])

    x = ak.array([1/11, 7/11])  # true answer
    b = ak.array([1, 2])        # RHS

    # Mx == b
    matvec = matvec_from_coo(R, C, V)
    assert ak.all(matvec(x) == b)

    # ONES @ [1, -1] = 0
    matvec = matvec_from_coo(R, C)
    assert ak.sum(matvec(ak.array([1, -1]))) == 0

    # now with explicitly different shape
    # M = [[1, 1],
    #      [1, 1],
    #      [0, 0]]
    matvec = matvec_from_coo(R, C, shape=(3, 2))
    assert ak.all(matvec(ak.array([1, 1])) == ak.array([2, 2, 0]))

    print('==== Testing Jacobi Preconditioner ====')

    P = diagonal_preconditioner(R, C, V)
    Px = P(ak.ones(2))
    assert Px[0] == 1/4 and Px[1] == 1/3

    print('##############')
    print('# YOU PASSED #')
    print('##############')
'''
