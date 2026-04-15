# semantic-spec (The Source of Truth)

**Mission:** The "Source of Truth" for data schemas.

Defines the Apache Avro schemas that serve as the contract for the entire ecosystem. It includes the `RefinedChunk` schema which ensures that data flowing from the Rust refinery to the Python AI engine maintains perfect structural integrity and context.

## Low-Level Design (LLD)

### Apache Avro Core
- **Schema-First Contract:** By using `RefinedChunk.avsc`, we guarantee that upstream components (`refinery-core`) cannot publish malformed data, and downstream consumers (`nexus-manager`) always know the exact layout of the refined text, metadata, and mapping dictionaries.
- **Zero-Copy Potential:** Compared to standard JSON, the binary format offers drastically lower serialization overhead, which is critical at terabyte-scale.

> Centralized type definitions. If a data shape changes here, the entire monorepo build fails until all services are updated, ensuring total system integrity.
