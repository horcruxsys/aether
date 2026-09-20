"""
Column Profiler — tokenization, normalization, and sketch generation.

This module bridges raw database columns to the MinHash/LSH pipeline:
  1. Tokenize column names (camelCase, snake_case, PascalCase → token set)
  2. Normalize values (lowercase, strip, collapse whitespace)
  3. Build ColumnProfile with MinHash sketches ready for LSH indexing
"""
import re
from typing import Set, List, Any, Optional
from .models import ColumnProfile
from .minhash import minhash


def tokenize_identifier(name: str) -> Set[str]:
    """
    Split a database identifier into semantic tokens.

    Handles camelCase, PascalCase, snake_case, kebab-case, and
    mixed conventions. Filters out single-character tokens and
    common noise like 'id' abbreviations.

    Examples:
        "customerUserId"  → {"customer", "user", "id"}
        "cust_id"         → {"cust", "id"}
        "emailAddress"    → {"email", "address"}
        "CREATED_AT"      → {"created", "at"}
        "uid"             → {"uid"}

    Args:
        name: Raw column/table name.

    Returns:
        Set of lowercase tokens (length > 1, or the entire name if short).
    """
    if not name:
        return set()

    # Insert underscore before uppercase runs: "customerUserId" → "customer_User_Id"
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Handle consecutive uppercase: "XMLParser" → "XML_Parser"
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)

    # Split on any non-alphanumeric character
    tokens = re.split(r"[^a-zA-Z0-9]+", s.lower())

    # Filter noise but keep short meaningful identifiers
    result = {t for t in tokens if t and len(t) > 1}

    # If the original name is short (like "uid", "pk"), keep it as-is
    if not result and name.strip():
        result = {name.lower().strip()}

    return result


def normalize_value(value: Any) -> Optional[str]:
    """
    Normalize a database value for MinHash comparison.

    - None / empty → excluded (not added to set)
    - Strings → lowercase, stripped, collapsed whitespace
    - Numbers → string representation
    - Everything else → str() conversion

    Args:
        value: Raw database value.

    Returns:
        Normalized string, or None if the value should be excluded.
    """
    if value is None:
        return None

    s = str(value).strip().lower()

    if not s or s in ("none", "null", "nan", ""):
        return None

    # Collapse internal whitespace
    s = re.sub(r"\s+", " ", s)

    return s


def profile_column_from_values(
    db_id: str,
    table: str,
    column: str,
    values: List[Any],
    dtype: str = "unknown",
    num_hashes: int = 256,
) -> ColumnProfile:
    """
    Build a complete ColumnProfile from a list of raw values.

    This is the primary entry point for profiling. In production,
    `values` would be sampled from the source database (e.g., via
    reservoir sampling — see ISSUE-006).

    Args:
        db_id: Identifier for the source database connection.
        table: Table or collection name.
        column: Column or field name.
        values: Raw sample values from the column.
        dtype: Detected data type string.
        num_hashes: MinHash signature dimension.

    Returns:
        ColumnProfile with sketches ready for LSH indexing.
    """
    # Normalize values, drop NULLs
    sample_values = set()
    for v in values:
        normed = normalize_value(v)
        if normed is not None:
            sample_values.add(normed)

    # Tokenize column name
    name_tokens = tokenize_identifier(column)

    # Generate MinHash signatures
    value_sketch = minhash(sample_values, num_hashes=num_hashes)
    name_sketch = minhash(name_tokens, num_hashes=num_hashes)

    return ColumnProfile(
        db_id=db_id,
        table=table,
        column=column,
        dtype=dtype,
        sample_values=sample_values,
        name_tokens=name_tokens,
        value_sketch=value_sketch,
        name_sketch=name_sketch,
    )
