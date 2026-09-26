"""The seat graph of a hall: which seats are neighbours, and its colouring.

With 8-neighbour adjacency this is a "king's graph" on the seat grid. All
candidates writing one paper in a hall must form an independent set of this
graph (no two of them adjacent). The engine uses a proper colouring of the
graph: seats of one colour class are never neighbours, so a paper confined
to one class can never sit next to itself.
"""
from __future__ import annotations

from functools import lru_cache

from app.services.engine.types import EngineHall, Seat

_OFFSETS = {
    4: ((-1, 0), (1, 0), (0, -1), (0, 1)),
    8: ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)),
}


def seat_label(row: int, col: int) -> str:
    """Row letter(s) + column number: (2, 3) -> "C4"."""
    letters = ""
    n = row
    while True:
        letters = chr(ord("A") + n % 26) + letters
        n = n // 26 - 1
        if n < 0:
            break
    return f"{letters}{col + 1}"


def parse_seat_label(label: str) -> Seat | None:
    text = label.strip().upper()
    letters = "".join(ch for ch in text if ch.isalpha())
    digits = text[len(letters):]
    if not letters or not digits.isdigit() or text != letters + digits:
        return None
    row = 0
    for ch in letters:
        row = row * 26 + (ord(ch) - ord("A") + 1)
    return row - 1, int(digits) - 1


def _crosses_aisle(c1: int, c2: int, aisles_after: frozenset[int]) -> bool:
    if c1 == c2:
        return False
    # "aisle after column k" (1-based) separates 0-based columns k-1 and k.
    return (min(c1, c2) + 1) in aisles_after


def neighbours_of(hall: EngineHall, seat: Seat, adjacency: int) -> list[Seat]:
    r, c = seat
    out = []
    for dr, dc in _OFFSETS[adjacency]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < hall.rows and 0 <= nc < hall.cols and (nr, nc) not in hall.blocked \
                and not _crosses_aisle(c, nc, hall.aisles_after):
            out.append((nr, nc))
    return out


def seat_neighbours(hall: EngineHall, adjacency: int) -> dict[Seat, list[Seat]]:
    return _neighbours_cached(hall, adjacency)


@lru_cache(maxsize=512)
def _neighbours_cached(hall: EngineHall, adjacency: int) -> dict[Seat, list[Seat]]:
    return {seat: neighbours_of(hall, seat, adjacency) for seat in hall.seats}


def seat_edges(hall: EngineHall, adjacency: int) -> list[tuple[Seat, Seat]]:
    """Each neighbouring pair once, in a stable order."""
    edges = []
    for seat, around in seat_neighbours(hall, adjacency).items():
        for other in around:
            if seat < other:
                edges.append((seat, other))
    return edges


def seat_class(seat: Seat, adjacency: int) -> int:
    """Colour of a seat in a proper colouring of the seat graph.

    8 neighbours: four classes by (row parity, column parity) - two seats of one
    class differ by at least two rows or two columns, so they are never
    neighbours. 4 neighbours: the two chessboard colours. Aisles and blocked
    seats only remove edges, so the colouring stays valid.
    """
    r, c = seat
    return (r % 2) * 2 + (c % 2) if adjacency == 8 else (r + c) % 2


def class_count(adjacency: int) -> int:
    return 4 if adjacency == 8 else 2


@lru_cache(maxsize=512)
def _classes_cached(hall: EngineHall, adjacency: int) -> dict[int, tuple[Seat, ...]]:
    classes: dict[int, list[Seat]] = {k: [] for k in range(class_count(adjacency))}
    for seat in hall.seats:
        classes[seat_class(seat, adjacency)].append(seat)
    return {k: tuple(v) for k, v in classes.items()}


def seat_classes(hall: EngineHall, adjacency: int) -> dict[int, tuple[Seat, ...]]:
    """Usable seats grouped by colour class. Any set of same-class seats has no two neighbours."""
    return _classes_cached(hall, adjacency)


def paper_ceiling(hall: EngineHall, adjacency: int) -> int:
    """Most candidates of one paper the engine will place in this hall (its largest colour class)."""
    return max((len(v) for v in seat_classes(hall, adjacency).values()), default=0)
