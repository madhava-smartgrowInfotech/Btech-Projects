"""Convert stored halls to the engine's layout type."""
from __future__ import annotations

from app.models import Hall
from app.services.engine import EngineHall
from app.services.engine.graph import parse_seat_label


def _seats(labels: list[str] | None) -> frozenset[tuple[int, int]]:
    out = set()
    for label in labels or []:
        seat = parse_seat_label(label)
        if seat is not None:
            out.add(seat)
    return frozenset(out)


def engine_hall(hall: Hall) -> EngineHall:
    return EngineHall(
        key=hall.code,
        rows=hall.rows,
        cols=hall.cols,
        blocked=_seats(hall.blocked_seats),
        accessible=_seats(hall.accessible_seats),
        aisles_after=frozenset(hall.aisles_after_cols or []),
    )
