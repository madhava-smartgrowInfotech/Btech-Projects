"""The Nuvara recommendation orchestrator.

Holds the in-memory state every intelligence surface reads from: the catalogue,
the three scoring agents, the live weight blend, and a short-lived store of
recommendation impressions that powers explainability and the feedback loop.

Scoring pipeline for one request:
  1. each agent produces a raw score over the whole catalogue
  2. a candidate pool is taken as the union of each agent's top slice
  3. scores are max-normalised inside that pool and blended by the live weights
  4. MMR re-ranking trades relevance against list novelty
  5. every surviving item is tagged with a rec_id and its full scoring record
"""

from __future__ import annotations

import threading
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import (
    DEFAULT_WEIGHTS,
    REC_CACHE_MAX,
    REC_CACHE_TTL_S,
    WEIGHT_FLOOR,
)
from ..models import Event, Product, StrategyState, User
from .collaborative import CollaborativeAgent, event_strength
from .content import ContentAgent
from .diversity import mmr_rerank
from .trending import TrendingAgent

AGENT_KEYS = ("collaborative", "content", "trending")
CANDIDATE_SLICE = 45


def normalise_weights(weights: dict) -> dict:
    """Clamp every lever above the floor and renormalise to sum to one."""
    cleaned = {}
    for key in ("collaborative", "content", "trending", "diversity"):
        value = float(weights.get(key, DEFAULT_WEIGHTS[key]))
        cleaned[key] = max(WEIGHT_FLOOR, min(1.0, value))
    total = sum(cleaned.values())
    return {k: round(v / total, 6) for k, v in cleaned.items()}


def _max_norm(vector: np.ndarray, pool: np.ndarray) -> np.ndarray:
    sub = vector[pool]
    peak = float(sub.max()) if sub.size else 0.0
    if peak <= 0:
        return np.zeros(sub.shape, dtype=np.float64)
    return np.clip(sub / peak, 0.0, 1.0).astype(np.float64)


