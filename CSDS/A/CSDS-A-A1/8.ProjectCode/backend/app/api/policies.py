"""Policies: upload, library, status, PDF pages, clauses, Policy Card, risk highlights, clause search."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf
from fastapi import APIRouter, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, get_owned_policy
from app.core.config import get_settings, project_relative
from app.core.errors import AppError, Conflict, NotFound
from app.core.logging import get_logger, log_event
from app.models import Clause, Document, Policy, PolicyCard, RiskFlag
from app.schemas.policy import (
    CardOut,
    ClauseOut,
    DocumentOut,
    PageInfo,
    PolicyOut,
    PolicyRename,
    PolicyStatusOut,
    RiskOut,
    SearchIn,
)
from app.schemas.policy_card import CARD_FIELDS, TIMELINE_FIELDS, WAITING_FIELDS

router = APIRouter(prefix="/policies", tags=["policies"])
log = get_logger("policies")


def _highlights(card: PolicyCard | None) -> dict[str, str]:
    if card is None:
        return {}
    data = card.data or {}
    wp = data.get("waiting_periods") or {}
    picks = {
        "sum_insured": data.get("sum_insured"),
        "co_payment": data.get("co_payment"),
        "room_rent": data.get("room_rent_limit"),
        "pre_existing_wait": wp.get("pre_existing"),
        "specific_wait": wp.get("specific_diseases"),
    }
    return {k: v.get("value") for k, v in picks.items() if isinstance(v, dict) and v.get("found")}


def policy_out(db, policy: Policy) -> PolicyOut:  # noqa: ANN001
    doc = policy.document
    card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == doc.id))
    counts = dict(db.execute(select(RiskFlag.severity, func.count()).where(RiskFlag.document_id == doc.id)
                             .group_by(RiskFlag.severity)).all())
    clause_count = db.scalar(select(func.count()).select_from(Clause).where(Clause.document_id == doc.id)) or 0
    return PolicyOut(
        id=policy.id, display_name=policy.display_name, is_sample=policy.is_sample, created_at=policy.created_at,
        document=DocumentOut.model_validate(doc), has_card=card is not None, clause_count=clause_count,
        risk_counts={k: int(v) for k, v in counts.items()}, highlights=_highlights(card),
    )


@router.get("", response_model=list[PolicyOut])
def list_policies(user: CurrentUser, db: DbSession) -> list[PolicyOut]:
    policies = db.scalars(select(Policy).where(Policy.owner_id == user.id).order_by(Policy.created_at.desc())).all()
    return [policy_out(db, p) for p in policies]


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
async def upload_policy(user: CurrentUser, db: DbSession, file: UploadFile = File(...),
                        display_name: str | None = Form(default=None)) -> PolicyOut:
    settings = get_settings()
    name = (file.filename or "policy.pdf").strip()
    if not name.lower().endswith(".pdf"):
        raise AppError("Please upload a PDF file (the policy wording document).", code="not_pdf")
    limit = settings.max_upload_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise AppError(f"This file is larger than {settings.max_upload_mb} MB.", code="too_large", status_code=413)
    if not content.startswith(b"%PDF"):
        raise AppError("This file is not a valid PDF.", code="not_pdf")
    try:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise AppError("This PDF is password-protected. Please upload an unlocked copy.", code="encrypted")
            pages = pdf.page_count
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise AppError("This PDF could not be opened. It may be damaged.", code="bad_pdf") from exc
    if pages == 0:
        raise AppError("This PDF has no pages.", code="bad_pdf")

    sha = hashlib.sha256(content).hexdigest()
    doc = db.scalar(select(Document).where(Document.sha256 == sha))
    if doc is not None:
        existing = db.scalar(select(Policy).where(Policy.owner_id == user.id, Policy.document_id == doc.id))
        if existing is not None:
            raise Conflict(f"This policy is already in your library as “{existing.display_name}”.",
                           code="duplicate_policy")
    else:
        path = settings.uploads_dir / f"{sha}.pdf"
        path.write_bytes(content)
        doc = Document(sha256=sha, file_name=name[:255], file_path=project_relative(path), size_bytes=len(content),
                       page_count=pages, status="queued")
        db.add(doc)
        db.flush()
    label = (display_name or "").strip() or Path(name).stem.replace("_", " ").replace("-", " ").strip().title()
    policy = Policy(owner_id=user.id, document_id=doc.id, display_name=label[:200])
    db.add(policy)
    db.commit()
    db.refresh(policy)
    if doc.status in ("queued", "failed"):
        from app.services.ingestion import enqueue

        enqueue(doc.id, "full")
    log_event(log, "policy_uploaded", user_id=user.id, policy_id=policy.id, document_id=doc.id, pages=pages,
              reused=doc.status == "ready")
    db.refresh(policy)
    return policy_out(db, policy)


@router.post("/samples", response_model=list[PolicyOut])
def add_samples(user: CurrentUser, db: DbSession) -> list[PolicyOut]:
    from app.services.seed import add_samples_to_library

    new_ids = add_samples_to_library(user.id)
    if not new_ids:
        raise AppError("All sample policies are already in your library.", code="samples_present")
    policies = db.scalars(select(Policy).where(Policy.id.in_(new_ids))).all()
    return [policy_out(db, p) for p in policies]


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: int, user: CurrentUser, db: DbSession) -> PolicyOut:
    return policy_out(db, get_owned_policy(db, user, policy_id))


@router.patch("/{policy_id}", response_model=PolicyOut)
def rename_policy(policy_id: int, body: PolicyRename, user: CurrentUser, db: DbSession) -> PolicyOut:
    policy = get_owned_policy(db, user, policy_id)
    policy.display_name = body.display_name.strip()
    db.commit()
    return policy_out(db, policy)


@router.get("/{policy_id}/status", response_model=PolicyStatusOut)
def policy_status(policy_id: int, user: CurrentUser, db: DbSession) -> PolicyStatusOut:
    policy = get_owned_policy(db, user, policy_id)
    doc = policy.document
    db.refresh(doc)
    has_card = db.scalar(select(func.count()).select_from(PolicyCard).where(PolicyCard.document_id == doc.id)) > 0
    return PolicyStatusOut(id=policy.id, status=doc.status, status_detail=doc.status_detail, progress=doc.progress,
                           error=doc.error, extraction_error=doc.extraction_error, has_card=has_card)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: int, user: CurrentUser, db: DbSession) -> None:
    policy = get_owned_policy(db, user, policy_id)
    doc = policy.document
    db.delete(policy)
    db.commit()
    others = db.scalar(select(func.count()).select_from(Policy).where(Policy.document_id == doc.id))
    if others == 0 and not doc.is_sample:
        from app.ml.retrieval import bm25_index, clause_cache, dense_index
        from app.services.ingestion import document_file
        from app.services.page_renderer import clear_pages

        path = document_file(doc)
        dense_index.delete_document(doc.id)
        clause_cache.invalidate(doc.id)
        bm25_index.invalidate(doc.id)
        clear_pages(doc.id)
        db.delete(doc)
        db.commit()
        if path.exists() and "uploads" in path.parts:
            path.unlink(missing_ok=True)
    log_event(log, "policy_deleted", user_id=user.id, policy_id=policy_id)


@router.get("/{policy_id}/file")
def policy_file(policy_id: int, user: CurrentUser, db: DbSession) -> FileResponse:
    from app.services.ingestion import document_file

    policy = get_owned_policy(db, user, policy_id)
    path = document_file(policy.document)
    if not path.exists():
        raise NotFound("The PDF file for this policy is missing.")
    return FileResponse(path, media_type="application/pdf", filename=policy.document.file_name,
                        content_disposition_type="inline")


@router.get("/{policy_id}/pages", response_model=list[PageInfo])
def policy_pages(policy_id: int, user: CurrentUser, db: DbSession) -> list[PageInfo]:
    doc = get_owned_policy(db, user, policy_id).document
    sizes = (doc.parse_stats or {}).get("page_sizes") or []
    if not sizes:
        from app.services.ingestion import document_file

        with pymupdf.open(str(document_file(doc))) as pdf:
            sizes = [[p.rect.width, p.rect.height] for p in pdf]
    return [PageInfo(number=i + 1, width=w, height=h) for i, (w, h) in enumerate(sizes)]


@router.get("/{policy_id}/pages/{page_number}")
def policy_page_image(policy_id: int, page_number: int, user: CurrentUser, db: DbSession,
                      scale: float = Query(default=1.5, ge=0.5, le=3.0)) -> FileResponse:
    from app.services.ingestion import document_file
    from app.services.page_renderer import render_page

    doc = get_owned_policy(db, user, policy_id).document
    try:
        path = render_page(document_file(doc), doc.id, page_number, scale)
    except IndexError as exc:
        raise NotFound("That page does not exist.") from exc
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, max-age=86400"})


def _clause_out(c: Clause) -> ClauseOut:
    ref = f"Clause {c.clause_ref}" if c.clause_ref else f"C{c.ordinal}"
    return ClauseOut(id=c.id, ordinal=c.ordinal, clause_ref=c.clause_ref, heading=c.heading,
                     section_path=c.section_path, text=c.text, page_start=c.page_start, page_end=c.page_end,
                     bboxes=c.bboxes or [], label=f"{ref} - {c.heading}" if c.heading else ref)


@router.get("/{policy_id}/clauses", response_model=list[ClauseOut])
def list_clauses(policy_id: int, user: CurrentUser, db: DbSession, page: int | None = None) -> list[ClauseOut]:
    doc = get_owned_policy(db, user, policy_id).document
    q = select(Clause).where(Clause.document_id == doc.id)
    if page is not None:
        q = q.where(Clause.page_start <= page, Clause.page_end >= page)
    return [_clause_out(c) for c in db.scalars(q.order_by(Clause.ordinal)).all()]


@router.get("/{policy_id}/clauses/{ordinal}", response_model=ClauseOut)
def get_clause(policy_id: int, ordinal: int, user: CurrentUser, db: DbSession) -> ClauseOut:
    doc = get_owned_policy(db, user, policy_id).document
    clause = db.scalar(select(Clause).where(Clause.document_id == doc.id, Clause.ordinal == ordinal))
    if clause is None:
        raise NotFound("Clause not found.")
    return _clause_out(clause)


def _labels() -> dict:
    return {"fields": dict(CARD_FIELDS), "waiting_periods": dict(WAITING_FIELDS),
            "claim_timelines": dict(TIMELINE_FIELDS)}


@router.get("/{policy_id}/card", response_model=CardOut)
def get_card(policy_id: int, user: CurrentUser, db: DbSession, lang: str | None = None) -> CardOut:
    policy = get_owned_policy(db, user, policy_id)
    card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == policy.document_id))
    if card is None:
        doc = policy.document
        if doc.status != "ready":
            raise AppError("The Policy Card is still being prepared.", code="card_pending", status_code=409)
        raise NotFound(doc.extraction_error or "The Policy Card is not available yet.", code="card_missing")
    language = lang or user.language or "en"
    data, summary, translated = card.data, card.summary, False
    if language != "en":
        from app.services.language import translate_card

        data, summary = translate_card(card.data, card.summary, language, user.id)
        translated = True
    return CardOut(policy_id=policy.id, document_id=card.document_id, language=language, model=card.model,
                   prompt_version=card.prompt_version, created_at=card.created_at, verified_ratio=card.verified_ratio,
                   translated=translated, data=data, summary=summary, labels=_labels())


@router.post("/{policy_id}/extract", response_model=PolicyStatusOut)
def rerun_extraction(policy_id: int, user: CurrentUser, db: DbSession) -> PolicyStatusOut:
    from app.services.ingestion import enqueue

    policy = get_owned_policy(db, user, policy_id)
    doc = policy.document
    if doc.status not in ("ready", "failed"):
        raise AppError("This policy is still being processed.", code="busy", status_code=409)
    if not get_settings().gemini_configured:
        raise AppError("Add a Gemini API key to .env to build the Policy Card.", code="ai_not_configured")
    doc.extraction_error = None
    db.commit()
    enqueue(doc.id, "reextract")  # bypasses the response cache: a genuinely new Gemini run
    return policy_status(policy_id, user, db)


@router.get("/{policy_id}/risks", response_model=list[RiskOut])
def get_risks(policy_id: int, user: CurrentUser, db: DbSession, lang: str | None = None) -> list[RiskOut]:
    policy = get_owned_policy(db, user, policy_id)
    risks = db.scalars(select(RiskFlag).where(RiskFlag.document_id == policy.document_id)).all()
    labels = {c.ordinal: c for c in db.scalars(select(Clause).where(Clause.document_id == policy.document_id)).all()}
    order = {"high": 0, "medium": 1, "low": 2}
    items = []
    for r in sorted(risks, key=lambda r: (order.get(r.severity, 3), r.id)):
        clause = labels.get(r.clause_ordinal) if r.clause_ordinal else None
        items.append({
            "id": r.id, "title": r.title, "category": r.category, "severity": r.severity,
            "explanation": r.explanation, "clause_ordinal": r.clause_ordinal,
            "clause_label": _clause_out(clause).label if clause else None, "page": r.page, "quote": r.quote,
            "source": r.source,
        })
    language = lang or user.language or "en"
    if language != "en":
        from app.services.language import translate_risks

        items = translate_risks(items, language, user.id)
    return [RiskOut(**i) for i in items]


@router.post("/{policy_id}/search")
def search_clauses(policy_id: int, body: SearchIn, user: CurrentUser, db: DbSession) -> dict:
    from app.ml.retrieval.hybrid import retrieve

    policy = get_owned_policy(db, user, policy_id)
    if policy.document.status not in ("ready", "extracting"):
        raise AppError("This policy is still being indexed.", code="busy", status_code=409)
    result = retrieve(policy.document_id, body.query, k=body.k, mode=body.mode)
    items = []
    for item in result.items:
        data = item.to_dict()
        data["clause"]["text"] = item.clause.text
        data["clause"]["label"] = item.clause.label
        data["clause"]["bboxes"] = list(item.clause.bboxes)
        items.append(data)
    return {"query": body.query, "mode": body.mode, "timings_ms": result.timings_ms, "items": items}
