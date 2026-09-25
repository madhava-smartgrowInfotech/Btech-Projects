import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class RoleEnum(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"
    lab_tech = "lab_tech"
    reception = "reception"


class DepartmentTypeEnum(str, enum.Enum):
    opd = "opd"
    laboratory = "laboratory"
    pharmacy = "pharmacy"
    ward = "ward"
    icu = "icu"
    emergency = "emergency"


class VisitStatusEnum(str, enum.Enum):
    waiting = "waiting"
    in_consultation = "in_consultation"
    lab_pending = "lab_pending"
    lab_in_progress = "lab_in_progress"
    pharmacy = "pharmacy"
    admitted_ward = "admitted_ward"
    admitted_icu = "admitted_icu"
    discharged = "discharged"
    cancelled = "cancelled"


class PriorityEnum(str, enum.Enum):
    critical = "critical"
    urgent = "urgent"
    normal = "normal"


class BedStatusEnum(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    cleaning = "cleaning"
    reserved = "reserved"


class LabTestStatusEnum(str, enum.Enum):
    ordered = "ordered"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    specialty = Column(String, nullable=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    avatar_color = Column(String, default="#6366f1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="staff")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    type = Column(Enum(DepartmentTypeEnum), nullable=False)
    floor = Column(String, nullable=True)
    avg_service_minutes = Column(Float, default=15.0)

    staff = relationship("User", back_populates="department")
    beds = relationship("Bed", back_populates="department")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=gen_id)
    mrn = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    visits = relationship("Visit", back_populates="patient")


class Visit(Base):
    __tablename__ = "visits"

    id = Column(String, primary_key=True, default=gen_id)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    token_number = Column(Integer, nullable=False)
    token_code = Column(String, nullable=False)
    chief_complaint = Column(String, nullable=True)
    vitals = Column(JSON, nullable=True)
    status = Column(Enum(VisitStatusEnum), default=VisitStatusEnum.waiting)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.normal)
    current_department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    assigned_doctor_id = Column(String, ForeignKey("users.id"), nullable=True)
    predicted_wait_minutes = Column(Float, nullable=True)
    triage_score = Column(Float, nullable=True)
    bed_id = Column(String, ForeignKey("beds.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    discharged_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="visits")
    current_department = relationship("Department", foreign_keys=[current_department_id])
    assigned_doctor = relationship("User", foreign_keys=[assigned_doctor_id])
    lab_tests = relationship("LabTest", back_populates="visit")
    movements = relationship("MovementLog", back_populates="visit", order_by="MovementLog.timestamp")


class Bed(Base):
    __tablename__ = "beds"

    id = Column(String, primary_key=True, default=gen_id)
    department_id = Column(String, ForeignKey("departments.id"), nullable=False)
    bed_number = Column(String, nullable=False)
    bed_type = Column(String, default="general")
    status = Column(Enum(BedStatusEnum), default=BedStatusEnum.available)
    current_visit_id = Column(String, ForeignKey("visits.id", use_alter=True), nullable=True)

    department = relationship("Department", back_populates="beds")


class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(String, primary_key=True, default=gen_id)
    visit_id = Column(String, ForeignKey("visits.id"), nullable=False)
    test_name = Column(String, nullable=False)
    status = Column(Enum(LabTestStatusEnum), default=LabTestStatusEnum.ordered)
    ordered_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    visit = relationship("Visit", back_populates="lab_tests")


class MovementLog(Base):
    __tablename__ = "movement_logs"

    id = Column(String, primary_key=True, default=gen_id)
    visit_id = Column(String, ForeignKey("visits.id"), nullable=False)
    from_department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    to_department_id = Column(String, ForeignKey("departments.id"), nullable=True)
    note = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    visit = relationship("Visit", back_populates="movements")
