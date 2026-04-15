# gateway-api

**Mission:** The secure "Control Plane" and entry point for all external requests.

* **Tech Stack:** Node.js (Fastify), TypeScript, Zod, Redis.
* **Core Logic:**
    * **Rate Limiting:** Protects downstream AI models from token-exhaustion attacks.
    * **Audit Logging:** Every data access request is logged with a "Provenance Trace" for compliance.

> The `gateway-api` is the traffic controller. It handles high-concurrency requests from both humans and AI Agents, ensuring that every request is authenticated via the Aether Auth layer before touching the data fabric.
