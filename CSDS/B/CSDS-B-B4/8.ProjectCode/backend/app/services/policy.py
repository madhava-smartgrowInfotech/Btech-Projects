"""Risk policy: score thresholds (0-100) -> Low / Medium / High, and when to block."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.registry import registry
from app.models import AppSetting, utcnow

KEY = "risk_policy"


def default_policy() -> dict:
    s = get_settings()
    tuned = registry.policy or {}
    return {
        "medium": int(tuned.get("medium", s.risk_medium_threshold)),
        "high": int(tuned.get("high", s.risk_high_threshold)),
        "block_report_score": float(tuned.get("block_report_score", 2.5)),
    }


def get_policy(db: Session) -> dict:
    policy = default_policy()
    row = db.get(AppSetting, KEY)
    if row:
        policy.update({k: row.value[k] for k in ("medium", "high", "block_report_score") if k in row.value})
    return policy


def set_policy(db: Session, medium: int, high: int, block_report_score: float) -> dict:
    row = db.get(AppSetting, KEY)
    value = {"medium": medium, "high": high, "block_report_score": block_report_score}
    if row:
        row.value = value
        row.updated_at = utcnow()
    else:
        db.add(AppSetting(key=KEY, value=value))
    db.commit()
    return get_policy(db)


def level_for(score: int, policy: dict) -> str:
    if score >= policy["high"]:
        return "high"
    if score >= policy["medium"]:
        return "medium"
    return "low"


def raise_level(level: str) -> str:
    return {"low": "medium", "medium": "high"}.get(level, "high")


def action_for(level: str) -> str:
    return {"low": "pay", "medium": "verify", "high": "hold"}[level]
