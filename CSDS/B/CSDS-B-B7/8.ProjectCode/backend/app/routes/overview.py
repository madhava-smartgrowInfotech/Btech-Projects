"""Meta, dashboard and model-performance endpoints."""
import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import (EQUIPMENT, EXPERIMENTS_DIR, FACILITIES, LONG_STAY_DAYS, NURSE_RATIO, OPERATING_DAY, SHIFTS,
                      WARDS, day_to_date)
from ..db import Admission, AllocationPlan, User, get_db
from ..services import planning
from ..services.engine import LABELS, get_engine

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/meta")
def meta(user: User = Depends(current_user)):
    return {"operating_date": day_to_date(OPERATING_DAY).isoformat(), "facilities": FACILITIES, "wards": WARDS,
            "shifts": SHIFTS, "equipment": EQUIPMENT, "nurse_ratio": NURSE_RATIO,
            "long_stay_threshold_days": LONG_STAY_DAYS, "feature_labels": LABELS}


@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    fc = planning.forecast(db, 14)
    capacity, _, _ = planning.load_state(db)
    eng = get_engine()
    app_adm = list(db.scalars(select(Admission)))
    facilities = []
    for f in FACILITIES:
        beds = sum(capacity[f].values())
        now = sum(fc[(f, w)]["current"] for w in WARDS)
        peak7 = max(sum(fc[(f, w)]["series"][k]["mean"] for w in WARDS) for k in range(7))
        facilities.append({"facility": f, "beds": beds, "occupied": now, "occupancy": round(now / beds, 3),
                           "peak_7d": round(peak7, 1), "peak_occupancy_7d": round(peak7 / beds, 3),
                           "icu_beds": capacity[f]["ICU"], "icu_occupied": fc[(f, "ICU")]["current"],
                           "icu_peak_7d": max(r["mean"] for r in fc[(f, "ICU")]["series"][:7])})
    beds = sum(x["beds"] for x in facilities)
    occ = sum(x["occupied"] for x in facilities)
    icu_beds = sum(x["icu_beds"] for x in facilities)
    icu_occ = sum(x["icu_occupied"] for x in facilities)
    daily = [{"date": fc[("A", "General")]["series"][k]["date"],
              "mean": round(sum(fc[(f, w)]["series"][k]["mean"] for f in FACILITIES for w in WARDS), 1),
              "upper": round(sum(fc[(f, w)]["series"][k]["upper"] for f in FACILITIES for w in WARDS), 1),
              "icu": round(sum(fc[(f, "ICU")]["series"][k]["mean"] for f in FACILITIES), 1)} for k in range(14)]
    in_house = eng.in_house(OPERATING_DAY)
    pred = list(in_house.pred_los) + [a.predicted_days for a in app_adm]
    latest = db.scalar(select(AllocationPlan).order_by(AllocationPlan.id.desc()).limit(1))
    return {
        "operating_date": day_to_date(OPERATING_DAY).isoformat(),
        "kpis": {"beds": beds, "occupied": occ, "occupancy": round(occ / beds, 3), "icu_beds": icu_beds,
                 "icu_occupied": icu_occ, "icu_occupancy": round(icu_occ / icu_beds, 3),
                 "admissions_next_24h": round(sum(fc[(f, w)]["series"][0]["arrivals"]
                                                  for f in FACILITIES for w in WARDS)),
                 "avg_predicted_los": round(sum(pred) / len(pred), 2),
                 "long_stay_share": round(sum(p > LONG_STAY_DAYS for p in pred) / len(pred), 3),
                 "peak_occupancy_7d": round(max(d["mean"] for d in daily[:7]) / beds, 3),
                 "admitted_today_in_app": len(app_adm)},
        "facilities": facilities, "daily": daily, "alerts": planning.alerts(fc)[:12],
        "icu_alerts": len(planning.alerts(fc, wards=["ICU"])),
        "latest_plan": None if not latest else {"id": latest.id, "status": latest.status,
                                                "created_at": latest.created_at.isoformat(),
                                                "actions": len(latest.actions), "summary": latest.summary["text"]},
    }


def _read(path):
    return json.loads(path.read_text()) if path.exists() else None


@router.get("/metrics")
def metrics(user: User = Depends(current_user)):
    eng = get_engine()
    imp = [{"feature": f, "label": LABELS[f], "importance": round(v, 4)}
           for f, v in eng.meta["feature_importance"][:12]]
    return {"training": _read(EXPERIMENTS_DIR / "metrics.json"),
            "evaluation": _read(EXPERIMENTS_DIR / "eval" / "metrics.json"), "feature_importance": imp}
