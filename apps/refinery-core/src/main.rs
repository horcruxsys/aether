use apache_avro::{Schema, Writer};
use shield::ShieldScrubber;
use std::collections::HashMap;
use std::fs::File;
use tokio::sync::mpsc;
use tonic::{Request, Response, Status, transport::Server};
use uuid::Uuid;

pub mod flattener;
pub mod models;

use chrono::Utc;
use flattener::EventFlattener;
use models::{CdcEvent, CdcOperation, SaasEventLog};
use serde_json::json;

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

        println!(
            "Received migration request: source={}, dest={}",
            req.source, req.destination
        );

        // Spawn the tokio mpsc pipeline for "chunking & masking"
        let (tx, mut rx) = mpsc::channel(100);
        let job_id_clone = job_id.clone();

        // Ingester Simulator (Massive CDC Stream)
        tokio::spawn(async move {
            let mut batch = Vec::with_capacity(1000);

            // Generate 10,000 synthetic legacy logs to test Rayon multi-core processing
            for i in 0..10_000 {
                let operation = if i % 100 == 0 {
                    CdcOperation::Delete
                } else {
                    CdcOperation::Insert
                };

                batch.push(CdcEvent {
                    operation,
                    log: SaasEventLog {
                        event_id: Uuid::new_v4(),
                        user_urn: format!("urn:aether:user:{}", i),
                        action_type: "BULK_LOAD".into(),
                        created_at: Utc::now(),
                        payload: json!({
                            "iteration": i,
                            "metrics": { "cpu_load_mock": i * 2 }
                        }),
                    },
                });

                if batch.len() == 1000 {
                    tx.send(batch.clone()).await.unwrap();
                    batch.clear();
                }
            }
        });

        // Flattener & Shield & Avro Writer (Consuming in batches for bulk I/O)
        tokio::spawn(async move {
            let scrubber = std::sync::Arc::new(ShieldScrubber::new());
            let flattener = std::sync::Arc::new(EventFlattener::new());

            // Setup Avro Writer
            let schema_str =
                include_str!("../../../packages/semantic-spec/schemas/RefinedChunk.avsc");
            let schema = Schema::parse_str(schema_str).unwrap();

            let dump_path = format!("../../.cache/aether-dump/{}.avro", &job_id_clone);
            let file = File::create(&dump_path).unwrap();
            let mut writer = Writer::new(&schema, file);

            // rx receives Vec<CdcEvent> batches of 1000 each
            while let Some(batch) = rx.recv().await {
                // Offload heavy Rayon CPU-bound work away from Tokio Async Loop
                let f_clone = flattener.clone();
                let results = tokio::task::spawn_blocking(move || f_clone.process_batch(&batch))
                    .await
                    .unwrap();

                // Masking and batch appending into Avro buffer
                for (id, document) in results {
                    let mask_result = scrubber.mask(&document);

                    let mut record = apache_avro::types::Record::new(writer.schema()).unwrap();
                    record.put("uuid", apache_avro::types::Value::String(id));
                    record.put(
                        "source_urn",
                        apache_avro::types::Value::String("cdc://legacy".to_string()),
                    );
                    record.put(
                        "content",
                        apache_avro::types::Value::String(mask_result.scrubbed_text),
                    );

                    let mut metadata = HashMap::new();
                    metadata.insert(
                        "job".to_string(),
                        apache_avro::types::Value::String("cdc_migration".to_string()),
                    );
                    record.put("metadata", apache_avro::types::Value::Map(metadata));

                    let mut mask_map_avro = HashMap::new();
                    for (k, v) in mask_result.pii_mask_map {
                        mask_map_avro.insert(k, apache_avro::types::Value::String(v));
                    }
                    record.put(
                        "pii_mask_map",
                        apache_avro::types::Value::Map(mask_map_avro),
                    );

                    writer.append(record).unwrap();
                }

                // Flush disk per 1000 records, not per row
                writer.flush().unwrap();
                println!("Flushed batch of 1000 CDC vectors to disk.");
            }
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
