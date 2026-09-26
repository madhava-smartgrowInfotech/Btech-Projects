"""
KnowledgeX AI - Gamification Service
========================================
Handles XP awarding, level progression, badges/achievements, daily streaks
and the platform leaderboard.
"""
from datetime import datetime, date, timedelta

from database.models import UserPoints, Achievement, User

LEVEL_THRESHOLDS = [
    (2500, "Knowledge Engineer"),
    (1000, "Skilled"),
    (500, "Learner"),
    (100, "Beginner"),
    (0, "Newcomer"),
]

XP_RULES = {
    "assessment_completed": 20,
    "topic_completed": 30,
    "resource_uploaded": 25,
    "resource_purchased": 5,
    "mentorship_session_completed": 40,
    "mock_interview_completed": 35,
    "coding_problem_solved": 25,
    "profile_completed": 15,
}


def _get_or_create_points(session, user_id):
    points = session.query(UserPoints).filter_by(user_id=user_id).first()
    if not points:
        points = UserPoints(user_id=user_id, xp=0, level="Newcomer")
        session.add(points)
        session.flush()
    return points


def award_xp(session, user_id, action_key, badge_on_award=None):
    """Award XP for an action, update level & streak, optionally grant a badge."""
    xp_gain = XP_RULES.get(action_key, 10)
    points = _get_or_create_points(session, user_id)
    points.xp += xp_gain

    for threshold, level_name in LEVEL_THRESHOLDS:
        if points.xp >= threshold:
            points.level = level_name
            break

    today_str = date.today().isoformat()
    if points.last_activity_date:
        last = date.fromisoformat(points.last_activity_date)
        if last == date.today() - timedelta(days=1):
            points.streak_days += 1
        elif last != date.today():
            points.streak_days = 1
    else:
        points.streak_days = 1
    points.last_activity_date = today_str

    if badge_on_award:
        grant_badge(session, user_id, badge_on_award)

    session.flush()
    return points, xp_gain


def grant_badge(session, user_id, badge_name, description=""):
    existing = session.query(Achievement).filter_by(user_id=user_id, badge_name=badge_name).first()
    if existing:
        return None
    badge = Achievement(user_id=user_id, badge_name=badge_name, description=description)
    session.add(badge)
    session.flush()
    return badge


def get_leaderboard(session, limit=10):
    rows = session.query(UserPoints, User).join(User).filter(User.role == "student").order_by(
        UserPoints.xp.desc()).limit(limit).all()
    return [{"name": u.name, "xp": p.xp, "level": p.level, "streak": p.streak_days} for p, u in rows]


def get_user_badges(session, user_id):
    return session.query(Achievement).filter_by(user_id=user_id).order_by(Achievement.earned_at.desc()).all()


def get_user_points(session, user_id):
    return _get_or_create_points(session, user_id)
