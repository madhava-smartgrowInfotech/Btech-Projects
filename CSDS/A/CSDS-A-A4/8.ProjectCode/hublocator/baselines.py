"""Objective 6 - compare with traditional hub location methods.

Methods compared (all planned on the same instance, evaluated on the same
realised demand):

    proposed  : RF forecast  -> matheuristic
    exact_mip : RF forecast  -> full MIP solved by CBC with a time limit (traditional exact)
    greedy    : RF forecast  -> greedy add heuristic + nearest-hub allocation
    kmeans    : RF forecast  -> k-means clustering, hub = region nearest the centroid
    fixed_avg : historical average demand (no forecasting) -> matheuristic
    largest   : "managerial" rule - hubs at the p largest markets
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from . import config
from .model import HAS_PULP, Instance, assign_greedy, evaluate_solution, solve_exact
from .matheuristic import construct, solve_matheuristic


def solve_greedy(inst: Instance) -> dict:
    t0 = time.time()
    hubs = construct(inst)
    assign = assign_greedy(inst, hubs)
    return {"status": "Heuristic", "hubs": sorted(hubs), "assign": assign,
            "objective": inst.objective(hubs, assign), "seconds": round(time.time() - t0, 2)}


def solve_kmeans(inst: Instance) -> dict:
    t0 = time.time()
    xy = inst.regions[["lat", "lon"]].to_numpy()
    km = KMeans(n_clusters=inst.p, n_init=10, random_state=config.RANDOM_STATE)
    km.fit(xy, sample_weight=inst.demand)
    hubs = []
    for c in km.cluster_centers_:
        d = ((xy - c) ** 2).sum(axis=1)
        for j in np.argsort(d):
            if j not in hubs:
                hubs.append(int(j))
                break
    assign = assign_greedy(inst, hubs)
    return {"status": "Clustering", "hubs": sorted(hubs), "assign": assign,
            "objective": inst.objective(hubs, assign), "seconds": round(time.time() - t0, 2)}


def solve_largest_markets(inst: Instance) -> dict:
    t0 = time.time()
    hubs = [int(j) for j in np.argsort(-inst.demand)[: inst.p]]
    assign = assign_greedy(inst, hubs)
    return {"status": "Rule", "hubs": sorted(hubs), "assign": assign,
            "objective": inst.objective(hubs, assign), "seconds": round(time.time() - t0, 2)}


METHODS = {
    "proposed": ("RF forecast + matheuristic (proposed)", solve_matheuristic),
    "exact_mip": ("RF forecast + exact MIP (CBC, time-limited)", solve_exact),
    "greedy": ("RF forecast + greedy heuristic", solve_greedy),
    "kmeans": ("RF forecast + k-means clustering", solve_kmeans),
    "largest": ("Largest markets rule (no optimisation)", solve_largest_markets),
}


def run_comparison(regions: pd.DataFrame, forecast: np.ndarray, realized: np.ndarray,
                   hist_avg: np.ndarray, params: dict | None = None, exact_time_limit: float = 60,
                   verbose: bool = True) -> dict:
    params = params or {}
    inst = Instance.from_forecast(regions, forecast, **params)
    results = {}
    for key, (label, fn) in METHODS.items():
        if key == "exact_mip" and not HAS_PULP:
            continue
        if verbose:
            print(f"  {label} ...", end=" ", flush=True)
        sol = fn(inst, time_limit=exact_time_limit) if key == "exact_mip" else fn(inst)
        if sol.get("assign") is None:
            if verbose:
                print("no solution")
            continue
        kpi = evaluate_solution(inst, sol["hubs"], sol["assign"], realized)
        kpi_plan = evaluate_solution(inst, sol["hubs"], sol["assign"])
        results[key] = {"label": label, "status": sol["status"], "seconds": sol["seconds"],
                        "planned_objective": round(sol["objective"], 0),
                        "planned_cost": kpi_plan["total_cost"], **kpi}
        if verbose:
            print(f"cost {kpi['total_cost']:,.0f}  avg {kpi['avg_delivery_hours']}h  "
                  f"fulfil {kpi['fulfilment_rate']:.3f}  rel {kpi['reliability_sla']:.3f}  ({sol['seconds']}s)")

    # fixed-demand baseline: plan on the historical average instead of the forecast
    if verbose:
        print("  Historical-average demand + matheuristic (no forecasting) ...", end=" ", flush=True)
    inst_fixed = Instance.from_forecast(regions, hist_avg, **params)
    sol = solve_matheuristic(inst_fixed)
    # hubs were sized for the historical average, so evaluate with those capacities
    kpi = evaluate_solution(inst_fixed, sol["hubs"], sol["assign"], realized)
    results["fixed_avg"] = {"label": "Historical-average demand + matheuristic (no forecast)",
                            "status": sol["status"], "seconds": sol["seconds"],
                            "planned_objective": round(sol["objective"], 0),
                            "planned_cost": evaluate_solution(inst_fixed, sol["hubs"], sol["assign"])["total_cost"],
                            **kpi}
    if verbose:
        print(f"cost {kpi['total_cost']:,.0f}  avg {kpi['avg_delivery_hours']}h  "
              f"fulfil {kpi['fulfilment_rate']:.3f}  rel {kpi['reliability_sla']:.3f}")

    base = results["proposed"]["total_cost"]
    for r in results.values():
        r["cost_vs_proposed_pct"] = round((r["total_cost"] - base) / base * 100, 2)
    summary = {"params": inst.params, "realized_total_demand": int(realized.sum()),
               "forecast_total_demand": int(forecast.sum()), "methods": results}
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.COMPARISON_JSON.write_text(json.dumps(summary, indent=2, default=float))
    return summary


def load_comparison() -> dict:
    return json.loads(config.COMPARISON_JSON.read_text()) if config.COMPARISON_JSON.exists() else {}
