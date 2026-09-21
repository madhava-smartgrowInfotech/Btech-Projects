"""F2 - Policy Card: schema-constrained Gemini extraction over the whole policy wording.

Every extracted value carries a clause tag and a verbatim quote. The quote is then located in the
parsed clauses (fuzzy match) to confirm - or correct - the clause and page; values whose quote
cannot be found are kept but marked *unverified* in the UI.
"""

from __future__ import annotations

import re
import time
from typing import Any

import pymupdf
from sqlalchemy import delete

from app.core.db import SessionLocal
from app.core.logging import get_logger, log_event
from app.ml.retrieval.clause_cache import ClauseRecord, load_clauses
from app.models import Document, PolicyCard, RiskFlag
from app.schemas.policy_card import PROMPT_VERSION, PolicyCardExtraction, Sourced
from app.services.gemini_client import generate_json
from app.services.text_match import contains_text, token_overlap

log = get_logger("extractor")

SYSTEM = """You are a meticulous health-insurance analyst. You read ONE Indian health-insurance policy wording
and fill a structured Policy Card for the policyholder.

Rules:
- Use ONLY the policy text provided. Never add outside knowledge about the insurer or the product.
- Every stated value must cite the clause tag where it appears (for example "C42") and include a short quote
  copied character-for-character from that clause (at most 30 words).
- If the policy does not state an item, set found=false, value="Not specified in this policy", clause=null,
  quote=null. Do not guess.
- If the policy EXCLUDES a benefit (for example maternity under a standard exclusion), that is a stated value:
  set found=true, value="Not covered" (add "except ..." or "available as an optional cover" when the text says
  so) and cite the exclusion clause.
- Give full ranges or options where the policy offers several (for example all sum insured options).
- Normalise numbers: rupees for amounts (1 lakh = 100000, 1 crore = 10000000), percent for percentages,
  months for waiting periods (2 years = 24 months), days for day counts.
- Write values and the summary in plain English for a policyholder: short, clear, legally faithful.
- Risks: focus on what reduces or delays a claim payout. Severity high = can deny or sharply cut a claim;
  medium = a notable cost or limit; low = minor or conditional.
"""


def format_policy_text(clauses: list[ClauseRecord]) -> str:
    parts = []
    for c in clauses:
        location = f"page {c.page_start}" if c.page_start == c.page_end else f"pages {c.page_start}-{c.page_end}"
        context = " > ".join(p for p in (c.section_path, c.heading) if p)
        header = f"[C{c.ordinal}] ({location})" + (f" {context}" if context else "")
        parts.append(f"{header}\n{c.text}")
    return "\n\n".join(parts)


class _Locator:
    """Finds the clause and page where a quote really appears."""

    def __init__(self, clauses: list[ClauseRecord], pdf_path: str | None) -> None:
        self.clauses = clauses
        self.by_ordinal = {c.ordinal: c for c in clauses}
        self._page_text: dict[int, str] = {}
        if pdf_path:
            try:
                with pymupdf.open(pdf_path) as doc:
                    self._page_text = {i + 1: page.get_text() for i, page in enumerate(doc)}
            except Exception:  # noqa: BLE001 - page refinement is optional
                self._page_text = {}

    def clause_from_tag(self, tag: str | None) -> ClauseRecord | None:
        if not tag:
            return None
        m = re.search(r"(\d+)", tag)
        return self.by_ordinal.get(int(m.group(1))) if m else None

    def page_of(self, quote: str, clause: ClauseRecord) -> int:
        if clause.page_start == clause.page_end or not self._page_text:
            return clause.page_start
        for page in range(clause.page_start, clause.page_end + 1):
            if contains_text(self._page_text.get(page, ""), quote, 0.8):
                return page
        return clause.page_start

    def locate(self, tag: str | None, quote: str | None) -> tuple[ClauseRecord | None, int | None, bool]:
        cited = self.clause_from_tag(tag)
        if quote and len(quote.split()) >= 2:
            if cited and contains_text(cited.text, quote, 0.8):
                return cited, self.page_of(quote, cited), True
            best: tuple[float, ClauseRecord] | None = None
            for c in self.clauses:
                if contains_text(c.text, quote, 0.8):
                    score = token_overlap(c.text, quote)
                    if best is None or score > best[0]:
                        best = (score, c)
            if best:
                return best[1], self.page_of(quote, best[1]), True
        if cited:
            return cited, cited.page_start, False
        return None, None, False


def _store_sourced(item: Sourced, locator: _Locator) -> dict[str, Any]:
    data = item.model_dump()
    data.pop("clause", None)
    if not item.found:
        data.update(clause_ordinal=None, clause_ref=None, clause_label=None, page=None, verified=False, quote=None)
        return data
    clause, page, verified = locator.locate(item.clause, item.quote)
    data.update(
        clause_ordinal=clause.ordinal if clause else None,
        clause_ref=clause.clause_ref if clause else None,
        clause_label=clause.label if clause else None,
        page=page,
        verified=verified,
    )
    return data


