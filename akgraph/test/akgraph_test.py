from base_test import ArkoudaTest
import arkouda as ak
import akgraph as akg

from akgraph.generators import path_graph, complete_graph, karate_club_graph

class akgraphTest(ArkoudaTest):
    
    #centrality.py tests
    def test_eigenvector_centrality(self):
        # generate data
        V = ak.array([1, 1, 3, 3, 3, 4, 4, 5, 5, 6]) - 1
        U = ak.array([2, 3, 1, 2, 5, 5, 6, 4, 6, 4]) - 1
        W = ak.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 1])


        # unweighted Eigenvector Centrality
        c, e = akg.eigenvector_centrality(V, U)
        e_ans = ak.array([0.3185602 , 0., 0.5154412 , 0.51544117, 0.51544117, 0.31856016])
        self.assertLess(np.abs(c - 1.61803397), 1e-4)
        self.assertTrue(ak.all(ak.abs(e - e_ans) < 1e-4))

        # weighted
        c, e = akg.eigenvector_centrality(V, U, W, tol=1e-6)
        e_ans = ak.array([0.11856115, 0., 0.46627055, 0.56972278, 0.66234765, 0.07243326])
        self.assertLess(np.abs(c - 7.86545993), 1e-4)
        self.assertTrue(ak.all(ak.abs(e - e_ans) < 1e-4))

    def test_HITS(self):
        # generate data
        V = ak.array([1, 1, 3, 3, 3, 4, 4, 5, 5, 6]) - 1
        U = ak.array([2, 3, 1, 2, 5, 5, 6, 4, 6, 4]) - 1
        W = ak.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 1])
   
        # unweighted
        h, a = akg.hub_auth(V, U)
        h_ans = ak.array( [0.35468849, 0., 0.75013338, 0.48164091, 0.26849258, 0.08619601])
        a_ans = ak.array( [0.3697928 , 0.54464337, 0.17485057, 0.17485062, 0.60722703, 0.36979285])
        self.assertTrue(ak.all(ak.abs(h - h_ans) < 1e-4))
        self.assertTrue(ak.all(ak.abs(a - a_ans) < 1e-4))

        # weighted
        h, a = akg.hub_auth(V, U, W)
        h_ans = ak.array([0.00263481, 0., 0.119855 , 0.54681211, 0.82786225, 0.03561533])
        a_ans = ak.array([2.62970646e-02, 3.52554515e-02, 3.85397440e-04, 4.86975543e-01, 2.83777614e-01, 8.24857839e-01])
        self.assertTrue(ak.all(ak.abs(h - h_ans) < 1e-4))
        self.assertTrue(ak.all(ak.abs(a - a_ans) < 1e-4))

    def test_PageRank(self):
        V = ak.array([1, 1, 3, 3, 3, 4, 4, 5, 5, 6]) - 1
        U = ak.array([2, 3, 1, 2, 5, 5, 6, 4, 6, 4]) - 1
        W = ak.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 1])
        c4V, c4U = complete_graph(4)
    
        # unweighted
        pr = ak.array([0.03721197, 0.05395736, 0.04150566, 0.3750808 , 0.20599833, 0.28624587])
        x = akg.pagerank(V, U, alpha=0.9, tol=1.0e-08)
        self.assertTrue(ak.all(ak.abs(x - pr) <= 1e-4))

        # weighted
        pr = ak.array([0.04711131, 0.06477131, 0.06087235, 0.35146311, 0.19361657, 0.28216535])
        x = akg.pagerank(V, U, W)
        self.assertTrue(ak.all(ak.abs(x - pr) <= 1e-4))

        # complete graph with differing personalizations
        p_vec = ak.array([1, 1, 4, 4])
        pr = ak.array([0.23246, 0.23246, 0.26753, 0.26753])
        x = akg.pagerank(c4V, c4U, p_vec=p_vec)
        self.assertTrue(ak.all(ak.abs(x - pr) <= 1e-4))

        p_vec = ak.array([0, 0, 0, 1])
        pr = ak.array([0.22077, 0.22077, 0.22077, 0.33766])
        x = akg.pagerank(c4V, c4U, p_vec=p_vec)
        self.assertTrue(ak.all(ak.abs(x - pr) <= 1e-4))


    #community.py tests
    def test_Single_Edge(self):
        # generate data
        V, U = ak.array([0, 1]), ak.array([1, 0])
        k, nc, c, C = akg.cdlp(V, U, randomize=False)
        self.assertEqual(k, 2)
        self.assertEqual(nc, 2)
        self.assertEqual(c, True)
        self.assertTrue(ak.all(C == V))
        
    def test_Diconnected(self):
        V = ak.array([0, 2, 0, 3, 2, 3, 1, 4, 1, 5, 4, 5])
        U = ak.array([2, 0, 3, 0, 3, 2, 4, 1, 5, 1, 5, 4])
        k, nc, c, C = akg.cdlp(V, U, randomize=False)
        self.assertEqual(k,  3)
        self.assertEqual(nc, 2)
        self.assertEqual(c, True)
        self.assertTrue(ak.all(C == ak.array([0, 1, 0, 0, 1, 1])))

        
    def test_Connected(self):
        A, B = complete_graph(5)
        X, Y = A + 5, B + 5
        V = ak.concatenate([A, X, ak.array([0, 5])], ordered=False)
        U = ak.concatenate([B, Y, ak.array([5, 0])], ordered=False)
        k, nc, c, C = akg.cdlp(V, U, randomize=False)
        self.assertEqual(k, 3)
        self.assertEqual(nc, 2)
        self.assertEqual(c, True)
        self.assertTrue(ak.all(C == ak.array([0, 0, 0, 0, 0, 5, 5, 5, 5, 5])))

    def test_Clique(self):
        V, U = complete_graph(10000)
        k, nc, c, C = akg.cdlp(V, U, randomize=False)
        self.assertEqual(k, 2)
        self.assertEqual(nc, 1)
        self.assertTrue(ak.all(C == 0))
        
    #components.py tests
    def test_BFS_LP(self):
        n = 5
        pV, pU = path_graph(n)
        cV, cU = complete_graph(n)
        pcV, pcU = (ak.concatenate([pV, cV + n], ordered=False),
                    ak.concatenate([pU, cU + n], ordered=False))
        pcC = ak.array([0] * n + [n] * n)
        comms, kV, kU = karate_club_graph()
        kC = ak.zeros_like(comms)


        _, C = akg.bfs_lp(pcV, pcU)
        self.assertTrue(ak.all(C == pcC))
        _, C = akg.bfs_lp(kV, kU)
        self.assertTrue(ak.all(C == kC))


    def test_FastSV(self):
        n = 5
        pV, pU = path_graph(n)
        cV, cU = complete_graph(n)
        pcV, pcU = (ak.concatenate([pV, cV + n], ordered=False),
                    ak.concatenate([pU, cU + n], ordered=False))
        pcC = ak.array([0] * n + [n] * n)
        comms, kV, kU = karate_club_graph()
        kC = ak.zeros_like(comms)


        _, C = akg.fast_sv(pcV, pcU)
        self.assertTrue(ak.all(C == pcC))
        _, C = akg.fast_sv(kV, kU)
        self.assertTrue(ak.all(C == kC))
        
    def test_FastSV(self):
        n = 5
        pV, pU = path_graph(n)
        cV, cU = complete_graph(n)
        pcV, pcU = (ak.concatenate([pV, cV + n], ordered=False),
                    ak.concatenate([pU, cU + n], ordered=False))
        pcC = ak.array([0] * n + [n] * n)
        comms, kV, kU = karate_club_graph()
        kC = ak.zeros_like(comms)

        _, C = akg.lps(pcV, pcU)
        self.assertTrue(ak.all(C == pcC))
        _, C = akg.lps(kV, kU)
        self.assertTrue(ak.all(C == kC))

    #core.py tests
    def test_k_Core_Path(self):
        V, U = path_graph(10)
        core = akg.k_core(V, U, 2)
        self.assertEqual(core.sum(), 0)
        core = akg.k_core(V, U, 1)
        self.assertEqual(core.sum(), 10)

    def test_k_Core_Clique(self):
        V, U = complete_graph(10)
        core = akg.k_core(V, U, 9)
        self.assertEqual(core.sum(), 10)
        core = akg.k_core(V, U, 10)
        self.assertEqual(core.sum(), 0)
        
    def test_k_Core_Karate(self):
        n = 34
        _, V, U = karate_club_graph()
        core = akg.k_core(V, U, 1)
        self.assertEqual(core.sum(), n)
        core = akg.k_core(V, U, 2)
        self.assertTrue(ak.all(core == ak.array([i != 11 for i in range(n)])))
        core = akg.k_core(V, U, 3)
        self.assertTrue(ak.all(core == ak.array( [True, True, True, True, True, True, True,
                                     True, True, False, True, False, False,
                                     True, False, False, False, False, False,
                                     True, False, False, False, True, True,
                                     True, False, True, True, True, True, True,
                                     True, True] )))
        core = akg.k_core(V, U, 4)
        self.assertTrue(ak.all(core == ak.array( [True, True, True, True, False, False,
                                     False, True, True, False, False, False,
                                     False, True, False, False, False, False,
                                     False, False, False, False, False, False,
                                     False, False, False, False, False, False,
                                     True, False, True, True] )))
        core = akg.k_core(V, U, 5)
        self.assertEqual(core.sum(), 0)
        

        cores = akg.core_number(V, U)
        self.assertTrue(ak.all(cores == ak.array([4, 4, 4, 4, 3, 3, 3, 4, 4, 2, 3, 1, 2, 4,
                                     2, 2, 2, 2, 2, 3, 2, 2, 2, 3, 3, 3, 2, 3,
                                     3, 3, 4, 3, 4, 4])))



    #mis.py tests
    def test_Maximal_Independent_Set(self):

    
        c, V, U = karate_club_graph()
        pi = ak.arange(c.size)
        ans = ak.cast(ak.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1,
                                0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0]),
                                'bool')
        I = akg.maximal_independent_set(V, U, pi)
        self.assertTrue(ak.all(I == ans))


    #msf.py tests
    def test_Minimum_Spanning_Forest(self):
        V = ak.array([0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 3,
                      3, 4, 4, 4, 4, 4, 5, 5, 5, 6, 6])
        U = ak.array([1, 3, 0, 2, 3, 4, 1, 4, 0, 1, 4,
                      5, 1, 2, 3, 5, 6, 3, 4, 6, 4, 5])
        W = ak.array([7, 5, 7, 8, 9, 7, 8, 5, 5, 9, 15,
                      6, 7, 5, 15, 8, 9, 6, 8, 11, 9, 11])
        c, vF, uF, wF = akg.msf_boruvka(V, U, W)
        self.assertTrue(ak.all(c == 0))
        self.assertTrue(ak.all(vF == ak.array([0, 0, 1, 2, 3, 4])))
        self.assertTrue(ak.all(uF == ak.array([1, 3, 4, 4, 5, 6])))
        self.assertTrue(ak.all(wF == ak.array([7, 5, 7, 5, 6, 9])))



    #traversal.py tests
    def test_BFS(self):

        _, V, U = karate_club_graph()
        X, Y = complete_graph(1000)

        # BFS from 0
        reachable = akg.bfs_reachable(V, U, 0)
        self.assertTrue(ak.all(reachable))

        # BFS from 0, depth_limit = 2
        reachable = akg.bfs_reachable(V, U, 0, 2)
        ans = ak.array([True, True, True, True, True, True, True, True, True, True,
                        True, True, True, True, False, False, True, True, False,
                        True, False, True, False, False, True, True, False, True,
                        True, False, True, True, True, True])
        self.assertTrue(ak.all(reachable == ans))

        # BFS from [0, 33], depth_limit = 1
        reachable = akg.bfs_reachable(V, U, ak.array([0, 33]), 1)
        ans = ak.array([True, True, True, True, True, True, True, True, True, True,
                        True, True, True, True, True, True, False, True, True,
                        True, True, True, True, True, False, False, True, True,
                        True, True, True, True, True, True])
        self.assertTrue(ak.all(reachable == ans))



        # directed bug
        dist = akg.bfs_distance(ak.array([0, 0, 2, 3]), ak.array([1, 2, 3, 4]), 0)
        ans = ak.array([0, 1, 1, 2, 3])
        self.assertTrue(ak.all(dist == ans))
    
        # BFS from 0
        dist = akg.bfs_distance(V, U, 0)
        ans = ak.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 3, 3, 2,
                        1, 3, 1, 3, 1, 3, 3, 2, 2, 3, 2, 2, 3, 2, 1, 2, 2])
        self.assertTrue(ak.all(dist == ans))

        # BFS from 0, depth_limit = 2
        dist = akg.bfs_distance(V, U, 0, 2)
        ans = ak.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, -1, -1, 2, 1,
                        -1, 1, -1, 1, -1, -1, 2, 2, -1, 2, 2, -1, 2, 1, 2, 2])
        self.assertTrue(ak.all(dist == ans))

        # BFS from {0, 33}
        dist = akg.bfs_distance(V, U, ak.array([0, 33]))
        ans = ak.array([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2,
                        1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 0])
        self.assertTrue(ak.all(dist == ans))

        # complete graph
        dist = akg.bfs_distance(X, Y, 0)
        self.assertEqual(dist[0], 0)
        self.assertTrue(ak.all(dist[1:] == 1))

    
        # BFS tree from 0
        tree = akg.bfs_forest(V, U, 0)
        ans = ak.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 33, 33, 6, 0, 33,
                        0, 33, 0, 33, 33, 31, 31, 33, 2, 31, 33, 8, 0, 31, 31])
        self.assertTrue(ak.all(tree == ans))

        # BFS tree from {0, 33}, depth_limit = 1
        tree = akg.bfs_forest(V, U, ak.array([0, 33]), 1)
        ans = ak.array(
            [0, 0, 0, 0, 0, 0, 0, 0, 33, 33, 0, 0, 0, 33, 33, 33, -1, 0,
             33, 33, 33, 0, 33, 33, -1, -1, 33, 33, 33, 33, 33, 33, 33, 33])
        self.assertTrue(ak.all(tree == ans))

        # complete graph
        tree = akg.bfs_forest(X, Y, 777)
        self.assertTrue(ak.all(tree == 777))

    def test_SSSP_Bellman_Ford(self):
        V = ak.array([0, 1, 1, 2, 2, 3, 4, 4, 4, 4, 5, 5, 6, 6, 6, 6])
        U = ak.array([4, 4, 5, 4, 6, 6, 0, 1, 2, 6, 1, 6, 2, 3, 4, 5])
        W = ak.array([0.00519276, 0.48041395, 0.82665647, 0.81736032, 0.85313951,
                      0.40577813, 0.00519276, 0.48041395, 0.81736032, 0.40383667,
                      0.82665647, 0.84988933, 0.85313951, 0.40577813, 0.40383667,
                      0.84988933])
        tree, dist = akg.sssp_bf(V, U, W, 0)
        ans_tree = ak.array([0, 4, 4, 6, 0, 6, 4])
        ans_dist = ak.array([0. , 0.48560671, 0.82255308, 0.81480756, 0.00519276,
                            1.25891875, 0.40902943])
        self.assertTrue(ak.all(tree == ans_tree))
        self.assertTrue(ak.all(ak.abs(dist - ans_dist) < 10 ** -7))
    
 
