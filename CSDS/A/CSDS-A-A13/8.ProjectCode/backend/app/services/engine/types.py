"""Plain data types the seating engine works on (no database objects)."""
from __future__ import annotations

from dataclasses import dataclass, field

Seat = tuple[int, int]  # (row, column), both 0-based


@dataclass(frozen=True)
class Rules:
    adjacency: int = 8            # 8 = sides, front, back and diagonals; 4 = no diagonals
    roll_gap: int = 5             # neighbours' roll numbers must differ by at least this (0/1 = off)
    department_mix: bool = True   # spread departments and minimise same-department neighbours
    fill_strategy: str = "compact"  # "compact" = fewest halls, "balanced" = every hall, even fill


@dataclass(frozen=True)
class EngineCandidate:
    key: str                # stable identifier
    roll_no: str
    paper: str              # conflict class: the course code, or its paper group
    course: str
    department: str
    needs_accessible: bool = False


@dataclass(frozen=True)
class EngineHall:
    key: str
    rows: int
    cols: int
    blocked: frozenset[Seat] = frozenset()
    accessible: frozenset[Seat] = frozenset()
    aisles_after: frozenset[int] = frozenset()  # an aisle runs after these column numbers (1-based)

    @property
    def seats(self) -> list[Seat]:
        return [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in self.blocked]

    @property
    def capacity(self) -> int:
        return self.rows * self.cols - len(self.blocked)

    @property
    def accessible_seats(self) -> list[Seat]:
        return sorted(s for s in self.accessible if s not in self.blocked)


@dataclass(frozen=True)
class Placement:
    candidate: str
    hall: str
    row: int
    col: int


@dataclass
class EngineResult:
    ok: bool
    placements: list[Placement]
    reasons: list[str]
    seed: int
    solve_ms: int
    stats: dict = field(default_factory=dict)
