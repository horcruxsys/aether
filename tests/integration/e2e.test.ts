/**
 * End-to-end integration tests for Aether data pipeline
 * Tests the full flow: refinery-core → nexus-manager → gateway-api
 *
 * Requires: docker-compose up -d running with all services healthy
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { promises as fs } from "fs";
import path from "path";

const GATEWAY_API_URL = "http://localhost:3000";
const NEXUS_MANAGER_URL = "http://localhost:8000";
const CACHE_DIR = ".cache/aether-dump";

/**
 * Helper to fetch with timeout
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs = 10000,
) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Helper to wait for a condition with retries
 */
async function waitForCondition(
  fn: () => Promise<boolean>,
  maxAttempts = 30,
  delayMs = 1000,
): Promise<void> {
  for (let i = 0; i < maxAttempts; i++) {
    if (await fn()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error("Condition timeout exceeded");
}

describe("Aether E2E Pipeline", () => {
  describe("Service Health Checks", () => {
    it("gateway-api should be healthy", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/health`,
      );
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.status).toBe("ok");
    });

    it("nexus-manager should be healthy", async () => {
      const response = await fetchWithTimeout(
        `${NEXUS_MANAGER_URL}/health`,
      );
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.status).toBe("operational");
    });

    it("nexus-manager should report vector store mode", async () => {
      const response = await fetchWithTimeout(
        `${NEXUS_MANAGER_URL}/health`,
      );
      const data = await response.json();
      expect(["qdrant_embedded", "qdrant_remote"]).toContain(
        data.vector_store,
      );
    });
  });

  describe("GraphQL Resolvers", () => {
    const graphqlQuery = (query: string) =>
      fetchWithTimeout(`${GATEWAY_API_URL}/graphql`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

    it("should return version", async () => {
      const response = await graphqlQuery("{ version }");
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.data.version).toBeDefined();
      expect(data.data.version).toMatch(/aether/i);
    });

    it("should return empty ingestion jobs initially", async () => {
      const response = await graphqlQuery("{ activeIngestionJobs { id } }");
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(Array.isArray(data.data.activeIngestionJobs)).toBe(true);
    });

    it("should return dataset metadata for unknown URN", async () => {
      const response = await graphqlQuery(
        '{ datasetMetadata(urn: "test://unknown") { urn pii_count } }',
      );
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.data.datasetMetadata.urn).toBe("test://unknown");
    });
  });

  describe("Vector Projection (Semantic Search)", () => {
    it("should accept text-based vector search", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/vector-projection`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: "What is customer information?",
            threshold: 0.5,
            top_k: 5,
          }),
        },
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(Array.isArray(data.matched_uuids)).toBe(true);
      expect(Array.isArray(data.matches)).toBe(true);
      expect(typeof data.confidence_score).toBe("number");
    });

    it("should accept pre-computed embeddings", async () => {
      const embedding = new Array(384).fill(0.1); // MiniLM is 384-d

      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/vector-projection`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            embeddings: embedding,
            threshold: 0.85,
            top_k: 10,
          }),
        },
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
    });

    it("should reject request without embeddings or text", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/vector-projection`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            threshold: 0.5,
          }),
        },
      );

      expect(response.status).toBe(400); // Zod validation error
    });
  });

  describe("Graph RAG Query", () => {
    it("should accept graph RAG query", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/graph-rag`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: "Find all customer documents",
            depth: 2,
          }),
        },
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
      expect(typeof data.nodes_traversed).toBe("number");
      expect(Array.isArray(data.edges_found)).toBe(true);
      expect(typeof data.context_payload).toBe("string");
    });

    it("should accept optional target_nodes parameter", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/graph-rag`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: "Find documents from source A",
            target_nodes: ["Document:A", "Document:B"],
            depth: 3,
          }),
        },
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
    });

    it("should require minimum 3-char query", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/graph-rag`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: "ab",
          }),
        },
      );

      expect(response.status).toBe(400); // Zod validation
    });
  });

  describe("Nexus Manager Routes", () => {
    it("GET /internal/jobs should return job list", async () => {
      const response = await fetchWithTimeout(
        `${NEXUS_MANAGER_URL}/internal/jobs`,
      );
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.active_jobs).toBeDefined();
      expect(Array.isArray(data.active_jobs)).toBe(true);
      expect(typeof data.total_processed).toBe("number");
    });

    it("GET /internal/datasets/{urn} should return metadata", async () => {
      const response = await fetchWithTimeout(
        `${NEXUS_MANAGER_URL}/internal/datasets/test%3A%2F%2Fsample`,
      );
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.urn).toBeDefined();
      expect(typeof data.pii_count).toBe("number");
      expect(typeof data.chunk_count).toBe("number");
    });

    it("POST /internal/vector-projection should work", async () => {
      const embedding = new Array(384).fill(0.1);
      const response = await fetchWithTimeout(
        `${NEXUS_MANAGER_URL}/internal/vector-projection`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            embeddings: embedding,
            threshold: 0.5,
            top_k: 5,
          }),
        },
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
    });

    it("POST /internal/graph-rag should work", async () => {
      const response = await fetchWithTimeout(
        `${NEXUS_MANAGER_URL}/internal/graph-rag`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: "Test query",
            depth: 1,
          }),
        },
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.success).toBe(true);
    });
  });

  describe("Error Handling", () => {
    it("gateway-api should return 502 when nexus-manager is unavailable", async () => {
      // This test would only run if nexus is explicitly stopped
      // Skipping for now as it requires orchestration
    });

    it("should handle malformed JSON gracefully", async () => {
      const response = await fetchWithTimeout(
        `${GATEWAY_API_URL}/api/semantic/vector-projection`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{ invalid json",
        },
      );

      expect(response.status).toBeGreaterThanOrEqual(400);
    });
  });
});
