from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, require_admin
from ..config import FACILITIES, SHIFTS, WARDS
from ..db import AllocationPlan, EquipmentInventory, NurseRoster, User, WardCapacity, get_db
from ..services import planning
from ..services.engine import get_engine
from ..services.optimizer import apply_actions, explain, optimize

router = APIRouter(prefix="/api/allocation", tags=["allocation"])


class RunIn(BaseModel):
    horizon_days: int = Field(7, ge=1, le=14)
    planning_level: Literal["expected", "p90"] = "expected"


class ActionEdit(BaseModel):
    id: int
    quantity: int = Field(ge=0)


class AcceptIn(BaseModel):
    actions: list[ActionEdit] = []


def plan_out(p: AllocationPlan):
    return {"id": p.id, "created_at": p.created_at.isoformat(), "created_by": p.created_by,
            "horizon_days": p.horizon_days, "planning_level": p.planning_level, "demand": p.demand,
            "actions": p.actions, "summary": p.summary, "status": p.status, "modified": p.modified,
            "accepted_by": p.accepted_by, "accepted_at": p.accepted_at.isoformat() if p.accepted_at else None}


@router.post("/run")
def run(body: RunIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    capacity, roster, inventory = planning.load_state(db)
    rates = get_engine().config["equipment_rates"]
    fc = planning.forecast(db, body.horizon_days)
    demand, peak_label = planning.planning_demand(fc, body.horizon_days, body.planning_level)
    try:
        result = optimize(demand, capacity, roster, inventory, rates)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    summary = explain(result["actions"], demand, capacity, roster, inventory, rates, peak_label)
    summary.update({"solver_status": result["status"], "solve_seconds": result["solve_seconds"],
                    "capacity_before": capacity})
    plan = AllocationPlan(created_by=user.email, horizon_days=body.horizon_days, planning_level=body.planning_level,
                          demand=demand, actions=result["actions"], summary=summary)
    db.add(plan)
    db.commit()
    return plan_out(plan)


@router.get("/plans")
def plans(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [plan_out(p) for p in db.scalars(select(AllocationPlan).order_by(AllocationPlan.id.desc()).limit(20))]


@router.get("/plans/{plan_id}")
def get_plan(plan_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(AllocationPlan, plan_id)
    if not p:
        raise HTTPException(404, "Plan not found")
    return plan_out(p)


@router.post("/plans/{plan_id}/accept")
def accept(plan_id: int, body: AcceptIn, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Accept a plan (optionally with edited quantities) and apply it to beds, roster and equipment."""
    p = db.get(AllocationPlan, plan_id)
    if not p:
        raise HTTPException(404, "Plan not found")
    if p.status != "proposed":
        raise HTTPException(409, "This plan has already been accepted")
    edits = {e.id: e.quantity for e in body.actions}
    actions, modified = [], False
    for a in p.actions:
        a = dict(a)
        if a["id"] in edits and edits[a["id"]] != a["quantity"]:
            a["original_quantity"], a["quantity"], modified = a["quantity"], edits[a["id"]], True
        actions.append(a)
    capacity, roster, inventory = planning.load_state(db)
    cap, ros, inv, _ = apply_actions(actions, None, capacity, roster, inventory)
    for f in FACILITIES:
        for w in WARDS:
            if cap[f][w] < 0 or any(ros[f][w][s] < 0 for s in SHIFTS):
                raise HTTPException(400, f"Edited plan removes more beds or nurses than Facility {f} {w} has")
        if any(v < 0 for v in inv[f].values()):
            raise HTTPException(400, f"Edited plan moves more equipment than Facility {f} holds")
    for r in db.scalars(select(WardCapacity)):
        r.beds = cap[r.facility][r.ward]
    for r in db.scalars(select(NurseRoster)):
        r.nurses = ros[r.facility][r.ward][r.shift]
    for r in db.scalars(select(EquipmentInventory)):
        r.units = inv[r.facility][r.item]
    p.actions, p.modified, p.status = actions, modified, "accepted"
    p.accepted_by, p.accepted_at = user.email, datetime.utcnow()
    db.commit()
    return plan_out(p)
