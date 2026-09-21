"""First-run data: the demo account and the labelled sample policies.

Sample policies come from ``data/processed/<slug>/`` (parsed clauses + the Policy Card previously
extracted by Gemini, committed to the repository), so a fresh install shows complete sample policies
without spending any API quota. If a processed folder is missing, the sample PDF in ``data/policies/``
is queued for the normal ingestion pipeline instead.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.core.config import ROOT_DIR, get_settings
from app.core.db import SessionLocal, utcnow
from app.core.logging import get_logger, log_event
from app.core.security import hash_password
from app.models import Clause, Document, Policy, PolicyCard, RiskFlag, User

log = get_logger("seed")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def ensure_demo_user() -> int:
    s = get_settings()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == s.demo_email.lower()))
        if user is None:
            user = User(email=s.demo_email.lower(), full_name="Demo User", password_hash=hash_password(s.demo_password))
            db.add(user)
            db.commit()
            log_event(log, "demo_user_created", email=s.demo_email)
        return user.id


def _load_processed(folder: Path) -> dict[str, Any] | None:
    meta_file = folder / "document.json"
    if not meta_file.exists():
        return None
    data = {"meta": json.loads(meta_file.read_text(encoding="utf-8"))}
    clauses_file = folder / "clauses.jsonl"
    data["clauses"] = [json.loads(line) for line in clauses_file.read_text(encoding="utf-8").splitlines()
                       if line.strip()] if clauses_file.exists() else []
    card_file = folder / "card.json"
    data["card"] = json.loads(card_file.read_text(encoding="utf-8")) if card_file.exists() else None
    return data


def import_sample(folder: Path) -> int | None:
    """Create (or refresh) a sample Document from a processed folder. Returns its id."""
    data = _load_processed(folder)
    if data is None:
        return None
    meta = data["meta"]
    pdf = ROOT_DIR / meta["file_path"]
    if not pdf.exists():
        log_event(log, "sample_pdf_missing", path=meta["file_path"])
        return None
    with SessionLocal() as db:
        doc = db.scalar(select(Document).where(Document.sha256 == meta["sha256"]))
        if doc is not None and doc.status == "ready" and doc.clauses and (doc.card or not data["card"]):
            if not doc.is_sample:
                doc.is_sample, doc.sample_slug = True, meta["slug"]
                db.commit()
            return doc.id
        if doc is None:
            doc = Document(sha256=meta["sha256"], file_name=meta["file_name"], file_path=meta["file_path"])
            db.add(doc)
        doc.size_bytes = meta.get("size_bytes", 0)
        doc.page_count = meta.get("page_count", 0)
        doc.insurer = meta.get("insurer")
        doc.product_name = meta.get("product_name")
        doc.uin = meta.get("uin")
        doc.parse_stats = meta.get("parse_stats")
        doc.is_sample = True
        doc.sample_slug = meta["slug"]
        doc.index_version = meta.get("index_version") or "sample"
        db.flush()
        for model in (Clause, PolicyCard, RiskFlag):
            db.query(model).filter(model.document_id == doc.id).delete()
        for c in data["clauses"]:
            db.add(Clause(document_id=doc.id, ordinal=c["ordinal"], clause_ref=c.get("clause_ref"),
                          heading=c.get("heading"), section_path=c.get("section_path"), text=c["text"],
                          page_start=c["page_start"], page_end=c["page_end"], bboxes=c.get("bboxes") or [],
                          word_count=c.get("word_count") or len(c["text"].split())))
        card = data["card"]
        if card:
            db.add(PolicyCard(document_id=doc.id, data=card["data"], summary=card.get("summary"),
                              model=card["model"], prompt_version=card["prompt_version"],
                              verified_ratio=card.get("verified_ratio", 0.0), latency_ms=card.get("latency_ms")))
            for r in card.get("risks", []):
                db.add(RiskFlag(document_id=doc.id, title=r["title"], category=r["category"], severity=r["severity"],
                                explanation=r["explanation"], clause_ordinal=r.get("clause_ordinal"),
                                page=r.get("page"), quote=r.get("quote"), source=r["source"],
                                rule_id=r.get("rule_id")))
        doc.status = "indexing"
        doc.status_detail = "Building the search index for the sample policy"
        doc.progress = 60
        doc.error = None
        db.commit()
        doc_id = doc.id
    from app.services.ingestion import enqueue

    enqueue(doc_id, "index")
    log_event(log, "sample_imported", slug=meta["slug"], document_id=doc_id)
    return doc_id


def queue_raw_sample(pdf: Path, display_name: str | None = None) -> int:
    """No processed data for this sample yet - register it and run the full pipeline."""
    sha = sha256_of(pdf)
    with SessionLocal() as db:
        doc = db.scalar(select(Document).where(Document.sha256 == sha))
        if doc is None:
            doc = Document(sha256=sha, file_name=pdf.name, file_path=_rel(pdf), size_bytes=pdf.stat().st_size,
                           is_sample=True, sample_slug=pdf.stem, product_name=display_name, status="queued")
            db.add(doc)
            db.commit()
            new = True
        else:
            new = doc.status == "failed"
        doc_id = doc.id
    if new:
        from app.services.ingestion import enqueue

        enqueue(doc_id, "full")
    return doc_id


def sample_document_ids() -> list[int]:
    with SessionLocal() as db:
        return list(db.scalars(select(Document.id).where(Document.is_sample.is_(True)).order_by(Document.id)))


_INSURER_TAILS = [re.compile(rf"\s+{tail}\b.*$", re.I) for tail in
                  ("and allied", "general insurance", "health insurance", "insurance", "company", "limited", "ltd")]
_PRODUCT_TAIL = re.compile(r"\s+(insurance plan|insurance policy|health insurance policy|policy)$", re.I)


def short_insurer(name: str | None) -> str | None:
    """'Star Health and Allied Insurance Company Limited' -> 'Star Health' (keeps at least two words)."""
    if not name:
        return None
    for tail in _INSURER_TAILS:
        short = tail.sub("", name.strip()).strip(" ,-")
        if short != name.strip() and len(short.split()) >= 2:
            return short
    return name.strip()


def sample_display_name(doc: Document) -> str:
    product = _PRODUCT_TAIL.sub("", (doc.product_name or "").strip()).strip()
    insurer = short_insurer(doc.insurer)
    if product and insurer and insurer.lower() not in product.lower():
        return f"{product} ({insurer})"
    return product or doc.file_name.rsplit(".", 1)[0].replace("-", " ").title()


def add_samples_to_library(user_id: int) -> list[int]:
    """Give a user library entries for every sample policy they do not have yet. Returns new policy ids."""
    created: list[int] = []
    with SessionLocal() as db:
        existing = set(db.scalars(select(Policy.document_id).where(Policy.owner_id == user_id)))
        for doc in db.scalars(select(Document).where(Document.is_sample.is_(True)).order_by(Document.id)):
            if doc.id in existing:
                continue
            policy = Policy(owner_id=user_id, document_id=doc.id, display_name=sample_display_name(doc)[:200],
                            is_sample=True, created_at=utcnow())
            db.add(policy)
            db.flush()
            created.append(policy.id)
        db.commit()
    return created


def seed_all() -> None:
    settings = get_settings()
    user_id = ensure_demo_user()
    processed_root = settings.processed_dir
    done_pdfs: set[str] = set()
    if processed_root.exists():
        for folder in sorted(p for p in processed_root.iterdir() if p.is_dir()):
            meta_file = folder / "document.json"
            if meta_file.exists():
                done_pdfs.add(json.loads(meta_file.read_text(encoding="utf-8"))["file_path"])
                import_sample(folder)
    if settings.policies_dir.exists():
        for pdf in sorted(settings.policies_dir.glob("*.pdf")):
            if _rel(pdf) not in done_pdfs:
                queue_raw_sample(pdf)
    add_samples_to_library(user_id)
