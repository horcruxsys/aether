# gateway-api & mcp-bridge (Agentic Integration)

**Mission:** Making Aether "Agent-Native" and acting as the secure "Control Plane" entry point.

This documentation suite covers the Model Context Protocol (MCP) implementation (`mcp-bridge`) combined with the secure Edge layer (`gateway-api`).

## Low-Level Design (LLD)

### Secure API Layer & Routing
- **`gateway-api`:** Fastify implementation serving as a high-throughput choke point validating migration requests via `Zod`. It orchestrates downstream Rust pipelines through a secure `gRPC` control plane wrapper.
- **`mcp-bridge`:** Translates the system's capabilities directly into the Model Context Protocol (MCP). It defines how autonomous agents (like Claude or GPT) interact with Aether as a "Native Tool", enabling them to safely queue data refinements and retrieve grounded contextual snippets without ever touching bare metal.

> This layer provides total data encapsulation, ensuring that every request is authenticated before touching the data fabric. It transforms the Aether platform into an immediate, native component for the modern AI workforce.
