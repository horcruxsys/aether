use shield::ShieldScrubber;
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct EdgeScrubber {
    scrubber: ShieldScrubber,
}

#[wasm_bindgen]
impl EdgeScrubber {
    #[wasm_bindgen(constructor)]
    pub fn new() -> EdgeScrubber {
        EdgeScrubber {
            scrubber: ShieldScrubber::new(),
        }
    }

    /// Exposes deterministic PII scrubbing logic into the client browser / Node.js
    /// securely preventing raw credentials from ever hitting the wire.
    #[wasm_bindgen]
    pub fn sanitize_payload(&self, raw_input: &str) -> String {
        // Assume `shield_pii` logic handles regexes natively without crashing WASM execution constraints
        self.scrubber.scrub(raw_input)
    }
}
