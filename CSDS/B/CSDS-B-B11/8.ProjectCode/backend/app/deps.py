from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import current_user
from .db import Profile, User, get_db
from .services.targets import compute_targets


def profile_dict(p: Profile) -> dict:
    return {"age": p.age, "gender": p.gender, "height_cm": p.height_cm, "weight_kg": p.weight_kg,
            "activity": p.activity, "diet_type": p.diet_type, "cuisine": p.cuisine,
            "allergies": list(p.allergies or []), "conditions": list(p.conditions or []), "goal": p.goal,
            "adaptive_adjust": p.adaptive_adjust or 0.0}


def require_profile(user: User = Depends(current_user), db: Session = Depends(get_db)) -> Profile:
    p = db.get(Profile, user.id)
    if p is None:
        raise HTTPException(400, "Please complete your profile first.")
    return p


def targets_for(p: Profile) -> dict:
    return compute_targets(profile_dict(p))
