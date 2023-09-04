# arkouda\_async\_proxy\_server

## Background

The [arkouda\_async\_proxy\_server](src/server.rs) implements an async gRPC server pattern, immediately returning a response to the AsyncGrpcChannel. The current implementation subsequently returns the status of the Arkouda request via the AsyncGrpcChannel.get_request_status method. 


## Status

The AsyncGrpcChannel-arkouda\_async\_proxy\_server stack is currently under development and not currently operational.