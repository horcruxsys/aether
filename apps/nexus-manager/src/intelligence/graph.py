from interfaces import GraphStore
from typing import Dict, Any, List, Optional
import json
import os

class KnowledgeGraph(GraphStore):
    def __init__(self):
        """Initialize the Knowledge Graph with persistent storage."""
        self.edges: List[Dict[str, Any]] = []
        self.storage_path = os.path.join(".cache", "knowledge_graph_edges.json")
        os.makedirs(".cache", exist_ok=True)
        self._load_edges()

    def _load_edges(self):
        """Load existing edges from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.edges = json.load(f)
                print(f"[GraphStore] Loaded {len(self.edges)} existing edges")
            except Exception as e:
                print(f"[GraphStore] Warning loading edges: {e}")
                self.edges = []

    def _save_edges(self):
        """Persist edges to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.edges, f, indent=2)
        except Exception as e:
            print(f"[GraphStore] Warning saving edges: {e}")

    def generate_edges(self, source_urn: str, metadata: Dict[str, Any], parsed_content: str) -> None:
        """
        Extract and persist edges. In production, this would use LLM parsing or NLP
        for subject-verb-object relations. For MVP, we extract based on metadata.
        """
        job_type = metadata.get('job', 'unknown_job')

        # Generate edges based on metadata
        edges = [
            {
                "id": f"{source_urn}:{job_type}:generated_by",
                "source": f"Document:{source_urn}",
                "relation": "GENERATED_BY",
                "target": f"Process:{job_type}"
            }
        ]

        # Add to in-memory store and persist
        for edge in edges:
            if edge not in self.edges:
                self.edges.append(edge)
                print(f"[GraphRAG] 🔗 Generated Edge: {edge['source']} -[{edge['relation']}]-> {edge['target']}")

        self._save_edges()

    def query_edges(self, source_urn: Optional[str] = None, depth: int = 2) -> List[Dict[str, Any]]:
        """Query edges, optionally filtered by source_urn."""
        if source_urn:
            filtered = [e for e in self.edges if source_urn in e.get("source", "")]
            return filtered[:depth * 10]  # Simple depth limiting
        return self.edges[:depth * 10]
