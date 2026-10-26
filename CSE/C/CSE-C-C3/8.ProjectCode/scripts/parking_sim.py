"""Discrete-event simulator of the ParkSure reservation rules.

It re-creates the experimental scenario described in the base paper (Cabri et al., arXiv:2605.17650:
8 parking areas, 80 reservable bays, 80-110 vehicles, each making 10 parks of 1-3 h, 25-50 % of the
vehicles overstaying by 1 h) but runs the *ParkSure* rules instead of SUMO:

  * admission    - accept a request only if  overlapping bookings + buffer < capacity   (engine.forecast_free)
  * arrival      - if the area is physically full, move the driver to exactly one nearest alternate with
                   forecast space (engine.nearest_alternate, haversine); if none exists the park fails
  * buffer       - static 0 / 1 / 3, ParkSure's shipped dynamic rule (+1 on every on-time checkout, cap 5,
                   reset to 1 every 24 h) and the paper-literal rule (+1 on every late checkout)
  * trust score  - B=3 benefits -> +1, W=2 warnings -> -1, suspension below 1.5 with a recent warning
                   (engine.record_checkout_trust / engine.suspension_block)

Everything the paper does not specify (arrival process, lead time, travel gaps, area layout) is an
assumption and is listed in SIM_ASSUMPTIONS.  tests/test_sim_parity.py checks that the admission and trust
functions here agree decision-for-decision with the real engine.
"""
from __future__ import annotations

import heapq
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config as C  # noqa: E402
from app.engine import fee_multiplier, haversine_km  # noqa: E402  (pure functions, reused as-is)

MIN = 1.0
HOUR = 60.0 * MIN

N_AREAS = 8
BAYS_PER_AREA = 10
PARKS_PER_VEHICLE = 10
GRACE_MIN = 10.0              # app/main.py::checkout treats <= end + 10 min as on time
OVERSTAY_MIN = 60.0           # bad vehicles stay one extra hour (as in the paper)

SIM_ASSUMPTIONS = {
    "areas": "8 areas x 10 bays on a 4x2 grid, 0.012 deg (about 1.3 km) apart",
    "area_choice": "uniform random per request",
    "first_request": "uniform in [0, 2] h after the start",
    "lead_time": "reservation placed 15-60 min before the planned arrival (uniform)",
    "duration": "planned stay uniform in [1, 3] h, as in the paper",
    "gap_after_park": "next request 15-60 min after the vehicle leaves (uniform)",
    "outside_stops": "two stops of 8-16 h outside the system, after two random parks, as in the paper",
    "bad_vehicles": "always leave 1 h after the reserved end; good vehicles leave exactly at the end",
    "check_in": "every driver checks in at the planned arrival time",
}

STRATEGIES = {
    "static_0": {"kind": "static", "buf": 0},
    "static_1": {"kind": "static", "buf": 1},
    "static_3": {"kind": "static", "buf": 3},
    "dynamic_parksure": {"kind": "dyn_on_time"},     # shipped code: +1 on every on-time checkout
    "dynamic_paper": {"kind": "dyn_on_late"},        # base paper: +1 on every late checkout
}


# ----------------------------------------------------------------------------- rules shared with the engine
def admit(overlap: int, buffer: int, capacity: int) -> bool:
    """engine.forecast_free: used + buffer < capacity."""
    return (overlap + buffer) < capacity


def trust_update(state: dict, on_time: bool) -> None:
    """engine.record_checkout_trust applied to a plain dict (trust, streak, warnings)."""
    if on_time:
        state["streak"] += 1
        if state["streak"] >= C.BENEFIT_STREAK_FOR_REWARD:
            if state["trust"] < C.TRUST_MAX:
                state["trust"] = min(C.TRUST_MAX, state["trust"] + 1.0)
            state["streak"] = 0
    else:
        state["streak"] = 0
        state["warnings"] += 1
        state["last_warning"] = state["now"]
        if state["warnings"] >= C.WARNINGS_FOR_PENALTY:
            state["trust"] = max(C.TRUST_MIN, state["trust"] - 1.0)
            state["warnings"] = 0


