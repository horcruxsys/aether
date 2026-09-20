"""
Canonical Entity Builder — merge all records in a cluster into one.

After Union-Find resolves which records are the same entity,
this module produces a single canonical representation by merging
fields from all source records.

Determinism: records are sorted by record_id before merging, so
the same cluster always produces the same canonical entity.
"""
import uuid
from typing import Set, Dict, List, Any, Optional
from .record_id import parse_record_id


def build_canonical_entity(
    cluster: Set[str],
    records_by_id: Dict[str, Dict[str, Any]],
    priority_order: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Merge all records in a cluster into one canonical entity.

    Fields from higher-priority databases override lower-priority ones.
    If no priority_order is given, records are merged in sorted order
    by record_id (deterministic).

    Args:
        cluster: Set of record IDs in this entity cluster.
        records_by_id: Mapping of record_id → record dict.
        priority_order: Optional list of db_ids from lowest to highest
                        priority. Higher-priority DB fields override.

    Returns:
        A canonical entity dict with merged fields, an entity_id,
        and provenance metadata.
    """
    # Sort records for determinism
    sorted_ids = sorted(cluster)

    # If priority_order given, sort by it (lower priority first, so
    # higher-priority fields overwrite)
    if priority_order:
        priority_map = {db: i for i, db in enumerate(priority_order)}

        def sort_key(rid: str) -> int:
            db_id, _, _ = parse_record_id(rid)
            return priority_map.get(db_id, -1)

        sorted_ids = sorted(sorted_ids, key=sort_key)

    canonical: Dict[str, Any] = {}
    source_fields: Dict[str, str] = {}  # field → source record_id

    for record_id in sorted_ids:
        record = records_by_id.get(record_id, {})
        for field, value in record.items():
            if value is not None and field not in ("_pk", "id"):
                canonical[field] = value
                source_fields[field] = record_id

    # Generate a deterministic entity ID from the sorted cluster members
    # Use a hash of sorted record IDs for reproducibility
    cluster_key = "|".join(sorted(cluster))
    entity_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, cluster_key))

    canonical["_entity_id"] = entity_id
    canonical["_source_records"] = sorted(cluster)
    canonical["_cluster_size"] = len(cluster)
    canonical["_field_sources"] = source_fields

    return canonical


def entity_to_text(entity: Dict[str, Any]) -> str:
    """
    Convert a canonical entity to a natural language representation
    suitable for embedding.

    Skips internal metadata fields (prefixed with _).
    """
    parts = []
    for key, value in sorted(entity.items()):
        if key.startswith("_"):
            continue
        parts.append(f"{key}: {value}")
    return ". ".join(parts)
