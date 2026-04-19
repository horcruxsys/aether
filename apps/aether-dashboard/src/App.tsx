import React, { useState, useEffect } from "react";
import { Button } from "@aether/ui";

export default function App() {
  const [anomalyStatus, setAnomalyStatus] = useState<string>("SYSTEM NOMINAL");
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    // OpenWebSocket bound to Phase 29 Fastify implementation
    const ws = new WebSocket("ws://localhost:3000/ws/telemetry");
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "telemetry_diff") {
        setMessages(prev => [...prev, `[${new Date(data.timestamp).toLocaleTimeString()}] Live CDC Event Processed.`].slice(-5));
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center space-y-8 p-12">
      <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
        Aether Agentic Orchestrator
      </h1>
      
      <div className="bg-gray-800 rounded-xl p-8 shadow-2xl border border-gray-700 w-full max-w-3xl">
        <h2 className="text-xl font-semibold mb-4 text-gray-300">Swarm Telemetry</h2>
        <div className="h-64 bg-gray-900 rounded p-4 font-mono text-sm overflow-y-auto space-y-2 border border-gray-700">
          {messages.length === 0 ? <p className="text-gray-500">Listening to zero-trust pipelines...</p> : null}
          {messages.map((msg, idx) => <p key={idx} className="text-green-400">{msg}</p>)}
        </div>
      </div>

      <div className="flex space-x-6">
        <Button variant="danger" size="lg" onClick={() => setAnomalyStatus("DRIFT DETECTED: LangGraph Overriding")}>
          Simulate Semantic Drift
        </Button>
        <Button variant="primary" size="lg" onClick={() => setAnomalyStatus("SYSTEM NOMINAL")}>
          Resolve Handshake
        </Button>
      </div>

      <p className={`text-xl font-bold ${anomalyStatus === "SYSTEM NOMINAL" ? 'text-green-500' : 'text-red-500 animate-pulse'}`}>
        {anomalyStatus}
      </p>
    </div>
  );
}
