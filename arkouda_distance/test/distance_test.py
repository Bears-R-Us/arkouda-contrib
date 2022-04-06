from base_test import ArkoudaTest
import arkouda as ak
import arkouda_distance as akd

class DistanceTest(ArkoudaTest):
    def test_dot(self):
        a = ak.arange(3)
        b = ak.arange(3, 6, 1)
        d = akd.dot(a, b)
        self.assertEqual(d, 14)

    def test_magnitude(self):
        a = ak.arange(10)
        m = akd.magnitude(a)
        self.assertEqual(m, 16.881943016134134)

    def test_cosine(self):
        a = ak.arange(3)
        b = ak.arange(3, 6, 1)
        c = akd.cosine(a, b)
        self.assertEqual(c, 0.1145622551528539)

    def test_euclidean(self):
        a = ak.arange(3)
        b = ak.arange(3, 6, 1)
        e = akd.euclidean(a, b)
        self.assertEqual(e, 5.196152422706632)
