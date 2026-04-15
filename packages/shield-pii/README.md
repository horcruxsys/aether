# shield-pii (Security & Governance)

**Mission:** Shared security primitives for the entire ecosystem.

Details the high-performance Rust library responsible for PII/PHI detection and masking. It uses a hybrid approach of **Aho-Corasick** for fixed patterns and **regex-automata** for structured data, successfully compiled to WebAssembly (WASM) to ensure the exact same security logic runs in both our backend streaming services and the edge-based gateway.

## Low-Level Design (LLD)

### Masking & Encryption Capabilities
- **Aho-Corasick:** Deployed for ultra-fast matching against thousands of known static terms (e.g., highly sensitive internal project names, confidential code names).
- **Regex Automata:** Employs deterministic finite automata to scan for structured personal data such as PANs, SSNs, and IBANs.
- **WASM Interoperability:** By structuring the core logic correctly, `shield-pii` crosses language boundaries, easily exportable to the Node.js API layers. 

> A zero-dependency, high-performance library for identifying and masking sensitive data. It ensures that no PII ever leaves the Aether ecosystem un-encrypted or un-masked.
