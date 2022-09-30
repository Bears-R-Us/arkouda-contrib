from base_test import ArkoudaTest
import arkouda as ak
import lsh_minmax as lsh

class DistanceTest(Arkouda
    def test_lsh(self):
        a = ak.array([0, 3, 10, 15, 27, 31, 38, 40, 44, 49, 50])
        b = ak.array([3, 4, 1, 3, 7, 8, 2, 1, 8, 4, 2, 5, 6, 9, 2, 5, 3, 2, 8, 8, 9, 1, 5, 3, 9, 3, 3, 3, 1, 8, 1, 6, 9, 9, 8, 7, 3, 5, 1, 1, 3, 8, 8, 6, 4, 6, 5, 1, 7, 1])
        c = 1/b
        (d,e) = lsh.lshMinMax(a, b, c, True, 3)
        f = ak.array([3, 3, 4, 1, 1, 4, 3, 3, 1, 3, 3, 7, 7, 8, 7, 2, 8, 8, 2, 1, 1, 1, 8, 1, 4, 8, 4, 2, 4, 4])
        g = ak.array([0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, -1.0, -1.0, -1.0, -1.0, -1.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -2.0, -1.0, 0.0, 0.0, -1.0, 0.0])
        self.assertEqual(d,f)
        self.assertEqual(e,g)

