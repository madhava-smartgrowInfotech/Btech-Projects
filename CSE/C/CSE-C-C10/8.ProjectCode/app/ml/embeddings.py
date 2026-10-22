"""Text embeddings via all-MiniLM-L6-v2 with deterministic fallback."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np

from app.config import EMBEDDING_MODEL_NAME, EMBEDDING_DIM, MODELS_DIR

log = logging.getLogger(__name__)
_model = None
_backend = "none"


def _fallback_embed(texts: list[str], dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Deterministic hashing-based embedding (384-d), L2-normalized. Used only if transformer unavailable."""
    out = np.zeros((len(texts), dim), dtype=np.float32)
    for i, t in enumerate(texts):
        toks = (t or "").lower().split() or ["empty"]
        vec = np.zeros(dim, dtype=np.float64)
        for tok in toks:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            for j in range(4):
                idx = (h >> (j * 8)) % dim
                vec[idx] += 1.0 / (j + 1)
        n = np.linalg.norm(vec)
        if n > 0:
            vec /= n
        out[i] = vec.astype(np.float32)
    return out


def get_backend() -> str:
    return _backend


def load_model():
    global _model, _backend
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        _backend = "sentence-transformers"
        log.info("Loaded embedding model %s", EMBEDDING_MODEL_NAME)
    except Exception as e:
        log.warning("Embedding model unavailable (%s); using deterministic fallback.", e)
        _model = None
        _backend = "hash-fallback"
    return _model


def embed_texts(texts: list[str]) -> tuple[np.ndarray, str]:
    texts = [(t or "")[:2000] for t in texts]
    m = load_model()
    if m is not None:
        try:
            vecs = m.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=False)
            return np.asarray(vecs, dtype=np.float32), "sentence-transformers"
        except Exception as e:
            log.warning("Transformer encode failed (%s); fallback.", e)
    return _fallback_embed(texts), "hash-fallback"


def l2norm(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (a / n).astype(np.float32)
