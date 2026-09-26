"""
KnowledgeX AI - Database Seeder
=================================
Populates the database with demo accounts, skills, careers, learning topics
(knowledge graph), assessments, interview & coding questions and sample
marketplace resources so the app is usable immediately after installation.
"""
import json
import os
import random
from datetime import datetime, timedelta

from database.database import get_session, init_db
from database.models import (
    User, StudentProfile, MentorProfile, Skill, StudentSkill, CareerRole,
    LearningTopic, TopicPrerequisite, Assessment, AssessmentQuestion,
    AssessmentResult, LearningProgress, Resource, InterviewQuestion,
    CodingProblem, UserPoints, Achievement, MentorRequest, MentorshipSession,
)
from services.authentication import hash_password

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Demo@1234")


def _load(fname):
    with open(os.path.join(DATA_DIR, fname), "r", encoding="utf-8") as f:
        return json.load(f)


def is_seeded(session) -> bool:
    return session.query(User).count() > 0


def seed_all(force=False):
    init_db()
    session = get_session()
    try:
        if is_seeded(session) and not force:
            return False

        _seed_skills(session)
        _seed_careers(session)
        _seed_topics_and_prereqs(session)
        _seed_assessments(session)
        _seed_interview_questions(session)
        _seed_coding_problems(session)
        _seed_users(session)
        _seed_resources(session)
        _seed_sample_mentorship_and_progress(session)
        session.commit()
        return True
    finally:
        session.close()


def _seed_skills(session):
    for s in _load("skills.json"):
        session.add(Skill(name=s["name"], category=s["category"]))
    session.flush()


def _seed_careers(session):
    for c in _load("careers.json"):
        session.add(CareerRole(**c))
    session.flush()


def _seed_topics_and_prereqs(session):
    data = _load("learning_topics.json")
    name_to_id = {}
    for t in data["topics"]:
        topic = LearningTopic(**t)
        session.add(topic)
        session.flush()
        name_to_id[t["name"]] = topic.id

    for p in data["prerequisites"]:
        session.add(TopicPrerequisite(
            topic_id=name_to_id[p["topic"]],
            prerequisite_id=name_to_id[p["prerequisite"]],
        ))
    session.flush()


def _seed_assessments(session):
    data = _load("sample_questions.json")["assessment_questions"]
    for topic, questions in data.items():
        assessment = Assessment(
            topic=topic,
            title=f"{topic} Skill Assessment",
            description=f"A short quiz to evaluate your proficiency in {topic}.",
        )
        session.add(assessment)
        session.flush()
        for q in questions:
            session.add(AssessmentQuestion(
                assessment_id=assessment.id,
                question=q["question"],
                option_a=q["options"]["A"],
                option_b=q["options"]["B"],
                option_c=q["options"]["C"],
                option_d=q["options"]["D"],
                correct_option=q["correct"],
            ))
    session.flush()


def _seed_interview_questions(session):
    for q in _load("sample_questions.json")["interview_questions"]:
        session.add(InterviewQuestion(
            role=q["role"], interview_type=q["type"], difficulty=q["difficulty"],
            question=q["question"], keywords=q["keywords"],
        ))
    session.flush()


def _seed_coding_problems(session):
    for p in _load("sample_questions.json")["coding_problems"]:
        session.add(CodingProblem(
            title=p["title"], description=p["description"], difficulty=p["difficulty"],
            concept_tag=p["concept_tag"], starter_code=p["starter_code"],
            function_name=p["function_name"], test_cases=json.dumps(p["test_cases"]),
        ))
    session.flush()


def _create_user(session, name, email, role, password=None):
    user = User(
        name=name, email=email, role=role,
        password_hash=hash_password(password or DEMO_PASSWORD),
        is_active=True, is_verified=(role != "mentor"),
    )
    session.add(user)
    session.flush()
    session.add(UserPoints(user_id=user.id, xp=0, level="Beginner"))
    return user


