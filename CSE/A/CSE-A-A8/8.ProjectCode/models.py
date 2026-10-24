"""
models.py
---------
SQLAlchemy ORM models for the AI-Powered Medical Lab Report Analysis
& Health Insights Platform.

Tables:
    - Report        : one row per uploaded lab report file
    - TestResult     : one row per extracted lab test within a report
    - HealthInsight  : one row per AI-generated explanation for an
                        abnormal TestResult
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Report(Base):
    """A single uploaded lab report (PDF/JPG/PNG)."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=True)          # pdf / jpg / png
    upload_date = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(50), default="Pending")
    # Pending -> Processing -> Completed -> Failed
    error_message = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)                  # full OCR/text dump

    test_results = relationship(
        "TestResult", back_populates="report", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Report id={self.id} file={self.file_name} status={self.processing_status}>"


class TestResult(Base):
    """A single lab test value extracted from a report."""

    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)

    test_name = Column(String(255), nullable=False)
    result_value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    reference_low = Column(Float, nullable=True)
    reference_high = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)              # LOW / NORMAL / HIGH / UNKNOWN
    test_date = Column(DateTime, nullable=True)
    confidence_score = Column(Float, default=0.0)           # 0-1 extraction confidence

    report = relationship("Report", back_populates="test_results")
    insights = relationship(
        "HealthInsight", back_populates="test_result", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<TestResult {self.test_name}={self.result_value}{self.unit or ''} "
            f"status={self.status}>"
        )


class HealthInsight(Base):
    """AI-generated educational explanation for an abnormal test result."""

    __tablename__ = "health_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)

    explanation = Column(Text, nullable=True)
    possible_causes = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_result = relationship("TestResult", back_populates="insights")

    def __repr__(self):
        return f"<HealthInsight for test_result_id={self.test_result_id}>"
