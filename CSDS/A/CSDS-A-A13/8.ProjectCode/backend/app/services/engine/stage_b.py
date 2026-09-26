"""Stage B - seat layout inside one hall.

Stage A gave every paper in the hall one colour class of the seat graph, so
same-paper neighbours are already impossible. This stage decides which
candidate sits on which seat of their paper's class. Boolean x[candidate,
seat] model solved with CP-SAT:

* every candidate gets exactly one seat of their class, every seat holds at
  most one candidate; candidates who need an accessible seat only get
  accessible seats;
* roll-number spacing: for every pair of candidates whose roll numbers are
  too close, a candidate on seat s forbids the other on any neighbour of s;
* objective: minimise same-department neighbour pairs, then maximise a
  seeded random weight - so the result is one random valid layout, not the
  solver's first structured one.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from ortools.sat.python import cp_model

from app.services.engine.graph import seat_classes, seat_edges, seat_neighbours
from app.services.engine.rolls import close_pairs
from app.services.engine.types import EngineCandidate, EngineHall, Placement, Rules, Seat

RANDOM_WEIGHT_RANGE = 20


@dataclass
class HallSolve:
    hall: str
    ok: bool
    status: str
    placements: list[Placement]
    ms: int
    same_department_pairs: int | None = None


def solve_hall(hall: EngineHall, cands: list[EngineCandidate], paper_class: dict[str, int], rules: Rules, *,
               seed: int, budget: float, workers: int = 1) -> HallSolve:
    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    classes = seat_classes(hall, rules.adjacency)
    seats = hall.seats
    seat_index = {s: i for i, s in enumerate(seats)}
    accessible = set(hall.accessible_seats)
    neighbours = seat_neighbours(hall, rules.adjacency)

    allowed: list[list[Seat]] = []
    for cand in cands:
        pool = classes[paper_class[cand.paper]]
        allowed.append([s for s in pool if s in accessible] if cand.needs_accessible else list(pool))

    model = cp_model.CpModel()
    x: dict[tuple[int, int], cp_model.IntVar] = {}
    by_seat: dict[int, list] = defaultdict(list)
    for ci, options in enumerate(allowed):
        row = []
        for s in options:
            var = model.NewBoolVar("")
            x[ci, seat_index[s]] = var
            by_seat[seat_index[s]].append(var)
            row.append(var)
        model.AddExactlyOne(row)
    for vars_on_seat in by_seat.values():
        if len(vars_on_seat) > 1:
            model.AddAtMostOne(vars_on_seat)

    # Roll-number spacing. Pairs in the same class can never be neighbours, so only
    # pairs in different classes need a constraint.
    for i, j in close_pairs([c.roll_no for c in cands], rules.roll_gap):
        if paper_class[cands[i].paper] == paper_class[cands[j].paper]:
            continue
        for s in allowed[i]:
            around = [x[j, seat_index[t]] for t in neighbours[s] if (j, seat_index[t]) in x]
            if around:
                model.AddAtMostOne([x[i, seat_index[s]], *around])

    # Department mix: a department spread over several classes can sit next to itself.
    penalties = []
    if rules.department_mix:
        dept_classes: dict[str, set[int]] = defaultdict(set)
        for cand in cands:
            dept_classes[cand.department].add(paper_class[cand.paper])
        for dept, used_classes in dept_classes.items():
            if len(used_classes) < 2:
                continue
            members = [ci for ci, c in enumerate(cands) if c.department == dept]
            for a, b in seat_edges(hall, rules.adjacency):
                ta = [x[ci, seat_index[a]] for ci in members if (ci, seat_index[a]) in x]
                tb = [x[ci, seat_index[b]] for ci in members if (ci, seat_index[b]) in x]
                if ta and tb:
                    p = model.NewBoolVar("")
                    model.Add(cp_model.LinearExpr.Sum(ta + tb) - 1 <= p)
                    penalties.append(p)

    keys = list(x)
    weights = rng.integers(0, RANDOM_WEIGHT_RANGE, size=len(keys))
    random_term = cp_model.LinearExpr.WeightedSum([x[k] for k in keys], [int(w) for w in weights])
    if penalties:
        dept_weight = len(cands) * RANDOM_WEIGHT_RANGE + 1
        model.Minimize(dept_weight * cp_model.LinearExpr.Sum(penalties) - random_term)
    else:
        model.Maximize(random_term)

    # Hint: a random assignment inside each class (valid unless two close roll numbers meet).
    taken: set[Seat] = set()
    for ci in sorted(range(len(cands)), key=lambda i: (not cands[i].needs_accessible, i)):
        options = [allowed[ci][k] for k in rng.permutation(len(allowed[ci]))]
        for s in options:
            if s not in taken:
                taken.add(s)
                model.AddHint(x[ci, seat_index[s]], 1)
                break

    solver = cp_model.CpSolver()
    params = solver.parameters
    params.random_seed = seed % 2**31
    params.max_deterministic_time = budget
    if workers > 1:
        params.num_workers = workers
        params.interleave_search = True  # several strategies, run deterministically in one thread
    else:
        params.num_workers = 1
    status = solver.Solve(model)
    ms = round((time.perf_counter() - started) * 1000)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        name = "infeasible" if status == cp_model.INFEASIBLE else "no_solution_in_budget"
        return HallSolve(hall=hall.key, ok=False, status=name, placements=[], ms=ms)

    placements = []
    for (ci, si), var in x.items():
        if solver.BooleanValue(var):
            r, c = seats[si]
            placements.append(Placement(candidate=cands[ci].key, hall=hall.key, row=r, col=c))
    same_dept = sum(solver.BooleanValue(p) for p in penalties)
    return HallSolve(hall=hall.key, ok=True, status=solver.StatusName(status).lower(), placements=placements,
                     ms=ms, same_department_pairs=int(same_dept))
