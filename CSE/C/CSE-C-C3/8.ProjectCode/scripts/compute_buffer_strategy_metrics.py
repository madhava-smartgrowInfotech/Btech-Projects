"""Deterministic buffer-strategy simulation over real stored booking history.

Replays the location's historical reservation requests in chronological order under
four buffer configurations (0 fixed / 1 fixed / 3 fixed / dynamic policy) and counts:
- unable_to_park: request admitted but no physical slot free at arrival
- declined: request rejected by the admission rule (bookings + buffer >= capacity)

The dynamic policy mirrors the live engine: start at BUFFER_INIT, +1 on each
on-time checkout (cap BUFFER_MAX), reset to BUFFER_INIT every 24h window.
Overstay is derived from actual stored checkout data (checked_out_at > end_time).
No randomness: identical input always yields identical output.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from datetime import timedelta
from collections import defaultdict
from app import config as C
from app.models import Reservation, ParkingLocation


def _tz(dt):
    from datetime import timezone
    return dt if dt and dt.tzinfo else (dt.replace(tzinfo=timezone.utc) if dt else dt)


def _overstay(res) -> bool:
    if res.checked_out_at is None:
        return False
    return _tz(res.checked_out_at) > _tz(res.end_time) + timedelta(minutes=10)


def simulate(requests: list[dict], capacity: int, mode) -> dict:
    """requests: [{start,end,on_time}] sorted by start. mode: int buffer or 'dynamic'."""
    buf = C.BUFFER_INIT if mode == "dynamic" else int(mode)
    parked_until: list = []   # end times of occupying vehicles (overstays linger +45m)
    active: list = []         # (start,end) of admitted bookings overlapping
    last_reset = None
    unable = declined = 0
    for rq in requests:
        s, e = rq["start"], rq["end"]
        if mode == "dynamic":
            if last_reset is None:
                last_reset = s
            if (s - last_reset) >= timedelta(hours=C.BUFFER_RESET_HOURS):
                buf = C.BUFFER_INIT
                last_reset = s
        # free finished occupancy
        parked_until = [t for t in parked_until if t > s]
        overlap = sum(1 for (a, b) in active if a < e and b > s)
        if overlap + buf >= capacity:
            declined += 1
            continue
        # admitted: physical arrival check against true capacity
        if len(parked_until) >= capacity:
            unable += 1
        else:
            parked_until.append(e + (timedelta(minutes=45) if not rq["on_time"] else timedelta(0)))
            active.append((s, e))
            if mode == "dynamic" and rq["on_time"] and buf < C.BUFFER_MAX:
                buf += 1
    return {"unable_to_park": unable, "declined": declined}


def compute_all(db, window_days: int = 60) -> dict:
    from app.engine import utcnow
    since = utcnow() - timedelta(days=window_days)
    locs = db.query(ParkingLocation).all()
    per_location = []
    totals = {"fixed_0": {"unable_to_park": 0, "declined": 0},
              "fixed_1": {"unable_to_park": 0, "declined": 0},
              "fixed_3": {"unable_to_park": 0, "declined": 0},
              "dynamic": {"unable_to_park": 0, "declined": 0}}
    for loc in locs:
        rows = (db.query(Reservation)
                .filter(Reservation.location_id == loc.id, Reservation.start_time >= since,
                        Reservation.status.in_(("completed", "failed", "active", "reserved")))
                .order_by(Reservation.start_time).all())
        reqs = [{"start": _tz(r.start_time), "end": _tz(r.end_time),
                 "on_time": (not _overstay(r))} for r in rows]
        actual_unable = sum(1 for r in rows if r.status == "failed")
        actual_declined = db.query(Reservation).filter(
            Reservation.location_id == loc.id, Reservation.status == "declined",
            Reservation.start_time >= since).count()
        sim = {"fixed_0": simulate(reqs, loc.capacity, 0),
               "fixed_1": simulate(reqs, loc.capacity, 1),
               "fixed_3": simulate(reqs, loc.capacity, 3),
               "dynamic": simulate(reqs, loc.capacity, "dynamic")}
        for k in totals:
            totals[k]["unable_to_park"] += sim[k]["unable_to_park"]
            totals[k]["declined"] += sim[k]["declined"]
        per_location.append({"location_id": loc.id, "location": loc.name, "capacity": loc.capacity,
                             "current_buffer": loc.buffer_size, "requests": len(reqs),
                             "actual": {"unable_to_park": actual_unable, "declined": actual_declined},
                             "simulated": sim})
    return {"window_days": window_days, "per_location": per_location, "totals": totals,
            "policy": {"init": C.BUFFER_INIT, "max": C.BUFFER_MAX, "reset_hours": C.BUFFER_RESET_HOURS},
            "note": "Simulated counts replay the location's real stored booking requests deterministically."}


if __name__ == "__main__":
    import argparse, json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.database import SessionLocal, Base, engine
    from app.seed import seed_if_empty
    ap = argparse.ArgumentParser(description="ParkSure buffer strategy metrics")
    ap.add_argument("--window-days", type=int, default=60)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
        out = compute_all(db, window_days=args.window_days)
    finally:
        db.close()
    print(json.dumps(out, indent=2, default=str))
