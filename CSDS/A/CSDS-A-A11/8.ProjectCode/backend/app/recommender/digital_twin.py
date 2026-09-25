"""Digital twin simulation lab.

Replays the whole synthetic shopper population against two weight blends — the
live one as baseline and a proposed candidate — and measures what each one
would have earned before anything is deployed.

The response model is the part that makes this worth trusting: a simulated
shopper's click and purchase probability is computed from the same hidden
latent taste vector that generated their real behaviour history, evaluated
against the categories, tags, price and quality of whatever was recommended.
A blend that genuinely surfaces better-matched stock therefore scores higher,
and one that does not cannot be made to look good by chance.

Both arms are run under common random numbers: the same uniform draws and the
same per-round score jitter are used for baseline and candidate, so the
measured lift isolates the effect of the weights rather than sampling noise.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session

from ..config import RANDOM_SEED
from ..models import SimulationRun
from ..seed import affinity
from .diversity import mmr_rerank
from .orchestrator import AGENT_KEYS, Orchestrator, normalise_weights

LIST_SIZE = 8
POOL_SIZE = 40

# Verdict gates, in percent.
DEPLOY_CTR_LIFT = 2.0
DEPLOY_CONVERSION_LIFT = 1.0
REJECT_CTR_LIFT = -2.0
REJECT_CONVERSION_LIFT = -4.0


def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


class PopulationModel:
    """Per-shopper precomputation shared by both arms of a run."""

    def __init__(self, engine: Orchestrator):
        self.engine = engine
        n_products = len(engine.products)
        self.users = engine.users
        self.n_products = n_products

        self.affinity = np.zeros((len(self.users), n_products), dtype=np.float64)
        for u, user in enumerate(self.users):
            for p, product in enumerate(engine.products):
                self.affinity[u, p] = affinity(user["latent"], product)

        self.price_tolerance = np.array(
            [80.0 + 700.0 * u["latent"]["price_affinity"] for u in self.users],
            dtype=np.float64,
        )

        trending = engine.trending.score()
        in_stock = engine.in_stock

        self.pools: list[np.ndarray] = []
        self.normalised: list[dict[str, np.ndarray]] = []

        for user in self.users:
            interaction = engine.collaborative.user_vector(user["id"])
            raw = {
                "collaborative": np.asarray(
                    engine.collaborative.score_from_vector(interaction), dtype=np.float64
                ),
                "content": np.asarray(
                    engine.content.score_from_vector(interaction), dtype=np.float64
                ),
                "trending": np.asarray(trending, dtype=np.float64),
            }

            pool: set[int] = set()
            for vector in raw.values():
                if not np.any(vector):
                    continue
                pool.update(int(i) for i in np.argsort(-vector)[:POOL_SIZE] if vector[i] > 0)
            pool = {i for i in pool if in_stock[i]}
            if len(pool) < LIST_SIZE * 2:
                pool.update(
                    int(i) for i in np.argsort(-trending)[: LIST_SIZE * 4] if in_stock[i]
                )
            pool_array = np.array(sorted(pool), dtype=np.int64)

            norm = {}
            for key in AGENT_KEYS:
                sub = raw[key][pool_array]
                peak = float(sub.max()) if sub.size else 0.0
                norm[key] = np.clip(sub / peak, 0.0, 1.0) if peak > 0 else np.zeros_like(sub)

            self.pools.append(pool_array)
            self.normalised.append(norm)


class ArmAccumulator:
    def __init__(self, n_rounds: int, segments: list[str]):
        self.impressions = 0
        self.clicks = 0
        self.purchases = 0
        self.revenue = 0.0
        self.surfaced: set[int] = set()
        self.diversity_sum = 0.0
        self.lists = 0
        self.round_impressions = np.zeros(n_rounds, dtype=np.float64)
        self.round_clicks = np.zeros(n_rounds, dtype=np.float64)
        self.segment_impressions = {s: 0 for s in segments}
        self.segment_clicks = {s: 0 for s in segments}
        self.segment_purchases = {s: 0 for s in segments}

    def metrics(self, catalog_size: int) -> dict:
        ctr = self.clicks / self.impressions if self.impressions else 0.0
        conversion = self.purchases / self.clicks if self.clicks else 0.0
        aov = self.revenue / self.purchases if self.purchases else 0.0
        return {
            "ctr": round(ctr, 5),
            "conversion_rate": round(conversion, 5),
            "avg_order_value": round(aov, 2),
            "catalog_coverage": round(len(self.surfaced) / catalog_size, 5),
            "diversity_index": round(self.diversity_sum / self.lists if self.lists else 0.0, 5),
            "impressions": self.impressions,
            "clicks": self.clicks,
            "purchases": self.purchases,
            "revenue": round(self.revenue, 2),
        }


def _pct_change(candidate: float, baseline: float) -> float:
    if baseline <= 0:
        return 0.0 if candidate <= 0 else 100.0
    return round((candidate / baseline - 1.0) * 100.0, 2)


def run_simulation(
    db: Session,
    engine: Orchestrator,
    *,
    name: str,
    candidate_weights: dict,
    population_size: int = 200,
    rounds: int = 5,
) -> dict:
    baseline_weights = normalise_weights(engine.weights)
    candidate_weights = normalise_weights(candidate_weights)

    population_size = int(max(10, min(2000, population_size)))
    rounds = int(max(1, min(30, rounds)))

    model = _population_model(engine)
    n_profiles = len(model.users)
    segments = sorted({u["segment"] for u in model.users})
    catalog_size = len(engine.products)
    n_categories = len(engine.categories)

    base_arm = ArmAccumulator(rounds, segments)
    cand_arm = ArmAccumulator(rounds, segments)

    # Common random numbers: the stream depends only on the run shape, never on
    # the weights, so both arms face identical shopper luck.
    rng = np.random.default_rng(RANDOM_SEED + population_size * 31 + rounds * 7919)

    for session in range(population_size):
        u = session % n_profiles
        user = model.users[u]
        pool = model.pools[u]
        if pool.size == 0:
            continue
        norm = model.normalised[u]
        segment = user["segment"]
        aff_row = model.affinity[u]
        tolerance = model.price_tolerance[u]

        for r in range(rounds):
            jitter = rng.normal(0.0, 0.03, size=pool.size)
            click_draws = rng.random(LIST_SIZE)
            purchase_draws = rng.random(LIST_SIZE)

            for weights, arm in ((baseline_weights, base_arm), (candidate_weights, cand_arm)):
                picks = _rank(engine, pool, norm, weights, jitter)
                _simulate_list(
                    engine=engine,
                    arm=arm,
                    picks=picks,
                    aff_row=aff_row,
                    tolerance=tolerance,
                    click_draws=click_draws,
                    purchase_draws=purchase_draws,
                    round_index=r,
                    segment=segment,
                    n_categories=n_categories,
                )

    baseline = base_arm.metrics(catalog_size)
    candidate = cand_arm.metrics(catalog_size)

    lift = {
        "ctr_pct": _pct_change(candidate["ctr"], baseline["ctr"]),
        "conversion_pct": _pct_change(candidate["conversion_rate"], baseline["conversion_rate"]),
        "revenue_pct": _pct_change(candidate["revenue"], baseline["revenue"]),
    }

    timeline = []
    for r in range(rounds):
        b_imp = base_arm.round_impressions[r] or 1.0
        c_imp = cand_arm.round_impressions[r] or 1.0
        timeline.append(
            {
                "round": r + 1,
                "baseline_ctr": round(float(base_arm.round_clicks[r] / b_imp), 5),
                "candidate_ctr": round(float(cand_arm.round_clicks[r] / c_imp), 5),
            }
        )

    segment_breakdown = []
    for segment in segments:
        b_imp = base_arm.segment_impressions[segment] or 1
        c_imp = cand_arm.segment_impressions[segment] or 1
        b_ctr = base_arm.segment_clicks[segment] / b_imp
        c_ctr = cand_arm.segment_clicks[segment] / c_imp
        segment_breakdown.append(
            {
                "segment": segment,
                "baseline_ctr": round(b_ctr, 5),
                "candidate_ctr": round(c_ctr, 5),
                "ctr_lift_pct": _pct_change(c_ctr, b_ctr),
                "impressions": int(c_imp),
            }
        )
    segment_breakdown.sort(key=lambda s: -s["ctr_lift_pct"])

    verdict = _verdict(lift)
    narrative = _narrative(
        name=name,
        verdict=verdict,
        lift=lift,
        baseline=baseline,
        candidate=candidate,
        baseline_weights=baseline_weights,
        candidate_weights=candidate_weights,
        segment_breakdown=segment_breakdown,
        population_size=population_size,
        rounds=rounds,
        n_profiles=n_profiles,
    )

    run_id = f"sim_{uuid.uuid4().hex[:16]}"
    created_at = datetime.utcnow()
    payload = {
        "run_id": run_id,
        "name": name,
        "weights": candidate_weights,
        "baseline_weights": baseline_weights,
        "baseline": baseline,
        "candidate": candidate,
        "lift": lift,
        "timeline": timeline,
        "segment_breakdown": segment_breakdown,
        "verdict": verdict,
        "narrative": narrative,
        "population_size": population_size,
        "distinct_profiles": n_profiles,
        "rounds": rounds,
        "created_at": created_at.isoformat() + "Z",
    }

    db.add(
        SimulationRun(
            run_id=run_id,
            name=name,
            weights=candidate_weights,
            verdict=verdict,
            lift=lift,
            payload=payload,
            created_at=created_at,
        )
    )
    db.commit()
    return payload


# --------------------------------------------------------------------- internals

_model_cache: dict[str, PopulationModel] = {}


def _population_model(engine: Orchestrator) -> PopulationModel:
    """Rebuild the precomputed population whenever the behaviour stream moves."""
    key = f"{len(engine.products)}:{len(engine.users)}:{int(engine.collaborative.matrix.sum())}"
    cached = _model_cache.get(key)
    if cached is None:
        cached = PopulationModel(engine)
        _model_cache.clear()
        _model_cache[key] = cached
    return cached


def _rank(
    engine: Orchestrator,
    pool: np.ndarray,
    norm: dict[str, np.ndarray],
    weights: dict,
    jitter: np.ndarray,
) -> list[tuple[int, float, float]]:
    agent_sum = weights["collaborative"] + weights["content"] + weights["trending"]
    blended = (
        weights["collaborative"] * norm["collaborative"]
        + weights["content"] * norm["content"]
        + weights["trending"] * norm["trending"]
    ) / agent_sum
    blended = np.clip(blended + jitter, 0.0, None)
    relevance = {int(pool[i]): float(blended[i]) for i in range(pool.size)}
    return mmr_rerank(
        candidate_indices=[int(i) for i in pool],
        relevance=relevance,
        content_sim=engine.content.item_sim,
        category_ids=engine.category_ids,
        diversity_weight=weights["diversity"],
        limit=LIST_SIZE,
    )


def _simulate_list(
    *,
    engine: Orchestrator,
    arm: ArmAccumulator,
    picks: list[tuple[int, float, float]],
    aff_row: np.ndarray,
    tolerance: float,
    click_draws: np.ndarray,
    purchase_draws: np.ndarray,
    round_index: int,
    segment: str,
    n_categories: int,
) -> None:
    categories_seen: set[int] = set()

    for rank, (idx, _score, _bonus) in enumerate(picks):
        aff = aff_row[idx]
        position = 1.0 / (1.0 + 0.55 * rank)
        p_click = float(np.clip(_sigmoid(7.0 * (aff - 0.42)) * position * 0.62, 0.002, 0.93))

        arm.impressions += 1
        arm.round_impressions[round_index] += 1
        arm.segment_impressions[segment] += 1
        arm.surfaced.add(idx)
        categories_seen.add(int(engine.category_ids[idx]))

        if click_draws[rank] >= p_click:
            continue

        arm.clicks += 1
        arm.round_clicks[round_index] += 1
        arm.segment_clicks[segment] += 1

        price = engine.prices[idx]
        # A shopper stretches past their usual price band only for a strong fit.
        price_penalty = float(np.exp(-max(0.0, price / tolerance - 1.0) * 1.4))
        p_purchase = float(
            np.clip(_sigmoid(5.5 * (aff - 0.52)) * price_penalty, 0.004, 0.78)
        )
        if purchase_draws[rank] < p_purchase:
            arm.purchases += 1
            arm.segment_purchases[segment] += 1
            arm.revenue += float(price)

    arm.lists += 1
    if picks:
        arm.diversity_sum += len(categories_seen) / min(len(picks), n_categories)


def _verdict(lift: dict) -> str:
    if lift["ctr_pct"] >= DEPLOY_CTR_LIFT and lift["conversion_pct"] >= DEPLOY_CONVERSION_LIFT:
        return "deploy"
    if lift["ctr_pct"] <= REJECT_CTR_LIFT or lift["conversion_pct"] <= REJECT_CONVERSION_LIFT:
        return "reject"
    return "hold"


def _biggest_move(baseline_weights: dict, candidate_weights: dict) -> str:
    deltas = {k: candidate_weights[k] - baseline_weights[k] for k in candidate_weights}
    lever = max(deltas, key=lambda k: abs(deltas[k]))
    direction = "up" if deltas[lever] > 0 else "down"
    return f"{lever} {direction} {abs(deltas[lever]) * 100:.1f} points"


def _narrative(
    *,
    name: str,
    verdict: str,
    lift: dict,
    baseline: dict,
    candidate: dict,
    baseline_weights: dict,
    candidate_weights: dict,
    segment_breakdown: list[dict],
    population_size: int,
    rounds: int,
    n_profiles: int,
) -> str:
    move = _biggest_move(baseline_weights, candidate_weights)
    best = segment_breakdown[0] if segment_breakdown else None
    worst = segment_breakdown[-1] if segment_breakdown else None

    head = (
        f"“{name}” moved {move} and ran {population_size:,} simulated sessions "
        f"drawn from {n_profiles} shopper profiles over {rounds} rounds. "
        f"Click-through went from {baseline['ctr']:.2%} to {candidate['ctr']:.2%} "
        f"({lift['ctr_pct']:+.1f}%), conversion from {baseline['conversion_rate']:.2%} to "
        f"{candidate['conversion_rate']:.2%} ({lift['conversion_pct']:+.1f}%), and simulated "
        f"revenue {lift['revenue_pct']:+.1f}%."
    )

    coverage = (
        f" Catalogue coverage {baseline['catalog_coverage']:.1%} → {candidate['catalog_coverage']:.1%} "
        f"and list diversity {baseline['diversity_index']:.2f} → {candidate['diversity_index']:.2f}."
    )

    segment_line = ""
    if best and worst and best["segment"] != worst["segment"]:
        segment_line = (
            f" {best['segment']} shoppers responded best at {best['ctr_lift_pct']:+.1f}% CTR; "
            f"{worst['segment']} came off worst at {worst['ctr_lift_pct']:+.1f}%."
        )

    if verdict == "deploy":
        tail = (
            " Both headline metrics clear the release gate, so this blend is safe to take live."
        )
    elif verdict == "reject":
        tail = (
            " The candidate loses ground on a headline metric beyond the tolerated band. "
            "Keep the current blend."
        )
    else:
        tail = (
            " The difference is inside the noise band the gate treats as inconclusive. "
            "Hold, and re-run with a wider population or a sharper weight change."
        )

    return head + coverage + segment_line + tail
