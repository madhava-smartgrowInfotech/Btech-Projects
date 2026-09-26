"""
KnowledgeX AI - Analytics Service
====================================
Aggregates data from the database into pandas DataFrames ready for Plotly
charting across student progress, marketplace, mentorship, interviews,
coding practice and platform-wide admin analytics.
"""
import pandas as pd

from database.models import (
    StudentSkill, Skill, Resource, Purchase, Transaction, MockInterview,
    CodingSubmission, LearningProgress, LearningTopic, User, MentorshipSession,
    MentorRequest,
)


def student_skill_dataframe(session, student_id):
    rows = session.query(StudentSkill, Skill).join(Skill).filter(StudentSkill.student_id == student_id).all()
    data = [{"Skill": s.name, "Proficiency": ss.proficiency} for ss, s in rows]
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Skill", "Proficiency"])


def learning_completion_dataframe(session, student_id):
    rows = session.query(LearningProgress, LearningTopic).join(LearningTopic).filter(
        LearningProgress.student_id == student_id).all()
    data = [{"Topic": t.name, "Completion": p.completion_percent, "Status": p.status} for p, t in rows]
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Topic", "Completion", "Status"])


def interview_performance_dataframe(session, student_id):
    rows = session.query(MockInterview).filter_by(student_id=student_id).order_by(MockInterview.created_at).all()
    data = [{
        "Date": r.created_at.strftime("%Y-%m-%d %H:%M"), "Role": r.role,
        "Overall": r.overall_score, "Technical": r.technical_score,
        "Communication": r.communication_score, "Relevance": r.relevance_score,
    } for r in rows]
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Date", "Role", "Overall"])


def coding_performance_dataframe(session, student_id):
    rows = session.query(CodingSubmission).filter_by(student_id=student_id).order_by(
        CodingSubmission.submitted_at).all()
    data = [{
        "Date": r.submitted_at.strftime("%Y-%m-%d %H:%M"),
        "Passed": r.passed, "TestsPassed": r.tests_passed, "TestsTotal": r.tests_total,
    } for r in rows]
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Date", "Passed"])


def marketplace_earnings_dataframe(session, user_id):
    rows = session.query(Transaction).filter_by(user_id=user_id, type="sale").order_by(Transaction.created_at).all()
    data = [{"Date": r.created_at.strftime("%Y-%m-%d"), "Earnings": r.amount} for r in rows]
    return pd.DataFrame(data) if data else pd.DataFrame(columns=["Date", "Earnings"])


def platform_overview(session):
    """Admin-level system-wide analytics."""
    total_students = session.query(User).filter_by(role="student").count()
    total_mentors = session.query(User).filter_by(role="mentor").count()
    total_resources = session.query(Resource).count()
    total_purchases = session.query(Purchase).count()
    total_sessions = session.query(MentorshipSession).count()
    total_interviews = session.query(MockInterview).count()
    total_submissions = session.query(CodingSubmission).count()
    revenue = sum(t.price_paid for t in session.query(Purchase).all())
    return {
        "total_students": total_students,
        "total_mentors": total_mentors,
        "total_resources": total_resources,
        "total_purchases": total_purchases,
        "total_sessions": total_sessions,
        "total_interviews": total_interviews,
        "total_submissions": total_submissions,
        "gross_marketplace_volume": round(revenue, 2),
    }
