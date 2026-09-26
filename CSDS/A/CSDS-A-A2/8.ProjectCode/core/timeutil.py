"""Timezone helpers. The database stores naive UTC; the UI shows config.TIMEZONE."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import config

LOCAL_TZ = ZoneInfo(config.TIMEZONE)


def utcnow() -> datetime:
    """Naive UTC now (what the DB stores)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_local(dt_utc: datetime) -> datetime:
    """Naive UTC -> aware local time."""
    return dt_utc.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)


def to_utc(dt_local: datetime) -> datetime:
    """Naive local time -> naive UTC (for storage)."""
    return dt_local.replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def fmt(dt_utc: datetime, with_seconds: bool = False) -> str:
    return to_local(dt_utc).strftime("%d %b %Y, %H:%M" + (":%S" if with_seconds else ""))


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)
