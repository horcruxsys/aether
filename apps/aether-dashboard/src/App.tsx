import React, { useState, useEffect } from "react";
import { Button } from "@aether/ui";
import "./App.css";

export default function App() {
  const [anomalyStatus, setAnomalyStatus] = useState<string>("SYSTEM NOMINAL");
  const [messages, setMessages] = useState<{timestamp: string, msg: string}[]>([]);

  useEffect(() => {
    // Open WebSocket bound to Phase 29 Fastify implementation
    try {
      const ws = new WebSocket("ws://localhost:3000/ws/telemetry");
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.event === "telemetry_diff") {
          const timestamp = new Date(data.timestamp).toLocaleTimeString();
          setMessages(prev => [...prev, {
            timestamp, 
            msg: "Live CDC Ingestion Burst Processed"
          }].slice(-10));
        }
      };

      return () => ws.close();
    } catch (e) {
      console.warn("WebSocket grid connection failed - Local environment boundary.");
    }
  }, []);

  return (
    <div className="dashboard-container">
      <h1 className="title-main">Aether Intelligence Core</h1>
      
      <div className="telemetry-card">
        <h2 className="card-title">Multi-Region Swarm Telemetry</h2>
        <div className="log-viewer">
          {messages.length === 0 ? (
            <p className="empty-state">Awaiting OIDC Handshake & Stream Sync...</p>
          ) : (
            messages.map((item, idx) => (
              <div key={idx} className="log-entry">
                <span className="timestamp">[{item.timestamp}]</span>
                <span className="message">{item.msg}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="controls-group">
        <Button 
          variant="danger" 
          size="lg" 
          onClick={() => setAnomalyStatus("DRIFT DETECTED: LangGraph Overriding")}
        >
          Inject Drift Anomaly
        </Button>
        <Button 
          variant="primary" 
          size="lg" 
          onClick={() => setAnomalyStatus("SYSTEM NOMINAL")}
        >
          Clear Memory Grids
        </Button>
      </div>

      <p className={`status-indicator ${anomalyStatus === "SYSTEM NOMINAL" ? 'status-nominal' : 'status-drift'}`}>
        STATUS: {anomalyStatus}
      </p>
    </div>
  );
}
