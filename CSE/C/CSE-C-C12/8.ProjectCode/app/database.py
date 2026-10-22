from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(f"sqlite:///{settings.DATABASE_PATH}", connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app import models  # noqa
    Base.metadata.create_all(bind=engine)
