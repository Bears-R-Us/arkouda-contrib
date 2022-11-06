# Arachne

## Abstract
Due to the emergence of massive real-world graphs such as social networks, computer networks, and genomes, whose sizes extend to terabytes, new tools must be developed to enable data scientists to handle such graphs efficiently. Arkouda has been developed to allow users to perform massively parallel computations on distributed data with an interface similar to NumPy. This Python package is ubiquitous in the world of Python data science workflows. Based on the Arkouda framework, we have developed a fundamental graph data structure and operations to support graph analytics. Futher, several typical graph algorithms were developed in Chapel to form a basic algorithm library. The methods we have implemented thus far include breadth-first search (BFS), connected components (CC), k-truss (KT), calculating the jaccard coefficient (JC), triangle counting (TC), and triangle centrality (TCE). All our work has been organized as an Arkouda extension package, and it is publicly available on GitHub.

## Modules
- `bfs()` returns a depth array with how far each vertex is from the source vrteex.