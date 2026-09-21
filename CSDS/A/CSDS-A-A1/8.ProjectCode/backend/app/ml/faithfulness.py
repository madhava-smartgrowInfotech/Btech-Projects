"""F9 - Faithfulness score: how well each answer claim is supported by the clauses it cites.

Each English claim is checked against sentence windows of its cited clauses with a local natural-
language-inference cross-encoder (``cross-encoder/nli-deberta-v3-xsmall``). The claim's support is
the highest entailment probability found. Numbers in a claim (months, %, rupee amounts) must also
appear in the cited text; a missing number halves the claim's support. The answer's score is the
mean claim support on a 0-100 scale.

The scorer is independent of the model that wrote the answer, runs offline and costs no API quota.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from app.ml.local_models import get_nli, nli_label_index
from app.services.text_match import normalise, token_overlap

_SENTENCE = re.compile(r"(?<=[.;:])\s+|\n+")
_NUMBER = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)(?!\w)")
MAX_WINDOWS = 8


@dataclass
class ClaimInput:
    text: str
    clause_ordinals: list[int]


def label_for(score: float | None) -> str:
    if score is None:
        return "not_applicable"
    if score >= 80:
        return "well_supported"
    if score >= 50:
        return "partly_supported"
    return "weakly_supported"


def _windows(texts: Sequence[str], claim: str) -> list[str]:
    windows: list[str] = []
    for text in texts:
        sentences = [s.strip() for s in _SENTENCE.split(text) if len(s.strip()) > 3]
        for i, sentence in enumerate(sentences):
            windows.append(sentence)
            if i + 1 < len(sentences):
                windows.append(f"{sentence} {sentences[i + 1]}")
        if len(text.split()) <= 180:
            windows.append(text)
    windows = [w[:1500] for w in windows]
    windows.sort(key=lambda w: token_overlap(w, claim), reverse=True)
    return windows[:MAX_WINDOWS]


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def score_claims(claims: Sequence[ClaimInput], clause_texts: dict[int, str]) -> dict:
    """Return {"score": 0-100 | None, "label": ..., "claims": [...]}."""
    if not claims:
        return {"score": None, "label": label_for(None), "claims": []}
    model = get_nli()
    labels = nli_label_index()
    ent_idx = labels.get("entailment", 1)
    con_idx = labels.get("contradiction", 0)

    pairs: list[tuple[str, str]] = []
    spans: list[tuple[int, int]] = []
    for claim in claims:
        evidence = [clause_texts[o] for o in claim.clause_ordinals if o in clause_texts]
        windows = _windows(evidence, claim.text) if evidence else []
        start = len(pairs)
        pairs.extend((w, claim.text) for w in windows)
        spans.append((start, len(pairs)))

    probs = np.zeros((0, 3))
    if pairs:
        logits = np.asarray(model.predict(pairs, batch_size=16, show_progress_bar=False, convert_to_numpy=True))
        logits = logits - logits.max(axis=1, keepdims=True)
        exp = np.exp(logits)
        probs = exp / exp.sum(axis=1, keepdims=True)

    details = []
    for claim, (start, end) in zip(claims, spans):
        evidence_text = " ".join(clause_texts.get(o, "") for o in claim.clause_ordinals)
        if start == end:
            details.append({"text": claim.text, "clauses": claim.clause_ordinals, "support": 0.0,
                            "contradiction": 0.0, "evidence": None, "numbers_ok": False,
                            "note": "No valid clause cited"})
            continue
        block = probs[start:end]
        best = int(block[:, ent_idx].argmax())
        entail = float(block[best, ent_idx])
        contra = float(block[:, con_idx].max())
        claim_numbers = _numbers(claim.text)
        evidence_numbers = _numbers(evidence_text)
        numbers_ok = claim_numbers.issubset(evidence_numbers) or not claim_numbers
        # Lexical backstop: a near-verbatim restatement of the clause is supported even when the
        # small NLI model is unsure about long legal sentences.
        overlap = token_overlap(claim.text, evidence_text)
        support = max(entail, 0.75 * overlap if overlap >= 0.8 else 0.0)
        if not numbers_ok:
            support *= 0.5
        details.append({
            "text": claim.text, "clauses": claim.clause_ordinals, "support": round(support, 3),
            "contradiction": round(contra, 3), "evidence": pairs[start + best][0][:400], "numbers_ok": numbers_ok,
            "note": None if numbers_ok else "A number in this statement was not found in the cited clause",
        })
    score = round(100 * float(np.mean([d["support"] for d in details])), 1)
    return {"score": score, "label": label_for(score), "claims": details}


def quick_support(claim: str, evidence: str) -> float:
    """Entailment probability of one claim against one evidence text (used in evaluation)."""
    result = score_claims([ClaimInput(claim, [0])], {0: evidence})
    return result["claims"][0]["support"] if result["claims"] else 0.0


def normalised_equal(a: str, b: str) -> bool:
    return normalise(a) == normalise(b)
