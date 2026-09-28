from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Profile, TargetHistory, User, WeightLog, get_db
from ..deps import profile_dict, require_profile, targets_for
from ..services.foods import ALLERGENS
from ..services.targets import ACTIVITY_FACTORS, CONDITIONS

router = APIRouter(prefix="/api", tags=["profile"])


class ProfileIn(BaseModel):
    age: int = Field(ge=18, le=90)
    gender: Literal["male", "female", "other"]
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=30, le=250)
    activity: Literal["sedentary", "light", "moderate", "active", "very_active"]
    diet_type: Literal["vegetarian", "eggetarian", "non_vegetarian", "vegan"]
    cuisine: Literal["north", "south", "both"]
    allergies: list[str] = []
    conditions: list[str] = []
    goal: Literal["lose", "maintain", "gain"]


@router.get("/profile/options")
def options():
    return {"activity": list(ACTIVITY_FACTORS), "allergies": ALLERGENS, "conditions": CONDITIONS,
            "diet_type": ["vegetarian", "eggetarian", "non_vegetarian", "vegan"], "cuisine": ["north", "south", "both"],
            "goal": ["lose", "maintain", "gain"]}


@router.get("/profile")
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Profile, user.id)
    return {"profile": profile_dict(p) if p else None}


@router.put("/profile")
def save_profile(body: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    bad = [a for a in body.allergies if a not in ALLERGENS] + [c for c in body.conditions if c not in CONDITIONS]
    if bad:
        raise HTTPException(400, f"Unknown option(s): {', '.join(bad)}")
    p = db.get(Profile, user.id)
    new = p is None
    if new:
        p = Profile(user_id=user.id, adaptive_adjust=0.0)
        db.add(p)
    elif p.goal != body.goal:
        p.adaptive_adjust = 0.0  # a new goal starts a fresh adaptive correction
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    p.last_recalc_at = datetime.utcnow()
    t = targets_for(p)
    db.add(TargetHistory(user_id=user.id, as_of=date.today(), kcal=t["kcal"], weight_kg=p.weight_kg,
                         reason="Initial target from your profile." if new else "Profile updated."))
    if db.query(WeightLog).filter_by(user_id=user.id, date=date.today()).first() is None:
        # baseline weight belongs to this calculation, so it is stamped just before it
        db.add(WeightLog(user_id=user.id, date=date.today(), weight_kg=p.weight_kg,
                         created_at=p.last_recalc_at - timedelta(seconds=1)))
    db.commit()
    return {"profile": profile_dict(p), "targets": t}


@router.get("/targets")
def get_targets(p: Profile = Depends(require_profile)):
    return targets_for(p)
