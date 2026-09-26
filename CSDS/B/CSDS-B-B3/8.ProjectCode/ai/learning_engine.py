"""
KnowledgeX AI - Personalized Learning Engine
================================================
Orchestrates the AI recommendation pipeline described in the spec:
Student Data -> Profile Analysis -> Skill Assessment -> Knowledge-State
Tracking -> Knowledge Graph -> Weak Skill Detection -> Career Goal Analysis
-> Recommendation Engine -> Personalized Roadmap -> Resources/Mentors/Projects
-> Progress Tracking -> Continuous Recommendation Update.

Runs fully locally (rule-based + graph algorithms) via the AI abstraction
layer in ai/recommendation_engine.py -- no external API required.
"""
from database.models import StudentProfile, LearningRoadmap
from graph.knowledge_graph import classify_topics, get_weak_prerequisites
from graph.roadmap_generator import generate_roadmap
import json
from datetime import datetime


def analyze_and_generate_roadmap(session, student_id, persist=True):
    """Full pipeline: analyze current knowledge state and produce a roadmap."""
    student = session.query(StudentProfile).get(student_id)
    if not student:
        return None

    weak_topics = get_weak_prerequisites(session, student_id)
    roadmap_steps = generate_roadmap(session, student_id, career_goal=student.career_goal)

    result = {
        "career_goal": student.career_goal or "Not set",
        "weak_prerequisites": weak_topics,
        "roadmap": roadmap_steps,
        "generated_at": datetime.utcnow().isoformat(),
    }

    if persist:
        record = LearningRoadmap(
            student_id=student_id,
            career_goal=student.career_goal or "General",
            roadmap_json=json.dumps(roadmap_steps),
        )
        session.add(record)
        session.flush()

    return result


def get_latest_saved_roadmap(session, student_id):
    record = session.query(LearningRoadmap).filter_by(student_id=student_id).order_by(
        LearningRoadmap.generated_at.desc()).first()
    if not record:
        return None
    return json.loads(record.roadmap_json)


def update_topic_progress(session, student_id, topic_id, completion_percent):
    """Update a student's completion on a topic and refresh status."""
    from database.models import LearningProgress
    progress = session.query(LearningProgress).filter_by(
        student_id=student_id, topic_id=topic_id).first()
    if not progress:
        progress = LearningProgress(student_id=student_id, topic_id=topic_id, completion_percent=0)
        session.add(progress)

    progress.completion_percent = min(100, max(0, completion_percent))
    if progress.completion_percent >= 85:
        progress.status = "completed"
    elif progress.completion_percent > 0:
        progress.status = "in_progress"
    else:
        progress.status = "not_started"
    progress.updated_at = datetime.utcnow()
    session.flush()
    return progress


def get_topic_overview(session, student_id):
    """Returns the classified knowledge-graph state for dashboard summaries."""
    classification = classify_topics(session, student_id)
    completed = sum(1 for v in classification.values() if v["status"] == "completed")
    strong = sum(1 for v in classification.values() if v["status"] == "strong")
    weak = sum(1 for v in classification.values() if v["status"] == "weak")
    locked = sum(1 for v in classification.values() if v["status"] == "locked")
    recommended = sum(1 for v in classification.values() if v["status"] == "recommended")
    return {
        "classification": classification,
        "counts": {
            "completed": completed, "strong": strong, "weak": weak,
            "locked": locked, "recommended": recommended, "total": len(classification),
        }
    }
