from __future__ import annotations
from typing import cast, Tuple, Union
from typeguard import typechecked
from arkouda.client import generic_msg
from arkouda.pdarrayclass import pdarray, create_pdarray
from arkouda.logger import getArkoudaLogger
from arkouda.dtypes import int64 as akint

__all__ = ["Graph",
           "DiGraph",
           "read_known_edgelist",
           "read_edgelist",
           "bfs_layers"
           ]

class Graph:
    """Base class for undirected graphs. 

    This is the double index graph data structure based graph representation. The graph data resides 
    on the arkouda server. The user should not call this class directly; rather its instances are 
    created by other arachne functions.

    Graphs hold undirected edges. Self loops and multiple edges are not allowed.

    Nodes currently are only allowed to be integers. They may contain optional key/value attributes.

    Edges are represented as links between nodes. They may contain optinal key/value attributes. 

    Parameters
    ----------
    None

    Attributes
    ----------
    n_vertices : int
        The number of vertices in the graph. 
    n_edges : int
        The number of edges in the graph.
    directed : int
        The graph is directed (True) or undirected (False).
    weighted : int
        The graph is weighted (True) or unweighted (False).
    name : string
        The name of the graph in the backend Chapel server. 
    logger : ArkoudaLogger
        Used for all logging operations.

    See Also
    --------
    DiGraph
        
    Notes
    -----
    """

    def __init__(self, *args) -> None:
        """Initializes the Graph instance by setting all instance
        attributes, some of which are derived from the array parameters.
        
        Parameters
        ----------
        n_vertices
            Must be provided in args[0].
        n_edges
            Must be provided in args[1].
        weighted
            Must be provided in args[3].
        name
            Must be provided in args[4].
        directed
            Defaults to 0 since Graph is inherently undirected. If needed,
            should be found in args[2].
        
            
        Returns
        -------
        None
        
        Raises
        ------
        RuntimeError
            Raised if there's an error from the server to create a graph.  
        ValueError
            Raised if not enough arguments are passed to generate the graph. 
        """
        try:
            if len(args) < 5:
                self.n_vertices = 0
                self.n_edges = 0
                self.weighted = None
                self.directed = 0
                self.name = None
            else:
                self.n_vertices = int(cast(int, args[0]))
                self.n_edges = int(cast(int, args[1]))
                self.weighted = int(cast(int, args[3]))
                oriname = cast(str, args[4])
                self.name = oriname.strip()
                self.directed = 0
        except Exception as e:
            raise RuntimeError(e)

        self.dtype = akint
        self.logger = getArkoudaLogger(name=__class__.__name__)

    def __iter__(self):
        """Currently, we do not provide a mechanism for iterating over arrays. The best workaround
        is to create an array of size n-1 where each element stores the index of the element
        location as an integeer. WARNING: This may create a very large array that Python may not be 
        able to handle.

        Returns
        -------
        None
        """
        raise NotImplementedError("""Graph does not support iteration. It is derived from
                                   Arkouda's pdarrays which also do not support iteration.""")

    def __len__(self) -> int:
        """Returns the number of vertices in the graph. Use: 'len(G)'.

        Returns
        -------
        n_vertices: int.
            The number of vertices in the graph.
        """
        return self.n_vertices

    def size(self) -> int:
        """Returns the number of edges in the graph. Use: 'G.size()'.

        Returns
        -------
        n_edges: int.
            The number of edges in the graph.
        """
        return self.n_edges

    def add_edges_from(self, akarray_src: pdarray, akarray_dst: pdarray, 
                       akarray_weight: Union[None, pdarray] = None) -> None:
        """Populates the graph object with edges as defined by the akarrays. 

        Returns
        -------
        None
        """
        cmd = "addEdgesFrom"

        if akarray_weight is not None:
            self.weighted = 1
        else:
            self.weighted = 0

        args = { "AkArraySrc" : akarray_src,
                 "AkArrayDst" : akarray_dst, 
                 "AkArrayWeight" : akarray_weight,
                 "Weighted" : bool(self.weighted),
                 "Directed": bool(self.directed) }
        
        repMsg = generic_msg(cmd=cmd, args=args)
        returned_vals = (cast(str, repMsg).split('+'))

        self.n_vertices = int(cast(int, returned_vals[0]))
        self.n_edges = int(cast(int, returned_vals[1]))
        self.weighted = int(cast(int, returned_vals[3]))
        oriname = cast(str, returned_vals[4])
        self.name = oriname.strip()

