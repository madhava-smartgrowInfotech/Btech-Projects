"""
Populates the database with a believable demo hospital: departments, beds,
staff accounts for every role, and a realistic spread of active patient
visits so every dashboard has something to show on first run.

Usage:  venv/Scripts/python.exe seed.py
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from faker import Faker

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.ml.predictor import DEFAULT_VITALS, ensure_models_trained, predict_triage, predict_wait_minutes
from app.models.models import (
    Bed,
    BedStatusEnum,
    Department,
    DepartmentTypeEnum,
    MovementLog,
    Patient,
    PriorityEnum,
    RoleEnum,
    User,
    Visit,
    VisitStatusEnum,
)
from app.services.queue_service import make_token_code, queue_ahead_count

fake = Faker()
Faker.seed(7)
random.seed(7)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
ensure_models_trained()

db = SessionLocal()

# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------
departments_data = [
    dict(name="General Medicine OPD", code="OPD1", type=DepartmentTypeEnum.opd, floor="Ground", avg_service_minutes=12),
    dict(name="Pediatrics OPD", code="OPD2", type=DepartmentTypeEnum.opd, floor="1st Floor", avg_service_minutes=10),
    dict(name="Emergency", code="ER", type=DepartmentTypeEnum.emergency, floor="Ground", avg_service_minutes=18),
    dict(name="Central Laboratory", code="LAB", type=DepartmentTypeEnum.laboratory, floor="Basement", avg_service_minutes=15),
    dict(name="Pharmacy", code="PHM", type=DepartmentTypeEnum.pharmacy, floor="Ground", avg_service_minutes=5),
    dict(name="General Ward", code="WARD", type=DepartmentTypeEnum.ward, floor="2nd Floor", avg_service_minutes=0),
    dict(name="Intensive Care Unit", code="ICU", type=DepartmentTypeEnum.icu, floor="3rd Floor", avg_service_minutes=0),
]
departments: dict[str, Department] = {}
for d in departments_data:
    dept = Department(**d)
    db.add(dept)
    db.flush()
    departments[dept.code] = dept

# ---------------------------------------------------------------------------
# Beds
# ---------------------------------------------------------------------------
for i in range(1, 13):
    status = BedStatusEnum.available if i > 7 else BedStatusEnum.occupied
    db.add(Bed(department_id=departments["WARD"].id, bed_number=f"W-{i:02d}", bed_type="general", status=status))
for i in range(1, 7):
    status = BedStatusEnum.available if i > 4 else BedStatusEnum.occupied
    db.add(Bed(department_id=departments["ICU"].id, bed_number=f"ICU-{i:02d}", bed_type="icu", status=status))
db.flush()

# ---------------------------------------------------------------------------
# Staff accounts (demo credentials — shown on the login screen)
# ---------------------------------------------------------------------------
staff_data = [
    dict(name="Ananya Sharma", email="admin@medflow.app", password="Admin@123", role=RoleEnum.admin, avatar_color="#7c3aed"),
    dict(name="Dr. Kabir Mehta", email="dr.mehta@medflow.app", password="Doctor@123", role=RoleEnum.doctor,
         specialty="General Medicine", department=departments["OPD1"], avatar_color="#2563eb"),
    dict(name="Dr. Aisha Rao", email="dr.rao@medflow.app", password="Doctor@123", role=RoleEnum.doctor,
         specialty="Emergency Medicine", department=departments["ER"], avatar_color="#dc2626"),
    dict(name="Dr. Neel Verma", email="dr.verma@medflow.app", password="Doctor@123", role=RoleEnum.doctor,
         specialty="Pediatrics", department=departments["OPD2"], avatar_color="#0891b2"),
    dict(name="Priya Iyer", email="nurse.iyer@medflow.app", password="Nurse@123", role=RoleEnum.nurse,
         department=departments["WARD"], avatar_color="#059669"),
    dict(name="Manjeet Singh", email="lab.singh@medflow.app", password="Lab@123", role=RoleEnum.lab_tech,
         department=departments["LAB"], avatar_color="#d97706"),
    dict(name="Harleen Kaur", email="reception.kaur@medflow.app", password="Reception@123", role=RoleEnum.reception,
         avatar_color="#db2777"),
]
users: dict[str, User] = {}
for s in staff_data:
    dept = s.pop("department", None)
    password = s.pop("password")
    user = User(**s, hashed_password=hash_password(password), department_id=dept.id if dept else None)
    db.add(user)
    db.flush()
    users[user.email] = user

# ---------------------------------------------------------------------------
# Sample patients + visits spread across statuses and departments
# ---------------------------------------------------------------------------
COMPLAINTS = [
    "Fever and body ache", "Persistent cough", "Abdominal pain", "Routine checkup",
    "Shortness of breath", "Chest discomfort", "Sprained ankle", "Child with high fever",
    "Headache and dizziness", "Follow-up consultation", "Allergic reaction", "Minor laceration",
]

VISIT_PLAN = [
    # (department_code, status, count)
    ("OPD1", VisitStatusEnum.waiting, 6),
    ("OPD1", VisitStatusEnum.in_consultation, 1),
    ("OPD2", VisitStatusEnum.waiting, 4),
    ("OPD2", VisitStatusEnum.in_consultation, 1),
    ("ER", VisitStatusEnum.waiting, 3),
    ("ER", VisitStatusEnum.in_consultation, 1),
    ("LAB", VisitStatusEnum.lab_pending, 3),
    ("LAB", VisitStatusEnum.lab_in_progress, 2),
    ("PHM", VisitStatusEnum.pharmacy, 2),
]

token_counters: dict[str, int] = {code: 0 for code in departments}


def random_vitals(critical: bool = False) -> dict:
    if critical:
        return dict(
            heart_rate=round(random.uniform(125, 160), 0),
            systolic_bp=round(random.uniform(75, 88), 0),
            diastolic_bp=round(random.uniform(45, 60), 0),
            spo2=round(random.uniform(84, 90), 0),
            temperature_c=round(random.uniform(39.2, 40.3), 1),
            respiratory_rate=round(random.uniform(26, 32), 0),
        )
    return dict(
        heart_rate=round(random.uniform(65, 95), 0),
        systolic_bp=round(random.uniform(105, 130), 0),
        diastolic_bp=round(random.uniform(68, 84), 0),
        spo2=round(random.uniform(95, 99), 0),
        temperature_c=round(random.uniform(36.4, 37.4), 1),
        respiratory_rate=round(random.uniform(14, 19), 0),
    )


created_visits = 0
for dept_code, visit_status, count in VISIT_PLAN:
    dept = departments[dept_code]
    for i in range(count):
        make_critical = random.random() < 0.12
        patient = Patient(
            mrn=f"MRN{random.randint(100000, 999999)}",
            name=fake.name(),
            age=random.randint(1, 88),
            gender=random.choice(["Male", "Female"]),
            phone=fake.phone_number()[:15],
            blood_group=random.choice(["A+", "B+", "O+", "AB+", "O-", "A-"]),
        )
        db.add(patient)
        db.flush()

        vitals = random_vitals(make_critical)
        triage_vitals = {k: v for k, v in vitals.items() if k != "diastolic_bp"}
        priority_label, confidence = predict_triage(age=patient.age, **triage_vitals)
        priority = PriorityEnum(priority_label)

        token_counters[dept_code] += 1
        token_number = token_counters[dept_code]
        token_code = make_token_code(dept, token_number)

        ahead = queue_ahead_count(db, dept.id, priority)
        predicted_wait = predict_wait_minutes(
            department_type=dept.type.value,
            queue_ahead=ahead,
            priority=priority.value,
            avg_service_minutes=dept.avg_service_minutes,
        )

        created_minutes_ago = random.randint(2, 90)
        visit = Visit(
            patient_id=patient.id,
            token_number=token_number,
            token_code=token_code,
            chief_complaint=random.choice(COMPLAINTS),
            vitals=vitals,
            status=visit_status,
            priority=priority,
            current_department_id=dept.id,
            assigned_doctor_id=None,
            predicted_wait_minutes=predicted_wait,
            triage_score=confidence,
            created_at=datetime.utcnow() - timedelta(minutes=created_minutes_ago),
            updated_at=datetime.utcnow() - timedelta(minutes=max(0, created_minutes_ago - 5)),
        )
        db.add(visit)
        db.flush()
        db.add(MovementLog(visit_id=visit.id, from_department_id=None, to_department_id=dept.id, note="Registered"))
        created_visits += 1

# A handful of already-discharged visits earlier today, for KPI history
for _ in range(9):
    patient = Patient(
        mrn=f"MRN{random.randint(100000, 999999)}",
        name=fake.name(),
        age=random.randint(5, 80),
        gender=random.choice(["Male", "Female"]),
        phone=fake.phone_number()[:15],
        blood_group=random.choice(["A+", "B+", "O+", "AB+"]),
    )
    db.add(patient)
    db.flush()
    dept = departments["OPD1"]
    token_counters["OPD1"] += 1
    created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 6))
    visit = Visit(
        patient_id=patient.id,
        token_number=token_counters["OPD1"],
        token_code=make_token_code(dept, token_counters["OPD1"]),
        chief_complaint=random.choice(COMPLAINTS),
        vitals=random_vitals(False),
        status=VisitStatusEnum.discharged,
        priority=PriorityEnum.normal,
        current_department_id=dept.id,
        predicted_wait_minutes=round(random.uniform(8, 35), 1),
        triage_score=0.9,
        created_at=created_at,
        updated_at=created_at + timedelta(minutes=30),
        discharged_at=created_at + timedelta(minutes=45),
    )
    db.add(visit)
    created_visits += 1

db.commit()
db.close()

print(f"Seeded {len(departments)} departments, {len(users)} staff accounts, {created_visits} patient visits.")
print("\nDemo login credentials:")
print("  admin@medflow.app         / Admin@123      (Administrator)")
print("  dr.mehta@medflow.app      / Doctor@123     (Doctor - General Medicine)")
print("  dr.rao@medflow.app        / Doctor@123     (Doctor - Emergency)")
print("  dr.verma@medflow.app      / Doctor@123     (Doctor - Pediatrics)")
print("  nurse.iyer@medflow.app    / Nurse@123      (Nurse - Ward)")
print("  lab.singh@medflow.app     / Lab@123        (Lab Technician)")
print("  reception.kaur@medflow.app/ Reception@123  (Reception)")
