use chrono::{DateTime, Utc};
use serde_json::Value as JsonValue;
use sqlx::FromRow;
use uuid::Uuid;

#[derive(FromRow, Debug, Clone)]
pub struct SaasEventLog {
    pub event_id: Uuid,
    pub user_urn: String,
    pub action_type: String,
    pub created_at: DateTime<Utc>,
    pub payload: JsonValue,
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_saas_event_log_creation() {
        let event = SaasEventLog {
            event_id: Uuid::new_v4(),
            user_urn: "urn:test:user".to_string(),
            action_type: "TEST_ACTION".to_string(),
            created_at: Utc::now(),
            payload: json!({"key": "value"}),
        };
        assert_eq!(event.user_urn, "urn:test:user");
        assert_eq!(event.action_type, "TEST_ACTION");
        assert_eq!(event.payload["key"], "value");
    }
}
