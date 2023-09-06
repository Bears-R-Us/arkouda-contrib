pub mod streaming_arkouda {
    tonic::include_proto!("streaming_arkouda");
}

use std::env;
use std::future::{Future, Pending};
use std::task::{Poll, Ready};
use log::{info,debug};
use tokio_stream::StreamExt;
use tonic::{transport::Server, Request, Response, Status, Streaming};

use serde::{Deserialize, Serialize};
use serde_json::json;

use zmq::{Socket, Context};

use streaming_arkouda::streaming_arkouda_server::{StreamingArkouda, StreamingArkoudaServer};
use streaming_arkouda::{ArkoudaReply, ArkoudaRequest};

#[derive(Serialize, Deserialize)]
struct ArkoudaMessage {
    user: String,
    cmd: String,
    format: String,
    token: String,
    size: i32,
    args: String
}


pub struct ZmqRead<'a> {
    socket: &'a Socket,
}

trait ZmqFuture {
    type Output;
    result: String;
    fn poll(&mut self, wake: fn()) -> Poll<Self::Output>;
}

impl ZmqFuture for ZmqRead<'_> {
    type Output = Vec<u8>;

    fn poll(&mut self, wake: fn()) -> Poll<Self::Output> {
        if self.socket.rcv_buff() {
            // The socket has data -- read it into a buffer and return it.
            Poll::Ready(self.socket.recv_msg())
        } else {
            // The socket does not yet have data.
            //
            // Arrange for `wake` to be called once data is available.
            // When data becomes available, `wake` will be called, and the
            // user of this `Future` will know to call `poll` again and
            // receive data.
            self.socket.set_readable_callback(wake);
            Poll::Pending
        }
    }
}

#[derive(Debug, Default)]
pub struct StreamingArkServer {
    url: String
}


#[tonic::async_trait]
impl StreamingArkouda for StreamingArkServer {

    async fn handle_request_stream(&self, request: Request<Streaming<ArkoudaRequest>>) -> Result<Response<ArkoudaReply>, Status> {
        debug!("received message from Arkouda");
        let mut stream = request.into_inner();

        let ctx = Context::new();
        let socket = ctx.socket(zmq::REQ).unwrap();

        socket.connect(&self.url).unwrap();
        
        let mut reply = ArkoudaReply::default();
        
        while let Some(arkouda_request) = stream.next().await {
            let ar = arkouda_request?;
            debug!("Received message from Arkouda client");

            // Generate and send message to arkouda_server
            let am = json!(ArkoudaMessage{user: String::from(ar.user),
                                          cmd:  String::from(ar.cmd),
                                          format:  String::from(ar.format),
                                          token:  String::from(ar.token),
                                          size: ar.size,
                                          args: String::from(ar.args)
                                          });
            let msg = &am.to_string();
        
            debug!("Sending message to Arkouda: {}", msg);        

            send_message(&socket,msg);

            // Receive and process response
            let result = recv_message(&socket);

            debug!("Return message from Arkouda: {}", result);

            reply.message = format!("{}", result).into();
        }
        debug!("Result from Arkouda: {}", reply.message);
        Ok(Response::new(reply))
    }
}

fn send_message(socket: &zmq::Socket, msg: &str) {
    socket.send(msg,0).unwrap();
}

fn recv_message(socket: &zmq::Socket) -> String  {
    let return_msg = socket.recv_msg(0).unwrap();
    let result = return_msg.as_str().unwrap();
    return result.to_string();
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    let port = &args[1];
    let arkouda_url = &args[2].to_string();
    
    //Generate SocketAddr
    let addr_str = "[::1]:${PORT}".to_string().replace("${PORT}",port);
    let addr = addr_str.parse()?;

    let streaming_arkouda = StreamingArkServer {url:arkouda_url.to_string()};

    info!("listening on: {} configured for arkouda at {}", addr, arkouda_url);

    Server::builder()
        .add_service(StreamingArkoudaServer::new(streaming_arkouda))
        .serve(addr)
        .await?;

    Ok(())
}