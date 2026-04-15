# refinery-core

**Mission:** High-speed data cleaning, PII masking, and semantic transformation.

* **Tech Stack:** Rust (Axum, Tokio, Rayon), WASM (for shared logic).
* **Core Logic:**
    * **The Sanitizer:** Real-time PII/PHI detection using a hybrid of Regex and high-speed NLP (Natural Language Processing).
    * **The Chunk-Master:** Implements "Semantic Overlap" chunking to ensure context is never cut mid-sentence.

> `refinery-core` is the "heavy lifter." Built in Rust for maximum memory safety and multi-threaded throughput, it processes gigabytes of legacy logs into clean, vector-ready text in seconds. It is designed to run in a stateless container for infinite horizontal scaling.
