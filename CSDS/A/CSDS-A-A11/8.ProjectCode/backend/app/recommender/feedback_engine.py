"""Self-learning weight loop.

Every piece of feedback is attributed back to the agents that actually produced
the recommendation, then the live blend is nudged with an exponential-weights
(Hedge) update:

    w_a  <-  w_a * exp(eta * reward * gain_a)

`gain_a` is the agent's share of that recommendation's score, so an agent is
only rewarded or penalised in proportion to how responsible it was. Weights are
clamped above a floor and renormalised to sum to one, which keeps the update
interpretable and stops any agent being switched off permanently.
"""

from __future__ import annotations

import math
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import LEARNING_RATE, WEIGHT_FLOOR
from ..models import FeedbackRecord
from .orchestrator import AGENT_KEYS, Orchestrator, normalise_weights

# Reward magnitude scales with how far down the funnel the action sits.
ACTION_REWARD = {
    "click": 0.60,
    "add_to_cart": 1.05,
    "purchase": 1.75,
    "dismiss": -0.55,
    "ignore": -0.22,
}

LEVERS = AGENT_KEYS + ("diversity",)


def _gains(record: dict) -> dict[str, float]:
    """Responsibility share of each lever for one recommendation."""
    contributions = {k: max(0.0, record["contributions"][k]) for k in AGENT_KEYS}
    # The diversity lever is credited by how much re-ranking moved this item,
    # which is the only way it influences what the shopper actually saw.
    diversity_effect = abs(record.get("diversity_bonus", 0.0))
    raw = dict(contributions)
    raw["diversity"] = diversity_effect

    total = sum(raw.values())
    if total <= 0:
        return {k: 1.0 / len(LEVERS) for k in LEVERS}
    return {k: v / total for k, v in raw.items()}


def apply_feedback(
    db: Session,
    engine: Orchestrator,
    *,
    rec_id: str,
    action: str,
    session_id: str,
    user_id: str | None,
) -> dict:
    """Update the live blend from one feedback signal. Returns the new weights."""
    record = engine.get_impression(rec_id)
    reward = ACTION_REWARD.get(action, 0.0)

    if record is None:
        # The impression aged out of the cache: log the signal, leave the blend
        # alone rather than guessing at attribution.
        db.add(
            FeedbackRecord(
                session_id=session_id,
                user_id=user_id,
                rec_id=rec_id,
                action=action,
                reward=reward,
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
        return {
            "weights": dict(engine.weights),
            "step": engine.step,
            "applied": False,
            "gains": {},
            "reward": reward,
        }

    gains = _gains(record)
    current = dict(engine.weights)

    updated = {}
    for lever in LEVERS:
        multiplier = math.exp(LEARNING_RATE * reward * gains[lever])
        updated[lever] = current[lever] * multiplier

    # Clamp then renormalise so the blend stays a probability vector.
    for lever in LEVERS:
        updated[lever] = max(WEIGHT_FLOOR, updated[lever])
    new_weights = normalise_weights(updated)

    engine.set_weights(db, new_weights, trigger_action=action)

    db.add(
        FeedbackRecord(
            session_id=session_id,
            user_id=user_id,
            rec_id=rec_id,
            action=action,
            reward=reward,
            created_at=datetime.utcnow(),
        )
    )
    db.commit()

    # Feed the behaviour itself back into the agents, so the next list reflects
    # the interaction and not only the weight change.
    if action in ("click", "add_to_cart", "purchase"):
        engine.record_event(
            user_id=user_id,
            session_id=session_id,
            product_id=record["product_id"],
            etype=action,
            value=None,
            query=None,
            created_at=datetime.utcnow(),
        )

    return {
        "weights": new_weights,
        "step": engine.step,
        "applied": True,
        "gains": {k: round(v, 4) for k, v in gains.items()},
        "reward": reward,
        "delta": {k: round(new_weights[k] - current[k], 5) for k in LEVERS},
    }
