"""Metric functions shared by the PolicyLens evaluation scripts.

Relevance is judged against *evidence snippets* - short verbatim phrases copied
from the policy wording - so the evaluation set does not depend on how the
parser happens to split clauses into chunks. Text matching reuses the product's
own quote verifier (``app.services.text_match``) so both agree on what "contains" means.
"""

from __future__ import annotations

import re
import statistics
from collections.abc import Iterable, Sequence

from ml import common  # noqa: F401 - puts backend/ on sys.path
from app.services.text_match import contains_text, normalise


def contains_evidence(chunk_text: str, evidence: Sequence[str], min_token_overlap: float = 0.85) -> bool:
    """True when the chunk contains any evidence snippet (exactly or nearly)."""
    return any(contains_text(chunk_text, snippet, min_token_overlap) for snippet in evidence if snippet)


def relevance_flags(ranked_texts: Sequence[str], evidence: Sequence[str]) -> list[bool]:
    return [contains_evidence(t, evidence) for t in ranked_texts]


def hit_at_k(flags: Sequence[bool], k: int) -> float:
    return 1.0 if any(flags[:k]) else 0.0


def reciprocal_rank(flags: Sequence[bool], k: int = 10) -> float:
    for i, flag in enumerate(flags[:k]):
        if flag:
            return 1.0 / (i + 1)
    return 0.0


def evidence_recall_at_k(ranked_texts: Sequence[str], evidence: Sequence[str], k: int) -> float:
    """Share of evidence snippets found somewhere in the top-k chunks."""
    if not evidence:
        return 0.0
    top = ranked_texts[:k]
    found = sum(1 for snip in evidence if any(contains_evidence(t, [snip]) for t in top))
    return found / len(evidence)


def retrieval_summary(per_item: Iterable[dict], ks: Sequence[int] = (1, 3, 5)) -> dict:
    """Aggregate per-item dicts holding ``flags`` (list[bool]) and ``recall@5`` values."""
    items = list(per_item)
    if not items:
        return {}
    out: dict[str, float] = {"n": len(items)}
    for k in ks:
        out[f"hit@{k}"] = round(statistics.fmean(hit_at_k(i["flags"], k) for i in items), 4)
    out["mrr@10"] = round(statistics.fmean(reciprocal_rank(i["flags"], 10) for i in items), 4)
    if all("recall@5" in i for i in items):
        out["recall@5"] = round(statistics.fmean(i["recall@5"] for i in items), 4)
    return out


# --- answers -----------------------------------------------------------------

_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "twelve": "12", "fifteen": "15",
    "eighteen": "18", "twenty": "20", "twenty four": "24", "thirty": "30",
    "thirty six": "36", "forty eight": "48", "sixty": "60", "ninety": "90",
}


def _numbers_as_digits(text: str) -> str:
    text = normalise(text)
    for word, digit in sorted(_NUMBER_WORDS.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"\b{word}\b", digit, text)
    return text


def key_fact_match(answer: str, key_facts: Sequence[Sequence[str] | str]) -> float:
    """Share of key facts present in the answer.

    Each key fact is either a string or a list of accepted variants
    (for example ``["24 months", "2 years"]``). Number words are converted to
    digits on both sides before matching.
    """
    if not key_facts:
        return 1.0
    ans = _numbers_as_digits(answer)
    hits = 0
    for fact in key_facts:
        variants = [fact] if isinstance(fact, str) else list(fact)
        if any(_numbers_as_digits(v) in ans for v in variants):
            hits += 1
    return hits / len(key_facts)


def citation_hit(cited_pages: Iterable[int], cited_texts: Sequence[str],
                 expected_pages: Iterable[int], evidence: Sequence[str]) -> bool:
    """A citation is correct when it quotes the evidence or points at an expected page."""
    if any(contains_evidence(t, evidence) for t in cited_texts):
        return True
    return bool(set(cited_pages) & set(expected_pages))


# --- latency and classification ------------------------------------------------

def latency_stats(values_ms: Sequence[float | None]) -> dict:
    vals = sorted(v for v in values_ms if v is not None)
    if not vals:
        return {}

    def pct(p: float) -> float:
        idx = min(len(vals) - 1, max(0, round(p * (len(vals) - 1))))
        return round(vals[idx], 1)

    return {
        "n": len(vals),
        "mean_ms": round(statistics.fmean(vals), 1),
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "max_ms": round(vals[-1], 1),
    }


def classification_report(y_true: Sequence[str], y_pred: Sequence[str], labels: Sequence[str]) -> dict:
    """Accuracy, per-label precision/recall/F1 and the confusion matrix (rows = true, columns = predicted)."""
    from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

    labels = list(labels)
    matrix = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "labels": labels,
        "confusion_matrix": matrix,
        "per_label": {
            lab: {
                "precision": round(float(p), 4),
                "recall": round(float(r), 4),
                "f1": round(float(f), 4),
                "support": int(s),
            }
            for lab, p, r, f, s in zip(labels, precision, recall, f1, support)
        },
    }
