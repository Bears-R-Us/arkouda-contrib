use arkouda::arkouda_client::ArkoudaClient;
use arkouda::ArkoudaRequest;

pub mod arkouda {
    tonic::include_proto!("arkouda");
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut client = ArkoudaClient::connect("http://[::1]:50051").await?;

    let request = tonic::Request::new(ArkoudaRequest {
        user: "Tonic".into(),
        token: "Tonic".into(),
        cmd: "Tonic".into(),
        format: "Tonic".into(),
        size: "Tonic".into(),
        args: "Tonic".into(),
    });

    let response = client.handle_request(request).await?;

    println!("RESPONSE={:?}", response);

    Ok(())
}
