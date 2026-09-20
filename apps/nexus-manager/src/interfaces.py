from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class VectorStore(ABC):
    @abstractmethod
    def upsert_embedding(self, chunk_uuid: str, content: str, mask_map: Dict[str, str], metadata: Dict[str, Any], tenant_id: Optional[str] = None) -> None:
        """Upsert a semantic chunk into the vector database."""
        pass

    @abstractmethod
    def prune_vector(self, chunk_uuid: str) -> None:
        """Prune an invalid or tombstoned chunk from the vector database."""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 10, tenant_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors in the database.

        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            tenant_filter: Optional tenant_id to filter results by

        Returns:
            List of matching points with id, score, and payload
        """
        pass

class GraphStore(ABC):
    @abstractmethod
    def generate_edges(self, source_urn: str, metadata: Dict[str, Any], parsed_content: str) -> None:
        """Extract and generate edges into the Knowledge Graph."""
        pass

    @abstractmethod
    def query_edges(self, source_urn: Optional[str] = None, depth: int = 2) -> List[Dict[str, Any]]:
        """Query the knowledge graph for edges.

        Args:
            source_urn: Optional source to filter from
            depth: Traversal depth

        Returns:
            List of edges in the graph
        """
        pass
