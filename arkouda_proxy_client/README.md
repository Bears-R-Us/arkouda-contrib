# arkouda\_proxy\_client

The arkouda\_proxy\_client is a Python client module that accesses the arkouda\_proxy\_server gRPC server.

# Artifacts

## arkouda.proto file

The [arkouda.proto](proto/arkouda.proto) file contains the protobuf ArkoudaRequest and ArkoudaResponse message definitions:

```
syntax = "proto3";
package arkouda;

service Arkouda {
   rpc HandleRequest(ArkoudaRequest) returns (ArkoudaResponse) {}
}

message ArkoudaRequest {
    string user=1;
    string token=2;
    string cmd=3;
    string format=4;
    int32 size=5;
    string args=6;
}

message ArkoudaResponse {
    string message=1;
}
```

## protobuf Python Modules

Python protobuf wrapper modules and classes enable translation of protobuf ArkoudaRequest and ArkoudaReply classes into corresponding Python classes.

## Generation of protobuf Modules

The Python protobuf modules and classes are generated via the following python3 command executed from the [arkouda\_proxy\_client](arkouda_proxy_client) directory:

```
python3 -m grpc_tools.protoc -I./proto --python_out=. --pyi_out=. --grpc_python_out=. ./proto/arkouda.proto
```

The corresponding files are as follows:

```
arkouda_pb2.py
arkouda_pb2.pyi
arkouda_pb2_grpc.py
```

## Post-Generation protobuf Module Updates

As of the original version of arkouda\_proxy\_client a slight update is needed within the [arkouda_pb2_grpc](./arkouda_proxy_client/arkouda_pb2_grpc.py). Specifically, the import statement must be changed as follows:

from...

```
from import arkouda_pb2 as arkouda__pb2
```
...to...

```
from . import arkouda_pb2 as arkouda__pb2
```

Otherwise, an import error occurs in the [client](arkouda_proxy_client) module. 

# Installation

## Install Arkouda

Since there currently is no pypi Arkouda install, Arkouda must first be installed locally.

## Install arkouda\_proxy\_client

From the arkouda\_proxy\_client root directory, execute the following command:

```
pip install -e .
```

# Accessing gRPC Proxy via arkouda_proxy_client

## Background

The arkouda_proxy [client](arkouda_proxy_client) module contains the GrpcChannel, which encapsulates all logic for connecting to the Arkouda gRPC proxy server as well as sending/receiving protobuf request/response messages. The GrpcChannel extends the Arkouda [Channel](https://github.com/Bears-R-Us/arkouda/blob/c5eb42f48c0f91e389b09d808f9d33e315975421/arkouda/client.py#L150) class, which will enable eventual integration of the arkouda_proxy_client into Arkouda.

## Command Sequence for Using arkouda\_proxy\_client

### Creating the GrpcChannel Object

An example command sequence of creating the GrpcChannel object is as follows: 

```
from arkouda_proxy_client.client import GrpcChannel
channel = GrpcChannel(connect_url='localhost:50053', user='kjyost')
```

The two required parameters are the connect_url and the user. The connect_url is composed of the arkouda_proxy_server host ip address, host name, or service name and the port in the form of host:port. 

### Setting the Arkouda client Channel

The Arkouda client Channel defaults to [ZmqChannel](https://github.com/Bears-R-Us/arkouda/blob/c5eb42f48c0f91e389b09d808f9d33e315975421/arkouda/client.py#L360). Passing the GrpcChannel object into the Arkouda client connect method sets the GrpcChannel object as the Arkouda client channel as shown below:

```
>>> import arkouda as ak
    _         _                   _       
   / \   _ __| | _____  _   _  __| | __ _ 
  / _ \ | '__| |/ / _ \| | | |/ _` |/ _` |
 / ___ \| |  |   < (_) | |_| | (_| | (_| |
/_/   \_\_|  |_|\_\___/ \__,_|\__,_|\__,_|
                                          

Client Version: v2023.06.16+7.g37e2e4f2.dirty
>>> from arkouda_proxy_client.client import GrpcChannel
>>> channel = GrpcChannel(connect_url='localhost:50053', user='kjyost')
>>> ak.connect(access_channel=channel)
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response connected to arkouda server tcp://*:5555
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response {"arkoudaVersion":"v2023.06.16", "chplVersion":"1.30.0", "ZMQVersion":"4.3.4", "HDF5Version":"1.12.1", "serverHostname":"shickadance", "ServerPort":5555, "numLocales":1, "numPUs":2, "maxTaskPar":2, "physicalMemory":20834103296, "distributionType":"BlockDom(1,int(64),false,unmanaged DefaultDist)", "LocaleConfigs":[{"id":0, "name":"shickadance", "numPUs":2, "maxTaskPar":2, "physicalMemory":20834103296}], "authenticate":false, "logLevel":"INFO", "logChannel":"CONSOLE", "regexMaxCaptures":20, "byteorder":"little", "autoShutdown":false, "serverInfoNoSplash":false,"ARROW_VERSION":"9.0.0"}
/Users/kjyost/development/git/hokiegeek2-forks/arkouda/arkouda/client.py:596: RuntimeWarning: Version mismatch between client (v2023.06.16+7.g37e2e4f2.dirty) and server (v2023.06.16); this may cause some commands to fail or behave incorrectly! Updating arkouda is strongly recommended.
  warnings.warn(
connected to arkouda server tcp://*:5555
```

Once the ak.connect() method is invoked, the Arkouda client operates normally with all requests going through the GrpcChannel as shown below:

```
>>> ones = ak.ones(100000000)
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response created id_XfxKShO_1 float64 100000000 1 (100000000,) 8
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response set id_XfxKShO_1 to 1.000000e+00
>>> ones * 8
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response created id_XfxKShO_2 float64 100000000 1 (100000000,) 8
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response array([8 8 8 ... 8 8 8])
array([8 8 8 ... 8 8 8])
>>> nums = ak.randint(0,10,1000)
[Arkouda Client] Line 20 DEBUG: Sending request to Arkouda gRPC ...
[Arkouda Client] Line 24 DEBUG: Arkouda gRPC client received response created id_XfxKShO_3 int64 1000 1 (1000,) 8
>>> 

```