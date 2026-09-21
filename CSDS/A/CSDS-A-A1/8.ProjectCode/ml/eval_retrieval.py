"""Retrieval ablation: does the expected clause appear in the top results for each method?

Methods: BM25 only, dense (MiniLM + ChromaDB) only, hybrid (Reciprocal Rank Fusion) and
hybrid + cross-encoder re-rank (the product's default). No API calls.
"""

from __future__ import annotations

import time
from typing import Any

from ml import common  # noqa: F401
from ml.metrics import evidence_recall_at_k, latency_stats, relevance_flags, retrieval_summary

MODES = ["bm25", "dense", "hybrid", "hybrid_rerank"]


def run(doc_ids: dict[str, int], items: list[dict[str, Any]], log=print) -> tuple[dict, list[dict]]:  # noqa: ANN001
    from app.ml.retrieval.hybrid import retrieve

    answerable = [i for i in items if i.get("answerable") and i.get("evidence")]
    per_mode: dict[str, list[dict]] = {m: [] for m in MODES}
    times: dict[str, list[float]] = {m: [] for m in MODES}
    predictions: list[dict] = []
    for item in answerable:
        doc_id = doc_ids[item["policy"]]
        row: dict[str, Any] = {"id": item["id"], "question": item["question"]}
        for mode in MODES:
            start = time.perf_counter()
            result = retrieve(doc_id, item["question"], k=10, mode=mode)
            times[mode].append((time.perf_counter() - start) * 1000)
            texts = [r.clause.text for r in result.items]
            flags = relevance_flags(texts, item["evidence"])
            per_mode[mode].append({"flags": flags, "recall@5": evidence_recall_at_k(texts, item["evidence"], 5)})
            row[mode] = {"top5": [r.clause.ordinal for r in result.items[:5]], "first_hit": (flags.index(True) + 1)
                         if True in flags else None}
        predictions.append(row)
        log(f"retrieval {item['id']}: " + " ".join(f"{m}={row[m]['first_hit']}" for m in MODES))
    metrics = {m: retrieval_summary(per_mode[m]) for m in MODES}
    metrics["latency_ms"] = {m: latency_stats(times[m]) for m in MODES}
    return metrics, predictions
