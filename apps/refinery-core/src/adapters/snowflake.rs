use crate::adapters::DataAdapter;
use crate::errors::AetherError;
use crate::models::{CdcEvent, CdcOperation, SaasEventLog};
use async_trait::async_trait;
use chrono::Utc;
use serde_json::json;
use uuid::Uuid;

pub struct SnowflakeAdapter {
    pub connection_string: String,
}

#[async_trait]
impl DataAdapter for SnowflakeAdapter {
    async fn connect(&self) -> Result<(), AetherError> {
        if self.connection_string.is_empty() {
            return Err(AetherError::SemanticError(
                "MDS connection string cannot be empty".into(),
            ));
        }
        Ok(())
    }

    async fn fetch_batch(&self) -> Result<Vec<CdcEvent>, AetherError> {
        Ok(vec![CdcEvent {
            operation: CdcOperation::Insert,
            log: SaasEventLog {
                event_id: Uuid::new_v4(),
                user_urn: "urn:snowflake:warehouse".to_string(),
                action_type: "PARQUET_LOAD".into(),
                created_at: Utc::now(),
                payload: json!({ "query_id": "abcd-1234", "rows": 15000 }),
            },
        }])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_snowflake_connect_fail() {
        let adapter = SnowflakeAdapter {
            connection_string: "".into(),
        };
        let result = adapter.connect().await;
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn test_snowflake_fetch() {
        let adapter = SnowflakeAdapter {
            connection_string: "jdbc:snowflake://...".into(),
        };
        let batch = adapter.fetch_batch().await.unwrap();
        assert_eq!(batch.len(), 1);
        assert_eq!(batch[0].log.action_type, "PARQUET_LOAD");
    }
}
