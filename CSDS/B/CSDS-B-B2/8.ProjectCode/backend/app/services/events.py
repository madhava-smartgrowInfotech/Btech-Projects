"""In-process event bus for live updates (Server-Sent Events). Safe to publish from worker threads."""
from __future__ import annotations

import asyncio
import threading
from typing import Any

_subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue]] = []
_lock = threading.Lock()


def subscribe() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    with _lock:
        _subscribers.append((asyncio.get_running_loop(), queue))
    return queue


def unsubscribe(queue: asyncio.Queue) -> None:
    with _lock:
        _subscribers[:] = [(loop, q) for loop, q in _subscribers if q is not queue]


def _put(queue: asyncio.Queue, event: dict) -> None:
    if queue.full():               # a slow client drops its oldest event rather than blocking everyone
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
    queue.put_nowait(event)


def publish(kind: str, data: Any) -> None:
    event = {"type": kind, "data": data}
    with _lock:
        targets = list(_subscribers)
    for loop, queue in targets:
        try:
            loop.call_soon_threadsafe(_put, queue, event)
        except RuntimeError:       # loop already closed
            unsubscribe(queue)


def subscriber_count() -> int:
    with _lock:
        return len(_subscribers)
