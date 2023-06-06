use std::env;

use tonic::{transport::Server, Request, Response, Status};

use arkouda::arkouda_server::{Arkouda, ArkoudaServer};
use arkouda::{ArkoudaReply, ArkoudaRequest};

use serde::{Deserialize, Serialize};
use serde_json::json;

#[derive(Serialize, Deserialize)]
struct ArkoudaMessage {
    user: String,
    cmd: String,
    format: String,
    token: String,
    size: i32,
    args: String
}

pub mod arkouda {
    tonic::include_proto!("arkouda");
}

#[derive(Debug, Default)]
pub struct ArkServer {
    url: String
}

#[tonic::async_trait]
impl Arkouda for ArkServer {
    async fn handle_request(&self, request: Request<ArkoudaRequest>) -> Result<Response<ArkoudaReply>, Status> {
        let req = request.into_inner();

        let ctx = zmq::Context::new();
        let socket = ctx.socket(zmq::REQ).unwrap();

        socket.connect(&self.url).unwrap();
        
        // Generate and send message
        let am = json!(ArkoudaMessage{user: String::from(req.user),
                                cmd:  String::from(req.cmd),
                                format:  String::from(req.format),
                                token:  String::from(req.token),
                                size: req.size,
                                args: String::from(req.args)
                                });
        let msg = &am.to_string();

        send_message(&socket,msg);

        // Receive and process response
        let result = recv_message(&socket);
        println!("Return message is {}",result);

        let reply = arkouda::ArkoudaReply {
            message: format!("{}", result).into(),
        };

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

    let args: Vec<String> = env::args().collect();
    let url = &args[1];

    let addr = "[::1]:50053".parse()?;
    let arkouda = ArkServer {url:url.to_string()};

    Server::builder()
        .add_service(ArkoudaServer::new(arkouda))
        .serve(addr)
        .await?;

    Ok(())
}