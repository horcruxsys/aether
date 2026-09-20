/**
 * HTTP client for nexus-manager service
 * Handles all outbound calls to the vector-graph database backend
 */

const NEXUS_MANAGER_URL = process.env.NEXUS_MANAGER_URL || "http://localhost:8000";
const TIMEOUT_MS = 30_000;

export interface GraphRagRequest {
  query: string;
  target_nodes?: string[];
  depth?: number;
}

export interface GraphRagResponse {
  success: boolean;
  nodes_traversed: number;
  edges_found: Array<{
    id: string;
    source: string;
    relation: string;
    target: string;
  }>;
  context_payload: string;
}

export interface VectorProjectionRequest {
  embeddings?: number[];
  text?: string;
  threshold?: number;
  top_k?: number;
}

export interface VectorProjectionMatch {
  id: string;
  score: number;
  content: string;
  metadata: Record<string, unknown>;
  mask_map: Record<string, string>;
  tenant_id: string;
}

export interface VectorProjectionResponse {
  success: boolean;
  matched_uuids: string[];
  matches: VectorProjectionMatch[];
  confidence_score: number;
}

export interface DatasetMetadata {
  urn: string;
  pii_count: number;
  chunk_count: number;
  tombstone_count: number;
}

class NexusClientError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string,
  ) {
    super(message);
    this.name = "NexusClientError";
  }
}

async function request<T>(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
  headers?: Record<string, string>,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(`${NEXUS_MANAGER_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new NexusClientError(
        response.status,
        response.statusText,
        `Nexus Manager returned ${response.status}: ${response.statusText}`,
      );
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function callGraphRag(
  body: GraphRagRequest,
  tenantId?: string,
): Promise<GraphRagResponse> {
  const headers: Record<string, string> = {};
  if (tenantId) {
    headers["x-tenant-id"] = tenantId;
  }

  return request<GraphRagResponse>("POST", "/internal/graph-rag", body, headers);
}

export async function callVectorProjection(
  body: VectorProjectionRequest,
  tenantId?: string,
): Promise<VectorProjectionResponse> {
  const headers: Record<string, string> = {};
  if (tenantId) {
    headers["x-tenant-id"] = tenantId;
  }

  return request<VectorProjectionResponse>(
    "POST",
    "/internal/vector-projection",
    body,
    headers,
  );
}

export async function getDatasetMetadata(
  urn: string,
  tenantId?: string,
): Promise<DatasetMetadata> {
  const headers: Record<string, string> = {};
  if (tenantId) {
    headers["x-tenant-id"] = tenantId;
  }

  return request<DatasetMetadata>(
    "GET",
    `/internal/datasets/${encodeURIComponent(urn)}`,
    undefined,
    headers,
  );
}

export async function getActiveJobs(tenantId?: string) {
  const headers: Record<string, string> = {};
  if (tenantId) {
    headers["x-tenant-id"] = tenantId;
  }

  return request<{
    active_jobs: Array<{
      job_id: string;
      source_urn: string;
      status: string;
      processed_count: number;
      pii_masked_count: number;
      timestamp: string;
    }>;
    total_processed: number;
  }>("GET", "/internal/jobs", undefined, headers);
}

export async function getHealthStatus() {
  return request<{
    status: string;
    dump_dir: string;
    vector_store: string;
    active_jobs: number;
  }>("GET", "/health");
}

export async function getVersion() {
  return request<{
    version: string;
    name: string;
    status: string;
  }>("GET", "/version");
}

export { NexusClientError };
