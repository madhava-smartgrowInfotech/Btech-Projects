"""PeerScope review synthesis: deterministic grounding + 3-step local-LLM pipeline."""
from __future__ import annotations

import re
from typing import Any


def _sentences(text: str, n: int = 3) -> list[str]:
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if len(s.strip()) > 40]
    return parts[:n]


def deterministic_review(doc: dict, feats: dict) -> dict[str, Any]:
    text = doc.get("full_text", "")
    title = doc.get("title", "Untitled paper")
    sections = doc.get("sections", {})
    ev = _sentences(text, 4)
    strengths, major, minor, recs = [], [], [], []

    if feats.get("has_methodology"):
        strengths.append(f"Methodology section present ({sections['methodology'].get('word_count', 0)} words) describing the approach.")
    if feats.get("has_evaluation"):
        strengths.append("Evaluation/results material detected, giving the claims an empirical anchor.")
    if feats.get("reference_count", 0) >= 8:
        strengths.append(f"Reference list of {feats['reference_count']} entries suggests engagement with prior work.")
    if feats.get("num_detected_sections", 0) >= 5:
        strengths.append(f"Document structure covers {feats['num_detected_sections']} recognized sections.")
    if not strengths:
        strengths.append("Paper presents a central problem and proposed direction identifiable from the text.")

    if not feats.get("has_methodology"):
        major.append("Methodology clarity: no clearly detected methodology section; the approach cannot be reproduced from the current text.")
    elif sections.get("methodology", {}).get("word_count", 0) < 120:
        major.append("Methodology clarity: methodology section is short; add architecture/training details, hyperparameters, and data splits.")
    if not feats.get("has_evaluation"):
        major.append("Evidence: no clearly detected experiments/results section; claims lack verifiable empirical support in the extracted text.")
    if feats.get("reference_count", 0) < 5:
        major.append(f"Evidence coverage: only {feats.get('reference_count', 0)} references detected; broaden related-work grounding.")
    if feats.get("avg_sentence_length", 0) > 32:
        major.append("Clarity: average sentence length is high; long sentences reduce readability.")
    if feats.get("pct_short_sections", 0) >= 40 and sections:
        minor.append("Several detected sections are very short; expand or merge them.")
    for m in feats.get("missing_sections", []):
        if m not in ("summary",):
            minor.append(f"Missing or undetected section: '{m}'. If absent, consider adding it.")
    if feats.get("title_length", 0) < 20:
        minor.append("Title is unusually short; make the contribution explicit in the title.")
    if feats.get("summary_length", 0) < 200:
        minor.append("Opening summary is brief; state problem, method, results, and contribution explicitly.")

    recs = [
        "State the problem, contribution, method, datasets, metrics, and limitations in the opening summary.",
        "Expand the methodology with full reproducibility details (data, splits, settings, compute).",
        "Add ablations or baselines so each major claim maps to at least one table/figure.",
        "Discuss threats to validity and failure cases explicitly.",
        "Proofread for sentence length and define all terminology on first use.",
    ]

    coverage = {
        "Method": 90 if feats.get("has_methodology") else 30,
        "Evidence": min(95, 25 + feats.get("reference_count", 0) * 5 + (20 if feats.get("has_evaluation") else 0)),
        "Clarity": 85 if 8 <= feats.get("avg_sentence_length", 18) <= 28 else 60,
        "Reproducibility": 80 if (feats.get("has_methodology") and feats.get("has_evaluation")) else 35,
        "Novelty": 55,
        "Limitations": 70 if "discussion" in sections or "conclusion" in sections else 40,
    }
    evidence_refs = [f"p.{p['page']}: {(p['text'][:120] + '...') if len(p['text']) > 120 else p['text']}"
                     for p in doc.get("pages", [])[:3] if p.get("text", "").strip()]
    return {
        "overall_assessment": _overall(feats),
        "strengths": strengths[:6],
        "major_concerns": major[:6] or ["No critical blocking concern detected in structural signals; verify claims against the full text."],
        "minor_concerns": minor[:6],
        "methodology_assessment": _method_text(feats, sections),
        "evidence_assessment": _evidence_text(feats),
        "clarity_assessment": f"Average sentence length {feats.get('avg_sentence_length')} words; {feats.get('word_count')} words over {feats.get('total_pages')} pages.",
        "reproducibility_assessment": ("Core ingredients (method + evaluation) detected; add code/data statements." if feats.get("has_methodology") and feats.get("has_evaluation") else "Reproducibility information could not be verified from the extracted text."),
        "novelty_considerations": "Novelty signal is inconclusive from local text alone and requires verification against related literature (see Related Literature). No novelty is claimed as proven.",
        "recommendations": recs,
        "coverage": coverage,
        "evidence_references": evidence_refs,
        "evidence_sentences": ev,
        "source": "deterministic",
        "title": title,
    }


