"""Seating plans: generate, publish, verify and delete."""
from __future__ import annotations

import hashlib
import json
import logging
import secrets
from collections import Counter

import numpy as np
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, NotFound
from app.ml.profile import hall_budget
from app.models import (
    AttendanceMark, ExamSession, Hall, InvigilatorAssignment, Plan, SeatAssignment, User,
)
from app.models._common import utcnow
from app.models.plan import PLAN_ARCHIVED, PLAN_DRAFT, PLAN_PUBLISHED
from app.models.user import ROLE_INVIGILATOR, STATUS_ACTIVE
from app.schemas.settings import RulesIn
from app.services import audit
from app.services.engine import (
    ENGINE_VERSION, EngineCandidate, EngineHall, Placement, Rules, derive_seed, solve, validate,
)
from app.services.engine.baselines import sequential
from app.services.engine.graph import seat_label
from app.services.halls import engine_hall
from app.services.sessions import session_entries

log = logging.getLogger("app.plans")


def engine_rules(rules: dict | RulesIn) -> Rules:
    data = rules.model_dump() if isinstance(rules, RulesIn) else rules
    return Rules(adjacency=int(data["adjacency"]), roll_gap=int(data["roll_gap"]),
                 department_mix=bool(data["department_mix"]), fill_strategy=data["fill_strategy"])


def load_inputs(db: Session, session: ExamSession, hall_ids: list[int]) -> tuple[list[EngineCandidate], list[EngineHall], dict, dict]:
    """Engine inputs for a sitting, plus lookups back to database ids."""
    entries = session_entries(db, session.id)
    candidates = [EngineCandidate(key=cand.roll_no, roll_no=cand.roll_no, paper=group or course.code,
                                  course=course.code, department=cand.department.code,
                                  needs_accessible=cand.needs_accessible_seat) for cand, course, group in entries]
    ids = {cand.roll_no: (cand.id, course.id) for cand, course, _ in entries}
    halls_db = {h.id: h for h in db.scalars(select(Hall).where(Hall.id.in_(hall_ids)))}
    missing = [i for i in hall_ids if i not in halls_db]
    if missing:
        raise AppError("Some selected halls no longer exist. Refresh the page and choose the halls again.")
    ordered = [halls_db[i] for i in hall_ids]
    return candidates, [engine_hall(h) for h in ordered], ids, {h.code: h for h in ordered}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def data_fingerprint(candidates: list[EngineCandidate], halls: list[EngineHall], rules: Rules, budget: float) -> str:
    return _sha({
        "engine": ENGINE_VERSION,
        "rules": [rules.adjacency, rules.roll_gap, rules.department_mix, rules.fill_strategy],
        "budget": budget,
        "candidates": sorted([c.key, c.paper, c.course, c.department, c.needs_accessible] for c in candidates),
        "halls": [[h.key, h.rows, h.cols, sorted(h.blocked), sorted(h.accessible), sorted(h.aisles_after)] for h in halls],
    })


def placements_hash(placements: list[Placement]) -> str:
    return _sha(sorted([p.candidate, p.hall, p.row, p.col] for p in placements))


def plan_placements(plan: Plan, halls_by_id: dict[int, Hall]) -> list[Placement]:
    return [Placement(candidate=s.candidate.roll_no, hall=halls_by_id[s.hall_id].code, row=s.row, col=s.col)
            for s in plan.seats]


def _baseline(candidates, halls, rules) -> dict:
    try:
        card = validate(candidates, halls, sequential(candidates, halls, rules), rules)
    except ValueError:
        return {}
    return {"method": "sequential roll order", "same_paper_pairs": card.same_paper_pairs,
            "roll_gap_violations": card.roll_gap_violations, "same_department_pairs": card.same_department_pairs,
            "accessible_violations": card.accessible_violations, "neighbour_pairs": card.neighbour_pairs}


