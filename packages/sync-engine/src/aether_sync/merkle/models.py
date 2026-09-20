from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any

class PartitionStrategy(Enum):
    BY_PRIMARY_KEY_RANGE = "pk_range"    # e.g., rows 0–999, 1000–1999
    BY_TIMESTAMP         = "timestamp"   # e.g., created_at ranges
    BY_HASH_BUCKET       = "hash_bucket" # consistent_hash(pk) % N
    BY_TABLE             = "table"       # one leaf per table (small DBs)

@dataclass
class MerkleNode:
    hash: str                        # SHA-256 hash of this node
    left: Optional['MerkleNode'] = None     # Left child
    right: Optional['MerkleNode'] = None    # Right child
    partition_id: Optional[str] = None      # Set only for leaf nodes
    record_count: int = 0                # Number of records in subtree
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Partition:
    id: str
    records: List[Dict[str, Any]]
