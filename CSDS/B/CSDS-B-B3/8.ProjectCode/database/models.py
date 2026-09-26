"""
KnowledgeX AI - Database Models
=================================
SQLAlchemy ORM models for the whole ecosystem. Uses SQLite for the prototype,
but the engine is created from a DATABASE_URL so swapping to Postgres/MySQL
later requires no model changes.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ---------------------------------------------------------------------------
# Users & Profiles
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")  # student, mentor, admin
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    mentor_profile = relationship("MentorProfile", back_populates="user", uselist=False)
    points = relationship("UserPoints", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    branch = Column(String(100), default="")
    year = Column(String(20), default="")
    college = Column(String(150), default="")
    bio = Column(Text, default="")
    interests = Column(Text, default="")          # comma separated
    career_goal = Column(String(100), default="")  # target career_roles.title
    avatar_seed = Column(String(50), default="student")
    wallet_balance = Column(Float, default=500.0)  # simulated currency for demo

    user = relationship("User", back_populates="student_profile")
    skills = relationship("StudentSkill", back_populates="student")
    assessment_results = relationship("AssessmentResult", back_populates="student")
    progress = relationship("LearningProgress", back_populates="student")
    roadmaps = relationship("LearningRoadmap", back_populates="student")


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    expertise = Column(Text, default="")       # comma separated skills
    domain = Column(String(150), default="")
    experience_years = Column(Float, default=0)
    bio = Column(Text, default="")
    availability = Column(String(255), default="Weekdays 6-8 PM")
    rating = Column(Float, default=4.5)
    rating_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    hourly_rate = Column(Float, default=0.0)
    wallet_balance = Column(Float, default=200.0)  # simulated currency, so mentors can also use the marketplace

    user = relationship("User", back_populates="mentor_profile")


# ---------------------------------------------------------------------------
# Skills / Careers / Learning Topics (Knowledge Graph)
# ---------------------------------------------------------------------------
class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    category = Column(String(100), default="General")


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    proficiency = Column(Float, default=0.0)  # 0-100
    updated_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="skills")
    skill = relationship("Skill")


class CareerRole(Base):
    __tablename__ = "career_roles"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), unique=True)
    description = Column(Text, default="")
    required_skills = Column(Text, default="")  # comma separated skill names
    avg_salary_lpa = Column(String(50), default="")
    suggested_certifications = Column(Text, default="")
    interview_topics = Column(Text, default="")


class LearningTopic(Base):
    __tablename__ = "learning_topics"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(Text, default="")
    difficulty = Column(String(20), default="Beginner")  # Beginner/Intermediate/Advanced
    estimated_hours = Column(Float, default=10)
    related_skill = Column(String(100), default="")


class TopicPrerequisite(Base):
    """Directed edge: prerequisite_id -> topic_id (prerequisite must be learned first)."""
    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("learning_topics.id"))
    prerequisite_id = Column(Integer, ForeignKey("learning_topics.id"))


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------
class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    topic = Column(String(100))
    title = Column(String(150))
    description = Column(Text, default="")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    question = Column(Text)
    option_a = Column(String(255))
    option_b = Column(String(255))
    option_c = Column(String(255))
    option_d = Column(String(255))
    correct_option = Column(String(1))  # A/B/C/D
    difficulty = Column(String(20), default="Medium")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    topic = Column(String(100))
    score_percent = Column(Float)
    taken_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="assessment_results")


# ---------------------------------------------------------------------------
# Learning Progress & Roadmaps
# ---------------------------------------------------------------------------
class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    topic_id = Column(Integer, ForeignKey("learning_topics.id"))
    completion_percent = Column(Float, default=0.0)
    status = Column(String(20), default="not_started")  # not_started/in_progress/completed
    updated_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="progress")
    topic = relationship("LearningTopic")


class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    career_goal = Column(String(120))
    generated_at = Column(DateTime, default=datetime.utcnow)
    roadmap_json = Column(Text)  # JSON-serialized ordered list of steps

    student = relationship("StudentProfile", back_populates="roadmaps")


# ---------------------------------------------------------------------------
# Marketplace
# ---------------------------------------------------------------------------
class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    description = Column(Text, default="")
    category = Column(String(100), default="Notes")
    resource_type = Column(String(50), default="Notes")
    author_id = Column(Integer, ForeignKey("users.id"))
    price = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    skill_tags = Column(Text, default="")
    file_path = Column(String(255), default="")
    is_approved = Column(Boolean, default=True)
    is_reported = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"))
    price_paid = Column(Float, default=0.0)
    purchased_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(String(30))  # purchase, sale, refund, topup
    description = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Mentorship
# ---------------------------------------------------------------------------
class MentorRequest(Base):
    __tablename__ = "mentor_requests"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    mentor_id = Column(Integer, ForeignKey("mentor_profiles.id"))
    message = Column(Text, default="")
    status = Column(String(20), default="pending")  # pending/accepted/rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("mentor_requests.id"))
    scheduled_time = Column(String(100), default="")
    topic = Column(String(150), default="")
    status = Column(String(20), default="scheduled")  # scheduled/completed/cancelled
    mentor_feedback = Column(Text, default="")
    student_rating = Column(Float, default=0.0)


# ---------------------------------------------------------------------------
# Mock Interviews
# ---------------------------------------------------------------------------
class MockInterview(Base):
    __tablename__ = "mock_interviews"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    role = Column(String(120))
    interview_type = Column(String(30))
    difficulty = Column(String(20))
    overall_score = Column(Float, default=0.0)
    technical_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True)
    role = Column(String(120))
    interview_type = Column(String(30))
    difficulty = Column(String(20))
    question = Column(Text)
    keywords = Column(Text, default="")  # comma separated ideal keywords for scoring


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("mock_interviews.id"))
    question_id = Column(Integer, ForeignKey("interview_questions.id"))
    answer_text = Column(Text, default="")
    score = Column(Float, default=0.0)


class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("mock_interviews.id"))
    strengths = Column(Text, default="")
    weaknesses = Column(Text, default="")
    suggested_topics = Column(Text, default="")
    summary = Column(Text, default="")


# ---------------------------------------------------------------------------
# Coding Practice
# ---------------------------------------------------------------------------
class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True)
    title = Column(String(150))
    description = Column(Text)
    difficulty = Column(String(20), default="Easy")
    concept_tag = Column(String(100), default="")
    starter_code = Column(Text, default="def solve():\n    pass\n")
    test_cases = Column(Text, default="[]")  # JSON list of {"input":..., "expected":...}
    function_name = Column(String(100), default="solve")


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    problem_id = Column(Integer, ForeignKey("coding_problems.id"))
    code = Column(Text)
    passed = Column(Boolean, default=False)
    tests_passed = Column(Integer, default=0)
    tests_total = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Gamification
# ---------------------------------------------------------------------------
class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_name = Column(String(120))
    description = Column(String(255), default="")
    earned_at = Column(DateTime, default=datetime.utcnow)


class UserPoints(Base):
    __tablename__ = "user_points"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    xp = Column(Integer, default=0)
    level = Column(String(40), default="Beginner")
    streak_days = Column(Integer, default=0)
    last_activity_date = Column(String(20), default="")

    user = relationship("User", back_populates="points")


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String(255))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    reason = Column(String(255))
    status = Column(String(20), default="open")  # open/resolved
    created_at = Column(DateTime, default=datetime.utcnow)
