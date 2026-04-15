# nexus-manager

**Mission:** Orchestrating the "Brain"—the hybrid Vector-Graph storage.

* **Tech Stack:** Python (FastAPI), PyTorch (for local embedding), SQLModel.
* **Core Logic:**
    * **GraphRAG Engine:** Automatically maps relational foreign keys into Graph edges while storing the text as Vectors.
    * **Sync Monitor:** Watches for "drift" between the legacy RDBMS and the Aether Vector store.

> Nexus is the system of record for the AI era. By combining the semantic power of vectors with the deterministic logic of Knowledge Graphs, it eliminates hallucinations and provides "Reasoning-as-a-Service."
