"""
Entity Resolution Pipeline — orchestrates matching strategies + Union-Find.

Applies all configured matching strategies across database pairs,
feeds results into the Union-Find, and produces resolved entity clusters.
"""
import itertools
from typing import List, Dict, Any, Tuple
from .core import UnionFind
from .matching import MatchStrategy
from .record_id import make_record_id


def resolve_entities(
    databases: Dict[str, Dict[str, List[Dict[str, Any]]]],
    alignments: List[Dict[str, Any]],
    strategies: List[MatchStrategy],
) -> UnionFind:
    """
    Run entity resolution across all database pairs.

    Args:
        databases: Nested dict: db_id → table_name → list of records.
                   Each record must have an "id" or "_pk" field.
        alignments: List of alignment dicts, each specifying:
                    {
                        "db_a": str, "table_a": str, "column_a": str,
                        "db_b": str, "table_b": str, "column_b": str,
                    }
        strategies: List of MatchStrategy implementations to apply.

    Returns:
        A populated UnionFind with all resolved entity clusters.
    """
    uf = UnionFind()

    # Register all records
    for db_id, tables in databases.items():
        for table_name, records in tables.items():
            for rec in records:
                pk = rec.get("_pk", rec.get("id"))
                if pk is not None:
                    uf.add(make_record_id(db_id, table_name, pk))

    # Apply each strategy to each alignment
    for alignment in alignments:
        db_a = alignment["db_a"]
        db_b = alignment["db_b"]
        table_a = alignment["table_a"]
        table_b = alignment["table_b"]
        col_a = alignment["column_a"]
        col_b = alignment["column_b"]

        records_a = databases.get(db_a, {}).get(table_a, [])
        records_b = databases.get(db_b, {}).get(table_b, [])

        if not records_a or not records_b:
            continue

        for strategy in strategies:
            matches = strategy.find_matches(
                records_a=records_a,
                records_b=records_b,
                db_id_a=db_a,
                db_id_b=db_b,
                table_a=table_a,
                table_b=table_b,
                key_column_a=col_a,
                key_column_b=col_b,
            )
            for rec_a, rec_b, evidence in matches:
                uf.union(rec_a, rec_b, evidence=evidence)

    return uf
