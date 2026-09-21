"""Reciprocal Rank Fusion (Cormack et al.): combine ranked lists without calibrating their scores."""

from __future__ import annotations

from collections.abc import Hashable, Sequence


def reciprocal_rank_fusion(rankings: Sequence[Sequence[Hashable]], k: int = 60,
                           weights: Sequence[float] | None = None) -> list[tuple[Hashable, float]]:
    weights = weights or [1.0] * len(rankings)
    scores: dict[Hashable, float] = {}
    for ranking, weight in zip(rankings, weights):
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + weight / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
