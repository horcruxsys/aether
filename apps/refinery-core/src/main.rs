use apache_avro::{Schema, Writer};
use shield::ShieldScrubber;
use std::collections::HashMap;
use std::fs::File;
use tokio::sync::mpsc;
use tonic::{Request, Response, Status, transport::Server};
use uuid::Uuid;

pub mod adapters;
pub mod dlq;
pub mod errors;
pub mod flattener;
pub mod models;
pub mod schema_registry;
pub mod telemetry;
pub mod zero_copy;

use dlq::DeadLetterQueue;
use errors::AetherError;
use tracing::{error, info, warn};

use chrono::Utc;
use flattener::EventFlattener;
use models::{CdcEvent, CdcOperation, SaasEventLog};
use serde_json::json;

pub mod aether {
    tonic::include_proto!("aether");
}

use aether::refinery_service_server::{RefineryService, RefineryServiceServer};
use aether::{MigrationRequest, MigrationResponse};

pub struct MyRefinery {
    pub flattener: std::sync::Arc<dyn flattener::BatchFlattener>,
    pub scrubber: std::sync::Arc<shield::ShieldScrubber>,
    pub adapter: std::sync::Arc<dyn adapters::DataAdapter>,
}

impl MyRefinery {
    pub fn new(
        flattener: std::sync::Arc<dyn flattener::BatchFlattener>,
        scrubber: std::sync::Arc<shield::ShieldScrubber>,
        adapter: std::sync::Arc<dyn adapters::DataAdapter>,
    ) -> Self {
        Self {
            flattener,
            scrubber,
            adapter,
        }
    }
}

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

        info!(
            "Received migration request: source={}, dest={}",
            req.source, req.destination
        );

        // Spawn the tokio mpsc pipeline for "chunking & masking"
        let (tx, mut rx) = mpsc::channel(100);
        let job_id_clone = job_id.clone();

        // Universal Adapter Pipeline
        let adapter = self.adapter.clone();
        tokio::spawn(async move {
            match adapter.connect().await {
                Ok(_) => {
                    info!("Successfully connected to enterprise data plane.");
                    loop {
                        match adapter.fetch_batch().await {
                            Ok(batch) => {
                                if batch.is_empty() {
                                    info!("CDC Source dry. Concluding ingestion.");
                                    break;
                                }
                                if let Err(e) = tx.send(batch).await {
                                    error!("Channel closed unexpectedly: {}", e);
                                    break;
                                }
                            }
                            Err(e) => {
                                error!("Adapter ingest failure: {}", e);
                                break;
                            }
                        }
                    }
                }
                Err(e) => error!("Failed to bind data adapter: {}", e),
            }
        });

        // Flattener & Shield & Avro Writer (Consuming in batches for bulk I/O)
        let scrubber = self.scrubber.clone();
        let flattener = self.flattener.clone();
        tokio::spawn(async move {
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
                info!("Flushed batch of 1000 CDC vectors to disk.");
            }
            info!("Refinery completed chunking path for job {}", &job_id_clone);
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
async fn main() -> Result<(), anyhow::Error> {
    // Initialize standard uniform tracing for the entire service
    telemetry::init_telemetry()?;

    let addr = "0.0.0.0:50051".parse()?;

    let flattener = std::sync::Arc::new(flattener::EventFlattener::new());
    let scrubber = std::sync::Arc::new(shield::ShieldScrubber::new());
    let adapter = std::sync::Arc::new(adapters::MockAdapter {});
    let refinery = MyRefinery::new(flattener, scrubber, adapter);

    info!("Refinery Core gRPC Server listening on {}", addr);

    Server::builder()
        .add_service(RefineryServiceServer::new(refinery))
        .serve(addr)
        .await?;

    Ok(())
}
