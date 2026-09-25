"""Persistence models for catalogue, shoppers, behaviour and intelligence state."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from .db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, index=True, nullable=False)
    subcategory = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    compare_at_price = Column(Float, nullable=True)
    currency = Column(String, default="USD", nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String, nullable=False)
    image_seed = Column(String, nullable=False)
    colorway = Column(String, nullable=False)
    rating = Column(Float, nullable=False)
    review_count = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    tags = Column(JSON, nullable=False)
    attributes = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    user_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    """A synthetic shopper. `latent` is the hidden taste vector that drives both
    the generated behaviour stream and the digital twin's response model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    segment = Column(String, index=True, nullable=False)
    avatar_seed = Column(String, nullable=False)
    blurb = Column(String, nullable=False)
    is_demo_persona = Column(Boolean, default=False, nullable=False)
    activity_level = Column(String, nullable=False)
    latent = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    product_id = Column(Integer, index=True, nullable=True)
    type = Column(String, index=True, nullable=False)
    query = Column(String, nullable=True)
    value = Column(Float, nullable=True)
    rec_id = Column(String, nullable=True)
    source_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class StrategyState(Base):
    """Single-row table holding the live orchestrator blend."""

    __tablename__ = "strategy_state"

    id = Column(Integer, primary_key=True)
    weights = Column(JSON, nullable=False)
    step = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WeightHistory(Base):
    __tablename__ = "weight_history"

    id = Column(Integer, primary_key=True)
    step = Column(Integer, index=True, nullable=False)
    weights = Column(JSON, nullable=False)
    trigger_action = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    run_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    weights = Column(JSON, nullable=False)
    verdict = Column(String, nullable=False)
    lift = Column(JSON, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    rec_id = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    reward = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
