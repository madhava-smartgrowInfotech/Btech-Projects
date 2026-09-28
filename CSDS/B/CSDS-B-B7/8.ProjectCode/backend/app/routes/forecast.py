from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import FACILITIES, WARDS
from ..db import User, get_db
from ..services import planning

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


@router.get("")
def occupancy(facility: str = "A", days: int = Query(14, ge=1, le=14), user: User = Depends(current_user),
              db: Session = Depends(get_db)):
    if facility not in FACILITIES:
        raise HTTPException(400, "Unknown facility")
    fc = planning.forecast(db, days)
    wards = [fc[(facility, w)] for w in WARDS]
    return {"facility": facility, "days": days, "wards": wards,
            "alerts": [a for a in planning.alerts(fc) if a["facility"] == facility]}


@router.get("/icu")
def icu(days: int = Query(14, ge=1, le=14), user: User = Depends(current_user), db: Session = Depends(get_db)):
    fc = planning.forecast(db, days)
    return {"days": days, "facilities": [fc[(f, "ICU")] for f in FACILITIES],
            "alerts": planning.alerts(fc, wards=["ICU"])}


@router.get("/resources")
def resources(facility: str = "A", days: int = Query(7, ge=1, le=14), user: User = Depends(current_user),
              db: Session = Depends(get_db)):
    if facility not in FACILITIES:
        raise HTTPException(400, "Unknown facility")
    return planning.resources(db, facility, days)
