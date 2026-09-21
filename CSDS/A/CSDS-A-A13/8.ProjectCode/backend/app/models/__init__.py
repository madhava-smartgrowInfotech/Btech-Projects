"""All database tables. Importing this package registers them with the metadata."""
from app.models.user import User
from app.models.exam import Candidate, Course, Department, ExamSession, Hall, Registration, SessionPaper
from app.models.plan import InvigilatorAssignment, Plan, SeatAssignment
from app.models.attendance import AttendanceMark, HallSubmission
from app.models.system import AppSetting, AuditEvent, ImportBatch

__all__ = [
    "AppSetting", "AttendanceMark", "AuditEvent", "Candidate", "Course", "Department", "ExamSession", "Hall",
    "HallSubmission", "ImportBatch", "InvigilatorAssignment", "Plan", "Registration", "SeatAssignment",
    "SessionPaper", "User",
]
