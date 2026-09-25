"""SQLAlchemy models + engine for prediction history storage."""
import datetime as dt
import uuid

from sqlalchemy import JSON, Column, DateTime, Float, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DB_URL

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=dt.datetime.utcnow, index=True)

    seed_type = Column(String, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rainfall = Column(Float, nullable=False)
    soil_ph = Column(Float, nullable=False)

    prediction = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    probability_germinate = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)

    morphological_features = Column(JSON, nullable=False)
    embedding_summary = Column(JSON, nullable=False)
    explanation = Column(JSON, nullable=False)
    thumbnail_data_url = Column(String, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
