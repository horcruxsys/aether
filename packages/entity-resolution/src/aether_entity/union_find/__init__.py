from .core import UnionFind
from .record_id import make_record_id, parse_record_id
from .matching import MatchStrategy, ExactKeyMatch, FuzzyStringMatch
from .canonical import build_canonical_entity
from .pipeline import resolve_entities

__all__ = [
    "UnionFind",
    "make_record_id",
    "parse_record_id",
    "MatchStrategy",
    "ExactKeyMatch",
    "FuzzyStringMatch",
    "build_canonical_entity",
    "resolve_entities",
]