def suspended(state: dict, now: float) -> bool:
    """engine.suspension_block: cooldown running, or trust below 1.5 with a warning in the last 14 days."""
    if state["suspended_until"] > now:
        return True
    if state["trust"] < C.TRUST_SUSPEND_THRESHOLD:
        recent = state["last_warning"] is not None and (now - state["last_warning"]) <= C.RECENT_VIOLATION_DAYS * 24 * HOUR
        if recent:
            state["suspended_until"] = now + C.SUSPEND_COOLDOWN_HOURS * HOUR
            return True
    return False


# ----------------------------------------------------------------------------- simulation state
@dataclass
class Area:
    idx: int
    lat: float
    lon: float
    cap: int = BAYS_PER_AREA
    buffer: int = 0
    last_reset: float = 0.0
    res: dict = field(default_factory=dict)       # rid -> (start, end) of admitted, not yet finished bookings
    occupied: int = 0

    def overlap(self, s: float, e: float) -> int:
        return sum(1 for (a, b) in self.res.values() if a < e and b > s)


@dataclass
class Vehicle:
    vid: int
    bad: bool
    long_stops: set
    k: int = 0
    st: dict = field(default_factory=lambda: {"trust": C.TRUST_START, "streak": 0, "warnings": 0,
                                              "last_warning": None, "suspended_until": -1.0, "now": 0.0})


