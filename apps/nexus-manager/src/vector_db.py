from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
import os
from typing import Dict, Any, List, Optional
from interfaces import VectorStore
from tenant_isolation import TenantIsolator
import embedding as embedding_module

class NexusQdrant(VectorStore):
    def __init__(self):
        """Initialize Qdrant client in dual-mode: embedded on-disk for dev, dockerized for prod."""
        self.collection_name = "aether_refined_chunks"
        self.tenant_isolator = TenantIsolator()

        # Dual-mode: check for QDRANT_URL (docker) first, fall back to embedded on-disk
        qdrant_url = os.environ.get("QDRANT_URL")
        qdrant_path = os.environ.get("QDRANT_PATH", ".cache/qdrant-storage")

        if qdrant_url:
            print(f"[Qdrant] Connecting to remote Qdrant at {qdrant_url}")
            self.client = QdrantClient(url=qdrant_url)
        else:
            print(f"[Qdrant] Using embedded on-disk storage at {qdrant_path}")
            self.client = QdrantClient(path=qdrant_path)

        # Ensure collection exists with real 384-d vectors (MiniLM output dimension)
        try:
            self.client.get_collection(self.collection_name)
            print(f"[Qdrant] Collection '{self.collection_name}' already exists")
        except:
            print(f"[Qdrant] Creating new collection '{self.collection_name}' with 384-d vectors")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def upsert_embedding(self, chunk_uuid: str, content: str, mask_map: dict, metadata: dict, tenant_id: Optional[str] = None) -> None:
        """Upsert a real embedding generated from content."""
        try:
            # Generate real embedding from content
            real_embedding = embedding_module.embed(content)

            payload = {
                "original_content": content,
                "metadata": metadata,
                "mask_map": mask_map,
                "tenant_id": tenant_id or "default"
            }

            # Validate tenant context if provided
            if tenant_id:
                self.tenant_isolator.assert_validity({"tenant_id": tenant_id})

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=chunk_uuid,
                        vector=real_embedding,
                        payload=payload
                    )
                ]
            )
            print(f"[Qdrant] 🟢 Upserted real 384-d semantic vector for chunk: {chunk_uuid} (tenant: {tenant_id or 'default'})")
        except Exception as e:
            print(f"[Qdrant] ❌ Error upserting embedding for {chunk_uuid}: {e}")
            raise

    def prune_vector(self, chunk_uuid: str) -> None:
        """Gracefully handle Tombstone records by deleting matching vectors."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[chunk_uuid]
            )
            print(f"[Qdrant] ☠️ TOMBSTONE Intercepted! Pruned vector: {chunk_uuid}")
        except Exception as e:
            print(f"[Qdrant] ⚠️ Warning pruning {chunk_uuid}: {e}")

    def search(self, query_vector: List[float], top_k: int = 10, tenant_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional tenant filtering."""
        try:
            # Build filter for tenant isolation if provided
            query_filter = None
            if tenant_filter:
                self.tenant_isolator.assert_validity({"tenant_id": tenant_filter})
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="tenant_id",
                            match=MatchValue(value=tenant_filter)
                        )
                    ]
                )

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )

            # Transform results to a clean format
            matches = []
            for result in results:
                matches.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("original_content"),
                    "metadata": result.payload.get("metadata"),
                    "mask_map": result.payload.get("mask_map"),
                    "tenant_id": result.payload.get("tenant_id")
                })

            print(f"[Qdrant] 🔍 Found {len(matches)} results (tenant: {tenant_filter or 'any'})")
            return matches
        except Exception as e:
            print(f"[Qdrant] ❌ Error searching: {e}")
            return []
