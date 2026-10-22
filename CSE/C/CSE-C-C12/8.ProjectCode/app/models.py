from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    consultations = relationship("Consultation", back_populates="user", cascade="all, delete-orphan")

class Consultation(Base):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symptom_query = Column(Text, nullable=False)
    generated_response = Column(Text, nullable=False)
    top_condition = Column(String(255), default="")
    retrieved_evidence = Column(Text, default="[]")
    retrieval_score = Column(Float, default=0.0)
    safety_flag = Column(String(50), default="routine")
    created_at = Column(DateTime, default=_utcnow)
    user = relationship("User", back_populates="consultations")
