"""Parity checks: the simulator's admission, trust and suspension rules against the real engine.

Each function returns {'cases': n, 'mismatches': k}; a faithful simulator has zero mismatches.
"""
from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import models  # noqa: E402,F401
from app.database import Base  # noqa: E402
from app.engine import forecast_free, record_checkout_trust, suspension_block  # noqa: E402
from app.models import ParkingLocation, Reservation, TrustEvent, User  # noqa: E402
from scripts.parking_sim import Area, HOUR, admit, suspended, trust_update  # noqa: E402

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)


def _session():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)
    return sessionmaker(bind=eng, autoflush=False, autocommit=False)()


def admission_parity(n_requests: int = 400, seed: int = 7) -> dict:
    rnd = random.Random(seed)
    cases = mism = 0
    for cap, buf in [(4, 0), (6, 1), (8, 3), (5, 1), (10, 3)]:
        db = _session()
        loc = ParkingLocation(name="P", address="", latitude=12.9, longitude=77.5, capacity=cap, buffer_size=buf, price_per_hour=3)
        u = User(name="U", email="u@x.io", password_hash="x")
        db.add_all([loc, u])
        db.commit()
        area = Area(0, 12.9, 77.5, cap=cap)
        area.buffer = buf
        for rid in range(n_requests):
            s_min = rnd.uniform(0, 48 * 60)
            e_min = s_min + rnd.uniform(60, 180)
            s, e = T0 + timedelta(minutes=s_min), T0 + timedelta(minutes=e_min)
            real = forecast_free(db, loc, s, e)
            sim = admit(area.overlap(s_min, e_min), area.buffer, area.cap)
            cases += 1
            mism += real != sim
            if real:
                db.add(Reservation(user_id=u.id, location_id=loc.id, start_time=s, end_time=e, status="reserved"))
                db.commit()
            if sim:
                area.res[rid] = (s_min, e_min)
        db.close()
    return {"cases": cases, "mismatches": mism}


def trust_parity(n_users: int = 200, steps: int = 40, seed: int = 11) -> dict:
    rnd = random.Random(seed)
    db = _session()
    cases = mism = 0
    for i in range(n_users):
        p_late = rnd.choice([0.0, 0.1, 0.25, 0.5, 0.8])
        u = User(name="U", email=f"u{i}@x.io", password_hash="x", trust_score=3.0)
        db.add(u)
        db.commit()
        st = {"trust": 3.0, "streak": 0, "warnings": 0, "last_warning": None, "suspended_until": -1.0, "now": 0.0}
        for step in range(steps):
            on_time = rnd.random() >= p_late
            record_checkout_trust(db, u, on_time)
            st["now"] = step * 60.0
            trust_update(st, on_time)
            cases += 1
            mism += (u.trust_score, u.benefit_streak, u.warning_count) != (st["trust"], st["streak"], st["warnings"])
    db.close()
    return {"cases": cases, "mismatches": mism}


def suspension_parity(n_cases: int = 300, seed: int = 13) -> dict:
    rnd = random.Random(seed)
    db = _session()
    cases = mism = 0
    for i in range(n_cases):
        trust = float(rnd.randint(0, 5))
        warned_days_ago = rnd.choice([None, 0.5, 3, 13, 15, 40])
        u = User(name="U", email=f"s{i}@x.io", password_hash="x", trust_score=trust)
        db.add(u)
        db.commit()
        now_min = 100 * 24 * 60.0
        st = {"trust": trust, "streak": 0, "warnings": 0, "last_warning": None, "suspended_until": -1.0, "now": now_min}
        if warned_days_ago is not None:
            db.add(TrustEvent(user_id=u.id, kind="warning", detail="w",
                              created_at=datetime.now(timezone.utc) - timedelta(days=warned_days_ago)))
            db.commit()
            st["last_warning"] = now_min - warned_days_ago * 24 * HOUR
        real = suspension_block(db, u) is not None
        sim = suspended(st, now_min)
        cases += 1
        mism += real != sim
    db.close()
    return {"cases": cases, "mismatches": mism}


def all_parity() -> dict:
    a, t, s = admission_parity(), trust_parity(), suspension_parity()
    return {"admission": a, "trust": t, "suspension": s,
            "total_cases": a["cases"] + t["cases"] + s["cases"],
            "total_mismatches": a["mismatches"] + t["mismatches"] + s["mismatches"]}


if __name__ == "__main__":
    print(all_parity())
