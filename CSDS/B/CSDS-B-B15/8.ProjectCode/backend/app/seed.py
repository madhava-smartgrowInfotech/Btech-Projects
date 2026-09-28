"""First-run seeding: hospital network, demo logins and clearly labelled sample patients for today."""
import csv
import json
import random
from datetime import datetime, timedelta

from sqlalchemy import func, select

from .auth import hash_password
from .config import DATA
from .db import Booking, Hospital, SessionLocal, User
from .services import noshow, triage
from .services.scheduling import next_token

DEMO_PASSWORD = "demo1234"


def seed_hospitals(db):
    if db.scalar(select(func.count(Hospital.id))):
        return
    with open(DATA / "hospitals_network.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            db.add(Hospital(osm_id=r["osm_id"], name=r["name"], lat=float(r["lat"]), lon=float(r["lon"]),
                            address=r["address"], ownership=r["ownership"], specialties=r["specialties"],
                            has_emergency=r["has_emergency"] == "1", op_limit=int(r["op_limit"]),
                            emergency_quota=int(r["emergency_quota"]), avg_consult_min=float(r["avg_consult_min"]),
                            op_start=r["op_start"]))
    db.commit()


def seed_users(db):
    if db.scalar(select(func.count(User.id))):
        return
    pw = hash_password(DEMO_PASSWORD)
    db.add(User(name="District Admin", email="admin@mediqueue.app", password_hash=pw, role="admin"))
    db.add(User(name="Demo Patient", email="patient@mediqueue.app", password_hash=pw, role="patient",
                age=34, gender="M", phone="9000000001"))
    for h in db.scalars(select(Hospital)).all():
        db.add(User(name=f"OP Desk - {h.name}", email=f"desk{h.id}@mediqueue.app", password_hash=pw,
                    role="staff", hospital_id=h.id))
    db.commit()


def seed_sample_day(db):
    """Sample queue for today (labelled 'Sample patient') so the console and dashboard have live data."""
    today = datetime.now().date()
    day = today.isoformat()
    if db.scalar(select(func.count(Booking.id)).where(Booking.date == day, Booking.is_sample.is_(True))):
        return
    rng = random.Random(int(today.strftime("%Y%m%d")))
    rows = []
    with open(DATA / "disease_symptom" / "dataset.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            syms = [triage.clean_symptom(s) for s in r[1:] if s.strip()]
            rows.append(syms)
    opening = datetime.combine(today, datetime.min.time()).replace(hour=9)
    n = 0
    for h in db.scalars(select(Hospital)).all():
        count = rng.randint(6, 18)
        seen_done = rng.randint(0, 3)
        for i in range(count):
            base = rows[rng.randrange(len(rows))]
            syms = rng.sample(base, k=min(len(base), rng.randint(2, 4)))
            t = triage.classify(syms)
            sev = "severe" if t["severity"] == "critical" else t["severity"]  # critical cases go to emergency, not OP
            age, gender = rng.randint(4, 80), rng.choice("MF")
            b = Booking(hospital_id=h.id, patient_name=f"Sample patient {i + 1}", age=age, gender=gender,
                        date=day, requested_date=day, token=next_token(db, h.id, day), kind="op",
                        severity=sev, priority=triage.PRIORITY[sev],
                        symptoms=json.dumps([s["key"] for s in t["symptoms"]]), condition=t["condition"],
                        specialty=t["specialty"], noshow_prob=noshow.predict(age, gender, today, today - timedelta(days=rng.randint(0, 5))),
                        is_sample=True)
            if i < seen_done:
                b.status = "done"
                b.called_at = opening + timedelta(minutes=i * h.avg_consult_min)
                b.completed_at = b.called_at + timedelta(minutes=h.avg_consult_min * rng.uniform(0.7, 1.3))
            db.add(b)
            db.flush()
            n += 1
    db.commit()
    print(f"seeded {n} sample bookings for {day}")


def run():
    with SessionLocal() as db:
        seed_hospitals(db)
        seed_users(db)
        seed_sample_day(db)
