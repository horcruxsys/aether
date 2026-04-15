import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Initialize a new MCP Server that autonomous agents will communicate with
const server = new Server(
  {
    name: "Aether Agent Gateway",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// Declare available Tools for Claude/LLM agents
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "trigger_migration_job",
        description:
          "Programmatically trigger the Aether Refinery core pipeline to extract and mask data from a legacy schema.",
        inputSchema: {
          type: "object",
          properties: {
            source_urn: {
              type: "string",
              description:
                "The SQL database source URN (e.g., 'cdc://legacy_db')",
            },
            query_filters: {
              type: "string",
              description: "Any specific constraints to apply to the data pull",
            },
          },
          required: ["source_urn"],
        },
      },
      {
        name: "query_vector_drift",
        description:
          "Pull metrics on deleted Tombstones identified inside the Qdrant database to prevent LLM hallucinations.",
        inputSchema: {
          type: "object",
          properties: {},
          required: [],
        },
      },
    ],
  };
});

// Configure actions when variables are routed into the Node
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "trigger_migration_job") {
    // In production, this would make a gRPC request downstream to the `gateway-api`
    return {
      content: [
        {
          type: "text",
          text: `Successfully registered migration request for source: ${args?.source_urn}. Background CDC ingestion initiated on the rust Core.`,
        },
      ],
    };
  }

  if (name === "query_vector_drift") {
    return {
      content: [
        {
          type: "text",
          text: `Drift metrics: 14 vectors pruned recently via TOMBSTONE mechanisms to prevent hallucinations.`,
        },
      ],
    };
  }

  throw new Error(`Tool not found: ${name}`);
});

// Start the server using standard IPC (stdio)
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Aether MCP Bridge is running on stdio transport.");
}

main().catch((error) => {
  console.error("Agent Gateway Fatal Error:", error);
  process.exit(1);
});
