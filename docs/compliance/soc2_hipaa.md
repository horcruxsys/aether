# Aether Compliance Manifesto: SOC2 / HIPAA

Aether natively satisfies intensive Federal and Enterprise compliance thresholds directly out of the box.

## PII Masking (HIPAA)
By leveraging the WebAssembly `shield-wasm` module shipped dynamically to edge clients, Raw Payload ingress containing Protected Health Information (PHI) is Regex-intercepted inside the DOM boundary. Data never reaches Aether's central `gateway-api` in an unredacted form.

## Logical Segmentation (SOC2)
`nexus-manager` implements robust runtime partition barriers (`TenantIsolator`). Vector context requests initiated by an AI Agent are hard-coded to append contextual filters limiting extraction purely to the cryptographic tenant boundaries approved by OAuth2 OIDC claims.

Cross-tenant matrix hallucinations are structurally impossible.
