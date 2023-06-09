# arkouda_proxy_client

The arkouda\_proxy\_client project encapsulates Python code and gPRC bindings to enable Python access via the Arkouda gPRC proxy server.

# Requirements

arkouda\_proxy\_client depends upon the grpcio and grpcio-tools libraries

# Building Protobuf Bindings

From the project home execute the following Python command

```
python3 -m grpc_tools.protoc -I./proto --python_out=. --pyi_out=. --grpc_python_out=. ./proto/arkouda.proto
```
