"""In-memory cache of a document's clauses (read from SQLite) shared by BM25 and the retriever."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import Clause, Document


@dataclass(frozen=True)
class ClauseRecord:
    id: int
    document_id: int
    ordinal: int
    clause_ref: str | None
    heading: str | None
    section_path: str | None
    text: str
    page_start: int
    page_end: int
    bboxes: tuple

    @property
    def index_text(self) -> str:
        parts = [p for p in (self.section_path, self.heading) if p]
        prefix = " > ".join(parts)
        return f"{prefix}\n{self.text}" if prefix else self.text

    @property
    def label(self) -> str:
        ref = f"Clause {self.clause_ref}" if self.clause_ref else f"C{self.ordinal}"
        return f"{ref} - {self.heading}" if self.heading else ref


_lock = threading.Lock()
_cache: dict[int, tuple[str, list[ClauseRecord]]] = {}


def load_clauses(document_id: int) -> list[ClauseRecord]:
    with SessionLocal() as db:
        version = db.scalar(select(Document.index_version).where(Document.id == document_id)) or ""
        cached = _cache.get(document_id)
        if cached and cached[0] == version:
            return cached[1]
        rows = db.scalars(select(Clause).where(Clause.document_id == document_id).order_by(Clause.ordinal)).all()
        records = [
            ClauseRecord(
                id=r.id, document_id=r.document_id, ordinal=r.ordinal, clause_ref=r.clause_ref, heading=r.heading,
                section_path=r.section_path, text=r.text, page_start=r.page_start, page_end=r.page_end,
                bboxes=tuple(r.bboxes or []),
            )
            for r in rows
        ]
    with _lock:
        _cache[document_id] = (version, records)
    return records


def invalidate(document_id: int) -> None:
    with _lock:
        _cache.pop(document_id, None)
