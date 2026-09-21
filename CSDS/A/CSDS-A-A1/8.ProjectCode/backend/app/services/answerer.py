"""F3 - Clause-grounded answers (RAG) with citations, abstention and a faithfulness score.

Pipeline: (translate Hindi/Telugu question for search) -> hybrid retrieval of the policy's clauses
-> Gemini answers ONLY from those clauses, citing [C<n>] tags, in the chosen language, and restates
its answer as English claims -> citations to clauses that were not retrieved are removed ->
the local NLI model scores each claim against its cited clause text.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.config import LANGUAGE_NAMES
from app.core.logging import get_logger, log_event
from app.ml.faithfulness import ClaimInput, score_claims
from app.ml.retrieval.clause_cache import ClauseRecord
from app.ml.retrieval.hybrid import RetrievalResult, retrieve
from app.services.gemini_client import generate_json
from app.services.language import to_english_query

log = get_logger("answerer")

# Below this cross-encoder relevance, nothing in the policy talks about the question.
ABSTAIN_BELOW = 0.004
TOP_K = 7
_TAG = re.compile(r"\[C(\d+)\]")
_MULTI_TAG = re.compile(r"\[\s*(C\s*\d+(?:\s*[,;/&]\s*(?:C\s*)?\d+)+)\s*\]")


def normalise_tags(text: str) -> str:
    """'[C15, C111]' -> '[C15][C111]' so every citation renders as its own chip."""
    return _MULTI_TAG.sub(lambda m: "".join(f"[C{n}]" for n in re.findall(r"\d+", m.group(1))), text or "")

NOT_IN_POLICY = {
    "en": "This isn't covered in this policy document - I couldn't find any clause about it. "
          "You may want to confirm with the insurer.",
    "hi": "यह जानकारी इस पॉलिसी दस्तावेज़ में नहीं दी गई है - मुझे इससे जुड़ा कोई क्लॉज़ नहीं मिला। "
          "कृपया बीमा कंपनी से पुष्टि कर लें।",
    "te": "ఈ విషయం ఈ పాలసీ డాక్యుమెంట్‌లో లేదు - దీనికి సంబంధించిన క్లాజ్ ఏదీ నాకు కనిపించలేదు. "
          "దయచేసి బీమా సంస్థతో నిర్ధారించుకోండి.",
}

SYSTEM = """You are PolicyLens, an assistant that explains ONE health-insurance policy to its policyholder.

Strict rules:
1. Answer ONLY from the numbered policy clauses provided. Never use outside knowledge, typical market terms or
   assumptions about "most policies".
2. Cite the clause tag, e.g. [C12], right after every statement it supports - one tag per bracket, like
   [C12][C15]. Only use tags that appear in the provided clauses.
3. If the clauses do not answer the question, set status="not_in_policy" and say plainly that this policy
   document does not cover it. If they answer only part of it, set status="partial" and say what is missing.
4. Be concrete: amounts, percentages, waiting periods, conditions, exceptions. Mention important conditions
   (waiting periods, sub-limits, co-payment) that change the answer.
5. Write the "answer" in the requested language, in simple words, with short paragraphs or bullets (Markdown).
   Keep clause tags like [C12] unchanged. Write "answer_en" as the same answer in English.
6. "claims" lists each factual statement of answer_en separately (in English), restated as close as possible to
   the clause wording, with the clause tags supporting it.
