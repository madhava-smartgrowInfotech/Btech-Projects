"""Manual seat moves on a hall map, checked against the same rules the engine uses."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFound
from app.models import Hall, Plan, SeatAssignment, SessionPaper, User
from app.models.plan import PLAN_ARCHIVED
from app.services import audit
from app.services.engine.graph import parse_seat_label, seat_label, seat_neighbours
from app.services.engine.rolls import roll_distance, violates_gap
from app.services.halls import engine_hall
from app.services.plans import engine_rules, refresh_scorecard


@dataclass
class Occupant:
    assignment: SeatAssignment
    roll_no: str
    paper: str
    course: str
    department: str
    needs_accessible: bool


def paper_keys(db: Session, plan: Plan) -> dict[int, str]:
    """course id -> the paper it is written on (its paper group, or its own code)."""
    return {p.course_id: (p.paper_group or p.course.code)
            for p in db.scalars(select(SessionPaper).where(SessionPaper.session_id == plan.session_id))}


def hall_occupancy(db: Session, plan: Plan, hall: Hall) -> dict[tuple[int, int], Occupant]:
    papers = paper_keys(db, plan)
    rows = db.scalars(select(SeatAssignment).where(SeatAssignment.plan_id == plan.id, SeatAssignment.hall_id == hall.id))
    return {(a.row, a.col): Occupant(a, a.candidate.roll_no, papers.get(a.course_id, a.course.code), a.course.code,
                                     a.candidate.department.code, a.candidate.needs_accessible_seat) for a in rows}


def _check(plan: Plan, hall: Hall, occupancy: dict, src: tuple[int, int], dst: tuple[int, int]) -> dict:
    """Would moving the candidate on src to dst (swapping with whoever sits there) keep every rule?"""
    rules = engine_rules(plan.rules)
    ehall = engine_hall(hall)
    neighbours = seat_neighbours(ehall, rules.adjacency)
    after = dict(occupancy)
    mover, other = after.pop(src), after.pop(dst, None)
    after[dst] = mover
    if other is not None:
        after[src] = other
    reasons: list[str] = []
    notes: list[str] = []
    accessible = ehall.accessible

    def check_seat(seat: tuple[int, int], who: Occupant) -> None:
        label = seat_label(*seat)
        if who.needs_accessible and seat not in accessible:
            reasons.append(f"{who.roll_no} needs an accessible seat and {label} is not one.")
        for n in neighbours.get(seat, []):
            near = after.get(n)
            if near is None or near is who:
                continue
            if near.paper == who.paper:
                reasons.append(f"{who.roll_no} would sit next to {near.roll_no} ({seat_label(*n)}) - both write {who.paper}.")
            if violates_gap(who.roll_no, near.roll_no, rules.roll_gap):
                reasons.append(f"Roll numbers {who.roll_no} and {near.roll_no} ({seat_label(*n)}) are only "
                               f"{roll_distance(who.roll_no, near.roll_no)} apart (minimum {rules.roll_gap}).")
            if rules.department_mix and near.department == who.department and near.paper != who.paper:
                notes.append(f"{who.roll_no} and {near.roll_no} are both from {who.department}.")

    check_seat(dst, mover)
    if other is not None:
        check_seat(src, other)
    # Report each problem once even when both seats see it.
    return {"ok": not reasons, "reasons": list(dict.fromkeys(reasons)), "notes": list(dict.fromkeys(notes))}


def _seat(ehall_seats: set, label: str) -> tuple[int, int]:
    seat = parse_seat_label(label)
    if seat is None or seat not in ehall_seats:
        raise AppError(f"Seat {label} does not exist in this hall.", 404)
    return seat


def _load(db: Session, plan_id: int, hall_id: int) -> tuple[Plan, Hall]:
    plan = db.get(Plan, plan_id)
    hall = db.get(Hall, hall_id)
    if plan is None:
        raise NotFound("Plan")
    if hall is None or hall.id not in plan.hall_ids:
        raise NotFound("Hall in this plan")
    return plan, hall


def swap_options(db: Session, plan_id: int, hall_id: int, seat: str) -> dict:
    plan, hall = _load(db, plan_id, hall_id)
    seats = set(engine_hall(hall).seats)
    src = _seat(seats, seat)
    occupancy = hall_occupancy(db, plan, hall)
    if src not in occupancy:
        raise AppError(f"Seat {seat.upper()} is empty. Pick up an occupied seat.", 400)
    targets = []
    for dst in sorted(seats):
        if dst == src:
            continue
        verdict = _check(plan, hall, occupancy, src, dst)
        targets.append({"seat": seat_label(*dst), "occupied": dst in occupancy, **verdict})
    return {"seat": seat_label(*src), "candidate": occupancy[src].roll_no, "targets": targets}


def apply_swap(db: Session, plan_id: int, hall_id: int, src_label: str, dst_label: str, user: User) -> dict:
    plan, hall = _load(db, plan_id, hall_id)
    if plan.status == PLAN_ARCHIVED:
        raise AppError("This version has been replaced; seats can only be changed on current versions.", 409)
    seats = set(engine_hall(hall).seats)
    src, dst = _seat(seats, src_label), _seat(seats, dst_label)
    if src == dst:
        raise AppError("Pick a different seat.", 400)
    occupancy = hall_occupancy(db, plan, hall)
    if src not in occupancy:
        raise AppError(f"Seat {src_label.upper()} is empty.", 400)
    verdict = _check(plan, hall, occupancy, src, dst)
    if not verdict["ok"]:
        raise AppError("This move is not allowed: " + " ".join(verdict["reasons"]), 409, details=verdict)

    mover, other = occupancy[src], occupancy.get(dst)
    # Move through a temporary position so the (plan, hall, row, col) uniqueness holds at every flush.
    mover.assignment.row, mover.assignment.col = -1, -1
    db.flush()
    if other is not None:
        other.assignment.row, other.assignment.col = src
        other.assignment.seat_label = seat_label(*src)
        db.flush()
    mover.assignment.row, mover.assignment.col = dst
    mover.assignment.seat_label = seat_label(*dst)
    plan.swaps += 1
    db.flush()
    db.expire(plan, ["seats"])
    card = refresh_scorecard(db, plan)
    what = (f"swapped {mover.roll_no} ({seat_label(*src)}) with {other.roll_no} ({seat_label(*dst)})" if other
            else f"moved {mover.roll_no} from {seat_label(*src)} to {seat_label(*dst)}")
    audit.record(db, "plan.seat_moved", f"{user.full_name} {what} in {hall.code}, {plan.session.label} v{plan.version}",
                 actor=user, plan_id=plan.id,
                 details={"hall": hall.code, "from": seat_label(*src), "to": seat_label(*dst), "notes": verdict["notes"]})
    db.commit()
    return {"ok": True, "message": what[0].upper() + what[1:], "notes": verdict["notes"],
            "assignment_hash": plan.assignment_hash, "hard_ok": card["hard_ok"]}
