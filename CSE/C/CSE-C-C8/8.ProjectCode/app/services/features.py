"""PeerScope deterministic paper feature / quality-signal extraction."""
from __future__ import annotations

import re

EXPECTED = ["summary", "introduction", "related_work", "methodology",
            "experiments", "results", "discussion", "conclusion", "references"]

STOP = set(
    "the a an and or of to in on for with by as at from that this these those it its is are was were be been has have had will would can could should may might paper we our they their method model data results using used use study approach proposed based between within into over under more most such than then also et al fig figure table section".split()
)

METHOD_TERMS = ["neural", "transformer", "regression", "classification", "clustering",
                "svm", "random forest", "gradient boosting", "cnn", "rnn", "lstm",
                "evaluation", "experiment", "dataset", "baseline", "training",
                "validation", "cross-validation", "statistical", "bayesian", "optimization"]

TOPIC_HINTS = ["vision", "language", "nlp", "learning", "network", "security",
               "systems", "theory", "robotics", "data", "software", "hardware",
               "medical", "education", "graph", "speech", "retrieval", "mining"]


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z]{3,}", text)]


def extract_features(doc: dict) -> dict:
    text = doc.get("full_text", "")
    sections = doc.get("sections", {})
    words = re.findall(r"[A-Za-z0-9']+", text)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    avg_sent = round(sum(len(s.split()) for s in sentences) / max(len(sentences), 1), 2)

    present = [k for k in EXPECTED if k in sections]
    missing = [k for k in EXPECTED if k not in sections]
    short_sections = [k for k, v in sections.items() if v.get("word_count", 0) < 40]
    pct_short = round(100.0 * len(short_sections) / max(len(sections), 1), 1) if sections else 100.0

    title = doc.get("title", "")
    summary = doc.get("paper_summary", "")
    ref_count = doc.get("reference_count", 0)
    pages = max(doc.get("page_count", 0), 1)
    ref_density = round(ref_count / pages, 2)

    toks = _tokens(text)
    freq: dict[str, int] = {}
    for t in toks:
        if t not in STOP:
            freq[t] = freq.get(t, 0) + 1
    keywords = sorted(freq, key=lambda k: (-freq[k], k))[:15]

    low = text.lower()
    method_terms = sorted({m for m in METHOD_TERMS if m in low})
    topics = sorted({h for h in TOPIC_HINTS if h in low})

    struct = round(100.0 * len(present) / len(EXPECTED), 1)
    evidence = min(100.0, round(ref_density * 22 + (10 if "experiments" in sections or "results" in sections else 0), 1))
    method_sig = 100.0 if "methodology" in sections and sections["methodology"].get("word_count", 0) >= 120 else (
        70.0 if "methodology" in sections else (45.0 if method_terms else 25.0))
    present_sig = 100.0 if 12 <= avg_sent <= 26 and pct_short < 40 else (
        75.0 if 8 <= avg_sent <= 32 else 50.0)

    overall_struct = round(0.35 * struct + 0.25 * evidence + 0.25 * method_sig + 0.15 * present_sig, 1)

    return {
        "total_pages": doc.get("page_count", 0),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": avg_sent,
        "reference_count": ref_count,
        "reference_density": ref_density,
        "detected_sections": present,
        "missing_sections": missing,
        "num_detected_sections": len(present),
        "pct_short_sections": pct_short,
        "short_sections": short_sections,
        "title_length": len(title),
        "summary_length": len(summary),
        "has_methodology": "methodology" in sections,
        "has_evaluation": ("experiments" in sections or "results" in sections),
        "has_conclusion": "conclusion" in sections,
        "keywords": keywords,
        "methodology_terms": method_terms,
        "research_topics": topics,
        "structure_completeness": struct,
        "evidence_coverage": evidence,
        "method_clarity_signal": method_sig,
        "presentation_signal": present_sig,
        "overall_structural": overall_struct,
    }
