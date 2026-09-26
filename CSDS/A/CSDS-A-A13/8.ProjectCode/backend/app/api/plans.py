from fastapi import APIRouter
from sqlalchemy import delete, select

from app.core.deps import DB, AdminUser, CurrentUser
from app.core.errors import AppError, NotFound
from app.models import ExamSession, Hall, InvigilatorAssignment, Plan, User
from app.models.plan import PLAN_ARCHIVED
from app.models.user import ROLE_INVIGILATOR, STATUS_ACTIVE
from app.schemas.plans import (
    InvigilatorsIn, PersonRef, PlanGenerateIn, PlanHall, PlanOut, PlanSummary, SessionRef, SwapIn, VerifyOut,
)
from app.schemas.settings import RulesIn
from app.services import audit, plans as plan_service
from app.services.hallmap import hall_map
from app.services.swap import apply_swap, swap_options

router = APIRouter(tags=["plans"])


def _session_ref(s: ExamSession) -> SessionRef:
    return SessionRef(id=s.id, code=s.code, label=s.label, date=s.date, start_time=s.start_time.strftime("%H:%M"),
                      end_time=s.end_time.strftime("%H:%M"))


def summary(db, plan: Plan) -> dict:
    card, base = plan.scorecard or {}, plan.baseline or {}
    creator = db.get(User, plan.created_by) if plan.created_by else None
    avoided = base.get("same_paper_pairs")
    return dict(
        id=plan.id, session=_session_ref(plan.session), version=plan.version, status=plan.status, seed=plan.seed,
        solve_ms=plan.solve_ms, swaps=plan.swaps, created_at=plan.created_at,
        created_by=creator.full_name if creator else None, published_at=plan.published_at,
        candidates=card.get("candidates", 0), halls_used=card.get("halls_used", 0),
        utilisation=card.get("utilisation", 0.0), same_paper_pairs=card.get("same_paper_pairs", 0),
        roll_gap_violations=card.get("roll_gap_violations", 0), accessible_violations=card.get("accessible_violations", 0),
        same_department_pairs=card.get("same_department_pairs", 0), hard_ok=card.get("hard_ok", False),
        conflicts_avoided=None if avoided is None else max(0, avoided - card.get("same_paper_pairs", 0)),
    )


def plan_out(db, plan: Plan) -> PlanOut:
    halls = {h.code: h for h in db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids)))}
    staff: dict[int, list[PersonRef]] = {}
    for a in db.scalars(select(InvigilatorAssignment).where(InvigilatorAssignment.plan_id == plan.id)):
        staff.setdefault(a.hall_id, []).append(PersonRef(id=a.user.id, full_name=a.user.full_name))
    rows = []
    for item in plan.scorecard.get("per_hall", []):
        hall = halls.get(item["hall"])
        if hall is None:
            continue
        rows.append(PlanHall(hall_id=hall.id, code=hall.code, name=hall.name, building=hall.building,
                             capacity=item["seats"], placed=item["placed"], utilisation=item["utilisation"],
                             papers=item["papers"], same_department_pairs=item["same_department_pairs"],
                             invigilators=staff.get(hall.id, [])))
    stats = {k: v for k, v in (plan.stats or {}).items() if k != "attempts"}
    stats["attempts"] = len((plan.stats or {}).get("attempts", []))
    stats["stage_a_ms"] = sum(a.get("stage_a_ms", 0) for a in (plan.stats or {}).get("attempts", []))
    stats["stage_b_ms"] = sum(a.get("stage_b_ms", 0) for a in (plan.stats or {}).get("attempts", []))
    return PlanOut(**summary(db, plan), rules=RulesIn(**plan.rules), hall_ids=plan.hall_ids,
                   engine_version=plan.engine_version, data_fingerprint=plan.data_fingerprint,
                   solver_hash=plan.solver_hash, assignment_hash=plan.assignment_hash, scorecard=plan.scorecard,
                   baseline=plan.baseline, stats=stats, halls=rows)


@router.post("/sessions/{session_id}/plans", response_model=PlanOut, status_code=201,
             summary="Generate a seating plan for a sitting (OR-Tools CP-SAT)")
def generate_plan(session_id: int, body: PlanGenerateIn, db: DB, admin: AdminUser) -> PlanOut:
    plan = plan_service.generate(db, session_id, body.rules, body.hall_ids, body.seed, admin)
    return plan_out(db, plan)


@router.get("/sessions/{session_id}/plans", response_model=list[PlanSummary], summary="Plan versions of a sitting")
def session_plans(session_id: int, db: DB, _: CurrentUser) -> list[PlanSummary]:
    if db.get(ExamSession, session_id) is None:
        raise NotFound("Sitting")
    items = db.scalars(select(Plan).where(Plan.session_id == session_id).order_by(Plan.version.desc())).all()
    return [PlanSummary(**summary(db, p)) for p in items]