def _assign_invigilators(db: Session, plan: Plan, hall_ids: list[int], seed: int) -> int:
    staff = db.scalars(select(User).where(User.role == ROLE_INVIGILATOR, User.status == STATUS_ACTIVE)
                       .order_by(User.id)).all()
    if not staff:
        return 0
    load = Counter(dict(db.execute(
        select(InvigilatorAssignment.user_id, func.count())
        .join(Plan, Plan.id == InvigilatorAssignment.plan_id)
        .where(Plan.status != PLAN_ARCHIVED, Plan.session_id != plan.session_id)
        .group_by(InvigilatorAssignment.user_id)).all()))
    rng = np.random.default_rng(derive_seed(seed, "invigilators"))
    tiebreak = {u.id: float(rng.random()) for u in staff}
    ordered = sorted(staff, key=lambda u: (load[u.id], tiebreak[u.id]))
    for user, hall_id in zip(ordered, hall_ids):
        db.add(InvigilatorAssignment(plan_id=plan.id, hall_id=hall_id, user_id=user.id))
    return min(len(staff), len(hall_ids))


def generate(db: Session, session_id: int, rules_in: RulesIn, hall_ids: list[int] | None, seed: int | None,
             user: User) -> Plan:
    session = db.get(ExamSession, session_id)
    if session is None:
        raise NotFound("Sitting")
    if not hall_ids:
        hall_ids = list(db.scalars(select(Hall.id).where(Hall.is_active.is_(True)).order_by(Hall.code)))
    if not hall_ids:
        raise AppError("There are no available halls. Import halls or mark some as available.")
    hall_ids = list(dict.fromkeys(hall_ids))
    rules = engine_rules(rules_in)
    seed = int(seed) if seed is not None else secrets.randbelow(2**31 - 1) + 1
    candidates, halls, ids, hall_by_code = load_inputs(db, session, hall_ids)
    if not candidates:
        raise AppError("No candidates are registered for the papers in this sitting.")

    budget = hall_budget()
    settings = get_settings()
    result = solve(candidates, halls, rules, seed=seed, budget=budget, threads=settings.solver_threads or None,
                   max_retries=settings.solver_max_retries)
    if not result.ok:
        audit.record(db, "plan.failed", f"{user.full_name} could not generate a plan for {session.label}",
                     actor=user, details={"seed": seed, "rules": rules_in.model_dump(), "reasons": result.reasons})
        db.commit()
        raise AppError("A plan could not be generated: " + " ".join(result.reasons), 422, details=result.reasons)

    card = validate(candidates, halls, result.placements, rules)
    if not card.hard_ok:  # never store a plan that breaks a hard rule
        log.error("Engine returned a plan that fails validation", extra={"session": session.id, "seed": seed})
        raise AppError("The engine produced a plan that failed the final check. Please try again with another seed.", 500)

    version = (db.scalar(select(func.max(Plan.version)).where(Plan.session_id == session.id)) or 0) + 1
    solver_hash = placements_hash(result.placements)
    plan = Plan(
        session_id=session.id, version=version, status=PLAN_DRAFT, seed=seed, rules=rules_in.model_dump(),
        hall_ids=hall_ids, engine_version=ENGINE_VERSION,
        data_fingerprint=data_fingerprint(candidates, halls, rules, budget),
        solver_hash=solver_hash, assignment_hash=solver_hash, solve_ms=result.solve_ms,
        stats={**result.stats, "hall_budget": budget}, scorecard=_card_summary(card),
        baseline=_baseline(candidates, halls, rules), created_by=user.id,
    )
    db.add(plan)
    db.flush()
    db.add_all(SeatAssignment(plan_id=plan.id, candidate_id=ids[p.candidate][0], course_id=ids[p.candidate][1],
                              hall_id=hall_by_code[p.hall].id, row=p.row, col=p.col, seat_label=seat_label(p.row, p.col))
               for p in result.placements)
    used_halls = [hall_by_code[k].id for k in sorted({p.hall for p in result.placements})]
    assigned = _assign_invigilators(db, plan, used_halls, seed)
    audit.record(
        db, "plan.generated",
        f"{user.full_name} generated version {version} for {session.label} with seed {seed}: "
        f"{card.placed} candidates in {card.halls_used} halls, {card.same_paper_pairs} same-paper neighbours, "
        f"solved in {result.solve_ms / 1000:.1f} s",
        actor=user, plan_id=plan.id,
        details={"seed": seed, "rules": rules_in.model_dump(), "data_fingerprint": plan.data_fingerprint,
                 "solver_hash": solver_hash, "halls": [h.key for h in halls], "invigilators_assigned": assigned})
    db.commit()
    log.info("Plan generated", extra={"plan": plan.id, "session": session.id, "ms": result.solve_ms, "seed": seed})
    return plan


