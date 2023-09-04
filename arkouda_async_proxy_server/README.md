# arkouda\_async\_proxy\_server

## Background

The [arkouda\_async\_proxy\_server](src/server.rs) implements an async gRPC server pattern, immediately returning a response to the AsyncGrpcChannel. The current implementation subsequently returns the status of the Arkouda request via the AsyncGrpcChannel.get_request_status method. 


## Status

The AsyncGrpcChannel-arkouda\_async\_proxy\_server stack is currently under development and not currently operational.

## Running arkouda\_async\_arkouda\_server

The arkouda\_async\_proxy\_server is started with the following command executed from the arkouda\_async\_proxy\_server directory:

```
export ARKOUDA_PROXY_PORT=50053
export ARKOUDA_URL=tcp://localhost:5555
export RUST_LOG=debug

cargo run --bin arkouda_proxy_server $ARKOUDA_PROXY_PORT $ARKOUDA_URL
```