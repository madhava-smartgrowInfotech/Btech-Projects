"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os
import tempfile

from PIL import Image
from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"


def crop(name, box, tag):
    """Crop a real screenshot to the part that matters on a slide (written to the temp folder, source untouched)."""
    out = os.path.join(tempfile.gettempdir(), f"c12_deck_{tag}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    E, KB, G, SF = F.ENV, F.KB, F.GEN, F.SAF
    r = F.ret
    s4, s3, s2, s1p, s1l = "S4_lay_language_60", "S3_two_symptoms_leave_one_out_176", "S2_verbatim_leave_one_out_176", "S1_shipped_protocol_30", "S1_leave_one_out_30"
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a local hybrid RAG pipeline from symptom text to a grounded, safety-checked answer",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how SymptoTrackAI, implemented as the CareLens AI web application, is designed and built: data, models, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and knowledge base"), ("03", "Preprocessing and models"), ("04", "Configuration and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "People turn to web search or general chatbots for symptoms and get generic, frightening or ungrounded answers, with no source shown and no record of earlier episodes.", K.ORANGE, "!"),
        ("Proposed system", "Retrieve matching medical records with FAISS and BM25, fuse and rerank them, build the answer only from those records, flag emergencies by rules and save each consultation privately.", K.BLUE, "i"),
        ("Base paper link", "Madhury and Ramesh combine RAG, FAISS and a web app with a stored log but report no numbers. We keep the product idea, add BM25, a reranker, safety rules and measurements. Results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, b_, col, gl, body_size=18)
    notes[3] = "One-minute recap of Review 1: the access and misinformation problem, our hybrid approach, and how the base paper relates (same idea, no numbers, fewer components)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.1, 5.6)
    K.text(s, 8.0, 1.5, 4.7, 5.3, [
        ("**Layers**", {"space_after": 8}),
        (f"Presentation: React 19 and Vite web app (port {F.WEB_PORT}), 8 pages.", {"bullet": True}),
        (f"Application: FastAPI (port {F.API_PORT}), 10 routes: auth, chat, history, about, health.", {"bullet": True}),
        ("RAG pipeline: nine modules under app/rag, loaded once as a lazy singleton.", {"bullet": True}),
        ("Data: SQLite (users, consultations), FAISS and BM25 index files, the knowledge base JSON and CSV.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[4] = "All routes live in app/routes. The RAG pipeline is one class in app/rag/pipeline.py; each stage is its own module so it can be tested alone. Storage is local."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("Symptom text", K.NAVY), ("HyDE-style expansion", K.PURPLE), ("FAISS + BM25", K.PURPLE), ("Fusion 0.65 / 0.35", K.GREEN),
                                      ("Cross-encoder rerank", K.ORANGE), ("Grounded answer", K.BLUE), ("Safety + store", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One pipeline", "Pipeline.answer() runs every stage in order, so the web app, the tests and the measurement script exercise the same code."),
                                 ("Graceful fallbacks", "No MiniLM: TF-IDF embeddings. No reranker: hybrid order. No generator: an evidence-based answer. The app keeps working offline."),
                                 ("Measured, not typed", "scripts/measure_metrics.py writes every reported number to docs/metrics/metrics.json; figures are regenerated from it.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 3.6)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=20, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.9, 3.4, 2.7, b_, size=17, color=K.TXT)
    notes[5] = "The three design principles: one pipeline, honest fallbacks, and numbers that come from a script."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Knowledge base and probe sets")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{KB['records']}", "records in the knowledge base", K.BLUE), (f"{KB['conditions']}", "conditions, 4 to 6 records each", K.GREEN),
                                   (f"{KB['symptom_vocabulary']}", "distinct symptom phrases", K.ORANGE), (f"{KB['distinct_description_guidance_pairs']}", "description / guidance pairs: one per condition", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f07_kb_composition.png"), 0.6, 2.9, 6.6, 3.5)
    K.text(s, 7.5, 2.95, 5.2, 3.9, [
        ("No public symptom-disease dataset was available, so prepare_data.py writes a hand-made table of 30 conditions with six random symptom-subset variants each (seed 42). It is labelled synthetic in every record.", {"bullet": True}),
        (f"Severity mix: {KB['severity']['moderate']} moderate, {KB['severity']['low']} low, {KB['severity']['high']} high, {KB['severity']['emergency']} emergency records.", {"bullet": True}),
        ("Probe sets written by the team: 60 lay-language descriptions (2 per condition), 15 out-of-base complaints, 40 emergency and 30 non-emergency texts.", {"bullet": True}),
    ], size=14, color=K.INK, space_after=10)
    K.text(s, 0.6, 6.45, 6.6, 0.5, "Records per condition and severity of the synthetic base.", size=12, color=K.TXT, align="c", italic=True)
    notes[6] = ("Be frank: the knowledge base is synthetic and written by the team, not clinically reviewed, and all records of a condition share one description and guidance text. "
                "That makes retrieval of the condition easy and is why every probe set here is also team-written and small.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing and query expansion")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_retrieval.png"), 0.6, 1.35, 6.9, 5.45)
    K.text(s, 7.8, 1.5, 4.9, 5.2, [
        ("1  Knowledge base: lower-case symptoms, collapse spaces, drop duplicates", {}),
        ("2  Each record becomes 'Disease: .. Symptoms: .. Description: .. Guidance: ..'", {}),
        ("3  Query: lower-case, collapse whitespace, ? ! ; become full stops", {}),
        ("4  Split on commas, 'and', 'with'; keep up to 8 fragments", {}),
        ("5  Wrap in a fixed 'medical symptom presentation' template (HyDE-style)", {}),
        ("6  Embed and search the original text plus the template", {}),
        ("Honest finding: the template is not a model, and removing it scored as high or higher in every set we measured.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=15, color=K.INK, space_after=9)
    notes[7] = "The expansion is rule based. On our lay-language probes top-1 was 0.967 with it and 1.000 without it, so the term HyDE is used loosely here and the benefit is not shown."

    # ---- 8 models
    s = S[7]
    set_title(s, "Models used")
    wipe(s)
    rows = [["Component", "Configuration", "Role"],
            ["Dense retriever", "all-MiniLM-L6-v2, 384-d, normalised, FAISS IndexFlatIP (exact); TF-IDF 384-d fallback", "semantic similarity"],
            ["Lexical retriever", "BM25Okapi (rank-bm25) over [a-z0-9] tokens of the record text", "exact symptom words"],
            ["Reranker", "cross-encoder/ms-marco-MiniLM-L-6-v2 on 15 query-record pairs", "precision at the top 5"],
            ["Generator", "google/flan-t5-small via transformers, 220 new tokens, greedy; evidence-based fallback", "grounded answer text"]]
    K.table(s, 0.6, 1.4, [2.4, 6.0, 3.73], rows, font_size=14, row_h=0.74, first_bold=True)
    K.tile(s, 0.6, 5.65, 3.8, 1.2, "384", "embedding dimensions", K.BLUE, vsize=26)
    K.tile(s, 4.7, 5.65, 3.8, 1.2, "0", "models trained: all four are used pre-trained", K.GREEN, vsize=26)
    K.tile(s, 8.8, 5.65, 3.93, 1.2, "No GPU", "everything runs on a CPU", K.ORANGE, vsize=26)
    notes[8] = "Four pre-trained components with separate jobs. Nothing is fine-tuned in this project; the contribution is the pipeline, the safety layer and the measurement."

    # ---- 9 configuration
    s = S[8]
    set_title(s, "Pipeline configuration and parameter analysis")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Candidates and output", f"{F.CANDIDATE_K} per retriever, fused, {F.TOP_K} records kept after the cross-encoder"],
            ["Fusion", f"min-max per retriever, then {F.FUSION_WEIGHTS[0]} x semantic + {F.FUSION_WEIGHTS[1]} x lexical (environment-configurable)"],
            ["Relevance label", "reranker score min-max over the pool; Strong >= 0.66, Moderate >= 0.33, else Weak"],
            ["Limits", "query 3 to 2,000 characters; session token 1,440 minutes; HS256 cookie"],
            ["Machine", f"{E['cpu']}, {E['ram_gb']} GB RAM; Python {E['python']}; no training step"]]
    K.table(s, 0.6, 1.4, [2.6, 9.53], rows, font_size=14, row_h=0.55, first_bold=True)
    K.picture(s, F.fig("f09_hyde_effect.png"), 0.6, 4.85, 5.6, 2.2)
    K.text(s, 6.5, 5.0, 6.2, 1.9, f"Parameter check: expansion on or off. Lay-language top-1 {r('hybrid_rerank', s4):.3f} with it and {r('hybrid_rerank_nohyde', s4):.3f} without; two-symptom queries {r('hybrid_rerank', s3):.3f} and {r('hybrid_rerank_nohyde', s3):.3f}. The weights 0.65 / 0.35 were taken from the project configuration and not tuned.", size=15, color=K.TXT)
    notes[9] = "Settings are read from app/config.py. The fusion weights were not tuned, and the expansion shows no gain in our measurements."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: safety layer and relevance")
    wipe(s)
    K.picture(s, F.diag("11_safety_decision_flow.png"), 0.6, 1.3, 5.2, 5.6)
    K.text(s, 6.2, 1.5, 6.5, 5.3, [
        (f"**Emergency.** {SF['n_rules']} regex rules (chest pain, breathing, bleeding, unconsciousness, stroke signs, allergic reaction, self-harm, sudden neurological signs, seizure, severe abdominal pain) prepend an urgent notice.", {"bullet": True, "space_after": 9}),
        (f"**Caution.** {SF['n_caution_keywords']} keywords such as pregnant, infant, bleeding show a caution banner.", {"bullet": True, "space_after": 9}),
        ("**Filter.** Five banned phrases (take ibuprofen, dosage, prescribe ...) are replaced in the answer text.", {"bullet": True, "space_after": 9}),
        ("**Relevance.** Reranker scores are min-max scaled, so the top record always reads 100%.", {"bullet": True, "space_after": 9}),
        ("**Always.** A non-diagnosis disclaimer on every answer.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[10] = "The safety layer is software rules, not a clinical triage model. We measure it later: it catches literal wording and misses paraphrases. The 100 percent relevance is a display artefact we also measure."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.2, 5.6)
    rows = [["Module", "Role"], ["query_expansion", "normalise + template"], ["embeddings", "MiniLM / TF-IDF"], ["faiss_store", "exact inner-product index"], ["bm25_store", "lexical index"],
            ["hybrid_retriever", "min-max fusion"], ["reranker", "cross-encoder, relevance"], ["generator", "Flan-T5 / fallback answer"], ["safety", "rules + answer filter"], ["pipeline", "orchestration, labels"]]
    K.table(s, 7.1, 1.4, [2.4, 3.23], rows, font_size=13, row_h=0.5)
    notes[11] = "Level-1 data flow: the symptom text becomes a retrieval query, the records are fused and reranked, the answer is checked by the safety layer and stored."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.4, 4.2)
    K.picture(s, F.diag("06_uml_class.png"), 7.2, 1.3, 5.5, 5.65)
    K.text(s, 0.6, 5.75, 6.4, 1.2, "Two SQLite tables: users and consultations (one user, many consultations, cascade delete). A consultation stores the retrieved evidence as JSON text, so history never depends on the index.", size=13, color=K.TXT, italic=True)
    notes[12] = "Two tables. Each consultation is a frozen snapshot of the answer and its evidence; users can only read or delete their own rows."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Backend", f"Python {E['python']}, FastAPI {E['fastapi']}, Uvicorn, Pydantic v2, SQLAlchemy {E['sqlalchemy']}, SQLite, bcrypt, PyJWT"],
            ["Retrieval", f"sentence-transformers {E['sentence_transformers']} (all-MiniLM-L6-v2, cross-encoder), faiss-cpu {E['faiss']}, rank-bm25"],
            ["Generation", f"PyTorch {E['torch']}, Transformers {E['transformers']}, google/flan-t5-small"],
            ["Data and ML utilities", f"scikit-learn {E['scikit_learn']} (TF-IDF fallback, metrics), NumPy, pandas"],
            ["Front end", "React 19, Vite 8, react-router 7, Recharts, Framer Motion, GSAP (port 5412)"],
            ["Testing", "pytest, FastAPI TestClient, smoke-test script, Playwright browser walk"],
            ["Packaging", "run.bat (venv, install, index build, both servers); Dockerfile + docker-compose with nginx"]]
    K.table(s, 0.6, 1.5, [3.2, 8.93], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = f"Python {E['python']} on Windows. Everything is open source; the transformers 5 line matters later: it removed the task the generator relies on."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Knowledge base and indexes (FAISS, BM25)", "Done", f"{KB['records']} records, {KB['conditions']} conditions; synthetic"],
            ["Hybrid retrieval, fusion and cross-encoder", "Done", f"lay-language top-1 {r('hybrid_rerank', s4):.3f} (n = 60)"],
            ["Answer generation", "Done, 1 defect", f"Flan-T5 output echoes its prompt ({G['echo_answers']}/{G['n']}); fallback answer works"],
            ["Safety rules and filter", "Done, limits", f"{SF['true_emergency']}/{SF['n_pos']} emergencies flagged; paraphrases 0/{SF['by_group_pos']['paraphrase']['n']}"],
            ["Accounts, history, search, delete", "Done", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks; 21 screenshots"],
            ["React web app and legacy pages", "Done", "8 pages, dark mode, mobile layout"],
            ["Trends and progression over time", "Not done", "history list only; no timeline or trend analysis"],
            ["Real medical knowledge base, user study", "Not done", "synthetic base; no clinician review"]]
    K.table(s, 0.6, 1.4, [4.6, 1.75, 5.78], rows, font_size=13, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps: trends over time, a real knowledge base and a clinician review."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(r('hybrid_rerank', s4)), "lay-language top-1, shipped pipeline (n = 60)", K.BLUE), (F.pct(r('hybrid_rerank', s3)), "two-symptom queries, leave-one-out (n = 176)", K.GREEN),
                                   (F.pct(r('hybrid_tfidf', s4)), "same probes with the offline TF-IDF fallback", K.ORANGE),
                                   (f"{SF['emergency_recall']:.2f}", f"emergency recall (paraphrases 0 of {SF['by_group_pos']['paraphrase']['n']})", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f02_ablation.png"), 0.6, 2.9, 6.6, 3.2)
    K.picture(s, F.fig("f03_protocol_comparison.png"), 7.4, 2.9, 5.3, 3.2)
    K.text(s, 0.6, 6.2, 12.1, 0.8, "The shipped 100% on the About page counts held-out records that are still in the index; removing them gives 0.967 (n = 30). Probes are written by the team on a synthetic base, so these are pipeline measurements, not clinical accuracy; not comparable with the base paper.", size=12, color=K.TXT)
    notes[15] = (f"Four headline numbers, each with its protocol. Shipped protocol {r('hybrid_rerank', s1p):.2f} is an upper bound; leave-one-out {r('hybrid_rerank', s1l):.3f}; "
                 f"two random symptoms {r('hybrid_rerank', s3):.3f}; lay language {r('hybrid_rerank', s4):.3f}. BM25 alone is already strong ({r('bm25', s4):.3f} on lay language).")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, crop("07_assistant_answer.png", (248, 285, 1440, 900), "a"), 0.6, 1.25, 6.0, 2.8, border=True)
    K.picture(s, crop("20_assistant_evidence.png", (248, 285, 1440, 900), "b"), 6.75, 1.25, 6.0, 2.8, border=True)
    K.picture(s, crop("08_assistant_emergency.png", (248, 285, 1440, 900), "c"), 0.6, 4.15, 6.0, 2.4, border=True)
    K.picture(s, crop("09_history.png", (248, 285, 1440, 900), "d"), 6.75, 4.15, 6.0, 2.4, border=True)
    K.text(s, 0.6, 6.72, 12.1, 0.4, "Top: answer and evidence card for a fever query. Bottom: emergency banner for chest pain, and the consultation history. All captured from the running app.", size=12, color=K.TXT)
    notes[16] = "Real screenshots of the running application. The answer text is the evidence-based fallback; the evidence card shows record symptoms, guidance and red flags."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    t5 = F.LAT_T5["chat_ms"]["median"]
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.BLUE),
                                   ("0", "console errors in the browser walk", K.ORANGE), (f"{t5 / 1000:.2f} s", "median /api/chat with the local generator", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["Out-of-base complaints (tooth ache, sprained ankle ...) still read 'Strong match' at 100%", "Documented; the raw reranker score separates them (AUROC 1.0), a fix is listed"],
            ["Flan-T5 'answer' is the prompt itself under transformers 5", "Recorded as a defect; fallback answer used for the screens"],
            ["Safety rules miss paraphrased emergencies and fire on negated or historical mentions", "Stated limit; measured on 40 + 30 probes"]]
    K.table(s, 0.6, 3.0, [6.3, 5.83], rows, font_size=15, row_h=0.88)
    notes[17] = "Tests ran against the real pipeline with real models. The observations come from measuring, and each is documented rather than hidden."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No open symptom-disease dataset could be used", "Synthetic, labelled base; every metric states it; ceiling effects explained"],
            ["Library drift: transformers 5 removed text2text-generation", "Defect measured (30 of 30 echoes); evidence-based fallback keeps answers usable"],
            ["CPU latency: the cross-encoder dominates", f"Measured {F.LAT['stages_ms']['rerank']['mean']:.0f} ms of a {F.LAT['pipeline_answer_fallback_only_ms']['mean']:.0f} ms answer; caching and a smaller pool are next steps"],
            ["Relevance shown to the user is relative, not absolute", "Measured with out-of-base queries; raw scores kept for a calibrated display"],
            ["Safety rules are literal regular expressions", "Reported recall by wording; synonyms, negation and a classifier listed as future work"]]
    K.table(s, 0.6, 1.5, [5.6, 6.53], rows, font_size=16, row_h=0.9)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Real knowledge", "Replace the synthetic base with a licensed medical source and have a clinician review conditions and guidance.", K.BLUE, "1"),
        ("Independent evaluation", "Test with queries written by people outside the team and report top-k with confidence intervals.", K.GREEN, "2"),
        ("Fix defects", "Load Flan-T5 directly for transformers 5, show a calibrated relevance, handle negation and paraphrase in the safety layer.", K.ORANGE, "3"),
        ("Track over time", "Add a symptom timeline and trend view over the stored consultations, as the base paper's gap statement asks.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 4.6, t, b_, col, gl, body_size=17)
    notes[19] = "Plan to the final review and beyond. The first two items address the biggest honest gaps: the synthetic base and team-made probes."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why BM25 plus dense; why the answer is not diagnosis; what the 100 percent on the About page means; what the safety layer cannot do."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
