use super::events::SaasEventLog;

#[derive(Debug, Clone, PartialEq)]
pub enum CdcOperation {
    Insert,
    Update,
    Delete,
}

#[derive(Debug, Clone)]
pub struct CdcEvent {
    pub operation: CdcOperation,
    pub log: SaasEventLog,
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;
    use serde_json::json;
    use uuid::Uuid;

    #[test]
    fn test_cdc_event_creation() {
        let log = SaasEventLog {
            event_id: Uuid::new_v4(),
            user_urn: "urn:test:user".to_string(),
            action_type: "USER_INSERT".to_string(),
            created_at: Utc::now(),
            payload: json!({}),
        };

        let event = CdcEvent {
            operation: CdcOperation::Insert,
            log,
        };

        assert_eq!(event.operation, CdcOperation::Insert);
        assert_eq!(event.log.user_urn, "urn:test:user");
    }

    #[test]
    fn test_cdc_operation_equality() {
        assert_eq!(CdcOperation::Delete, CdcOperation::Delete);
        assert_ne!(CdcOperation::Insert, CdcOperation::Update);
    }
}
