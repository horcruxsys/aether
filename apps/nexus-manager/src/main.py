from fastapi import FastAPI
import threading
import time
import os
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fastavro
from uuid import uuid4

from vector_db import NexusQdrant
from intelligence.graph import KnowledgeGraph
from interfaces import VectorStore, GraphStore
from routes import vector, graph, jobs

DUMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.cache/aether-dump"))

# Global instances shared between watcher and HTTP handlers
_vector_store: VectorStore = None
_graph_store: GraphStore = None
_active_jobs: dict = {}

class AvroHandler(FileSystemEventHandler):
    def __init__(self, vector_store: VectorStore, graph_store: GraphStore):
        self.vector_store = vector_store
        self.graph_store = graph_store

    def process_file(self, file_path):
        if not file_path.endswith('.avro'):
            return
        time.sleep(0.5)  # Wait for write completion (in a real system we'd use atomic renames)
        print(f"\n[Nexus Orchestrator] Detected new Avro payload: {file_path}")

        # Create a job tracking entry
        job_id = str(uuid4())
        _active_jobs[job_id] = {
            "source_urn": "unknown",
            "status": "RUNNING",
            "processed_count": 0,
            "pii_masked_count": 0,
            "timestamp": time.time()
        }

        try:
            with open(file_path, 'rb') as fo:
                reader = fastavro.reader(fo)
                processed = 0
                for record in reader:
                    chunk_uuid = record.get('uuid')
                    content = record.get('content')
                    mask_map = record.get('pii_mask_map', {})
                    metadata = record.get('metadata', {})
                    source_urn = record.get('source_urn', 'unknown')
                    tenant_id = record.get('tenant_id', 'default')

                    print("-" * 50)

                    if content == "TOMBSTONE_PRUNE_VECTOR":
                        self.vector_store.prune_vector(chunk_uuid)
                    else:
                        print(f"UUID: {chunk_uuid}")
                        print(f"Content: {content[:100]}..." if len(content) > 100 else f"Content: {content}")
                        print(f"Mask Map: {mask_map}")

                        # GraphRAG Edge Extraction
                        self.graph_store.generate_edges(source_urn, metadata, content)

                        # Semantic Vector Clustering (with real embeddings)
                        self.vector_store.upsert_embedding(
                            chunk_uuid,
                            content,
                            mask_map,
                            metadata,
                            tenant_id=tenant_id
                        )

                        processed += 1
                        _active_jobs[job_id]["processed_count"] = processed
                        _active_jobs[job_id]["pii_masked_count"] = sum(len(m) for m in [mask_map])
                        _active_jobs[job_id]["source_urn"] = source_urn

            # Mark job as completed
            _active_jobs[job_id]["status"] = "COMPLETED"
            print(f"\n[Nexus Orchestrator] ✅ Processed {processed} chunks from {file_path}")

        except Exception as e:
            print(f"[Nexus Orchestrator] Error parsing Avro: {e}")
            _active_jobs[job_id]["status"] = "FAILED"
        finally:
            # Keep job in history for a bit before removing
            def cleanup_job():
                time.sleep(60)
                _active_jobs.pop(job_id, None)
            threading.Thread(target=cleanup_job, daemon=True).start()

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

def start_watcher():
    os.makedirs(DUMP_DIR, exist_ok=True)
    print(f"Starting Avro watcher on {DUMP_DIR}")

    # Inject dependencies purely matching interface definitions
    event_handler = AvroHandler(
        vector_store=_vector_store,
        graph_store=_graph_store
    )
    observer = Observer()
    observer.schedule(event_handler, DUMP_DIR, recursive=False)
    observer.start()

    # Process existing files on startup
    for file in glob.glob(f"{DUMP_DIR}/*.avro"):
        event_handler.process_file(file)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

app = FastAPI(title="Nexus Manager MVP")

# Include the new route routers
app.include_router(vector.router)
app.include_router(graph.router)
app.include_router(jobs.router)

@app.on_event("startup")
def startup_event():
    global _vector_store, _graph_store

    # Initialize shared instances
    _vector_store = NexusQdrant()
    _graph_store = KnowledgeGraph()

    print("[Nexus Manager] ✅ Initialized shared services")
    print(f"[Nexus Manager] Vector Store: {type(_vector_store).__name__}")
    print(f"[Nexus Manager] Graph Store: {type(_graph_store).__name__}")

    # Run the watcher in a background thread
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

@app.get("/health")
def health():
    return {
        "status": "operational",
        "dump_dir": DUMP_DIR,
        "vector_store": "qdrant_embedded" if not os.environ.get("QDRANT_URL") else "qdrant_remote",
        "active_jobs": len(_active_jobs)
    }

@app.get("/version")
def version():
    return {
        "version": "1.0.0",
        "name": "Nexus Manager MVP",
        "status": "production-ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
