use std::env;

use log::{info,debug};

use tonic::{transport::Server, Request, Response, Status};

use arkouda::arkouda_server::{Arkouda, ArkoudaServer};
use arkouda::{ArkoudaReply, ArkoudaRequest};

use serde::{Deserialize, Serialize};
use serde_json::json;

use tokio::task::{spawn,JoinHandle};

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

pub fn print_type_of<T>(_: &T) {
    println!("{}", std::any::type_name::<T>())
}

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
    tasks: Arc<RwLock<HashMap<String, JoinHandle<()>>>>
}

trait ArkoudaProxy: Arkouda {
    fn new(proxy_url: &'static str) -> Self;
}

#[tonic::async_trait]
impl Arkouda for ArkServer {

    async fn handle_request(&self, request: Request<ArkoudaRequest>) -> Result<Response<ArkoudaReply>, Status> {
        let req = request.into_inner();

        let ctx = zmq::Context::new();
        let socket = ctx.socket(zmq::REQ).unwrap();

        socket.connect(&self.url).unwrap();
        
        let user:String = String::from(req.user.clone());
        let requesting_user:String = String:: from(req.user.clone());
        let cmd:String = String::from(req.cmd.clone());
        
        // Generate and send message to arkouda_server
        let am = json!(ArkoudaMessage{user: user.clone(),
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
        
        let mut map = self.tasks.write().await;
        
        if cmd != "get_request_status" {
            let handle = spawn( async move { async_process_message(url, msg).await; });
            map.insert(String::from(user), handle);
            debug!("Sent message to Arkouda, current tasks cache {:?}", map);  
        } else {
            let user_request = map.get(&String::from(user));
            debug!("Current tasks cache for {:?} {:?}", requesting_user, user_request);
        }

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

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let args: Vec<String> = env::args().collect();
    let port = &args[1];
    let arkouda_url = &args[2].to_string();
    
    //Generate SocketAddr
    let addr_str = "[::1]:${PORT}".to_string().replace("${PORT}",port);
    let addr = addr_str.parse()?;

    //let mut tasks: Vec<JoinHandle<()>> = vec![];
    let tasks:Arc<RwLock<HashMap<String, JoinHandle<()>>>> = Arc::new(RwLock::new(HashMap::new()));

    let arkouda = ArkServer {url:arkouda_url.to_string(), tasks:tasks};

    info!("listening on: {} configured for arkouda at {}", addr, arkouda_url);

    Server::builder()
        .add_service(ArkoudaServer::new(arkouda))
        .serve(addr)
        .await?;

    Ok(())
}