def simulate(n_vehicles: int, bad_share: float, strategy: str, seed: int, trust_on: bool = True) -> dict:
    rnd = random.Random(seed)
    spec = STRATEGIES[strategy]
    areas = [Area(i, 12.97 + 0.012 * (i // 4), 77.59 + 0.012 * (i % 4)) for i in range(N_AREAS)]
    for a in areas:
        a.buffer = spec["buf"] if spec["kind"] == "static" else C.BUFFER_INIT

    n_bad = int(round(n_vehicles * bad_share))
    bad_ids = set(rnd.sample(range(n_vehicles), n_bad))
    vehicles = [Vehicle(i, i in bad_ids, set(rnd.sample(range(PARKS_PER_VEHICLE), 2))) for i in range(n_vehicles)]

    heap: list = []
    seq = 0

    def push(t, kind, payload):
        nonlocal seq
        seq += 1
        heapq.heappush(heap, (t, seq, kind, payload))

    for v in vehicles:
        push(rnd.uniform(0, 2 * HOUR), "REQ", v.vid)

    m = dict(requests=0, accepted=0, no_reservation=0, suspended=0, arrivals=0, parked_direct=0, moved_to_alternate=0,
             no_park=0, alt_overflow=0, overstay_departures=0, ontime_departures=0, bay_minutes=0.0,
             alt_km_total=0.0, trust_sum_end=0.0)
    bookings: dict = {}
    rid_seq = 0
    t_end = 0.0

    def next_request(v: Vehicle, t: float, after_park: bool):
        gap = rnd.uniform(15, 60)
        if after_park and v.k in v.long_stops:
            gap += rnd.uniform(8 * HOUR, 16 * HOUR)
        v.k += 1
        if v.k < PARKS_PER_VEHICLE:
            push(t + gap, "REQ", v.vid)

    def maybe_reset(a: Area, t: float):
        if spec["kind"] != "static" and (t - a.last_reset) >= C.BUFFER_RESET_HOURS * HOUR:
            a.buffer = C.BUFFER_INIT
            a.last_reset = t

    while heap:
        t, _, kind, p = heapq.heappop(heap)
        t_end = max(t_end, t)
        if kind == "REQ":
            v = vehicles[p]
            m["requests"] += 1
            v.st["now"] = t
            if trust_on and suspended(v.st, t):
                m["suspended"] += 1
                next_request(v, t, after_park=False)
                continue
            a = areas[rnd.randrange(N_AREAS)]
            maybe_reset(a, t)
            s = t + rnd.uniform(15, 60)
            e = s + rnd.uniform(1 * HOUR, 3 * HOUR)
            if not admit(a.overlap(s, e), a.buffer, a.cap):
                m["no_reservation"] += 1
                next_request(v, t, after_park=False)
                continue
            m["accepted"] += 1
            rid_seq += 1
            a.res[rid_seq] = (s, e)
            bookings[rid_seq] = {"v": v.vid, "area": a.idx, "s": s, "e": e}
            push(s, "ARR", rid_seq)
        elif kind == "ARR":
            b = bookings[p]
            v = vehicles[b["v"]]
            a = areas[b["area"]]
            m["arrivals"] += 1
            if a.occupied >= a.cap:                      # physically full: overstayers are still inside
                del a.res[p]
                best, best_km = None, None
                for alt in areas:
                    if alt.idx == a.idx:
                        continue
                    if not admit(alt.overlap(b["s"], b["e"]), alt.buffer, alt.cap):
                        continue
                    km = haversine_km(a.lat, a.lon, alt.lat, alt.lon)
                    if best is None or km < best_km:
                        best, best_km = alt, km
                if best is None:
                    m["no_park"] += 1
                    next_request(v, t, after_park=False)
                    continue
                m["moved_to_alternate"] += 1
                m["alt_km_total"] += best_km
                if best.occupied >= best.cap:            # the shipped code does not re-check the alternate's bays
                    m["alt_overflow"] += 1
                best.res[p] = (b["s"], b["e"])
                b["area"] = best.idx
                a = best
            else:
                m["parked_direct"] += 1
            a.occupied += 1
            b["arrived"] = t
            leave = b["e"] + (OVERSTAY_MIN if v.bad else 0.0)
            push(leave, "DEP", p)
        else:  # DEP
            b = bookings[p]
            v = vehicles[b["v"]]
            a = areas[b["area"]]
            a.occupied -= 1
            a.res.pop(p, None)
            m["bay_minutes"] += t - b["arrived"]
            on_time = t <= b["e"] + GRACE_MIN
            m["ontime_departures" if on_time else "overstay_departures"] += 1
            maybe_reset(a, t)
            if spec["kind"] == "dyn_on_time" and on_time and a.buffer < C.BUFFER_MAX:
                a.buffer += 1
            elif spec["kind"] == "dyn_on_late" and (not on_time) and a.buffer < C.BUFFER_MAX:
                a.buffer += 1
            v.st["now"] = t
            if trust_on:
                trust_update(v.st, on_time)
            next_request(v, t, after_park=True)

    m["parks_completed"] = m["parked_direct"] + m["moved_to_alternate"]
    m["success_rate"] = m["parks_completed"] / m["requests"] if m["requests"] else 0.0
    m["no_park_rate"] = m["no_park"] / m["accepted"] if m["accepted"] else 0.0
    m["utilisation"] = m["bay_minutes"] / (N_AREAS * BAYS_PER_AREA * t_end) if t_end else 0.0
    m["makespan_h"] = t_end / HOUR
    m["mean_trust_end"] = sum(v.st["trust"] for v in vehicles) / len(vehicles)
    m["n_vehicles"], m["bad_share"] = n_vehicles, bad_share
    del m["trust_sum_end"], m["bay_minutes"]
    return m


def mean_std(xs):
    n = len(xs)
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return mu, var ** 0.5


def run_config(n_vehicles, bad_share, strategy, seeds, trust_on=True, random_population=False):
    runs = []
    for sd in seeds:
        n = random.Random(10_000 + sd).randint(80, 110) if random_population else n_vehicles
        runs.append(simulate(n, bad_share, strategy, sd, trust_on))
    keys = ["requests", "accepted", "no_reservation", "suspended", "no_park", "moved_to_alternate", "alt_overflow",
            "parks_completed", "success_rate", "no_park_rate", "utilisation", "overstay_departures", "mean_trust_end"]
    out = {"runs": len(runs)}
    for k in keys:
        mu, sd_ = mean_std([r[k] for r in runs])
        out[k] = {"mean": round(mu, 4), "std": round(sd_, 4)}
    return out


if __name__ == "__main__":
    r = simulate(100, 0.25, "dynamic_parksure", 1)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
