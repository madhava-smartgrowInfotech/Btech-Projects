"""Daily OP limits, emergency quotas and no-show-aware day allocation (integer programme, PuLP).

For each candidate day d in the booking horizon we know the bookings already held (n_d) and the
expected attendance E_d = sum(1 - p_noshow). A day is feasible for one more booking when
  E_d + (1 - p_new) <= op_limit                  (expected patients seen stays within the OP limit)
  n_d + 1 <= floor(op_limit * (1 + MAX_OVERBOOK))  (hard cap on controlled overbooking)
The ILP picks one day minimising  urgency_weight * days_of_delay + overbook_penalty * extra_over_limit,
so urgent patients accept an overbooked slot today while mild cases move to a free day.
"""
from datetime import date, timedelta

import pulp
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import BOOKING_HORIZON_DAYS, MAX_OVERBOOK
from ..db import Booking, Hospital

URGENCY_WEIGHT = {"critical": 100, "severe": 20, "moderate": 6, "mild": 3}
OVERBOOK_PENALTY = 5
ACTIVE = ("waiting", "called", "done", "no_show")


def day_stats(db: Session, hospital_id: int, day: str) -> dict:
    rows = db.execute(select(Booking.noshow_prob, Booking.kind, Booking.uses_quota).where(
        Booking.hospital_id == hospital_id, Booking.date == day, Booking.status.in_(ACTIVE))).all()
    op = [r for r in rows if r.kind == "op" and not r.uses_quota]
    return {
        "booked": len(op),
        "expected": sum(1 - r.noshow_prob for r in op),
        "quota_used": sum(1 for r in rows if r.uses_quota or r.kind == "emergency"),
    }


def hard_cap(h: Hospital) -> int:
    return int(h.op_limit * (1 + MAX_OVERBOOK))


def allocate(db: Session, h: Hospital, requested: date, p_new: float, severity: str, today: date) -> dict:
    """Return {date, uses_quota, moved, reason} for a new booking at hospital h."""
    if severity == "critical" and requested == today:
        s = day_stats(db, h.id, requested.isoformat())
        if s["quota_used"] < h.emergency_quota:
            return {"date": requested, "uses_quota": True, "moved": False,
                    "reason": f"emergency quota slot ({s['quota_used'] + 1}/{h.emergency_quota})"}

    days = [requested + timedelta(days=i) for i in range(BOOKING_HORIZON_DAYS)]
    stats = [day_stats(db, h.id, d.isoformat()) for d in days]
    feasible = [s["expected"] + (1 - p_new) <= h.op_limit and s["booked"] + 1 <= hard_cap(h) for s in stats]
    if not any(feasible):
        return {"date": None, "uses_quota": False, "moved": False,
                "reason": f"fully booked for the next {BOOKING_HORIZON_DAYS} days"}

    prob = pulp.LpProblem("day_allocation", pulp.LpMinimize)
    x = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(len(days))]
    w = URGENCY_WEIGHT.get(severity, 6)
    prob += pulp.lpSum(x[i] * (w * i + OVERBOOK_PENALTY * max(0, s["booked"] + 1 - h.op_limit))
                       for i, s in enumerate(stats))
    prob += pulp.lpSum(x) == 1
    for i, s in enumerate(stats):
        prob += x[i] * (s["expected"] + 1 - p_new) <= h.op_limit
        prob += x[i] * (s["booked"] + 1) <= hard_cap(h)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    i = next(i for i, v in enumerate(x) if v.value() and v.value() > 0.5)
    chosen = days[i]
    s = stats[i]
    if i == 0:
        reason = (f"slot {s['booked'] + 1} of {h.op_limit}"
                  + (" (overbooked - no-show adjusted)" if s["booked"] + 1 > h.op_limit else ""))
    elif not feasible[0]:
        reason = f"{requested.isoformat()} is full - moved automatically to {chosen.isoformat()}"
    else:
        reason = f"moved to {chosen.isoformat()} to avoid overbooking {requested.isoformat()}"
    return {"date": chosen, "uses_quota": False, "moved": i > 0, "reason": reason}


def next_token(db: Session, hospital_id: int, day: str) -> int:
    cur = db.scalar(select(func.max(Booking.token)).where(Booking.hospital_id == hospital_id, Booking.date == day))
    return (cur or 0) + 1
