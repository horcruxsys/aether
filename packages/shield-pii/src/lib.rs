use aho_corasick::AhoCorasick;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;
use wasm_bindgen::prelude::*;

#[derive(Serialize, Deserialize)]
pub struct MaskResult {
    pub scrubbed_text: String,
    pub pii_mask_map: HashMap<String, String>,
}

#[wasm_bindgen]
pub struct ShieldScrubber {
    ac: AhoCorasick,
    patterns: Vec<Regex>,
}

#[wasm_bindgen]
impl ShieldScrubber {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        let keywords = &["CONFIDENTIAL", "PROJECT_X", "TOP_SECRET", "SSN", "PAN"];
        let ac = AhoCorasick::new(keywords).unwrap();

        let patterns = vec![
            Regex::new(r"\b\d{3}-\d{2}-\d{4}\b").unwrap(), // SSN
            Regex::new(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b").unwrap(), // PAN
            Regex::new(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+").unwrap(), // Email
        ];

        ShieldScrubber { ac, patterns }
    }

    #[wasm_bindgen]
    pub fn mask_js(&self, input: &str) -> JsValue {
        let result = self.mask_internal(input);
        serde_wasm_bindgen::to_value(&result).unwrap()
    }
}

// Internal implementation (non-WASM)
impl ShieldScrubber {
    pub fn mask(&self, input: &str) -> MaskResult {
        self.mask_internal(input)
    }

    fn mask_internal(&self, input: &str) -> MaskResult {
        let mut pii_mask_map = HashMap::new();
        let mut scrubbed = input.to_string();

        // 1. Process Regexes
        for re in &self.patterns {
            scrubbed = re
                .replace_all(&scrubbed, |caps: &regex::Captures| {
                    let matched_text = caps[0].to_string();
                    let token = format!("[[{}]]", Uuid::new_v4().to_string());
                    pii_mask_map.insert(token.clone(), matched_text);
                    token
                })
                .to_string();
        }

        // 2. Process Aho-Corasick static keywords
        let mut final_scrubbed = String::new();
        let mut last_match = 0;

        for mat in self.ac.find_iter(&scrubbed) {
            final_scrubbed.push_str(&scrubbed[last_match..mat.start()]);

            let matched_text = &scrubbed[mat.start()..mat.end()];
            let token = format!("[[{}]]", Uuid::new_v4().to_string());
            pii_mask_map.insert(token.clone(), matched_text.to_string());

            final_scrubbed.push_str(&token);
            last_match = mat.end();
        }
        final_scrubbed.push_str(&scrubbed[last_match..]);

        MaskResult {
            scrubbed_text: final_scrubbed,
            pii_mask_map,
        }
    }
}
