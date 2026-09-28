"""Forecasts, warnings and plans built from the engine plus the live database state."""
import math

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import EQUIPMENT, FACILITIES, NURSE_RATIO, OPERATING_DAY, SHIFTS, WARDS, day_to_date
from ..db import Admission, EquipmentInventory, NurseRoster, WardCapacity
from .engine import WARN_Z, Z90, get_engine


def load_state(db: Session):
    capacity = {f: {} for f in FACILITIES}
    for r in db.scalars(select(WardCapacity)):
        capacity[r.facility][r.ward] = r.beds
    roster = {f: {w: {} for w in WARDS} for f in FACILITIES}
    for r in db.scalars(select(NurseRoster)):
        roster[r.facility][r.ward][r.shift] = r.nurses
    inventory = {f: {} for f in FACILITIES}
    for r in db.scalars(select(EquipmentInventory)):
        inventory[r.facility][r.item] = r.units
    return capacity, roster, inventory


def app_admissions(db: Session) -> pd.DataFrame:
    rows = [{"facid": a.facility, "ward": a.ward, "pred_los": a.predicted_days, "elapsed": 0}
            for a in db.scalars(select(Admission))]
    return pd.DataFrame(rows, columns=["facid", "ward", "pred_los", "elapsed"])


def forecast(db: Session, horizon: int = 14):
    """Census forecast per facility x ward with bands, capacity and warnings."""
    eng = get_engine()
    capacity, _, _ = load_state(db)
    fc = eng.forecast_census(OPERATING_DAY, horizon, app_admissions(db))
    dates = [day_to_date(OPERATING_DAY + k).isoformat() for k in range(1, horizon + 1)]
    out = {}
    for (f, w), x in fc.items():
        sd = np.sqrt(x["var"])
        mean, lower, upper = x["mean"], np.clip(x["mean"] - Z90 * sd, 0, None), x["mean"] + Z90 * sd
        cap = capacity[f][w]
        over_mean = np.where(mean > cap)[0]
        warn_curve = mean + WARN_Z * sd
        over_upper = np.where(warn_curve > cap)[0]
        level, first = None, None
        if len(over_mean):
            level, first = "critical", int(over_mean[0])
        elif len(over_upper):
            level, first = "warning", int(over_upper[0])
        out[(f, w)] = {
            "facility": f, "ward": w, "capacity": cap, "current": x["current"],
            "series": [{"date": dates[k], "day": k + 1, "mean": round(float(mean[k]), 1),
                        "lower": round(float(lower[k]), 1), "upper": round(float(upper[k]), 1), "sd": round(float(sd[k]), 3),
                        "arrivals": round(float(x["arrivals"][k]), 1)} for k in range(horizon)],
            "peak": round(float(mean.max()), 1), "peak_day": int(mean.argmax()) + 1,
            "peak_upper": round(float(upper.max()), 1),
            "alert": None if level is None else {
                "level": level, "day": first + 1, "date": dates[first],
                "expected": round(float(mean[first]), 1), "upper": round(float(upper[first]), 1),
                "risk_level": round(float(warn_curve[first]), 1)},
        }
    return out


def alert_message(x):
    a = x["alert"]
    if a["level"] == "critical":
        return (f"Facility {x['facility']} {x['ward']}: expected {a['expected']:.0f} patients on day {a['day']} "
                f"({a['date']}) - above {x['capacity']} beds.")
    return (f"Facility {x['facility']} {x['ward']}: about a 1-in-6 chance of passing {x['capacity']} beds on day "
            f"{a['day']} ({a['date']}) - expected {a['expected']:.0f}, up to {a['upper']:.0f} (90% band).")


def alerts(fc: dict, wards=None):
    items = []
    for x in fc.values():
        if x["alert"] and (wards is None or x["ward"] in wards):
            items.append({"facility": x["facility"], "ward": x["ward"], **x["alert"], "message": alert_message(x)})
    items.sort(key=lambda a: (a["level"] != "critical", a["ward"] != "ICU", a["day"]))
    return items


def resources(db: Session, facility: str, horizon: int = 7):
    """Nurses per shift and equipment needed each day vs what is rostered / in stock."""
    eng = get_engine()
    _, roster, inventory = load_state(db)
    fc = forecast(db, horizon)
    days = []
    for k in range(horizon):
        load = {w: fc[(facility, w)]["series"][k]["mean"] for w in WARDS}
        nurses = []
        for w in WARDS:
            need = eng.nurses_needed(w, load[w])
            nurses.append({"ward": w, "patients": round(load[w], 1),
                           "shifts": [{"shift": s, "needed": need[s], "rostered": roster[facility][w][s],
                                       "gap": max(0, need[s] - roster[facility][w][s])} for s in SHIFTS]})
        eq_need = eng.equipment_needed(load)
        equipment = [{"item": e, "needed": eq_need[e], "available": inventory[facility][e],
                      "gap": max(0, eq_need[e] - inventory[facility][e])} for e in EQUIPMENT]
        days.append({"date": fc[(facility, WARDS[0])]["series"][k]["date"], "day": k + 1,
                     "nurses": nurses, "equipment": equipment,
                     "nurse_gap": sum(s["gap"] for n in nurses for s in n["shifts"]),
                     "equipment_gap": sum(e["gap"] for e in equipment)})
    return {"facility": facility, "ratios": NURSE_RATIO, "equipment_rates": eng.config["equipment_rates"],
            "days": days}


def planning_demand(fc: dict, horizon: int, level: str):
    """Peak load per facility x ward over the horizon (expected or 90% upper band)."""
    key = "upper" if level == "p90" else "mean"
    demand, peak_label = {f: {} for f in FACILITIES}, {f: {} for f in FACILITIES}
    for (f, w), x in fc.items():
        s = x["series"][:horizon]
        best = max(s, key=lambda r: r[key])
        demand[f][w] = int(math.ceil(best[key] - 1e-9))
        peak_label[f][w] = f"day {best['day']}, {best['date']}"
    return demand, peak_label
