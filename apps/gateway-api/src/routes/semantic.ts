import { FastifyInstance, FastifyRequest, FastifyReply } from "fastify";
import { z } from "zod";
import * as nexusClient from "../nexusClient";

const GraphRAGSchema = z.object({
  query: z.string().min(3),
  target_nodes: z.array(z.string()).optional(),
  depth: z.number().int().min(1).max(5).default(2),
});

const VectorProjectionSchema = z.object({
  embeddings: z.array(z.number()).optional(),
  text: z.string().optional(),
  threshold: z.number().min(0.0).max(1.0).default(0.85),
  top_k: z.number().int().min(1).default(10),
}).refine(
  (data) => data.embeddings || data.text,
  { message: "Either embeddings or text must be provided" }
);

export const semanticRoutes = async (fastify: FastifyInstance) => {
  fastify.post(
    "/api/semantic/graph-rag",
    {
      schema: { body: GraphRAGSchema },
    },
    async (request: FastifyRequest, reply: FastifyReply) => {
      try {
        const { query, target_nodes, depth } = request.body as z.infer<typeof GraphRAGSchema>;
        const tenantId = (request as any).tenant_id;

        request.log.info(
          `Graph-RAG query: ${query} (Depth: ${depth}, Tenant: ${tenantId || "default"})`,
        );

        const response = await nexusClient.callGraphRag(
          { query, target_nodes, depth },
          tenantId,
        );

        return response;
      } catch (error) {
        if (error instanceof nexusClient.NexusClientError) {
          request.log.error(`Nexus Manager error: ${error.message}`);
          reply.status(502);
          return {
            success: false,
            nodes_traversed: 0,
            edges_found: [],
            context_payload: `Backend unavailable: ${error.message}`,
          };
        }

        request.log.error(`Unexpected error: ${error}`);
        reply.status(500);
        return {
          success: false,
          nodes_traversed: 0,
          edges_found: [],
          context_payload: "Internal server error",
        };
      }
    },
  );

  fastify.post(
    "/api/semantic/vector-projection",
    {
      schema: { body: VectorProjectionSchema },
    },
    async (request: FastifyRequest, reply: FastifyReply) => {
      try {
        const { embeddings, text, threshold, top_k } = request.body as z.infer<typeof VectorProjectionSchema>;
        const tenantId = (request as any).tenant_id;

        request.log.info(
          `Vector search: ${text ? `text="${text.substring(0, 50)}..."` : `embeddings[${embeddings?.length}]`} (Tenant: ${tenantId || "default"})`,
        );

        const response = await nexusClient.callVectorProjection(
          { embeddings, text, threshold, top_k },
          tenantId,
        );

        return response;
      } catch (error) {
        if (error instanceof nexusClient.NexusClientError) {
          request.log.error(`Nexus Manager error: ${error.message}`);
          reply.status(502);
          return {
            success: false,
            matched_uuids: [],
            matches: [],
            confidence_score: 0.0,
          };
        }

        request.log.error(`Unexpected error: ${error}`);
        reply.status(500);
        return {
          success: false,
          matched_uuids: [],
          matches: [],
          confidence_score: 0.0,
        };
      }
    },
  );
};
