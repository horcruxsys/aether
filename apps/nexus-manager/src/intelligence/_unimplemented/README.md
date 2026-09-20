# Unimplemented Intelligence Modules

This directory contains modules that are **not yet implemented for production use**:

- **orchestrator.py** — LangGraph agentic workflow. Requires real LLM integration and tool execution.
- **swarm.py** — Multi-agent critic/actor pattern. Requires real LLM backends.
- **tools.py** — Tool definitions for agent use. Stubs only, no real implementation.

These modules have `langchain` and `langgraph` dependencies that are currently **broken** (declared in `pyproject.toml` but not in `uv.lock`).

## Status

These are deferred to **Phase 2: Autonomous Intelligence** in the project roadmap, when the agentic orchestration layer will be properly designed and implemented.

Until then, only `drift_detector.py` in the parent `intelligence/` directory is wired into the live ingestion pipeline.
