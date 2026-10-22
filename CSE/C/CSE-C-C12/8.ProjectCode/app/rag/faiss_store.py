"""FAISS CPU store with cosine-equivalent normalized inner product."""
import json
import numpy as np
from pathlib import Path

class FaissStore:
    def __init__(self, index_path: Path, meta_path: Path):
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self.index = None
        self.records: list[dict] = []

    def build(self, vectors: np.ndarray, records: list[dict]):
        import faiss
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(vectors.astype(np.float32))
        self.records = records
        self.save()

    def save(self):
        import faiss
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def load(self) -> bool:
        try:
            import faiss
            if not self.index_path.exists() or not self.meta_path.exists():
                return False
            self.index = faiss.read_index(str(self.index_path))
            self.records = json.loads(self.meta_path.read_text(encoding="utf-8"))
            return True
        except Exception as e:
            print(f"[faiss] load failed: {e}")
            return False

    def search(self, query_vec: np.ndarray, k: int = 15):
        if self.index is None:
            raise RuntimeError("FAISS index not loaded")
        q = query_vec.astype(np.float32).reshape(1, -1)
        scores, idxs = self.index.search(q, min(k, self.index.ntotal))
        out = []
        for s, i in zip(scores[0], idxs[0]):
            if int(i) < 0:
                continue
            out.append((float(s), self.records[int(i)], int(i)))
        return out
