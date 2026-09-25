from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/areas")
def list_risk_areas(db: Session = Depends(get_db)):
    rows = db.query(models.DistrictRisk).all()
    return [
        {
            "state": r.state,
            "district": r.district,
            "lat": r.lat,
            "lng": r.lng,
            "crime_rate": r.crime_rate,
            "risk_score": r.risk_score,
            "risk_tier": r.risk_tier,
        }
        for r in rows
    ]
