"""
Matching strategies — generate evidence for entity merges.

Each strategy implements find_matches() which returns triples of
(record_id_a, record_id_b, evidence) for records believed to be
the same real-world entity.

Strategies are composable: the entity resolution pipeline applies
all strategies and feeds their outputs to Union-Find.
"""
import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Set, Any, Optional
from .record_id import make_record_id


class MatchStrategy(ABC):
    """Base class for entity matching strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this strategy."""
        ...

    @abstractmethod
    def find_matches(
        self,
        records_a: List[Dict[str, Any]],
        records_b: List[Dict[str, Any]],
        db_id_a: str,
        db_id_b: str,
        table_a: str,
        table_b: str,
        key_column_a: str,
        key_column_b: str,
    ) -> List[Tuple[str, str, List[str]]]:
        """
        Find matching records between two record sets.

        Args:
            records_a: Records from database A (list of dicts).
            records_b: Records from database B (list of dicts).
            db_id_a: Database A identifier.
            db_id_b: Database B identifier.
            table_a: Table name in database A.
            table_b: Table name in database B.
            key_column_a: Column name used for matching in A.
            key_column_b: Column name used for matching in B.

        Returns:
            List of (record_id_a, record_id_b, evidence_list) triples.
        """
        ...


class ExactKeyMatch(MatchStrategy):
    """
    Match records sharing identical values in aligned key columns.

    This is the highest-confidence strategy — if two databases have
    the same customer_id value, they almost certainly refer to the
    same entity.
    """

    @property
    def name(self) -> str:
        return "exact_key_match"

    def find_matches(
        self,
        records_a: List[Dict[str, Any]],
        records_b: List[Dict[str, Any]],
        db_id_a: str,
        db_id_b: str,
        table_a: str,
        table_b: str,
        key_column_a: str,
        key_column_b: str,
    ) -> List[Tuple[str, str, List[str]]]:
        matches = []

        # Build index on B's key column
        b_index: Dict[str, List[Dict]] = {}
        for rec in records_b:
            val = rec.get(key_column_b)
            if val is not None:
                key = str(val).strip()
                if key:
                    b_index.setdefault(key, []).append(rec)

        # Look up each A record in B's index
        for rec_a in records_a:
            val_a = rec_a.get(key_column_a)
            if val_a is None:
                continue
            key = str(val_a).strip()
            if not key:
                continue

            for rec_b in b_index.get(key, []):
                # Need a primary key from each record to build the record ID
                pk_a = rec_a.get("_pk", rec_a.get("id", id(rec_a)))
                pk_b = rec_b.get("_pk", rec_b.get("id", id(rec_b)))

                id_a = make_record_id(db_id_a, table_a, pk_a)
                id_b = make_record_id(db_id_b, table_b, pk_b)

                evidence = [
                    f"exact_key_match::{key_column_a}={key_column_b}::{key}"
                ]
                matches.append((id_a, id_b, evidence))

        return matches


class FuzzyStringMatch(MatchStrategy):
    """
    Match records where a string column matches after normalization.

    Normalization includes: lowercase, strip whitespace, remove
    punctuation, and optionally handle email-specific patterns
    (e.g., stripping +aliases from Gmail addresses).
    """

    def __init__(self, similarity_threshold: float = 1.0):
        """
        Args:
            similarity_threshold: 1.0 = exact after normalization,
                                  < 1.0 = fuzzy matching (future).
        """
        self.threshold = similarity_threshold

    @property
    def name(self) -> str:
        return "fuzzy_string_match"

    @staticmethod
    def _normalize(value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip().lower()
        # Handle email plus-addressing FIRST: user+tag@domain → user@domain
        s = re.sub(r"\+[^@]*@", "@", s)
        # Remove punctuation except @ and .
        s = re.sub(r"[^\w@.\-]", "", s)
        return s if s else None

    def find_matches(
        self,
        records_a: List[Dict[str, Any]],
        records_b: List[Dict[str, Any]],
        db_id_a: str,
        db_id_b: str,
        table_a: str,
        table_b: str,
        key_column_a: str,
        key_column_b: str,
    ) -> List[Tuple[str, str, List[str]]]:
        matches = []

        # Build normalized index on B
        b_index: Dict[str, List[Dict]] = {}
        for rec in records_b:
            normed = self._normalize(rec.get(key_column_b))
            if normed:
                b_index.setdefault(normed, []).append(rec)

        for rec_a in records_a:
            normed_a = self._normalize(rec_a.get(key_column_a))
            if not normed_a:
                continue

            for rec_b in b_index.get(normed_a, []):
                pk_a = rec_a.get("_pk", rec_a.get("id", id(rec_a)))
                pk_b = rec_b.get("_pk", rec_b.get("id", id(rec_b)))

                id_a = make_record_id(db_id_a, table_a, pk_a)
                id_b = make_record_id(db_id_b, table_b, pk_b)

                evidence = [
                    f"fuzzy_string_match::{key_column_a}={key_column_b}"
                    f"::normalized={normed_a}"
                ]
                matches.append((id_a, id_b, evidence))

        return matches
