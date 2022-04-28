from base_test import ArkoudaTest
import arkouda as ak
import arkouda_BlockArrays2D as ak2D

class Array2DTest(ArkoudaTest):
    def test_reshape(self):
        a = ak.array([1,2,3,4])
        a2d = ak2D.reshape(a, (2, 2))
        self.assertTrue((a2d == [[1,2],[3,4]]).all())

    def test_flatten(self):
        a = ak2D.array2D(10, 2,2)
        flat = ak2D.reshape(a, 4)
        self.assertTrue((flat == [10,10,10,10]).all())
        
    def test_operators(self):
        a = ak2D.randint2D(0,10,2,2)
        b = ak2D.randint2D(0,10,2,2)

        res = a + b
        resRow1 = a[0] + b[0]
        resRow2 = a[1] + b[1]
        self.assertTrue((res[0] == resRow1).all())
        self.assertTrue((res[1] == resRow2).all())