"""


class AnswerClaimOut(BaseModel):
    text_en: str = Field(description="One factual statement from the answer, in English.")
    clauses: list[str] = Field(description="Clause tags supporting it, e.g. ['C12'].")


class AnswerOut(BaseModel):
    status: Literal["answered", "partial", "not_in_policy"]
    answer: str = Field(description="The answer in the requested language, citing clause tags like [C12].")
    answer_en: str = Field(description="The same answer in English, with the same clause tags.")
    claims: list[AnswerClaimOut]
    follow_up_questions: list[str] = Field(description="Up to 3 short follow-up questions, in the requested language.")


@dataclass
class AnswerResult:
    status: str
    answer: str
    answer_en: str
    citations: list[dict[str, Any]]
    faithfulness: dict[str, Any]
    follow_ups: list[str]
    retrieval: dict[str, Any]
    timings: dict[str, Any]
    model: str | None
    language: str
    extra: dict[str, Any] = field(default_factory=dict)


def format_clauses(clauses: list[ClauseRecord]) -> str:
    blocks = []
    for c in clauses:
        pages = f"page {c.page_start}" if c.page_start == c.page_end else f"pages {c.page_start}-{c.page_end}"
        ref = f"Clause {c.clause_ref}" if c.clause_ref else "Unnumbered clause"
        context = " > ".join(p for p in (c.section_path, c.heading) if p)
        blocks.append(f"[C{c.ordinal}] {ref}, {pages}" + (f" | {context}" if context else "") + f"\n{c.text}")
    return "\n\n".join(blocks)


def citation_for(clause: ClauseRecord, claim_texts: list[str] | None = None) -> dict[str, Any]:
    """Citation payload for the UI: clause label, page, highlight boxes and the most relevant sentence."""
    from app.services.text_match import token_overlap

    sentences = [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n+", clause.text) if len(s.strip()) > 20]
    quote = clause.text[:240]
    if sentences and claim_texts:
        quote = max(sentences, key=lambda s: max(token_overlap(s, t) for t in claim_texts))[:320]
    return {
        "ordinal": clause.ordinal, "tag": f"C{clause.ordinal}", "clause_ref": clause.clause_ref,
        "heading": clause.heading, "label": clause.label, "page": clause.page_start, "page_end": clause.page_end,
        "quote": quote, "bboxes": list(clause.bboxes),
    }


def _history_text(history: list[tuple[str, str]]) -> str:
    if not history:
        return "(no earlier messages)"
    lines = []
    for role, text in history[-6:]:
        lines.append(f"{'User' if role == 'user' else 'PolicyLens'}: {text[:600]}")
    return "\n".join(lines)


def answer_question(document_id: int, question: str, language: str = "en",
                    history: list[tuple[str, str]] | None = None, user_id: int | None = None,
                    cache: bool = False) -> AnswerResult:
    history = history or []
    timings: dict[str, Any] = {}
    t0 = time.perf_counter()

    t = time.perf_counter()
    english = to_english_query(question, user_id)
    timings["translate_ms"] = round((time.perf_counter() - t) * 1000)

    search_query = english or question
    extra: list[str] = []
    if english:
        extra.append(question)
    last_user = next((text for role, text in reversed(history) if role == "user"), None)
    if last_user and len(search_query.split()) <= 7:
        extra.append(f"{last_user} {search_query}")  # short follow-up: carry the previous topic

    t = time.perf_counter()
    result: RetrievalResult = retrieve(document_id, search_query, k=TOP_K, extra_queries=extra or None)
    timings["retrieval_ms"] = round((time.perf_counter() - t) * 1000)
    timings["retrieval_stages_ms"] = result.timings_ms
    retrieval_info = {
        "query": search_query,
        "items": [{"ordinal": i.clause.ordinal, "label": i.clause.label, "page": i.clause.page_start,
                   "bm25_rank": i.bm25_rank, "dense_rank": i.dense_rank, "rerank": i.rerank} for i in result.items],
    }
    clauses = [i.clause for i in result.items]
    by_ordinal = {c.ordinal: c for c in clauses}

    if not clauses or result.best_score < ABSTAIN_BELOW:
        timings["total_ms"] = round((time.perf_counter() - t0) * 1000)
        text = NOT_IN_POLICY.get(language, NOT_IN_POLICY["en"])
        return AnswerResult("not_in_policy", text, NOT_IN_POLICY["en"], [], score_claims([], {}), [],
                            retrieval_info, timings, None, language, {"abstained_before_llm": True})

    prompt = (
        f"Answer language: {LANGUAGE_NAMES.get(language, 'English')}\n\n"
        f"Earlier conversation:\n{_history_text(history)}\n\n"
        f"Question: {question}\n" + (f"(English: {english})\n" if english else "") +
        f"\nPOLICY CLAUSES\n\n{format_clauses(clauses)}"
    )
    t = time.perf_counter()
    out, meta = generate_json(prompt=prompt, schema=AnswerOut, purpose="chat_answer", system=SYSTEM,
                              user_id=user_id, temperature=0.2, cache=cache)
    timings["generation_ms"] = round((time.perf_counter() - t) * 1000)

    # Keep only citations to clauses we actually retrieved.
    def clean(text: str) -> str:
        text = normalise_tags(text)
        return _TAG.sub(lambda m: m.group(0) if int(m.group(1)) in by_ordinal else "", text).replace("  ", " ")

    answer, answer_en = clean(out.answer), clean(out.answer_en)
    claims: list[ClaimInput] = []
    for c in out.claims:
        ordinals = [int(m) for tag in c.clauses for m in re.findall(r"\d+", tag) if int(m) in by_ordinal]
        claims.append(ClaimInput(c.text_en, ordinals))
    cited = sorted({int(m) for m in _TAG.findall(answer_en + " " + answer)} | {o for c in claims for o in c.clause_ordinals})
    citations = [citation_for(by_ordinal[o], [c.text for c in claims if o in c.clause_ordinals] or [answer_en])
                 for o in cited if o in by_ordinal]

    t = time.perf_counter()
    status = out.status
    faithfulness = score_claims(claims, {o: by_ordinal[o].text for o in by_ordinal}) if status != "not_in_policy" \
        else score_claims([], {})
    timings["faithfulness_ms"] = round((time.perf_counter() - t) * 1000)
    timings["total_ms"] = round((time.perf_counter() - t0) * 1000)
    log_event(log, "answered", document_id=document_id, status=status, citations=len(citations),
              faithfulness=faithfulness["score"], ms=timings["total_ms"], model=meta.model)
    return AnswerResult(status, answer, answer_en, citations, faithfulness, out.follow_up_questions[:3],
                        retrieval_info, timings, meta.model, language, {"cached": meta.cached})
