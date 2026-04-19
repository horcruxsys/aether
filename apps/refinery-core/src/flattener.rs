use crate::models::{CdcEvent, CdcOperation, SaasEventLog};
use rayon::prelude::*;

pub trait BatchFlattener: Send + Sync {
    fn process_batch(&self, batch: &[CdcEvent]) -> Vec<(String, String)>;
}

pub struct EventFlattener {}

impl EventFlattener {
    pub fn new() -> Self {
        EventFlattener {}
    }
}

impl BatchFlattener for EventFlattener {
    fn process_batch(&self, batch: &[CdcEvent]) -> Vec<(String, String)> {
        // We use par_iter to blast through thousands of rows in parallel across CPU cores
        batch
            .par_iter()
            .map(|event| {
                if event.operation == CdcOperation::Delete {
                    // If it's a CDC Delete, we generate a specific tombstone instruction
                    (
                        event.log.event_id.to_string(),
                        "TOMBSTONE_PRUNE_VECTOR".to_string(),
                    )
                } else {
                    (
                        event.log.event_id.to_string(),
                        self.flatten_event(&event.log),
                    )
                }
            })
            .collect()
    }
}

impl EventFlattener {
    fn flatten_event(&self, event: &SaasEventLog) -> String {
        let mut document = format!(
            "On {}, user {} performed the action {}. ",
            event.created_at.to_rfc3339(),
            event.user_urn,
            event.action_type
        );

        // Recursively stringify and flatten JSON payload
        if let Some(obj) = event.payload.as_object() {
            document.push_str("Event Details context: ");
            for (key, value) in obj.iter() {
                document.push_str(&format!("{}: {} | ", key, self.stringify_value(value)));
            }
        }

        document
    }

    fn stringify_value(&self, value: &serde_json::Value) -> String {
        match value {
            serde_json::Value::String(s) => s.to_string(),
            serde_json::Value::Number(n) => n.to_string(),
            serde_json::Value::Bool(b) => b.to_string(),
            serde_json::Value::Array(arr) => {
                let items: Vec<String> = arr.iter().map(|v| self.stringify_value(v)).collect();
                format!("[{}]", items.join(", "))
            }
            serde_json::Value::Object(obj) => {
                let items: Vec<String> = obj
                    .iter()
                    .map(|(k, v)| format!("{}: {}", k, self.stringify_value(v)))
                    .collect();
                format!("{{{}}}", items.join(", "))
            }
            serde_json::Value::Null => "null".to_string(),
        }
    }
}
