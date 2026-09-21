"""Independent plan checker.

Re-checks every rule on a finished plan without using the solver, and
produces the scorecard shown in the product. The same checks back live swap
validation, so the UI, the exports and the benchmark all agree.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field

from app.services.engine.graph import seat_label, seat_neighbours
from app.services.engine.rolls import roll_distance, violates_gap
from app.services.engine.types import EngineCandidate, EngineHall, Placement, Rules

MAX_LISTED_VIOLATIONS = 200


@dataclass
class Scorecard:
    candidates: int = 0
    placed: int = 0
    unplaced: int = 0
    capacity_violations: int = 0
    same_paper_pairs: int = 0
    roll_gap_violations: int = 0
    accessible_violations: int = 0
    same_department_pairs: int = 0
    neighbour_pairs: int = 0
    halls_used: int = 0
    seats_in_used_halls: int = 0
    utilisation: float = 0.0
    hard_ok: bool = True
    per_hall: list[dict] = field(default_factory=list)
    violations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def validate(candidates: list[EngineCandidate], halls: list[EngineHall], placements: list[Placement],
             rules: Rules) -> Scorecard:
    card = Scorecard(candidates=len(candidates))
    by_key = {c.key: c for c in candidates}
    hall_by_key = {h.key: h for h in halls}
    violations: list[dict] = []

    def note(kind: str, hall: str, seats: list[tuple[int, int]], who: list[str], detail: str) -> None:
        if len(violations) < MAX_LISTED_VIOLATIONS:
            violations.append({"type": kind, "hall": hall, "seats": [seat_label(*s) for s in seats],
                               "candidates": who, "detail": detail})

    seat_of: dict[tuple[str, int, int], str] = {}
    seated: set[str] = set()
    for p in placements:
        hall = hall_by_key.get(p.hall)
        cand = by_key.get(p.candidate)
        if p.candidate in seated:
            card.capacity_violations += 1
            note("capacity", p.hall, [(p.row, p.col)], [p.candidate], "candidate has more than one seat")
            continue
        if hall is None or cand is None:
            card.capacity_violations += 1
            note("capacity", p.hall, [], [p.candidate], "unknown hall or candidate")
            continue
        if not (0 <= p.row < hall.rows and 0 <= p.col < hall.cols) or (p.row, p.col) in hall.blocked:
            card.capacity_violations += 1
            note("capacity", p.hall, [(p.row, p.col)], [p.candidate], "seat does not exist or is blocked")
            continue
        slot = (p.hall, p.row, p.col)
        if slot in seat_of:
            card.capacity_violations += 1
            note("capacity", p.hall, [(p.row, p.col)], [seat_of[slot], p.candidate], "two candidates on one seat")
            continue
        seat_of[slot] = p.candidate
        seated.add(p.candidate)
        if cand.needs_accessible and (p.row, p.col) not in hall.accessible:
            card.accessible_violations += 1
            note("accessible", p.hall, [(p.row, p.col)], [p.candidate], "needs an accessible seat")

    card.placed = len(seated)
    card.unplaced = len(candidates) - card.placed
    card.capacity_violations += card.unplaced

    occupied_by_hall: dict[str, dict[tuple[int, int], str]] = defaultdict(dict)
    for (hall_key, r, c), cand_key in seat_of.items():
        occupied_by_hall[hall_key][(r, c)] = cand_key

    for hall in halls:
        occupied = occupied_by_hall.get(hall.key, {})
        if not occupied:
            continue
        stats = Counter()
        for seat, cand_key in occupied.items():
            me = by_key[cand_key]
            for other_seat in seat_neighbours(hall, rules.adjacency).get(seat, []):
                if other_seat <= seat or other_seat not in occupied:
                    continue
                other = by_key[occupied[other_seat]]
                stats["neighbour_pairs"] += 1
                if me.paper == other.paper:
                    stats["same_paper_pairs"] += 1
                    note("same_paper", hall.key, [seat, other_seat], [me.key, other.key],
                         f"both write {me.paper}")
                if violates_gap(me.roll_no, other.roll_no, rules.roll_gap):
                    stats["roll_gap_violations"] += 1
                    note("roll_gap", hall.key, [seat, other_seat], [me.key, other.key],
                         f"roll numbers {roll_distance(me.roll_no, other.roll_no)} apart (minimum {rules.roll_gap})")
                if me.department == other.department:
                    stats["same_department_pairs"] += 1
        papers = Counter(by_key[k].paper for k in occupied.values())
        departments = Counter(by_key[k].department for k in occupied.values())
        card.halls_used += 1
        card.seats_in_used_halls += hall.capacity
        card.neighbour_pairs += stats["neighbour_pairs"]
        card.same_paper_pairs += stats["same_paper_pairs"]
        card.roll_gap_violations += stats["roll_gap_violations"]
        card.same_department_pairs += stats["same_department_pairs"]
        card.per_hall.append({
            "hall": hall.key,
            "seats": hall.capacity,
            "placed": len(occupied),
            "utilisation": round(len(occupied) / hall.capacity, 4) if hall.capacity else 0.0,
            "papers": dict(sorted(papers.items())),
            "departments": dict(sorted(departments.items())),
            "same_paper_pairs": stats["same_paper_pairs"],
            "roll_gap_violations": stats["roll_gap_violations"],
            "same_department_pairs": stats["same_department_pairs"],
            "neighbour_pairs": stats["neighbour_pairs"],
        })

    card.utilisation = round(card.placed / card.seats_in_used_halls, 4) if card.seats_in_used_halls else 0.0
    card.hard_ok = not (card.capacity_violations or card.same_paper_pairs or card.roll_gap_violations
                        or card.accessible_violations)
    card.violations = violations
    return card
