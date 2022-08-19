from base_test import ArkoudaTest
import arkouda as ak
import lsh_minmax as lsh

class DistanceTest(Arkouda
    def test_lsh(self):
        a = ak.arange(3)
        b = ak.array([])
        C = ak.array([])
        (d,e) = lsh.lshMinMax(a, b, c, 2)
        e = ak.array([])
        f = ak.array([])
        self.assertEqual(d, 14)

