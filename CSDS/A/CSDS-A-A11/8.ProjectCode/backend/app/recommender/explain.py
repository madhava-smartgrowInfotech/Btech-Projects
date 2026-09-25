"""Explainability layer.

Reconstructs why a specific recommendation impression was produced, using the
scoring record captured at the moment the list was built. Nothing here is
re-derived approximately: the weights, raw agent scores and contributions are
exactly the numbers the orchestrator used for that rec_id.
"""

from __future__ import annotations

import numpy as np

from ..seed import affinity
from .orchestrator import AGENT_KEYS, Orchestrator

AGENT_LABELS = {
    "collaborative": "Neighbourhood",
    "content": "Catalogue affinity",
    "trending": "Momentum",
}


def _narrative(agent: str, engine: Orchestrator, record: dict) -> str:
    weight = record["weights"][agent]
    normalised = record["normalised"][agent]
    share = _share(record)[agent]
    product = engine.products[record["product_idx"]]

    if agent == "collaborative":
        drivers = record["drivers"].get("collaborative") or []
        if drivers:
            src = engine.products[drivers[0][0]]
            return (
                f"Shoppers with an overlapping history to yours engaged with both this and "
                f"the {src['name']}. That co-engagement supplied {share:.0%} of the final score "
                f"at a {weight:.0%} agent weight."
            )
        return (
            f"There was little neighbourhood signal for this pick, so the agent returned "
            f"{normalised:.2f} of its possible score and contributed {share:.0%}."
        )

    if agent == "content":
        drivers = record["drivers"].get("content") or []
        if drivers:
            src = engine.products[drivers[0][0]]
            terms = engine.content.shared_terms(drivers[0][0], record["product_idx"], k=3)
            joined = ", ".join(terms) if terms else "the same category language"
            return (
                f"The TF-IDF profile built from what you have browsed overlaps this listing on "
                f"{joined}, closest to the {src['name']}. That match carried {share:.0%} of the score."
            )
        return (
            f"Matched against the {product['category']} vocabulary rather than your own history, "
            f"scoring {normalised:.2f} and contributing {share:.0%}."
        )

    percentile = engine.trending.rank_within_category(record["product_idx"])
    return (
        f"Recency-weighted demand puts this in the {percentile:.0%} percentile of "
        f"{product['category']}. At a {weight:.0%} momentum weight that is {share:.0%} of the score."
    )


def _share(record: dict) -> dict:
    total = sum(record["contributions"].values()) or 1e-9
    return {k: record["contributions"][k] / total for k in AGENT_KEYS}


def _headline(engine: Orchestrator, record: dict) -> str:
    product = engine.products[record["product_idx"]]
    shares = _share(record)
    lead = max(shares, key=shares.get)
    confidence = record["confidence"]
    bonus = record["diversity_bonus"]

    base = (
        f"{AGENT_LABELS[lead]} drove {shares[lead]:.0%} of the score for the {product['name']}, "
        f"ranked #{record['rank'] + 1} at {confidence:.0%} confidence."
    )
    if bonus < -0.02:
        return base + " Diversity re-ranking moved it down to keep the list spread across categories."
    if record["rank"] > 0 and bonus > -0.005:
        return base + " It survived diversity re-ranking without being penalised for repetition."
    return base


def _similar_because(engine: Orchestrator, record: dict, k: int = 4) -> list[dict]:
    """The products that most drove the neighbourhood and affinity scores."""
    target = record["product_idx"]
    seen: set[int] = set()
    out: list[dict] = []

    for src_idx, contribution in record["drivers"].get("collaborative", []):
        if src_idx in seen or src_idx == target:
            continue
        seen.add(src_idx)
        similarity = float(engine.collaborative.item_sim[src_idx, target])
        out.append(
            {
                "product": engine.products[src_idx],
                "similarity": round(similarity, 4),
                "shared_signal": "Bought and browsed together by shoppers with your history",
            }
        )

    for src_idx, similarity in record["drivers"].get("content", []):
        if src_idx in seen or src_idx == target:
            continue
        seen.add(src_idx)
        terms = engine.content.shared_terms(src_idx, target, k=3)
        signal = ", ".join(terms) if terms else engine.products[target]["category"]
        out.append(
            {
                "product": engine.products[src_idx],
                "similarity": round(float(similarity), 4),
                "shared_signal": f"Shared listing signals: {signal}",
            }
        )

    if not out:
        # No personal history yet: fall back to the nearest catalogue neighbours.
        neighbours = np.argsort(-engine.content.item_sim[target])[:k]
        for src_idx in neighbours:
            src_idx = int(src_idx)
            terms = engine.content.shared_terms(src_idx, target, k=3)
            out.append(
                {
                    "product": engine.products[src_idx],
                    "similarity": round(float(engine.content.item_sim[src_idx, target]), 4),
                    "shared_signal": f"Nearest catalogue match on: {', '.join(terms) or 'category'}",
                }
            )

    out.sort(key=lambda r: -r["similarity"])
    return out[:k]


def _audience_fit(engine: Orchestrator, record: dict) -> dict:
    """Which shopper segment over-indexes on this product, and by how much.

    Computed against the hidden latent taste vectors of the whole synthetic
    population, so it moves with the catalogue rather than being a label.
    """
    product = engine.products[record["product_idx"]]
    scores: list[float] = []
    by_segment: dict[str, list[float]] = {}

    for user in engine.users:
        value = affinity(user["latent"], product)
        scores.append(value)
        by_segment.setdefault(user["segment"], []).append(value)

    if not scores:
        return {"segment": "General", "percentile": 50.0}

    means = {seg: float(np.mean(values)) for seg, values in by_segment.items()}
    best_segment = max(means, key=means.get)
    population = np.array(scores, dtype=np.float64)
    percentile = float((population < means[best_segment]).mean() * 100.0)
    return {
        "segment": best_segment,
        "percentile": round(percentile, 1),
        "segment_affinity": round(means[best_segment], 4),
        "population_affinity": round(float(population.mean()), 4),
    }


def explain(engine: Orchestrator, rec_id: str) -> dict | None:
    record = engine.get_impression(rec_id)
    if record is None:
        return None

    breakdown = []
    for agent in AGENT_KEYS:
        breakdown.append(
            {
                "agent": agent,
                "weight": round(record["weights"][agent], 4),
                "raw_score": round(record["normalised"][agent], 5),
                "contribution": round(record["contributions"][agent], 5),
                "narrative": _narrative(agent, engine, record),
            }
        )
    breakdown.sort(key=lambda b: -b["contribution"])

    return {
        "rec_id": rec_id,
        "product": engine.products[record["product_idx"]],
        "headline": _headline(engine, record),
        "agent_breakdown": breakdown,
        "similar_because": _similar_because(engine, record),
        "audience_fit": _audience_fit(engine, record),
        "diversity_bonus": round(record["diversity_bonus"], 5),
        "confidence": round(record["confidence"], 4),
        "context": record["context"],
    }
