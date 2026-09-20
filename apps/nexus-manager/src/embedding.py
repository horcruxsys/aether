"""Embedding generation using sentence-transformers."""

from typing import List
from sentence_transformers import SentenceTransformer

# Load model once at module import (cached for the lifetime of the process)
_model = None

def _get_model() -> SentenceTransformer:
    """Lazy-load and cache the embedding model."""
    global _model
    if _model is None:
        print("[Embedding] Loading sentence-transformers/all-MiniLM-L6-v2...")
        _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("[Embedding] ✅ Model loaded (384-dimensional embeddings)")
    return _model

def embed(text: str) -> List[float]:
    """Generate a real embedding vector for the given text.

    Args:
        text: The content to embed

    Returns:
        A 384-dimensional vector as a list of floats
    """
    model = _get_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()
