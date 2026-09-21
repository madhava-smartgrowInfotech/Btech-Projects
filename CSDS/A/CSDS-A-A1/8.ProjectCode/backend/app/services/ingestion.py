"""Background ingestion: parse -> clauses -> dense index -> Policy Card extraction -> risks.

A single worker thread processes jobs one at a time (local models and the Gemini quota are
shared resources), so uploads return immediately and the UI polls the document status.
"""

from __future__ import annotations

import queue
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, select

from app.core.config import ROOT_DIR, get_settings
from app.core.db import SessionLocal, utcnow
from app.core.logging import get_logger, log_event
from app.models import Clause, Document
from app.services.pdf_parser import ScannedPdfError, parse_pdf
from app.services.segmenter import find_uin, segment

log = get_logger("ingestion")


@dataclass(frozen=True)
class Job:
    document_id: int
    kind: str = "full"  # full | index | extract | reextract (bypasses the response cache)


_queue: queue.Queue[Job | None] = queue.Queue()
_pending: set[tuple[int, str]] = set()
_pending_lock = threading.Lock()
_thread: threading.Thread | None = None
_current: Job | None = None


def _set_status(document_id: int, status: str, detail: str | None = None, progress: int | None = None,
                **fields: object) -> None:
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return
        doc.status = status
        doc.status_detail = detail
        if progress is not None:
            doc.progress = progress
        for key, value in fields.items():
            setattr(doc, key, value)
        db.commit()


def document_file(doc: Document) -> Path:
    path = Path(doc.file_path)
    return path if path.is_absolute() else ROOT_DIR / path


def parse_into_db(document_id: int) -> int:
    """Parse the PDF and replace the document's clauses. Returns the clause count."""
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            raise ValueError("Document not found")
        path = document_file(doc)
    start = time.perf_counter()
    parsed = parse_pdf(path)
    chunks = segment(parsed)
    if not chunks:
        raise ValueError("No readable clauses were found in this PDF.")
    stats = {
        "pages": parsed.page_count,
        "words": parsed.word_count,
        "clauses": len(chunks),
        "two_column": parsed.two_column,
        "headers_removed": parsed.removed_furniture,
        "page_sizes": [[round(w, 1), round(h, 1)] for w, h in parsed.page_sizes],
        "parse_ms": round((time.perf_counter() - start) * 1000),
    }
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        db.execute(delete(Clause).where(Clause.document_id == document_id))
        db.add_all(
            Clause(document_id=document_id, ordinal=c.ordinal, clause_ref=c.clause_ref, heading=c.heading,
                   section_path=c.section_path, text=c.text, page_start=c.page_start, page_end=c.page_end,
                   bboxes=c.bboxes, word_count=c.word_count)
            for c in chunks
        )
        doc.page_count = parsed.page_count
        doc.uin = doc.uin or find_uin(parsed)
        doc.parse_stats = stats
        doc.index_version = f"{int(time.time())}"
        db.commit()
    _invalidate(document_id)
    log_event(log, "parsed", document_id=document_id, pages=parsed.page_count, clauses=len(chunks),
              ms=stats["parse_ms"])
    return len(chunks)


def _invalidate(document_id: int) -> None:
    from app.ml.retrieval import bm25_index, clause_cache

    clause_cache.invalidate(document_id)
    bm25_index.invalidate(document_id)


def index_into_store(document_id: int) -> int:
    from app.ml.retrieval import dense_index

    return dense_index.index_document(document_id)


def extract_into_db(document_id: int, fresh: bool = False) -> None:
    from app.services.extractor import extract_policy_card

    extract_policy_card(document_id, fresh=fresh)


def process(job: Job) -> None:
    doc_id = job.document_id
    try:
        if job.kind == "full":
            _set_status(doc_id, "parsing", "Reading the PDF and splitting it into clauses", 10, error=None)
            parse_into_db(doc_id)
        if job.kind in ("full", "index"):
            _set_status(doc_id, "indexing", "Building the keyword and semantic search index", 40)
            index_into_store(doc_id)
        if job.kind in ("full", "extract", "reextract"):
            settings = get_settings()
            if settings.gemini_configured:
                _set_status(doc_id, "extracting", "Building the Policy Card and risk highlights with AI", 65)
                try:
                    extract_into_db(doc_id, fresh=job.kind == "reextract")
                    _set_status(doc_id, "extracting", "Policy Card ready", 95, extraction_error=None)
                except Exception as exc:  # noqa: BLE001 - the policy stays usable for search and chat
                    log_event(log, "extraction_failed", document_id=doc_id, error=str(exc)[:300])
                    _set_status(doc_id, "extracting", None, 95, extraction_error=_friendly(exc))
            else:
                _set_status(doc_id, "extracting", None, 95,
                            extraction_error="Add a Gemini API key to .env to build the Policy Card.")
        _set_status(doc_id, "ready", None, 100, processed_at=utcnow())
    except ScannedPdfError as exc:
        _set_status(doc_id, "failed", None, 100, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        log.error("ingestion_failed document_id=%s\n%s", doc_id, traceback.format_exc())
        _set_status(doc_id, "failed", None, 100, error=_friendly(exc))


def _friendly(exc: Exception) -> str:
    detail = getattr(exc, "detail", None)
    if isinstance(detail, str):
        return detail
    text = str(exc) or type(exc).__name__
    return text[:400]


def _worker() -> None:
    global _current
    while True:
        job = _queue.get()
        if job is None:
            break
        with _pending_lock:
            _pending.discard((job.document_id, job.kind))
        _current = job
        started = time.perf_counter()
        log_event(log, "job_started", document_id=job.document_id, kind=job.kind)
        process(job)
        log_event(log, "job_finished", document_id=job.document_id, kind=job.kind,
                  s=round(time.perf_counter() - started, 1))
        _current = None
        _queue.task_done()


def enqueue(document_id: int, kind: str = "full") -> None:
    key = (document_id, kind)
    with _pending_lock:
        if key in _pending:
            return
        _pending.add(key)
    if kind == "full":
        _set_status(document_id, "queued", "Waiting to be processed", 5)
    _queue.put(Job(document_id, kind))


def start_worker() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_worker, name="ingestion", daemon=True)
    _thread.start()
    _resume_unfinished()


def stop_worker() -> None:
    if _thread is not None and _thread.is_alive():
        _queue.put(None)


def _resume_unfinished() -> None:
    """Re-queue work interrupted by a restart, and index documents whose vectors are missing."""
    from app.ml.retrieval import dense_index

    with SessionLocal() as db:
        docs = db.scalars(select(Document)).all()
        for doc in docs:
            if doc.status in ("queued", "parsing"):
                enqueue(doc.id, "full")
            elif doc.status in ("indexing",):
                enqueue(doc.id, "index")
            elif doc.status == "extracting":
                enqueue(doc.id, "extract")
            elif doc.status == "ready":
                clause_count = len(doc.clauses)
                if clause_count and dense_index.count_for(doc.id) != clause_count:
                    _queue.put(Job(doc.id, "index"))


def worker_status() -> dict[str, object]:
    return {
        "running": _thread is not None and _thread.is_alive(),
        "queued": _queue.qsize(),
        "current": {"document_id": _current.document_id, "kind": _current.kind} if _current else None,
    }


def wait_until_idle(timeout: float = 600.0) -> bool:
    """Block until the queue is empty (used by scripts and tests)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _queue.unfinished_tasks == 0:
            return True
        time.sleep(0.5)
    return False
