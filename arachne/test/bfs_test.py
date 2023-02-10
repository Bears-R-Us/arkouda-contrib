from base_test import ArkoudaTest
import arkouda as ak
import arachne as ar

class ArachneTest(ArkoudaTest):
    def test_bfs_layers(self):
        print("BREADTH FIRST SEARCH -- CORRECTNESS CHECK")
        curr_path = str(pathlib.Path(__file__).parent.resolve())
        filepath_and_filename = curr_path.rsplit("/", 1)
        curr_path = filepath_and_filename[0] + "/"
        filename = curr_path + "data/karate.mtx"

        # Split up filename parameter to only path and only name of file.
        filepath_and_filename = filename.rsplit("/", 1)
        only_filepath = filepath_and_filename[0] + "/"
        only_filename = filepath_and_filename[1]
        only_extension = filename.rsplit(".", 1)[1]

        weighted = False
        directed = False
        # Read in metadata for file from external info file.
        for line in open(only_filepath + "info.txt"):
            if line[0] == "#":
                continue
            
            text = line.split()

            if text[0] == only_filename:
                directed = bool(int(text[1]))
                weighted = bool(int(text[2]))

        # Read in the graph. 
        G = ar.read_edgelist(filename, directed=directed, weighted=weighted, filetype=only_extension)
        print(f"G = Graph with {len(G)} nodes and {G.size()} edges")

        # Run bfs_layers. 
        start = time.time()
        ar_layers = ar.bfs_layers(G, 0).to_ndarray()
        end = time.time()

        ar_layer_dict = {}
        # Generate dictionary object.
        for (i,x) in enumerate(ar_layers):
            if x not in ar_layer_dict:
                ar_layer_dict[x] = [i]
            else:
                ar_layer_dict[x].append(i)

        # NetworkX reading in below.
        fh = open(filename, "rb")
        H = nx.from_scipy_sparse_array(sp.io.mmread(fh))
        print("H =", H)
        nx_layer_dict = dict(enumerate(nx.bfs_layers(H, 0)))

        # Sort to make the lists the same.
        for key in ar_layer_dict:
            ar_layer_dict[key].sort()
            nx_layer_dict[key].sort()

        return self.assertEqual(ar_layer_dict, nx_layer_dict)