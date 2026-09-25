"""Maximal Marginal Relevance re-ranking.

The blended relevance score is traded off against similarity to everything
already selected, so a list cannot fill up with eight variations of one
product. The live `diversity` weight is the trade-off strength: at 0 the list
is pure relevance order, at 1 it is driven almost entirely by novelty.

Written against numpy arrays with an incrementally maintained max-similarity
vector so the digital twin can run it tens of thousands of times per request.
"""

from __future__ import annotations

import numpy as np


def mmr_rerank(
    candidate_indices: list[int],
    relevance: dict[int, float],
    content_sim: np.ndarray,
    category_ids: np.ndarray,
    diversity_weight: float,
    limit: int,
) -> list[tuple[int, float, float]]:
    """Greedily select up to `limit` items.

    Returns (product_index, final_score, diversity_bonus) where the bonus is the
    novelty adjustment MMR applied to that item: zero for the first pick, and
    increasingly negative for items that echo something already in the list.
    """
    if not candidate_indices:
        return []

    lam = float(min(0.95, max(0.0, diversity_weight)))
    pool = np.asarray(candidate_indices, dtype=np.int64)
    base = np.array([relevance.get(int(i), 0.0) for i in pool], dtype=np.float64)

    n_categories = int(category_ids.max()) + 1 if category_ids.size else 1
    pool_categories = category_ids[pool]

    # Similarity of each remaining candidate to the closest already-picked item.
    max_sim = np.zeros(pool.size, dtype=np.float64)
    category_counts = np.zeros(n_categories, dtype=np.float64)

    alive = np.ones(pool.size, dtype=bool)
    selected: list[tuple[int, float, float]] = []

    for step in range(min(limit, pool.size)):
        if step == 0:
            penalty = np.zeros(pool.size, dtype=np.float64)
        else:
            repeat = category_counts[pool_categories] / float(step)
            penalty = 0.55 * max_sim + 0.45 * repeat

        value = (1.0 - lam) * base - lam * penalty
        value = np.where(alive, value, -np.inf)

        pick = int(np.argmax(value))
        product_idx = int(pool[pick])
        final_score = float(value[pick])
        # The bonus isolates the novelty term, so it reads as "what diversity
        # re-ranking did to this item" rather than including the relevance
        # rescaling that applies uniformly across the list.
        bonus = float(-lam * penalty[pick])
        selected.append((product_idx, final_score, bonus))

        alive[pick] = False
        category_counts[pool_categories[pick]] += 1.0
        max_sim = np.maximum(max_sim, content_sim[product_idx, pool].astype(np.float64))

    return selected
