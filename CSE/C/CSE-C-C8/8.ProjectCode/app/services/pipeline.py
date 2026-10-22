"""PeerScope analysis pipeline: PDF -> features -> ML + review + literature + matching."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services import features as feat_svc
from app.services import literature as lit_svc
from app.services import matching as match_svc
from app.services import ml_predict as ml_svc
from app.services import pdf_extract as pdf_svc
from app.services import review_synthesis as rev_svc


def run_analysis(pdf_path: str | Path, filename: str, reviewers: list, session_options: dict | None = None) -> dict[str, Any]:
    opts = session_options or {}
    doc = pdf_svc.extract_pdf(pdf_path)
    feats = feat_svc.extract_features(doc)
    ml = ml_svc.predict_decision(doc.get("title", ""), doc.get("paper_summary", ""), doc.get("full_text", ""))
    review = rev_svc.llm_review(doc, feats)
    quality = rev_svc.review_quality(review)
    lit = lit_svc.retrieve_literature(doc.get("title", ""), feats.get("keywords", []), feats.get("research_topics", []))
    paper_prof = match_svc.paper_profile(doc.get("title", ""), doc.get("paper_summary", ""),
                                         feats.get("keywords", []), feats.get("methodology_terms", []),
                                         feats.get("research_topics", []))
    ranked = match_svc.match_reviewers(paper_prof, reviewers, (doc.get("full_text", "") or "")[:4000])

    # Apply UI filters
    if opts.get("active_only", True):
        ranked = [r for r in ranked if r.get("is_active")]
    min_score = float(opts.get("min_score", 0.0) or 0.0)
    ranked = [r for r in ranked if r.get("score", 0) >= min_score]
    topic = (opts.get("topic") or "").strip().lower()
    if topic:
        ranked = [r for r in ranked if topic in (r.get("expertise", "") + " " + " ".join(r.get("matching_topics", []))).lower()]
    method = (opts.get("method") or "").strip().lower()
    if method:
        ranked = [r for r in ranked if method in (r.get("expertise", "") + " " + " ".join(r.get("matching_methods", []))).lower()]
    top5 = ranked[:5]

    overall = review.get("overall_assessment", "")
    concerns = len(review.get("major_concerns", [])) + len(review.get("minor_concerns", []))
    result = {
        "product": "PeerScope",
        "filename": filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper": {"title": doc.get("title"), "paper_summary": doc.get("paper_summary"),
                  "page_count": doc.get("page_count"), "word_count": doc.get("word_count"),
                  "reference_count": doc.get("reference_count"), "sections": doc.get("sections"),
                  "pages_preview": [{"page": p["page"], "text": p["text"][:800]} for p in doc.get("pages", [])[:4]]},
        "features": feats,
        "ml_decision_signal": ml,
        "structural_assessment": {"overall_structural": feats.get("overall_structural"),
                                  "structure_completeness": feats.get("structure_completeness"),
                                  "evidence_coverage": feats.get("evidence_coverage"),
                                  "method_clarity_signal": feats.get("method_clarity_signal"),
                                  "presentation_signal": feats.get("presentation_signal")},
        "review": review,
        "review_quality": quality,
        "literature": lit,
        "reviewers": top5,
        "reviewer_pool_size": len(reviewers),
        "overall_assessment": overall,
        "concern_count": concerns,
        "recommendation_count": len(review.get("recommendations", [])),
        "top_reviewer": top5[0]["display_name"] if top5 else "",
        "disclaimer": "PeerScope provides AI-assisted analysis and reviewer matching for decision support. Final editorial judgment remains with a qualified human.",
        "responsible_use": ("AI output can contain errors. Scientific validity requires human expertise. "
                            "Reviewer recommendations are suggestions. Retrieved literature is context, not proof of novelty."),
    }
    return result
