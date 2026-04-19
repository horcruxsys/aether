import { describe, it, expect } from "vitest";
import { server } from "../src/index";

describe("MCP Bridge Tool Tests", () => {
  it("should list available tools", async () => {
    // We mock the RequestHandler interaction for basic integration tests
    const listToolsHandler = (server as any).requestHandlers.get("tools/list");
    expect(listToolsHandler).toBeDefined();

    const response = await listToolsHandler(
      { method: "tools/list", params: {} } as any,
      {} as any,
    );
    expect(response.tools.length).toBeGreaterThan(0);
    expect(
      response.tools.find((t: any) => t.name === "trigger_migration_job"),
    ).toBeDefined();
  });

  it("should handle trigger_migration_job properly", async () => {
    const callToolHandler = (server as any).requestHandlers.get("tools/call");
    expect(callToolHandler).toBeDefined();

    const response = await callToolHandler(
      {
        method: "tools/call",
        params: {
          name: "trigger_migration_job",
          arguments: {
            source_urn: "cdc://postgres",
          },
        },
      } as any,
      {} as any,
    );

    expect(response.content[0].type).toBe("text");
    expect(response.content[0].text).toContain(
      "Successfully registered migration request",
    );
  });

  it("should handle query_vector_drift properly", async () => {
    const callToolHandler = (server as any).requestHandlers.get("tools/call");

    const response = await callToolHandler(
      {
        method: "tools/call",
        params: {
          name: "query_vector_drift",
          arguments: {},
        },
      } as any,
      {} as any,
    );

    expect(response.content[0].text).toContain(
      "Drift metrics: 14 vectors pruned",
    );
  });
});
