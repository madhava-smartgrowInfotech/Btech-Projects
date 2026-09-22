"""Runtime settings: .env values are the defaults; administrators override them from the Settings screen."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import utcnow
from ..models import Setting

# key -> (type, default, min, max, description)
SPEC: dict[str, tuple[type, Any, float | None, float | None, str]] = {
    "detect_min_readings": (int, settings.detect_min_readings, 2, 200, "Readings needed in the window before a zone is judged"),
    "detect_window_min": (int, settings.detect_window_min, 1, 1440, "Sliding window length (minutes)"),
    "detect_bad_share": (float, settings.detect_bad_share, 0.3, 1.0, "Share of Weak/Dead readings that makes a zone bad"),
    "detect_persist_min": (int, settings.detect_persist_min, 0, 1440, "Minutes a zone must stay bad before the complaint is registered"),
    "verify_min_readings": (int, settings.verify_min_readings, 2, 200, "New readings needed to verify a resolved complaint"),
    "verify_strong_share": (float, settings.verify_strong_share, 0.3, 1.0, "Share of Strong readings that confirms a fix"),
    "verify_reopen_share": (float, settings.verify_reopen_share, 0.2, 1.0, "Share of Weak/Dead readings that reopens a complaint"),
    "verify_timeout_days": (int, settings.verify_timeout_days, 1, 90, "Days to wait for verification readings"),
    "probe_weak_rtt_ms": (float, settings.probe_weak_rtt_ms, 50, 5000, "Phone probe: round-trip above this is Weak (ms)"),
    "probe_weak_dl_mbps": (float, settings.probe_weak_dl_mbps, 0.1, 100, "Phone probe: download below this is Weak (Mbps)"),
    "notify_telegram": (bool, True, None, None, "Send complaint updates to the Telegram desk chat"),
    "notify_email": (bool, True, None, None, "Send complaint updates to the desk email address"),
    "telegram_chat_id": (str, settings.telegram_chat_id, None, None, "Telegram chat that receives desk notifications"),
}

DEMO_PRESET = {"detect_min_readings": 4, "detect_window_min": 10, "detect_bad_share": 0.7, "detect_persist_min": 2,
               "verify_min_readings": 3, "verify_strong_share": 0.7, "verify_reopen_share": 0.5}


def _coerce(key: str, value: Any) -> Any:
    kind, _, lo, hi, _ = SPEC[key]
    if kind is bool:
        return bool(value) if not isinstance(value, str) else value.lower() in ("1", "true", "yes", "on")
    if kind is str:
        return "" if value is None else str(value).strip()
    v = kind(value)
    if lo is not None and v < lo:
        raise ValueError(f"{key} must be at least {lo}")
    if hi is not None and v > hi:
        raise ValueError(f"{key} must be at most {hi}")
    return v


def get_all(db: Session) -> dict[str, Any]:
    values = {k: spec[1] for k, spec in SPEC.items()}
    for row in db.query(Setting).filter(Setting.key.in_(SPEC.keys())).all():
        try:
            values[row.key] = _coerce(row.key, row.value)
        except (ValueError, TypeError):
            pass
    return values


def describe(db: Session) -> list[dict]:
    values = get_all(db)
    return [{"key": k, "value": values[k], "default": spec[1], "type": spec[0].__name__, "min": spec[2], "max": spec[3],
             "description": spec[4]} for k, spec in SPEC.items()]


def update(db: Session, changes: dict[str, Any], user_id: int | None) -> dict[str, Any]:
    clean = {}
    for key, value in changes.items():
        if key not in SPEC:
            raise ValueError(f"Unknown setting: {key}")
        clean[key] = _coerce(key, value)
    for key, value in clean.items():
        row = db.get(Setting, key)
        if row:
            row.value, row.updated_by, row.updated_at = value, user_id, utcnow()
        else:
            db.add(Setting(key=key, value=value, updated_by=user_id))
    db.commit()
    return get_all(db)
