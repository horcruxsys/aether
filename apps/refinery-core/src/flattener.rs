use crate::models::SaasEventLog;

pub struct EventFlattener {}

impl EventFlattener {
    pub fn new() -> Self {
        EventFlattener {}
    }

    pub fn flatten(&self, event: &SaasEventLog) -> String {
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
                let items: Vec<String> = obj.iter().map(|(k, v)| format!("{}: {}", k, self.stringify_value(v))).collect();
                format!("{{{}}}", items.join(", "))
            }
            serde_json::Value::Null => "null".to_string(),
        }
    }
}
