import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { fastify } from "../src/index";

describe("Gateway API Integration Tests", () => {
  beforeAll(async () => {
    await fastify.ready();
  });

  afterAll(async () => {
    await fastify.close();
  });

  it("should return ok for /health", async () => {
    const response = await fastify.inject({
      method: "GET",
      url: "/health",
    });

    expect(response.statusCode).toBe(200);
    const json = JSON.parse(response.body);
    expect(json.status).toBe("ok");
    expect(json.timestamp).toBeDefined();
  });

  it("should reject invalid /migrate payload due to zod schema validation", async () => {
    const response = await fastify.inject({
      method: "POST",
      url: "/migrate",
      payload: {
        source: "not-a-url", // This breaks validation
        destination: "nexus",
      },
    });

    expect(response.statusCode).toBe(400);
  });
});
