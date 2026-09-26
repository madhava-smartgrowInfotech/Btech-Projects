"""Device identification derived from the browser's request headers."""
from __future__ import annotations

import hashlib
import uuid

FINGERPRINT_HEADERS = (
    "user-agent",
    "accept-language",
    "sec-ch-ua",
    "sec-ch-ua-platform",
    "sec-ch-ua-mobile",
)


def fingerprint(headers: dict | None, extra: str = "") -> str:
    """
    Build a stable device hash from request headers (+ an optional extra seed,
    e.g. a per-browser id). Falls back to a random id when headers are unavailable
    (bare-mode tests).
    """
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    parts = [headers.get(h, "") for h in FINGERPRINT_HEADERS]
    raw = "|".join(parts) + "|" + extra
    if not any(parts) and not extra:
        raw = uuid.uuid4().hex
    return hashlib.sha256(raw.encode()).hexdigest()


def label(headers: dict | None) -> str:
    """Human-readable device label for the faculty dashboard."""
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    ua = headers.get("user-agent", "unknown device")
    platform = headers.get("sec-ch-ua-platform", "").strip('"')
    mobile = headers.get("sec-ch-ua-mobile", "") == "?1"
    short = ua[:60] + ("…" if len(ua) > 60 else "")
    return f"{'Mobile' if mobile else 'Desktop'} · {platform or '?'} · {short}"
