"""PeerScope embedding helper: sentence-transformers with TF-IDF fallback."""
from __future__ import annotations

import threading

import numpy as np

_lock = threading.Lock()
_model = None
_model_error: str | None = None

_FALLBACK_VEC = None
_FALLBACK_VOCAB: list[str] | None = None


def embedding_status() -> dict:
    return {"loaded": _model is not None, "error": _model_error,
            "model": "sentence-transformers/all-MiniLM-L6-v2" if _model is not None else "tfidf-fallback"}


def _get_model():
    global _model, _model_error
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        try:
            from sentence_transformers import SentenceTransformer

            from app.config import EMBEDDING_MODEL

            _model = SentenceTransformer(EMBEDDING_MODEL)
            return _model
        except Exception as exc:
            _model_error = str(exc)
            return None


def embed_texts(texts: list[str]) -> np.ndarray:
    mdl = _get_model()
    clean = [(t or " ")[:2000] for t in texts]
    if mdl is not None:
        arr = mdl.encode(clean, normalize_embeddings=False, show_progress_bar=False)
        return np.asarray(arr, dtype=float)
    # Deterministic TF-IDF fallback so matching still works offline.
    from sklearn.feature_extraction.text import TfidfVectorizer

    global _FALLBACK_VEC, _FALLBACK_VOCAB
    if _FALLBACK_VEC is None:
        _FALLBACK_VEC = TfidfVectorizer(max_features=512, ngram_range=(1, 2))
        mat = _FALLBACK_VEC.fit_transform(clean).toarray()
        return np.asarray(mat, dtype=float)
    mat = _FALLBACK_VEC.transform(clean).toarray()
    return np.asarray(mat, dtype=float)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float((a @ a) ** 0.5) * float((b @ b) ** 0.5)
    if not denom:
        return 0.0
    return float(max(-1.0, min(1.0, (a @ b) / denom)))
