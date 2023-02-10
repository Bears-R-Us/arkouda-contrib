# Arachne: Graph Analysis Extension to Arkouda

## Overview
The Arachne project provides an extension to Arkouda that mimics the NetworkX API for graph analysis based off Arkouda `pdarrays`.

## Installation
Follow the install instructions specified in the main directory of arkouda-cotnrib. 

When properly built, navigate to both the Arkouda and Arachne main client repos and execute the following commands:
```
pip3 install -e /path/to/arachne/client/.
pip3 install -e /path/to/arkouda/.
```

## Usage
Functions currently available can be found in `client/README.md` with a benchmark file that can be used as a sample found in `benchmarks/bfs.py`. Sample executions of benchmark file follow.

For benchmarking a single graph you can execute: 
```
python3 bfs.py node port -f /path/to/arkouda-contrib/arachne/data/karate.mtx -t 10
```

For benchmaarking a directory of graphs you can execute: 
```
python3 bfs.py node01 5554 -d /path/to/arkouda-contrib/arachne/data -t 10
```

## Testing
The Arachne tests are executed from the arkouda-contrib directory as follows:
```
python3 -m pytest arachne/test/bfs_test.py arachne/test/reading_test.py arachne/test/class_test.py
```
**Note**: Errors when executing using pytest from arachne directory. 