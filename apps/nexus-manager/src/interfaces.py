from abc import ABC, abstractmethod
from typing import Dict, Any

class VectorStore(ABC):
    @abstractmethod
    def upsert_embedding(self, chunk_uuid: str, content: str, mask_map: Dict[str, str], metadata: Dict[str, Any]) -> None:
        """Upsert a semantic chunk into the vector database."""
        pass

    @abstractmethod
    def prune_vector(self, chunk_uuid: str) -> None:
        """Prune an invalid or tombstoned chunk from the vector database."""
        pass

class GraphStore(ABC):
    @abstractmethod
    def generate_edges(self, source_urn: str, metadata: Dict[str, Any], parsed_content: str) -> None:
        """Extract and generate edges into the Knowledge Graph."""
        pass
