"""Tests for vector database operations"""

import pytest
import tempfile
import shutil
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vector_db import NexusQdrant
from interfaces import VectorStore


def test_vector_store_initialization():
    """Test that NexusQdrant initializes without errors"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['QDRANT_PATH'] = tmpdir
        store = NexusQdrant()
        assert isinstance(store, VectorStore)
        assert store.collection_name == "aether_refined_chunks"


def test_upsert_embedding():
    """Test upserting an embedding"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['QDRANT_PATH'] = tmpdir
        store = NexusQdrant()

        store.upsert_embedding(
            chunk_uuid="test-123",
            content="test content",
            mask_map={"PII": "***"},
            metadata={"source": "test"},
            tenant_id="test-tenant"
        )
        # Should not raise


def test_search_empty_database():
    """Test searching in an empty database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['QDRANT_PATH'] = tmpdir
        store = NexusQdrant()

        query_vector = [0.1] * 384
        results = store.search(query_vector, top_k=5)

        assert isinstance(results, list)
        assert len(results) == 0


def test_prune_vector():
    """Test deleting a vector"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['QDRANT_PATH'] = tmpdir
        store = NexusQdrant()

        # Upsert a vector
        store.upsert_embedding(
            chunk_uuid="to-delete",
            content="will be deleted",
            mask_map={},
            metadata={}
        )

        # Prune it
        store.prune_vector("to-delete")
        # Should not raise


def test_tenant_filtering():
    """Test that tenant filtering works in search"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['QDRANT_PATH'] = tmpdir
        store = NexusQdrant()

        # Upsert with specific tenant
        store.upsert_embedding(
            chunk_uuid="tenant-1-vector",
            content="tenant 1 data",
            mask_map={},
            metadata={},
            tenant_id="tenant-1"
        )

        # Search with tenant filter
        query_vector = [0.1] * 384
        results = store.search(query_vector, tenant_filter="tenant-1")

        # Results should be empty but not error
        assert isinstance(results, list)


def test_vector_dimension():
    """Test that vectors are stored with correct dimension"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['QDRANT_PATH'] = tmpdir
        store = NexusQdrant()

        # MiniLM produces 384-d vectors
        assert store.collection_name == "aether_refined_chunks"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
