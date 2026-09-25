from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..db import get_db
from ..services import osrm, risk

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.post("/plan")
async def plan_route(
    body: schemas.RoutePlanIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        alternatives = await osrm.get_route_alternatives(
            body.origin_lat, body.origin_lng, body.dest_lat, body.dest_lng
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Routing service unavailable: {e}")

    if not alternatives:
        raise HTTPException(status_code=404, detail="No route found between these points")

    districts = db.query(models.DistrictRisk).all()

    scored = []
    for i, route in enumerate(alternatives):
        s = risk.score_route(route, districts)
        scored.append({
            "index": i,
            "distance_m": route["distance_m"],
            "duration_s": route["duration_s"],
            "coordinates": route["coordinates"],
            "risk_score": s["score"],
            "risk_tiers": s["tiers"],
            "is_night": s["night"],
        })

    scored.sort(key=lambda r: r["risk_score"])
    for i, r in enumerate(scored):
        r["recommended"] = i == 0

    return {"routes": scored, "safest_index": 0}