#TBD: update these tests
'''
#/util/general.py tests
if __name__ == '__main__':
    host = input("enter arkouda hostname: ")
    ak.connect(host)

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Set Partitions ====')
    A = ak.array([1, 2, 3, 1, 2, 3, 1, 2, 2, 3])
    B = ak.array([0, 1, 2, 0, 1, 2, 0, 1, 1, 2])
    assert ak.all(canonize_partition(A) == B)
    assert is_refinement(A, B)
    assert is_refinement(B, A)

    A = ak.randint(0, 256, 2 ** 32)
    B = canonize_partition(A)
    assert is_refinement(A, B)
    assert is_refinement(B, A)
    C = ak.zeros_like(A)
    assert is_refinement(A, C)
    assert not is_refinement(C, A)

    print('==== Testing Permutatitons ====')
    pi = get_perm(10 ** 6)
    assert is_perm(pi)
    assert is_perm(ak.arange(10 ** 6))
    assert not is_perm(ak.zeros(10, dtype='int64'))

    print('##############')
    print('# YOU PASSED #')
    print('##############')

#/utuil/graph.py tests

if __name__ == '__main__':
    from akgraph.generators import path_graph, complete_graph, karate_club_graph

    host = input("enter arkouda hostname: ")
    ak.connect(host)

    A = ak.array([1, 1, 1, 3, 3, 8, 8, 1])
    B = ak.array([1, 2, 3, 1, 4, 8, 5, 2])

    print('####################')
    print('# PERFORMING TESTS #')
    print('####################')

    print('==== Testing Loop Removal ====')
    X, Y = remove_loops(A, B)
    X_ans = ak.array([1, 1, 3, 3, 8, 1])
    Y_ans = ak.array([2, 3, 1, 4, 5, 2])
    assert ak.all(X == X_ans)
    assert ak.all(Y == Y_ans)

    print('==== Testing Duplicate Removal ====')
    X, Y = remove_duplicates(A, B)
    X_ans = ak.array([1, 1, 1, 3, 3, 8, 8])
    Y_ans = ak.array([1, 2, 3, 1, 4, 5, 8])
    assert ak.all(X == X_ans)
    assert ak.all(Y == Y_ans)

    print('==== Testing Symmetrize ====')
    X, Y = symmetrize_egdes(A, B)
    X_ans = ak.array([1, 1, 1, 2, 1, 3, 3, 1, 3, 4, 8, 8, 8, 5, 1, 2])
    Y_ans = ak.array([1, 1, 2, 1, 3, 1, 1, 3, 4, 3, 8, 8, 5, 8, 2, 1])
    assert ak.all(X == X_ans)
    assert ak.all(Y == Y_ans)

    print('==== Testing Edge Standardization ====')
    V, U, L = standardize_edges(A, B, symmetric=False, return_labels=True)
    assert ak.all(L == ak.array([1, 2, 3, 4, 5, 8]))
    assert ak.all(V == ak.array([0, 0, 2, 2, 5]))
    assert ak.all(U == ak.array([1, 2, 0, 3, 4]))

    V, U = standardize_edges(A, B)
    assert ak.all(V == ak.array([0, 0, 1, 2, 2, 3, 4, 5]))
    assert ak.all(U == ak.array([1, 2, 0, 0, 3, 2, 5, 4]))

    print('==== Testing Edge Packing ====')
    V = ak.randint(0, 2 ** 8, 2 ** 16, dtype='int64')
    U = ak.randint(0, 2 ** 8, 2 ** 16, dtype='int64')
    V, U = standardize_edges(V, U)
    E = pack_edges(V, U)
    X, Y = unpack_edges(E)
    F = pack_edges(X, Y)
    assert ak.all(V == X)
    assert ak.all(U == Y)
    assert ak.all(E == F)

    print('==== Testing Induced Subgraphs ====')
    # path graph
    V, U = path_graph(4)
    pi = ak.coargsort([V, U])
    V, U = V[pi], U[pi]
    nodes = ak.array([0, 1, 2])
    A, B = subgraph(V, U, nodes)
    assert ak.all(A == ak.array([0, 1, 1, 2]))
    assert ak.all(B == ak.array([1, 0, 2, 1]))
    C, D = subgraph(V, U, nodes, True) # one-hop
    assert ak.all(C == ak.array([0, 1, 1, 2, 2, 3]))
    assert ak.all(D == ak.array([1, 0, 2, 1, 3, 2]))

    # complete graph
    V, U = complete_graph(5)
    A, B = complete_graph(3)
    C, D = subgraph(V, U, ak.array([0, 1, 2]))
    assert ak.all(A == C) and ak.all(B == D)
    C, D = subgraph(V, U, ak.array([0, 1, 2]), True) # one-hop
    assert ak.all(C == ak.array(
        [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4]))
    assert ak.all(D == ak.array(
        [1, 2, 3, 4, 0, 2, 3, 4, 0, 1, 3, 4, 0, 1, 2, 0, 1, 2]))

    print('##############')
    print('# YOU PASSED #')
    print('##############')

'''
