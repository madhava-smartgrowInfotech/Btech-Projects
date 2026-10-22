from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    education = Column(String(120), default="")
    skill_level = Column(String(60), default="Beginner")
    interests = Column(Text, default="")  # comma separated
    preferred_topics = Column(Text, default="")
    learning_style = Column(String(80), default="Self-paced")
    goals = Column(Text, default="")
    course_preferences = Column(Text, default="")
    weekly_hours = Column(Float, default=5.0)
    age_band = Column(String(30), default="25-34")
    gender = Column(String(30), default="Prefer not to say")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="profile")

class Course(Base):
    __tablename__ = "courses"
    id = Column(String(30), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(120), default="")
    topic = Column(String(120), default="")
    skill_level = Column(String(60), default="Beginner")
    description = Column(Text, default="")
    duration_hours = Column(Float, default=10.0)
    difficulty = Column(String(40), default="Introductory")
    prerequisites = Column(Text, default="")
    outcomes = Column(Text, default="")
    tags = Column(Text, default="")
    resource_type = Column(String(80), default="Video + Quizzes")
    rating = Column(Float, default=4.5)

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    course_id = Column(String(30), index=True, default="")
    event_type = Column(String(60), index=True)  # view, open, start, quiz, content, forum, complete, dismiss, save
    value = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="interactions")

class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    course_id = Column(String(30), index=True)
    score = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class AuthToken(Base):
    __tablename__ = "auth_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="tokens")
