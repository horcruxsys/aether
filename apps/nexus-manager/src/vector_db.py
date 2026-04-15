from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import random

class NexusQdrant:
    def __init__(self):
        # Using memory storage for developmental speed without needing Docker.
        self.client = QdrantClient(":memory:")
        self.collection_name = "aether_refined_chunks"
        
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )

    def upsert_embedding(self, chunk_uuid: str, content: str, mask_map: dict, metadata: dict):
        # Generate the Mock 1024-d Vector array mimicking sentence-transformers
        mock_embedding = [random.uniform(-1.0, 1.0) for _ in range(1024)]
        
        # We explicitly cast UUID strings into integers as an example, but Qdrant natively supports string UUID payload.
        # To make it fully compliant with strict Qdrant format natively, we supply UUID string as the ID.
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=chunk_uuid,
                    vector=mock_embedding,
                    payload={
                        "original_content": content,
                        "metadata": metadata,
                        "mask_map": mask_map
                    }
                )
            ]
        )
        print(f"[Qdrant] 🟢 Upserted 1024-d Semantic Vector for chunk: {chunk_uuid}")
        
    def prune_vector(self, chunk_uuid: str):
        # Gracefully handle Tombstone records by explicitly deleting matching vectors
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[chunk_uuid]  # Provide UUID directly in selector
        )
        print(f"[Qdrant] ☠️ TOMBSTONE Intercepted! Pruned vector: {chunk_uuid} to prevent LLM hallucination.")
