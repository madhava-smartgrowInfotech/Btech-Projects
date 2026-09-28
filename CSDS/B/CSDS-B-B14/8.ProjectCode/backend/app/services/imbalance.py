"""Distribution imbalance: supply vs demand per zone, equity score and a simulated rebalancing plan."""
import threading

from . import twin

_cache = {}
_lock = threading.Lock()
SPEEDS = [1.0, 1.05, 1.1, 1.15]
THROTTLES = [None, {"P01": 300.0}, {"P02": 300.0}]
THROTTLE_LABEL = {"P01": "Zone 1 trunk main (P01)", "P02": "Zone 4 trunk main (P02)"}


def state(leaks=(), pump_speed=1.0, throttle=None):
    """Simulated 24h state of the twin; cached per configuration."""
    key = (tuple(sorted(leaks)), round(pump_speed, 3), tuple(sorted((throttle or {}).items())))
    with _lock:
        if key in _cache:
            return _cache[key]
    wn, res = twin.simulate_state(list(leaks), pump_speed, throttle)
    out = (wn, res, twin.summarize_eps(wn, res))
    with _lock:
        if len(_cache) > 64:
            _cache.clear()
        _cache[key] = out
    return out


def _objective(s):
    # favour equity, penalise extra leakage from higher pressure
    return s["equity_score"] - 3.0 * s["nrw_pct"] - (0.5 if s.get("_throttled") else 0.0)


def describe_action(speed, throttle):
    parts = []
    if abs(speed - 1.0) > 1e-6:
        parts.append(f"run PUMP1 at {round(speed * 100)}% speed")
    if throttle:
        for p, k in throttle.items():
            parts.append(f"partly close the valve on the {THROTTLE_LABEL.get(p, p)} (loss coefficient {k:g})")
    return " and ".join(parts) or "keep current settings"


def analyse(leaks=()):
    _, _, cur = state(leaks)
    zones = list(cur["zones"].values())
    worst = min(zones, key=lambda z: z["pressure_adequacy"] * min(1, z["service_ratio"]))
    best = max(zones, key=lambda z: z["avg_pressure"])
    for z in zones:
        z["balance_m3"] = round(z["supply_m3"] - z["demand_m3"], 1)
        if z["pressure_adequacy"] < 0.95 or z["service_ratio"] < 0.99:
            z["status"] = "under-supplied"
        elif z["losses_m3"] > 0.14 * z["demand_m3"]:
            z["status"] = "high losses"
        elif z["avg_pressure"] > 45:
            z["status"] = "excess pressure"
        else:
            z["status"] = "balanced"
    candidates = []
    for sp in SPEEDS:
        for th in THROTTLES:
            if sp == 1.0 and th is None:
                continue
            _, _, s = state(leaks, sp, th)
            s = {**s, "_throttled": bool(th)}
            candidates.append({"pump_speed": sp, "throttle": th, "equity_score": s["equity_score"],
                               "nrw_pct": s["nrw_pct"], "min_pressure": s["min_pressure"],
                               "pump_m3": s["pump_m3"], "objective": round(_objective(s), 2),
                               "zones": {z: {"pressure_adequacy": v["pressure_adequacy"], "avg_pressure": v["avg_pressure"]}
                                         for z, v in s["zones"].items()}})
    best_c = max(candidates, key=lambda c: c["objective"])
    improves = best_c["objective"] > _objective(cur) + 1.0
    if improves:
        text = (f"{worst['name']} is the least served zone ({round(worst['pressure_adequacy'] * 100)}% of node-hours at "
                f"or above {twin.REQUIRED_PRESSURE:g} m, minimum {worst['min_pressure']} m) while {best['name']} runs at "
                f"{best['avg_pressure']} m on average. Recommended: {describe_action(best_c['pump_speed'], best_c['throttle'])}. "
                f"Simulated result: equity {cur['equity_score']} -> {best_c['equity_score']}, "
                f"NRW {cur['nrw_pct']}% -> {best_c['nrw_pct']}%.")
    else:
        text = "Supply is balanced across zones; no rebalancing action improves the twin's outcome."
    return {
        "current": {k: cur[k] for k in ("equity_score", "nrw_pct", "avg_pressure", "min_pressure", "system_input_m3",
                                         "billed_m3", "demand_m3", "pump_m3")},
        "zones": zones,
        "worst_zone": worst["zone"],
        "suggestion": {"text": text, "recommended": best_c if improves else None, "improves": improves},
        "candidates": sorted(candidates, key=lambda c: -c["objective"]),
    }


def whatif(leaks=(), pump_speed=1.0, throttle=None):
    _, _, s = state(leaks, pump_speed, throttle)
    return {"pump_speed": pump_speed, "throttle": throttle, "action": describe_action(pump_speed, throttle), **s}
