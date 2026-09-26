"""Stage A - hall and colour-class allocation.

Decides, for every hall, how many candidates of each (paper, department,
accessible-need) group it receives, and which colour class of the hall's
seat graph each paper occupies. Seats of one colour class are never
neighbours, so confining each paper to one class per hall guarantees that
no two neighbours write the same paper - by construction, before any seat
is chosen. Several papers may share a class (they are never neighbours of
each other either).

1. Hall selection. Compact strategy: the fewest halls, largest first, that
   provably fit every paper into colour classes. Balanced: every hall.
2. CP-SAT allocation over the selected halls. Hard: every candidate placed,
   class and hall capacity, accessible seats. Objective (lexicographic):
   lowest peak fill, papers and departments spread across halls, each
   department kept to one class per hall.
3. A second CP-SAT pass keeps that objective value and follows seeded random
   weights, so the classes and halls a paper gets cannot be predicted.
"""
from __future__ import annotations

import time
from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np
from ortools.sat.python import cp_model

from app.services.engine.graph import class_count, seat_classes
from app.services.engine.types import EngineCandidate, EngineHall, Rules

GroupKey = tuple[str, str, bool]  # (paper, department, needs accessible seat)


@dataclass
class HallAllocation:
    counts: dict[str, dict[GroupKey, int]]      # hall -> group -> candidates
    paper_class: dict[str, dict[str, int]]      # hall -> paper -> colour class
    status: str
    ms: int


def _class_sizes(halls: list[EngineHall], adjacency: int) -> tuple[dict, dict]:
    seats = {h.key: {k: len(v) for k, v in seat_classes(h, adjacency).items()} for h in halls}
    access = {h.key: {k: sum(1 for s in v if s in h.accessible) for k, v in seat_classes(h, adjacency).items()}
              for h in halls}
    return seats, access


def greedy_pack(sizes: Counter, halls: list[EngineHall], class_seats: dict, class_access: dict,
                capacity: dict[str, int], rng: np.random.Generator) -> dict | None:
    """Best-fit packing: each paper, largest first, repeatedly takes the emptiest colour class
    of a hall it is not in yet. Returns None when it cannot place everyone."""
    rem = {h.key: dict(class_seats[h.key]) for h in halls}
    rem_acc = {h.key: dict(class_access[h.key]) for h in halls}
    room = {h.key: capacity[h.key] for h in halls}
    by_paper: dict[str, list[list]] = defaultdict(list)
    for g, size in sorted(sizes.items()):
        by_paper[g[0]].append([g, size])
    n: dict[tuple[str, GroupKey], int] = {}
    cls: dict[tuple[str, str], int] = {}
    acc: dict[tuple[str, str, int], int] = {}
    for paper in sorted(by_paper, key=lambda p: (-sum(s for _, s in by_paper[p]), p)):
        pending = sorted(by_paper[paper], key=lambda gs: not gs[0][2])  # accessible needs first
        left = sum(s for _, s in pending)
        need_acc = sum(s for g, s in pending if g[2])
        while left:
            # While candidates who need accessible seats are waiting, prefer classes that have them;
            # a class without any only helps if it can take everyone else.
            options = []
            for h in rem:
                if (h, paper) in cls:
                    continue
                for k in rem[h]:
                    space = min(rem[h][k], room[h])
                    has_acc = rem_acc[h][k] > 0
                    if space <= 0 or (need_acc and not has_acc and left - need_acc <= 0):
                        continue
                    options.append((bool(need_acc) and has_acc, space, rng.random(), h, k))
            if not options:
                return None
            _, space, _, key, k = max(options)
            placed = 0
            for item in pending:
                g, size = item
                if size == 0 or placed >= space:
                    continue
                take = min(size, space - placed)
                if g[2]:
                    take = min(take, rem_acc[key][k])
                    rem_acc[key][k] -= take
                    need_acc -= take
                    if take:
                        acc[key, paper, k] = acc.get((key, paper, k), 0) + take
                if take:
                    n[key, g] = n.get((key, g), 0) + take
                    item[1] -= take
                    placed += take
            cls[key, paper] = k
            rem[key][k] -= placed
            room[key] -= placed
            left -= placed
            if placed == 0:
                return None
    return {"n": n, "class": cls, "acc": acc}


