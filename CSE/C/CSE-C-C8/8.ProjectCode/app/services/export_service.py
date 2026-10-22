"""PeerScope export service (JSON + human-readable PDF report)."""
from __future__ import annotations

import io
import json
from typing import Any


def analysis_to_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def analysis_to_pdf(result: dict[str, Any]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#0b3d62"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#0b3d62"))
    body = styles["BodyText"]
    story = []
    esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    story += [Paragraph("PeerScope — Paper Analysis Report", h1),
              Paragraph(f"File: {esc(result.get('filename',''))} &nbsp;&nbsp; Date: {esc(result.get('created_at',''))}", body),
              Spacer(1, 6),
              Paragraph("Disclaimer: PeerScope provides AI-assisted analysis for decision support. Final editorial judgment remains with a qualified human.", body),
              Spacer(1, 8)]
    paper = result.get("paper", {})
    story += [Paragraph("1. Paper Overview", h2),
              Paragraph(f"<b>Title:</b> {esc(paper.get('title',''))}", body),
              Paragraph(f"<b>Pages:</b> {paper.get('page_count')} &nbsp; <b>Words:</b> {paper.get('word_count')} &nbsp; <b>References:</b> {paper.get('reference_count')}", body),
              Paragraph(f"<b>Summary:</b> {esc((paper.get('paper_summary') or '')[:1200])}", body), Spacer(1, 6)]
    story += [Paragraph("2. Preliminary Assessment", h2),
              Paragraph(esc(result.get("overall_assessment", "")), body), Spacer(1, 4)]
    ml = result.get("ml_decision_signal", {})
    story += [Paragraph(f"Historical decision signal: {esc(str(ml.get('label')))} (confidence {ml.get('confidence')})", body),
              Paragraph(f"Structural score: {result.get('features', {}).get('overall_structural')}", body), Spacer(1, 6)]
    for key, title in (("strengths", "3. Strengths"), ("major_concerns", "4. Major Concerns"),
                       ("minor_concerns", "5. Minor Concerns"), ("recommendations", "6. Recommendations")):
        items = (result.get("review", {}) or {}).get(key, [])
        story.append(Paragraph(title, h2))
        for it in items:
            story.append(Paragraph(f"• {esc(it)}", body))
        story.append(Spacer(1, 4))
    story.append(Paragraph("7. Recommended Reviewers", h2))
    rows = [["Rank", "Reviewer", "Score", "Strength"]]
    for r in result.get("reviewers", [])[:5]:
        rows.append([str(r.get("rank")), esc(r.get("display_name", "")), str(r.get("score")), esc(r.get("match_strength", ""))])
    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b3d62")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                           ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    story += [t, Spacer(1, 6),
              Paragraph("Responsible use: AI output can contain errors; verify claims, conflicts, and novelty with human expertise.", body)]
    doc.build(story)
    return buf.getvalue()
