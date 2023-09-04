# arkouda\_proxy\_client

The arkouda\_proxy\_client is a Python client module encapsulating Arkouda [Channel](https://github.com/Bears-R-Us/arkouda/blob/f4694ad97fef0decda389d2648668eab1a59da24/arkouda/client.py#L238) implementions that access Arkouda via an Arkouda gRPC proxy server implementation.

# Artifacts

## arkouda.proto file

The [arkouda.proto](proto/arkouda.proto) file contains the protobuf ArkoudaRequest and ArkoudaResponse message definitions used to generate the protobuf objects that are the transport message formats used to communicate with the Arkouda gRPC proxy server:

```
syntax = "proto3";
package arkouda;

service Arkouda {
   rpc HandleRequest(ArkoudaRequest) returns (ArkoudaResponse) {}
}

message ArkoudaRequest {
	// arkouda user connecting to arkouda_server via arkouda gRPC proxy
    string user=1;

    // token for arkouda_server configured for authentication
    string token=2;

    // arkouda_server command to be executed
    string cmd=3;

    // encapsulated message format, either STRING or BINARY
    string format=4;

    // number of args
    int32 size=5;

    // 0..n cmd args
    string args=6;

    // optional request_id
    optional string request_id=7;
}

// Encapsulates single-line response from the arkouda_server
message ArkoudaResponse {
	// arkouda_server response
    string message=1;

    // optional request_id corresponding to the response
    optional string request_id=2;

    // status of request (PENDING, RUNNING, FINISHED)
    optional string request_status=3;

	// arkouda user connecting to arkouda_server via arkouda gRPC proxy
    optional string user=4;

    // cmd requested via async proxy
    optional string cmd=5;

    // 0..n cmd args
    optional string args=6;
}
```

## protobuf Python Modules

Python protobuf wrapper modules and classes enable translation of protobuf ArkoudaRequest and ArkoudaReply classes into corresponding Python classes.

## Generation of protobuf Modules

The Python protobuf modules and classes are generated via the following python3 command executed from the [arkouda\_proxy\_client](arkouda_proxy_client) directory containing Python and proto files:

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

As of the original version of arkouda\_proxy\_client, a slight update is needed within the [arkouda_pb2_grpc](./arkouda_proxy_client/arkouda_pb2_grpc.py) file. Specifically, the import statement must be changed as follows:

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

The [arkouda\_proxy_client](arkouda_proxy_client) module contains the GrpcChannel, AsyncGrpcChannel, and 
PollingGrpcChannel classes, which each encapsulate all logic for connecting to the Arkouda gRPC proxy server as well as sending/receiving protobuf request/response messages. 

The GrpcChannel extends the Arkouda [Channel](https://github.com/Bears-R-Us/arkouda/blob/c5eb42f48c0f91e389b09d808f9d33e315975421/arkouda/client.py#L150) class, which will enable eventual integration of the arkouda\_proxy\_client into Arkouda.

The PollingAsyncGrpcChannel class is a gRPC implementation of Arkouda Channel that supports polling asynchronous gRPC requests to the arkouda\_proxy\_server. Specifically, PollingAsyncGrpcChannel launches a gRPC request asynchronously, invokes asyncio.sleep for a configurable amount of time, rechecks the status of the request, continuing this cycle until arkouda_server sends back the response,

Finally, the prototype AsyncGrpcChannel class extends the GrpcChannel class by enabling non-blocking async requests to the arkouda\_async\_proxy]\_server via the "fire-and-forget" pattern where the eventual Arkouda result is either retrieved from the arkouda\_async\_proxy\_server (current implementation) or is streamed back to the client via bidirectional gRPC (future implementation). Important note: the AsyncGrpcChannel is not currently operational due to one or both of the two following issues. Firstly, several client methods encapsulate 2..n Arkouda client-server roundtrips, which will require additional metadata to ensure all execute in the correct order. Secondly, several methods such as get_config_msg parse the return message from Arkouda and, as a consequence, 1..n KeyErrors occur when the arkouda_async_proxy_server returns a handle to an async method invocation instead of the expected Arkouda payload. Additional design and development are required to enable the AsyncGrpcChannel 


## Command Sequence for Using arkouda\_proxy\_client

### Creating the GrpcChannel, PollingAsyncGrpcChannel, or AsyncGrpcChannel Object

An example command sequence of creating the GrpcChannel object is as follows: 

```
from arkouda_proxy_client.client import GrpcChannel
channel = GrpcChannel(connect_url='localhost:50053', user='kjyost')
```

The two required parameters are the connect_url and the user. The connect\_url is composed of the arkouda\_proxy\_server/arkouda\_async\_proxy\_server host ip address, host name, or service name and the port in the form of host:port. 

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