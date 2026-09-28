"""Text models: intent + topic, per-segment sentiment and keyword extraction (trained by ml/train.py)."""
import re
from functools import lru_cache

import joblib
import numpy as np

from ..config import MODELS_DIR

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def clean(text):
    text = re.sub(r"\{\{[^}]*\}\}", " ", str(text))
    return re.sub(r"\s+", " ", text).strip().lower()


@lru_cache(maxsize=1)
def _intent():
    return joblib.load(MODELS_DIR / "intent.joblib")


@lru_cache(maxsize=1)
def _sentiment():
    return joblib.load(MODELS_DIR / "sentiment.joblib")["model"]


@lru_cache(maxsize=1)
def _keywords():
    return joblib.load(MODELS_DIR / "keywords.joblib")


def models_ready():
    return all((MODELS_DIR / f).exists() for f in ("intent.joblib", "sentiment.joblib", "keywords.joblib"))


def sentences(text):
    return [s for s in (x.strip() for x in SENT_SPLIT.split(text or "")) if len(s.split()) >= 3]


def classify_intent(customer_turns, max_turns=4):
    """Intent of a call from what the customer says early on.

    Each sentence of the first customer turns is scored by the single-utterance model; sentences are weighted by
    confidence (squared max probability) and position, so the sentence that states the reason dominates.
    """
    bundle = _intent()
    model, cats = bundle["model"], bundle["categories"]
    sents = []
    for i, turn in enumerate(customer_turns[:max_turns]):
        for s in sentences(turn) or ([turn] if turn.strip() else []):
            sents.append((s, 1.0 / (1 + 0.35 * i)))
    if not sents:
        return None
    probs = model.predict_proba([clean(s) for s, _ in sents])
    w = np.array([pw for _, pw in sents]) * probs.max(axis=1) ** 2
    agg = (probs * w[:, None]).sum(axis=0) / max(w.sum(), 1e-9)
    order = np.argsort(agg)[::-1]
    classes = model.classes_
    best = classes[order[0]]
    evidence = sents[int(np.argmax(probs[:, order[0]]))][0]
    return {
        "intent": best, "confidence": round(float(agg[order[0]]), 3), "topic": cats.get(best, "OTHER"),
        "top": [{"intent": classes[j], "score": round(float(agg[j]), 3)} for j in order[:3]],
        "evidence": evidence,
    }


def sentiment_batch(texts):
    """[{label, score (-1..1), probs}] per text; score = P(positive) - P(negative)."""
    if not texts:
        return []
    model = _sentiment()
    probs = model.predict_proba([clean(t) for t in texts])
    idx = {c: i for i, c in enumerate(model.classes_)}
    out = []
    for p in probs:
        d = {c: round(float(p[i]), 3) for c, i in idx.items()}
        out.append({"label": max(d, key=d.get), "score": round(d["positive"] - d["negative"], 3), "probs": d})
    return out


# conversational filler that carries no information about what the call was about
FILLER = set("""thank thanks calling help great okay goodbye bye day good morning afternoon evening sure just right yes
hello please welcome lovely wonderful nice today speaking course pleasure happy glad really need want like know let
tell sorry certainly brilliant perfect excellent fine thing things time lot able alex sam jordan shows got
zero one two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty hundred""".split())


def keywords(text, k=8):
    vec = _keywords()
    x = vec.transform([clean(text)])
    if x.nnz == 0:
        return []
    terms = vec.get_feature_names_out()
    row = x.tocoo()
    ranked = sorted(zip(row.data, row.col), reverse=True)
    picked = []
    for _, j in ranked:
        t = terms[j]
        if any(w in FILLER for w in t.split()) or len(t) < 4:
            continue
        if any(t in p or p in t for p in picked):  # skip overlapping uni/bi-grams
            continue
        picked.append(t)
        if len(picked) == k:
            break
    return picked
