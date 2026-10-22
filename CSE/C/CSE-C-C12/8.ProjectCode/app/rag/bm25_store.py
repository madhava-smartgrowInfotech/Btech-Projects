"""BM25 lexical store."""
import json
import re
from pathlib import Path
from rank_bm25 import BM25Okapi

def _tok(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())

class BM25Store:
    def __init__(self, save_path: Path):
        self.save_path = Path(save_path)
        self.records: list[dict] = []
        self.bm25: BM25Okapi | None = None
        self.corpus_tokens: list[list[str]] = []

    def build(self, records: list[dict], text_key: str = "retrieval_text"):
        self.records = records
        self.corpus_tokens = [_tok(r.get(text_key, "")) for r in records]
        self.bm25 = BM25Okapi(self.corpus_tokens)
        self.save(text_key)

    def save(self, text_key: str = "retrieval_text"):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"records": self.records, "corpus": [" ".join(t) for t in self.corpus_tokens], "text_key": text_key}
        self.save_path.write_text(json.dumps(payload), encoding="utf-8")

    def load(self) -> bool:
        try:
            if not self.save_path.exists():
                return False
            payload = json.loads(self.save_path.read_text(encoding="utf-8"))
            self.records = payload["records"]
            self.corpus_tokens = [c.split() for c in payload["corpus"]]
            self.bm25 = BM25Okapi(self.corpus_tokens)
            return True
        except Exception as e:
            print(f"[bm25] load failed: {e}")
            return False

    def search(self, query: str, k: int = 15):
        if self.bm25 is None:
            raise RuntimeError("BM25 not loaded")
        scores = self.bm25.get_scores(_tok(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [(float(scores[i]), self.records[i], i) for i in order]
