# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aether** is a polyglot monorepo designed to migrate, refine, and expose legacy enterprise data to the Agentic AI workforce. The system follows a pipeline: Ingest (legacy SQL/SaaS) → Refine (masking + chunking) → Store (hybrid vector-graph DB) → Expose (APIs for agents).

## Architecture

### Tech Stack

- **Monorepo:** Turbo with `pnpm` workspaces
- **Node/TypeScript:** Backend services, APIs, tooling
- **Python 3.10+:** Data processing pipelines (using `uv` as package manager)
- **Rust (2024 edition):** Performance-critical ingest and masking
- **React 19 / Next.js:** UI dashboard

### Package Organization

```
apps/
  ├── gateway-api          → GraphQL/gRPC API server (Fastify + Mercurius)
  ├── refinery-core        → Rust core for data ingestion, transformation, Avro serialization
  ├── nexus-manager        → Python vector-graph database manager
  └── aether-dashboard     → React/Next.js UI

packages/
  ├── mcp-bridge          → Model Context Protocol server implementation
  ├── schema-discovery    → MinHash + LSH schema alignment (Python)
  ├── sync-engine         → Merkle tree incremental sync engine (Python)
  ├── entity-resolution   → Union-Find entity deduplication (Python)
  ├── shield-pii          → PII masking library (Rust + WASM)
  ├── shield-wasm         → WASM bindings for shield-pii
  ├── aether-sdk-ts       → TypeScript SDK
  ├── sdk/ts              → TS SDK subpackage
  ├── sdk/python          → Python SDK subpackage
  ├── ui                  → Shared React components
  ├── config              → Shared configuration
  ├── semantic-spec       → Avro schema definitions
  └── chaos-tests         → Integration test suite
```

## Development Commands

All commands use **Turbo** for orchestration and run against the appropriate workspace based on dependencies:

### Core Commands

```bash
# Install dependencies (uses pnpm)
pnpm install

# Run all dev servers (persistent, cache disabled)
turbo dev
# Alternatively: pnpm dev

# Build all packages (respects build dependencies)
turbo build
# Alternatively: pnpm build

# Run linting across all packages
turbo lint

# Format code with Prettier
turbo format

# Type check all TypeScript code
turbo check-types
```

### Running Individual Packages

```bash
# Run a specific package's task
turbo run dev --filter=gateway-api
turbo run test --filter=schema-discovery
turbo run build --filter=refinery-core

# Run only packages matching a pattern
turbo run test --filter='./packages/*'
```

### Package-Specific Commands

**Gateway API** (TypeScript service with Fastify + Mercurius):
```bash
cd apps/gateway-api
pnpm dev          # Run with hot reload (tsx watch)
pnpm build        # Build to dist/
pnpm test         # Run Vitest
pnpm start        # Run compiled output
```

**Refinery Core** (Rust):
```bash
cd apps/refinery-core
cargo build --release
cargo test
cargo clippy       # Linting
cargo fmt          # Format
```

**Python Packages** (schema-discovery, sync-engine, entity-resolution, nexus-manager):
```bash
cd packages/schema-discovery
uv sync            # Install dependencies
uv run pytest      # Run tests
uv build           # Build wheel
```

**Aether Dashboard** (Next.js):
```bash
cd apps/aether-dashboard
pnpm dev           # Start dev server at http://localhost:3000
pnpm build         # Build for production
pnpm start         # Run production build
```

**MCP Bridge**:
```bash
cd packages/mcp-bridge
pnpm dev           # Run MCP server with tsx watch
pnpm test          # Run Vitest
```

## Key Design Patterns

### Data Pipeline

1. **Ingest:** `refinery-core` reads from legacy SQL/SaaS sources using `sqlx`, applies Avro serialization
2. **Refine:** `shield-pii` masks sensitive data; configurable chunking strategies
3. **Schema Discovery:** `schema-discovery` uses MinHash + LSH for efficient schema alignment across heterogeneous sources
4. **Sync:** `sync-engine` implements Merkle tree snapshots for incremental synchronization with SQLite persistence
5. **Entity Resolution:** `entity-resolution` uses Union-Find algorithm for cross-source entity deduplication
6. **Expose:** `gateway-api` provides GraphQL/gRPC access; `mcp-bridge` enables agent integration

### Polyglot Approach

- **Rust** (`refinery-core`, `shield-pii`): CPU-bound data processing, serialization
- **Python** (data engines): ML-style data processing, algorithmic workloads
- **TypeScript** (APIs, SDKs): Glue, agent interfaces, real-time communication
- **React** (UI): Monitoring, configuration, telemetry visualization

### Important Notes

- **Turbo tasks depend on build outputs:** `test` depends on `build`, `build` respects `^build` (dependencies first)
- **Python uses `uv`:** Not pip. Check `.python-version` files (e.g., `3.10`) for Python version constraints
- **Rust edition 2024:** Uses newer syntax; ensure `rustup` is up to date
- **Avro schemas:** Defined in `semantic-spec`; code generation happens during build
- **gRPC/Protobuf:** `refinery-core` uses `prost`; protos should be in `src/protos/`
- **Next.js version differences:** Aether dashboard uses Next.js 15+; see `AGENTS.md` in that app for breaking changes

## Testing

- **Turbo caching:** Test output is cached by default; use `turbo run test --force` to bypass
- **Vitest** (Node packages): `pnpm test` in each package
- **Pytest** (Python): `uv run pytest` from package directory
- **Cargo test** (Rust): `cargo test` respects workspace structure
- **Integration tests:** `packages/chaos-tests` contains multi-package scenarios

## Notes for Future Development

- Before adding new packages, verify if it should be an app or package (apps = services, packages = libraries/utilities)
- Keep polyglot rationale in mind: if a new component is pure data processing, prefer Python; if real-time/network, prefer TS; if CPU-critical, prefer Rust
- Turbo configurations in `turbo.json` define task dependencies; update if adding new task types
- The monorepo uses `@aether/` namespace for all packages; maintain this convention
- PII handling is critical: always run through `shield-pii` pipeline before exposure
