"""
Schema Graph — weighted alignment graph and concept cluster extraction.

Takes LSH candidate pairs and builds a networkx graph where:
  - Nodes = columns (across all databases)
  - Edges = alignment confidence (combined MinHash + name similarity)
  - Connected components = "concept clusters" (semantically equivalent columns)

The output is a JSON-serializable schema map that downstream components
(Entity Resolution via Union-Find — ISSUE-003) consume directly.
"""
import json
from typing import List, Set, Dict, Any, Optional
from .models import ColumnProfile, AlignmentCandidate

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


def build_schema_graph(
    candidates: List[AlignmentCandidate],
    profiles: Dict[str, ColumnProfile],
    threshold: float = 0.5,
) -> "nx.Graph":
    """
    Build a weighted schema alignment graph from LSH candidate pairs.

    Args:
        candidates: List of alignment candidates from LSH.
        profiles: Dict of column key → ColumnProfile.
        threshold: Minimum combined score to create an edge.

    Returns:
        networkx.Graph with columns as nodes and similarity as edge weights.
    """
    if not HAS_NETWORKX:
        raise ImportError(
            "networkx is required for schema graph construction. "
            "Install with: pip install networkx"
        )

    G = nx.Graph()

    # Add all profiled columns as nodes
    for key, profile in profiles.items():
        G.add_node(key, **{
            "db_id": profile.db_id,
            "table": profile.table,
            "column": profile.column,
            "dtype": profile.dtype,
        })

    # Add edges for alignments above threshold
    for candidate in candidates:
        if candidate.combined_score >= threshold:
            G.add_edge(
                candidate.source_key,
                candidate.target_key,
                weight=candidate.combined_score,
                value_similarity=candidate.value_similarity,
                name_similarity=candidate.name_similarity,
            )

    return G


def extract_concept_clusters(G: "nx.Graph") -> List[Set[str]]:
    """
    Extract concept clusters as connected components of the schema graph.

    Each connected component represents a set of columns across databases
    that refer to the same semantic concept.

    Returns:
        List of sets, where each set contains column keys.
    """
    if not HAS_NETWORKX:
        raise ImportError("networkx required")

    return [comp for comp in nx.connected_components(G) if len(comp) > 1]


def serialize_clusters(
    clusters: List[Set[str]],
    profiles: Dict[str, ColumnProfile],
    G: Optional["nx.Graph"] = None,
) -> Dict[str, Any]:
    """
    Serialize concept clusters to a JSON-compatible schema map.

    Produces the output format consumed by downstream components
    (Entity Resolution, Vector DB metadata, Schema Registry).

    Args:
        clusters: Connected components from extract_concept_clusters.
        profiles: Dict of column key → ColumnProfile.
        G: Optional graph for extracting edge weights (confidence).

    Returns:
        JSON-serializable dict with concept clusters.
    """
    result_clusters = []

    for cluster in clusters:
        members = []
        total_confidence = 0.0
        edge_count = 0

        for key in sorted(cluster):
            profile = profiles.get(key)
            if profile:
                members.append({
                    "db": profile.db_id,
                    "table": profile.table,
                    "column": profile.column,
                    "dtype": profile.dtype,
                })

        # Compute average edge weight as cluster confidence
        if G is not None:
            sorted_keys = sorted(cluster)
            for i, k1 in enumerate(sorted_keys):
                for k2 in sorted_keys[i + 1:]:
                    if G.has_edge(k1, k2):
                        total_confidence += G[k1][k2]["weight"]
                        edge_count += 1

        confidence = (total_confidence / edge_count) if edge_count > 0 else 0.0

        # Pick canonical name: most common token across member column names
        all_tokens: Dict[str, int] = {}
        for key in cluster:
            p = profiles.get(key)
            if p:
                for token in p.name_tokens:
                    all_tokens[token] = all_tokens.get(token, 0) + 1

        canonical = max(all_tokens, key=all_tokens.get) if all_tokens else "unknown"
        # Try to build a compound name from the top tokens
        sorted_tokens = sorted(all_tokens.items(), key=lambda x: -x[1])
        if len(sorted_tokens) >= 2:
            # Take the two most common tokens
            canonical = "_".join(t[0] for t in sorted_tokens[:2])

        result_clusters.append({
            "canonical_name": canonical,
            "confidence": round(confidence, 4),
            "member_count": len(members),
            "members": members,
        })

    # Sort by confidence descending
    result_clusters.sort(key=lambda c: -c["confidence"])

    return {
        "concept_clusters": result_clusters,
        "total_clusters": len(result_clusters),
    }


def to_json(schema_map: Dict[str, Any], indent: int = 2) -> str:
    """Serialize the schema map to a JSON string."""
    return json.dumps(schema_map, indent=indent)
