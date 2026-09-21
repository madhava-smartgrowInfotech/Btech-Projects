"""Fairness and unpredictability measures for a seating method.

A fair, cheat-resistant plan should not let anyone predict a seat from a
roll number, should not seat the same people together every time, and
should not favour any department with front-row seats.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

import numpy as np

import ml  # noqa: F401
from app.services.engine import EngineCandidate, EngineHall, Placement, Rules
from app.services.engine.graph import seat_neighbours
from ml.baselines import roll_sort_key


def roll_seat_correlation(candidates: list[EngineCandidate], halls: list[EngineHall],
                          placements: list[Placement]) -> float:
    """Spearman correlation between roll order and seat order (hall, row, column)."""
    hall_index = {h.key: i for i, h in enumerate(halls)}
    roll_rank = {c.key: i for i, c in enumerate(sorted(candidates, key=lambda c: roll_sort_key(c.roll_no)))}
    seats = sorted(placements, key=lambda p: (hall_index[p.hall], p.row, p.col))
    x = np.array([roll_rank[p.candidate] for p in seats], dtype=float)
    y = np.arange(len(seats), dtype=float)
    x_rank = np.argsort(np.argsort(x)).astype(float)
    return float(np.corrcoef(x_rank, y)[0, 1])


def neighbour_pairs(halls: list[EngineHall], placements: list[Placement], rules: Rules) -> set[frozenset[str]]:
    by_seat = {(p.hall, p.row, p.col): p.candidate for p in placements}
    pairs: set[frozenset[str]] = set()
    for hall in halls:
        for seat, around in seat_neighbours(hall, rules.adjacency).items():
            me = by_seat.get((hall.key, *seat))
            if me is None:
                continue
            for other_seat in around:
                other = by_seat.get((hall.key, *other_seat))
                if other is not None:
                    pairs.add(frozenset((me, other)))
    return pairs


def neighbour_overlap(first: set[frozenset[str]], second: set[frozenset[str]]) -> float:
    """Share of one plan's neighbour pairs that are neighbours again in another plan."""
    return len(first & second) / len(first) if first else 0.0


def front_row_bias(candidates: list[EngineCandidate], placements: list[Placement]) -> float:
    """Largest gap (percentage points) between a department's front-row share and its overall share."""
    dept = {c.key: c.department for c in candidates}
    overall = Counter(dept.values())
    front = Counter(dept[p.candidate] for p in placements if p.row == 0)
    total_front = sum(front.values()) or 1
    return max(abs(front[d] / total_front - n / len(candidates)) for d, n in overall.items()) * 100


def evaluate_method(scenario, method, seeds: list[int]) -> dict:
    """Run ``method(candidates, halls, rules, seed)`` for every seed and summarise predictability."""
    plans = [method(scenario.candidates, scenario.halls, scenario.rules, seed) for seed in seeds]
    correlations = [abs(roll_seat_correlation(scenario.candidates, scenario.halls, p)) for p in plans]
    pairs = [neighbour_pairs(scenario.halls, p, scenario.rules) for p in plans]
    overlaps = [neighbour_overlap(a, b) for a, b in combinations(pairs, 2)]
    biases = [front_row_bias(scenario.candidates, p) for p in plans]
    return {
        "seeds": len(seeds),
        "abs_roll_seat_correlation": float(np.mean(correlations)),
        "neighbour_overlap": float(np.mean(overlaps)) if overlaps else None,
        "front_row_bias_pp": float(np.mean(biases)),
    }
