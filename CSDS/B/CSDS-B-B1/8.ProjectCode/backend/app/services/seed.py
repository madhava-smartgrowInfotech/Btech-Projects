"""Seeded generator for wards, departments, accounts and SAMPLE complaint histories.

Sample complaints reuse real CivicComp-HiEn complaint texts (EN / HI / Hinglish), are placed in
sample wards of Bengaluru (the city the texts come from), and take their resolution times from the
real NYC 311 distribution of the same category. Every generated row has is_sample = True and is
shown with a "Sample" badge in the UI.
"""
from datetime import datetime, timedelta

import numpy as np

from ..auth import hash_password
from ..config import SEED
from ..db import Complaint, Department, Event, SessionLocal, User, Ward
from .taxonomy import CATEGORY_TO_DEPT, DEPARTMENTS

# Sample city: Bengaluru localities (approximate centres)
WARDS = [
    ("Koramangala", 12.9352, 77.6245), ("Indiranagar", 12.9784, 77.6408), ("Jayanagar", 12.9250, 77.5938),
    ("BTM Layout", 12.9166, 77.6101), ("HSR Layout", 12.9116, 77.6474), ("Whitefield", 12.9698, 77.7500),
    ("Malleshwaram", 13.0031, 77.5643), ("Rajajinagar", 12.9910, 77.5550), ("Hebbal", 13.0358, 77.5970),
    ("Yelahanka", 13.1007, 77.5963), ("Basavanagudi", 12.9422, 77.5738), ("Banashankari", 12.9255, 77.5468),
    ("Marathahalli", 12.9569, 77.7011), ("Electronic City", 12.8452, 77.6602), ("JP Nagar", 12.9063, 77.5857),
    ("Shivajinagar", 12.9857, 77.6057), ("Bellandur", 12.9304, 77.6784), ("Hennur", 13.0358, 77.6433),
    ("Vijayanagar", 12.9719, 77.5329), ("KR Puram", 13.0077, 77.6955), ("Bommanahalli", 12.9030, 77.6240),
    ("Yeshwanthpur", 13.0285, 77.5409), ("Ulsoor", 12.9817, 77.6190), ("Frazer Town", 12.9968, 77.6143),
]

DEMO_ACCOUNTS = [
    ("Demo Citizen", "citizen@civicpulse.local", "Citizen@123", "citizen", None),
    ("Grievance Officer", "officer@civicpulse.local", "Officer@123", "officer", None),
    ("City Administrator", "admin@civicpulse.local", "Admin@123", "admin", None),
]
N_SAMPLE_COMPLAINTS = 700
N_SAMPLE_QUEUE = 12  # most recent sample complaints left awaiting officer review
HISTORY_DAYS = 90


def nearest_ward(db, lat, lng):
    wards = db.query(Ward).all()
    if lat is None or lng is None or not wards:
        return None
    return min(wards, key=lambda w: (w.lat - lat) ** 2 + (w.lng - lng) ** 2)


def seed_base(db):
    if db.query(Department).count() == 0:
        db.add_all([Department(name=n, sla_days=d) for n, d in DEPARTMENTS.items()])
    if db.query(Ward).count() == 0:
        db.add_all([Ward(name=n, lat=la, lng=ln) for n, la, ln in WARDS])
    for name, email, pw, role, dept in DEMO_ACCOUNTS:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=name, email=email, password_hash=hash_password(pw), role=role, department=dept))
    for dept in DEPARTMENTS:  # one sample field officer per department
        email = f"{dept.lower().replace(' ', '.')}@civicpulse.local"
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=f"{dept} Desk", email=email, password_hash=hash_password("Officer@123"),
                        role="officer", department=dept, is_sample=True))
    db.commit()


