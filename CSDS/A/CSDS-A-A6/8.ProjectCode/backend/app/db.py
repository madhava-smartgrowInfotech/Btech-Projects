import json
from datetime import datetime

from sqlalchemy import (
    create_engine, ForeignKey, String, Integer, Float, Text, DateTime, LargeBinary
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)

from .config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contracts: Mapped[list["Contract"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(500))
    contract_type_guess: Mapped[str] = mapped_column(String(100), default="general")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complexity_grade: Mapped[str] = mapped_column(String(2), default="")
    complexity_score: Mapped[float] = mapped_column(Float, default=0.0)
    readability_score: Mapped[float] = mapped_column(Float, default=0.0)
    legalese_density: Mapped[float] = mapped_column(Float, default=0.0)
    cross_reference_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_sentence_length: Mapped[float] = mapped_column(Float, default=0.0)

    plain_summary: Mapped[str] = mapped_column(Text, default="")
    key_obligations: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    combo_flags: Mapped[str] = mapped_column(Text, default="[]")  # JSON list

    owner: Mapped["User"] = relationship(back_populates="contracts")
    clauses: Mapped[list["Clause"]] = relationship(back_populates="contract", cascade="all, delete-orphan")

    def combo_flags_list(self):
        return json.loads(self.combo_flags or "[]")

    def key_obligations_list(self):
        return json.loads(self.key_obligations or "[]")


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    index_in_doc: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    text: Mapped[str] = mapped_column(Text)
    clause_type: Mapped[str] = mapped_column(String(100), default="Unclassified")
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    classification_method: Mapped[str] = mapped_column(String(20), default="embedding")
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="clauses")
    flags: Mapped[list["Flag"]] = relationship(back_populates="clause", cascade="all, delete-orphan")


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    clause_id: Mapped[int] = mapped_column(ForeignKey("clauses.id"))
    rule_id: Mapped[str] = mapped_column(String(100))
    rule_label: Mapped[str] = mapped_column(String(200))
    severity: Mapped[str] = mapped_column(String(20))  # low/medium/high
    reason: Mapped[str] = mapped_column(Text, default="")
    provision: Mapped[str] = mapped_column(Text, default="")
    safer_wording: Mapped[str] = mapped_column(Text, default="")

    clause: Mapped["Clause"] = relationship(back_populates="flags")


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
