"""Cross-encoder reranker with graceful fallback to hybrid order."""
from typing import Optional

class Reranker:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.available = False
        self._load()

    def _load(self):
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            self.available = True
        except Exception as e:
            print(f"[reranker] CrossEncoder unavailable ({e}); using hybrid order.")
            self.available = False

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5):
        if not candidates:
            return []
        if self.available and self.model is not None:
            try:
                pairs = [(query, c["record"].get("retrieval_text", "")) for c in candidates]
                scores = self.model.predict(pairs)
                for c, s in zip(candidates, scores):
                    c["rerank"] = float(s)
                candidates = sorted(candidates, key=lambda d: d["rerank"], reverse=True)
            except Exception as e:
                print(f"[reranker] predict failed: {e}")
                for c in candidates:
                    c["rerank"] = float(c.get("hybrid", 0.0))
        else:
            for c in candidates:
                c["rerank"] = float(c.get("hybrid", 0.0))
        # normalize rerank to 0..1 for display
        vals = [c["rerank"] for c in candidates]
        lo, hi = min(vals), max(vals)
        for c in candidates:
            c["relevance"] = 1.0 if hi - lo < 1e-9 else (c["rerank"] - lo) / (hi - lo)
        return candidates[:top_k]
