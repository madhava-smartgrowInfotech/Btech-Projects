"""Trending agent.

Recency-weighted popularity over the behaviour stream. Every interaction
contributes its event strength decayed by an exponential half-life, so a burst
of activity this week outweighs a steady trickle from two months ago. Scores
are kept both globally and per category so a product page or category feed can
ask the narrower question.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np

HALF_LIFE_DAYS = 12.0


class TrendingAgent:
    def __init__(self, n_products: int, categories: list[str], product_categories: list[str]):
        self.n_products = n_products
        self.categories = categories
        self.product_categories = product_categories
        self.raw = np.zeros(n_products, dtype=np.float64)
        self.scores = np.zeros(n_products, dtype=np.float32)
        self.category_scores: dict[str, np.ndarray] = {}
        self.reference_time = datetime.utcnow()

    def add_interaction(self, product_idx: int, strength: float, timestamp: datetime) -> None:
        age_days = max(0.0, (self.reference_time - timestamp).total_seconds() / 86400.0)
        self.raw[product_idx] += strength * (0.5 ** (age_days / HALF_LIFE_DAYS))

    def fit(self) -> None:
        peak = self.raw.max()
        self.scores = (self.raw / peak if peak > 0 else self.raw).astype(np.float32)

        self.category_scores = {}
        for category in self.categories:
            mask = np.array([c == category for c in self.product_categories])
            vec = np.zeros(self.n_products, dtype=np.float32)
            within = self.raw * mask
            top = within.max()
            if top > 0:
                vec = (within / top).astype(np.float32)
            self.category_scores[category] = vec

    def score(self, category: str | None = None) -> np.ndarray:
        if category and category in self.category_scores:
            return self.category_scores[category].copy()
        return self.scores.copy()

    def rank_within_category(self, product_idx: int) -> float:
        """Percentile of this product's momentum inside its own category, 0-1."""
        category = self.product_categories[product_idx]
        peers = [i for i, c in enumerate(self.product_categories) if c == category]
        if not peers:
            return 0.0
        values = self.raw[peers]
        return float((values < self.raw[product_idx]).mean())