class Orchestrator:
    def __init__(self):
        self.lock = threading.RLock()
        self.products: list[dict] = []
        self.product_by_id: dict[int, dict] = {}
        self.index_by_id: dict[int, int] = {}
        self.categories: list[str] = []
        self.category_ids = np.zeros(0, dtype=np.int64)
        self.prices = np.zeros(0, dtype=np.float64)
        self.in_stock = np.zeros(0, dtype=bool)

        self.users: list[dict] = []
        self.user_by_id: dict[str, dict] = {}

        self.collaborative: CollaborativeAgent | None = None
        self.content: ContentAgent | None = None
        self.trending: TrendingAgent | None = None

        self.weights: dict = dict(DEFAULT_WEIGHTS)
        self.step: int = 0

        # Anonymous sessions accumulate their own interaction vector.
        self.session_vectors: dict[str, np.ndarray] = {}
        self.session_carts: dict[str, list[int]] = {}
        self.session_queries: dict[str, str] = {}

        self.impressions: "OrderedDict[str, dict]" = OrderedDict()
        self.ready = False

    # ------------------------------------------------------------------ build

    def build(self, db: Session) -> None:
        """Load catalogue, population and behaviour stream, then fit every agent."""
        with self.lock:
            rows = db.execute(select(Product).order_by(Product.id)).scalars().all()
            self.products = [self._product_dict(p) for p in rows]
            self.product_by_id = {p["id"]: p for p in self.products}
            self.index_by_id = {p["id"]: i for i, p in enumerate(self.products)}
            self.categories = sorted({p["category"] for p in self.products})
            cat_lookup = {c: i for i, c in enumerate(self.categories)}
            self.category_ids = np.array(
                [cat_lookup[p["category"]] for p in self.products], dtype=np.int64
            )
            self.prices = np.array([p["price"] for p in self.products], dtype=np.float64)
            self.in_stock = np.array([p["stock"] > 0 for p in self.products], dtype=bool)

            user_rows = db.execute(select(User).order_by(User.id)).scalars().all()
            self.users = [
                {
                    "id": u.id,
                    "name": u.name,
                    "segment": u.segment,
                    "avatar_seed": u.avatar_seed,
                    "blurb": u.blurb,
                    "is_demo_persona": u.is_demo_persona,
                    "activity_level": u.activity_level,
                    "latent": u.latent,
                }
                for u in user_rows
            ]
            self.user_by_id = {u["id"]: u for u in self.users}

            n = len(self.products)
            self.collaborative = CollaborativeAgent(n, [u["id"] for u in self.users])
            self.content = ContentAgent(self.products)
            self.trending = TrendingAgent(
                n, self.categories, [p["category"] for p in self.products]
            )

            events = db.execute(select(Event).order_by(Event.id)).scalars().all()
            # Anchor the recency window on the freshest interaction, so demand
            # ranking stays meaningful however long the database has existed.
            newest = max((e.created_at for e in events if e.created_at), default=None)
            self.trending.reference_time = max(
                [t for t in (newest, datetime.utcnow()) if t is not None]
            )
            for ev in events:
                self._ingest(ev.user_id, ev.session_id, ev.product_id, ev.type, ev.value, ev.created_at)

            self.collaborative.fit()
            self.trending.fit()

            state = db.get(StrategyState, 1)
            if state is not None:
                self.weights = normalise_weights(state.weights)
                self.step = state.step
            self.ready = True

    @staticmethod
    def _product_dict(p: Product) -> dict:
        return {
            "id": p.id,
            "slug": p.slug,
            "name": p.name,
            "category": p.category,
            "subcategory": p.subcategory,
            "price": p.price,
            "compare_at_price": p.compare_at_price,
            "currency": p.currency,
            "description": p.description,
            "short_description": p.short_description,
            "image_seed": p.image_seed,
            "colorway": p.colorway,
            "rating": p.rating,
            "review_count": p.review_count,
            "stock": p.stock,
            "tags": list(p.tags or []),
            "attributes": dict(p.attributes or {}),
            "created_at": p.created_at,
        }

    # ------------------------------------------------------------ ingestion

    def _ingest(self, user_id, session_id, product_id, etype, value, created_at) -> None:
        if product_id is None:
            return
        idx = self.index_by_id.get(product_id)
        if idx is None:
            return
        strength = event_strength(etype, value)

        if user_id and user_id in self.user_by_id:
            self.collaborative.add_interaction(user_id, idx, strength)
        if session_id:
            vec = self.session_vectors.setdefault(
                session_id, np.zeros(len(self.products), dtype=np.float32)
            )
            vec[idx] += strength
            if etype == "add_to_cart":
                cart = self.session_carts.setdefault(session_id, [])
                if idx not in cart:
                    cart.append(idx)
            if etype == "purchase":
                cart = self.session_carts.get(session_id, [])
                if idx in cart:
                    cart.remove(idx)

        ts = created_at or datetime.utcnow()
        self.trending.add_interaction(idx, strength, ts)

    def record_event(
        self,
        *,
        user_id: str | None,
        session_id: str,
        product_id: int | None,
        etype: str,
        value: float | None,
        query: str | None,
        created_at: datetime,
    ) -> None:
        """Fold a live event into every agent so the next request reflects it."""
        with self.lock:
            if etype == "search" and query:
                self.session_queries[session_id] = query
            self._ingest(user_id, session_id, product_id, etype, value, created_at)
            if product_id is not None:
                # The neighbourhood model is small enough to refit per event,
                # which keeps personalisation genuinely live.
                self.collaborative.fit()
                self.trending.fit()

    # ---------------------------------------------------------- score vectors

    def interaction_vector(self, user_id: str | None, session_id: str | None) -> np.ndarray:
        """Combined history for a shopper: persisted profile plus live session."""
        vec = self.collaborative.user_vector(user_id)
        if session_id and session_id in self.session_vectors:
            vec = vec + self.session_vectors[session_id]
        return vec

    def agent_scores(
        self,
        *,
        interaction_vector: np.ndarray,
        context: str,
        anchor_idx: int | None,
        cart_indices: list[int],
        query: str | None,
    ) -> dict[str, np.ndarray]:
        """Raw, un-normalised score vector from each agent for the given context."""
        collab = self.collaborative
        content = self.content
        trending = self.trending

        if context == "product" and anchor_idx is not None:
            c_scores = collab.also_bought(anchor_idx)
            if np.any(interaction_vector):
                c_scores = 0.72 * c_scores + 0.28 * _unit(collab.score_from_vector(interaction_vector))
            t_scores = trending.score(self.products[anchor_idx]["category"])
            ct_scores = content.score_for_product(anchor_idx)

        elif context == "cart" and cart_indices:
            c_scores = np.zeros(len(self.products), dtype=np.float32)
            ct_scores = np.zeros(len(self.products), dtype=np.float32)
            for idx in cart_indices:
                c_scores = c_scores + collab.also_bought(idx)
                ct_scores = ct_scores + content.score_for_product(idx)
            # Complements, not duplicates: damp anything in the same subcategory
            # as something already in the basket.
            cart_subs = {self.products[i]["subcategory"] for i in cart_indices}
            damp = np.array(
                [0.35 if p["subcategory"] in cart_subs else 1.0 for p in self.products],
                dtype=np.float32,
            )
            ct_scores = ct_scores * damp
            c_scores = c_scores * damp
            t_scores = trending.score()

        elif context == "search" and query:
            ct_scores = content.score_for_query(query)
            c_scores = collab.score_from_vector(interaction_vector)
            t_scores = trending.score()
            # A search feed stays anchored to the query: anything with no
            # lexical overlap is pushed out of contention.
            relevant = ct_scores > 0.01
            if relevant.any():
                c_scores = c_scores * relevant
                t_scores = t_scores * relevant

        else:  # home, or any context that lost its anchor
            c_scores = collab.score_from_vector(interaction_vector)
            ct_scores = content.score_from_vector(interaction_vector)
            t_scores = trending.score()

        return {
            "collaborative": np.asarray(c_scores, dtype=np.float64),
            "content": np.asarray(ct_scores, dtype=np.float64),
            "trending": np.asarray(t_scores, dtype=np.float64),
        }

    def candidate_pool(
        self, raw: dict[str, np.ndarray], exclude: set[int], limit: int
    ) -> np.ndarray:
        pool: set[int] = set()
        for vector in raw.values():
            if not np.any(vector):
                continue
            order = np.argsort(-vector)[: CANDIDATE_SLICE]
            pool.update(int(i) for i in order if vector[i] > 0)

        if len(pool) < limit * 3:
            # Cold start: back-fill with the strongest catalogue momentum.
            fallback = np.argsort(-self.trending.scores)[: limit * 5]
            pool.update(int(i) for i in fallback)

        pool -= exclude
        pool = {i for i in pool if self.in_stock[i]}
        if not pool:
            pool = {int(i) for i in np.argsort(-self.trending.scores)[:limit] if self.in_stock[i]}
        return np.array(sorted(pool), dtype=np.int64)

    # ------------------------------------------------------------- recommend

    def recommend(
        self,
        *,
        user_id: str | None = None,
        session_id: str | None = None,
        context: str = "home",
        product_id: int | None = None,
        query: str | None = None,
        limit: int = 12,
        weights: dict | None = None,
        register: bool = True,
    ) -> dict:
        with self.lock:
            weights = normalise_weights(weights or self.weights)
            anchor_idx = self.index_by_id.get(product_id) if product_id is not None else None
            cart_indices = list(self.session_carts.get(session_id or "", []))
            if not cart_indices and user_id:
                cart_indices = self._recent_cart_for_user(user_id)
            if context == "search" and not query and session_id:
                query = self.session_queries.get(session_id)

            interaction = self.interaction_vector(user_id, session_id)
            raw = self.agent_scores(
                interaction_vector=interaction,
                context=context,
                anchor_idx=anchor_idx,
                cart_indices=cart_indices,
                query=query,
            )

            exclude = set()
            if anchor_idx is not None:
                exclude.add(anchor_idx)
            exclude.update(cart_indices if context == "cart" else [])

            pool = self.candidate_pool(raw, exclude, limit)
            if pool.size == 0:
                return {
                    "strategy": {"name": self._strategy_name(weights), "weights": weights},
                    "items": [],
                }

            normalised = {key: _max_norm(raw[key], pool) for key in AGENT_KEYS}
            agent_sum = weights["collaborative"] + weights["content"] + weights["trending"]
            blended = (
                weights["collaborative"] * normalised["collaborative"]
                + weights["content"] * normalised["content"]
                + weights["trending"] * normalised["trending"]
            ) / agent_sum

            relevance = {int(pool[i]): float(blended[i]) for i in range(pool.size)}
            pool_position = {int(pool[i]): i for i in range(pool.size)}

            selected = mmr_rerank(
                candidate_indices=[int(i) for i in pool],
                relevance=relevance,
                content_sim=self.content.item_sim,
                category_ids=self.category_ids,
                diversity_weight=weights["diversity"],
                limit=limit,
            )

            history_signal = float(min(1.0, interaction.sum() / 70.0))
            items = []
            for rank, (idx, final_score, bonus) in enumerate(selected):
                pos = pool_position[idx]
                per_agent = {k: float(normalised[k][pos]) for k in AGENT_KEYS}
                contributions = {
                    k: float(weights[k] * per_agent[k] / agent_sum) for k in AGENT_KEYS
                }
                confidence = self._confidence(
                    per_agent, relevance[idx], blended, history_signal
                )
                reason, drivers = self._reason(
                    idx=idx,
                    context=context,
                    anchor_idx=anchor_idx,
                    cart_indices=cart_indices,
                    query=query,
                    interaction=interaction,
                    contributions=contributions,
                )

                record = {
                    "created_at": datetime.now(timezone.utc),
                    "product_idx": idx,
                    "product_id": self.products[idx]["id"],
                    "user_id": user_id,
                    "session_id": session_id,
                    "context": context,
                    "weights": dict(weights),
                    "raw": {k: float(raw[k][idx]) for k in AGENT_KEYS},
                    "normalised": per_agent,
                    "contributions": contributions,
                    "diversity_bonus": float(bonus),
                    "base_score": float(relevance[idx]),
                    "score": float(final_score),
                    "confidence": confidence,
                    "reason": reason,
                    "drivers": drivers,
                    "anchor_idx": anchor_idx,
                    "rank": rank,
                    "interaction": interaction.copy(),
                }
                rec_id = f"rec_{uuid.uuid4().hex[:18]}"
                if register:
                    self._remember(rec_id, record)

                items.append(
                    {
                        "product": self.products[idx],
                        "rec_id": rec_id,
                        "score": round(float(final_score), 5),
                        "base_score": round(float(relevance[idx]), 5),
                        "reason": reason,
                        "agents": {
                            "collaborative": round(per_agent["collaborative"], 5),
                            "content": round(per_agent["content"], 5),
                            "trending": round(per_agent["trending"], 5),
                            "diversity_bonus": round(float(bonus), 5),
                        },
                        "confidence": round(confidence, 4),
                    }
                )

            return {
                "strategy": {"name": self._strategy_name(weights), "weights": weights},
                "items": items,
            }

    def _recent_cart_for_user(self, user_id: str) -> list[int]:
        """Treat the shopper's strongest add-to-cart signals as a standing basket."""
        vec = self.collaborative.user_vector(user_id)
        if not np.any(vec):
            return []
        order = np.argsort(-vec)[:3]
        return [int(i) for i in order if vec[i] >= 3.0]

    def _strategy_name(self, weights: dict) -> str:
        lead = max(AGENT_KEYS, key=lambda k: weights[k])
        label = {
            "collaborative": "Neighbourhood-led",
            "content": "Catalogue-affinity-led",
            "trending": "Momentum-led",
        }[lead]
        if weights["diversity"] >= 0.25:
            return f"{label} · wide spread"
        if weights["diversity"] <= 0.09:
            return f"{label} · tight focus"
        return f"{label} blend"

    @staticmethod
    def _confidence(
        per_agent: dict, base_score: float, blended: np.ndarray, history_signal: float
    ) -> float:
        """Confidence from three observable quantities, not a constant.

        How much history backs the shopper, how far this item sits above the
        rest of the candidate pool, and how strongly the agents agree on it.
        """
        spread = float(blended.max() - blended.min()) or 1e-6
        margin = float((base_score - float(np.median(blended))) / spread)
        margin = max(0.0, min(1.0, margin))
        values = np.array(list(per_agent.values()), dtype=np.float64)
        agreement = 1.0 - min(1.0, float(values.std()) / 0.45)
        raw = 0.26 + 0.30 * history_signal + 0.26 * margin + 0.18 * agreement
        return float(max(0.05, min(0.99, raw)))

    def _reason(
        self,
        *,
        idx: int,
        context: str,
        anchor_idx: int | None,
        cart_indices: list[int],
        query: str | None,
        interaction: np.ndarray,
        contributions: dict,
    ) -> tuple[str, dict]:
        """Human-readable justification plus the evidence that produced it."""
        product = self.products[idx]
        collab_drivers = self.collaborative.top_drivers(interaction, idx, k=3)
        content_drivers = self.content.top_drivers(interaction, idx, k=3)
        drivers = {"collaborative": collab_drivers, "content": content_drivers}

        if context == "product" and anchor_idx is not None:
            anchor = self.products[anchor_idx]
            if contributions["collaborative"] >= contributions["content"]:
                return f"Shoppers who viewed the {anchor['name']} also bought this", drivers
            return f"Closely matched to the {anchor['name']}", drivers

        if context == "cart" and cart_indices:
            partner = self.products[cart_indices[0]]
            return f"Pairs with the {partner['name']} in your basket", drivers

        if context == "search" and query:
            return f"Strong match for “{query}” in {product['category']}", drivers

        lead = max(contributions, key=contributions.get)
        if lead == "collaborative" and collab_drivers:
            src = self.products[collab_drivers[0][0]]
            return f"Because you viewed the {src['name']}", drivers
        if lead == "content" and content_drivers:
            src = self.products[content_drivers[0][0]]
            shared = self.content.shared_terms(content_drivers[0][0], idx, k=1)
            if shared:
                return f"Shares {shared[0]} with the {src['name']} you looked at", drivers
            return f"Similar to the {src['name']} you looked at", drivers
        if lead == "trending":
            percentile = self.trending.rank_within_category(idx)
            if percentile > 0.85:
                return f"Trending in {product['category']} this week", drivers
            return f"Picking up momentum in {product['subcategory']}", drivers

        return f"Highly rated in {product['category']}", drivers

    # ------------------------------------------------------- impression store

    def _remember(self, rec_id: str, record: dict) -> None:
        self.impressions[rec_id] = record
        self._purge()

    def _purge(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=REC_CACHE_TTL_S)
        while self.impressions:
            oldest_key = next(iter(self.impressions))
            oldest = self.impressions[oldest_key]
            if oldest["created_at"] < cutoff or len(self.impressions) > REC_CACHE_MAX:
                self.impressions.pop(oldest_key)
            else:
                break

    def get_impression(self, rec_id: str) -> dict | None:
        with self.lock:
            return self.impressions.get(rec_id)

    # ------------------------------------------------------------ weight state

    def set_weights(self, db: Session, weights: dict, trigger_action: str) -> dict:
        from ..models import WeightHistory

        with self.lock:
            self.weights = normalise_weights(weights)
            self.step += 1
            state = db.get(StrategyState, 1)
            if state is None:
                state = StrategyState(id=1, weights=dict(self.weights), step=self.step)
                db.add(state)
            else:
                state.weights = dict(self.weights)
                state.step = self.step
                state.updated_at = datetime.utcnow()
            db.add(
                WeightHistory(
                    step=self.step,
                    weights=dict(self.weights),
                    trigger_action=trigger_action,
                    created_at=datetime.utcnow(),
                )
            )
            db.commit()
            return dict(self.weights)


def _unit(vector: np.ndarray) -> np.ndarray:
    peak = float(np.max(vector)) if vector.size else 0.0
    if peak <= 0:
        return np.zeros_like(vector, dtype=np.float64)
    return (vector / peak).astype(np.float64)


orchestrator = Orchestrator()
