import unittest
from arkouda_integration.k8s import InvocationMethod

class ArkoudaIntegrationTest(unittest.TestCase):

    def test_invocation_method(self):
        self.assertEqual(InvocationMethod.GET_POD_IPS,InvocationMethod('GET_POD_IPS'))
        self.assertEqual('GET_POD_IPS', str(InvocationMethod.GET_POD_IPS))
