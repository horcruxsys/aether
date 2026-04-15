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
