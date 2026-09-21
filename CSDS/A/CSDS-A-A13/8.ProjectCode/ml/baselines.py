"""Common manual seating methods, used as baselines for the engine.

All three fill halls in the given order, row by row, skipping blocked seats,
and ignore the anti-cheating rules - exactly what a spreadsheet plan does.
"""
from __future__ import annotations

import re
from collections import defaultdict, deque

import numpy as np

import ml  # noqa: F401
from app.services.engine import EngineCandidate, EngineHall, Placement, Rules

_ROLL = re.compile(r"^(.*?)(\d+)$")


def roll_sort_key(roll_no: str) -> tuple[str, int, str]:
    match = _ROLL.match(roll_no.strip())
    if match:
        return match.group(1).upper(), int(match.group(2)), roll_no
    return roll_no.upper(), -1, roll_no


def seat_order(halls: list[EngineHall]) -> list[tuple[str, int, int]]:
    return [
        (hall.key, r, c)
        for hall in halls
        for r in range(hall.rows)
        for c in range(hall.cols)
        if (r, c) not in hall.blocked
    ]


def _fill(ordered: list[EngineCandidate], halls: list[EngineHall]) -> list[Placement]:
    seats = seat_order(halls)
    if len(ordered) > len(seats):
        raise ValueError(f"{len(ordered)} candidates but only {len(seats)} seats")
    return [Placement(candidate=c.key, hall=h, row=r, col=col) for c, (h, r, col) in zip(ordered, seats)]


def sequential(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, seed: int = 0) -> list[Placement]:
    """Roll-number order, row by row: the classic spreadsheet plan."""
    return _fill(sorted(candidates, key=lambda c: roll_sort_key(c.roll_no)), halls)


def round_robin(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, seed: int = 0) -> list[Placement]:
    """Papers interleaved in a repeating cycle (largest paper first): the usual improved manual plan."""
    by_paper: dict[str, list[EngineCandidate]] = defaultdict(list)
    for cand in candidates:
        by_paper[cand.paper].append(cand)
    queues = [deque(sorted(group, key=lambda c: roll_sort_key(c.roll_no)))
              for _, group in sorted(by_paper.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
    ordered: list[EngineCandidate] = []
    while any(queues):
        for queue in queues:
            if queue:
                ordered.append(queue.popleft())
    return _fill(ordered, halls)


def random_shuffle(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, seed: int = 0) -> list[Placement]:
    """A random permutation with no rules at all."""
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(candidates))
    return _fill([candidates[i] for i in order], halls)


BASELINES = {
    "Sequential": sequential,
    "Round-robin": round_robin,
    "Random shuffle": random_shuffle,
}
