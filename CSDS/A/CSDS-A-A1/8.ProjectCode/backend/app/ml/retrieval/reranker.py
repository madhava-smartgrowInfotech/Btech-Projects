"""Cross-encoder re-ranking of fused candidates (ms-marco MiniLM, local CPU)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from app.ml.local_models import get_reranker


def rerank_scores(query: str, passages: Sequence[str]) -> list[float]:
    """Relevance probability (0-1) for each passage."""
    if not passages:
        return []
    logits = get_reranker().predict([(query, p[:2000]) for p in passages], batch_size=16,
                                    show_progress_bar=False, convert_to_numpy=True)
    return [1.0 / (1.0 + math.exp(-float(x))) for x in logits]
