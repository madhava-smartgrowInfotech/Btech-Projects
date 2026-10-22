"""PeerScope auditable reviewer-expertise matching."""
from __future__ import annotations

import re

import numpy as np

from app.config import MATCH_WEIGHTS
from app.services.embeddings import cosine, embed_texts


def _split(v: str | None) -> list[str]:
    if not v:
        return []
    return [p.strip().lower() for p in re.split(r"[,;|\n]+", v) if p.strip()]


def _overlap(a: list[str], b: list[str]) -> tuple[float, list[str]]:
    if not a or not b:
        return 0.0, []
    sa, sb = set(a), set(b)
    hits = sorted(sa & sb)
    # partial substring hits
    for x in sa:
        for y in sb:
            if x != y and (x in y or y in x) and x not in hits and y not in hits:
                hits.append(f"{x}~{y}")
    denom = max(len(sa), len(sb))
    return round(min(1.0, len(hits) / denom + 0.1 * len(hits) / max(denom, 1)), 4), hits


def paper_profile(title: str, summary: str, keywords: list[str], methods: list[str], topics: list[str]) -> dict:
    text = " ".join([title or "", summary or "", " ".join(keywords or []),
                     " ".join(methods or []), " ".join(topics or [])])
    return {"text": text, "keywords": [k.lower() for k in (keywords or [])],
            "methods": [m.lower() for m in (methods or [])],
            "topics": [t.lower() for t in (topics or [])]}


def reviewer_profile(r) -> dict:
    kw = _split(r.keywords) + _split(r.research_topics)
    text = " ".join([r.expertise_description or "", r.research_topics or "",
                     r.methods or "", r.keywords or "", r.publication_titles or ""])
    return {"text": text, "keywords": kw, "methods": _split(r.methods),
            "topics": _split(r.research_topics)}


def detect_conflict(paper_text: str, paper_title: str, r) -> dict:
    low = f"{paper_text[:3000]} {paper_title}".lower()
    terms = [t for t in _split(r.conflict_terms) if t]
    hits = [t for t in terms if t and t in low]
    name_hit = bool(r.display_name and r.display_name.lower().split()[0] in low and len(r.display_name.split()[0]) > 3 and r.display_name.lower() in low)
    aff_hit = bool(r.affiliation and len(r.affiliation) > 4 and r.affiliation.lower() in low)
    conflicted = bool(hits or name_hit or aff_hit)
    reason = ""
    if hits:
        reason = f"Conflict term match: {', '.join(hits[:3])}."
    elif name_hit:
        reason = "Reviewer name appears in the paper text."
    elif aff_hit:
        reason = "Reviewer affiliation appears in the paper text."
    return {"conflicted": conflicted, "reason": reason, "terms": hits}


def match_reviewers(paper: dict, reviewers: list, paper_text_extra: str = "") -> list[dict]:
    texts = [paper["text"]] + [reviewer_profile(r)["text"] or " " for r in reviewers]
    try:
        vecs = embed_texts(texts)
        pv = vecs[0]
        sims = []
        for v in vecs[1:]:
            try:
                sims.append(max(0.0, cosine(np.asarray(pv, dtype=float), np.asarray(v, dtype=float))))
            except Exception:
                sims.append(0.0)
    except Exception:
        sims = [0.0] * len(reviewers)

    w = MATCH_WEIGHTS
    ranked = []
    for r, sim in zip(reviewers, sims):
        rp = reviewer_profile(r)
        kw_s, kw_hits = _overlap(paper["keywords"], rp["keywords"])
        m_s, m_hits = _overlap(paper["methods"] + paper["topics"], rp["methods"] + rp["topics"])
        maxload = max(int(r.maximum_load or 5), 1)
        avail = max(0.0, min(1.0, 1.0 - (int(r.current_load or 0) / maxload)))
        conf = detect_conflict(paper_text_extra, "", r)
        penalty = float(w["conflict_penalty"]) if conf["conflicted"] else 0.0
        raw = (w["expertise_similarity"] * sim + w["keyword_score"] * kw_s
               + w["method_score"] * m_s + w["availability_score"] * avail - penalty)
        score100 = round(max(0.0, min(100.0, raw * 100)), 1)
        strength = "Strong" if score100 >= 65 else ("Good" if score100 >= 45 else ("Possible" if score100 >= 25 else "Weak"))
        expl = _explain(sim, kw_hits, m_hits, avail, conf)
        ranked.append({
            "reviewer_id": r.id, "display_name": r.display_name, "affiliation": r.affiliation or "",
            "expertise": (r.expertise_description or "")[:400],
            "score": score100, "match_strength": strength,
            "matching_topics": kw_hits[:8], "matching_methods": m_hits[:8],
            "availability": {"current_load": r.current_load, "maximum_load": r.maximum_load,
                             "score": round(avail, 3), "available": bool(r.is_active) and avail > 0},
            "is_active": bool(r.is_active),
            "conflict": conf,
            "breakdown": {"expertise_similarity": round(float(sim), 4), "keyword_score": kw_s,
                          "method_score": m_s, "availability_score": round(avail, 4),
                          "conflict_penalty": round(penalty, 4),
                          "weights": dict(w)},
            "explanation": expl,
        })
    ranked.sort(key=lambda d: d["score"], reverse=True)
    for i, d in enumerate(ranked, start=1):
        d["rank"] = i
    return ranked


def _explain(sim: float, kw: list, m: list, avail: float, conf: dict) -> str:
    if conf["conflicted"]:
        return f"Penalized: {conf['reason']} Verify before assigning."
    bits = []
    if sim >= 0.45:
        bits.append("semantic expertise closely matches the paper")
    elif sim >= 0.25:
        bits.append("semantic expertise partially matches the paper")
    else:
        bits.append("limited semantic overlap with the paper")
    if kw:
        bits.append(f"overlapping terms: {', '.join(kw[:4])}")
    if m:
        bits.append(f"shared methods/topics: {', '.join(m[:4])}")
    bits.append(f"availability {'good' if avail >= 0.5 else 'limited'}")
    return "Match because " + "; ".join(bits) + "."
