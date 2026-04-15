# refinery-core (High-Throughput Processing)

**Mission:** High-speed data cleaning, PII masking, and semantic transformation.

The "heavy lifter" built in Rust. This document outlines the pipeline architecture handling the multi-source ingestion and generation of semantic documents.

## Low-Level Design (LLD)

### Pipeline Architecture

1. **Ingest Engine:** Multi-source stream ingestion designed around `tokio` streams. It safely consumes legacy inputs (SQL rows, vast JSON logs) seamlessly.
2. **Flattening Layer:** Transforms abstract relational rows and key-value pairings into highly descriptive, readable semantic prose optimized for Machine Learning consumption.
3. **Serialization Engine:** Employs zero-copy binary serialization using `Apache Avro`. Converts the clean, masked in-memory data structures straight into the definitive `.avro` chunked payloads, bridging the path to the Nexus orchestrator.

> `refinery-core` is the "heavy lifter." Built in Rust for maximum memory safety and multi-threaded throughput, it processes gigabytes of legacy logs into clean, vector-ready text in seconds. It is designed to run in a stateless container for infinite horizontal scaling.
