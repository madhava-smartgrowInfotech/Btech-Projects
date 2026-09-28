import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import EXPERIMENTS
from ..db import Alert, LeakEvent, QualityCheck, User, get_db
from ..services import anomaly, demand, ops, twin

router = APIRouter(prefix="/api", tags=["operations"])


@router.get("/forecast/zones")
def forecast_zones(user: User = Depends(current_user)):
    return demand.zones()


@router.get("/forecast")
def forecast(zone: str = "Z3", user: User = Depends(current_user)):
    if zone not in twin.ZONES:
        raise HTTPException(400, "Unknown zone")
    return demand.forecast(zone)


@router.get("/anomalies")
def anomalies(user: User = Depends(current_user)):
    return {"summary": anomaly.summary(), "meters": anomaly.flagged_meters()}


@router.get("/anomalies/meter/{meter_id}")
def meter(meter_id: str, user: User = Depends(current_user)):
    s = anomaly.meter_series(meter_id)
    if not s:
        raise HTTPException(404, "Unknown meter")
    return s


@router.get("/alerts")
def alerts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    ops.sync_alerts(db)
    return [ops.alert_dict(a) for a in ops.open_alerts(db)]


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    ops.sync_alerts(db)
    _, _, s = ops.twin_state(db)
    checks = db.scalars(select(QualityCheck).order_by(QualityCheck.id.desc()).limit(20)).all()
    fc, source = demand.next_week_by_zone()
    hist = demand.load_history()
    last7 = hist[hist["date"] > hist["date"].max() - __import__("pandas").Timedelta(days=7)]
    week = fc.groupby("date")["forecast_m3"].sum().round(1)
    return {
        "kpis": {
            "nrw_pct": s["nrw_pct"],
            "avg_pressure": s["avg_pressure"],
            "min_pressure": s["min_pressure"],
            "equity_score": s["equity_score"],
            "system_input_m3": s["system_input_m3"],
            "billed_m3": s["billed_m3"],
            "quality_potable_pct": round(100 * sum(c.potable for c in checks) / len(checks), 1) if checks else None,
            "quality_checks": db.scalar(select(func.count(QualityCheck.id))),
            "active_leaks": db.scalar(select(func.count(LeakEvent.id)).where(LeakEvent.active.is_(True))),
            "open_alerts": db.scalar(select(func.count(Alert.id)).where(Alert.open.is_(True))),
            "flagged_meters": len(anomaly.flagged_meters()),
            "forecast_week_m3": round(float(fc["forecast_m3"].sum()), 1),
            "last_week_m3": round(float(last7["consumption_m3"].sum()), 1),
        },
        "hourly_pressure": s["hourly_pressure"],
        "hourly_supply_lps": s["hourly_supply_lps"],
        "tank_level": s["tank_level"],
        "zones": list(s["zones"].values()),
        "forecast_week": [{"date": d, "forecast_m3": v} for d, v in week.items()],
        "weather_source": source,
        "alerts": [ops.alert_dict(a) for a in ops.open_alerts(db, 8)],
    }


@router.get("/metrics")
def metrics(user: User = Depends(current_user)):
    out = {}
    for name in ("quality", "demand", "leak", "anomaly"):
        p = EXPERIMENTS / f"{name}_metrics.json"
        if p.exists():
            out[name] = json.loads(p.read_text())
    p = EXPERIMENTS / "eval" / "metrics.json"
    if p.exists():
        out["eval"] = json.loads(p.read_text())
    return out
