"""
Union-Find (Disjoint Set Union) — core data structure for entity resolution.

Two key optimizations make all operations near-constant O(α(n)):
  1. Path compression in find() — flattens tree on every lookup
  2. Union by rank — always attaches the shallower tree under the deeper one

Additionally tracks:
  - Cluster sizes (without traversal)
  - Merge evidence / provenance (which matching rule caused each merge)
  - Full serialization to/from JSON for persistence between sync runs
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Set, List, Tuple, Optional, Any


class UnionFind:
    """
    Efficient Disjoint Set Union for entity resolution.

    Each record starts as its own singleton cluster. As matching
    strategies identify equivalent records, union() merges them
    into the same cluster. find() returns the canonical representative
    with path compression.
    """

    def __init__(self):
        self._parent: Dict[str, str] = {}
        self._rank: Dict[str, int] = {}
        self._size: Dict[str, int] = {}
        self._evidence: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # Maps: "child_root" → list of evidence dicts for why it was merged

    # ── Core Operations ───────────────────────────────────────────────

    def add(self, record_id: str) -> None:
        """
        Register a new record as its own entity.
        Idempotent — safe to call multiple times for the same ID.
        """
        if record_id not in self._parent:
            self._parent[record_id] = record_id
            self._rank[record_id] = 0
            self._size[record_id] = 1

    def find(self, x: str) -> str:
        """
        Find the canonical representative of x's cluster.

        Uses path compression: every node on the path from x to the
        root is re-pointed directly to the root, flattening the tree
        for future lookups.

        Raises KeyError if x has not been added.
        """
        if x not in self._parent:
            raise KeyError(f"Record '{x}' not registered. Call add() first.")

        # Iterative path compression (avoids stack overflow on deep trees)
        root = x
        while self._parent[root] != root:
            root = self._parent[root]

        # Compress: point every node on the path directly to root
        while self._parent[x] != root:
            next_parent = self._parent[x]
            self._parent[x] = root
            x = next_parent

        return root

    def union(
        self,
        x: str,
        y: str,
        evidence: Optional[List[str]] = None,
    ) -> bool:
        """
        Merge the clusters containing x and y.

        Uses union by rank to keep trees shallow.

        Args:
            x: First record ID.
            y: Second record ID.
            evidence: List of evidence strings explaining why these
                      records are the same entity (for audit trail).

        Returns:
            True if a merge happened (they were in different clusters).
            False if they were already in the same cluster.
        """
        # Auto-add if not present
        self.add(x)
        self.add(y)

        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False  # Already same entity

        # Union by rank — attach shallower tree under deeper one
        if self._rank[root_x] < self._rank[root_y]:
            root_x, root_y = root_y, root_x

        self._parent[root_y] = root_x
        self._size[root_x] += self._size[root_y]

        if self._rank[root_x] == self._rank[root_y]:
            self._rank[root_x] += 1

        # Track provenance
        if evidence:
            self._evidence[root_y].append({
                "merged_into": root_x,
                "evidence": evidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return True

    def connected(self, x: str, y: str) -> bool:
        """Check if x and y are in the same cluster."""
        return self.find(x) == self.find(y)

    # ── Cluster Queries ───────────────────────────────────────────────

    def get_cluster(self, x: str) -> Set[str]:
        """Return all record IDs in the same cluster as x."""
        root = self.find(x)
        return {r for r in self._parent if self.find(r) == root}

    def cluster_size(self, x: str) -> int:
        """Return the size of x's cluster in O(1)."""
        return self._size[self.find(x)]

    def all_clusters(self) -> List[Set[str]]:
        """Return all entity clusters as a list of sets."""
        groups: Dict[str, Set[str]] = defaultdict(set)
        for record_id in self._parent:
            groups[self.find(record_id)].add(record_id)
        return list(groups.values())

    def num_clusters(self) -> int:
        """Return the number of distinct clusters."""
        roots = {self.find(r) for r in self._parent}
        return len(roots)

    def num_records(self) -> int:
        """Return total number of registered records."""
        return len(self._parent)

    def get_evidence(self, x: str) -> List[Dict[str, Any]]:
        """Return all merge evidence involving record x or its ancestors."""
        # Collect evidence from x and all nodes that were merged
        all_evidence = []
        for merged_root, ev_list in self._evidence.items():
            for ev in ev_list:
                all_evidence.append({
                    "merged_node": merged_root,
                    **ev,
                })
        return all_evidence

    def get_cluster_evidence(self, x: str) -> List[Dict[str, Any]]:
        """Return evidence for all merges within x's cluster."""
        cluster = self.get_cluster(x)
        result = []
        for node in cluster:
            if node in self._evidence:
                result.extend(self._evidence[node])
        return result

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Union-Find state to a JSON-compatible dict."""
        return {
            "parent": dict(self._parent),
            "rank": dict(self._rank),
            "size": dict(self._size),
            "evidence": {k: v for k, v in self._evidence.items()},
            "num_records": self.num_records(),
            "num_clusters": self.num_clusters(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnionFind":
        """Deserialize a Union-Find from a dict."""
        uf = cls()
        uf._parent = dict(data["parent"])
        uf._rank = dict(data["rank"])
        uf._size = dict(data["size"])
        uf._evidence = defaultdict(list, {
            k: v for k, v in data.get("evidence", {}).items()
        })
        return uf

    @classmethod
    def from_json(cls, json_str: str) -> "UnionFind":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save_to_file(self, path: str) -> None:
        """Persist to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: str) -> "UnionFind":
        """Load from a JSON file."""
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))

    def __repr__(self) -> str:
        return (
            f"UnionFind(records={self.num_records()}, "
            f"clusters={self.num_clusters()})"
        )
