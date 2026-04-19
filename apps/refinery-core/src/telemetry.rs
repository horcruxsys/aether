use crate::errors::AetherError;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Initializes the global telemetry and logging subsystem for the node.
/// In this execution phase, we use native `tracing` subscriber hooks, 
/// architected to seamlessly plug into `tracing_opentelemetry` for Jaeger/Prometheus
/// when OTLP collector endpoints are provisioned in Phase 16.
pub fn init_telemetry() -> Result<(), AetherError> {
    // We instantiate building blocks that can be swapped with OpenTelemetry pipelines: 
    // let tracer = opentelemetry_otlp::new_pipeline().tracing()...
    // let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);

    let format_layer = tracing_subscriber::fmt::layer()
        .with_target(true)
        .with_thread_ids(true);

    tracing_subscriber::registry()
        .with(format_layer)
        // .with(telemetry) // Un-comment when OTLP cluster is active
        .try_init()
        .map_err(|e| AetherError::InternalError(anyhow::anyhow!("Failed to initialize tracing: {}", e)))?;

    info!("OpenTelemetry tracing & formatting layer initialized boundary successfully.");
    Ok(())
}
