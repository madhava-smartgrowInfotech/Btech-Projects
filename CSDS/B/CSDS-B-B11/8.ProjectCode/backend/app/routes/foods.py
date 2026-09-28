from fastapi import APIRouter, Depends, HTTPException

from ..db import Profile
from ..deps import profile_dict, require_profile
from ..services import usda
from ..services.foods import food_db

router = APIRouter(prefix="/api/foods", tags=["foods"])


@router.get("/search")
def search(q: str, limit: int = 15, p: Profile = Depends(require_profile)):
    return {"results": food_db().search(q, limit=min(limit, 50), prefs=profile_dict(p))}


@router.get("/usda")
def usda_search(q: str, p: Profile = Depends(require_profile)):
    if len(q.strip()) < 2:
        raise HTTPException(400, "Type at least 2 letters.")
    try:
        return {"results": usda.search(q.strip())}
    except usda.USDAError as e:
        raise HTTPException(503, str(e))


@router.get("/{food_id}")
def get_food(food_id: int, p: Profile = Depends(require_profile)):
    f = food_db().get(food_id)
    if f is None:
        raise HTTPException(404, "Dish not found.")
    return food_db().public(f, profile_dict(p))
