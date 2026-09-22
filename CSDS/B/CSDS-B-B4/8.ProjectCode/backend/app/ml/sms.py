"""SMS / payment-note scam analysis: NLP model + scam-pattern rules -> verdict with highlighted phrases."""
from __future__ import annotations

import re
from typing import Any

import numpy as np

from app.services.sms_rules import detect_language, extract_entities, match_rules, rules_score

# Word tokens that keep Devanagari / Telugu vowel signs inside the word.
TOKEN_PATTERN = r"(?u)[\wऀ-ॿఀ-౿]{2,}"
DEFAULT_THRESHOLDS = {"scam": 0.7, "suspicious": 0.4}


def _merge_spans(spans: list[dict]) -> list[dict]:
    spans = sorted(spans, key=lambda s: (s["start"], -s["end"]))
    merged: list[dict] = []
    for s in spans:
        if merged and s["start"] <= merged[-1]["end"]:
            last = merged[-1]
            last["end"] = max(last["end"], s["end"])
            last["sources"] = sorted(set(last["sources"]) | set(s["sources"]))
            last["rules"] = sorted(set(last["rules"]) | set(s["rules"]))
        else:
            merged.append({**s, "sources": list(s["sources"]), "rules": list(s["rules"])})
    return merged


def model_terms(bundle: dict[str, Any], text: str, top: int = 6) -> list[tuple[str, float]]:
    """Word n-grams in this message that pushed the model towards 'scam' the most."""
    pipe = bundle["pipeline"]
    union = pipe.named_steps["features"]
    word_vec = dict(union.transformer_list)["word"]
    clf = pipe.named_steps["clf"]
    coef = clf.coef_.ravel()[: len(word_vec.vocabulary_)]
    row = word_vec.transform([text])
    vocab = word_vec.get_feature_names_out()
    contrib = [(vocab[j], float(row[0, j] * coef[j])) for j in row.indices]
    return sorted([c for c in contrib if c[1] > 0], key=lambda c: -c[1])[:top]


def analyze(bundle: dict[str, Any] | None, text: str) -> dict[str, Any]:
    text = text.strip()
    language, script = detect_language(text)
    hits = match_rules(text)
    r = rules_score(hits)
    if bundle is not None:
        p = float(bundle["pipeline"].predict_proba([text])[0, 1])
        thresholds = bundle.get("thresholds", DEFAULT_THRESHOLDS)
        terms = model_terms(bundle, text)
    else:  # model file missing - rules still protect the user
        p, thresholds, terms = r, DEFAULT_THRESHOLDS, []
    combined = 1.0 - (1.0 - p) * (1.0 - r)
    verdict = "scam" if combined >= thresholds["scam"] else "suspicious" if combined >= thresholds["suspicious"] else "safe"

    scam_type = None
    typed = [h for h in hits if h["category"]]
    if typed:
        scam_type = max(typed, key=lambda h: h["weight"])["category"]
    elif verdict != "safe" and bundle is not None and bundle.get("type_model") is not None:
        scam_type = str(bundle["type_model"].predict([text])[0])
    if verdict == "safe":
        scam_type = None

    spans: list[dict] = []
    for h in hits:
        if h["weight"] < 0.1:
            continue
        for start, end in h["spans"]:
            spans.append({"start": start, "end": end, "sources": ["rule"], "rules": [h["rule"]]})
    lowered = text.lower()
    for term, _ in terms:
        for m in re.finditer(re.escape(term), lowered):
            spans.append({"start": m.start(), "end": m.end(), "sources": ["model"], "rules": []})
    highlights = _merge_spans(spans) if verdict != "safe" else []
    for h in highlights:
        h["text"] = text[h["start"] : h["end"]]

    return {
        "text": text,
        "language": language,
        "script": script,
        "model_probability": round(p, 4),
        "rules_score": round(r, 4),
        "probability": round(combined, 4),
        "verdict": verdict,
        "scam_type": scam_type,
        "signals": [{"rule": h["rule"], "weight": h["weight"], "category": h["category"]} for h in sorted(hits, key=lambda h: -h["weight"])],
        "model_terms": [{"term": t, "weight": round(w, 4)} for t, w in terms],
        "highlights": highlights,
        "entities": extract_entities(text),
    }


def batch_scores(bundle: dict[str, Any], texts: list[str]) -> np.ndarray:
    """Combined model + rules score for many texts (used in evaluation and the simulator)."""
    p = bundle["pipeline"].predict_proba(texts)[:, 1]
    r = np.array([rules_score(match_rules(t)) for t in texts])
    return 1.0 - (1.0 - p) * (1.0 - r)
