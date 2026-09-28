import copy
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Plan, Profile, get_db
from ..deps import profile_dict, require_profile, targets_for
from ..services.planner import SLOTS, PlanError, apply_swap, generate_week, swap_options

router = APIRouter(prefix="/api/plans", tags=["plans"])


def plan_out(plan: Plan):
    return {"id": plan.id, "created_at": plan.created_at.isoformat(), "start_date": plan.start_date.isoformat(),
            "target_kcal": plan.target_kcal, **plan.data}


def load_plan(plan_id: int, p: Profile, db: Session) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None or plan.user_id != p.user_id:
        raise HTTPException(404, "Plan not found.")
    return plan


def locate(plan: Plan, day: int, meal: str, index: int):
    if meal not in SLOTS or not (1 <= day <= len(plan.data["days"])):
        raise HTTPException(400, "Invalid day or meal.")
    items = plan.data["days"][day - 1]["meals"][meal]
    if not (0 <= index < len(items)):
        raise HTTPException(400, "Invalid dish position.")
    return day - 1


class GenerateIn(BaseModel):
    seed: int | None = None


@router.post("")
def generate(body: GenerateIn | None = None, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    t = targets_for(p)
    try:
        week = generate_week(profile_dict(p), t, seed=body.seed if body else None)
    except PlanError as e:
        raise HTTPException(422, str(e))
    plan = Plan(user_id=p.user_id, start_date=date.fromisoformat(week["start_date"]), target_kcal=t["kcal"], data=week)
    db.add(plan)
    db.commit()
    return plan_out(plan)


@router.get("/latest")
def latest(p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    plan = db.scalar(select(Plan).where(Plan.user_id == p.user_id).order_by(Plan.id.desc()))
    return {"plan": plan_out(plan) if plan else None}


@router.get("/{plan_id}")
def get_plan(plan_id: int, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    return plan_out(load_plan(plan_id, p, db))


@router.get("/{plan_id}/swap-options")
def options(plan_id: int, day: int, meal: str, index: int, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    plan = load_plan(plan_id, p, db)
    d = locate(plan, day, meal, index)
    return swap_options(plan.data, d, meal, index, profile_dict(p), targets_for(p))


class SwapIn(BaseModel):
    day: int
    meal: str
    index: int
    food_id: int
    grams: float


@router.post("/{plan_id}/swap")
def swap(plan_id: int, body: SwapIn, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    plan = load_plan(plan_id, p, db)
    d = locate(plan, body.day, body.meal, body.index)
    data = copy.deepcopy(plan.data)
    try:
        apply_swap(data, d, body.meal, body.index, body.food_id, body.grams, profile_dict(p), targets_for(p))
    except PlanError as e:
        raise HTTPException(422, str(e))
    plan.data = data  # reassign so SQLAlchemy stores the JSON change
    db.commit()
    return plan_out(plan)
