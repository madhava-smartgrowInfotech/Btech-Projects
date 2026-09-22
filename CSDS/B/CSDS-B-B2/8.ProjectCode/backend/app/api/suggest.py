from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.security import get_current_user
from ..models import User
from ..services.suggest_service import strong_spot_pack, suggest_for, surface_for

router = APIRouter(tags=["better signal"])


@router.get("/api/suggest", summary="Nearest spot predicted to have strong signal (Gaussian Process)")
def suggest(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180), operator: str | None = None,
            user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return suggest_for(db, lat, lon, operator)


@router.get("/api/suggest/area", summary="Predicted strong spots around a point, for offline use on the phone")
def suggest_area(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180), operator: str | None = None,
                 radius_m: float = Query(2500, ge=300, le=5000), user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)) -> dict:
    return strong_spot_pack(db, lat, lon, operator, radius_m)


@router.get("/api/coverage/predicted", summary="Predicted coverage grid around a point (map layer)")
def predicted(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180), operator: str | None = None,
              radius_m: float = Query(1200, ge=200, le=3000), user: User = Depends(get_current_user),
              db: Session = Depends(get_db)) -> dict:
    return surface_for(db, lat, lon, operator, radius_m)
