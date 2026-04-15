import React from "react";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-cyan-500/30">
      <main className="container mx-auto px-6 py-12">
        <header className="mb-12 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
              Aether Nexus
            </h1>
            <p className="mt-2 text-slate-400">
              Enterprise PII Telemetry & CDC Sync
            </p>
          </div>
          <div className="flex border border-slate-800 bg-slate-900/50 rounded-full px-4 py-2 items-center space-x-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-sm font-medium text-slate-300">
              Qdrant Active
            </span>
          </div>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <MetricCard
            title="Total Vectors Embedded"
            value="14,029"
            trend="+12% this hour"
          />
          <MetricCard
            title="PII Entities Masked"
            value="98,401"
            trend="Shield Active"
            highlight="cyan"
          />
          <MetricCard
            title="Tombstones Pruned"
            value="14"
            trend="Zero-Drift Validated"
            highlight="rose"
          />
        </section>

        <section className="border border-slate-800 rounded-xl bg-slate-900/30 p-8 shadow-2xl backdrop-blur-sm">
          <h2 className="text-xl font-semibold mb-6 flex items-center">
            <svg
              className="w-5 h-5 mr-2 text-emerald-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            Live Refinery Core Stream
          </h2>
          <div className="space-y-4 font-mono text-sm">
            <LogEntry
              time="10:42:01"
              type="UPSERT"
              message="Processed 1000 CDC vectors to disk."
            />
            <LogEntry
              time="10:42:05"
              type="MASK"
              message="ShieldScrubber intercepted 431 SSN patterns."
            />
            <LogEntry
              time="10:42:15"
              type="TOMBSTONE"
              message="Event Flattener generated PRUNE flag for User URN 909."
              isWarning
            />
            <LogEntry
              time="10:42:16"
              type="PURGE"
              message="Qdrant pruned 1 legacy vector array."
              isSuccess
            />
          </div>
        </section>
      </main>
    </div>
  );
}

function MetricCard({ title, value, trend, highlight = "emerald" }: any) {
  const colors: any = {
    emerald: "text-emerald-400",
    cyan: "text-cyan-400",
    rose: "text-rose-400",
  };

  return (
    <div className="border border-slate-800 rounded-xl bg-slate-900/50 p-6 flex flex-col hover:border-slate-700 transition-colors duration-300">
      <span className="text-slate-400 text-sm font-medium">{title}</span>
      <span className={`text-5xl font-bold mt-2 ${colors[highlight]}`}>
        {value}
      </span>
      <span className="text-xs text-slate-500 mt-auto pt-4">{trend}</span>
    </div>
  );
}

function LogEntry({
  time,
  type,
  message,
  isWarning = false,
  isSuccess = false,
}: any) {
  let badgeColor = "bg-slate-800 text-slate-300";
  if (isWarning)
    badgeColor = "bg-rose-900/50 text-rose-400 border border-rose-800/50";
  if (isSuccess)
    badgeColor =
      "bg-emerald-900/50 text-emerald-400 border border-emerald-800/50";

  return (
    <div className="flex items-start space-x-4 p-3 rounded bg-slate-950/50 hover:bg-slate-950 transition-colors duration-200">
      <span className="text-slate-600 shrink-0">[{time}]</span>
      <span
        className={`px-2 py-0.5 rounded text-xs font-semibold shrink-0 w-24 text-center ${badgeColor}`}
      >
        {type}
      </span>
      <span className="text-slate-300">{message}</span>
    </div>
  );
}
