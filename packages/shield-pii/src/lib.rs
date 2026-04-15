use aho_corasick::AhoCorasick;
use regex::Regex;
use std::collections::HashMap;
use uuid::Uuid;

pub struct MaskResult {
    pub scrubbed_text: String,
    pub pii_mask_map: HashMap<String, String>,
}

pub struct ShieldScrubber {
    ac: AhoCorasick,
    patterns: Vec<Regex>,
}

impl ShieldScrubber {
    pub fn new() -> Self {
        // High-speed static keyword matching for known sensitive internal terms
        let keywords = &["CONFIDENTIAL", "PROJECT_X", "TOP_SECRET", "SSN", "PAN"];
        let ac = AhoCorasick::new(keywords).unwrap();

        // Regex Automata for structured PII
        // Mocking PAN and SSN-like patterns
        let patterns = vec![
            Regex::new(r"\b\d{3}-\d{2}-\d{4}\b").unwrap(), // SSN
            Regex::new(r"\b\d{4}-\d{4}-\d{4}-\d{4}\b").unwrap(), // PAN
            Regex::new(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+").unwrap(), // Email
            // ... MOCK: FastText logic stubbed out to avoid heavy C++ dependencies ...
        ];

        ShieldScrubber { ac, patterns }
    }

    pub fn mask(&self, input: &str) -> MaskResult {
        let mut pii_mask_map = HashMap::new();
        let mut scrubbed = input.to_string();

        // 1. Process Regexes
        for re in &self.patterns {
            scrubbed = re.replace_all(&scrubbed, |caps: &regex::Captures| {
                let matched_text = caps[0].to_string();
                let token = format!("[[{}]]", Uuid::new_v4().to_string());
                pii_mask_map.insert(token.clone(), matched_text);
                token
            }).to_string();
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

        // 3. Mock FastText context filter
        // If we found "Sandwich" in a certain context, maybe it's a code name, but we skip for MVP.

        MaskResult {
            scrubbed_text: final_scrubbed,
            pii_mask_map,
        }
    }
}
