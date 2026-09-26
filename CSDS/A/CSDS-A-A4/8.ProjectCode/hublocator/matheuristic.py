"""Objective 4 - solve the hub location problem efficiently with a matheuristic.

A matheuristic embeds exact mathematical programming inside a heuristic
search. Here the search is over *which* hubs are open; every time a hub set
is examined, the allocation of regions to those hubs is solved exactly with
a small MIP (`assign_exact`). Three phases:

    1. Construction   - demand-weighted greedy + k-medoids seeding
    2. Local search   - swap / drop / add moves on the hub set; each move is
                        priced by the exact assignment sub-MIP (first-improvement)
    3. Kernel search  - a restricted full MIP over the "kernel" of promising
                        candidate hubs discovered during the search, with a
                        short time limit, to polish the solution

Runs in seconds even when the full MIP would need minutes, and the result
carries an exact allocation for the chosen hubs.
"""
from __future__ import annotations

import time

import numpy as np

from .model import HAS_PULP, Instance, assign_exact, assign_greedy, solve_exact


def _bound(inst: Instance, hubs: list[int]) -> float:
    """Cheap estimate of a hub set's cost (capacity-aware greedy allocation)."""
    a = assign_greedy(inst, hubs)
    return inst.objective(hubs, a)


def _price(inst: Instance, hubs: list[int], cache: dict, time_limit: float):
    key = tuple(sorted(hubs))
    if key in cache:
        return cache[key]
    assign, status = assign_exact(inst, list(key), time_limit)
    if assign is None:                     # infeasible (capacity / SLA) -> huge cost
        cache[key] = (None, float("inf"))
        return cache[key]
    obj = inst.objective(list(key), assign)
    cache[key] = (assign, obj)
    return cache[key]


def construct(inst: Instance) -> list[int]:
    """Greedy weighted k-medoids: repeatedly open the hub that most reduces cost."""
    hubs: list[int] = []
    remaining = set(range(inst.n))
    while len(hubs) < inst.p:
        best, best_cost = None, float("inf")
        for j in remaining:
            trial = hubs + [j]
            cost = (inst.unit_cost[:, trial] * inst.demand[:, None]).min(axis=1).sum() + inst.fixed_cost[trial].sum()
            if cost < best_cost:
                best, best_cost = j, cost
        hubs.append(best)
        remaining.remove(best)
    # medoid refinement on the un-capacitated problem
    for _ in range(10):
        changed = False
        for k, h in enumerate(hubs):
            members = np.where(np.argmin(inst.unit_cost[:, hubs], axis=1) == k)[0]
            if len(members) == 0:
                continue
            costs = [(inst.unit_cost[members, m] * inst.demand[members]).sum() + inst.fixed_cost[m] for m in members]
            new = int(members[int(np.argmin(costs))])
            if new != h and new not in hubs:
                hubs[k] = new
                changed = True
        if not changed:
            break
    return hubs


def solve_matheuristic(inst: Instance, time_limit: float | None = None, kernel_size: int = 24,
                       sub_time_limit: float = 5, verbose: bool = False, log: list | None = None,
                       screen_tol: float = 0.06) -> dict:
    t0 = time.time()
    time_limit = time_limit or inst.params["time_limit"]
    cache: dict = {}
    log = log if log is not None else []

    hubs = construct(inst)
    assign, obj = _price(inst, hubs, cache, sub_time_limit)
    if assign is None:      # construction infeasible - open more hubs greedily until feasible
        for j in np.argsort(-inst.demand):
            if len(hubs) >= inst.p:
                break
            if j not in hubs:
                hubs.append(int(j))
                assign, obj = _price(inst, hubs, cache, sub_time_limit)
                if assign is not None:
                    break
    log.append({"phase": "construction", "hubs": sorted(hubs), "objective": obj, "t": round(time.time() - t0, 2)})
    if verbose:
        print(f"  construction: {obj:,.0f}  hubs={[inst.regions.city[h] for h in hubs]}")

    # ---- phase 2: MIP-priced local search --------------------------------
    improved = True
    iters = 0
    while improved and time.time() - t0 < time_limit * 0.7:
        improved = False
        iters += 1
        # rank closed candidates by attractiveness (weighted demand near them)
        closed = [j for j in range(inst.n) if j not in hubs]
        attractiveness = {j: (inst.demand * np.exp(-inst.dist[:, j] / 400)).sum() for j in closed}
        closed.sort(key=lambda j: -attractiveness[j])
        top = closed[: max(12, inst.n // 4)]
        moves = [("swap", h, j) for h in hubs for j in top]
        if len(hubs) > 1:
            moves += [("drop", h, None) for h in hubs]
        if len(hubs) < inst.p:
            moves += [("add", None, j) for j in top]
        # screen every move with the cheap greedy bound, price the promising ones exactly
        scored = []
        for kind, h, j in moves:
            trial = [x for x in hubs if x != h] + ([j] if j is not None else [])
            scored.append((_bound(inst, trial), kind, h, j, trial))
        scored.sort(key=lambda t: t[0])
        for b, kind, h, j, trial in scored:
            if time.time() - t0 > time_limit * 0.7:
                break
            if b > obj * (1 + screen_tol):
                break                                  # greedy bound too poor to be worth a MIP
            a, o = _price(inst, trial, cache, sub_time_limit)
            if o < obj - 1e-6:
                hubs, assign, obj, improved = trial, a, o, True
                log.append({"phase": f"local-search {kind}", "hubs": sorted(hubs), "objective": o,
                            "t": round(time.time() - t0, 2)})
                if verbose:
                    print(f"  {kind:<5} -> {o:,.0f}  hubs={[inst.regions.city[x] for x in hubs]}")
                break   # first improvement

    # ---- phase 3: kernel search (restricted exact MIP) --------------------
    kernel_status = "skipped"
    if HAS_PULP:
        visited = sorted(cache.items(), key=lambda kv: kv[1][1])
        kernel = set(hubs)
        for h in hubs:                                   # geographic neighbours of open hubs
            kernel.update(int(j) for j in np.argsort(inst.dist[h])[1:3])
        for key, _ in visited:
            kernel.update(key)
            if len(kernel) >= kernel_size:
                break
        # also admit the most attractive closed candidates not yet examined
        attractiveness = np.array([(inst.demand * np.exp(-inst.dist[:, j] / 400)).sum() for j in range(inst.n)])
        for j in np.argsort(-attractiveness):
            if len(kernel) >= kernel_size:
                break
            kernel.add(int(j))
        remaining = max(2.0, time_limit - (time.time() - t0))
        res = solve_exact(inst, time_limit=remaining, candidates=sorted(kernel))
        kernel_status = res["status"]
        if res.get("assign") is not None and res["objective"] < obj - 1e-6:
            hubs, assign, obj = res["hubs"], res["assign"], res["objective"]
            log.append({"phase": "kernel-search", "hubs": sorted(hubs), "objective": obj,
                        "t": round(time.time() - t0, 2)})
            if verbose:
                print(f"  kernel -> {obj:,.0f}  hubs={[inst.regions.city[x] for x in hubs]}")

    if assign is None:
        assign = assign_greedy(inst, hubs)
        obj = inst.objective(hubs, assign)
    return {"status": "Matheuristic", "hubs": sorted(int(h) for h in hubs), "assign": assign,
            "objective": obj, "seconds": round(time.time() - t0, 2), "iterations": iters,
            "subproblems_solved": len(cache), "kernel_status": kernel_status, "log": log}