@router.get("/plans", response_model=list[PlanSummary], summary="All plans (newest first)")
def all_plans(db: DB, _: CurrentUser, status: str | None = None) -> list[PlanSummary]:
    stmt = select(Plan).order_by(Plan.created_at.desc())
    if status:
        stmt = stmt.where(Plan.status == status)
    return [PlanSummary(**summary(db, p)) for p in db.scalars(stmt)]


@router.get("/plans/{plan_id}", response_model=PlanOut, summary="A plan with its scorecard, halls and audit data")
def get_plan(plan_id: int, db: DB, _: CurrentUser) -> PlanOut:
    return plan_out(db, plan_service.get_plan(db, plan_id))


@router.post("/plans/{plan_id}/publish", response_model=PlanOut, summary="Publish (candidates can look up their seats)")
def publish_plan(plan_id: int, db: DB, admin: AdminUser) -> PlanOut:
    return plan_out(db, plan_service.publish(db, plan_service.get_plan(db, plan_id), admin))


@router.post("/plans/{plan_id}/verify", response_model=VerifyOut, summary="Re-run the solver with the stored seed and compare")
def verify_plan(plan_id: int, db: DB, admin: AdminUser) -> VerifyOut:
    return VerifyOut(**plan_service.verify(db, plan_service.get_plan(db, plan_id), admin))


@router.delete("/plans/{plan_id}", status_code=204, summary="Delete a draft or replaced plan")
def delete_plan(plan_id: int, db: DB, admin: AdminUser) -> None:
    plan_service.delete_plan(db, plan_service.get_plan(db, plan_id), admin)


@router.put("/plans/{plan_id}/invigilators", response_model=PlanOut, summary="Set the invigilators of each hall")
def set_invigilators(plan_id: int, body: InvigilatorsIn, db: DB, admin: AdminUser) -> PlanOut:
    plan = plan_service.get_plan(db, plan_id)
    if plan.status == PLAN_ARCHIVED:
        raise AppError("This version has been replaced; change the invigilators on the current version.", 409)
    staff = {u.id: u for u in db.scalars(select(User).where(User.role == ROLE_INVIGILATOR, User.status == STATUS_ACTIVE))}
    used = {h["hall"] for h in plan.scorecard.get("per_hall", [])}
    halls = {h.id: h for h in db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids)))}
    seen: dict[int, str] = {}
    for item in body.assignments:
        hall = halls.get(item.hall_id)
        if hall is None or hall.code not in used:
            raise AppError("Invigilators can only be assigned to halls this plan uses.", 400)
        for uid in item.user_ids:
            if uid not in staff:
                raise AppError("Only active invigilators can be assigned.", 400)
            if uid in seen and seen[uid] != hall.code:
                raise AppError(f"{staff[uid].full_name} cannot supervise {seen[uid]} and {hall.code} at the same time.", 400)
            seen[uid] = hall.code
    for item in body.assignments:
        db.execute(delete(InvigilatorAssignment).where(InvigilatorAssignment.plan_id == plan.id,
                                                       InvigilatorAssignment.hall_id == item.hall_id))
        for uid in dict.fromkeys(item.user_ids):
            db.add(InvigilatorAssignment(plan_id=plan.id, hall_id=item.hall_id, user_id=uid))
    changes = "; ".join(f"{halls[i.hall_id].code}: {', '.join(staff[u].full_name for u in i.user_ids) or 'nobody'}"
                        for i in body.assignments)
    audit.record(db, "plan.invigilators", f"{admin.full_name} set invigilators for v{plan.version} of "
                 f"{plan.session.label} ({changes})", actor=admin, plan_id=plan.id)
    db.commit()
    return plan_out(db, plan)


@router.get("/plans/{plan_id}/halls/{hall_id}", summary="Seat map of one hall in a plan")
def get_hall_map(plan_id: int, hall_id: int, db: DB, user: CurrentUser) -> dict:
    return hall_map(db, plan_id, hall_id, user)


@router.get("/plans/{plan_id}/halls/{hall_id}/swap-check",
            summary="For the candidate on a seat, which seats could they move to, and why not")
def swap_check(plan_id: int, hall_id: int, seat: str, db: DB, _: AdminUser) -> dict:
    return swap_options(db, plan_id, hall_id, seat)


@router.post("/plans/{plan_id}/swap", summary="Move or swap candidates (blocked if it breaks a rule)")
def swap(plan_id: int, body: SwapIn, db: DB, admin: AdminUser) -> dict:
    return apply_swap(db, plan_id, body.hall_id, body.from_seat, body.to_seat, admin)
