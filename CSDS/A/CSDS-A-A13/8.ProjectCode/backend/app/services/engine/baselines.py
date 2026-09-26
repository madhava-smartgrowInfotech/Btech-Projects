"""Common manual seating methods, used for comparison.

All three fill halls in the given order, row by row, skipping blocked seats,
and ignore the anti-cheating rules - what a spreadsheet plan usually does.
"""
from __future__ import annotations

from collections import defaultdict, deque

import numpy as np

from app.services.engine.rolls import roll_sort_key
from app.services.engine.types import EngineCandidate, EngineHall, Placement, Rules


def seat_order(halls: list[EngineHall]) -> list[tuple[str, int, int]]:
    return [(hall.key, r, c) for hall in halls for r, c in hall.seats]


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
    order = np.random.default_rng(seed).permutation(len(candidates))
    return _fill([candidates[i] for i in order], halls)


BASELINES = {
    "Sequential": sequential,
    "Round-robin": round_robin,
    "Random shuffle": random_shuffle,
}
