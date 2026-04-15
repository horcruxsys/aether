# Aether: The Autonomous Data Fabric 🌌

**Aether** is a polyglot monorepo designed to migrate, refine, and expose legacy enterprise data to the Agentic AI workforce.

## 🏗️ Architecture at a Glance

- **Ingest:** Legacy SQL/SaaS -> `refinery-core`
- **Refine:** `shield-pii` (Masking) + `refinery-core` (Chunking)
- **Store:** `nexus-manager` (Hybrid Vector-Graph DB)
- **Expose:** `gateway-api` + `mcp-bridge` (Agent Access)

## 🚦 Developer Quickstart

1. **Install Dependencies:** `pnpm install`
2. **Setup Rust Toolchain:** `rustup toolchain install stable`
3. **Run Dev Environment:** `turbo dev`

## 📈 The Vision

To become the invisible "nervous system" of every AI-powered enterprise. We don't just move data; we make it **intelligent**.
