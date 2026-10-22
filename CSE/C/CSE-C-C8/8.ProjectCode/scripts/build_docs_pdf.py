"""PeerScope product documentation PDF builder (reportlab; embeds real metrics + screenshots)."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "PeerScope_Product_Documentation.pdf"


def main() -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    metrics = {}
    mp = BASE / "models" / "metrics.json"
    if mp.exists():
        metrics = json.loads(mp.read_text(encoding="utf-8"))

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#0b3d62"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#0b3d62"))
    body = styles["BodyText"]
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            title="PeerScope Product Documentation", author="PeerScope")
    S = []
    A = S.append
    A(Paragraph("PeerScope — Product Documentation", h1))
    A(Paragraph("AI-assisted research-paper evaluation and reviewer recommendation for decision support.", body))
    A(Spacer(1, 6))
    secs = [
        ("1. Overview", "PeerScope is a local web application: upload a research-paper PDF and receive a preliminary assessment plus ranked reviewer recommendations with a transparent audit trail. Final editorial judgment always remains with a qualified human."),
        ("2. Product purpose", "Support editors, chairs, and authors with fast, explainable triage: extraction, structural checks, a historical decision signal, a structured AI-assisted critique, related-literature context, and auditable expertise matching."),
        ("3. Key features", "PDF extraction and section detection; trained paper-decision model with published metrics; deterministic quality signals; local language-model review pipeline (analyze → critique → synthesize); OpenAlex literature grounding with graceful fallback; reviewer directory with CSV import/export; auditable matching with conflict checks; history and JSON/PDF export."),
        ("4. User workflow", "Dashboard → Analyze Paper (upload PDF, set filters, Analyze) → inspect Paper Overview, Preliminary Assessment, Strengths, Concerns, Recommendations, Review Coverage, Related Literature, Recommended Reviewers, Audit Details → export JSON/PDF → manage Reviewers → review Model Performance and Analysis History."),
        ("5. Technology stack", "Python, FastAPI, Uvicorn, Pydantic, PyMuPDF, scikit-learn (TF-IDF + LogisticRegression), pandas, numpy, joblib, sentence-transformers (all-MiniLM-L6-v2) with TF-IDF fallback, Hugging Face Transformers (Qwen2.5-1.5B-Instruct, 0.5B fallback, CPU, lazy load), SQLite + SQLAlchemy, vanilla HTML/CSS/JS, reportlab, OpenAlex API."),
        ("6. Architecture summary", "Modular services: pdf extraction, feature extraction, ML prediction, local LLM, literature retrieval, review synthesis, reviewer matching, audit scoring, export. Pipeline: PDF → extraction → normalization → features → hybrid signals (ML + structural + LLM + literature) → synthesis → matching → ranking → dashboard/export."),
        ("7. Paper-processing pipeline", "Extension/MIME/size validation (20 MB), safe temp handling, PyMuPDF page text, whitespace normalization, heading-based section detection (title, summary, introduction, related work, methodology, experiments, results, discussion, conclusion, references), reference extraction, word/sentence counts, page previews."),
        ("8. ML component", "TF-IDF word (1–2) + char (3–5) features over title+text; LogisticRegression with class balancing; stratified split; fixed seed 42. Metrics (accuracy, precision, recall, F1, ROC-AUC, confusion matrix) are computed after training and shown in-app; never hardcoded."),
        ("9. AI review component", "Three-step local pipeline: ANALYZE (problem, contribution, approach, setup, claims, evidence), CRITIQUE (method clarity, evidence, completeness, reproducibility, limitations), SYNTHESIZE (structured assessment with evidence references). Cautious wording ('novelty signal', 'requires verification'); no invented experiments, data, or citations; unavailable-model state shown explicitly."),
        ("10. Reviewer matching method", "Paper and reviewer texts embedded (sentence-transformers, TF-IDF fallback); cosine similarity plus keyword/method overlap, availability factor, and conflict penalty. final = 0.55*expertise + 0.20*keyword + 0.15*method + 0.10*availability − conflict_penalty, normalized 0–100. Top 5 shown with filters (active, min score, topic, method)."),
        ("11. Auditability", "Every recommendation shows expertise similarity, topic overlap, method overlap, availability, conflict penalty, final score, matching terms, and a deterministic human-readable explanation derived from matching evidence."),
        ("12. Literature grounding", "OpenAlex related-work retrieval (top ~6) ranked by semantic similarity; titles, years, authors, links shown as supporting context only. Failures continue without RAG and record literature_retrieval_status=unavailable; nothing is fabricated."),
        ("13. How to run", "Double-click run.bat (automatic), or Docker (docker build -t peerscope . / docker run --rm -p 8408:8408 peerscope), or manual venv + pip install + uvicorn on 127.0.0.1:8408 and the web app (npm run dev) on 5408. Open http://localhost:5408. See HOW_TO_RUN.md."),
    ]
    for title, text in secs:
        A(Paragraph(title, h2))
        A(Paragraph(text, body))
        A(Spacer(1, 4))
    A(Paragraph("14. Actual model metrics", h2))
    if metrics and metrics.get("status") == "ok":
        rows = [["Metric", "Value"],
                ["Accuracy", str(metrics.get("accuracy"))],
                ["Precision (macro)", str(metrics.get("precision_macro"))],
                ["Recall (macro)", str(metrics.get("recall_macro"))],
                ["F1 (macro)", str(metrics.get("f1_macro"))],
                ["ROC-AUC", str(metrics.get("roc_auc"))],
                ["Test samples", str(metrics.get("test_samples"))],
                ["Dataset rows", str(metrics.get("dataset_rows"))],
                ["Dataset source", str(metrics.get("dataset_source")) + (" (synthetic fallback)" if metrics.get("synthetic_fallback") else "")],
                ["Model", str(metrics.get("model_type"))],
                ["Features", str(metrics.get("features"))],
                ["Trained at", str(metrics.get("trained_at"))]]
        t = Table(rows, colWidths=[55 * mm, 100 * mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b3d62")),
                               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                               ("FONTSIZE", (0, 0), (-1, -1), 9)]))
        A(t)
        A(Spacer(1, 4))
        A(Paragraph(f"Class distribution: {metrics.get('class_distribution')} · Labels: {metrics.get('labels')}", body))
    else:
        A(Paragraph("Metrics artifact not found. Run scripts/train_model.py to generate real metrics.", body))
    A(Spacer(1, 4))
    A(Paragraph("15. Example analysis screenshots", h2))
    A(Paragraph("Screenshots below are captured from the running application (scripts/capture_screenshots.py).", body))
    for name in ["01_dashboard.png", "02_analyze.png", "03_results.png", "05_reviewers.png", "06_model.png"]:
        p = BASE / "screenshots" / name
        if p.exists():
            try:
                A(Image(str(p), width=150 * mm, height=96 * mm, kind="proportional"))
                A(Paragraph(name, body))
                A(Spacer(1, 4))
            except Exception:
                A(Paragraph(f"{name} (could not embed)", body))
    A(PageBreak())
    A(Paragraph("16. Limitations and responsible use", h2))
    A(Paragraph("AI output can contain errors. Scientific validity requires human expertise. Recommendations are suggestions. "
                "Retrieved literature is context, not proof of novelty. Verify claims and conflicts independently. "
                "Do not use PeerScope as the sole basis for publication decisions. PeerScope never claims 100% accuracy and never replaces human reviewers.", body))
    A(Spacer(1, 6))
    A(Paragraph("PeerScope provides AI-assisted analysis and reviewer matching for decision support. Final editorial judgment remains with a qualified human.", body))
    doc.build(S)
    print(f"Documentation written -> {OUT}")


if __name__ == "__main__":
    main()
