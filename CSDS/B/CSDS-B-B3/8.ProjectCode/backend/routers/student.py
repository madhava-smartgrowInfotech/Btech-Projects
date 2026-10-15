"""Student-facing screens: dashboard, learning, knowledge graph, career, progress, profile."""
import json
from typing import Dict, Optional

import networkx as nx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_db, current_user, require, student_of, mentor_of, iso
from database.models import (
    User, StudentProfile, Assessment, AssessmentQuestion, AssessmentResult, StudentSkill, Skill,
    LearningTopic, LearningRoadmap, CareerRole, Purchase,
)
from ai.learning_engine import analyze_and_generate_roadmap, update_topic_progress, get_topic_overview
from ai.career_engine import recommend_careers
from graph.knowledge_graph import build_topic_graph, classify_topics
from services.gamification_service import award_xp, grant_badge, get_user_points, get_user_badges, get_leaderboard
from services.marketplace_service import get_seller_dashboard
from services.mentorship_service import get_sessions_for_student
from services.analytics_service import (
    student_skill_dataframe, learning_completion_dataframe, interview_performance_dataframe,
    coding_performance_dataframe, marketplace_earnings_dataframe,
)

router = APIRouter(tags=["student"])
student_only = require("student")


def points_dict(p):
    return {"xp": p.xp, "level": p.level, "streak_days": p.streak_days}


def badges_list(db, user_id):
    return [{"badge_name": b.badge_name, "description": b.description, "earned_at": iso(b.earned_at)}
            for b in get_user_badges(db, user_id)]


