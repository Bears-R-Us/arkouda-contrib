# arkouda\_proxy\_client

The arkouda\_proxy\_client is a Python client module that accesses the arkouda\_proxy\_server gRPC server.

## Artifacts

### arkouda.proto file

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

### Protobuf Files

The Protobuf files are generated via the following python command executed from the python\_proxy\_client directory:

```
python3 -m grpc_tools.protoc -I./proto --python_out=. --pyi_out=. --grpc_python_out=. ./proto/arkouda.proto
```

The corresponding files are as follows:

```
arkouda_pb2.py
arkouda_pb2.pyi
arkouda_pb2_grpc.py
```
