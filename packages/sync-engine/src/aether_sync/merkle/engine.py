import hashlib
import json
from typing import List, Optional, Dict, Any
from .models import MerkleNode, Partition

def hash_partition(records: List[Dict[str, Any]]) -> str:
    """
    Hash a partition of records in a stable, order-independent way.
    Sort by primary key (or some stable tiebreaker) before hashing to ensure determinism.
    We assume the records might have an 'id' or similarly stable unique key.
    If no 'id' is present, we sort by the entire stringified record.
    """
    if not records:
        return hashlib.sha256(b"empty_partition").hexdigest()

    # Determine sort key: use 'id' if available, else string representation
    def get_sort_key(r):
        return str(r.get('id', r))

    normalized = sorted(
        [json.dumps(r, sort_keys=True, default=str) for r in records],
        key=lambda x: x
    )
    combined = "||".join(normalized)
    return hashlib.sha256(combined.encode()).hexdigest()

def build_merkle_tree(partitions: List[Partition]) -> MerkleNode:
    """
    Build the Merkle Tree bottom-up from leaf partitions.
    """
    if not partitions:
        return MerkleNode(hash=hashlib.sha256(b"empty_tree").hexdigest())

    leaves = [
        MerkleNode(
            hash=hash_partition(p.records), 
            partition_id=p.id, 
            record_count=len(p.records)
        )
        for p in partitions
    ]
    return _build_internal(leaves)

def _build_internal(nodes: List[MerkleNode]) -> MerkleNode:
    if len(nodes) == 1:
        return nodes[0]
    
    # We build a binary tree. If odd number of nodes, we can duplicate the last one 
    # or just keep it as is. Typical Merkle Tree (like Bitcoin) duplicates the last hash.
    next_level = []
    for i in range(0, len(nodes), 2):
        left = nodes[i]
        right = nodes[i+1] if i + 1 < len(nodes) else None
        
        if right:
            combined_hash = hashlib.sha256(
                (left.hash + right.hash).encode()
            ).hexdigest()
            parent = MerkleNode(
                hash=combined_hash,
                left=left,
                right=right,
                record_count=left.record_count + right.record_count
            )
        else:
            # Single node remaining, just pass it up or hash it again?
            # Git-style: internal nodes always have children.
            # For simplicity, we'll just promote it if it's the only one left at this level
            # but if it has a sibling, we hash them.
            parent = left
            
        next_level.append(parent)
    
    return _build_internal(next_level)

def find_changed_partitions(
    old_tree: Optional[MerkleNode],
    new_tree: Optional[MerkleNode]
) -> List[str]:
    """
    Returns list of partition_ids that changed.
    Traverses only branches where hashes differ.
    """
    if not old_tree and not new_tree:
        return []
    if not old_tree:
        # Everything in new_tree is "changed" or rather added
        return _get_all_partition_ids(new_tree)
    if not new_tree:
        # Everything in old_tree is removed
        return [] # Or should we return them? Usually "changed" means we need to re-sync.

    if old_tree.hash == new_tree.hash:
        return []   # Subtree unchanged — prune entire branch

    if old_tree.partition_id is not None or new_tree.partition_id is not None:
        # Leaf node with different hash or one is a leaf and the other isn't
        # Return the new partition_id if it exists
        return [new_tree.partition_id] if new_tree.partition_id else []

    changed = []
    # Both are internal nodes with differing hashes
    # We compare children. This assumes tree structure is stable.
    # If structure changes (e.g. number of partitions changes), we'll find differences.
    
    # Note: A real Merkle diff might be more complex if tree structure is not stable.
    # But here we assume built from the same set/order of partition IDs.
    
    if old_tree.left and new_tree.left:
        changed += find_changed_partitions(old_tree.left, new_tree.left)
    elif new_tree.left:
        changed += _get_all_partition_ids(new_tree.left)
        
    if old_tree.right and new_tree.right:
        changed += find_changed_partitions(old_tree.right, new_tree.right)
    elif new_tree.right:
        changed += _get_all_partition_ids(new_tree.right)
        
    return list(set(changed)) # Deduplicate just in case

def _get_all_partition_ids(node: MerkleNode) -> List[str]:
    if node.partition_id:
        return [node.partition_id]
    ids = []
    if node.left:
        ids += _get_all_partition_ids(node.left)
    if node.right:
        ids += _get_all_partition_ids(node.right)
    return ids
