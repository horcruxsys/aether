# semantic-spec

**Mission:** The "Source of Truth" for data schemas.

* **Tech Stack:** Protobuf, JSON Schema.
* **Function:** Ensures the Rust refinery and the Python manager speak the same language.

> Centralized type definitions. If a data shape changes here, the entire monorepo build fails until all services are updated, ensuring total system integrity.
