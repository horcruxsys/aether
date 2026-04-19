use apache_avro::Schema;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Decentralized Schema Registry supporting live hot-reloading 
/// of Aether Schema contracts without bounding to external API endpoints.
pub struct AvroSchemaRegistry {
    schemas: Arc<RwLock<HashMap<String, Schema>>>,
}

impl AvroSchemaRegistry {
    pub fn new() -> Self {
        Self {
            schemas: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Registers a backwards-compatible schema mutation
    pub async fn register_schema(&self, topic: &str, raw_schema: &str) -> Result<(), String> {
        let parsed = Schema::parse_str(raw_schema).map_err(|e| format!("Invalid Avro Schema: {}", e))?;
        let mut map = self.schemas.write().await;
        map.insert(topic.to_string(), parsed);
        Ok(())
    }

    /// Pulls active schema definition
    pub async fn get_schema(&self, topic: &str) -> Option<Schema> {
        let map = self.schemas.read().await;
        map.get(topic).cloned()
    }
}
