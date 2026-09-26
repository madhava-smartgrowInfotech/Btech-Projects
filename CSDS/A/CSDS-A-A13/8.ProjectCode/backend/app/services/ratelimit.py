"""A small in-memory sliding-window rate limiter (one SeatWise server, so memory is enough)."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.errors import AppError


class RateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > 60:
                hits.popleft()
            if len(hits) >= self.per_minute:
                raise AppError("Too many lookups from this device. Please wait a minute and try again.", 429)
            hits.append(now)
            if len(self._hits) > 10_000:  # forget idle clients
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] > 60][:5000]:
                    del self._hits[k]


def client_key(request: Request) -> str:
    """The caller's address. Requests arrive through the local web server, which forwards the real one."""
    peer = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and peer in {"127.0.0.1", "::1", "localhost"}:
        return forwarded.split(",")[0].strip()
    return peer
