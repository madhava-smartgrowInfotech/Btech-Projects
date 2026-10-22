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
    out = os.path.join(tempfile.gettempdir(), f"c8_deck_{tag}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    SH, MM, TF, GEN, E, L = F.SHIPPED, F.MINILM, F.TFIDF, F.GEN, F.ENV["packages"], F.LATENCY
    llm_s = L["http_llm_on_s"]
    llm_lo, llm_hi = min(llm_s["ieee_base_paper_30_pages"], llm_s["arxiv_survey_30_pages"]), llm_s["reviewgraph_17_pages_via_browser"]
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a local pipeline from PDF to assessment and an auditable reviewer ranking",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how PeerScope is designed and built: the data and models, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and models"), ("04", "Training and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Submissions outgrow reviewer pools. Editors choose reviewers from memory or keywords, matches are hard to explain, and first-pass screening of papers is inconsistent.", K.ORANGE, "!"),
        ("Proposed system", "PeerScope reads the PDF locally, adds a decision signal and a local AI critique, retrieves related work, and ranks reviewers with a score whose terms are all shown.", K.BLUE, "i"),
        ("Base paper link", "Bagheri et al. make reviewer matching auditable with LLM keyword induction. PeerScope keeps the audit idea, adds paper assessment, availability and conflict terms, and runs locally. Results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.9, t, b_, col, gl, body_size=19)
    notes[3] = "One-minute recap of Review 1: the editorial bottleneck, our hybrid approach, and how the base paper relates (shared principle, different scope and data)."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.1, 5.6)
    K.text(s, 8.0, 1.5, 4.7, 5.3, [
        ("**Four tiers**", {"space_after": 8}),
        (f"Presentation: React and Vite web app (port {F.WEB_PORT}), 8 pages.", {"bullet": True}),
        (f"Application: FastAPI (port {F.API_PORT}), 12 routes under /api, PDF-only upload with a 20 MB limit and header check.", {"bullet": True}),
        ("Services: plain function modules orchestrated by pipeline.run_analysis.", {"bullet": True}),
        ("Data: SQLite (reviewers, analyses), joblib model files, cached language models. Only the OpenAlex query leaves the machine.", {"bullet": True}),
    ], size=16, color=K.INK)
    notes[4] = "All routes live in app/main.py; the services are separate modules so each stage can be tested alone. Storage is local."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.2, [("PDF upload", K.NAVY), ("Extract + sections", K.PURPLE), ("Features + signals", K.PURPLE), ("Decision signal", K.GREEN),
                                      ("AI critique", K.ORANGE), ("Literature", K.BLUE), ("Reviewer ranking", K.NAVY)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("One pipeline", "A single function, run_analysis, calls every stage in order and stores the result, so the web app, the tests and the scripts exercise the same code."),
                                 ("Graceful degradation", "No language model: deterministic review with a visible notice. No internet: literature marked unavailable. No sentence-embedding model: TF-IDF fallback."),
                                 ("Measured, not typed", "scripts/measure_metrics.py writes every reported number to docs/metrics/metrics.json; figures are regenerated from it.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.1, 3.85, 3.6)
        K.text(s, x + 0.25, 3.25, 3.4, 0.5, t, size=20, color=K.INK, bold=True)
        K.text(s, x + 0.25, 3.9, 3.4, 2.7, b_, size=18, color=K.TXT)
    notes[5] = "The three design principles: one pipeline, honest fallbacks, and numbers that come from a script. The same pipeline serves the live app and the measurements."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Datasets used")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.DM['rows']:,}", "synthetic labelled papers (decision model)", K.BLUE), ("3", "classes: accept, borderline, reject", K.GREEN),
                                   (f"{F.DM['train']:,} / {F.DM['test']}", "train / held-out test (stratified)", K.ORANGE), ("40 + 6", "probe abstracts + demo reviewers", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f06_dataset_structure.png"), 0.6, 2.95, 6.6, 3.2)
    K.text(s, 7.5, 2.95, 5.2, 3.9, [
        ("The public peer-review probe in prepare_dataset.py returned no data, so the project generated a labelled synthetic set (seed 42).", {"bullet": True}),
        (f"Labels come from the same strength and weakness phrases that appear in the text, and borderline is drawn from both: no text classifier can exceed about {F.pct(GEN['best_possible_accuracy_from_phrases'], 0)} accuracy.", {"bullet": True}),
        ("Reviewer pool: six demo profiles. Matching probe: 40 abstracts written by the team, labelled by the team.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=10)
    K.text(s, 0.6, 6.25, 6.6, 0.6, "Class counts and how the label relates to the text phrases.", size=12, color=K.TXT, align="c", italic=True)
    notes[6] = ("Be frank: the dataset is synthetic, so the decision model demonstrates the pipeline and is not evidence of predicting real peer-review decisions. "
                "The matching probe is also team-made; independent expert labels were not available.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Data preprocessing: from PDF to features")
    wipe(s)
    K.picture(s, F.diag("12_pdf_extraction_flow.png"), 0.6, 1.35, 6.9, 5.45)
    K.text(s, 7.8, 1.5, 4.9, 5.2, [
        ("1  PyMuPDF text of every page, whitespace normalised", {}), ("2  Title: first plausible line (12-220 characters, no final full stop)", {}),
        ("3  Nine sections found by heading patterns", {}), ("4  References parsed (up to 60)", {}), ("5  Frequency keywords, 21 method terms, 18 topic hints", {}),
        ("6  Four structural signals combined 0.35 / 0.25 / 0.25 / 0.15", {}),
        ("Known weakness: roman-numeral headings such as 'I. INTRODUCTION' are not detected.", {"italic": True, "size": 14, "color": K.TXT}),
    ], size=15, color=K.INK, space_after=9)
    notes[7] = "The extraction is rule based. On the IEEE base paper itself the introduction heading was not detected and the title came out as the DOI line; this is listed as a defect."

    # ---- 8 models
    s = S[7]
    set_title(s, "Models used")
    wipe(s)
    rows = [["Component", "Configuration", "Role"],
            ["Decision signal", "TF-IDF words 1-2 (8,000) + characters 3-5 (4,000), logistic regression, balanced classes", "accept / borderline / reject probabilities"],
            ["Sentence embeddings", "all-MiniLM-L6-v2 (TF-IDF fallback, 512 terms, when it cannot load)", "expertise similarity paper vs reviewer"],
            ["Local language model", "Qwen2.5-1.5B-Instruct on CPU, 32-bit floats (0.5B fallback); analyse, critique, synthesise", "reviewer-style critique, never a ranking"]]
    K.table(s, 0.6, 1.5, [2.4, 6.0, 3.73], rows, font_size=14, row_h=0.95, first_bold=True)
    K.tile(s, 0.6, 5.6, 3.8, 1.2, "12,000", "TF-IDF features in the decision model", K.BLUE, vsize=26)
    K.tile(s, 4.7, 5.6, 3.8, 1.2, "1.5 B", "parameters in the local language model", K.GREEN, vsize=26)
    K.tile(s, 8.8, 5.6, 3.93, 1.2, "No GPU", "everything runs on a CPU", K.ORANGE, vsize=26)
    notes[8] = "Three models with separate jobs. The language model only writes the critique text; ranking never depends on it, which keeps the score auditable."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration (decision model)")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Data and split", f"{F.DM['rows']:,} synthetic rows; 80 / 20 stratified, seed 42 ({F.DM['train']:,} train / {F.DM['test']} test)"],
            ["Classifier", "LogisticRegression, C = 1.0, max_iter = 1000, class_weight = balanced"],
            ["Features", "TF-IDF word 1-2 grams (8,000, English stop words) + character 3-5 grams (4,000) over title + text"],
            ["Robustness check", f"Five other splits: accuracy {F.SEEDS['accuracy']['mean']:.3f} +/- {F.SEEDS['accuracy']['sd']:.3f}, macro F1 {F.SEEDS['f1_macro']['mean']:.3f} +/- {F.SEEDS['f1_macro']['sd']:.3f}"],
            ["Hardware", f"{F.ENV['cpu'].replace('(R)', '').replace('Intel ', 'Intel ')}, {F.ENV['ram_gb']} GB RAM, CPU only; training takes seconds"]]
    K.table(s, 0.6, 1.4, [2.6, 9.53], rows, font_size=15, row_h=0.55, first_bold=True)
    K.picture(s, F.fig("f04_seed_study.png"), 0.6, 4.85, 5.6, 2.15)
    K.text(s, 6.5, 5.1, 6.2, 1.8, "Accuracy moves by about three points between splits, so one split's 0.55 is not a precise figure. Training and the five-split study both run in the measurement script; the shipped model files were not changed.", size=16, color=K.TXT)
    notes[9] = "Settings are from scripts/train_model.py. The five-split study re-trains in memory only. The spread shows the headline number is a noisy estimate."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: the auditable match score")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_matching.png"), 0.6, 1.3, 5.2, 5.6)
    K.text(s, 6.2, 1.5, 6.5, 5.3, [
        ("**Score.** 0.55 x embedding similarity + 0.20 x keyword overlap + 0.15 x method / topic overlap + 0.10 x availability - 0.60 x conflict penalty, scaled to 0-100.", {"bullet": True, "space_after": 9}),
        ("**Bands.** Strong from 65, Good from 45, Possible from 25, otherwise Weak.", {"bullet": True, "space_after": 9}),
        ("**Availability.** 1 - current load / maximum load.", {"bullet": True, "space_after": 9}),
        ("**Conflict.** A listed conflict term, the reviewer's full name or affiliation found in the paper text applies the penalty.", {"bullet": True, "space_after": 9}),
        ("**Audit.** Every card shows each term, its weight, the matching words and a plain-language reason.", {"bullet": True}),
    ], size=17, color=K.INK)
    notes[10] = "The weights live in app/config.py. Conflict detection is literal string matching, a limitation measured later: 12 of 12 literal links found, paraphrased ones missed."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 6.2, 5.6)
    rows = [["Module", "Role"], ["pdf_extract", "text, sections, references"], ["features", "keywords, structural signals"], ["ml_predict", "decision signal"], ["review_synthesis", "rules + 3-step AI review"],
            ["llm_service", "lazy Qwen loading"], ["literature", "OpenAlex retrieval"], ["embeddings", "MiniLM / TF-IDF"], ["matching", "score, conflicts, ranking"], ["export_service", "JSON and PDF report"]]
    K.table(s, 7.1, 1.4, [2.4, 3.23], rows, font_size=13, row_h=0.5)
    notes[11] = "Level-1 data flow: the upload becomes a paper profile, the profile is scored against the reviewer directory, and the result is stored and exported."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 6.4, 4.2)
    K.picture(s, F.diag("06_uml_class.png"), 7.2, 1.3, 5.5, 5.65)
    K.text(s, 0.6, 5.75, 6.4, 1.2, "Two SQLite tables, no foreign key: an analysis stores the whole ranked result as JSON and copies the top reviewer's name. Trained models and the dataset are files.", size=13, color=K.TXT, italic=True)
    notes[12] = "Honest point: the services are plain function modules, drawn as classes in the UML for readability. The analyses table has no foreign key to reviewers."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Backend", f"Python {F.ENV['python']}, FastAPI {E['fastapi']}, Uvicorn, Pydantic, SQLAlchemy {E['SQLAlchemy']}, SQLite"],
            ["PDF and reports", f"PyMuPDF (text extraction), reportlab {E['reportlab']} (PDF export)"],
            ["Machine learning", f"scikit-learn {E['scikit-learn']}, NumPy, pandas, joblib"],
            ["Embeddings and language model", f"sentence-transformers {E['sentence-transformers']} (all-MiniLM-L6-v2), PyTorch {E['torch']}, Transformers {E['transformers']}, Qwen2.5-1.5B-Instruct"],
            ["Literature", "OpenAlex public REST API through requests (8 s timeout, no key)"],
            ["Front end", "React 19, Vite 8, Recharts, Framer Motion, GSAP, three.js (port 5408)"],
            ["Testing", "pytest, FastAPI TestClient, httpx, Playwright browser walk, smoke script"]]
    K.table(s, 0.6, 1.5, [3.2, 8.93], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = f"Python {F.ENV['python']} on Windows. Everything is open source; run.bat creates the environment, trains the decision model if needed and starts both servers."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["PDF extraction, sections, features", "Done", "4 real PDFs and a demo paper processed"],
            ["Decision signal (TF-IDF + logistic regression)", "Done", "synthetic data; accuracy " + F.f2(SH["accuracy"])],
            ["Local AI review with deterministic fallback", "Done", f"Qwen2.5-1.5B; {round(llm_lo / 60)}-{round(llm_hi / 60)} min per analysis on CPU"],
            ["Literature grounding (OpenAlex)", "Done, 1 defect", "HTTP 400 when the title contains a question mark"],
            ["Reviewer matching and conflict check", "Done", "40-abstract probe; 12 of 12 literal conflicts found"],
            ["API (12 routes) and web app (8 pages)", "Done", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks; 17 screenshots"],
            ["Real publication profiles, h-index", "Not done", "six demo reviewers only"],
            ["Novelty assessment", "Not done", "coverage chart shows a fixed placeholder"]]
    K.table(s, 0.6, 1.4, [5.0, 1.75, 5.38], rows, font_size=13, row_h=0.6)
    notes[14] = "State of the code base. The honest gaps: real publication histories, novelty assessment, and independent expert evaluation."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(SH["accuracy"]), f"decision accuracy, synthetic test (n = {F.DM['test']})", K.BLUE), (F.f3(SH["f1_macro"]), "macro F1 (borderline recall 0.07)", K.GREEN),
                                   (f"{F.pct(MM['full_hybrid_shipped_weights']['top1'], 0)} / {F.pct(TF['full_hybrid_shipped_weights']['top1'], 0)}", "matching top-1: MiniLM / TF-IDF fallback", K.ORANGE),
                                   ("12 / 12", "literal conflicts found; 0 false flags", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    K.picture(s, F.fig("f01_confusion_matrix.png"), 0.6, 2.9, 4.9, 3.8)
    K.picture(s, F.fig("f07_matching_configs.png"), 5.7, 2.9, 7.0, 3.1)
    K.text(s, 5.7, 6.05, 7.0, 0.95, "Decision model: synthetic labels, so accuracy cannot exceed about 0.56; accept vs reject is 93% right. Matching: 40 abstracts written by the team, 6 demo reviewers; not comparable with the base paper.", size=12, color=K.TXT)
    notes[15] = ("Four headline numbers, each with its caveat. 55.0 percent accuracy on synthetic data near the 0.56 ceiling; macro F1 0.509; matching top-1 0.95 with MiniLM and 0.75 with the TF-IDF fallback on the team's 40-abstract probe; "
                 "12 of 12 literal conflicts detected, none of the paraphrased ones.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, crop("09_result_reviewers.png", (240, 1130, 1440, 2050), "s09"), 0.6, 1.3, 7.0, 4.85, border=True)
    K.picture(s, crop("06_analyze_result_overview.png", (240, 840, 1440, 1020), "s06a"), 7.85, 1.3, 4.88, 0.8, border=True)
    K.picture(s, crop("06_analyze_result_overview.png", (240, 1580, 1440, 1960), "s06b"), 7.85, 2.3, 4.88, 1.55, border=True)
    K.picture(s, crop("08_result_literature.png", (240, 1108, 1440, 1700), "s08"), 7.85, 4.05, 4.88, 2.4, border=True)
    K.text(s, 0.6, 6.25, 7.0, 0.75, "Real paper (ReViewGraph PDF): rank 1 scores only 28.4 of 100 because the demo reviewers are far from its topic; the breakdown shows why. Right: assessment and literature.", size=12, color=K.TXT)
    notes[16] = "Real screenshots of the running application with the local language model loaded, from an analysis of a real 17-page paper. Low absolute scores are expected: the demo reviewers do not work on this topic."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.BLUE),
                                   ("0", "console errors in the browser walk", K.ORANGE), (f"{L['http_api']['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s", "analysis without the AI review (3 pages)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.45, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["OpenAlex answers HTTP 400 when the extracted title has a question mark; the survey PDF got no literature", "Shown as 'unavailable'; query clean-up listed as next step"],
            ["IEEE-format PDF: introduction not detected, title came out as the DOI line", "Recorded as a defect; heading patterns to be extended"],
            ["Paraphrased affiliations and first names are not flagged as conflicts", "Stated limitation; literal links 12 of 12, 0 false flags"]]
    K.table(s, 0.6, 3.0, [6.3, 5.83], rows, font_size=15, row_h=0.88)
    notes[17] = "Tests ran with the language model disabled so they are fast and repeatable. The observations come from running real PDFs and injected conflict cases, and each is documented rather than hidden."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No open peer-review corpus could be fetched", "Labelled synthetic set, stated everywhere; ceiling analysis shows what it can show"],
            [f"The local language model is slow on a CPU ({llm_lo}-{llm_hi} s per analysis)", "Lazy loading, rules-based review always shown, visible status badge"],
            ["Offline or failing services (OpenAlex, embedding model)", "Time-outs and fallbacks: literature 'unavailable', TF-IDF embeddings"],
            ["TF-IDF fallback is fitted once and then frozen", f"Measured: top-1 {F.pct(TF['full_hybrid_shipped_weights']['top1'], 0)} against {F.pct(MM['full_hybrid_shipped_weights']['top1'], 0)}; MiniLM preferred"],
            ["Ranking re-embeds every reviewer per request", f"Measured: {MM['scaling_ms'][0]['median_ms']:.0f} ms for 6 reviewers, {MM['scaling_ms'][-1]['median_ms'] / 1000:.1f} s for 500; caching planned"]]
    K.table(s, 0.6, 1.5, [5.6, 6.53], rows, font_size=16, row_h=0.9)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Real data", "Train and test the decision model on a real open review corpus, and build reviewer profiles from real publication histories.", K.BLUE, "1"),
        ("Independent evaluation", "Judge the ranking against assignments or labels made by people outside the team, and report MRR and precision at 3.", K.GREEN, "2"),
        ("Harden", "Clean the OpenAlex query, detect roman-numeral headings, cache reviewer embeddings, add authentication.", K.ORANGE, "3"),
        ("Extend", "Estimate novelty against retrieved literature, support scanned PDFs, try a smaller or quantised language model.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 4.6, t, b_, col, gl, body_size=19)
    notes[19] = "Plan to the final review and beyond. The first two items address the biggest honest gaps: synthetic training data and team-made labels."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why a classical classifier for the decision signal; how conflicts are detected (literal strings); what the language model is allowed to do (write a critique, never rank)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