def _card_summary(card) -> dict:
    data = card.to_dict()
    data["violations"] = data["violations"][:50]
    return data


def get_plan(db: Session, plan_id: int) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise NotFound("Plan")
    return plan


def refresh_scorecard(db: Session, plan: Plan) -> dict:
    """Re-validate the stored plan (after manual moves) and store the result."""
    halls_by_id = {h.id: h for h in db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids)))}
    candidates, halls, _, _ = load_inputs(db, plan.session, [i for i in plan.hall_ids if i in halls_by_id])
    placements = plan_placements(plan, halls_by_id)
    card = validate(candidates, halls, placements, engine_rules(plan.rules))
    plan.scorecard = _card_summary(card)
    plan.assignment_hash = placements_hash(placements)
    return plan.scorecard


def publish(db: Session, plan: Plan, user: User) -> Plan:
    if plan.status == PLAN_PUBLISHED:
        return plan
    if plan.status == PLAN_ARCHIVED:
        raise AppError("This version was replaced by a newer published version. Publish a current version instead.", 409)
    card = refresh_scorecard(db, plan)
    if not card["hard_ok"]:
        raise AppError("This plan breaks a seating rule and cannot be published. Fix the highlighted seats first.", 409)
    previous = db.scalars(select(Plan).where(Plan.session_id == plan.session_id, Plan.status == PLAN_PUBLISHED)).all()
    for old in previous:
        old.status = PLAN_ARCHIVED
    plan.status = PLAN_PUBLISHED
    plan.published_at = utcnow()
    replaced = f" (replacing version {previous[0].version})" if previous else ""
    audit.record(db, "plan.published", f"{user.full_name} published version {plan.version} for {plan.session.label}{replaced}",
                 actor=user, plan_id=plan.id, details={"assignment_hash": plan.assignment_hash})
    db.commit()
    return plan


def verify(db: Session, plan: Plan, user: User) -> dict:
    """Re-run the solver with the stored seed and rules and compare with what the solver produced originally."""
    halls_by_id = {h.id: h for h in db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids)))}
    if len(halls_by_id) != len(plan.hall_ids):
        raise AppError("A hall used by this plan was deleted, so the plan cannot be reproduced.", 409)
    candidates, halls, _, _ = load_inputs(db, plan.session, plan.hall_ids)
    rules = engine_rules(plan.rules)
    budget = float(plan.stats.get("hall_budget") or hall_budget())
    fingerprint = data_fingerprint(candidates, halls, rules, budget)
    outcome = {"plan_id": plan.id, "seed": plan.seed, "data_unchanged": fingerprint == plan.data_fingerprint,
               "stored_solver_hash": plan.solver_hash, "recomputed_hash": None, "reproduced": False,
               "manual_moves": plan.swaps, "engine_version": ENGINE_VERSION, "solve_ms": None}
    if outcome["data_unchanged"]:
        result = solve(candidates, halls, rules, seed=plan.seed, budget=budget,
                       threads=get_settings().solver_threads or None, max_retries=get_settings().solver_max_retries)
        if result.ok:
            outcome["recomputed_hash"] = placements_hash(result.placements)
            outcome["reproduced"] = outcome["recomputed_hash"] == plan.solver_hash
            outcome["solve_ms"] = result.solve_ms
    verdict = "reproduced exactly" if outcome["reproduced"] else (
        "could not be reproduced: the candidate or hall data changed" if not outcome["data_unchanged"]
        else "could not be reproduced")
    audit.record(db, "plan.verified", f"{user.full_name} verified version {plan.version} of {plan.session.label}: {verdict}",
                 actor=user, plan_id=plan.id, details=outcome)
    db.commit()
    return outcome


def delete_plan(db: Session, plan: Plan, user: User) -> None:
    if plan.status == PLAN_PUBLISHED:
        raise AppError("A published plan cannot be deleted. Publish another version first.", 409)
    if db.scalar(select(func.count()).select_from(AttendanceMark).where(AttendanceMark.plan_id == plan.id)):
        raise AppError("Attendance has been taken with this plan, so it is kept for the record.", 409)
    audit.record(db, "plan.deleted", f"{user.full_name} deleted version {plan.version} of {plan.session.label}",
                 actor=user, details={"plan_id": plan.id, "seed": plan.seed})
    db.execute(delete(Plan).where(Plan.id == plan.id))
    db.commit()
