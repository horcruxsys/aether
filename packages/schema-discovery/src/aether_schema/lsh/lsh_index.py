"""
LSH Index — Locality Sensitive Hashing for fast candidate discovery.

Divides each MinHash signature into bands and hashes each band into
a bucket. Columns whose signatures collide in ANY band are candidate
matches. This reduces pairwise comparison from O(n²) to O(n).

Configuration:
  - NUM_BANDS × ROWS_PER_BAND = NUM_HASHES (signature length)
  - More bands → higher recall (fewer false negatives), more candidates
  - Fewer bands → higher precision (fewer false positives), faster

With 32 bands × 4 rows (128 hashes total):
  - Probability of becoming a candidate at similarity s:
    P(candidate) = 1 - (1 - s^4)^32
  - At s=0.6: P ≈ 0.98  (2% false negative rate)
  - At s=0.3: P ≈ 0.24  (good filtering of dissimilar pairs)
"""
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from .models import ColumnProfile, AlignmentCandidate
from .minhash import jaccard_estimate, NUM_HASHES

NUM_BANDS = 32
ROWS_PER_BAND = NUM_HASHES // NUM_BANDS  # 4


class LSHIndex:
    """
    Locality Sensitive Hashing index for approximate nearest neighbor
    search over MinHash signatures.

    Supports:
      - Incremental addition of new columns/databases
      - Query for candidates matching a given profile
      - Bulk alignment across all indexed profiles
      - Configurable value/name similarity weighting
    """

    def __init__(
        self,
        num_bands: int = NUM_BANDS,
        value_weight: float = 0.7,
        name_weight: float = 0.3,
    ):
        """
        Args:
            num_bands: Number of LSH bands.
            value_weight: Weight for value-distribution similarity in combined score.
            name_weight: Weight for column-name similarity in combined score.
        """
        self.num_bands = num_bands
        self.rows_per_band = NUM_HASHES // num_bands
        self.value_weight = value_weight
        self.name_weight = name_weight

        # band_idx → (band_hash → list of column keys)
        self._value_buckets: Dict[int, Dict[Tuple, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._name_buckets: Dict[int, Dict[Tuple, List[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._profiles: Dict[str, ColumnProfile] = {}

    @property
    def size(self) -> int:
        """Number of indexed columns."""
        return len(self._profiles)

    def add(self, profile: ColumnProfile) -> None:
        """
        Add a column profile to the index.
        Supports incremental addition — no need to rebuild.
        """
        key = profile.key
        self._profiles[key] = profile

        # Index value sketch bands
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            end = start + self.rows_per_band
            band = tuple(profile.value_sketch[start:end])
            self._value_buckets[band_idx][band].append(key)

        # Index name sketch bands
        if profile.name_sketch:
            for band_idx in range(self.num_bands):
                start = band_idx * self.rows_per_band
                end = start + self.rows_per_band
                band = tuple(profile.name_sketch[start:end])
                self._name_buckets[band_idx][band].append(key)

    def add_many(self, profiles: List[ColumnProfile]) -> None:
        """Add multiple profiles to the index."""
        for p in profiles:
            self.add(p)

    def find_candidates(
        self,
        profile: ColumnProfile,
        threshold: float = 0.3,
        exclude_same_db: bool = False,
    ) -> List[AlignmentCandidate]:
        """
        Find all columns similar to the given profile.

        Args:
            profile: Query column profile.
            threshold: Minimum combined score to include as candidate.
            exclude_same_db: If True, don't match columns from the same database.

        Returns:
            List of AlignmentCandidates sorted by combined_score descending.
        """
        query_key = profile.key
        candidate_keys: set = set()

        # Collect value-based candidates
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            end = start + self.rows_per_band
            band = tuple(profile.value_sketch[start:end])
            bucket = self._value_buckets[band_idx].get(band, [])
            candidate_keys.update(bucket)

        # Collect name-based candidates
        if profile.name_sketch:
            for band_idx in range(self.num_bands):
                start = band_idx * self.rows_per_band
                end = start + self.rows_per_band
                band = tuple(profile.name_sketch[start:end])
                bucket = self._name_buckets[band_idx].get(band, [])
                candidate_keys.update(bucket)

        # Remove self
        candidate_keys.discard(query_key)

        # Score candidates
        results: List[AlignmentCandidate] = []
        for key in candidate_keys:
            candidate = self._profiles[key]

            if exclude_same_db and candidate.db_id == profile.db_id:
                continue

            val_sim = jaccard_estimate(
                profile.value_sketch, candidate.value_sketch
            )
            name_sim = jaccard_estimate(
                profile.name_sketch, candidate.name_sketch
            )
            combined = (
                self.value_weight * val_sim + self.name_weight * name_sim
            )

            if combined >= threshold:
                results.append(AlignmentCandidate(
                    source_key=query_key,
                    target_key=key,
                    value_similarity=val_sim,
                    name_similarity=name_sim,
                    combined_score=combined,
                ))

        results.sort(key=lambda c: -c.combined_score)
        return results

    def find_all_alignments(
        self,
        threshold: float = 0.5,
        exclude_same_db: bool = True,
    ) -> List[AlignmentCandidate]:
        """
        Discover all cross-database column alignments above the threshold.

        Returns deduplicated candidates (A↔B appears once, not twice).
        """
        seen_pairs: set = set()
        all_candidates: List[AlignmentCandidate] = []

        for profile in self._profiles.values():
            candidates = self.find_candidates(
                profile, threshold=threshold, exclude_same_db=exclude_same_db
            )
            for c in candidates:
                pair = tuple(sorted([c.source_key, c.target_key]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    all_candidates.append(c)

        all_candidates.sort(key=lambda c: -c.combined_score)
        return all_candidates

    def get_profile(self, key: str) -> Optional[ColumnProfile]:
        """Retrieve a stored profile by key."""
        return self._profiles.get(key)
