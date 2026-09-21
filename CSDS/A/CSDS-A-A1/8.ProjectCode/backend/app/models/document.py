"""A parsed policy wording, shared by every library entry that uploads the same PDF (keyed by SHA-256)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, utcnow

# Processing states, in order.
DOC_STATUSES = ("queued", "parsing", "indexing", "extracting", "ready", "failed")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))  # relative to the project root
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    insurer: Mapped[str | None] = mapped_column(String(200))
    product_name: Mapped[str | None] = mapped_column(String(200))
    uin: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    status_detail: Mapped[str | None] = mapped_column(String(300))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    extraction_error: Mapped[str | None] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(default=False)
    sample_slug: Mapped[str | None] = mapped_column(String(80))
    index_version: Mapped[str | None] = mapped_column(String(60))
    parse_stats: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    clauses: Mapped[list[Clause]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="Clause.ordinal"
    )
    card: Mapped[PolicyCard | None] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )
    risks: Mapped[list[RiskFlag]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Clause(Base):
    """One retrievable chunk of a policy wording, with its location in the PDF."""

    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)  # 1-based order within the document; shown as C<ordinal>
    clause_ref: Mapped[str | None] = mapped_column(String(60))  # numbering printed in the policy, e.g. "4.2.1"
    heading: Mapped[str | None] = mapped_column(String(300))
    section_path: Mapped[str | None] = mapped_column(String(600))  # "Exclusions > Specific waiting periods"
    text: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    bboxes: Mapped[list[dict[str, float]]] = mapped_column(JSON, default=list)  # [{page,x0,y0,x1,y1}] in PDF points
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped[Document] = relationship(back_populates="clauses")


class PolicyCard(Base):
    __tablename__ = "policy_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(20))
    verified_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    document: Mapped[Document] = relationship(back_populates="card")


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(10))  # high | medium | low
    explanation: Mapped[str] = mapped_column(Text)
    clause_ordinal: Mapped[int | None] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer)
    quote: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(10))  # rule | ai
    rule_id: Mapped[str | None] = mapped_column(String(60))

    document: Mapped[Document] = relationship(back_populates="risks")
