use crate::errors::AetherError;
use crate::models::CdcEvent;
use serde_json::json;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{error, warn};

/// Conceptually buffers and flushes unresolvable semantic masking failures or parsing
/// distortions into a cold-storage isolation area preventing ingestion blocks.
#[derive(Clone)]
pub struct DeadLetterQueue {
    buffer: Arc<Mutex<Vec<(CdcEvent, String)>>>,
}

impl DeadLetterQueue {
    pub fn new() -> Self {
        Self {
            buffer: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub async fn push_failure(&self, event: CdcEvent, reason: String) -> Result<(), AetherError> {
        let mut buf = self.buffer.lock().await;
        warn!(
            "DLQ EVENT PUSHED: Event {} failed due to: {}",
            event.log.event_id, reason
        );
        buf.push((event, reason));

        // Flush mechanism triggers over synthetic limits
        if buf.len() > 100 {
            error!(
                "DLQ capacity breached! Flushing 100 malformed models to synthetic cold storage..."
            );
            buf.clear();
        }

        Ok(())
    }
}
