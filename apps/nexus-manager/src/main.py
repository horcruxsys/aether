from fastapi import FastAPI
import threading
import time
import os
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fastavro

from vector_db import NexusQdrant
from intelligence.graph import KnowledgeGraph

from interfaces import VectorStore, GraphStore

DUMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.cache/aether-dump"))

class AvroHandler(FileSystemEventHandler):
    def __init__(self, vector_store: VectorStore, graph_store: GraphStore):
        self.vector_store = vector_store
        self.graph_store = graph_store

    def process_file(self, file_path):
        if not file_path.endswith('.avro'):
            return
        time.sleep(0.5) # Wait for write completion (in a real system we'd use atomic renames)
        print(f"\n[Nexus Orchestrator] Detected new Avro payload: {file_path}")
        
        try:
            with open(file_path, 'rb') as fo:
                reader = fastavro.reader(fo)
                for record in reader:
                    chunk_uuid = record.get('uuid')
                    content = record.get('content')
                    mask_map = record.get('pii_mask_map')
                    metadata = record.get('metadata')
                    source_urn = record.get('source_urn', 'unknown')

                    print("-" * 50)
                    
                    if content == "TOMBSTONE_PRUNE_VECTOR":
                        self.vector_store.prune_vector(chunk_uuid)
                    else:
                        print(f"UUID: {chunk_uuid}")
                        print(f"Content: {content}")
                        print(f"Mask Map: {mask_map}")
                        
                        # GraphRAG Edge Extraction
                        self.graph_store.generate_edges(source_urn, metadata, content)
                        
                        # Semantic Vector Clustering
                        self.vector_store.upsert_embedding(chunk_uuid, content, mask_map, metadata)
                        
        except Exception as e:
            print(f"[Nexus Orchestrator] Error parsing Avro: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

def start_watcher():
    os.makedirs(DUMP_DIR, exist_ok=True)
    print(f"Starting Avro watcher on {DUMP_DIR}")
    
    # Injecting dependencies purely matching interface definitions
    qdrant = NexusQdrant()
    graph = KnowledgeGraph()
    event_handler = AvroHandler(vector_store=qdrant, graph_store=graph)
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

@app.on_event("startup")
def startup_event():
    # Run the watcher in a background thread
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()

@app.get("/health")
def health():
    return {
        "status": "watching_avro",
        "dump_dir": DUMP_DIR
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
