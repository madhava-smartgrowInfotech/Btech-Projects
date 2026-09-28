"""Rank hospitals by severity, distance, specialty and availability."""
import math
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Hospital
from .scheduling import day_stats, hard_cap

# weights per severity: distance, specialty match, availability, emergency capability
WEIGHTS = {
    "mild": (0.35, 0.30, 0.35, 0.00),
    "moderate": (0.30, 0.40, 0.30, 0.00),
    "severe": (0.30, 0.40, 0.15, 0.15),
    "critical": (0.55, 0.10, 0.05, 0.30),
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def recommend(db: Session, lat: float, lon: float, severity: str, specialty: str, day: date, limit: int = 5):
    wd, ws, wa, we = WEIGHTS.get(severity, WEIGHTS["moderate"])
    out = []
    for h in db.scalars(select(Hospital)).all():
        specs = h.specialty_list()
        if specialty in specs:
            spec_score = 1.0
        elif specialty == "General Medicine" or ("General Medicine" in specs and severity in ("mild", "moderate")):
            spec_score = 0.5
        else:
            spec_score = 0.0
        if severity in ("severe", "moderate") and spec_score == 0:
            continue
        dist = haversine_km(lat, lon, h.lat, h.lon)
        s = day_stats(db, h.id, day.isoformat())
        free = max(h.op_limit - s["booked"], 0)
        overbook_left = max(hard_cap(h) - s["booked"], 0)
        avail = min(free / max(h.op_limit, 1), 1.0)
        emerg = 1.0 if h.has_emergency else 0.0
        if severity == "critical" and not h.has_emergency:
            continue
        score = wd * math.exp(-dist / 8) + ws * spec_score + wa * avail + we * emerg
        why = [f"{dist:.1f} km away"]
        if spec_score == 1.0:
            why.append(f"has {specialty}")
        elif spec_score:
            why.append("General Medicine OP")
        if free:
            why.append(f"{free} of {h.op_limit} slots free")
        elif overbook_left:
            why.append("OP limit reached - no-show-adjusted slots may remain")
        else:
            why.append("full on this day - next free day will be used")
        if h.has_emergency:
            why.append("24x7 emergency")
        out.append({"id": h.id, "name": h.name, "lat": h.lat, "lon": h.lon, "address": h.address,
                    "distance_km": round(dist, 2), "specialties": specs, "has_emergency": h.has_emergency,
                    "op_limit": h.op_limit, "booked": s["booked"], "free_slots": free,
                    "specialty_match": spec_score == 1.0, "score": round(score, 4), "why": why})
    out.sort(key=lambda r: -r["score"])
    return out[:limit]
