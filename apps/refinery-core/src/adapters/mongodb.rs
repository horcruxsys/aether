use crate::adapters::DataAdapter;
use crate::errors::AetherError;
use crate::models::{CdcEvent, CdcOperation, SaasEventLog};
use async_trait::async_trait;
use chrono::Utc;
use serde_json::json;
use uuid::Uuid;

pub struct MongoAdapter {
    pub uri: String,
}

#[async_trait]
impl DataAdapter for MongoAdapter {
    async fn connect(&self) -> Result<(), AetherError> {
        if !self.uri.starts_with("mongodb://") {
            return Err(AetherError::SemanticError(
                "Invalid BSON URI signature".into(),
            ));
        }
        Ok(())
    }

    async fn fetch_batch(&self) -> Result<Vec<CdcEvent>, AetherError> {
        Ok(vec![CdcEvent {
            operation: CdcOperation::Update,
            log: SaasEventLog {
                event_id: Uuid::new_v4(),
                user_urn: "urn:mongodb:cluster".to_string(),
                action_type: "BSON_MUTATION".into(),
                created_at: Utc::now(),
                payload: json!({ "doc_id": "xyz", "changes": [] }),
            },
        }])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mongo_connect_success() {
        let adapter = MongoAdapter {
            uri: "mongodb://localhost:27017".into(),
        };
        assert!(adapter.connect().await.is_ok());
    }

    #[tokio::test]
    async fn test_mongo_connect_failure() {
        let adapter = MongoAdapter {
            uri: "postgres://localhost:5432".into(),
        };
        assert!(adapter.connect().await.is_err());
    }
}
