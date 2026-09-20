"""Graph RAG query routes."""

from fastapi import APIRouter, Depends, Header
from typing import List, Optional
from pydantic import BaseModel
from interfaces import GraphStore

router = APIRouter()

class GraphRAGRequest(BaseModel):
    query: str
    target_nodes: Optional[List[str]] = None
    depth: int = 2

class GraphRAGResponse(BaseModel):
    success: bool
    nodes_traversed: int
    edges_found: List[dict]
    context_payload: str

def get_graph_store() -> GraphStore:
    """Dependency injection for graph store (will be injected by main.py)."""
    from main import _graph_store
    return _graph_store

@router.post("/internal/graph-rag", response_model=GraphRAGResponse)
async def graph_rag(
    request: GraphRAGRequest,
    x_tenant_id: Optional[str] = Header(None),
    graph_store: GraphStore = Depends(get_graph_store)
):
    """Execute a Graph-RAG traversal query."""
    try:
        # Query the knowledge graph
        edges = graph_store.query_edges(depth=request.depth)

        # Filter edges if target nodes specified
        if request.target_nodes:
            edges = [
                e for e in edges
                if any(target in e.get("source", "") or target in e.get("target", "")
                       for target in request.target_nodes)
            ]

        # Build context payload from edges
        context_lines = [f"{e.get('source')} -[{e.get('relation')}]-> {e.get('target')}" for e in edges]
        context_payload = "\n".join(context_lines) if context_lines else "No edges found matching query."

        return GraphRAGResponse(
            success=True,
            nodes_traversed=len(edges),
            edges_found=edges,
            context_payload=context_payload
        )
    except Exception as e:
        print(f"[Graph Routes] Error in graph-rag: {e}")
        return GraphRAGResponse(
            success=False,
            nodes_traversed=0,
            edges_found=[],
            context_payload=f"Error: {str(e)}"
        )
