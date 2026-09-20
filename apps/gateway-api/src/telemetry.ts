/**
 * Real-time telemetry streaming via WebSocket backed by Redis pub/sub
 * Allows dashboard to receive live ingestion events and metrics
 */

import { FastifyInstance } from "fastify";
import { Server } from "socket.io";

// This will be populated at runtime
let sockets: Set<any> = new Set();

interface TelemetryEvent {
  event: string;
  timestamp: number;
  data: Record<string, unknown>;
}

/**
 * Initialize telemetry streaming
 * For MVP, use in-memory broadcasting to all connected clients
 * In production (Phase 1), replace with Redis pub/sub for distributed deployment
 */
export function initTelemetry(fastify: FastifyInstance) {
  // Register WebSocket route
  fastify.register(async function (fastify) {
    fastify.get("/ws/telemetry", { websocket: true }, (connection, req) => {
      console.log("[Telemetry] New WebSocket client connected");
      sockets.add(connection.socket);

      // Send initial connection message
      connection.socket.send(
        JSON.stringify({
          event: "connected",
          timestamp: Date.now(),
          data: { clients: sockets.size },
        } as TelemetryEvent),
      );

      // Handle incoming messages (client heartbeat, etc.)
      connection.socket.on("message", (message: any) => {
        try {
          const msg = JSON.parse(message.toString());
          console.log("[Telemetry] Received from client:", msg);

          // Echo back a server acknowledgment
          connection.socket.send(
            JSON.stringify({
              event: "ack",
              timestamp: Date.now(),
              data: { received: msg },
            } as TelemetryEvent),
          );
        } catch (error) {
          console.error("[Telemetry] Error parsing client message:", error);
        }
      });

      connection.socket.on("close", () => {
        console.log("[Telemetry] Client disconnected");
        sockets.delete(connection.socket);
      });

      connection.socket.on("error", (error) => {
        console.error("[Telemetry] WebSocket error:", error);
        sockets.delete(connection.socket);
      });
    });
  });

  console.log("[Telemetry] WebSocket server initialized at /ws/telemetry");
}

/**
 * Broadcast a telemetry event to all connected clients
 * In MVP: direct in-memory broadcast
 * In production: publish to Redis pub/sub for multi-instance deployment
 */
export function broadcastTelemetry(event: TelemetryEvent) {
  const message = JSON.stringify(event);
  let sent = 0;

  for (const socket of sockets) {
    try {
      if (socket.readyState === 1) {
        // WebSocket.OPEN = 1
        socket.send(message);
        sent++;
      }
    } catch (error) {
      console.error("[Telemetry] Error broadcasting to socket:", error);
      sockets.delete(socket);
    }
  }

  if (sent > 0) {
    console.log(`[Telemetry] Broadcast to ${sent}/${sockets.size} clients`);
  }
}

/**
 * Publish ingestion progress event (called by refinery-core results)
 */
export function publishIngestionProgress(data: {
  job_id: string;
  source_urn: string;
  uuid: string;
  processed_count: number;
  pii_masked_count: number;
}) {
  broadcastTelemetry({
    event: "ingestion_progress",
    timestamp: Date.now(),
    data,
  });
}

/**
 * Publish data drift alert
 */
export function publishDriftAlert(data: {
  source_urn: string;
  drift_score: number;
  threshold: number;
}) {
  broadcastTelemetry({
    event: "semantic_drift",
    timestamp: Date.now(),
    data,
  });
}

/**
 * Publish health status
 */
export function publishHealthStatus(data: {
  status: string;
  active_jobs: number;
  total_vectors: number;
}) {
  broadcastTelemetry({
    event: "health_update",
    timestamp: Date.now(),
    data,
  });
}

/**
 * Get current number of connected clients
 */
export function getConnectedClients() {
  return sockets.size;
}
