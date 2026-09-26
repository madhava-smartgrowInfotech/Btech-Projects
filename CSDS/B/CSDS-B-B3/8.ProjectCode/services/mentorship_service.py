"""
KnowledgeX AI - Mentorship Service
=====================================
Handles sending/accepting/rejecting mentorship requests, scheduling sessions,
and recording feedback/ratings.
"""
from database.models import MentorRequest, MentorshipSession, MentorProfile, User


def send_request(session, student_id, mentor_id, message):
    existing = session.query(MentorRequest).filter_by(
        student_id=student_id, mentor_id=mentor_id, status="pending").first()
    if existing:
        return None, "You already have a pending request with this mentor."
    req = MentorRequest(student_id=student_id, mentor_id=mentor_id, message=message, status="pending")
    session.add(req)
    session.flush()
    return req, ""


def respond_to_request(session, request_id, accept: bool):
    req = session.query(MentorRequest).get(request_id)
    if not req:
        return False, "Request not found."
    req.status = "accepted" if accept else "rejected"
    session.flush()
    if accept:
        session.add(MentorshipSession(
            request_id=req.id, topic="Introductory Session", status="scheduled",
            scheduled_time="To be scheduled",
        ))
        session.flush()
    return True, "Request updated."


def get_requests_for_mentor(session, mentor_id, status=None):
    q = session.query(MentorRequest).filter_by(mentor_id=mentor_id)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(MentorRequest.created_at.desc()).all()


def get_requests_for_student(session, student_id):
    return session.query(MentorRequest).filter_by(student_id=student_id).order_by(
        MentorRequest.created_at.desc()).all()


def get_sessions_for_mentor(session, mentor_id):
    return session.query(MentorshipSession).join(MentorRequest).filter(
        MentorRequest.mentor_id == mentor_id).all()


def get_sessions_for_student(session, student_id):
    return session.query(MentorshipSession).join(MentorRequest).filter(
        MentorRequest.student_id == student_id).all()


def submit_feedback(session, session_id, feedback_text=None, rating=None):
    s = session.query(MentorshipSession).get(session_id)
    if not s:
        return False
    if feedback_text is not None:
        s.mentor_feedback = feedback_text
    if rating is not None:
        s.student_rating = rating
        s.status = "completed"
        # Update mentor's aggregate rating
        req = session.query(MentorRequest).get(s.request_id)
        mentor = session.query(MentorProfile).get(req.mentor_id)
        total = mentor.rating * mentor.rating_count + rating
        mentor.rating_count += 1
        mentor.rating = round(total / mentor.rating_count, 2)
    session.flush()
    return True
