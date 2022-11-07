from __future__ import annotations
from typing import cast, Tuple, Union
from typeguard import typechecked
from arkouda.client import generic_msg
from arkouda.pdarrayclass import pdarray, create_pdarray
from arkouda.logger import getArkoudaLogger
from arkouda.dtypes import int64 as akint

__all__ = ["Graph",
           "read_edgelist",
           "bfs_edges"
           ]

class Graph:
    """
    This is a double index graph data structure based graph representation. The graph data resides on the
    arkouda server. The user should not call this class directly;
    rather its instances are created by other arkouda functions.
    Attributes
    ----------
    n_vertices : int
        The starting indices for each string
    n_edges : int
        The starting indices for each string
    directed : int
        The graph is directed (True) or undirected (False)
    weighted : int
        The graph is weighted (True) or not
    name : string
        The graph name in Chapel
    logger : ArkoudaLogger
        Used for all logging operations
        
    Notes
    -----
    """

    def __init__(self, *args) -> None:
        """
        Initializes the Graph instance by setting all instance
        attributes, some of which are derived from the array parameters.
        
        Parameters
        ----------
        n_vertices  : must provide args[0]
        n_edges     : must provide args[1]
        directed    : must provide args[2]
        weighted    : must provide args[3]
        name        : must provide args[4]
        
            
        Returns
        -------
        None
        
        Raises
        ------
        RuntimeError
            Raised if there's an error converting a Numpy array or standard
            Python array to either the offset_attrib or bytes_attrib   
        ValueError
            Raised if there's an error in generating instance attributes 
            from either the offset_attrib or bytes_attrib parameter 
        """
        try:
            if len(args) < 5:
                raise ValueError
            self.n_vertices = int (cast(int, args[0]))
            self.n_edges = int(cast(int, args[1]))
            self.directed = int(cast(int, args[2]))
            self.weighted = int(cast(int, args[3]))
            oriname=cast(str, args[4])
            self.name = oriname.strip()
        except Exception as e:
            raise RuntimeError(e)

        self.dtype = akint
        self.logger = getArkoudaLogger(name=__class__.__name__)  # type: ignore

    def __iter__(self):
        raise NotImplementedError('Graph does not support iteration')

    def __size__(self) -> int:
        return self.n_vertices

@typechecked
def read_edgelist(Ne: int, Nv: int, Ncol: int, directed: int, filename: str,\
                    RemapFlag:int=1, DegreeSortFlag:int=0, RCMFlag:int=0, WriteFlag:int=0, BuildAlignedArray:int=0) -> Graph:
    """
        This function is used for creating a graph from a file.
        The file should like this
          1   5
          13  9
          7   6 
        This file means the edges are <1,5>,<13,9>,<7,6>. If additional column is added, it is the weight
        of each edge.
        Ne : the total number of edges of the graph
        Nv : the total number of vertices of the graph
        Ncol: how many column of the file. Ncol=2 means just edges (so no weight and weighted=0) 
              and Ncol=3 means there is weight for each edge (so weighted=1). 
        directed: 0 means undirected graph and 1 means directed graph
        filename: the file that has the edge list
        RemapFlag: if the vertex ID is larger than the total number of vertices, we will relabel the vertex ID
        DegreeSortFlag: we will let small vertex ID be the vertex whose degree is small
        RCMFlag: we will remap the vertex ID based on the RCM algorithm
        WriteFlag: we will output the final edge list src->dst array as a new input file.
        BuildAlignedArray: using the Edge-Vertex-Locale aligned mapping instead of the default distribution
        Returns
        -------
        Graph
            The Graph class to represent the data
        See Also
        --------
        Notes
        -----
        
        Raises
        ------  
        RuntimeError
        """
    cmd = "segmentedGraphFile"
    #args = "{} {} {} {} {} {} {} {} {} {}".format(Ne, Nv, Ncol, directed, filename, \
    #        RemapFlag, DegreeSortFlag, RCMFlag, WriteFlag,BuildAlignedArray)
    args = {"NumOfEdges":Ne, "NumOfVertices":Nv, "NumOfColumns":Ncol,\
             "Directed":directed, "FileName":filename, \
            "RemapFlag":RemapFlag, "DegreeSortFlag":DegreeSortFlag,\
            "RCMFlag":RCMFlag, "WriteFlag":WriteFlag,"AlignedFlag":BuildAlignedArray}
    repMsg = generic_msg(cmd=cmd, args=args)

    return Graph(*(cast(str, repMsg).split('+')))

@typechecked
def bfs_edges(graph: Graph, root: int, rcm_flag:int) -> pdarray:
    """
        This function is generating the breadth-first search vertices sequences in given graph
        starting from the given root vertex
        Returns
        -------
        pdarray
            The bfs vertices results
        See Also
        --------
        Notes
        -----
        
        Raises
        ------  
        RuntimeError
        """
    cmd = "segmentedGraphBFS"
    DefaultRatio = -0.9
    #args = "{} {} {} {} {} {} {} {}".format(
    #    rcm_flag, graph.n_vertices, graph.n_edges,
    #    graph.directed, graph.weighted, graph.name, root, DefaultRatio)
    args = {"RCMFlag":RCMFlag,"NumOfVertices":graph.n_vertices,"NumOfEdges":graph.n_edges,\
             "Directed":graph.directed,"Weighted": graph.weighted,\
             "GraphName":graph.name,"Root":root,"Ratio":DefaultRatio}

    repMsg = generic_msg(cmd=cmd, args=args)
    return create_pdarray(repMsg)