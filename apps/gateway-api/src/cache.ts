import Redis from "ioredis";

// Instantiate native connection pool to the localized isolated Redis cluster
export const semanticCache = new Redis({
  host: process.env.REDIS_HOST || "localhost",
  port: parseInt(process.env.REDIS_PORT || "6379"),
  maxRetriesPerRequest: 1, // Fail fast on edge bounds
  lazyConnect: true,
});

export async function getCachedVector(queryRef: string): Promise<number[] | null> {
  const hit = await semanticCache.get(`aether_vec:${queryRef}`);
  return hit ? JSON.parse(hit) : null;
}

export async function setCachedVector(queryRef: string, embeddings: number[]): Promise<void> {
  // Ensure cached nodes dissolve logically to prevent semantic drift against the backend embeddings
  await semanticCache.set(`aether_vec:${queryRef}`, JSON.stringify(embeddings), "EX", 3600);
}
