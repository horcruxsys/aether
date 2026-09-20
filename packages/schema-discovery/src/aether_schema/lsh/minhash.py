"""
MinHash — probabilistic Jaccard similarity estimation.

Uses a pair of random linear hash functions (a*x + b) mod p mod m
instead of SHA-256 per hash function. This is the standard textbook
approach (Broder, 1997) and is orders of magnitude faster than
cryptographic hashing in a loop.

Accuracy / dimension tradeoff:
  - 128 hashes → ~8.8% standard error
  - 256 hashes → ~6.2% standard error

We use 256 hashes by default for better accuracy on real-world data.
"""
import hashlib
import struct
import random as _random
from typing import Set, List

NUM_HASHES = 256  # Signature dimension — 32 bands × 8 rows

# Large prime for universal hashing
_MERSENNE_PRIME = (1 << 61) - 1
_MAX_HASH = (1 << 32) - 1

# Pre-generate random coefficients for universal hash functions
# a*hash(x) + b mod prime — each (a, b) pair is one hash function
_rng = _random.Random(42)  # Fixed seed for reproducibility
_HASH_COEFFS = [
    (_rng.randint(1, _MERSENNE_PRIME - 1), _rng.randint(0, _MERSENNE_PRIME - 1))
    for _ in range(NUM_HASHES)
]


def _element_hash(element: str) -> int:
    """Fast 32-bit hash of a string element using md5 truncation."""
    return struct.unpack("<I", hashlib.md5(element.encode("utf-8")).digest()[:4])[0]


def minhash(elements: Set[str], num_hashes: int = NUM_HASHES) -> List[int]:
    """
    Compute a MinHash signature for a set of string elements.

    Uses universal hashing: h_i(x) = (a_i * hash(x) + b_i) mod p
    This is the standard approach from Broder (1997) and is much
    faster than SHA-256-per-hash-function.

    Args:
        elements: Set of string tokens (values or name tokens).
        num_hashes: Number of hash functions (signature dimension).

    Returns:
        List of min-hash values (one per hash function).
    """
    if not elements:
        return [_MERSENNE_PRIME] * num_hashes

    # Ensure we have enough coefficients
    coeffs = _HASH_COEFFS[:num_hashes]

    signature = [_MERSENNE_PRIME] * num_hashes

    # Pre-hash all elements once
    elem_hashes = [_element_hash(e) for e in elements]

    for eh in elem_hashes:
        for i, (a, b) in enumerate(coeffs):
            h = (a * eh + b) % _MERSENNE_PRIME
            if h < signature[i]:
                signature[i] = h

    return signature


def jaccard_estimate(sig_a: List[int], sig_b: List[int]) -> float:
    """
    Estimate Jaccard similarity from two MinHash signatures.

    The fraction of positions where both signatures agree is an
    unbiased estimator of the true Jaccard coefficient.

    Args:
        sig_a: MinHash signature of set A.
        sig_b: MinHash signature of set B.

    Returns:
        Estimated Jaccard similarity in [0.0, 1.0].
    """
    if len(sig_a) != len(sig_b):
        raise ValueError(
            f"Signature lengths must match: {len(sig_a)} vs {len(sig_b)}"
        )
    if not sig_a:
        return 0.0

    matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return matches / len(sig_a)
