# arkouda\_proxy\_server

# Background

The arkouda\_proxy\_server is a gRPC server written in Rust that provides a proxy to the arkouda\_server. arkouda\_proxy\_server enables features such as multiplexed and bidirectional comms that better support multiuser arkouda\_server instances. 

# Running arkouda\_proxy\_server

## Setting Log Level

arkouda\_proxy\_server can be run with logging set to the DEBUG or INFO level, setting the RUST_LOG env variable accordingly

The arkouda_proxy_server is started with the following command executed from the arkouda_proxy_server directory

```
export ARKOUDA_PROXY_PORT=50053
export ARKOUDA_URL=tcp://shickadance:5555
export RUST_LOG=debug

cargo run --bin arkouda_proxy_server $ARKOUDA_PROXY_PORT $ARKOUDA_URL
```

# Handling Arkouda Requests

The arkouda\_proxy\_server processes the incoming protobuf ArkoudaRequest message, translates the message into an ArkoudaMessage and sends it to the arkouda\_server via the Rust zmq client. Once the incoming request has been received and processed by arkouda\_server, the arkouda\_proxy\_server parses the return message, creates a corresponding protobuf ArkoudaReply and returns it to the arkouda\_proxy\_client GrpcChannel.

Example arkouda\_proxy_\server startup and logging:

```
export ARKOUDA_PROXY_PORT=50053
export ARKOUDA_URL=tcp://shickadance:5555
export RUST_LOG=debug

$ cargo run --bin arkouda_proxy_server $ARKOUDA_PROXY_PORT $ARKOUDA_URL
    Finished dev [unoptimized + debuginfo] target(s) in 0.43s
     Running `target/debug/arkouda_proxy_server 50053 'tcp://shickadance:5555'`
[2023-06-26T11:31:17Z INFO  arkouda_proxy_server] listening on: [::1]:50053 configured for arkouda at tcp://shickadance:5555
[2023-06-26T11:32:09Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"","cmd":"connect","format":"STRING","size":-1,"token":"","user":"kjyost"}
[2023-06-26T11:32:10Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"connected to arkouda server tcp://*:5555", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
[2023-06-26T11:32:10Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"[]","cmd":"getconfig","format":"STRING","size":0,"token":"","user":"kjyost"}
[2023-06-26T11:32:10Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"{\"arkoudaVersion\":\"v2023.06.16\", \"chplVersion\":\"1.30.0\", \"ZMQVersion\":\"4.3.4\", \"HDF5Version\":\"1.12.1\", \"serverHostname\":\"shickadance\", \"ServerPort\":5555, \"numLocales\":1, \"numPUs\":2, \"maxTaskPar\":2, \"physicalMemory\":20834103296, \"distributionType\":\"BlockDom(1,int(64),false,unmanaged DefaultDist)\", \"LocaleConfigs\":[{\"id\":0, \"name\":\"shickadance\", \"numPUs\":2, \"maxTaskPar\":2, \"physicalMemory\":20834103296}], \"authenticate\":false, \"logLevel\":\"INFO\", \"logChannel\":\"CONSOLE\", \"regexMaxCaptures\":20, \"byteorder\":\"little\", \"autoShutdown\":false, \"serverInfoNoSplash\":false,\"ARROW_VERSION\":\"9.0.0\"}", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
[2023-06-26T11:33:30Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"[\"{\\\"key\\\": \\\"size\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"str\\\", \\\"val\\\": \\\"1000000\\\"}\", \"{\\\"key\\\": \\\"dtype\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"str\\\", \\\"val\\\": \\\"int64\\\"}\", \"{\\\"key\\\": \\\"low\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"str\\\", \\\"val\\\": \\\"0\\\"}\", \"{\\\"key\\\": \\\"high\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"str\\\", \\\"val\\\": \\\"100\\\"}\", \"{\\\"key\\\": \\\"seed\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"NoneType\\\", \\\"val\\\": \\\"None\\\"}\"]","cmd":"randint","format":"STRING","size":5,"token":"","user":"kjyost"}
[2023-06-26T11:33:31Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"created id_Uz5jtoB_5 int64 1000000 1 (1000000,) 8", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
[2023-06-26T11:33:31Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"[\"{\\\"key\\\": \\\"name\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"str\\\", \\\"val\\\": \\\"id_Uz5jtoB_4\\\"}\"]","cmd":"delete","format":"STRING","size":1,"token":"","user":"kjyost"}
[2023-06-26T11:33:31Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"deleted id_Uz5jtoB_4", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
[2023-06-26T11:33:37Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"[\"{\\\"key\\\": \\\"x\\\", \\\"objType\\\": \\\"PDARRAY\\\", \\\"dtype\\\": \\\"int64\\\", \\\"val\\\": \\\"id_Uz5jtoB_5\\\"}\"]","cmd":"mean","format":"STRING","size":1,"token":"","user":"kjyost"}
[2023-06-26T11:33:37Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"float64 49.481762000000003", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
[2023-06-26T11:33:43Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"[\"{\\\"key\\\": \\\"func\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"str\\\", \\\"val\\\": \\\"cos\\\"}\", \"{\\\"key\\\": \\\"array\\\", \\\"objType\\\": \\\"PDARRAY\\\", \\\"dtype\\\": \\\"int64\\\", \\\"val\\\": \\\"id_Uz5jtoB_5\\\"}\"]","cmd":"efunc","format":"STRING","size":2,"token":"","user":"kjyost"}
[2023-06-26T11:33:44Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"created id_Uz5jtoB_6 float64 1000000 1 (1000000,) 8", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
[2023-06-26T11:33:44Z DEBUG arkouda_proxy_server] Sending message to Arkouda: {"args":"[\"{\\\"key\\\": \\\"array\\\", \\\"objType\\\": \\\"PDARRAY\\\", \\\"dtype\\\": \\\"float64\\\", \\\"val\\\": \\\"id_Uz5jtoB_6\\\"}\", \"{\\\"key\\\": \\\"printThresh\\\", \\\"objType\\\": \\\"VALUE\\\", \\\"dtype\\\": \\\"int\\\", \\\"val\\\": \\\"100\\\"}\"]","cmd":"repr","format":"STRING","size":2,"token":"","user":"kjyost"}
[2023-06-26T11:33:44Z DEBUG arkouda_proxy_server] Return message from Arkouda: {"msg":"array([-0.43217794488477829 0.24954011797333814 0.56975033426531196 ... 0.94967769788254319 -0.62644444791033904 0.17171734183077755])", "msgType":"NORMAL", "msgFormat":"STRING", "user":"kjyost"}
```
