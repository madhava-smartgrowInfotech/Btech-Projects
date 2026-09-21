"""F5 - Claim Copilot: coverage verdict, eligibility pre-checks, document checklist and claim steps.

Retrieval runs several targeted sub-queries (coverage, exclusions, waiting periods, sub-limits, claim
procedure, documents) and merges their best clauses. Deterministic pre-checks from the Policy Card are
computed first and handed to Gemini, which returns a structured, clause-cited plan in the chosen language.
"""

from __future__ import annotations

import re
import time
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.config import LANGUAGE_NAMES
from app.core.logging import get_logger, log_event
from app.ml.faithfulness import ClaimInput, score_claims
from app.ml.retrieval.clause_cache import ClauseRecord, load_clauses
from app.ml.retrieval.hybrid import retrieve
from app.services.answerer import citation_for, format_clauses, normalise_tags
from app.services.eligibility import pre_checks
from app.services.gemini_client import generate_json
from app.services.language import to_english_query
from app.services.text_match import token_overlap

log = get_logger("claims")

SYSTEM = """You are PolicyLens Claim Copilot. You help a policyholder check whether a treatment is covered by
THEIR health-insurance policy and how to claim it.

Rules:
- Use ONLY the numbered policy clauses and the computed facts provided. Never rely on typical market practice.
- Cite clause tags like [C12] in every reason, check, document and step that comes from the policy. Only use
  tags that appear in the provided clauses. Standard practical items not in the policy (for example "keep
  original bills") may have no tag.
- Verdict: "covered" = clearly payable if the stated conditions are met; "partly_covered" = payable but capped,
  co-paid, or only some expenses are payable; "not_covered" = excluded or a waiting period clearly applies;
  "needs_info" = the answer depends on facts the user has not given (for example the policy start date).
- Respect the computed facts: if a waiting-period check "fail"s, the verdict cannot be "covered".
- Write every user-facing text field in the requested language, simply. Also give English versions where asked.
"""


class Reason(BaseModel):
    text: str = Field(description="Reason in the requested language, citing tags like [C12].")
    text_en: str = Field(description="The same reason in English.")
    policy_fact_en: str = Field(description="Only the policy rule behind this reason, restated in English as close as "
                                            "possible to the clause wording, WITHOUT the user's details (no dates, "
                                            "ages or costs). Example: 'Joint replacement is excluded until the "
                                            "expiry of 24 months of continuous coverage.'")
    clauses: list[str]


class Check(BaseModel):
    check: str
    status: Literal["pass", "fail", "unknown", "warning"]
    detail: str
    clauses: list[str]


class DocItem(BaseModel):
    item: str
    why: str
    clauses: list[str]


class Step(BaseModel):
    title: str
    detail: str
    timeline: str | None = None
    clauses: list[str]


class ClaimPlan(BaseModel):
    verdict: Literal["covered", "partly_covered", "not_covered", "needs_info"]
    verdict_summary: str = Field(description="One or two sentences in the requested language.")
    verdict_summary_en: str
    reasons: list[Reason]
    prechecks: list[Check] = Field(description="Eligibility checks beyond the computed ones.")
    documents: list[DocItem] = Field(description="Documents needed for this claim, 5-12 items.")
    steps: list[Step] = Field(description="Step-by-step claim procedure for the chosen claim mode, 4-8 steps.")
    cost_notes: list[str] = Field(description="Cost points: sub-limits, co-payment, non-payable items, room rent.")


def _queries(treatment: str, inputs: dict[str, Any]) -> list[str]:
    mode = inputs.get("claim_mode") or "cashless"
    queries = [
        f"Is {treatment} covered under this policy",
        f"{treatment} waiting period",
        f"{treatment} exclusion not covered",
        f"{treatment} sub limit maximum amount payable",
        f"{'cashless claim procedure pre-authorization network hospital' if mode != 'reimbursement' else 'reimbursement claim procedure submission'}",
        "documents required for claim submission",
        "claim intimation notification time limit",
    ]
    if inputs.get("pre_existing") in ("yes", "not_sure"):
        queries.append("pre-existing disease waiting period")
    if inputs.get("room_type") not in (None, "not_sure", "general_ward"):
        queries.append("room rent limit proportionate deduction")
    if inputs.get("hospitalization_type") == "day_care":
        queries.append(f"day care treatment {treatment}")
    return queries


def _gather(document_id: int, treatment: str, inputs: dict[str, Any]) -> tuple[list[ClauseRecord], dict]:
    scores: dict[int, tuple[float, ClauseRecord]] = {}
    timings: dict[str, float] = {}
    for q in _queries(treatment, inputs):
        res = retrieve(document_id, q, k=4)
        for k, v in res.timings_ms.items():
            timings[k] = timings.get(k, 0) + v
        for item in res.items:
            best = scores.get(item.clause.ordinal)
            if best is None or item.score > best[0]:
                scores[item.clause.ordinal] = (item.score, item.clause)
    ranked = sorted(scores.values(), key=lambda s: s[0], reverse=True)[:16]
    clauses = sorted((c for _, c in ranked), key=lambda c: c.ordinal)
    return clauses, timings


