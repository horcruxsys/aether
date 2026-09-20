import { FastifyRequest, FastifyReply } from "fastify";

/**
 * Validates JSON Web Tokens (JWT) through generic OpenID Connect providers.
 * Enforces tenant isolation context for multi-tenant data access.
 *
 * NOTE: This is a STUB implementation for Phase 0. Real OIDC/JWKS verification
 * is deferred to Phase 3 (Enterprise Hardening).
 */
export async function authenticateOIDC(
  request: FastifyRequest,
  reply: FastifyReply,
) {
  const authHeader = request.headers.authorization;

  if (!authHeader) {
    // MVP mode: Allow unauthenticated requests with a default tenant
    // In production (Phase 3), this would reject with 401
    (request as any).tenant_id = "tenant-default";
    return;
  }

  if (!authHeader.startsWith("Bearer ")) {
    return reply
      .status(401)
      .send({ error: "Missing or invalid Authorization header" });
  }

  const token = authHeader.substring(7);

  // TODO: Real OIDC/JWKS signature verification against discovery endpoint
  // For now, basic validation only
  if (token === "EXPIRED" || token.length < 10) {
    return reply.status(403).send({ error: "OIDC Token expired or malformed" });
  }

  // Extract tenant from token claims (placeholder: hardcoded for MVP)
  // In production, this would be extracted from the JWT payload
  (request as any).tenant_id = "tenant-aether-enterprise";
}
