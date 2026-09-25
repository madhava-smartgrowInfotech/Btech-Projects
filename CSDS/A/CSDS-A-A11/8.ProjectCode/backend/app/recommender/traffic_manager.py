"""Traffic and load control centre.

A background task advances a small queueing model once a second. Incoming rps
follows a demand curve that a load test can reshape; requests are served by a
worker pool with finite throughput, so any excess builds a queue and the queue
is what drives latency. Autoscaling reacts to the demand but only adds workers
with a short lag, which is what produces the realistic overshoot-then-recover
shape. Sustained traffic warms the cache, and a warmer cache shortens service
time, which drains the queue faster.

Nothing here is a scripted animation: change the incoming curve and every
downstream number follows from the model.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..config import BASELINE_RPS, TRAFFIC_TICK_S, WORKER_CAPACITY_RPS

MIN_WORKERS = 4
MAX_WORKERS = 96
BASE_SERVICE_MS = 38.0

PROFILES = ("steady", "flash_sale", "spike")


@dataclass
class LoadTest:
    test_id: str
    profile: str
    duration_s: float
    started_at: float


@dataclass
class TrafficState:
    rps: float = BASELINE_RPS
    p50_latency_ms: float = 46.0
    p99_latency_ms: float = 120.0
    queue_length: float = 0.0
    cache_hit_rate: float = 0.71
    active_workers: int = 8
    autoscale_target: int = 8
    status: str = "nominal"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def snapshot(self) -> dict:
        return {
            "rps": round(self.rps, 1),
            "p50_latency_ms": round(self.p50_latency_ms, 1),
            "p99_latency_ms": round(self.p99_latency_ms, 1),
            "queue_length": int(round(self.queue_length)),
            "cache_hit_rate": round(self.cache_hit_rate, 4),
            "active_workers": self.active_workers,
            "autoscale_target": self.autoscale_target,
            "status": self.status,
            "updated_at": self.updated_at,
        }


class TrafficManager:
    def __init__(self):
        self.state = TrafficState()
        self.active_test: LoadTest | None = None
        self.history: list[dict] = []
        self._rng = random.Random(4172)
        self._task: asyncio.Task | None = None
        self._clients: set = set()
        self._elapsed = 0.0

    # ----------------------------------------------------------- demand curve

    def _demand(self) -> float:
        """Incoming rps for this tick, from the baseline or the active profile."""
        # Baseline demand has a slow diurnal sway plus tick-to-tick jitter.
        sway = 1.0 + 0.12 * math.sin(self._elapsed / 47.0)
        base = BASELINE_RPS * sway

        test = self.active_test
        if test is None:
            return max(10.0, base * self._rng.uniform(0.95, 1.05))

        # A monotonic wall clock, not the loop clock: load tests are started
        # from a worker thread where no event loop is running.
        progress = (time.monotonic() - test.started_at) / max(test.duration_s, 1e-6)
        if progress >= 1.0:
            self.active_test = None
            return max(10.0, base * self._rng.uniform(0.95, 1.05))

        if test.profile == "steady":
            multiplier = 1.0
        elif test.profile == "flash_sale":
            # Ramp over the first 35%, hold, then release over the last 15%.
            if progress < 0.35:
                multiplier = 1.0 + 3.6 * (progress / 0.35)
            elif progress < 0.85:
                multiplier = 4.6
            else:
                multiplier = 4.6 - 3.3 * ((progress - 0.85) / 0.15)
        else:  # spike
            if progress < 0.12:
                multiplier = 1.0 + 8.2 * (progress / 0.12)
            else:
                multiplier = 1.0 + 8.2 * math.exp(-(progress - 0.12) * 7.5)

        return max(10.0, base * multiplier * self._rng.uniform(0.96, 1.04))

    # ------------------------------------------------------------- model tick

    def tick(self, dt: float = TRAFFIC_TICK_S) -> dict:
        state = self.state
        self._elapsed += dt
        incoming = self._demand()

        # Demand is smoothed a little: connections do not appear instantly.
        state.rps += (incoming - state.rps) * 0.55

        # A warm cache serves a share of traffic without touching a worker.
        effective_rps = state.rps * (1.0 - 0.45 * state.cache_hit_rate)
        capacity = state.active_workers * WORKER_CAPACITY_RPS

        # Queue is the running backlog of work the pool could not absorb.
        overflow = (effective_rps - capacity) * dt
        state.queue_length = max(0.0, state.queue_length + overflow)
        if overflow < 0:
            # Spare capacity drains the backlog rather than going to waste.
            state.queue_length = max(0.0, state.queue_length + overflow * 0.6)

        utilisation = effective_rps / capacity if capacity > 0 else 4.0

        # Service time rises with utilisation and falls as the cache warms.
        service_ms = BASE_SERVICE_MS * (1.0 - 0.38 * state.cache_hit_rate)
        congestion = 1.0 / max(0.08, 1.0 - min(0.96, utilisation))
        queue_wait_ms = (state.queue_length / max(capacity, 1.0)) * 1000.0

        state.p50_latency_ms = service_ms * min(congestion, 9.0) + queue_wait_ms * 0.35
        state.p99_latency_ms = state.p50_latency_ms * (2.1 + 0.85 * min(utilisation, 3.0)) + queue_wait_ms * 0.9
        state.p50_latency_ms = max(12.0, state.p50_latency_ms)
        state.p99_latency_ms = max(state.p50_latency_ms * 1.6, state.p99_latency_ms)

        # Autoscaler targets 70% utilisation, and reacts to backlog as well.
        desired = effective_rps / (WORKER_CAPACITY_RPS * 0.70)
        desired += state.queue_length / 120.0
        state.autoscale_target = int(max(MIN_WORKERS, min(MAX_WORKERS, math.ceil(desired))))

        # Workers arrive with a lag: scaling up is faster than scaling down.
        gap = state.autoscale_target - state.active_workers
        if gap > 0:
            state.active_workers += max(1, math.ceil(gap * 0.34))
        elif gap < 0:
            state.active_workers -= max(1, math.floor(abs(gap) * 0.12))
        state.active_workers = int(max(MIN_WORKERS, min(MAX_WORKERS, state.active_workers)))

        # Sustained traffic warms the cache; quiet periods let it go cold.
        load_ratio = min(2.5, state.rps / BASELINE_RPS)
        warm_target = 0.60 + 0.34 * min(1.0, load_ratio / 1.8)
        state.cache_hit_rate += (warm_target - state.cache_hit_rate) * 0.09
        state.cache_hit_rate = min(0.97, max(0.42, state.cache_hit_rate))

        if state.p99_latency_ms > 900 or state.queue_length > 400:
            state.status = "critical"
        elif state.p99_latency_ms > 340 or state.queue_length > 80:
            state.status = "elevated"
        else:
            state.status = "nominal"

        state.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        snapshot = state.snapshot()
        self.history.append(snapshot)
        if len(self.history) > 600:
            del self.history[:-600]
        return snapshot

    # --------------------------------------------------------------- lifecycle

    async def _loop(self) -> None:
        while True:
            try:
                snapshot = self.tick()
                await self._broadcast(snapshot)
            except asyncio.CancelledError:
                raise
            except Exception:
                # A modelling hiccup must never take the control centre offline.
                pass
            await asyncio.sleep(TRAFFIC_TICK_S)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

    # ---------------------------------------------------------------- clients

    async def connect(self, websocket) -> None:
        self._clients.add(websocket)
        await websocket.send_json(self.state.snapshot())

    def disconnect(self, websocket) -> None:
        self._clients.discard(websocket)

    async def _broadcast(self, snapshot: dict) -> None:
        if not self._clients:
            return
        dead = []
        for client in list(self._clients):
            try:
                await client.send_json(snapshot)
            except Exception:
                dead.append(client)
        for client in dead:
            self._clients.discard(client)

    # -------------------------------------------------------------- load test

    def start_load_test(self, profile: str, duration_s: float) -> str:
        if profile not in PROFILES:
            raise ValueError(f"Unknown traffic profile '{profile}'")
        duration_s = float(max(5.0, min(900.0, duration_s)))
        test_id = f"load_{uuid.uuid4().hex[:12]}"
        self.active_test = LoadTest(
            test_id=test_id,
            profile=profile,
            duration_s=duration_s,
            started_at=time.monotonic(),
        )
        return test_id

    def current_test(self) -> dict | None:
        test = self.active_test
        if test is None:
            return None
        remaining = max(0.0, test.duration_s - (time.monotonic() - test.started_at))
        return {
            "test_id": test.test_id,
            "profile": test.profile,
            "duration_s": test.duration_s,
            "remaining_s": round(remaining, 1),
        }


traffic_manager = TrafficManager()
