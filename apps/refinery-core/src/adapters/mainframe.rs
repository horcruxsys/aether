use crate::adapters::DataAdapter;
use crate::errors::AetherError;
use crate::models::{CdcEvent, CdcOperation, SaasEventLog};
use async_trait::async_trait;
use chrono::Utc;
use serde_json::json;
use uuid::Uuid;

pub struct MainframeAdapter {
    pub flat_file_path: String,
}

#[async_trait]
impl DataAdapter for MainframeAdapter {
    async fn connect(&self) -> Result<(), AetherError> {
        if !self.flat_file_path.ends_with(".dat") {
            return Err(AetherError::IoError(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "COBOL flat file must end with .dat",
            )));
        }
        Ok(())
    }

    async fn fetch_batch(&self) -> Result<Vec<CdcEvent>, AetherError> {
        Ok(vec![CdcEvent {
            operation: CdcOperation::Insert,
            log: SaasEventLog {
                event_id: Uuid::new_v4(),
                user_urn: "urn:mainframe:cobol".to_string(),
                action_type: "FLAT_FILE_READ".into(),
                created_at: Utc::now(),
                payload: json!({ "ebcdic_segment": "00000X1239999" }),
            },
        }])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mainframe_extension_failure() {
        let adapter = MainframeAdapter {
            flat_file_path: "/var/data/dump.txt".into(),
        };
        let result = adapter.connect().await;
        assert!(result.is_err());
    }
}
