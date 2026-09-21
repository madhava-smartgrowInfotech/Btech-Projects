"""BM25 keyword search per document (rank-bm25), built lazily from the cached clauses."""

from __future__ import annotations

import threading

import numpy as np
from rank_bm25 import BM25Okapi

from app.ml.retrieval.clause_cache import ClauseRecord, load_clauses
from app.ml.retrieval.text import expand_query, tokenize

_lock = threading.Lock()
_indexes: dict[int, tuple[int, BM25Okapi]] = {}


def _index_for(document_id: int, clauses: list[ClauseRecord]) -> BM25Okapi:
    key = id(clauses)
    cached = _indexes.get(document_id)
    if cached and cached[0] == key:
        return cached[1]
    corpus = [tokenize(c.index_text) or ["_"] for c in clauses]
    index = BM25Okapi(corpus, k1=1.4, b=0.7)
    with _lock:
        _indexes[document_id] = (key, index)
    return index


def search(document_id: int, query: str, k: int = 30, expand: bool = True) -> list[tuple[ClauseRecord, float]]:
    clauses = load_clauses(document_id)
    if not clauses:
        return []
    index = _index_for(document_id, clauses)
    tokens = tokenize(expand_query(query) if expand else query)
    if not tokens:
        return []
    scores = index.get_scores(tokens)
    order = np.argsort(scores)[::-1][:k]
    return [(clauses[i], float(scores[i])) for i in order if scores[i] > 0]


def invalidate(document_id: int) -> None:
    with _lock:
        _indexes.pop(document_id, None)
