from datetime import date as Date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import FoodLog, Profile, TargetHistory, WeightLog, get_db
from ..deps import require_profile, targets_for
from ..services.progress import adherence, recalculation, weight_trend

router = APIRouter(prefix="/api", tags=["progress"])


class WeightIn(BaseModel):
    date: Date | None = None
    weight_kg: float = Field(ge=30, le=250)


def run_recalc(p: Profile, db: Session, points):
    r = recalculation(points, p.goal, p.adaptive_adjust or 0.0)
    if r is None:
        return None
    old_kcal = targets_for(p)["kcal"]
    p.adaptive_adjust = r["adaptive_adjust"]
    p.weight_kg = r["latest_weight"]
    p.last_recalc_at = datetime.utcnow()
    t = targets_for(p)
    db.add(TargetHistory(user_id=p.user_id, as_of=r["as_of"], kcal=t["kcal"], weight_kg=p.weight_kg, reason=r["reason"]))
    db.commit()
    return {**r, "as_of": r["as_of"].isoformat(), "old_target_kcal": old_kcal, "new_target_kcal": t["kcal"]}


@router.post("/weights")
def add_weight(body: WeightIn, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    d = body.date or Date.today()
    if d > Date.today():
        raise HTTPException(400, "Weight date cannot be in the future.")
    row = db.scalar(select(WeightLog).where(WeightLog.user_id == p.user_id, WeightLog.date == d))
    if row:
        row.weight_kg = body.weight_kg
        row.created_at = datetime.utcnow()
    else:
        db.add(WeightLog(user_id=p.user_id, date=d, weight_kg=body.weight_kg))
    db.commit()
    # automatic weekly recalculation once the weights entered since the last one cover a week
    fresh = db.scalars(select(WeightLog).where(WeightLog.user_id == p.user_id, WeightLog.created_at > p.last_recalc_at)).all()
    recalc = None
    if len(fresh) >= 4 and (max(w.date for w in fresh) - min(w.date for w in fresh)).days >= 6:
        recalc = run_recalc(p, db, [(w.date, w.weight_kg) for w in fresh])
    return {"ok": True, "recalculated": recalc, "target_kcal": targets_for(p)["kcal"]}


@router.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    row = db.get(WeightLog, weight_id)
    if row is None or row.user_id != p.user_id:
        raise HTTPException(404, "Entry not found.")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/progress/recalculate")
def recalc_now(p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    rows = db.scalars(select(WeightLog).where(WeightLog.user_id == p.user_id).order_by(WeightLog.date)).all()
    if not rows:
        raise HTTPException(400, "Log your weight first.")
    last = rows[-1].date
    pts = [(w.date, w.weight_kg) for w in rows if (last - w.date).days <= 13]
    r = run_recalc(p, db, pts)
    if r is None:
        raise HTTPException(400, "Need at least 3 weight entries spanning 7 days (within the last 2 weeks) to recalculate.")
    return r


@router.get("/progress")
def progress(days: int = 30, p: Profile = Depends(require_profile), db: Session = Depends(get_db)):
    days = max(7, min(days, 180))
    today = Date.today()
    start = today - timedelta(days=days - 1)
    weights = db.scalars(select(WeightLog).where(WeightLog.user_id == p.user_id).order_by(WeightLog.date)).all()
    logs = db.scalars(select(FoodLog).where(FoodLog.user_id == p.user_id, FoodLog.date >= start)).all()
    history = db.scalars(select(TargetHistory).where(TargetHistory.user_id == p.user_id).order_by(TargetHistory.id)).all()
    t = targets_for(p)

    def target_for(d):
        k = None
        for h in history:
            if h.as_of <= d:
                k = h.kcal
        return k if k is not None else (history[0].kcal if history else t["kcal"])

    daily = {}
    for row in logs:
        e = daily.setdefault(row.date, {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0})
        for n in e:
            e[n] += getattr(row, n)
    empty = {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0}
    intake = []
    for i in range(days):
        d = start + timedelta(days=i)
        intake.append({"date": d.isoformat(), **{n: round(v, 1) for n, v in daily.get(d, empty).items()}, "target": target_for(d)})
    recent = [(w.date, w.weight_kg) for w in weights if (today - w.date).days <= 13]
    trend = weight_trend(recent)
    return {
        "weights": [{"id": w.id, "date": w.date.isoformat(), "weight_kg": w.weight_kg} for w in weights],
        "intake": intake,
        "adherence": adherence(daily, target_for, t["protein_g"], today),
        "target_history": [{"date": h.as_of.isoformat(), "kcal": h.kcal, "weight_kg": h.weight_kg, "reason": h.reason} for h in history],
        "current_target": t["kcal"],
        "trend_kg_week": round(trend, 2) if trend is not None else None,
        "goal_rate_kg_week": t["goal_rate_kg_week"],
    }
