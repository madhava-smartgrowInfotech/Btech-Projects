"""Full RAG pipeline orchestration with lazy singleton."""
import json
from pathlib import Path
import numpy as np
from app.config import settings
from app.rag.query_expansion import expand_query_hyde
from app.rag.embeddings import EmbeddingBackend
from app.rag.faiss_store import FaissStore
from app.rag.bm25_store import BM25Store
from app.rag.hybrid_retriever import fuse
from app.rag.reranker import Reranker
from app.rag.generator import Generator
from app.rag import safety as safety_mod

BASE = Path(__file__).resolve().parent.parent.parent
PROCESSED = BASE / "data" / "processed" / "knowledge_base.json"
FAISS_PATH = BASE / "data" / "index" / "faiss.index"
META_PATH = BASE / "data" / "index" / "records.json"
BM25_PATH = BASE / "data" / "index" / "bm25.json"

_pipeline = None

class Pipeline:
    def __init__(self):
        self.embeddings = EmbeddingBackend(settings.EMBEDDING_MODEL)
        self.faiss = FaissStore(FAISS_PATH, META_PATH)
        self.bm25 = BM25Store(BM25_PATH)
        self.reranker = Reranker(settings.RERANKER_MODEL)
        self.generator = Generator(settings.GENERATOR_MODEL)
        self.ready = False
        self._ensure_index()

    def _ensure_index(self):
        if self.faiss.load() and self.bm25.load():
            # ensure embedding fallback vectorizer fitted on loaded records
            if self.embeddings.mode == "tfidf" and self.embeddings.vectorizer is None:
                texts = [r.get("retrieval_text", "") for r in self.faiss.records]
                if texts:
                    self.embeddings.fit_fallback(texts)
            self.ready = True
            return
        self.rebuild()

    def rebuild(self):
        if not PROCESSED.exists():
            raise FileNotFoundError(f"Processed knowledge base missing: {PROCESSED}. Run scripts/prepare_data.py first.")
        records = json.loads(PROCESSED.read_text(encoding="utf-8"))
        texts = [r.get("retrieval_text", "") for r in records]
        if self.embeddings.mode == "tfidf":
            vecs = self.embeddings.fit_fallback(texts)
        else:
            vecs = self.embeddings.encode(texts)
        vecs = np.asarray(vecs, dtype=np.float32)
        self.faiss.build(vecs, records)
        self.bm25.build(records)
        self.ready = True

    def answer(self, raw_query: str, top_k: int | None = None) -> dict:
        top_k = top_k or settings.RETRIEVAL_TOP_K
        exp = expand_query_hyde(raw_query)
        combined = exp["combined"]
        qvec = self.embeddings.encode([combined])[0]
        sem_hits = self.faiss.search(qvec, k=settings.CANDIDATE_K)
        lex_hits = self.bm25.search(combined, k=settings.CANDIDATE_K)
        fused = fuse(sem_hits, lex_hits, settings.HYBRID_SEMANTIC_WEIGHT,
                     settings.HYBRID_LEXICAL_WEIGHT, k=settings.CANDIDATE_K)
        ranked = self.reranker.rerank(combined, fused, top_k=top_k)
        evidence = []
        for c in ranked:
            r = c["record"]
            evidence.append({
                "record_id": r.get("record_id", ""),
                "disease": r.get("disease", ""),
                "symptoms": r.get("symptoms", ""),
                "description": r.get("description", ""),
                "guidance": r.get("guidance", ""),
                "severity": r.get("severity", ""),
                "red_flags": r.get("red_flags", ""),
                "relevance": round(float(c.get("relevance", 0.0)), 3),
                "hybrid": round(float(c.get("hybrid", 0.0)), 4),
                "rerank": round(float(c.get("rerank", 0.0)), 4),
            })
        safe = safety_mod.check_safety(raw_query)
        answer, gen_by = self.generator.generate(exp["normalized"], ranked)
        answer = safety_mod.apply_safety_filter(answer)
        if safe["flag"] == "emergency":
            answer = safe["message"] + "\n\n" + answer
        top_condition = evidence[0]["disease"] if evidence else ""
        score = float(evidence[0]["relevance"]) if evidence else 0.0
        # user-friendly relevance label
        if score >= 0.66:
            label = "Strong match"
        elif score >= 0.33:
            label = "Moderate match"
        else:
            label = "Weak match"
        return {
            "answer": answer,
            "top_condition": top_condition,
            "evidence": evidence,
            "safety_flag": safe["flag"],
            "safety_message": safe["message"],
            "relevance_label": label,
            "retrieval_score": score,
            "generated_by": gen_by,
            "expanded": exp,
        }

def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline
