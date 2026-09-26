"""Objective 5 - re-optimise hub configurations as demand changes.

`rolling_reoptimisation()` walks month by month through the last
`n_months` of history. For each month it (a) forecasts demand with the
Random Forest using only earlier data, (b) re-runs the matheuristic, and
(c) evaluates the chosen configuration against the demand that actually
materialised. It also tracks which hubs opened/closed between months and
compares against a *static* plan fixed once at the start of the horizon
(the traditional fixed-demand approach).

`scalability_benchmark()` shows why a matheuristic is needed: it inflates
the network to several hundred demand points and times the exact MIP
(with a time limit) against the matheuristic.
"""
from __future__ import annotations

import json
import math
import time

import numpy as np
import pandas as pd

from . import config
from .data import distance_matrix
from .forecast import forecast_for_period
from .matheuristic import solve_matheuristic
from .model import HAS_PULP, Instance, evaluate_solution, solve_exact


def _series(demand: pd.DataFrame, regions: pd.DataFrame, period: str) -> np.ndarray:
    return demand[demand.period == period].set_index("region_id").loc[regions.region_id, "orders"].to_numpy(float)


def rolling_reoptimisation(regions: pd.DataFrame, demand: pd.DataFrame, n_months: int = 6,
                           params: dict | None = None, verbose: bool = True) -> dict:
    params = params or {}
    periods = sorted(demand.period.unique())[-n_months:]
    first_hist = demand[demand.period < periods[0]]
    hist_avg = first_hist.groupby("region_id")["orders"].mean().loc[regions.region_id].to_numpy(float)

    # static baseline: one configuration planned once on the historical average
    static_inst = Instance.from_forecast(regions, hist_avg, **params)
    static = solve_matheuristic(static_inst)

    timeline, prev_hubs = [], None
    for p in periods:
        fc = forecast_for_period(regions, demand, p).set_index("region_id").loc[regions.region_id, "forecast"].to_numpy(float)
        real = _series(demand, regions, p)
        inst = Instance.from_forecast(regions, fc, **params)
        sol = solve_matheuristic(inst)
        kpi = evaluate_solution(inst, sol["hubs"], sol["assign"], real)
        kpi_static = evaluate_solution(static_inst, static["hubs"], static["assign"], real)
        opened = sorted(set(sol["hubs"]) - set(prev_hubs or sol["hubs"]))
        closed = sorted(set(prev_hubs or sol["hubs"]) - set(sol["hubs"]))
        entry = {
            "period": p, "forecast_total": int(fc.sum()), "realized_total": int(real.sum()),
            "forecast_error_pct": round(abs(fc.sum() - real.sum()) / real.sum() * 100, 2),
            "hubs": sol["hubs"], "hub_cities": kpi["hub_cities"],
            "opened": [regions.city[h] for h in opened], "closed": [regions.city[h] for h in closed],
            "solve_seconds": sol["seconds"],
            "adaptive": {k: kpi[k] for k in ("total_cost", "avg_delivery_hours", "fulfilment_rate",
                                             "reliability_sla", "overloaded_hubs", "cost_per_order")},
            "static": {k: kpi_static[k] for k in ("total_cost", "avg_delivery_hours", "fulfilment_rate",
                                                  "reliability_sla", "overloaded_hubs", "cost_per_order")},
        }
        timeline.append(entry)
        prev_hubs = sol["hubs"]
        if verbose:
            print(f"  {p}: fc {int(fc.sum()):>9,} real {int(real.sum()):>9,} | adaptive fulfil "
                  f"{kpi['fulfilment_rate']:.3f} cost {kpi['total_cost']:>13,.0f} | static fulfil "
                  f"{kpi_static['fulfilment_rate']:.3f} cost {kpi_static['total_cost']:>13,.0f} | "
                  f"+{entry['opened']} -{entry['closed']}")

    def avg(key, which):
        return round(float(np.mean([t[which][key] for t in timeline])), 4)

    summary = {
        "periods": periods, "static_hubs": [regions.city[h] for h in static["hubs"]],
        "timeline": timeline,
        "adaptive_avg": {k: avg(k, "adaptive") for k in ("total_cost", "avg_delivery_hours", "fulfilment_rate", "reliability_sla")},
        "static_avg": {k: avg(k, "static") for k in ("total_cost", "avg_delivery_hours", "fulfilment_rate", "reliability_sla")},
        "hub_changes": int(sum(len(t["opened"]) for t in timeline[1:])),
        "params": Instance.from_forecast(regions, hist_avg, **params).params,
    }
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.ROLLING_JSON.write_text(json.dumps(summary, indent=2, default=float))
    return summary


def load_rolling() -> dict:
    return json.loads(config.ROLLING_JSON.read_text()) if config.ROLLING_JSON.exists() else {}


# ---------------------------------------------------------------------- #
def inflate_network(regions: pd.DataFrame, demand_vec: np.ndarray, factor: int, seed: int = 0):
    """Split every region into `factor` nearby demand points (for benchmarking)."""
    rng = np.random.default_rng(seed)
    rows, dem = [], []
    for i, r in regions.iterrows():
        shares = rng.dirichlet(np.ones(factor))
        for k in range(factor):
            b = rng.uniform(0, 2 * math.pi)
            km = rng.uniform(10, 60) if k else 0
            rows.append(dict(region_id=f"{r.region_id}-{k}", city=f"{r.city}#{k}", lat=r.lat + km / 111 * math.cos(b),
                             lon=r.lon + km / (111 * math.cos(math.radians(r.lat))) * math.sin(b), tier=r.tier if k == 0 else 3))
            dem.append(demand_vec[i] * shares[k])
    return pd.DataFrame(rows), np.array(dem)


def scalability_benchmark(regions: pd.DataFrame, demand_vec: np.ndarray, factors=(1, 2, 4),
                          exact_time_limit: float = 45, n_hubs: int = 6, verbose: bool = True,
                          append: bool = False) -> list[dict]:
    out = load_scalability() if append else []
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for f in factors:
        reg, dem = inflate_network(regions, demand_vec, f)
        inst = Instance(reg, dem, distance_matrix(reg), {"n_hubs": n_hubs, "time_limit": 30})
        mh = solve_matheuristic(inst)
        row = {"nodes": len(reg), "binary_vars": len(reg) + len(reg) ** 2, "matheuristic_seconds": mh["seconds"],
               "matheuristic_objective": round(mh["objective"], 0)}
        if HAS_PULP:
            ex = solve_exact(inst, time_limit=exact_time_limit)
            row.update(exact_seconds=ex["seconds"], exact_status=ex["status"],
                       exact_objective=round(ex["objective"], 0) if ex.get("assign") is not None else None)
            if row["exact_objective"]:
                row["matheuristic_gap_pct"] = round((mh["objective"] - ex["objective"]) / ex["objective"] * 100, 2)
        out.append(row)
        (config.RESULTS_DIR / "scalability.json").write_text(json.dumps(out, indent=2, default=float))
        if verbose:
            print(f"  n={row['nodes']:>4}  matheuristic {row['matheuristic_seconds']:>6}s  "
                  f"exact {row.get('exact_seconds','-'):>6}s ({row.get('exact_status','-')})  "
                  f"gap {row.get('matheuristic_gap_pct','-')}%")
    (config.RESULTS_DIR / "scalability.json").write_text(json.dumps(out, indent=2, default=float))
    return out


def load_scalability() -> list:
    p = config.RESULTS_DIR / "scalability.json"
    return json.loads(p.read_text()) if p.exists() else []
