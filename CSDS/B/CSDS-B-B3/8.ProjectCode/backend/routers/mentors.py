"""Peer mentorship: student side (/mentors) and mentor panel (/mentor)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.deps import get_db, require, student_of, mentor_of, iso
from database.models import User, MentorProfile, StudentProfile, MentorRequest, MentorshipSession
from ai.mentor_engine import recommend_mentors
from services.mentorship_service import (
    send_request, get_requests_for_student, get_sessions_for_student, submit_feedback,
    get_requests_for_mentor, respond_to_request, get_sessions_for_mentor,
)
from services.analytics_service import student_skill_dataframe, learning_completion_dataframe
from services.gamification_service import award_xp

router = APIRouter(tags=["mentorship"])
student_only = require("student")
mentor_only = require("mentor")


def mentor_name(db, mentor_id):
    mp = db.get(MentorProfile, mentor_id)
    u = db.get(User, mp.user_id) if mp else None
    return u.name if u else "Unknown"


def session_dict(db, s: MentorshipSession, other: str):
    return {"id": s.id, "topic": s.topic, "status": s.status, "scheduled_time": s.scheduled_time,
            "student_rating": s.student_rating, "mentor_feedback": s.mentor_feedback, "with": other}


# ---------------------------------------------------------------- student side
class RecommendIn(BaseModel):
    required_skill: str = ""
    career_goal: str = ""
    domain: str = ""


@router.post("/mentors/recommend")
def recommend(body: RecommendIn, user: User = Depends(student_only), db=Depends(get_db)):
    return recommend_mentors(db, required_skill=body.required_skill, career_goal=body.career_goal, domain=body.domain)


class RequestIn(BaseModel):
    mentor_id: int
    message: str = Field(min_length=1)


@router.post("/mentors/requests")
def create_request(body: RequestIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    if not db.get(MentorProfile, body.mentor_id):
        raise HTTPException(404, "Mentor not found.")
    req, err = send_request(db, sp.id, body.mentor_id, body.message)
    if err:
        raise HTTPException(422, err)
    return {"id": req.id, "message": f"Request sent to {mentor_name(db, body.mentor_id)}."}


@router.get("/mentors/requests")
def my_requests(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    return [{"id": r.id, "mentor_id": r.mentor_id, "mentor": mentor_name(db, r.mentor_id), "status": r.status, "message": r.message,
             "created_at": iso(r.created_at)} for r in get_requests_for_student(db, sp.id)]


@router.get("/mentors/sessions")
def my_sessions(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    out = []
    for s in get_sessions_for_student(db, sp.id):
        req = db.get(MentorRequest, s.request_id)
        out.append(session_dict(db, s, mentor_name(db, req.mentor_id)))
    return out


class RateIn(BaseModel):
    rating: int = Field(ge=1, le=5)


@router.post("/mentors/sessions/{session_id}/complete")
def complete_session(session_id: int, body: RateIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    s = db.get(MentorshipSession, session_id)
    req = db.get(MentorRequest, s.request_id) if s else None
    if not s or req.student_id != sp.id:
        raise HTTPException(404, "Session not found.")
    if s.status != "scheduled":
        raise HTTPException(422, "This session is already closed.")
    submit_feedback(db, s.id, rating=body.rating)
    award_xp(db, user.id, "mentorship_session_completed")
    return {"message": "Session marked complete. Thank you for your feedback!"}


# ---------------------------------------------------------------- mentor panel
@router.get("/mentor/panel")
def panel(user: User = Depends(mentor_only), db=Depends(get_db)):
    mp = mentor_of(db, user)
    pending = []
    for r in get_requests_for_mentor(db, mp.id, status="pending"):
        sp = db.get(StudentProfile, r.student_id)
        su = db.get(User, sp.user_id)
        pending.append({"id": r.id, "student": su.name, "branch": sp.branch, "year": sp.year,
                        "career_goal": sp.career_goal, "message": r.message, "created_at": iso(r.created_at)})
    sessions = []
    for s in get_sessions_for_mentor(db, mp.id):
        req = db.get(MentorRequest, s.request_id)
        sp = db.get(StudentProfile, req.student_id)
        su = db.get(User, sp.user_id)
        skills = student_skill_dataframe(db, sp.id)
        prog = learning_completion_dataframe(db, sp.id)
        sessions.append({**session_dict(db, s, su.name),
                         "skills": [{"skill": r["Skill"], "proficiency": r["Proficiency"]} for r in skills.to_dict("records")],
                         "progress": [{"topic": r["Topic"], "completion": r["Completion"], "status": r["Status"]}
                                      for r in prog.to_dict("records")]})
    return {"is_verified": mp.is_verified, "pending": pending, "sessions": sessions}


class RespondIn(BaseModel):
    accept: bool


@router.post("/mentor/requests/{request_id}/respond")
def respond(request_id: int, body: RespondIn, user: User = Depends(mentor_only), db=Depends(get_db)):
    mp = mentor_of(db, user)
    req = db.get(MentorRequest, request_id)
    if not req or req.mentor_id != mp.id:
        raise HTTPException(404, "Request not found.")
    if req.status != "pending":
        raise HTTPException(422, "This request was already answered.")
    respond_to_request(db, request_id, body.accept)
    return {"message": "Request accepted." if body.accept else "Request rejected."}


class FeedbackIn(BaseModel):
    feedback: str


@router.post("/mentor/sessions/{session_id}/feedback")
def feedback(session_id: int, body: FeedbackIn, user: User = Depends(mentor_only), db=Depends(get_db)):
    mp = mentor_of(db, user)
    s = db.get(MentorshipSession, session_id)
    req = db.get(MentorRequest, s.request_id) if s else None
    if not s or req.mentor_id != mp.id:
        raise HTTPException(404, "Session not found.")
    submit_feedback(db, s.id, feedback_text=body.feedback)
    return {"message": "Feedback saved and shared with the student."}