def run_claim_copilot(document_id: int, card: dict | None, treatment: str, inputs: dict[str, Any],
                      language: str = "en", user_id: int | None = None, cache: bool = False) -> dict[str, Any]:
    t0 = time.perf_counter()
    english = to_english_query(treatment, user_id)
    search_treatment = english or treatment

    t = time.perf_counter()
    clauses, stage_ms = _gather(document_id, search_treatment, inputs)
    retrieval_ms = round((time.perf_counter() - t) * 1000)
    by_ordinal = {c.ordinal: c for c in clauses}

    computed = pre_checks(card, search_treatment, inputs)
    # Every clause behind a calculated check goes to the model too, so it can cite it and we can verify it.
    all_clauses = {c.ordinal: c for c in load_clauses(document_id)}
    for check in computed["checks"]:
        ordinal = check.get("clause_ordinal")
        if ordinal and ordinal not in by_ordinal and ordinal in all_clauses:
            by_ordinal[ordinal] = all_clauses[ordinal]
            clauses.append(all_clauses[ordinal])
    clauses.sort(key=lambda c: c.ordinal)
    labels = {
        "hospitalization_type": inputs.get("hospitalization_type"), "claim_mode": inputs.get("claim_mode"),
        "policy_start_date": inputs["policy_start_date"].isoformat()
        if isinstance(inputs.get("policy_start_date"), date) else None,
        "insured_age": inputs.get("insured_age"), "pre_existing": inputs.get("pre_existing"),
        "estimated_cost": inputs.get("estimated_cost"), "room_type": inputs.get("room_type"),
        "notes": inputs.get("notes"),
    }
    prompt = (
        f"Requested language: {LANGUAGE_NAMES.get(language, 'English')}\n"
        f"Treatment / hospitalisation: {treatment}" + (f" (English: {english})" if english else "") + "\n"
        f"Details from the user: {labels}\n\n"
        f"Computed facts (from the Policy Card, deterministic):\n- " + "\n- ".join(computed["facts"] or ["none"]) +
        f"\n\nPOLICY CLAUSES\n\n{format_clauses(clauses)}"
    )
    t = time.perf_counter()
    plan, meta = generate_json(prompt=prompt, schema=ClaimPlan, purpose="claim_copilot", system=SYSTEM,
                               user_id=user_id, temperature=0.2, cache=cache)
    generation_ms = round((time.perf_counter() - t) * 1000)

    def tags(values: list[str]) -> list[int]:
        return [o for v in values for o in (int(x) for x in re.findall(r"\d+", v)) if o in by_ordinal]

    def cite(values: list[str]) -> list[dict[str, Any]]:
        return [{"ordinal": o, "label": by_ordinal[o].label, "page": by_ordinal[o].page_start} for o in tags(values)]

    # Guard-rail: a failed computed waiting-period check can never be "covered".
    verdict = plan.verdict
    if verdict == "covered" and any(c["status"] == "fail" for c in computed["checks"]):
        verdict = "not_covered"

    checks = [dict(c, clauses=[{"ordinal": c["clause_ordinal"], "page": c.get("page")}]
                   if c.get("clause_ordinal") else []) for c in computed["checks"]]
    for c in plan.prechecks:
        # Skip AI checks that restate a calculated one ("Initial 30-day waiting period" vs "Initial waiting period").
        if any(token_overlap(c.check, existing["check"]) >= 0.5 for existing in checks):
            continue
        checks.append({"check": c.check, "status": c.status, "detail": c.detail, "source": "ai",
                       "clauses": cite(c.clauses)})

    claims = [ClaimInput(r.policy_fact_en or r.text_en, tags(r.clauses)) for r in plan.reasons]
    t = time.perf_counter()
    faithfulness = score_claims(claims, {o: c.text for o, c in by_ordinal.items()})
    faith_ms = round((time.perf_counter() - t) * 1000)
    cited_ordinals = sorted({o for r in plan.reasons for o in tags(r.clauses)}
                            | {o for s in plan.steps for o in tags(s.clauses)}
                            | {o for d in plan.documents for o in tags(d.clauses)}
                            | {c["clause_ordinal"] for c in computed["checks"]
                               if c.get("clause_ordinal") in by_ordinal})
    total_ms = round((time.perf_counter() - t0) * 1000)
    result = {
        "verdict": verdict,
        "model_verdict": plan.verdict,
        "verdict_summary": plan.verdict_summary,
        "verdict_summary_en": plan.verdict_summary_en,
        "reasons": [{"text": normalise_tags(r.text), "text_en": r.text_en, "policy_fact_en": r.policy_fact_en,
                     "clauses": cite(r.clauses)} for r in plan.reasons],
        "prechecks": checks,
        "documents": [{"id": f"d{i}", "item": d.item, "why": d.why, "clauses": cite(d.clauses)}
                      for i, d in enumerate(plan.documents)],
        "steps": [{"title": s.title, "detail": s.detail, "timeline": s.timeline, "clauses": cite(s.clauses)}
                  for s in plan.steps],
        "cost_notes": plan.cost_notes,
        "estimate": computed["estimate"],
        "matched_specific_disease": computed.get("matched_specific_disease"),
        "citations": [citation_for(by_ordinal[o]) for o in cited_ordinals],
        "faithfulness": faithfulness,
        "timings": {"retrieval_ms": retrieval_ms, "retrieval_stages_ms": stage_ms, "generation_ms": generation_ms,
                    "faithfulness_ms": faith_ms, "total_ms": total_ms},
        "model": meta.model,
        "cached": meta.cached,
    }
    log_event(log, "claim_checked", document_id=document_id, verdict=verdict, ms=total_ms, model=meta.model)
    return result
