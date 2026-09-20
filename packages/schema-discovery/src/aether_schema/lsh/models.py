"""
Data models for schema discovery and alignment.
"""
from dataclasses import dataclass, field
from typing import Set, List, Optional


@dataclass
class ColumnProfile:
    """
    A rich profile of a single database column, capturing both
    its structural identity and its statistical fingerprint.

    The value_sketch and name_sketch are MinHash signatures that
    enable O(1) approximate similarity comparison.
    """
    db_id: str                                # Source database identifier
    table: str                                # Table / collection name
    column: str                               # Column / field name
    dtype: str = "unknown"                    # Detected data type
    sample_values: Set[str] = field(default_factory=set)   # Normalized value sample
    name_tokens: Set[str] = field(default_factory=set)     # Tokenized column name
    value_sketch: List[int] = field(default_factory=list)  # MinHash sig of values
    name_sketch: List[int] = field(default_factory=list)   # MinHash sig of name tokens

    @property
    def key(self) -> str:
        """Unique key for this column across all databases."""
        return f"{self.db_id}.{self.table}.{self.column}"


@dataclass
class AlignmentCandidate:
    """A pair of columns with estimated similarity."""
    source_key: str
    target_key: str
    value_similarity: float    # Jaccard estimate from value sketches
    name_similarity: float     # Jaccard estimate from name sketches
    combined_score: float      # Weighted blend

    def to_dict(self) -> dict:
        return {
            "source": self.source_key,
            "target": self.target_key,
            "value_similarity": round(self.value_similarity, 4),
            "name_similarity": round(self.name_similarity, 4),
            "combined_score": round(self.combined_score, 4),
        }
