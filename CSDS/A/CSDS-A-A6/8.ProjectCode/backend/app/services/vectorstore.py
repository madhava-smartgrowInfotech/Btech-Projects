"""Local vector store: NumPy arrays for clause embeddings + cosine similarity
search, and centroid embeddings per CUAD-style clause type (no ChromaDB/pgvector)."""
import numpy as np


def to_blob(vector: list[float]) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def cosine_similarity_matrix(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """query: (d,), matrix: (n, d) -> (n,) similarities."""
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
    norms[norms == 0] = 1e-9
    return (matrix @ query) / norms


def top_k_similar(query: np.ndarray, matrix: np.ndarray, k: int = 5) -> list[tuple[int, float]]:
    sims = cosine_similarity_matrix(query, matrix)
    idx = np.argsort(-sims)[:k]
    return [(int(i), float(sims[i])) for i in idx]
