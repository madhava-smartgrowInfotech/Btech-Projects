from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.models import (
    BedStatusEnum,
    DepartmentTypeEnum,
    LabTestStatusEnum,
    PriorityEnum,
    RoleEnum,
    VisitStatusEnum,
)


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: RoleEnum
    specialty: Optional[str] = None
    department_id: Optional[str] = None
    avatar_color: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Department ----------
class DepartmentOut(BaseModel):
    id: str
    name: str
    code: str
    type: DepartmentTypeEnum
    floor: Optional[str] = None
    avg_service_minutes: float

    class Config:
        from_attributes = True


# ---------- Patient / Visit ----------
class PatientCreate(BaseModel):
    name: str
    age: int = Field(ge=0, le=130)
    gender: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None


class VitalsIn(BaseModel):
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    spo2: Optional[float] = None
    temperature_c: Optional[float] = None
    respiratory_rate: Optional[float] = None


class VisitCreate(BaseModel):
    patient: PatientCreate
    department_id: str
    chief_complaint: str
    vitals: Optional[VitalsIn] = None


class PatientOut(BaseModel):
    id: str
    mrn: str
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None

    class Config:
        from_attributes = True


class VisitOut(BaseModel):
    id: str
    token_number: int
    token_code: str
    chief_complaint: Optional[str] = None
    vitals: Optional[dict[str, Any]] = None
    status: VisitStatusEnum
    priority: PriorityEnum
    current_department_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    predicted_wait_minutes: Optional[float] = None
    triage_score: Optional[float] = None
    bed_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    patient: PatientOut

    class Config:
        from_attributes = True


class VisitStatusUpdate(BaseModel):
    status: VisitStatusEnum
    department_id: Optional[str] = None
    note: Optional[str] = None


class AssignDoctorRequest(BaseModel):
    doctor_id: str


# ---------- Beds ----------
class BedOut(BaseModel):
    id: str
    department_id: str
    bed_number: str
    bed_type: str
    status: BedStatusEnum
    current_visit_id: Optional[str] = None

    class Config:
        from_attributes = True


class BedStatusUpdate(BaseModel):
    status: BedStatusEnum


class AdmitRequest(BaseModel):
    bed_id: str


# ---------- Lab ----------
class LabTestCreate(BaseModel):
    visit_id: str
    test_name: str


class LabTestOut(BaseModel):
    id: str
    visit_id: str
    test_name: str
    status: LabTestStatusEnum
    ordered_at: datetime
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class LabTestStatusUpdate(BaseModel):
    status: LabTestStatusEnum
    notes: Optional[str] = None


# ---------- Dashboard / analytics ----------
class KpiSummary(BaseModel):
    patients_today: int
    active_visits: int
    avg_wait_minutes: float
    critical_cases: int
    bed_occupancy_pct: float
    icu_occupancy_pct: float


class DepartmentLoad(BaseModel):
    department: str
    code: str
    waiting: int
    in_progress: int
    avg_wait_minutes: float


class MovementLogOut(BaseModel):
    id: str
    from_department_id: Optional[str] = None
    to_department_id: Optional[str] = None
    note: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
