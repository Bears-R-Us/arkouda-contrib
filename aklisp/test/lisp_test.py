import numpy as np
from base_test import ArkoudaTest
import arkouda as ak

@arkouda_func
def my_axpy(a: ak.float64, x : ak.pdarray, y: ak.pdarray) -> ak.pdarray:
    return a * x + y

class LispTest(ArkoudaTest):
    def test_my_axpy(self):
        a = 5.0
        x = ak.randint(0,100,100,np.float64)
        y = ak.randint(0,100,100,np.float64)

        lisp_res = my_axpy(a,x,y)
        ak_res = a * x + y

        self.assertTrue((lisp_res == ak_res).all())
