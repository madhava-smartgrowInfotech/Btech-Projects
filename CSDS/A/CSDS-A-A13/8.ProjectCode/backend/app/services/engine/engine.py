"""The seating engine: pre-checks, Stage A (halls), Stage B (seats per hall, in parallel)."""
from __future__ import annotations

import hashlib
import logging
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.services.engine.prechecks import precheck
from app.services.engine.stage_a import allocate
from app.services.engine.stage_b import HallSolve, solve_hall
from app.services.engine.types import EngineCandidate, EngineHall, EngineResult, Placement, Rules

log = logging.getLogger("app.engine")

ENGINE_VERSION = "1.0.0"
DEFAULT_HALL_BUDGET = 0.15    # deterministic solver time per hall (tuned by ml/benchmark.py)
STAGE_A_BUDGET = 0.3
DEFAULT_WORKERS_PER_HALL = 1
MAX_RETRIES = 5
SLOW_HALL_BUDGET_FACTOR = 4   # a hall that found nothing in time gets one longer try


def derive_seed(seed: int, label: str) -> int:
    """A stable sub-seed (independent of Python's hash randomisation)."""
    digest = hashlib.sha256(f"{seed}:{label}".encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def _split_by_hall(candidates: list[EngineCandidate], counts: dict[str, dict], halls: list[EngineHall],
                   rng: np.random.Generator) -> dict[str, list[EngineCandidate]]:
    """Give each hall the allocated number of candidates from every group, chosen at random."""
    groups: dict[tuple, list[EngineCandidate]] = defaultdict(list)
    for cand in candidates:
        groups[(cand.paper, cand.department, cand.needs_accessible)].append(cand)
    out: dict[str, list[EngineCandidate]] = defaultdict(list)
    for key in sorted(groups):
        pool = [groups[key][i] for i in rng.permutation(len(groups[key]))]
        start = 0
        for hall in halls:
            take = counts.get(hall.key, {}).get(key, 0)
            out[hall.key].extend(pool[start:start + take])
            start += take
    return {k: sorted(v, key=lambda c: c.key) for k, v in out.items() if v}


def solve(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, *, seed: int,
          budget: float | None = None, threads: int | None = None, workers_per_hall: int | None = None,
          max_retries: int = MAX_RETRIES) -> EngineResult:
    """Seat every candidate. Deterministic for the same inputs, rules, seed and budget."""
    started = time.perf_counter()
    budget = budget or DEFAULT_HALL_BUDGET
    workers_per_hall = workers_per_hall or DEFAULT_WORKERS_PER_HALL
    threads = threads or os.cpu_count() or 4
    candidates = sorted(candidates, key=lambda c: c.key)
    stats: dict = {"engine_version": ENGINE_VERSION, "hall_budget": budget, "attempts": []}

    def done(ok: bool, placements: list[Placement], reasons: list[str]) -> EngineResult:
        ms = round((time.perf_counter() - started) * 1000)
        stats["solve_ms"] = ms
        return EngineResult(ok=ok, placements=placements, reasons=reasons, seed=seed, solve_ms=ms, stats=stats)

    reasons = precheck(candidates, halls, rules)
    if reasons:
        return done(False, [], reasons)

    capacity = {h.key: h.capacity for h in halls}
    hall_by_key = {h.key: h for h in halls}

    for attempt in range(max_retries + 1):
        allocation = None
        for stretch in (1, 4):
            allocation = allocate(candidates, halls, rules, capacity=capacity,
                                  seed=derive_seed(seed, f"stage-a-{attempt}"), budget=STAGE_A_BUDGET * stretch)
            if allocation is not None:
                break
        if allocation is None:
            return done(False, [], [
                "No way to share the candidates between the selected halls satisfies every rule. "
                "Select more halls, or relax the rules (4-neighbour adjacency or a smaller roll-number gap)."])

        rng = np.random.default_rng(derive_seed(seed, f"split-{attempt}"))
        per_hall = _split_by_hall(candidates, allocation.counts, halls, rng)
        stage_b_started = time.perf_counter()

        def run(keys: list[str], hall_budget: float) -> dict[str, HallSolve]:
            with ThreadPoolExecutor(max_workers=min(threads, max(1, len(keys)))) as pool:
                futures = {
                    key: pool.submit(solve_hall, hall_by_key[key], per_hall[key], allocation.paper_class[key], rules,
                                     seed=derive_seed(seed, f"hall-{key}-{attempt}"), budget=hall_budget,
                                     workers=workers_per_hall)
                    for key in keys
                }
                return {key: f.result() for key, f in futures.items()}

        results = run(sorted(per_hall), budget)
        slow = sorted(k for k, r in results.items() if r.status == "no_solution_in_budget")
        if slow:
            results.update(run(slow, budget * SLOW_HALL_BUDGET_FACTOR))

        failed = sorted(k for k, r in results.items() if not r.ok)
        stats["attempts"].append({
            "attempt": attempt + 1,
            "stage_a_ms": allocation.ms,
            "stage_a_status": allocation.status,
            "stage_b_ms": round((time.perf_counter() - stage_b_started) * 1000),
            "halls_given_more_time": slow,
            "halls": {k: {"candidates": len(per_hall[k]), "status": r.status, "ms": r.ms,
                          "paper_class": allocation.paper_class[k],
                          "same_department_pairs": r.same_department_pairs} for k, r in sorted(results.items())},
            "failed_halls": failed,
        })
        if not failed:
            placements = [p for key in sorted(results) for p in results[key].placements]
            stats["halls_used"] = len(results)
            stats["retries"] = attempt
            log.info("Plan solved", extra={"candidates": len(candidates), "halls": len(results),
                                           "attempts": attempt + 1, "seed": seed})
            return done(True, placements, [])

        # Ease the halls that could not be laid out and share their load elsewhere.
        for key in failed:
            load = len(per_hall[key])
            capacity[key] = max(0, load - max(1, load // 10))
        log.info("Re-balancing halls", extra={"failed": ",".join(failed), "attempt": attempt + 1})

    return done(False, [], [
        "The engine could not lay out every hall within its time budget. "
        f"Halls that failed: {', '.join(stats['attempts'][-1]['failed_halls'])}. "
        "Select more halls so each one is less full, or relax the rules."])
