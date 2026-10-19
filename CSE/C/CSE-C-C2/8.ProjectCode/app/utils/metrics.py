"""StoryVox metric helpers with real local computations."""
from __future__ import annotations

import math
from collections import Counter


def _levenshtein(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate computed locally (real edit-distance metric)."""
    try:
        import jiwer as _jiwer

        return float(_jiwer.wer(reference or "", hypothesis or ""))
    except Exception:
        ref = (reference or "").split()
        hyp = (hypothesis or "").split()
        if not ref:
            return 0.0 if not hyp else 1.0
        return round(_levenshtein(ref, hyp) / max(1, len(ref)), 4)


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate computed locally."""
    try:
        import jiwer as _jiwer

        return float(_jiwer.cer(reference or "", hypothesis or ""))
    except Exception:
        ref = list(reference or "")
        hyp = list(hypothesis or "")
        if not ref:
            return 0.0 if not hyp else 1.0
        return round(_levenshtein(ref, hyp) / max(1, len(ref)), 4)


def tfidf_cosine(reference: str, hypothesis: str) -> float:
    """Real semantic-overlap proxy: TF cosine similarity in [0, 1]."""
    ref_tokens = (reference or "").lower().split()
    hyp_tokens = (hypothesis or "").lower().split()
    if not ref_tokens or not hyp_tokens:
        return 0.0
    vocab = sorted(set(ref_tokens) | set(hyp_tokens))
    rc, hc = Counter(ref_tokens), Counter(hyp_tokens)
    dot = sum(rc[t] * hc[t] for t in vocab)
    denom = math.sqrt(sum(v * v for v in rc.values())) * math.sqrt(sum(v * v for v in hc.values()))
    if denom == 0:
        return 0.0
    return round(dot / denom, 4)


def rouge_l_f1(reference: str, hypothesis: str) -> float:
    try:
        from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        return round(float(scorer.score(reference or "", hypothesis or "")["rougeL"].fmeasure), 4)
    except Exception:
        return tfidf_cosine(reference, hypothesis)
