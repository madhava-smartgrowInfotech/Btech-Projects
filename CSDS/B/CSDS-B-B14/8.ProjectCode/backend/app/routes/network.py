from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..auth import current_user, require_role
from ..db import Alert, LeakEvent, User, add_alert, get_db
from ..services import imbalance, leaks, ops, twin

router = APIRouter(prefix="/api", tags=["network"])


def event_dict(e):
    return {"id": e.id, "created_at": e.created_at.isoformat(), "pipe": e.pipe, "zone": e.zone,
            "leak_lps": e.leak_lps, "active": e.active, "detected": e.detected, "probability": e.probability,
            "top_pipe": e.top_pipe, "true_rank": e.true_rank, "ranking": e.result.get("ranking", [])}


@router.get("/network")
def network(db: Session = Depends(get_db), user: User = Depends(current_user)):
    wn, res, s = ops.twin_state(db)
    geo = twin.network_geo(res, wn)
    last = db.scalar(select(LeakEvent).where(LeakEvent.active.is_(True)).order_by(LeakEvent.id.desc()))
    geo["active_leaks"] = [event_dict(e) for e in db.scalars(select(LeakEvent).where(LeakEvent.active.is_(True))).all()]
    geo["suspects"] = last.result.get("ranking", []) if last else []
    geo["summary"] = {k: s[k] for k in ("nrw_pct", "avg_pressure", "min_pressure", "equity_score", "system_input_m3")}
    geo["zone_stats"] = s["zones"]
    geo["snapshot"] = "08:00 (morning peak)"
    return geo


@router.get("/imbalance")
def get_imbalance(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return imbalance.analyse(ops.active_leaks(db))


class WhatIfIn(BaseModel):
    pump_speed: float = Field(1.0, ge=0.7, le=1.3)
    throttle: dict[str, float] | None = None


@router.post("/imbalance/whatif")
def whatif(body: WhatIfIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    for p in (body.throttle or {}):
        if p not in twin.pipe_zone():
            raise HTTPException(400, f"Unknown pipe {p}")
    return imbalance.whatif(ops.active_leaks(db), body.pump_speed, body.throttle)


@router.get("/leaks/pipes")
def pipes(user: User = Depends(current_user)):
    pz = twin.pipe_zone()
    return [{"pipe": p, "zone": pz[p]} for p in twin.candidate_pipes()]


class InjectIn(BaseModel):
    pipe: str
    leak_lps: float = Field(10.0, ge=1.0, le=40.0)


@router.post("/leaks/inject")
def inject(body: InjectIn, db: Session = Depends(get_db), user: User = Depends(require_role("engineer"))):
    if body.pipe not in twin.candidate_pipes():
        raise HTTPException(400, f"{body.pipe} is not a distribution pipe of the twin")
    if db.scalar(select(LeakEvent).where(LeakEvent.active.is_(True), LeakEvent.pipe == body.pipe)):
        raise HTTPException(400, f"A leak is already active on {body.pipe}")
    r = leaks.inject(body.pipe, body.leak_lps)
    top = r["ranking"][0]
    zone = twin.pipe_zone()[body.pipe]
    e = LeakEvent(pipe=body.pipe, zone=zone, leak_lps=body.leak_lps, detected=r["detected"],
                  probability=r["leak_probability"], top_pipe=top["pipe"], true_rank=r["true_rank"], result=r)
    db.add(e)
    db.commit()
    if r["detected"]:
        add_alert(db, "leak", "high", f"Leak detected in {twin.ZONE_NAMES[top['zone']]} - most likely pipe {top['pipe']}",
                  f"Probability {round(r['leak_probability'] * 100)}%, estimated {top['estimated_lps']} L/s. "
                  f"Next candidates: {', '.join(x['pipe'] for x in r['ranking'][1:4])}.",
                  zone=top["zone"], ref=f"leak:{e.id}")
    return {"event": event_dict(e), **r}


@router.get("/leaks/events")
def events(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(LeakEvent).order_by(LeakEvent.id.desc()).limit(30)).all()
    return [event_dict(e) for e in rows]


@router.post("/leaks/clear")
def clear(db: Session = Depends(get_db), user: User = Depends(require_role("engineer"))):
    """Repair all injected leaks in the twin (returns the twin to its baseline state)."""
    n = db.execute(update(LeakEvent).where(LeakEvent.active.is_(True)).values(active=False)).rowcount
    db.execute(update(Alert).where(Alert.kind == "leak", Alert.open.is_(True)).values(open=False))
    db.commit()
    return {"repaired": n}
