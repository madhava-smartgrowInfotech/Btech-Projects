"""PeerScope ORM models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database import Base


class Reviewer(Base):
    __tablename__ = "reviewers"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String(200), nullable=False)
    affiliation = Column(String(300), default="")
    expertise_description = Column(Text, default="")
    research_topics = Column(Text, default="")  # comma separated
    methods = Column(Text, default="")  # comma separated
    keywords = Column(Text, default="")  # comma separated
    publication_titles = Column(Text, default="")
    current_load = Column(Integer, default=0)
    maximum_load = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    conflict_terms = Column(Text, default="")  # comma separated


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(300), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    overall_assessment = Column(String(120), default="")
    concern_count = Column(Integer, default=0)
    recommendation_count = Column(Integer, default=0)
    top_reviewer = Column(String(200), default="")
    status = Column(String(60), default="completed")
    result_json = Column(Text, default="{}")
