"""
MerkleTreeStore — SQLite-backed snapshot persistence.

Why SQLite:
  - Zero external dependencies (ships with Python stdlib)
  - ACID transactions for safe concurrent snapshot writes
  - Single-file database, easy to backup / ship / embed
  - Supports JSON1 extension natively for tree serialization
  - Perfect for local metadata stores; scales to terabytes on disk
"""
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from .models import MerkleNode


_SCHEMA = """
CREATE TABLE IF NOT EXISTS merkle_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id   TEXT    NOT NULL,
    root_hash       TEXT    NOT NULL,
    tree_json       TEXT    NOT NULL,
    record_count    INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL,
    is_latest       INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_conn_latest
    ON merkle_snapshots(connection_id, is_latest);

CREATE INDEX IF NOT EXISTS idx_conn_created
    ON merkle_snapshots(connection_id, created_at);
"""


class MerkleTreeStore:
    """
    Persists Merkle Tree snapshots in a local SQLite database.

    Each source-database connection gets its own history of snapshots,
    enabling rollback and point-in-time auditing.
    """

    def __init__(self, db_path: str = "merkle_snapshots.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")  # concurrent readers
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── Public API ────────────────────────────────────────────────────

    def save_snapshot(self, connection_id: str, tree: MerkleNode) -> int:
        """
        Persist a new Merkle Tree snapshot for a given connection.
        Marks all previous snapshots for this connection as non-latest.
        Returns the snapshot id.
        """
        tree_json = json.dumps(self._serialize(tree))
        now = datetime.now(timezone.utc).isoformat()

        cur = self._conn.cursor()
        # Demote previous latest
        cur.execute(
            "UPDATE merkle_snapshots SET is_latest = 0 "
            "WHERE connection_id = ? AND is_latest = 1",
            (connection_id,),
        )
        cur.execute(
            "INSERT INTO merkle_snapshots "
            "(connection_id, root_hash, tree_json, record_count, created_at, is_latest) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (connection_id, tree.hash, tree_json, tree.record_count, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def load_latest(self, connection_id: str) -> Optional[MerkleNode]:
        """Load the most recent snapshot for a connection."""
        cur = self._conn.execute(
            "SELECT tree_json FROM merkle_snapshots "
            "WHERE connection_id = ? AND is_latest = 1 "
            "LIMIT 1",
            (connection_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._deserialize(json.loads(row[0]))

    def load_snapshot_by_id(self, snapshot_id: int) -> Optional[MerkleNode]:
        """Load a specific historical snapshot by its id."""
        cur = self._conn.execute(
            "SELECT tree_json FROM merkle_snapshots WHERE id = ?",
            (snapshot_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._deserialize(json.loads(row[0]))

    def rollback_to(self, connection_id: str, snapshot_id: int) -> bool:
        """
        Roll back to a previous snapshot. Marks it as latest,
        demotes the current latest.
        """
        cur = self._conn.cursor()
        # Verify it belongs to this connection
        cur.execute(
            "SELECT id FROM merkle_snapshots "
            "WHERE id = ? AND connection_id = ?",
            (snapshot_id, connection_id),
        )
        if not cur.fetchone():
            return False

        cur.execute(
            "UPDATE merkle_snapshots SET is_latest = 0 "
            "WHERE connection_id = ? AND is_latest = 1",
            (connection_id,),
        )
        cur.execute(
            "UPDATE merkle_snapshots SET is_latest = 1 WHERE id = ?",
            (snapshot_id,),
        )
        self._conn.commit()
        return True

    def list_snapshots(self, connection_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent snapshots for a connection (metadata only)."""
        cur = self._conn.execute(
            "SELECT id, root_hash, record_count, created_at, is_latest "
            "FROM merkle_snapshots "
            "WHERE connection_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (connection_id, limit),
        )
        return [
            {
                "id": r[0],
                "root_hash": r[1],
                "record_count": r[2],
                "created_at": r[3],
                "is_latest": bool(r[4]),
            }
            for r in cur.fetchall()
        ]

    def prune_old_snapshots(self, connection_id: str, keep: int = 10) -> int:
        """Delete all but the N most recent snapshots. Returns count deleted."""
        cur = self._conn.cursor()
        cur.execute(
            "DELETE FROM merkle_snapshots "
            "WHERE connection_id = ? AND id NOT IN ("
            "  SELECT id FROM merkle_snapshots "
            "  WHERE connection_id = ? "
            "  ORDER BY created_at DESC LIMIT ?"
            ")",
            (connection_id, connection_id, keep),
        )
        self._conn.commit()
        return cur.rowcount

    def close(self):
        self._conn.close()

    # ── Serialization ─────────────────────────────────────────────────

    def _serialize(self, node: MerkleNode) -> Dict[str, Any]:
        return {
            "hash": node.hash,
            "partition_id": node.partition_id,
            "record_count": node.record_count,
            "last_modified": node.last_modified.isoformat(),
            "left": self._serialize(node.left) if node.left else None,
            "right": self._serialize(node.right) if node.right else None,
        }

    def _deserialize(self, data: Dict[str, Any]) -> MerkleNode:
        return MerkleNode(
            hash=data["hash"],
            partition_id=data.get("partition_id"),
            record_count=data.get("record_count", 0),
            last_modified=datetime.fromisoformat(data["last_modified"]),
            left=self._deserialize(data["left"]) if data.get("left") else None,
            right=self._deserialize(data["right"]) if data.get("right") else None,
        )
