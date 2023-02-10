#!/usr/bin/env python3                                                         

from os import walk
import argparse
import pathlib
import time 
import sys
import io
import numpy as np
import scipy as sp
import scipy.io
import networkx as nx
import arkouda as ak
import arachne as ar

def bfs_single(filename:str, trials:int):
    print(f"BREADTH FIRST SEARCH -- SINGLE MODE")

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

    # Read in the graph and perform BFS steps. 
    G = ar.read_edgelist(filename, directed=directed, weighted=weighted, filetype=only_extension)
    selectroot = np.random.randint(0, len(G) - 1, trials)
    start = time.time()
    for root in selectroot:
        ar.bfs_layers(G, int(root))
    end = time.time()
    avg = (end - start) / trials
    print(f"Average performance for {trials} trials for graph {only_filename}: {avg}")

def bfs_batch(dirname:str, trials:int):
    print("BREADTH FIRST SEARCH -- BATCH MODE")

    # Read all mtx files in the passed directory. 
    filenames = next(walk(dirname), (None, None, []))[2]
    dirname = dirname + "/"

    for filename in filenames:
        # Split up filename parameter to only path and only name of file.
        only_filepath = dirname
        only_filename = filename
        only_extension = filename.rsplit(".", 1)[1]

        if only_extension != "mtx":
            continue

        filename = dirname + filename

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

        # Read in the graph and perform BFS steps. 
        G = ar.read_edgelist(filename, filetype=only_extension, directed=directed, weighted=weighted)
        selectroot = np.random.randint(0, len(G) - 1, trials)
        start = time.time()
        for root in selectroot:
            ar.bfs_layers(G, int(root))
        end = time.time()
        avg = (end - start) / trials
        print(f"Average performance for {trials} trials for graph {only_filename}: {avg}")

def correctness():
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

    return ar_layer_dict == nx_layer_dict
    
def create_parser():
    parser = argparse.ArgumentParser(
        description="Measure the performance of breadth-first search on a graph."
    )
    parser.add_argument("hostname", help="Hostname of arkouda server")
    parser.add_argument("port", type=int, help="Port of arkouda server")
    parser.add_argument(
        "-t", 
        "--trials", 
        type=int, 
        default=1, 
        help="Number of times to run the benchmark."
    )
    parser.add_argument(
        "--correctness-only", 
        default=False, 
        action="store_true", 
        help="Only check correctness, not performance."
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        help="Absolute path to file of the graph we wish to preprocess."
    )
    parser.add_argument(
        "-d",
        "--dirname",
        type=str,
        help="Absolute path to directory with multiple files to preprocess (batch method). Must end without '/'."
    )
    
    return parser

if __name__ == "__main__":    
    parser = create_parser()
    args = parser.parse_args()
    ak.verbose = False
    ak.connect(args.hostname, args.port)
    print(f"Passed arguments = {args}")

    cfg = ak.get_config()
    print (
        f"BREADTH FIRST SEARCH BENCHMARK\n"
        f"server hostname = {cfg['serverHostname']}\n"
        f"number of locales = {cfg['numLocales']}\n"
        f"number of PUs = {cfg['numPUs']}\n"
        f"max tasks = {cfg['maxTaskPar']}\n"
        f"memory = {cfg['physicalMemory']}\n")

    print(f"Correctness = {'Correct' if correctness() else 'Incorrect'}")
    
    if args.correctness_only:
        ak.shutdown()
        sys.exit(0)
    else:
        print()
        if args.filename is not None:
            bfs_single(args.filename, args.trials)
        elif args.dirname is not None:
            bfs_batch(args.dirname, args.trials)
        else:
            print(f"File name or directory name were not passed, function cannot proceed.")
            sys.exit(0)

    ak.shutdown()