def seed_history(db, predictor, log=print):
    """Generate sample complaint histories (only when none exist yet)."""
    if db.query(Complaint).filter_by(is_sample=True).count():
        return
    from .datasets import load_civiccomp, load_nyc

    rng = np.random.default_rng(SEED)
    cc = load_civiccomp()
    cc = cc[cc.category.notna() & (cc.split == "test")].reset_index(drop=True)  # unseen by the models
    nyc_days = load_nyc().groupby("category").days.apply(np.asarray).to_dict()
    wards = db.query(Ward).all()
    officer = db.query(User).filter_by(email="officer@civicpulse.local").one()
    depts = {d.name: d.sla_days for d in db.query(Department).all()}

    # sample citizens (no personal data)
    citizens = []
    for i in range(1, 41):
        email = f"sample.citizen{i:02d}@civicpulse.local"
        u = db.query(User).filter_by(email=email).first()
        if not u:
            u = User(name=f"Sample Citizen {i:02d}", email=email, password_hash=hash_password(f"Sample@{i:02d}x"),
                     role="citizen", is_sample=True)
            db.add(u)
        citizens.append(u)
    db.flush()

    # each category has a few wards where it recurs more often -> visible hotspots
    cats = sorted(cc.category.unique())
    hot = {c: rng.choice(len(wards), size=3, replace=False) for c in cats}
    picks = cc.sample(N_SAMPLE_COMPLAINTS, random_state=SEED).reset_index(drop=True)
    now = datetime.now().replace(microsecond=0)
    ages = np.sort(rng.gamma(2.0, HISTORY_DAYS / 5, size=N_SAMPLE_COMPLAINTS).clip(0.05, HISTORY_DAYS))[::-1]
    log(f"generating {N_SAMPLE_COMPLAINTS} sample complaints...")
    for i, row in picks.iterrows():
        created = now - timedelta(days=float(ages[i]), hours=float(rng.uniform(0, 3)))
        created = created.replace(hour=int(rng.choice([8, 9, 10, 11, 12, 14, 16, 18, 20])))
        if created > now:
            created = now - timedelta(minutes=int(rng.integers(5, 300)))
        w = wards[int(rng.choice(hot[row.category]))] if rng.random() < 0.55 else wards[int(rng.integers(len(wards)))]
        lat, lng = w.lat + rng.normal(0, 0.006), w.lng + rng.normal(0, 0.006)
        queue = i >= N_SAMPLE_COMPLAINTS - N_SAMPLE_QUEUE
        ai = predictor.predict(row.text, created, explain=queue)
        ai["sla_days"] = depts[ai["department"]]
        ai["sla_breach_risk"] = ai["expected_days"] > ai["sla_days"]
        c = Complaint(tracking_id=f"CP-{created:%y%m}-S{i:04d}", citizen_id=citizens[i % len(citizens)].id,
                      text=row.text, language=row.lang, lat=float(lat), lng=float(lng), ward_id=w.id,
                      created_at=created, ai=ai, is_sample=True,
                      extraction_status="not_requested", status="Submitted")
        c.events.append(Event(kind="status", status="Submitted", message="Complaint received",
                              created_at=created))
        if not queue:
            # historical decision = the dataset's reference label
            c.final_category, c.final_priority = row.category, row.priority
            c.final_department = CATEGORY_TO_DEPT[row.category]
            c.final_days = round(predictor.expected_days(row.category, row.priority, created)[0], 1)
            c.reviewed_by, c.reviewed_at = officer.id, created + timedelta(hours=float(rng.uniform(0.5, 8)))
            c.status = "Assigned"
            c.events.append(Event(kind="status", status="Assigned", actor_id=officer.id, created_at=c.reviewed_at,
                                  message=f"Assigned to {c.final_department}"))
            actual = float(rng.choice(nyc_days[row.category]))  # real 311 resolution time of this category
            done = created + timedelta(days=actual)
            if done <= now and rng.random() < 0.93:
                c.status, c.resolved_at = "Resolved", max(done, c.reviewed_at + timedelta(minutes=30))
                c.events.append(Event(kind="status", status="Resolved", actor_id=officer.id,
                                      created_at=c.resolved_at, message="Issue resolved by field team"))
            elif (now - c.reviewed_at).days >= 1:
                c.status = "In Progress"
                c.events.append(Event(kind="status", status="In Progress", actor_id=officer.id,
                                      created_at=c.reviewed_at + timedelta(hours=6), message="Field team assigned"))
        db.add(c)
    db.commit()
    log("sample history ready")


def run_seed(predictor, log=print):
    db = SessionLocal()
    try:
        seed_base(db)
        seed_history(db, predictor, log=log)
    finally:
        db.close()
