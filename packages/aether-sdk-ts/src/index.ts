export interface AetherClientOptions {
  apiUrl: string;
  jwtToken: string;
  tenantId: string;
}

/**
 * Aether Enterprise Edge SDK bindings.
 * Abstracts the raw Gateway REST and WebSocket topologies allowing third-party Enterprise
 * platforms to ingest multi-modal chunks deterministically.
 */
export class AetherClient {
  private config: AetherClientOptions;

  constructor(options: AetherClientOptions) {
    this.config = options;
  }

  async runGraphQuery(queryContext: string, options: { depth?: number } = {}) {
    const res = await fetch(`${this.config.apiUrl}/api/semantic/graph-rag`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.config.jwtToken}`,
        "X-Tenant-ID": this.config.tenantId
      },
      body: JSON.stringify({
        query: queryContext,
        depth: options.depth || 2
      })
    });

    if (!res.ok) throw new Error("Aether Matrix Rejection: " + res.statusText);
    return res.json();
  }
}
