"use client";

import { useEffect, useState } from "react";

interface TelemetryEvent {
  event: string;
  timestamp: number;
  data: Record<string, unknown>;
}

export default function Dashboard() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<TelemetryEvent | null>(null);
  const [eventCount, setEventCount] = useState(0);
  const [activeJobs, setActiveJobs] = useState(0);
  const [totalVectors, setTotalVectors] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState("Disconnecting...");

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log("[Dashboard] WebSocket connected");
          setIsConnected(true);
          setConnectionStatus("Connected");
        };

        ws.onmessage = (event) => {
          try {
            const telemetry: TelemetryEvent = JSON.parse(event.data);
            console.log("[Dashboard] Received telemetry:", telemetry);

            setLastEvent(telemetry);
            setEventCount((prev) => prev + 1);

            // Update dashboard metrics based on event type
            if (
              telemetry.event === "health_update" &&
              telemetry.data
            ) {
              setActiveJobs(telemetry.data.active_jobs as number || 0);
              setTotalVectors(telemetry.data.total_vectors as number || 0);
            }

            if (
              telemetry.event === "ingestion_progress" &&
              telemetry.data
            ) {
              setTotalVectors((prev) =>
                Math.max(prev, (telemetry.data.processed_count as number) || 0)
              );
            }
          } catch (error) {
            console.error("[Dashboard] Error parsing telemetry:", error);
          }
        };

        ws.onerror = (error) => {
          console.error("[Dashboard] WebSocket error:", error);
          setConnectionStatus("Error");
        };

        ws.onclose = () => {
          console.log("[Dashboard] WebSocket disconnected");
          setIsConnected(false);
          setConnectionStatus("Disconnected - Reconnecting in 3s...");

          // Auto-reconnect after 3 seconds
          reconnectTimer = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        };
      } catch (error) {
        console.error("[Dashboard] Failed to create WebSocket:", error);
        setConnectionStatus("Failed to connect");
      }
    };

    // Connect on mount
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Aether Dashboard</h1>
            <p className="text-slate-400">Real-time ingestion telemetry</p>
          </div>
          <div className="text-right">
            <div
              className={`inline-block px-4 py-2 rounded-full text-sm font-medium ${
                isConnected
                  ? "bg-green-500/20 text-green-400 border border-green-500/30"
                  : "bg-red-500/20 text-red-400 border border-red-500/30"
              }`}
            >
              {connectionStatus}
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Active Jobs Card */}
          <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <div className="text-slate-400 text-sm font-medium mb-2">
              Active Jobs
            </div>
            <div className="text-5xl font-bold mb-2">{activeJobs}</div>
            <div className="text-slate-500 text-xs">
              Ingestion pipelines running
            </div>
          </div>

          {/* Total Vectors Card */}
          <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <div className="text-slate-400 text-sm font-medium mb-2">
              Vectors Processed
            </div>
            <div className="text-5xl font-bold mb-2">
              {totalVectors.toLocaleString()}
            </div>
            <div className="text-slate-500 text-xs">Semantic embeddings</div>
          </div>

          {/* Events Received Card */}
          <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
            <div className="text-slate-400 text-sm font-medium mb-2">
              Events Received
            </div>
            <div className="text-5xl font-bold mb-2">
              {eventCount.toLocaleString()}
            </div>
            <div className="text-slate-500 text-xs">
              Telemetry messages since page load
            </div>
          </div>
        </div>

        {/* Last Event Details */}
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
          <h2 className="text-xl font-bold mb-4">Latest Event</h2>

          {lastEvent ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-slate-400 text-xs uppercase tracking-wider">
                    Event Type
                  </div>
                  <div className="text-lg font-mono text-blue-400 mt-1">
                    {lastEvent.event}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 text-xs uppercase tracking-wider">
                    Timestamp
                  </div>
                  <div className="text-lg font-mono text-green-400 mt-1">
                    {formatTime(lastEvent.timestamp)}
                  </div>
                </div>
              </div>

              {Object.keys(lastEvent.data).length > 0 && (
                <div>
                  <div className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                    Event Data
                  </div>
                  <div className="bg-slate-900/50 rounded p-3 font-mono text-sm text-slate-300 overflow-auto max-h-40">
                    {JSON.stringify(lastEvent.data, null, 2)}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-slate-400 italic">
              Waiting for telemetry events...
            </div>
          )}
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center text-slate-500 text-xs">
          <p>
            WebSocket connection to{" "}
            <code className="text-slate-400">/ws/telemetry</code> • Events
            update in real-time
          </p>
        </div>
      </div>
    </div>
  );
}
