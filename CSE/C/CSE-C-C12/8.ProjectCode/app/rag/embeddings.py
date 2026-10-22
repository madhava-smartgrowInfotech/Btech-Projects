"""Embedding backend: SentenceTransformer with TF-IDF fallback for offline use."""
import json
import numpy as np
from pathlib import Path

class EmbeddingBackend:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.mode = "unknown"
        self.model = None
        self.vectorizer = None
        self.dim = 384
        self._load()

    def _load(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.dim = self.model.get_sentence_embedding_dimension()
            self.mode = "sentence-transformer"
        except Exception as e:
            print(f"[embeddings] SentenceTransformer unavailable ({e}); using TF-IDF fallback.")
            self.mode = "tfidf"
            self.model = None

    def fit_fallback(self, texts: list[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
        mat = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)
        # pad/truncate to 384
        n, d = mat.shape
        if d < 384:
            mat = np.pad(mat, ((0, 0), (0, 384 - d)))
        else:
            mat = mat[:, :384]
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
        return mat / norms

    def encode(self, texts: list[str]) -> np.ndarray:
        if self.mode == "sentence-transformer" and self.model is not None:
            vecs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(vecs, dtype=np.float32)
        # TF-IDF fallback
        if self.vectorizer is None:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
            mat = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)
        else:
            mat = self.vectorizer.transform(texts).toarray().astype(np.float32)
        n, d = mat.shape
        if d < 384:
            mat = np.pad(mat, ((0, 0), (0, 384 - d)))
        else:
            mat = mat[:, :384]
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
        return (mat / norms).astype(np.float32)
