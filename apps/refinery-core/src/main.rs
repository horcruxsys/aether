use std::collections::HashMap;
use tonic::{transport::Server, Request, Response, Status};
use apache_avro::{Schema, Writer};
use std::fs::File;
use uuid::Uuid;
use tokio::sync::mpsc;
use shield::ShieldScrubber;

pub mod aether {
    tonic::include_proto!("aether");
}

use aether::refinery_service_server::{RefineryService, RefineryServiceServer};
use aether::{MigrationRequest, MigrationResponse};

#[derive(Default)]
pub struct MyRefinery {}

#[tonic::async_trait]
impl RefineryService for MyRefinery {
    async fn start_migration(
        &self,
        request: Request<MigrationRequest>,
    ) -> Result<Response<MigrationResponse>, Status> {
        let req = request.into_inner();
        // Since we are running from target/release or from the monorepo root depending on execution context, 
        // using include_str! allows the file content to be embedded at compile time.
        // However, since we mock saving the `.avro` file, we'll write it relative to CWD.
        let job_id = Uuid::new_v4().to_string();
        
        println!("Received migration request: source={}, dest={}", req.source, req.destination);
        
        // Spawn the tokio mpsc pipeline for "chunking & masking"
        let (tx, mut rx) = mpsc::channel(100);
        let job_id_clone = job_id.clone();
        
        // Ingester Simulator
        tokio::spawn(async move {
            let sample_rows = vec![
                "User Alice (SSN: 123-45-6789) has role admin.",
                "User Bob (PAN: 1234-5678-1234-5678) has role user."
            ];
            for row in sample_rows {
                tx.send(row.to_string()).await.unwrap();
            }
        });

        // Flattener & Shield & Avro Writer
        tokio::spawn(async move {
            let scrubber = ShieldScrubber::new();
            
            // Setup Avro Writer
            let schema_str = include_str!("../../../packages/semantic-spec/schemas/RefinedChunk.avsc");
            let schema = Schema::parse_str(schema_str).unwrap();
            
            // In a real app we'd configure the output path, we dump into our .cache directory here.
            let dump_path = format!("../../.cache/aether-dump/{}.avro", &job_id_clone);
            let file = File::create(&dump_path).unwrap();
            let mut writer = Writer::new(&schema, file);

            while let Some(msg) = rx.recv().await {
                // Flattening (Simulated)
                let document = format!("Document flattened from legacy DB: {}", msg);
                
                // Masking via Shield-PII
                let mask_result = scrubber.mask(&document);
                
                // Formatting to Avro
                let mut record = apache_avro::types::Record::new(writer.schema()).unwrap();
                record.put("uuid", apache_avro::types::Value::String(Uuid::new_v4().to_string()));
                record.put("source_urn", apache_avro::types::Value::String("sql://mock/mock".to_string()));
                record.put("content", apache_avro::types::Value::String(mask_result.scrubbed_text));
                
                let mut metadata = HashMap::new();
                metadata.insert("job".to_string(), apache_avro::types::Value::String("migration".to_string()));
                record.put("metadata", apache_avro::types::Value::Map(metadata));

                let mut mask_map_avro = HashMap::new();
                for (k, v) in mask_result.pii_mask_map {
                    mask_map_avro.insert(k, apache_avro::types::Value::String(v));
                }
                record.put("pii_mask_map", apache_avro::types::Value::Map(mask_map_avro));

                writer.append(record).unwrap();
            }
            writer.flush().unwrap();
            println!("Refinery completed chunking path for job {}", &job_id_clone);
        });

        let reply = MigrationResponse {
            job_id,
            status: "STARTED".into(),
            message: "Refinery-core Blast Path executing".into(),
        };

        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "0.0.0.0:50051".parse()?;
    let refinery = MyRefinery::default();

    println!("Refinery Core gRPC Server listening on {}", addr);

    Server::builder()
        .add_service(RefineryServiceServer::new(refinery))
        .serve(addr)
        .await?;

    Ok(())
}