class DiGraph(Graph):
    """Base class for directed graphs. Inherits from Graph.

    This is the double index graph data structure based graph representation. The graph data resides 
    on the arkouda server. The user should not call this class directly; rather its instances are 
    created by other arachne functions.

    Graphs hold undirected edges. Self loops and multiple edges are not allowed.

    Nodes currently are only allowed to be integers. They may contain optional key/value attributes.

    Edges are represented as directed links between nodes. They may contain optional key/value 
    attributes. 

    Parameters
    ----------
    None

    Attributes
    ----------
    n_vertices : int
        The number of vertices in the graph. 
    n_edges : int
        The number of edges in the graph.
    directed : int
        The graph is directed (True) or undirected (False).
    weighted : int
        The graph is weighted (True) or unweighted (False).
    name : string
        The name of the graph in the backend Chapel server. 
    logger : ArkoudaLogger
        Used for all logging operations.

    See Also
    --------
    Graph
        
    Notes
    -----
    """

    def __init__(self, *args) -> None:
        """Initializes the Graph instance by setting all instance
        attributes, some of which are derived from the array parameters.
        
        Parameters
        ----------
        n_vertices
            Must be provided in args[0].
        n_edges
            Must be provided in args[1].
        weighted
            Must be provided in args[3].
        name
            Must be provided in args[4].
        directed
            Defaults to 1 since DiGraph is inherently directed. If needed,
            should be found in args[2].
         
        Returns
        -------
        None
        
        Raises
        ------
        RuntimeError
            Raised if there's an error from the server to create a graph.   
        ValueError
            Raised if not enough arguments are passed to generate the graph. 
        """
        try:
            if len(args) < 5:
                self.n_vertices = 0
                self.n_edges = 0
                self.weighted = None
                self.directed = 1
                self.name = None
            else:
                self.n_vertices = int (cast(int, args[0]))
                self.n_edges = int(cast(int, args[1]))
                self.weighted = int(cast(int, args[3]))
                oriname = cast(str, args[4])
                self.name = oriname.strip()
                self.directed = 1
        except Exception as e:
            raise RuntimeError(e)

        self.dtype = akint
        self.logger = getArkoudaLogger(name=__class__.__name__)

@typechecked
def read_known_edgelist(ne: int, nv: int, path: str, weighted: bool = False, directed: bool = False, 
                        comments: str = "#", filetype: str = "txt") -> Union[Graph, DiGraph]:
    """ This function is used for creating a graph from a file containing an edge list. To save 
    time, this method exists for when the number of edges and vertices are known a priori. We also
    assume that the graph, by nature, does not have self-loops nor multiple edges. TODO: this 
    should be used after a preprocessing() method! 
    
    The file typically looks as below delimited by whitespaces. TODO: add more delimitations.
        1       5
        13      9
        7       6 
    This file givs the edges of the graph which are <1,5>, <13,9>, <7,6> in this case. If an 
    additional column is added, it is the weight of each edge. We assume the graph is unweighted 
    unless stated otherwise. 

    Parameters
    ----------
    ne
        The total number of edges of the graph.
    nv
        The total number of vertices of the graph.
    path
        Absolute path to where the file is stored. 
    weight
        True if the graph is to be weighted, False otherwise. 
    comments
        If a line in the file starts with this string, the line is ignored and not read. 
    filetype:
        Exists to read an mtx file differently without needing to modify the mtx file before
        reading it in. If reading an mtx file change to mtx.
    create_using:
        Specify the type of graph to be created. If just undirected, do not change, change if
        reading in a directed graph. 

    Returns
    -------
    Graph | DiGraph
        The Graph or DiGraph object to represent the edge list data. 
    
    See Also
    --------
    
    Notes
    -----
    
    Raises
    ------  
    RuntimeError
    """
    cmd = "readKnownEdgelist"
    args = { "NumOfEdges" : ne, 
             "NumOfVertices" : nv,
             "Path": path,
             "Weighted" : weighted,
             "Directed": directed,
             "Comments" : comments,
             "FileType" : filetype }
    repMsg = generic_msg(cmd=cmd, args=args)

    if not directed:
        return Graph(*(cast(str, repMsg).split('+')))
    else:
        return DiGraph(*(cast(str, repMsg).split('+')))

@typechecked
def read_edgelist(path: str, weighted: bool = False, directed: bool = False, comments: str = "#",\
                  filetype: str = "txt") -> Union[Graph, DiGraph]:
    """ This function is used for creating a graph from a file containing an edge list.
        
    The file typically looks as below delimited by whitespaces. TODO: add more delimitations.
        1       5
        13      9
        7       6 
    This file givs the edges of the graph which are <1,5>, <13,9>, <7,6> in this case. If an 
    additional column is added, it is the weight of each edge. We assume the graph is unweighted 
    unless stated otherwise. 

    Parameters
    ----------
    path
        Absolute path to where the file is stored. 
    weight
        True if the graph is to be weighted, False otherwise. 
    comments
        If a line in the file starts with this string, the line is ignored and not read. 
    filetype:
        Exists to read an mtx file differently without needing to modify the mtx file before
        reading it in. If reading an mtx file change to mtx.
    create_using:
        Specify the type of graph to be created. If just undirected, do not change, change if
        reading in a directed graph. 

    Returns
    -------
    Graph | DiGraph
        The Graph or DiGraph object to represent the edge list data. 
    
    See Also
    --------
    
    Notes
    -----
    
    Raises
    ------  
    RuntimeError
    """
    cmd = "readEdgelist"
    args = { "Path": path,
             "Weighted" : weighted,
             "Directed": directed,
             "Comments" : comments,
             "FileType" : filetype}
    repMsg = generic_msg(cmd=cmd, args=args)

    if not directed:
        return Graph(*(cast(str, repMsg).split('+')))
    else:
        return DiGraph(*(cast(str, repMsg).split('+')))

@typechecked
def bfs_layers(graph: Graph, source: int) -> pdarray:
    """ This function generates the breadth-first search sequence of the vertices in a given graph
        starting from the given source vertex.
        
        Returns
        -------
        pdarray
            The depth of each vertex in relation to the source vertex. 
        
        See Also
        --------
        
        Notes
        -----
        
        Raises
        ------  
        RuntimeError
        """
    cmd = "segmentedGraphBFS"
    args = { "NumOfVertices":graph.n_vertices,
             "NumOfEdges":graph.n_edges,
             "Directed":graph.directed,
             "Weighted":graph.weighted,
             "GraphName":graph.name,
             "Source":source}

    repMsg = generic_msg(cmd=cmd, args=args)
    return create_pdarray(repMsg)