# ---------------------------------------------------------------- dashboard
@router.get("/student/dashboard")
def dashboard(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    overview = get_topic_overview(db, sp.id)
    seller = get_seller_dashboard(db, user.id)
    sessions = get_sessions_for_student(db, sp.id)
    upcoming = [s for s in sessions if s.status == "scheduled"]
    latest = db.query(LearningRoadmap).filter_by(student_id=sp.id).order_by(LearningRoadmap.generated_at.desc()).first()
    return {
        "name": user.name,
        "profile": {"branch": sp.branch, "year": sp.year, "career_goal": sp.career_goal,
                    "wallet_balance": sp.wallet_balance},
        "points": points_dict(get_user_points(db, user.id)),
        "counts": overview["counts"],
        "active_mentors": len({s.request_id for s in upcoming}),
        "roadmap": json.loads(latest.roadmap_json)[:5] if latest else [],
        "badges": badges_list(db, user.id),
        "marketplace": {"uploads": len(seller["resources"]), "total_earnings": seller["total_earnings"],
                        "purchases": db.query(Purchase).filter_by(buyer_id=user.id).count()},
        "leaderboard": get_leaderboard(db, limit=5),
    }


@router.get("/gamification/leaderboard")
def leaderboard(limit: int = 10, user: User = Depends(current_user), db=Depends(get_db)):
    return get_leaderboard(db, limit=min(max(limit, 1), 50))


# ---------------------------------------------------------------- learning
@router.get("/learning/assessments")
def assessments(user: User = Depends(student_only), db=Depends(get_db)):
    out = []
    for a in db.query(Assessment).all():
        n = db.query(AssessmentQuestion).filter_by(assessment_id=a.id).count()
        out.append({"id": a.id, "topic": a.topic, "title": a.title, "description": a.description, "question_count": n})
    return out


@router.get("/learning/assessments/{assessment_id}")
def assessment_detail(assessment_id: int, user: User = Depends(student_only), db=Depends(get_db)):
    a = db.get(Assessment, assessment_id)
    if not a:
        raise HTTPException(404, "Assessment not found.")
    qs = db.query(AssessmentQuestion).filter_by(assessment_id=a.id).all()
    return {
        "id": a.id, "topic": a.topic, "title": a.title,
        "questions": [{"id": q.id, "question": q.question,
                       "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}} for q in qs],
    }


class AssessmentIn(BaseModel):
    answers: Dict[str, str]


@router.post("/learning/assessments/{assessment_id}/submit")
def submit_assessment(assessment_id: int, body: AssessmentIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    a = db.get(Assessment, assessment_id)
    if not a:
        raise HTTPException(404, "Assessment not found.")
    questions = db.query(AssessmentQuestion).filter_by(assessment_id=a.id).all()
    if any(str(q.id) not in body.answers for q in questions):
        raise HTTPException(422, "Please answer all questions before submitting.")
    correct = sum(1 for q in questions if body.answers[str(q.id)] == q.correct_option)
    score = round((correct / len(questions)) * 100, 1)
    db.add(AssessmentResult(student_id=sp.id, assessment_id=a.id, topic=a.topic, score_percent=score))

    skill = db.query(Skill).filter_by(name=a.topic).first()
    if skill:
        ss = db.query(StudentSkill).filter_by(student_id=sp.id, skill_id=skill.id).first()
        if not ss:
            db.add(StudentSkill(student_id=sp.id, skill_id=skill.id, proficiency=score))
        else:
            ss.proficiency = round((ss.proficiency + score) / 2, 1)  # blended update, as in the Streamlit page
    topic = db.query(LearningTopic).filter_by(name=a.topic).first()
    if topic:
        update_topic_progress(db, sp.id, topic.id, score)

    _, xp = award_xp(db, user.id, "assessment_completed")
    badge = None
    if score >= 80:
        badge = f"{a.topic} Master"
        grant_badge(db, user.id, badge, f"Scored {score}% in {a.topic}")
    return {"topic": a.topic, "score": score, "correct": correct, "total": len(questions),
            "xp_gained": xp, "badge": badge,
            "results": [{"question_id": q.id, "chosen": body.answers[str(q.id)], "correct": q.correct_option}
                        for q in questions]}


@router.get("/learning/roadmap")
def saved_roadmap(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    rec = db.query(LearningRoadmap).filter_by(student_id=sp.id).order_by(LearningRoadmap.generated_at.desc()).first()
    return {
        "career_goal": sp.career_goal,
        "roadmap": json.loads(rec.roadmap_json) if rec else None,
        "generated_at": iso(rec.generated_at) if rec else None,
        "careers": [c.title for c in db.query(CareerRole).all()],
    }


class RoadmapIn(BaseModel):
    career_goal: str


@router.post("/learning/roadmap")
def generate_roadmap_route(body: RoadmapIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    goal = body.career_goal.strip()
    if not goal:
        raise HTTPException(422, "Enter a career goal first.")
    sp.career_goal = goal
    return analyze_and_generate_roadmap(db, sp.id)


@router.get("/learning/topics")
def topics(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    cls = classify_topics(db, sp.id)
    return [{"id": tid, "name": v["name"], "difficulty": v["difficulty"], "proficiency": v["proficiency"],
             "status": v["status"]} for tid, v in sorted(cls.items(), key=lambda kv: kv[1]["name"])]


class ProgressIn(BaseModel):
    topic_id: int
    completion_percent: float


@router.post("/learning/progress")
def set_progress(body: ProgressIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    topic = db.get(LearningTopic, body.topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found.")
    p = update_topic_progress(db, sp.id, topic.id, body.completion_percent)
    badge = None
    if body.completion_percent >= 85:
        award_xp(db, user.id, "topic_completed")
        badge = f"{topic.name} Completed"
        grant_badge(db, user.id, badge)
    return {"topic": topic.name, "completion_percent": p.completion_percent, "status": p.status, "badge": badge}


# ---------------------------------------------------------------- knowledge graph
@router.get("/graph")
def graph(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    g = build_topic_graph(db)
    cls = classify_topics(db, sp.id)
    if len(g.nodes) == 0:
        return {"nodes": [], "edges": [], "counts": {}}
    layout = nx.spring_layout(g, seed=42, k=0.9)
    nodes = []
    for nid in g.nodes():
        info = cls[nid]
        nodes.append({"id": nid, "name": info["name"], "status": info["status"],
                      "proficiency": float(info["proficiency"]), "difficulty": info["difficulty"],
                      "description": info["description"], "estimated_hours": info["estimated_hours"],
                      "prerequisites": info["prerequisites"], "next_topics": info["next_topics"],
                      "x": float(layout[nid][0]), "y": float(layout[nid][1])})
    counts = {}
    for n in nodes:
        counts[n["status"]] = counts.get(n["status"], 0) + 1
    return {"nodes": nodes, "edges": [{"source": u, "target": v} for u, v in g.edges()], "counts": counts}


# ---------------------------------------------------------------- career
@router.get("/career/recommendations")
def careers(top_n: int = 8, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    return {"career_goal": sp.career_goal, "recommendations": recommend_careers(db, sp.id, top_n=min(max(top_n, 1), 20))}


class GoalIn(BaseModel):
    title: str


@router.post("/career/goal")
def set_goal(body: GoalIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    if not db.query(CareerRole).filter_by(title=body.title).first():
        raise HTTPException(404, "Unknown career role.")
    sp.career_goal = body.title
    return {"career_goal": sp.career_goal}


# ---------------------------------------------------------------- progress analytics
def _records(df):
    return json.loads(df.to_json(orient="records"))


@router.get("/progress/analytics")
def analytics(user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    counts = get_topic_overview(db, sp.id)["counts"]
    coding = coding_performance_dataframe(db, sp.id)
    passed = int(coding["Passed"].sum()) if len(coding) else 0
    return {
        "counts": counts,
        "skills": _records(student_skill_dataframe(db, sp.id)),
        "completion": _records(learning_completion_dataframe(db, sp.id)),
        "interviews": _records(interview_performance_dataframe(db, sp.id)),
        "coding": {"total": len(coding), "passed": passed, "failed": len(coding) - passed},
        "earnings": _records(marketplace_earnings_dataframe(db, user.id)),
    }


# ---------------------------------------------------------------- profile (student + mentor)
@router.get("/profile")
def get_profile(user: User = Depends(current_user), db=Depends(get_db)):
    base = {"role": user.role, "name": user.name, "email": user.email}
    if user.role == "student":
        sp = student_of(db, user)
        mine = {ss.skill_id: ss.proficiency for ss in db.query(StudentSkill).filter_by(student_id=sp.id).all()}
        return {**base,
                "profile": {"branch": sp.branch, "year": sp.year, "college": sp.college, "bio": sp.bio,
                            "interests": sp.interests, "career_goal": sp.career_goal,
                            "wallet_balance": sp.wallet_balance},
                "careers": [c.title for c in db.query(CareerRole).all()],
                "skills": [{"skill_id": s.id, "name": s.name, "category": s.category,
                            "proficiency": mine.get(s.id, 0)} for s in db.query(Skill).all()],
                "points": points_dict(get_user_points(db, user.id)),
                "badges": badges_list(db, user.id)}
    if user.role == "mentor":
        mp = mentor_of(db, user)
        return {**base,
                "profile": {"expertise": mp.expertise, "domain": mp.domain, "experience_years": mp.experience_years,
                            "bio": mp.bio, "availability": mp.availability, "is_verified": mp.is_verified,
                            "rating": mp.rating, "rating_count": mp.rating_count}}
    raise HTTPException(404, "Admin accounts don't have a learner or mentor profile.")


class ProfileIn(BaseModel):
    branch: Optional[str] = None
    year: Optional[str] = None
    college: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[str] = None
    career_goal: Optional[str] = None
    expertise: Optional[str] = None
    domain: Optional[str] = None
    experience_years: Optional[float] = None
    availability: Optional[str] = None


@router.put("/profile")
def put_profile(body: ProfileIn, user: User = Depends(current_user), db=Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    if user.role == "student":
        sp = student_of(db, user)
        for k in ("branch", "year", "college", "bio", "interests", "career_goal"):
            if k in data:
                setattr(sp, k, data[k])
        award_xp(db, user.id, "profile_completed")
    elif user.role == "mentor":
        mp = mentor_of(db, user)
        for k in ("expertise", "domain", "experience_years", "bio", "availability"):
            if k in data:
                setattr(mp, k, data[k])
    else:
        raise HTTPException(403, "Admin accounts don't have a profile to edit.")
    return {"message": "Profile updated."}


class SkillsIn(BaseModel):
    skills: Dict[str, float]


@router.put("/profile/skills")
def put_skills(body: SkillsIn, user: User = Depends(student_only), db=Depends(get_db)):
    sp = student_of(db, user)
    mine = {ss.skill_id: ss for ss in db.query(StudentSkill).filter_by(student_id=sp.id).all()}
    valid = {s.id for s in db.query(Skill).all()}
    for sid, val in body.skills.items():
        sid = int(sid)
        val = max(0.0, min(100.0, val))
        if sid not in valid:
            continue
        if sid in mine:
            mine[sid].proficiency = val
        elif val > 0:
            db.add(StudentSkill(student_id=sp.id, skill_id=sid, proficiency=val))
    return {"message": "Skills updated."}
