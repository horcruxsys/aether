"""Vector search and projection routes."""

from fastapi import APIRouter, Depends, Header
from typing import List, Optional
from pydantic import BaseModel
import embedding as embedding_module
from interfaces import VectorStore

router = APIRouter()

class VectorProjectionRequest(BaseModel):
    embeddings: Optional[List[float]] = None
    text: Optional[str] = None
    threshold: float = 0.85
    top_k: int = 10

class VectorProjectionResponse(BaseModel):
    success: bool
    matched_uuids: List[str]
    matches: List[dict]
    confidence_score: float

class DatasetMetadataResponse(BaseModel):
    urn: str
    pii_count: int
    chunk_count: int
    tombstone_count: int

def get_vector_store() -> VectorStore:
    """Dependency injection for vector store (will be injected by main.py)."""
    from main import _vector_store
    return _vector_store

@router.post("/internal/vector-projection", response_model=VectorProjectionResponse)
async def vector_projection(
    request: VectorProjectionRequest,
    x_tenant_id: Optional[str] = Header(None),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """Search for vectors in the database by embedding or text."""
    try:
        # Generate embedding from text if provided, otherwise use provided embeddings
        if request.text:
            query_vector = embedding_module.embed(request.text)
        elif request.embeddings:
            query_vector = request.embeddings
        else:
            return VectorProjectionResponse(
                success=False,
                matched_uuids=[],
                matches=[],
                confidence_score=0.0
            )

        # Search with optional tenant filtering
        results = vector_store.search(
            query_vector=query_vector,
            top_k=request.top_k,
            tenant_filter=x_tenant_id
        )

        # Filter by threshold and extract UUIDs
        matched = [r for r in results if r.get("score", 0) >= request.threshold]
        matched_uuids = [r["id"] for r in matched]

        avg_confidence = sum(r.get("score", 0) for r in matched) / len(matched) if matched else 0.0

        return VectorProjectionResponse(
            success=True,
            matched_uuids=matched_uuids,
            matches=matched,
            confidence_score=avg_confidence
        )
    except Exception as e:
        print(f"[Vector Routes] Error in vector-projection: {e}")
        return VectorProjectionResponse(
            success=False,
            matched_uuids=[],
            matches=[],
            confidence_score=0.0
        )

@router.get("/internal/datasets/{urn}", response_model=DatasetMetadataResponse)
async def get_dataset_metadata(
    urn: str,
    x_tenant_id: Optional[str] = Header(None),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """Get metadata about a dataset by URN."""
    try:
        # Search for all chunks from this source
        # We use an empty/zero vector just to get all results if Qdrant supports it
        # For MVP, return mock counts; in production, aggregate from actual data
        results = vector_store.search(
            query_vector=[0.0] * 384,  # Dummy zero vector
            top_k=1000,
            tenant_filter=x_tenant_id
        )

        # Filter to this URN's chunks (in metadata)
        matching = [r for r in results if r.get("metadata", {}).get("source_urn") == urn]

        pii_count = sum(len(r.get("mask_map", {})) for r in matching)

        return DatasetMetadataResponse(
            urn=urn,
            pii_count=pii_count,
            chunk_count=len(matching),
            tombstone_count=0
        )
    except Exception as e:
        print(f"[Vector Routes] Error fetching dataset metadata: {e}")
        return DatasetMetadataResponse(
            urn=urn,
            pii_count=0,
            chunk_count=0,
            tombstone_count=0
        )
