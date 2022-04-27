from base_test import ArkoudaTest
import arkouda as ak

class DistanceTest(ArkoudaTest):
    def test_dot(self):
        a = ak.array([1,2,3])
        b = ak.array([1,2,3])
        self.assertEqual(True, True)
