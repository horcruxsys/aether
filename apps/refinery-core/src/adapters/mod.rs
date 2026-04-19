pub mod snowflake;
pub mod mongodb;
pub mod mainframe;

use crate::errors::AetherError;
use crate::models::CdcEvent;
use async_trait::async_trait;

#[async_trait]
pub trait DataAdapter: Send + Sync {
    /// Attempts to establish a persistent or ephemeral connection to the legacy domain
    async fn connect(&self) -> Result<(), AetherError>;

    /// Ingests data uniformly translating upstream abstractions into standardized CDC flows
    async fn fetch_batch(&self) -> Result<Vec<CdcEvent>, AetherError>;
}

pub struct MockAdapter {}

#[async_trait]
impl DataAdapter for MockAdapter {
    async fn connect(&self) -> Result<(), AetherError> {
        Ok(())
    }

    async fn fetch_batch(&self) -> Result<Vec<CdcEvent>, AetherError> {
        // Return structured mocked batch similar to previous inline logic
        let mut batch = Vec::new();
        // Just return a single mock event acting as a sentinel for testing, returning empty vec later to stop stream
        Ok(batch)
    }
}
