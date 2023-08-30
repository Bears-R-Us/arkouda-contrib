use std::env;

use log::{info,debug};

use tonic::{transport::Server, Request, Response, Status};

use arkouda::arkouda_server::{Arkouda, ArkoudaServer};
use arkouda::{ArkoudaRequest, ArkoudaResponse};

use serde::{Deserialize, Serialize};
use serde_json::{json};
use serde_json;
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
    tasks: Arc<RwLock<HashMap<String, JoinHandle<String>>>>
}

#[tonic::async_trait]
impl Arkouda for ArkServer {

    async fn handle_request(&self, request: Request<ArkoudaRequest>) -> Result<Response<ArkoudaResponse>, Status> {
        let req = request.into_inner();
        
        debug!("Incoming message from client: {:?}", req); 

        let ctx = zmq::Context::new();
        let socket = ctx.socket(zmq::REQ).unwrap();

        socket.connect(&self.url).unwrap();
        
        let user:String = String::from(req.user.clone());
        let requesting_user:String = String:: from(req.user.clone());
        let cmd:String = String::from(req.cmd.clone());
        let request_id:String = String::from(req.request_id.clone());
        //let args = String::from(req.args.clone());
        
        
        // Generate and send message to arkouda_server
        let am = json!(ArkoudaMessage{user: user.clone(),
                                cmd:  String::from(req.cmd),
                                format:  String::from(req.format),
                                token:  String::from(req.token),
                                size: req.size,
                                args: String::from(req.args.clone())
                                });
        let msg = am.to_string();
        
        debug!("Sending message to Arkouda: {}", msg);        

        let url:String = self.url.to_owned();

        let mut response = ArkoudaResponse::default();
        response.request_id = request_id.clone();
        
        let mut map = self.tasks.write().await;

        if cmd != "getrequeststatus" {
            let handle = spawn( async { return async_process_message(url, msg).await; });
            map.insert(String::from(request_id.clone()), handle);
            debug!("Sent message to Arkouda, current tasks cache {:?}", map);  
            
            response.user = user.clone();
            response.cmd = cmd.clone();
            response.args = req.args.clone();
            response.request_id = request_id.clone();
            response.request_status = String::from("SUBMITTED");
            response.message = String::from("submitted request to Arkouda");           
        } else {
            let lookup_request_id = request_id.clone();
            debug!("lookup_request_id:  {:?}", lookup_request_id.clone());
            
            let user_request = map.get(&lookup_request_id.clone()).unwrap();

            if user_request.is_finished() {
                debug!("Result for {:?} {:?}", requesting_user, lookup_request_id.clone());
                
                // Remove the JoinHandle from the map to get ownership and access to result via await
                let request_result = map.remove(&lookup_request_id.clone()).unwrap().await;
                debug!("result: {:?} for user: {:?} request_id: {:?}", request_result, requesting_user, request_id.clone());
                
                //response.message = String::from(request_result.unwrap());
                let result_string = String::from(request_result.unwrap());
                response.message = format!(r#"{{"request_id": Some(request_id), "request_result": "{result_string}"}}"#);
            }
        }

        Ok(Response::new(response))
    }
}

async fn async_process_message(url: String, msg: String) -> String {
    let ctx = zmq::Context::new();
    let socket = ctx.socket(zmq::REQ).unwrap();

    socket.connect(&url).unwrap();  
    socket.send(&msg,0).unwrap();   
    
    let return_msg = socket.recv_msg(0).unwrap();
    let result = return_msg.as_str().unwrap();
    debug!("The result: {:?}", result);
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

    let tasks:Arc<RwLock<HashMap<String, JoinHandle<String>>>> = Arc::new(RwLock::new(HashMap::new()));

    let arkouda = ArkServer {url:arkouda_url.to_string(), tasks:tasks};

    info!("listening on: {} configured for arkouda at {}", addr, arkouda_url);

    Server::builder()
        .add_service(ArkoudaServer::new(arkouda))
        .serve(addr)
        .await?;

    Ok(())
}

