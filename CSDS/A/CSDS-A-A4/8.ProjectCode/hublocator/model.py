"""Objective 3 - hub location as an optimisation problem with cost, time and
capacity constraints.

Capacitated single-allocation hub location (p-hub with fixed costs):

    min  sum_j f_j y_j                                   fixed hub cost
       + sum_ij (r * dist_ij + lam * time_ij) * d_i x_ij  transport + delivery-time cost
    s.t. sum_j x_ij = 1               each region served by exactly one hub
         x_ij <= y_j                  only open hubs serve
         sum_i d_i x_ij <= C_j y_j    hub capacity
         sum_j y_j <= p               at most p hubs
         time_ij x_ij <= SLA          (optional hard service-level constraint)
         x, y binary

`Instance` holds the data, `evaluate_solution()` computes every KPI for a
given (hubs, assignment) pair, and `solve_exact()` is the traditional exact
MIP (used both as a baseline and as the building block of the matheuristic).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config
from .data import distance_matrix

try:
    import pulp
    HAS_PULP = True
except ImportError:  # pragma: no cover
    HAS_PULP = False


@dataclass
class Instance:
    regions: pd.DataFrame
    demand: np.ndarray              # forecast (or fixed) demand per region, used to plan
    dist: np.ndarray                # km, n x n
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        p = {**config.DEFAULTS, **self.params}
        self.params = p
        n = len(self.regions)
        self.n = n
        self.time = self.dist / p["truck_speed_kmph"] + p["hub_handling_hours"]   # hours
        np.fill_diagonal(self.time, p["hub_handling_hours"] * 0.5)                # local delivery
        self.unit_cost = p["transport_rate"] * self.dist + p["time_penalty"] * self.time
        tier_mult = self.regions["tier"].map({1: 1.35, 2: 1.0, 3: 0.75}).fillna(1.0).to_numpy()
        self.fixed_cost = p["fixed_cost_per_hub"] * tier_mult
        total = float(self.demand.sum())
        self.capacity = np.full(n, p["capacity_factor"] * total / p["n_hubs"])
        self.p = int(p["n_hubs"])

    @classmethod
    def from_forecast(cls, regions: pd.DataFrame, forecast: pd.Series | np.ndarray, **params):
        return cls(regions, np.asarray(forecast, dtype=float), distance_matrix(regions), params)

    # ------------------------------------------------------------------ #
    def objective(self, hubs: list[int], assign: np.ndarray, demand: np.ndarray | None = None) -> float:
        d = self.demand if demand is None else demand
        idx = np.arange(self.n)
        return float(self.fixed_cost[hubs].sum() + (self.unit_cost[idx, assign] * d).sum())


def assign_greedy(inst: Instance, hubs: list[int], demand: np.ndarray | None = None) -> np.ndarray | None:
    """Capacity-aware nearest-hub assignment (fallback when no MIP solver)."""
    d = inst.demand if demand is None else demand
    load = {h: 0.0 for h in hubs}
    assign = np.full(inst.n, -1)
    order = np.argsort(-d)                          # place big regions first
    for i in order:
        cands = sorted(hubs, key=lambda h: inst.unit_cost[i, h])
        for h in cands:
            if load[h] + d[i] <= inst.capacity[h] or (inst.params["sla_hard"] is False and h == cands[-1]):
                assign[i] = h
                load[h] += d[i]
                break
        if assign[i] == -1:
            assign[i] = cands[0]
            load[cands[0]] += d[i]
    return assign


def assign_exact(inst: Instance, hubs: list[int], time_limit: float = 10) -> tuple[np.ndarray | None, str]:
    """Solve the assignment sub-problem for a FIXED hub set exactly (small MIP)."""
    if not HAS_PULP:
        return assign_greedy(inst, hubs), "greedy"
    prob = pulp.LpProblem("assignment", pulp.LpMinimize)
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", cat="Binary") for i in range(inst.n) for j in hubs}
    prob += pulp.lpSum(inst.unit_cost[i, j] * inst.demand[i] * x[i, j] for i in range(inst.n) for j in hubs)
    for i in range(inst.n):
        prob += pulp.lpSum(x[i, j] for j in hubs) == 1
    for j in hubs:
        prob += pulp.lpSum(inst.demand[i] * x[i, j] for i in range(inst.n)) <= inst.capacity[j]
    if inst.params["sla_hard"]:
        for i in range(inst.n):
            for j in hubs:
                if inst.time[i, j] > inst.params["sla_hours"]:
                    prob += x[i, j] == 0
    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
    if pulp.LpStatus[prob.status] not in ("Optimal",):
        return None, pulp.LpStatus[prob.status]
    assign = np.array([max(hubs, key=lambda j: x[i, j].value() or 0) for i in range(inst.n)])
    return assign, "Optimal"


def solve_exact(inst: Instance, time_limit: float | None = None, candidates: list[int] | None = None,
                fix_open: list[int] | None = None) -> dict:
    """Traditional exact method: the full MIP solved by CBC (branch-and-cut).

    `candidates` restricts which regions may host a hub (used by the
    matheuristic's kernel step); `fix_open` forces hubs open.
    """
    time_limit = time_limit or inst.params["time_limit"]
    if not HAS_PULP:
        raise RuntimeError("pulp is required for the exact MIP")
    cands = list(range(inst.n)) if candidates is None else list(candidates)
    t0 = time.time()
    prob = pulp.LpProblem("hub_location", pulp.LpMinimize)
    y = {j: pulp.LpVariable(f"y_{j}", cat="Binary") for j in cands}
    x = {(i, j): pulp.LpVariable(f"x_{i}_{j}", cat="Binary") for i in range(inst.n) for j in cands}
    prob += (pulp.lpSum(inst.fixed_cost[j] * y[j] for j in cands)
             + pulp.lpSum(inst.unit_cost[i, j] * inst.demand[i] * x[i, j] for i in range(inst.n) for j in cands))
    for i in range(inst.n):
        prob += pulp.lpSum(x[i, j] for j in cands) == 1
    for j in cands:
        prob += pulp.lpSum(inst.demand[i] * x[i, j] for i in range(inst.n)) <= inst.capacity[j] * y[j]
        for i in range(inst.n):
            prob += x[i, j] <= y[j]
    prob += pulp.lpSum(y[j] for j in cands) <= inst.p
    if inst.params["sla_hard"]:
        for (i, j), v in x.items():
            if inst.time[i, j] > inst.params["sla_hours"]:
                prob += v == 0
    for j in fix_open or []:
        prob += y[j] == 1
    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
    status = pulp.LpStatus[prob.status]
    if status == "Optimal" and time.time() - t0 >= time_limit * 0.97:
        status = "Time limit (feasible)"      # CBC reports 'Optimal' even when stopped early
    hubs = [j for j in cands if (y[j].value() or 0) > 0.5]
    if not hubs:
        return {"status": status, "hubs": [], "assign": None, "seconds": time.time() - t0}
    assign = np.array([max(cands, key=lambda j: x[i, j].value() or 0) for i in range(inst.n)])
    return {"status": status, "hubs": hubs, "assign": assign, "seconds": round(time.time() - t0, 2),
            "objective": inst.objective(hubs, assign), "mip_gap_note": "optimal" if status == "Optimal" else "time limit"}


# ---------------------------------------------------------------------- #
# KPI evaluation (Objective 6 metrics)
# ---------------------------------------------------------------------- #
def evaluate_solution(inst: Instance, hubs: list[int], assign: np.ndarray,
                      realized: np.ndarray | None = None) -> dict:
    """Compute delivery time, fulfilment, reliability and cost for a configuration.

    `realized` is the demand that actually materialised (defaults to the
    planning demand). Capacity is exceeded when realised demand > planned.
    """
    d = inst.demand if realized is None else np.asarray(realized, float)
    idx = np.arange(inst.n)
    t = inst.time[idx, assign]
    dist = inst.dist[idx, assign]
    total = d.sum()

    load = np.zeros(inst.n)
    np.add.at(load, assign, d)
    served = np.minimum(load, inst.capacity)                       # orders each hub can process
    fulfil_by_hub = np.where(load > 0, served / np.maximum(load, 1e-9), 1.0)
    fulfilment = float((fulfil_by_hub[assign] * d).sum() / total)

    on_time = (t <= inst.params["sla_hours"]).astype(float)
    reliability = float((on_time * fulfil_by_hub[assign] * d).sum() / total)

    transport = float((inst.params["transport_rate"] * dist * d).sum())
    time_cost = float((inst.params["time_penalty"] * t * d).sum())
    fixed = float(inst.fixed_cost[hubs].sum())
    utilisation = {int(h): round(float(load[h] / inst.capacity[h]), 3) for h in hubs}

    return {
        "n_hubs": len(hubs),
        "hubs": [int(h) for h in hubs],
        "hub_cities": [inst.regions.city[h] for h in hubs],
        "total_cost": round(fixed + transport + time_cost, 0),
        "fixed_cost": round(fixed, 0),
        "transport_cost": round(transport, 0),
        "time_cost": round(time_cost, 0),
        "cost_per_order": round((fixed + transport + time_cost) / total, 3),
        "avg_delivery_hours": round(float((t * d).sum() / total), 2),
        "max_delivery_hours": round(float(t.max()), 2),
        "avg_distance_km": round(float((dist * d).sum() / total), 1),
        "fulfilment_rate": round(fulfilment, 4),
        "reliability_sla": round(reliability, 4),
        "overloaded_hubs": int((load[hubs] > inst.capacity[hubs] + 1e-6).sum()),
        "utilisation": utilisation,
        "assignment": [{"region": inst.regions.city[i], "region_id": inst.regions.region_id[i],
                        "hub": inst.regions.city[assign[i]], "demand": int(d[i]),
                        "distance_km": round(float(dist[i]), 1), "hours": round(float(t[i]), 1)}
                       for i in range(inst.n)],
    }
