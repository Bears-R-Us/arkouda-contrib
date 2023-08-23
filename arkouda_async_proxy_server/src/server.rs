use std::env;

use log::{info,debug};

use tonic::{transport::Server, Request, Response, Status};

use arkouda::arkouda_server::{Arkouda, ArkoudaServer};
use arkouda::{ArkoudaReply, ArkoudaRequest};

use serde::{Deserialize, Serialize};
use serde_json::json;

use tokio::task::{spawn,JoinHandle};

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
    url: String,
}

#[tonic::async_trait]
impl Arkouda for ArkServer {

    async fn handle_request(&self, request: Request<ArkoudaRequest>) -> Result<Response<ArkoudaReply>, Status> {
        let req = request.into_inner();

        let ctx = zmq::Context::new();
        let socket = ctx.socket(zmq::REQ).unwrap();

        socket.connect(&self.url).unwrap();
        
        // Generate and send message to arkouda_server
        let am = json!(ArkoudaMessage{user: String::from(req.user),
                                cmd:  String::from(req.cmd),
                                format:  String::from(req.format),
                                token:  String::from(req.token),
                                size: req.size,
                                args: String::from(req.args)
                                });
        let msg = am.to_string();
        
        debug!("Sending message to Arkouda: {}", msg);        

        let url:String = self.url.to_owned();
        
        let reply = ArkoudaReply::default();

        TASKS.add_task(spawn( async move { async_process_message(url, msg).await; }));

        Ok(Response::new(reply))
    }
}

async fn async_process_message(url: String, msg: String) -> String {
    let ctx = zmq::Context::new();
    let socket = ctx.socket(zmq::REQ).unwrap();

    socket.connect(&url).unwrap();  
    socket.send(&msg,0).unwrap();   
    
    let return_msg = socket.recv_msg(0).unwrap();
    let result = return_msg.as_str().unwrap();
    return result.to_string();  
}

pub struct TaskList{
    tasks: Vec<JoinHandle<()>>
}

impl TaskList {
    pub fn add_task(&mut self, task: JoinHandle<()>) {
        self.tasks.push(task);
    }
}

const TASKS:TaskList = TaskList{tasks:Vec::<JoinHandle<()>>::new()};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    let port = &args[1];
    let arkouda_url = &args[2].to_string();
    
    //Generate SocketAddr
    let addr_str = "[::1]:${PORT}".to_string().replace("${PORT}",port);
    let addr = addr_str.parse()?;

    let arkouda = ArkServer {url:arkouda_url.to_string()};

    info!("listening on: {} configured for arkouda at {}", addr, arkouda_url);

    Server::builder()
        .add_service(ArkoudaServer::new(arkouda))
        .serve(addr)
        .await?;

    Ok(())
}

