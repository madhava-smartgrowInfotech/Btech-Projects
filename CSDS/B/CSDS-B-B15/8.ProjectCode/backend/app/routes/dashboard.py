from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require_role
from ..db import Booking, Hospital, Referral, User, get_db
from ..services.queue import consult_minutes, ordered_waiting, today_str

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
LEVELS = ["mild", "moderate", "severe", "critical"]


@router.get("")
def dashboard(date: str | None = None, user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    day = date or today_str()
    bookings = db.scalars(select(Booking).where(Booking.date == day)).all()
    by_h: dict[int, list[Booking]] = {}
    for b in bookings:
        by_h.setdefault(b.hospital_id, []).append(b)

    rows = []
    for h in db.scalars(select(Hospital)).all():
        bs = by_h.get(h.id, [])
        op = [b for b in bs if b.kind == "op" and not b.uses_quota]
        waiting = ordered_waiting(db, h.id, day)
        m = consult_minutes(db, h, day)
        waits, acc = [], 0.0
        for b in waiting:
            waits.append(acc)
            acc += (1 - b.noshow_prob) * m
        rows.append({
            "id": h.id, "name": h.name, "lat": h.lat, "lon": h.lon, "op_limit": h.op_limit,
            "booked": len(op), "load_pct": round(100 * len(op) / max(h.op_limit, 1), 1),
            "waiting": len(waiting), "done": sum(b.status == "done" for b in bs),
            "no_show": sum(b.status == "no_show" for b in bs),
            "emergencies": sum(b.kind == "emergency" or b.uses_quota for b in bs),
            "emergency_quota": h.emergency_quota,
            "avg_wait_min": round(sum(waits) / len(waits), 1) if waits else 0,
            "max_wait_min": round(waits[-1], 1) if waits else 0,
            "severity": {lv: sum(b.severity == lv for b in bs) for lv in LEVELS},
        })
    rows.sort(key=lambda r: -r["load_pct"])
    refs = db.scalars(select(Referral)).all()
    ref_status = {}
    for r in refs:
        ref_status[r.status] = ref_status.get(r.status, 0) + 1
    waiting_rows = [r for r in rows if r["waiting"]]
    return {
        "date": day,
        "totals": {
            "hospitals": len(rows), "bookings": len(bookings),
            "waiting": sum(r["waiting"] for r in rows), "done": sum(r["done"] for r in rows),
            "no_show": sum(r["no_show"] for r in rows), "emergencies": sum(r["emergencies"] for r in rows),
            "moved_next_day": db.query(Booking).filter(Booking.requested_date == day, Booking.date != day).count(),
            "avg_wait_min": round(sum(r["avg_wait_min"] for r in waiting_rows) / len(waiting_rows), 1) if waiting_rows else 0,
            "capacity": sum(r["op_limit"] for r in rows),
        },
        "severity": {lv: sum(b.severity == lv for b in bookings) for lv in LEVELS},
        "referrals": ref_status,
        "hospitals": rows,
    }
