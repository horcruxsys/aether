"""Tests for knowledge graph operations"""

import pytest
import tempfile
import os
import sys
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from intelligence.graph import KnowledgeGraph
from interfaces import GraphStore


def test_graph_initialization():
    """Test that KnowledgeGraph initializes without errors"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to tmpdir so .cache is created there
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            graph = KnowledgeGraph()
            assert isinstance(graph, GraphStore)
        finally:
            os.chdir(old_cwd)


def test_generate_edges():
    """Test edge generation and persistence"""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            graph = KnowledgeGraph()

            graph.generate_edges(
                source_urn="test://source",
                metadata={"job": "test_job"},
                parsed_content="test content"
            )

            # Verify edge was stored
            edges = graph.query_edges(source_urn="test://source")
            assert len(edges) > 0
            assert any("test://source" in e.get("source", "") for e in edges)
        finally:
            os.chdir(old_cwd)


def test_query_edges():
    """Test edge querying"""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            graph = KnowledgeGraph()

            # Generate multiple edges
            for i in range(3):
                graph.generate_edges(
                    source_urn=f"test://source-{i}",
                    metadata={"job": f"job_{i}"},
                    parsed_content=f"content {i}"
                )

            # Query all edges
            all_edges = graph.query_edges()
            assert len(all_edges) >= 3

            # Query filtered edges
            filtered = graph.query_edges(source_urn="test://source-0")
            assert len(filtered) > 0
        finally:
            os.chdir(old_cwd)


def test_edge_persistence():
    """Test that edges are persisted to disk"""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create graph and add edge
            graph1 = KnowledgeGraph()
            graph1.generate_edges(
                source_urn="persist://test",
                metadata={"job": "test"},
                parsed_content="test"
            )

            # Create new graph instance
            graph2 = KnowledgeGraph()
            edges = graph2.query_edges()

            # Should still have the edge from the first instance
            assert len(edges) > 0
            assert any("persist://test" in e.get("source", "") for e in edges)
        finally:
            os.chdir(old_cwd)


def test_edge_structure():
    """Test that generated edges have correct structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            graph = KnowledgeGraph()

            graph.generate_edges(
                source_urn="test://doc",
                metadata={"job": "ingest"},
                parsed_content="data"
            )

            edges = graph.query_edges()
            assert len(edges) > 0

            edge = edges[0]
            assert "id" in edge
            assert "source" in edge
            assert "relation" in edge
            assert "target" in edge
        finally:
            os.chdir(old_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
