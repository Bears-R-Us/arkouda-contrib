from base_test import ArkoudaTest
import arkouda as ak
import arkouda_BlockArrays2D as ak2D

class Array2DTest(ArkoudaTest):
    def test_create(self):
        a2di = ak2D.array2D(0, 2, 2, dtype=ak.int64)
        self.assertTrue((a2di[0] == ak.array([0,0], dtype=ak.int64)).all())
        self.assertTrue((a2di[1] == ak.array([0,0], dtype=ak.int64)).all())
        a2df = ak2D.array2D(0.5, 2, 2, dtype=ak.float64)
        self.assertTrue((a2df[0] == ak.array([0.5,0.5], dtype=ak.float64)).all())
        self.assertTrue((a2df[1] == ak.array([0.5,0.5], dtype=ak.float64)).all())

    def test_reshape(self):
        a = ak.array([1,2,3,4])
        a2d = ak2D.reshape(a, (2, 2))
        self.assertTrue((a2d[0] == ak.array([1,2])).all())
        self.assertTrue((a2d[1] == ak.array([3,4])).all())
        
    def test_operators(self):
        a = ak2D.randint2D(0,10,2,2)
        b = ak2D.randint2D(0,10,2,2)

        res = a + b
        resRow1 = a[0] + b[0]
        resRow2 = a[1] + b[1]
        self.assertTrue((res[0] == resRow1).all())
        self.assertTrue((res[1] == resRow2).all())