def select_halls(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, capacity: dict[str, int],
                 rng_seed: int) -> list[EngineHall]:
    """Compact strategy: the smallest set of the largest halls that can hold everyone."""
    if rules.fill_strategy == "balanced":
        return list(halls)
    sizes = Counter((c.paper, c.department, c.needs_accessible) for c in candidates)
    ordered = sorted(halls, key=lambda h: (-capacity[h.key], h.key))
    needed_acc = sum(c.needs_accessible for c in candidates)
    class_seats, class_access = _class_sizes(halls, rules.adjacency)
    for count in range(1, len(ordered) + 1):
        chosen = ordered[:count]
        if sum(capacity[h.key] for h in chosen) < len(candidates):
            continue
        if sum(len(h.accessible_seats) for h in chosen) < needed_acc:
            continue
        if greedy_pack(sizes, chosen, class_seats, class_access, capacity, np.random.default_rng(rng_seed)):
            return sorted(chosen, key=lambda h: halls.index(h))
    return list(halls)


def _solver(seed: int, budget: float) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = seed % 2**31
    solver.parameters.max_deterministic_time = budget
    return solver


def allocate(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, *,
             capacity: dict[str, int], seed: int, budget: float) -> HallAllocation | None:
    started = time.perf_counter()
    halls = select_halls(candidates, halls, rules, capacity, seed)
    sizes = Counter((c.paper, c.department, c.needs_accessible) for c in candidates)
    groups = sorted(sizes)
    papers = sorted({g[0] for g in groups})
    departments = sorted({g[1] for g in groups})
    paper_depts: dict[str, set[str]] = defaultdict(set)
    for g in groups:
        paper_depts[g[0]].add(g[1])
    accessible_papers = {g[0] for g in groups if g[2]}
    classes = range(class_count(rules.adjacency))
    class_seats, class_access = _class_sizes(halls, rules.adjacency)
    total = len(candidates)

    model = cp_model.CpModel()
    n = {(h.key, g): model.NewIntVar(0, min(sizes[g], capacity[h.key]), "") for h in halls for g in groups}
    z, m, a = {}, {}, {}
    for h in halls:
        for p in papers:
            for k in classes:
                z[h.key, p, k] = model.NewBoolVar("")
                m[h.key, p, k] = model.NewIntVar(0, class_seats[h.key][k], "")
                model.Add(m[h.key, p, k] <= class_seats[h.key][k] * z[h.key, p, k])
                if p in accessible_papers:
                    a[h.key, p, k] = model.NewIntVar(0, class_access[h.key][k], "")
                    model.Add(a[h.key, p, k] <= class_access[h.key][k] * z[h.key, p, k])
                    model.Add(a[h.key, p, k] <= m[h.key, p, k])
    peak = model.NewIntVar(0, 100, "peak_fill")
    top_paper, top_dept, w = {}, {}, {}

    for g in groups:
        model.Add(sum(n[h.key, g] for h in halls) == sizes[g])

    for h in halls:
        key = h.key
        occupancy = sum(n[key, g] for g in groups)
        model.Add(occupancy <= capacity[key])
        model.Add(100 * occupancy <= h.capacity * peak)
        top_paper[key] = model.NewIntVar(0, h.capacity, "")
        for p in papers:
            in_paper = sum(n[key, g] for g in groups if g[0] == p)
            model.AddAtMostOne(z[key, p, k] for k in classes)
            model.Add(sum(m[key, p, k] for k in classes) == in_paper)
            model.Add(top_paper[key] >= in_paper)
            if p in accessible_papers:
                model.Add(sum(a[key, p, k] for k in classes) == sum(n[key, g] for g in groups if g[0] == p and g[2]))
        for k in classes:
            model.Add(sum(m[key, p, k] for p in papers) <= class_seats[key][k])
            if accessible_papers:
                model.Add(sum(a[key, p, k] for p in accessible_papers) <= class_access[key][k])
        if rules.department_mix and len(departments) > 1:
            top_dept[key] = model.NewIntVar(0, h.capacity, "")
            for d in departments:
                model.Add(top_dept[key] >= sum(n[key, g] for g in groups if g[1] == d))
                # A department spread over several classes of one hall can sit next to itself.
                dept_papers = [p for p in papers if d in paper_depts[p]]
                if len(dept_papers) > 1:
                    for k in classes:
                        w[key, d, k] = model.NewBoolVar("")
                        for p in dept_papers:
                            model.Add(w[key, d, k] >= z[key, p, k])

    spread = sum(top_paper.values()) + sum(top_dept.values()) + 5 * sum(w.values())
    peak_weight = 2 * total + 5 * len(w) + 1
    primary = spread + peak_weight * peak

    # Warm start from the greedy packing.
    rng = np.random.default_rng(seed)
    start = greedy_pack(sizes, halls, class_seats, class_access, capacity, rng)
    if start:
        occ: Counter = Counter()
        per_paper: Counter = Counter()
        per_dept: Counter = Counter()
        for (hk, g), v in start["n"].items():
            occ[hk] += v
            per_paper[hk, g[0]] += v
            per_dept[hk, g[1]] += v
        for (hk, g), var in n.items():
            model.AddHint(var, start["n"].get((hk, g), 0))
        for (hk, p, k), var in z.items():
            chosen = start["class"].get((hk, p)) == k
            model.AddHint(var, chosen)
            model.AddHint(m[hk, p, k], per_paper[hk, p] if chosen else 0)
            if (hk, p, k) in a:
                model.AddHint(a[hk, p, k], start["acc"].get((hk, p, k), 0))
        for hk, var in top_paper.items():
            model.AddHint(var, max((v for (h2, _), v in per_paper.items() if h2 == hk), default=0))
        for hk, var in top_dept.items():
            model.AddHint(var, max((v for (h2, _), v in per_dept.items() if h2 == hk), default=0))
        for (hk, d, k), var in w.items():
            model.AddHint(var, any(start["class"].get((hk, p)) == k and d in paper_depts[p] for p in papers))
        model.AddHint(peak, max(-(-100 * occ[h.key] // h.capacity) for h in halls))

    # Pass 1: the best allocation.
    model.Minimize(primary)
    solver = _solver(seed, budget)
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    best = int(solver.ObjectiveValue())
    status_name = solver.StatusName(status).lower()

    # Pass 2: among allocations that are just as good, follow seeded random weights,
    # so which class (and hall) a paper gets cannot be predicted.
    model.ClearObjective()
    model.ClearHints()
    model.Add(primary <= best)
    keys = sorted(z)
    weights = rng.integers(0, 1000, size=len(keys))
    model.Maximize(cp_model.LinearExpr.WeightedSum([z[k] for k in keys], [int(v) for v in weights]))
    for var in [*n.values(), *z.values(), *m.values(), *a.values(), *top_paper.values(), *top_dept.values(),
                *w.values(), peak]:
        model.AddHint(var, solver.Value(var))
    solver2 = _solver(seed + 1, budget / 2)
    status2 = solver2.Solve(model)
    final = solver2 if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE) else solver

    counts: dict[str, dict[GroupKey, int]] = {}
    paper_class: dict[str, dict[str, int]] = {}
    for h in halls:
        per_group = {g: int(final.Value(n[h.key, g])) for g in groups}
        per_group = {g: v for g, v in per_group.items() if v}
        if not per_group:
            continue
        counts[h.key] = per_group
        present = sorted({g[0] for g in per_group})
        paper_class[h.key] = {p: next(k for k in classes if final.BooleanValue(z[h.key, p, k])) for p in present}
    return HallAllocation(counts=counts, paper_class=paper_class, status=status_name,
                          ms=round((time.perf_counter() - started) * 1000))
