"""Hybrid clause retrieval: BM25 + dense (ChromaDB) -> Reciprocal Rank Fusion -> cross-encoder re-rank.

``mode`` lets the evaluation compare each stage: ``bm25``, ``dense``, ``hybrid`` (RRF) and
``hybrid_rerank`` (the default used by the product).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Literal

from app.ml.retrieval import bm25_index, dense_index
from app.ml.retrieval.clause_cache import ClauseRecord
from app.ml.retrieval.fusion import reciprocal_rank_fusion
from app.ml.retrieval.reranker import rerank_scores

Mode = Literal["bm25", "dense", "hybrid", "hybrid_rerank"]
CANDIDATES = 30
RERANK_POOL = 20
SOLO_TOP = 8  # each retriever's own top hits always reach the re-ranker


@dataclass
class Retrieved:
    clause: ClauseRecord
    score: float
    bm25: float | None = None
    bm25_rank: int | None = None
    dense: float | None = None
    dense_rank: int | None = None
    rrf: float | None = None
    rerank: float | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        clause = data.pop("clause")
        data["clause"] = {k: clause[k] for k in ("id", "ordinal", "clause_ref", "heading", "section_path",
                                                 "page_start", "page_end")}
        return data


@dataclass
class RetrievalResult:
    query: str
    mode: str
    items: list[Retrieved]
    timings_ms: dict[str, float] = field(default_factory=dict)

    @property
    def best_score(self) -> float:
        return max((i.score for i in self.items), default=0.0)


def retrieve(document_id: int, query: str, k: int = 6, mode: Mode = "hybrid_rerank",
             provider: str | None = None, extra_queries: list[str] | None = None) -> RetrievalResult:
    """Return the top-``k`` clauses of one document for ``query``.

    ``extra_queries`` (e.g. an English translation or sub-questions) are searched too and fused.
    """
    timings: dict[str, float] = {}
    queries = [query, *(extra_queries or [])]

    t = time.perf_counter()
    bm25_lists = [bm25_index.search(document_id, q, CANDIDATES) for q in queries] if mode != "dense" else []
    timings["bm25"] = round((time.perf_counter() - t) * 1000, 1)

    t = time.perf_counter()
    dense_lists = [dense_index.search(document_id, q, CANDIDATES, provider) for q in queries] if mode != "bm25" else []
    timings["dense"] = round((time.perf_counter() - t) * 1000, 1)

    by_ordinal: dict[int, Retrieved] = {}

    def entry(clause: ClauseRecord) -> Retrieved:
        if clause.ordinal not in by_ordinal:
            by_ordinal[clause.ordinal] = Retrieved(clause=clause, score=0.0)
        return by_ordinal[clause.ordinal]

    for results in bm25_lists:
        for rank, (clause, score) in enumerate(results, start=1):
            e = entry(clause)
            if e.bm25 is None or score > e.bm25:
                e.bm25, e.bm25_rank = round(score, 4), rank
    for results in dense_lists:
        for rank, (clause, score) in enumerate(results, start=1):
            e = entry(clause)
            if e.dense is None or score > e.dense:
                e.dense, e.dense_rank = round(score, 4), rank

    if mode == "bm25":
        ranked = sorted((e for e in by_ordinal.values() if e.bm25 is not None), key=lambda e: e.bm25, reverse=True)
        for e in ranked:
            e.score = e.bm25 or 0.0
        return RetrievalResult(query, mode, ranked[:k], timings)
    if mode == "dense":
        ranked = sorted((e for e in by_ordinal.values() if e.dense is not None), key=lambda e: e.dense, reverse=True)
        for e in ranked:
            e.score = e.dense or 0.0
        return RetrievalResult(query, mode, ranked[:k], timings)

    t = time.perf_counter()
    rankings = [[c.ordinal for c, _ in lst] for lst in (*bm25_lists, *dense_lists)]
    fused = reciprocal_rank_fusion(rankings, k=60)
    for ordinal, score in fused:
        by_ordinal[ordinal].rrf = round(score, 5)
    timings["fusion"] = round((time.perf_counter() - t) * 1000, 1)

    pool = [by_ordinal[o] for o, _ in fused]
    if mode == "hybrid":
        for e in pool:
            e.score = e.rrf or 0.0
        return RetrievalResult(query, mode, pool[:k], timings)

    t = time.perf_counter()
    # Re-rank the fused top candidates plus each retriever's own top hits, so a clause that only one
    # method finds (e.g. an exact keyword match) still gets a chance.
    chosen: dict[int, Retrieved] = {e.clause.ordinal: e for e in pool[:RERANK_POOL]}
    for results in (*bm25_lists, *dense_lists):
        for clause, _ in results[:SOLO_TOP]:
            chosen.setdefault(clause.ordinal, by_ordinal[clause.ordinal])
    pool = list(chosen.values())
    scores = rerank_scores(query, [e.clause.index_text for e in pool])
    if extra_queries:
        # Score against the English/sub-queries as well and keep the best view of each clause.
        for q in extra_queries:
            alt = rerank_scores(q, [e.clause.index_text for e in pool])
            scores = [max(a, b) for a, b in zip(scores, alt)]
    for e, s in zip(pool, scores):
        e.rerank = round(s, 4)
        # Blend: cross-encoder relevance first, fused rank as a tie-breaker.
        e.score = round(s + 0.001 * (e.rrf or 0.0) * 60, 4)
    pool.sort(key=lambda e: e.score, reverse=True)
    timings["rerank"] = round((time.perf_counter() - t) * 1000, 1)
    return RetrievalResult(query, mode, pool[:k], timings)