def enrich(extraction: PolicyCardExtraction, locator: _Locator) -> dict[str, Any]:
    """Convert the model output into the stored Policy Card shape with verified sources."""
    out: dict[str, Any] = {
        "insurer": extraction.insurer,
        "product_name": extraction.product_name,
        "uin": extraction.uin,
        "policy_type": extraction.policy_type,
        "specific_disease_examples": extraction.specific_disease_examples[:12],
    }
    for name, value in extraction:
        if isinstance(value, Sourced):
            out[name] = _store_sourced(value, locator)
        elif isinstance(value, list) and value and isinstance(value[0], Sourced):
            out[name] = [_store_sourced(v, locator) | {"name": getattr(v, "name", "")} for v in value]
        elif name in ("waiting_periods", "claim_timelines"):
            out[name] = {k: _store_sourced(v, locator) for k, v in value}
        elif name in ("co_payment_conditions", "sub_limits", "key_exclusions"):
            out[name] = []
    return out


def iter_sourced(card: dict[str, Any]):  # noqa: ANN201 - yields (path, sourced dict)
    for key, value in card.items():
        if isinstance(value, dict) and "found" in value:
            yield key, value
        elif isinstance(value, dict):
            for sub, item in value.items():
                if isinstance(item, dict) and "found" in item:
                    yield f"{key}.{sub}", item
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict) and "found" in item:
                    yield f"{key}[{i}]", item


def verified_ratio(card: dict[str, Any]) -> float:
    found = [item for _, item in iter_sourced(card) if item.get("found")]
    if not found:
        return 0.0
    return round(sum(1 for item in found if item.get("verified")) / len(found), 3)


def run_extraction(document_id: int, user_id: int | None = None, fresh: bool = False
                   ) -> tuple[dict[str, Any], dict[str, Any], list[dict], dict[str, Any]]:
    """Call Gemini and return (card, summary, ai_risks, meta) without writing to the database."""
    from app.services.ingestion import document_file

    clauses = load_clauses(document_id)
    if not clauses:
        raise ValueError("This policy has no parsed clauses yet.")
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        sha, name, uin = doc.sha256, doc.file_name, doc.uin
        pdf_path = str(document_file(doc))

    prompt = (
        f"Policy file: {name}\nUIN printed on the document: {uin or 'not detected'}\n"
        f"Clause tags look like [C12] and are followed by the page and the section heading.\n\n"
        f"POLICY TEXT\n\n{format_policy_text(clauses)}"
    )
    start = time.perf_counter()
    extraction, meta = generate_json(
        prompt=prompt, schema=PolicyCardExtraction, purpose="policy_card", system=SYSTEM, user_id=user_id,
        temperature=0.1, cache=True, refresh=fresh, cache_salt=f"{sha}:{PROMPT_VERSION}", max_output_tokens=24000,
    )
    locator = _Locator(clauses, pdf_path)
    card = enrich(extraction, locator)
    ai_risks = []
    for risk in extraction.ai_risks[:8]:
        clause, page, verified = locator.locate(risk.clause, risk.quote)
        ai_risks.append({
            "title": risk.title, "severity": risk.severity, "category": risk.category,
            "explanation": risk.explanation, "clause_ordinal": clause.ordinal if clause else None,
            "page": page, "quote": risk.quote if verified else None, "source": "ai",
        })
    info = meta.to_dict() | {"total_ms": round((time.perf_counter() - start) * 1000)}
    return card, extraction.summary.model_dump(), ai_risks, info


def extract_policy_card(document_id: int, user_id: int | None = None, fresh: bool = False) -> None:
    from app.services.risk_engine import build_risks

    card, summary, ai_risks, meta = run_extraction(document_id, user_id, fresh=fresh)
    clauses = load_clauses(document_id)
    risks = build_risks(card, ai_risks, clauses)
    save_card(document_id, card, summary, risks, model=meta["model"], latency_ms=meta.get("latency_ms"))
    log_event(log, "card_extracted", document_id=document_id, model=meta["model"], cached=meta["cached"],
              verified=verified_ratio(card), risks=len(risks))


def save_card(document_id: int, card: dict[str, Any], summary: dict[str, Any] | None, risks: list[dict],
              model: str, latency_ms: int | None = None, prompt_version: str = PROMPT_VERSION) -> None:
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        db.execute(delete(PolicyCard).where(PolicyCard.document_id == document_id))
        db.execute(delete(RiskFlag).where(RiskFlag.document_id == document_id))
        db.add(PolicyCard(document_id=document_id, data=card, summary=summary, model=model,
                          prompt_version=prompt_version, verified_ratio=verified_ratio(card), latency_ms=latency_ms))
        for r in risks:
            db.add(RiskFlag(document_id=document_id, title=r["title"][:200], category=r["category"],
                            severity=r["severity"], explanation=r["explanation"], clause_ordinal=r.get("clause_ordinal"),
                            page=r.get("page"), quote=r.get("quote"), source=r["source"], rule_id=r.get("rule_id")))
        if card.get("insurer"):
            doc.insurer = card["insurer"][:200]
        if card.get("product_name"):
            doc.product_name = card["product_name"][:200]
        if card.get("uin") and not doc.uin:
            doc.uin = card["uin"][:60]
        db.commit()
