"""Seeded benchmark scenarios for the seating engine.

Each scenario is one exam session: candidates spread over several papers and
departments, and a set of halls large enough to seat them. Everything is
derived from the scenario seed, so a scenario can be rebuilt exactly.

    python -m ml.scenarios            # list the scenario matrix
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

import ml  # noqa: F401  (adds the backend to the import path)
from app.services.engine import EngineCandidate, EngineHall, Rules

# (rows, columns, aisle after these column numbers)
HALL_SHAPES: list[tuple[int, int, tuple[int, ...]]] = [
    (6, 6, ()),
    (6, 8, (4,)),
    (8, 8, (4,)),
    (8, 10, (5,)),
    (10, 10, (5,)),
    (10, 12, (4, 8)),
]
HALL_SHAPE_WEIGHTS = [0.10, 0.20, 0.25, 0.20, 0.15, 0.10]
MAX_PAPER_SHARE = 0.22   # no single paper takes more than 22% of a session
ACCESSIBLE_SEATS_PER_HALL = 2


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    candidates: int
    papers: int
    departments: int
    adjacency: int = 8
    roll_gap: int = 5
    accessible_share: float = 0.01
    target_fill: float = 0.80
    seed: int = 2026


@dataclass
class Scenario:
    spec: ScenarioSpec
    candidates: list[EngineCandidate]
    halls: list[EngineHall]
    rules: Rules

    @property
    def seats(self) -> int:
        return sum(h.rows * h.cols - len(h.blocked) for h in self.halls)


SCENARIOS: list[ScenarioSpec] = [
    ScenarioSpec("xs-150", 150, 4, 3),
    ScenarioSpec("s-300", 300, 6, 4),
    ScenarioSpec("m-600", 600, 8, 6),
    ScenarioSpec("l-1000", 1000, 10, 7),
    ScenarioSpec("xl-2000", 2000, 14, 8),
    ScenarioSpec("m-600-adj4", 600, 8, 6, adjacency=4),
    ScenarioSpec("m-600-gap0", 600, 8, 6, roll_gap=0),
    ScenarioSpec("m-600-gap10", 600, 8, 6, roll_gap=10),
]
SIZE_SCENARIOS = ["xs-150", "s-300", "m-600", "l-1000", "xl-2000"]
TYPICAL = "m-600"


def spec_by_name(name: str) -> ScenarioSpec:
    for spec in SCENARIOS:
        if spec.name == name:
            return spec
    raise KeyError(f"unknown scenario {name!r}")


def _paper_sizes(rng: np.random.Generator, total: int, papers: int) -> list[int]:
    """Uneven paper sizes that add up to ``total``, none above the share cap."""
    cap = math.floor(total * MAX_PAPER_SHARE)
    if cap * papers < total:
        raise ValueError(f"{papers} papers cannot hold {total} candidates under the {MAX_PAPER_SHARE:.0%} cap")
    sizes = np.floor(rng.dirichlet(np.full(papers, 4.0)) * total).astype(int)
    sizes = np.clip(sizes, 8, cap)
    while sizes.sum() != total:
        if sizes.sum() < total:
            room = np.flatnonzero(sizes < cap)
            sizes[rng.choice(room)] += 1
        else:
            spare = np.flatnonzero(sizes > 8)
            sizes[rng.choice(spare)] -= 1
    return sizes.tolist()


def _independence_bound(rows: int, cols: int, aisles: tuple[int, ...], adjacency: int) -> int:
    """Upper bound on seats one paper can take in an empty hall of this shape."""
    edges = [0, *aisles, cols]
    blocks = [b - a for a, b in zip(edges, edges[1:])]
    if adjacency == 8:
        return sum(math.ceil(rows / 2) * math.ceil(w / 2) for w in blocks)
    return sum(math.ceil(rows * w / 2) for w in blocks)


def _make_hall(rng: np.random.Generator, index: int) -> EngineHall:
    shape = HALL_SHAPES[rng.choice(len(HALL_SHAPES), p=HALL_SHAPE_WEIGHTS)]
    rows, cols, aisles = shape
    accessible = frozenset((0, c) for c in range(ACCESSIBLE_SEATS_PER_HALL))
    candidates = [(r, c) for r in range(1, rows) for c in range(cols)]
    n_blocked = int(rng.integers(0, 4))
    picks = rng.choice(len(candidates), size=n_blocked, replace=False) if n_blocked else []
    blocked = frozenset(candidates[i] for i in picks)
    return EngineHall(
        key=f"H{index + 1:02d}",
        rows=rows,
        cols=cols,
        blocked=blocked,
        accessible=accessible,
        aisles_after=frozenset(aisles),
    )


def build(spec: ScenarioSpec) -> Scenario:
    rng = np.random.default_rng(spec.seed + spec.candidates * 7919 + spec.papers)
    sizes = _paper_sizes(rng, spec.candidates, spec.papers)

    # Every department gets at least one paper; the rest are shared out at random.
    dept_codes = [f"D{chr(ord('A') + i)}" for i in range(spec.departments)]
    paper_dept = dept_codes + [str(d) for d in rng.choice(dept_codes, size=spec.papers - spec.departments)]
    rng.shuffle(paper_dept)
    papers = [f"P{i + 1:02d}" for i in range(spec.papers)]

    # Candidates of one department get serial roll numbers in random order, so
    # papers of the same department interleave and the roll-gap rule matters.
    candidates: list[EngineCandidate] = []
    for dept in dept_codes:
        members = [p for p, d in zip(papers, paper_dept) if d == dept]
        seats = [p for p in members for _ in range(sizes[papers.index(p)])]
        rng.shuffle(seats)
        serial = int(rng.integers(1, 40))
        for paper in seats:
            candidates.append(EngineCandidate(
                key=f"{dept}24{serial:04d}",
                roll_no=f"{dept}24{serial:04d}",
                paper=paper,
                course=paper,
                department=dept,
                needs_accessible=bool(rng.random() < spec.accessible_share),
            ))
            serial += 1 + int(rng.random() < 0.15)  # occasional gaps: not everyone sits every session

    # Add halls until capacity, accessible seats and the per-paper ceiling all fit.
    halls: list[EngineHall] = []
    needed_seats = math.ceil(spec.candidates / spec.target_fill)
    needed_accessible = sum(c.needs_accessible for c in candidates)
    largest = max(sizes)
    while True:
        seats = sum(h.rows * h.cols - len(h.blocked) for h in halls)
        bound = sum(_independence_bound(h.rows, h.cols, tuple(sorted(h.aisles_after)), spec.adjacency) for h in halls)
        accessible = sum(len(h.accessible) for h in halls)
        if seats >= needed_seats and bound >= largest / 0.85 and accessible >= needed_accessible:
            break
        halls.append(_make_hall(rng, len(halls)))

    rules = Rules(adjacency=spec.adjacency, roll_gap=spec.roll_gap)
    return Scenario(spec=spec, candidates=candidates, halls=halls, rules=rules)


def describe(scenario: Scenario) -> dict:
    return {
        **asdict(scenario.spec),
        "halls": len(scenario.halls),
        "seats": scenario.seats,
        "accessible_candidates": sum(c.needs_accessible for c in scenario.candidates),
    }


if __name__ == "__main__":
    for spec in SCENARIOS:
        info = describe(build(spec))
        print(f"{info['name']:<12} candidates={info['candidates']:>5} papers={info['papers']:>2} "
              f"halls={info['halls']:>3} seats={info['seats']:>5} adjacency={info['adjacency']} "
              f"roll_gap={info['roll_gap']:>2} accessible={info['accessible_candidates']}")
