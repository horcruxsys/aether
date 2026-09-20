"""
Record ID utilities — globally unique identifiers across databases.

Convention: "{db_id}::{table}::{pk_value}"

Examples:
  - "postgres_crm::customers::12345"
  - "mongo_orders::orders::507f1f77bcf86cd799439011"
  - "cassandra_events::clickstream::evt-001"
"""
from typing import Any, Tuple


def make_record_id(db_id: str, table: str, pk_value: Any) -> str:
    """
    Create a globally unique record identifier.

    Args:
        db_id: Database connection identifier.
        table: Table or collection name.
        pk_value: Primary key value (any type, will be str-converted).

    Returns:
        A deterministic, globally unique string ID.
    """
    return f"{db_id}::{table}::{pk_value}"


def parse_record_id(record_id: str) -> Tuple[str, str, str]:
    """
    Parse a record ID back into its components.

    Args:
        record_id: A string in the format "db_id::table::pk_value".

    Returns:
        Tuple of (db_id, table, pk_value).

    Raises:
        ValueError: If the record_id doesn't have exactly 3 parts.
    """
    parts = record_id.split("::", 2)
    if len(parts) != 3:
        raise ValueError(
            f"Invalid record_id format: '{record_id}'. "
            f"Expected 'db_id::table::pk_value'."
        )
    return parts[0], parts[1], parts[2]
