"""Time base and seeded exogenous profiles (solar, load, price, weather)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class TimeStep:
    index: int
    minute_of_day: int
    label: str


def build_timeline(start_hhmm: str, steps: int, dt: int) -> list[TimeStep]:
    h, m = (int(x) for x in start_hhmm.split(":"))
    start = h * 60 + m
    out = []
    for i in range(steps):
        mod = (start + i * dt) % (24 * 60)
        out.append(TimeStep(i, mod, f"{mod // 60:02d}:{mod % 60:02d}"))
    return out


@dataclass
class Exogenous:
    load_kw: dict[str, float]
    pv_kw: dict[str, float]
    price: float
    weather: dict[str, float]
    storage_available: dict[str, bool] = field(default_factory=dict)


def price_at(hour: float) -> float:
    """Time-of-use tariff, INR/kWh (illustrative)."""
    if hour < 6:
        return 3.8
    if hour < 10:
        return 5.2
    if hour < 17:
        return 4.6
    if hour < 22:
        return 9.0
    return 5.0


class Profiles:
    def __init__(self, seed: int, node_specs, timeline: list[TimeStep], load_scale=1.0, pv_scale=1.0,
                 price_scale=1.0, ev_mode: str = "always_home"):
        self.specs, self.timeline = list(node_specs), timeline
        self.load_scale, self.pv_scale, self.price_scale, self.ev_mode = load_scale, pv_scale, price_scale, ev_mode
        rng = np.random.default_rng(seed)
        n = len(timeline)
        k = np.ones(5) / 5.0
        cn = np.convolve(rng.normal(size=n + 8), k, mode="same")[4:4 + n]
        self.cloud = np.clip(0.88 + 0.12 * cn / (cn.std() + 1e-9), 0.45, 1.0)
        self.noise = {s.node_id: rng.normal(size=n) for s in self.specs}
        day = [price_at(x / 4.0) for x in range(96)]
        self.price_stats = {"min": min(day) * price_scale, "max": max(day) * price_scale, "avg": sum(day) / 96 * price_scale}

    @staticmethod
    def _load_shape(h: float) -> float:
        return 0.55 + 0.35 * math.exp(-(((h - 7.5) / 1.5) ** 2)) + 0.75 * math.exp(-(((h - 19.5) / 2.0) ** 2))

    def at(self, i: int) -> Exogenous:
        ts = self.timeline[i]
        h = ts.minute_of_day / 60.0
        sun = max(0.0, math.sin(math.pi * (h - 6.0) / 12.0)) ** 1.2 if 6.0 <= h <= 18.0 else 0.0
        load, pv, avail = {}, {}, {}
        for s in self.specs:
            load[s.node_id] = max(0.05, s.base_load_kw * self.load_scale * self._load_shape(h) * (1 + 0.05 * self.noise[s.node_id][i]))
            pv[s.node_id] = s.pv_kwp * self.pv_scale * sun * float(self.cloud[i])
            avail[s.node_id] = True
            if s.role == "ev_storage" and self.ev_mode == "commuter":
                avail[s.node_id] = not (7.5 <= h < 18.0)
        w = {"cloud_factor": round(float(self.cloud[i]), 2), "temp_c": round(24 + 7 * math.sin(math.pi * (h - 9) / 12), 1)}
        return Exogenous(load, pv, price_at(h) * self.price_scale, w, avail)
