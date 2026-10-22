"""Generate CareLens_AI_Product_Documentation.pdf from real metrics."""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
METRICS = BASE / "results" / "metrics.json"

def main():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    out = BASE / "CareLens_AI_Product_Documentation.pdf"
    m = json.loads(METRICS.read_text(encoding="utf-8")) if METRICS.exists() else {}
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out), pagesize=A4, topMargin=18*mm, bottomMargin=18*mm)
    story = []
    def h(t): story.append(Paragraph(f"<b>{t}</b>", styles["Heading1"])); story.append(Spacer(1, 4))
    def p(t): story.append(Paragraph(t, styles["BodyText"])); story.append(Spacer(1, 6))
    h("CareLens AI — Product Documentation")
    p("CareLens AI is a local web-based symptom-monitoring and preliminary health-guidance assistant. It combines hybrid retrieval (FAISS semantic search plus BM25 lexical search), cross-encoder reranking, and grounded local text generation with a software safety layer. All data stays on the user's machine in SQLite.")
    for title, body in [
        ("1. Product goals", "Provide understandable preliminary health information, show supporting evidence and match relevance, escalate emergencies clearly, and keep health data private and local."),
        ("2. Key features", "Secure accounts; conversational symptom input; top matching conditions; contributing-symptom evidence; health guidance; match-relevance indicator; emergency safety notices; consultation history with search, detail view and deletion."),
        ("3. User workflow", "Register, sign in, describe symptoms, review the grounded response with evidence cards and safety advice, revisit or delete past consultations, sign out."),
        ("4. System architecture", "USER SYMPTOMS -> preprocessing -> HyDE-style local expansion -> embeddings -> hybrid retrieval (FAISS + BM25) -> score fusion (0.65 semantic / 0.35 lexical, configurable) -> cross-encoder rerank (top-5) -> grounded generation -> safety filter -> UI + SQLite storage."),
        ("5. Technology stack", "Python, FastAPI, Uvicorn, SQLite, SQLAlchemy, Pydantic, Jinja2, Sentence Transformers (all-MiniLM-L6-v2), FAISS CPU, rank-bm25, cross-encoder ms-marco-MiniLM-L-6-v2, Flan-T5 small with evidence-based fallback, scikit-learn, pandas, numpy."),
        ("6. Dataset and preprocessing", "Normalized knowledge-base records with record_id, disease, symptoms, description, guidance, severity, red_flags, source. Text normalized, duplicates removed, symptom separators standardized, canonical retrieval text built as 'Disease: ... Symptoms: ... Description: ... Guidance: ...', validated and saved to data/processed/."),
        ("7. Hybrid retrieval", "Independent FAISS semantic path and BM25 lexical path, min-max normalized and fused with configurable weights. Candidate pool of ~15, reranked to top-5."),
        ("8. Query expansion", "Rule-based local HyDE-style step: normalizes the query and constructs a concise hypothetical medical-information representation ('Medical symptom presentation involving ...') used alongside the original query. No external API, no separate trained model."),
        ("9. FAISS / BM25 / reranking", "FAISS IndexFlatIP over L2-normalized embeddings (cosine-equivalent). BM25Okapi over tokenized retrieval texts. Cross-encoder ms-marco-MiniLM-L-6-v2 reranks candidates; falls back to hybrid order offline. Raw scores are translated to a simple match-relevance display."),
        ("10. Response generation & safety", "Flan-T5 answers only from retrieved context with instructions to avoid definitive diagnosis and prescriptions, note uncertainty, and recommend professional care. A deterministic evidence-based fallback assembles the same content if generation is unavailable. A rule layer flags emergency patterns (chest pain, breathing difficulty, bleeding, unconsciousness, stroke-like signs, anaphylaxis, self-harm, seizures) and always shows a non-diagnosis disclaimer."),
        ("11. Authentication & database", "SQLite via SQLAlchemy; bcrypt password hashing; signed token sessions in HttpOnly cookies; per-user ownership enforced on all history endpoints; input validation throughout."),
        ("12. How to run", "Double-click run.bat (recommended), or use Docker (run-docker.bat), or follow HOW_TO_RUN.md Method C for manual setup. The app binds to 127.0.0.1 and opens http://localhost:8000."),
        ("13. Limitations & responsible use", "Preliminary information only, not a diagnosis; knowledge base is limited; similarity is not medical probability; never prescribe medication. In emergencies seek immediate professional care."),
    ]:
        h(title); p(body)
    h("14. Evaluation methodology and measured results")
    if m:
        p("Evaluation runs on a held-out record per condition (one random record per disease), querying with its symptom list and mapping the top-ranked retrieved disease to the expected label. Metrics below are the actual outputs of scripts/evaluate.py.")
        for k in ["n_test","top1_accuracy","top3_accuracy","recall_at_3","macro_precision","macro_recall","macro_f1","mrr_at_3","mean_latency_ms","embedding_mode","reranker_available","generator_available"]:
            p(f"{k}: {m.get(k)}")
    else:
        p("No metrics file found. Run scripts/evaluate.py to generate results/metrics.json before regenerating this PDF.")
    doc.build(story)
    print("Wrote", out)

if __name__ == "__main__":
    main()