def _overall(feats: dict) -> str:
    s = feats.get("overall_structural", 0)
    if s >= 75:
        return "Strong preliminary structure with verifiable method and evaluation signals. Human review should verify claims."
    if s >= 55:
        return "Moderate preliminary structure; address the major concerns before editorial consideration."
    return "Early-stage draft signals; substantial revision of method, evidence, and presentation recommended."


def _method_text(feats: dict, sections: dict) -> str:
    if feats.get("has_methodology"):
        return f"Methodology section detected ({sections['methodology'].get('word_count', 0)} words). Verify architecture, data, and settings are fully specified."
    return "Methodology section could not be detected; methodological clarity cannot be verified."


def _evidence_text(feats: dict) -> str:
    return (f"{feats.get('reference_count', 0)} references detected "
            f"(density {feats.get('reference_density')}/page); "
            f"evaluation present: {bool(feats.get('has_evaluation'))}. "
            "Map each claim to a table/figure.")


ANALYZE_SYS = ("You are PeerScope, an AI assistant supporting human peer review. "
               "Analyze only what is in the provided paper text. Never invent experiments, data, or citations.")
CRITIQUE_SYS = ("You critique methodology, evidence, reproducibility, and clarity. "
                "Flag unsupported claims. Use cautious wording such as 'novelty signal' and 'requires verification'.")
SYNTH_SYS = ("Write a structured reviewer-style assessment with: Overall assessment, Strengths, Major concerns, "
             "Minor concerns, Methodology, Evidence, Clarity, Reproducibility, Novelty considerations, Recommendations. "
             "Reference pages/sections when possible. Say when something could not be verified.")


def llm_review(doc: dict, feats: dict) -> dict[str, Any]:
    """Run the 3-step local LLM pipeline; fall back to deterministic review with visible status."""
    from app.services import llm_service

    base = deterministic_review(doc, feats)
    if llm_service.ensure_llm() is None:
        base["llm_status"] = "unavailable"
        base["llm_note"] = ("Local AI model unavailable in this environment "
                            f"({(llm_service.llm_status().get('error') or 'not downloaded')}). "
                            "Showing deterministic structural review only.")
        return base
    excerpt = (doc.get("full_text", "") or "")[:6000]
    a = llm_service.generate(f"{ANALYZE_SYS}\nPAPER TITLE: {doc.get('title')}\nEXCERPT:\n{excerpt}\n\nList: problem, contribution, approach, setup, claims, evidence, strengths, weaknesses, missing info.", 512)
    b = llm_service.generate(f"{CRITIQUE_SYS}\nPAPER TITLE: {doc.get('title')}\nEXCERPT:\n{excerpt}\n\nCritique method clarity, evidence, completeness, reproducibility, limitations, consistency.", 512)
    c = llm_service.generate(f"{SYNTH_SYS}\nPAPER TITLE: {doc.get('title')}\nANALYSIS:\n{a.get('text','')}\nCRITIQUE:\n{b.get('text','')}\n\nProduce the structured assessment now.", 700)
    if c.get("status") != "ok" or not c.get("text"):
        base["llm_status"] = "error"
        base["llm_note"] = f"AI generation failed ({c.get('error', 'empty output')}); showing deterministic review."
        return base
    base["llm_status"] = "ok"
    base["llm_model"] = c.get("model")
    base["ai_synthesis"] = c["text"]
    base["ai_analysis_step"] = a.get("text", "")[:2000]
    base["ai_critique_step"] = b.get("text", "")[:2000]
    base["source"] = "deterministic+llm"
    return base


def review_quality(review: dict) -> dict[str, Any]:
    return {
        "num_strengths": len(review.get("strengths", [])),
        "num_major": len(review.get("major_concerns", [])),
        "num_minor": len(review.get("minor_concerns", [])),
        "num_recommendations": len(review.get("recommendations", [])),
        "num_evidence_refs": len(review.get("evidence_references", [])),
        "coverage": review.get("coverage", {}),
        "review_length_chars": sum(len(s) for s in (
            review.get("strengths", []) + review.get("major_concerns", [])
            + review.get("minor_concerns", []) + review.get("recommendations", []))),
    }
