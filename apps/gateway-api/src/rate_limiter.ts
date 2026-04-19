import { semanticCache } from "./cache.js";

/**
 * Hard stops API ingestion traffic exceeding 50 requests per second locally,
 * leveraging Redis for decentralized counting against DDoS hallucination vectors.
 */
export async function rateLimit(tenant_id: string): Promise<boolean> {
  const current_window = Math.floor(Date.now() / 1000);
  const key = `rl_${tenant_id}_${current_window}`;

  const hits = await semanticCache.incr(key);
  if (hits === 1) {
    await semanticCache.expire(key, 5);
  }

  return hits <= 50;
}
