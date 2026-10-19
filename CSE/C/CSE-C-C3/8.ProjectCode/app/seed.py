"""ParkSure seed: realistic demo locations/users/bookings with on-time + overstay mix."""
from __future__ import annotations
from datetime import timedelta
import random
from .config import BUFFER_INIT
from .engine import utcnow, ensure_tz
from .models import ParkingLocation, Reservation, User, TrustEvent, Payment
from .auth import hash_password

LOCATIONS = [
    ("Central Station Garage", "12 Station Road", 12.9716, 77.5946, 20, 4.0),
    ("Market Street Lot", "45 Market Street", 12.9750, 77.6000, 12, 3.0),
    ("Riverside Parking", "8 River View", 12.9650, 77.5900, 15, 2.5),
    ("Airport Express Park", "Airport Road", 12.9850, 77.6100, 25, 5.0),
    ("Old Town Deck", "3 Heritage Lane", 12.9600, 77.5850, 8, 2.0),
]


def seed_if_empty(db) -> bool:
    if db.query(ParkingLocation).count() > 0:
        return False
    rnd = random.Random(42)
    for name, addr, lat, lon, cap, price in LOCATIONS:
        db.add(ParkingLocation(name=name, address=addr, latitude=lat, longitude=lon,
                               capacity=cap, buffer_size=BUFFER_INIT, price_per_hour=price))
    admin = User(name="ParkSure Admin", email="admin@parksure.app",
                 password_hash=hash_password("admin123"), role="admin", trust_score=5.0)
    db.add(admin)
    drivers = []
    for i in range(1, 9):
        late = i in (3, 6)  # demo users with overstay history
        u = User(name=f"Demo Driver {i}", email=f"driver{i}@parksure.app",
                 password_hash=hash_password("driver123"), role="driver",
                 trust_score=2.0 if late else (4.0 if i in (1, 2) else 3.0))
        db.add(u)
        drivers.append((u, late))
    db.flush()
    now = utcnow()
    locs = db.query(ParkingLocation).all()
    small = [l for l in locs if l.capacity <= 12] or locs
    # 60 days of history: mix of completed on-time, late, failed, declined.
    for day in range(60, 0, -1):
        for _ in range(rnd.randint(2, 5)):
            loc = rnd.choice(locs)
            u, late_user = rnd.choice(drivers)
            start = now - timedelta(days=day, hours=rnd.randint(0, 12))
            end = start + timedelta(hours=rnd.choice([1, 2, 2, 3, 4]))
            roll = rnd.random()
            if roll < 0.08:
                st = "failed"
            elif roll < 0.18:
                st = "declined"
            else:
                st = "completed"
            late = (roll > 0.55 and late_user) or rnd.random() < 0.12
            r = Reservation(user_id=u.id, location_id=loc.id, start_time=start, end_time=end,
                            status=st, fee=round(2 * loc.price_per_hour, 2), fee_multiplier=1.0,
                            checked_in_at=start if st in ("completed", "failed") else None,
                            checked_out_at=(end + timedelta(minutes=45 if late else -5)) if st == "completed" else None,
                            decline_reason=("No forecasted availability in simulation window" if st == "declined"
                                            else ("No free slot at arrival" if st == "failed" else "")))
            db.add(r)
            db.flush()
            if st == "completed":
                db.add(Payment(reservation_id=r.id, user_id=u.id, amount=r.fee, provider="demo", status="paid"))
            if st == "completed" and late:
                db.add(TrustEvent(user_id=u.id, kind="warning", detail="Late checkout (seeded history)",
                                  created_at=end))
    # Peak-hour pressure bursts at smaller lots so Strategy Insights has real
    # contention to replay: many overlapping Friday-evening requests at Old Town Deck.
    deck = next((l for l in locs if l.name == "Old Town Deck"), small[0])
    for week in range(8):
        base = (now - timedelta(weeks=week)).replace(hour=18, minute=0, second=0, microsecond=0)
        # move to the most recent Friday 18:00 relative to base
        days_back = (base.weekday() - 4) % 7
        peak = base - timedelta(days=days_back)
        if peak > now:
            peak -= timedelta(weeks=1)
        for k in range(deck.capacity + 3):  # over-subscribe: forces declined/unable
            u, _ = rnd.choice(drivers)
            s = peak + timedelta(minutes=rnd.randint(0, 15))
            e = s + timedelta(hours=1)
            late = rnd.random() < 0.5
            roll = rnd.random()
            st = "completed" if roll < 0.7 else ("declined" if roll < 0.85 else "failed")
            r = Reservation(user_id=u.id, location_id=deck.id, start_time=s, end_time=e,
                            status=st, fee=round(2 * deck.price_per_hour, 2), fee_multiplier=1.0,
                            checked_in_at=s if st in ("completed", "failed") else None,
                            checked_out_at=(e + timedelta(minutes=50 if late else -5)) if st == "completed" else None,
                            decline_reason=("No forecasted availability during peak window" if st == "declined"
                                            else ("No free slot at arrival during peak" if st == "failed" else "")))
            db.add(r)
            db.flush()
            if st == "completed":
                db.add(Payment(reservation_id=r.id, user_id=u.id, amount=r.fee, provider="demo", status="paid"))
                if late:
                    db.add(TrustEvent(user_id=u.id, kind="warning", detail="Late checkout (seeded peak history)",
                                      created_at=e))
        for j in range(5):  # second wave arrives as wave-1 bookings end; overstays still occupy slots
            u, _ = rnd.choice(drivers)
            s = peak + timedelta(minutes=65 + rnd.randint(0, 10))
            e = s + timedelta(hours=1)
            st = "completed" if rnd.random() < 0.75 else "failed"
            r = Reservation(user_id=u.id, location_id=deck.id, start_time=s, end_time=e,
                            status=st, fee=round(2 * deck.price_per_hour, 2), fee_multiplier=1.0,
                            checked_in_at=s if st == "completed" else None,
                            checked_out_at=(e - timedelta(minutes=5)) if st == "completed" else None,
                            decline_reason=("No free slot at arrival (peak overstays)" if st == "failed" else ""))
            db.add(r)
            db.flush()
            if st == "completed":
                db.add(Payment(reservation_id=r.id, user_id=u.id, amount=r.fee, provider="demo", status="paid"))
    db.commit()
    return True