def _seed_users(session):
    # --- Demo accounts required by spec ---
    student_user = _create_user(session, "Aarav Sharma", "student@example.com", "student")
    sp = StudentProfile(
        user_id=student_user.id, branch="Computer Science", year="3rd Year",
        college="KnowledgeX Institute of Technology",
        bio="Aspiring Machine Learning Engineer passionate about AI.",
        interests="Machine Learning, Python, Data Science",
        career_goal="Machine Learning Engineer", wallet_balance=500.0,
    )
    session.add(sp)
    session.flush()

    demo_scores = {
        "Python": 80, "Data Structures": 60, "Algorithms": 40, "Statistics": 45,
        "Machine Learning": 25, "SQL": 55, "NumPy": 65, "Pandas": 50,
        "Programming Fundamentals": 90, "Database": 50,
    }
    skills = {s.name: s for s in session.query(Skill).all()}
    for skill_name, prof in demo_scores.items():
        if skill_name in skills:
            session.add(StudentSkill(student_id=sp.id, skill_id=skills[skill_name].id, proficiency=prof))

    mentor_user = _create_user(session, "Priya Verma", "mentor@example.com", "mentor")
    mp = MentorProfile(
        user_id=mentor_user.id, expertise="Machine Learning, Python, Data Science",
        domain="Artificial Intelligence", experience_years=3,
        bio="Senior Data Scientist mentoring students in ML and career growth.",
        availability="Weekdays 6-8 PM, Weekends flexible", rating=4.8, rating_count=24,
        is_verified=True, hourly_rate=0,
    )
    session.add(mp)

    admin_user = _create_user(session, "System Admin", "admin@example.com", "admin")

    # --- Additional sample students & mentors for realism ---
    sample_students = [
        ("Rohan Gupta", "rohan.g@example.com", "Electronics", "2nd Year", "Data Scientist"),
        ("Sneha Iyer", "sneha.i@example.com", "Computer Science", "4th Year", "AI Engineer"),
        ("Karan Mehta", "karan.m@example.com", "IT", "3rd Year", "Software Developer"),
    ]
    for name, email, branch, year, goal in sample_students:
        u = _create_user(session, name, email, "student")
        session.add(StudentProfile(
            user_id=u.id, branch=branch, year=year, college="KnowledgeX Institute of Technology",
            interests=goal, career_goal=goal, wallet_balance=300.0,
        ))

    sample_mentors = [
        ("Arjun Nair", "arjun.n@example.com", "Deep Learning, Computer Vision, Python", "AI Research", 4.0, 4.7),
        ("Meera Rao", "meera.r@example.com", "SQL, Data Analysis, Statistics", "Data Analytics", 5.0, 4.6),
        ("Vikram Singh", "vikram.s@example.com", "Cloud, System Design, Java", "Cloud Engineering", 6.0, 4.9),
    ]
    for name, email, expertise, domain, exp, rating in sample_mentors:
        u = _create_user(session, name, email, "mentor")
        session.add(MentorProfile(
            user_id=u.id, expertise=expertise, domain=domain, experience_years=exp,
            bio=f"Experienced professional in {domain}.", rating=rating, rating_count=random.randint(5, 40),
            is_verified=True,
        ))
    session.flush()


def _seed_resources(session):
    student = session.query(User).filter_by(email="student@example.com").first()
    mentor = session.query(User).filter_by(email="mentor@example.com").first()
    resources = [
        ("Python Basics Cheat Sheet", "Quick-reference cheat sheet covering Python syntax and built-ins.",
         "Cheat Sheets", "Cheat Sheet", 0, "Python", student.id),
        ("Data Structures Complete Notes", "Comprehensive handwritten notes covering arrays to graphs.",
         "Notes", "Notes", 49, "Data Structures", student.id),
        ("Machine Learning Project: House Price Prediction", "End-to-end regression project with code and report.",
         "Projects", "Project Report", 99, "Machine Learning,Python", mentor.id),
        ("SQL Interview Question Bank", "150+ SQL interview questions with solutions.",
         "Interview Prep", "Interview Preparation Material", 49, "SQL", mentor.id),
        ("Complete ML Foundations Course", "Video + text course covering ML from scratch to deployment.",
         "Courses", "Course", 299, "Machine Learning,Statistics", mentor.id),
        ("Coding Templates Pack: DSA", "Ready-to-use Python templates for common DSA patterns.",
         "Coding Templates", "Coding Template", 79, "Data Structures,Algorithms", student.id),
        ("Free Statistics Primer", "Beginner friendly introduction to statistics for data science.",
         "Notes", "Notes", 0, "Statistics", mentor.id),
        ("Mini Project: Student Grade Predictor", "A small ML mini-project ideal for beginners.",
         "Projects", "Mini Project", 0, "Machine Learning,Python", student.id),
        ("Practice Questions: Python OOP", "50 practice questions on Python OOP concepts.",
         "Practice Questions", "Practice Questions", 29, "Python", student.id),
    ]
    for title, desc, category, rtype, price, tags, author_id in resources:
        session.add(Resource(
            title=title, description=desc, category=category, resource_type=rtype,
            author_id=author_id, price=price, rating=round(random.uniform(3.8, 5.0), 1),
            rating_count=random.randint(3, 80), downloads=random.randint(10, 500),
            skill_tags=tags, is_approved=True,
        ))
    session.flush()


def _seed_sample_mentorship_and_progress(session):
    sp = session.query(StudentProfile).join(User).filter(User.email == "student@example.com").first()
    mp = session.query(MentorProfile).join(User).filter(User.email == "mentor@example.com").first()

    req = MentorRequest(student_id=sp.id, mentor_id=mp.id, message="I need help with Machine Learning fundamentals.",
                         status="accepted")
    session.add(req)
    session.flush()
    session.add(MentorshipSession(
        request_id=req.id, scheduled_time=(datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        topic="Machine Learning Fundamentals", status="scheduled",
    ))

    # Mark a couple of topics as completed / in-progress for demo realism
    topics = {t.name: t for t in session.query(LearningTopic).all()}
    progress_seed = {
        "Programming Fundamentals": ("completed", 100),
        "Python": ("completed", 100),
        "Data Structures": ("in_progress", 60),
        "Algorithms": ("in_progress", 40),
        "Statistics": ("in_progress", 45),
    }
    for name, (status, pct) in progress_seed.items():
        if name in topics:
            session.add(LearningProgress(student_id=sp.id, topic_id=topics[name].id,
                                          completion_percent=pct, status=status))
    session.flush()
