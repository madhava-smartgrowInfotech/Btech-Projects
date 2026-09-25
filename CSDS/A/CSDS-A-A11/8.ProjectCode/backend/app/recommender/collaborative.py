"""Collaborative filtering agent.

Builds a shopper x product interaction matrix weighted by event strength,
then derives item-item cosine similarity. A shopper is scored by multiplying
their own interaction row through that similarity matrix, which is the
classic item-based neighbourhood formulation.
"""

from __future__ import annotations

import numpy as np

EVENT_STRENGTH = {
    "view": 1.0,
    "click": 2.0,
    "search": 0.4,
    "add_to_cart": 3.0,
    "purchase": 5.0,
    "review": 4.0,
}


def event_strength(event_type: str, value: float | None) -> float:
    """A rating event contributes its own star value; everything else is fixed."""
    if event_type == "rating":
        return float(value) if value is not None else 3.0
    return EVENT_STRENGTH.get(event_type, 1.0)


class CollaborativeAgent:
    def __init__(self, n_products: int, user_ids: list[str]):
        self.n_products = n_products
        self.user_ids = list(user_ids)
        self.user_index = {u: i for i, u in enumerate(self.user_ids)}
        self.matrix = np.zeros((len(self.user_ids), n_products), dtype=np.float32)
        self.item_sim = np.zeros((n_products, n_products), dtype=np.float32)

    def add_interaction(self, user_id: str, product_idx: int, strength: float) -> None:
        row = self.user_index.get(user_id)
        if row is None:
            # Grow the matrix for a shopper the population did not contain.
            self.user_index[user_id] = len(self.user_ids)
            self.user_ids.append(user_id)
            self.matrix = np.vstack(
                [self.matrix, np.zeros((1, self.n_products), dtype=np.float32)]
            )
            row = self.user_index[user_id]
        self.matrix[row, product_idx] += strength

    def fit(self) -> None:
        """Recompute item-item cosine similarity from the current matrix."""
        norms = np.linalg.norm(self.matrix, axis=0, keepdims=True)
        norms[norms == 0] = 1.0
        normalised = self.matrix / norms
        sim = normalised.T @ normalised
        np.fill_diagonal(sim, 0.0)
        self.item_sim = sim.astype(np.float32)

    def user_vector(self, user_id: str | None) -> np.ndarray:
        row = self.user_index.get(user_id) if user_id else None
        if row is None:
            return np.zeros(self.n_products, dtype=np.float32)
        return self.matrix[row].copy()

    def score_from_vector(self, interaction_vector: np.ndarray) -> np.ndarray:
        """Multiply an interaction vector through the item similarity matrix."""
        if not np.any(interaction_vector):
            return np.zeros(self.n_products, dtype=np.float32)
        scores = interaction_vector @ self.item_sim
        # Do not re-recommend what the shopper already engaged with heavily.
        scores = np.where(interaction_vector > 4.5, scores * 0.25, scores)
        return scores.astype(np.float32)

    def score_for_user(self, user_id: str | None) -> np.ndarray:
        return self.score_from_vector(self.user_vector(user_id))

    def also_bought(self, product_idx: int) -> np.ndarray:
        """Items co-engaged with a given product."""
        return self.item_sim[product_idx].copy()

    def top_drivers(self, interaction_vector: np.ndarray, product_idx: int, k: int = 3):
        """Which of the shopper's past items most drove this candidate's score."""
        contributions = interaction_vector * self.item_sim[:, product_idx]
        order = np.argsort(-contributions)[:k]
        return [(int(i), float(contributions[i])) for i in order if contributions[i] > 1e-6]
