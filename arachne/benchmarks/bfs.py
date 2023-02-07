#!/usr/bin/env python3                                                         

import argparse
import time 
import sys
import numpy as np
import networkx as nx
import arkouda as ak
import arachne as ar

def bfs_single(filename:str):
    cfg = ak.get_config()
    print(
        f"BREADTH FIRST SEARCH -- SINGLE MODE\n"
        f"server hostname = {cfg['serverHostname']}\n"
        f"number of locales = {cfg['numLocales']}\n"
        f"number of PUs = {cfg['numPUs']}\n"
        f"max tasks = {cfg['maxTaskPar']}\n"
        f"memory = {cfg['physicalMemory']}\n")

    # Split up filename parameter to only path and only name of file.
    filepath_and_filename = filename.rsplit("/", 1)
    only_filepath = filepath_and_filename[0] + "/"
    only_filename = filepath_and_filename[1]
    only_extension = filename.rsplit(".", 1)[1]

    # Read in the graph and perform BFS steps. 
    G = ar.read_edgelist(filename, filetype=only_extension)
    selectroot = np.random.randint(0, num_vertices-1, trials)
    start = time.time()
    for root in selectroot:
        ar.bfs_layers(G, int(root))
    end = time.time()
    avg = (end-start) / trials
    print("Average performance for {} trials for graph {}: {}".format(trials, only_filename, avg))

def bfs_batch(dirname:str):
    cfg = ak.get_config()
    print("BREADTH FIRST SEARCH -- BATCH MODE")
    print("server Hostname =", cfg["serverHostname"])
    print("Number of Locales=", cfg["numLocales"])
    print("number of PUs =", cfg["numPUs"])
    print("Max Tasks =", cfg["maxTaskPar"])
    print("Memory =", cfg["physicalMemory"])

def correctness():
    #TODO: simple correctness test!
    return
    
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
        help="Absolute path to directory with multiple files to preprocess (batch method)."
    )
    
    return parser

if __name__ == "__main__":    
    parser = create_parser()
    args = parser.parse_args()
    
    print("BREADTH FIRST SEARCH BENCHMARK")
    ak.verbose = False
    ak.connect(args.hostname, args.port)

    print(args)
    
    if args.filename is not None:
        bfs_single(args.filename)
    elif args.dirname is not None:
        bfs_batch(args.dirname)
    else:
        print("File name or directory name were not passed, function cannot proceed.")
        sys.exit(0)

    ak.shutdown()