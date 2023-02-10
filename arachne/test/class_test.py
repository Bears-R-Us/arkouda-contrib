from base_test import ArkoudaTest
import arkouda as ak
import arachne as ar
import scipy as sp
import scipy.io
import pathlib
import networkx as nx

class ClassTest(ArkoudaTest):
    def test_add_edges_from(self):
        src = [0, 1, 2, 3, 4, 5, 6, 7,  8, 9,  9]
        dst = [1, 2, 3, 4, 5, 6, 7, 8, 10, 8, 10]
        wgt = [1, 4, 5, 6, 7, 8, 2, 3,  3, 3, 2.1]

        Gu = ar.Graph()
        Hu = nx.Graph()

        Gd = ar.DiGraph()
        Hd = nx.DiGraph()

        Guw = ar.Graph()
        Huw = nx.Graph()

        Gdw = ar.DiGraph()
        Hdw = nx.DiGraph()

        akarray_src = ak.array(src)
        akarray_dst = ak.array(dst)
        akarray_wgt = ak.array(wgt)

        ebunch = list(zip(src, dst))
        ebunchw = list(zip(src, dst, wgt))

        Gu.add_edges_from(akarray_src, akarray_dst)
        Hu.add_edges_from(ebunch)
        ar_tuple_u = (len(Gu), Gu.size())
        nx_tuple_u = (len(Hu), Hu.size())
        
        Gd.add_edges_from(akarray_src, akarray_dst)
        Hd.add_edges_from(ebunch)
        ar_tuple_d = (len(Gd), Gd.size())
        nx_tuple_d = (len(Hd), Hd.size())
        
        Guw.add_edges_from(akarray_src, akarray_dst, akarray_wgt)
        Huw.add_weighted_edges_from(ebunchw)
        ar_tuple_uw = (len(Guw), Guw.size())
        nx_tuple_uw = (len(Huw), Huw.size())
        
        Gdw.add_edges_from(akarray_src, akarray_dst, akarray_wgt)
        Hdw.add_weighted_edges_from(ebunchw)
        ar_tuple_dw = (len(Gdw), Gdw.size())
        nx_tuple_dw = (len(Hdw), Hdw.size())

        test1 = self.assertEqual(ar_tuple_u, nx_tuple_u)
        test2 = self.assertEqual(ar_tuple_d, nx_tuple_d)
        test3 = self.assertEqual(ar_tuple_uw, nx_tuple_uw)
        test4 = self.assertEqual(ar_tuple_dw, nx_tuple_dw)

        test5 = self.assertEqual(test1, test2)
        test6 = self.assertEqual(test3, test4)

        return self.assertEqual(test5, test6)



