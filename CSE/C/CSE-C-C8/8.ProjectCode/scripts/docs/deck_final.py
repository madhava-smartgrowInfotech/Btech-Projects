"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited)."""

import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .lit import (BASE_PAPER_POINTS, EXISTING_SYSTEM, EXPECTED_OUTCOMES, GAPS, LIT_TABLE, OBJECTIVES, PROBLEM_STATEMENT, PROPOSED_APPROACH,
                  SUPPORT_EVIDENCE)
from .refs import REFS

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520
CROPS = os.path.join(tempfile.gettempdir(), "c8_deck_crops")


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text, size)
            return


def wipe(slide):
    K.clear(slide, chrome)


def fbox(slide, x, y, w, h, fill=K.FHEAD, line=None):
    return K.box(slide, x, y, w, h, fill=fill, line=line, radius=0.04)


def ftable(slide, x, y, widths, rows, size=13, row_h=0.45, align=None, first_bold=True):
    return K.table(slide, x, y, widths, rows, font_size=size, row_h=row_h, header_fill=K.FHEAD, header_color=K.FNAVY, zebra=K.FZEBRA,
                   body_color=K.DARK, first_bold=first_bold, font=FONT, align=align, border=K.RGBColor(0xBF, 0xBF, 0xBF))


def ftext(slide, x, y, w, h, paras, size=16, color=K.DARK, **kw):
    return K.text(slide, x, y, w, h, paras, size=size, color=color, font=FONT, **kw)


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=12, color=K.DARK, font=FONT)


def crop(name, box):
    """Crop a region (left, top, right, bottom in pixels) from a real screenshot into a temp PNG and return its path."""
    from PIL import Image

    os.makedirs(CROPS, exist_ok=True)
    out = os.path.join(CROPS, f"{os.path.splitext(name)[0]}_{box[1]}.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.subject = F.PRODUCT
    cp.keywords = "research paper evaluation, reviewer recommendation, NLP, sentence embeddings, peer review"
    notes = {}
    D, SH = F.DM, F.SHIPPED
    mm, tf = F.MINILM, F.TFIDF
    hy, hyt = mm["full_hybrid_shipped_weights"], tf["full_hybrid_shipped_weights"]
    LAT = F.LATENCY
    st = LAT["pipeline_stages"]["demo"]
    http = LAT["http_api"]
    cx = mm["conflict"]["detected_by_kind"]
    ceil = F.GEN["best_possible_accuracy_from_phrases"]
    probe = "team-written 40-abstract probe, 6 demo reviewers"

    # footers on every slide except the title
    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.FULL_TITLE, 24)
        elif sh.name == "Text 2":
            K.replace_text(sh, f"Final Review  ·  {F.PRODUCT}")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and the project: PeerScope, a local application that assesses a research paper and ranks reviewers with an audit trail."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Dataset & Models\nScoring Workflow, Interaction & Storage\nImplementation Highlights\nResults: Decision Model, Reviewer Matching\nPerformance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, [
        ("Journals receive more submissions than their reviewer pools can absorb; assigning reviewers is manual, keyword matching favours shared vocabulary over expertise, and first-pass screening is inconsistent.", {"bullet": True, "space_after": 9}),
        ("PeerScope reads a PDF locally, extracts sections and structural signals, adds a TF-IDF decision signal, a local Qwen2.5-1.5B critique and OpenAlex literature, then ranks reviewers with an auditable score: 0.55 embedding similarity + 0.20 keywords + 0.15 methods + 0.10 availability - 0.60 conflict.", {"bullet": True, "space_after": 9}),
        (f"Decision model: {F.pct(SH['accuracy'])} accuracy on {D['test']} synthetic test papers; the labels limit any text classifier to about {ceil:.2f}, so this shows the pipeline, not real-world prediction.", {"bullet": True, "space_after": 9}),
        (f"Reviewer matching: first-choice reviewer acceptable in {F.pct(hy['top1'], 0)} (MiniLM) and {F.pct(hyt['top1'], 0)} (TF-IDF fallback) on a {probe}; 12 of 12 literal conflict links flagged.", {"bullet": True, "space_after": 9}),
        (f"Without the language model an analysis takes about {http['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s; with it, {F.lat_demo_text()} on a CPU. {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass.", {"bullet": True, "space_after": 9}),
        ("Not done: real peer-review data, independent expert labels, novelty scoring, a user study.", {"bullet": True}),
    ], size=16)
    notes[3] = "Read the problem, then the system in one breath. Give each number with its protocol and end on the honest limits."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.8, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper: LLM-assisted reviewer assignment via auditable expertise matching"],
            ["Method", "Ensemble of producer LLMs, a judge LLM and deterministic normalisation induce keywords; LLMs never rank reviewers. Matchers: TF-IDF, Jaccard, SBERT (all-MiniLM-L6-v2), cross-encoder re-ranking, keyword graphs"],
            ["Data", BASE_PAPER_POINTS[2] + " (Semantic Scholar profiles); relevance = historical assignments"],
            ["Reported results", "Best MRR@3 0.7778 (titles, two-stage re-ranking) and 0.7843 (abstracts, KG edge-Jaccard); best P@3 0.4545 and MAP@3 0.3232 (summaries, keyword-aware SBERT)"],
            ["Auditability", "Every stage stores prompts, model ids, keywords, score matrices and top-3 lists as an audit trail"],
            ["Stated limits", "No expert judgements; conflict of interest and capacity not benchmarked; most text-encoder differences not significant; no assessment of the paper itself"]]
    ftable(s, 0.55, 2.7, [2.0, 10.2], rows, size=13, row_h=0.62)
    notes[4] = "Bagheri et al., IEEE Access 2026. We adopt the auditable principle and the MiniLM encoder, add paper assessment, availability and conflict handling, and do not use an LLM ensemble."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Data / finding / limitation"]]
    for r in LIT_TABLE:
        rows.append([r[0].replace(" (base paper)", " (base)"), r[1], r[2], r[3]])
    ftable(s, 0.55, 1.8, [2.3, 0.7, 4.9, 4.3], rows, size=10, row_h=0.55, align=["l", "c", "l", "l"])
    notes[5] = "Representative work in reviewer assignment, embeddings and automated review. Items whose text could not be read are marked in the report's reference list."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(g, {"bullet": True, "space_after": 16}) for g in GAPS], size=21)
    notes[6] = "Six gaps drawn from the survey. We address the first, second, fifth and sixth directly; the third and fourth shape the design and the limits."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.9, 12.2, 2.3)
    ftext(s, 0.85, 1.95, 11.6, 2.2, PROBLEM_STATEMENT, size=17, anchor="m", bullets=True)
    for i, (t, b_) in enumerate([("Input", "Research-paper PDF (up to 20 MB) and a directory of reviewer profiles"), ("Output", "Preliminary assessment and ranked reviewers with a visible score breakdown"), ("Record", "Stored analyses, JSON and PDF export, measured model metrics")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.5, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.6, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.1, 3.5, 1.0, b_, size=15)
    notes[7] = "The statement has three parts: assess the paper, rank the reviewers transparently, and keep an inspectable record."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives of the proposal. The conclusion states the real status of each: 1 and 6 only partly met, 5 met except novelty."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.1, [("PDF upload", K.FNAVY), ("Extract + signals", K.FBLUE), ("Decision + AI review", K.GREEN), ("Literature", K.ORANGE), ("Rank reviewers", K.PURPLE)], size=15, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.35, 12.2, 3.5, [(p, {"bullet": True, "space_after": 10}) for p in PROPOSED_APPROACH] + [
        ("Final editorial judgement stays with a human: every screen carries the decision-support disclaimer.", {"bullet": True})], size=17)
    notes[9] = "The proposed system as one line of boxes and the five design rules behind it."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 8.4, 5.1)
    ftext(s, 9.2, 2.0, 3.6, 4.8, [
        ("Web app: React + Vite on port 5408", {"bullet": True, "space_after": 8}),
        ("API: FastAPI on port 8408, 12 routes", {"bullet": True, "space_after": 8}),
        ("Services: extraction, features, decision, review, literature, matching", {"bullet": True, "space_after": 8}),
        ("Storage: SQLite (reviewers, analyses) and model files", {"bullet": True, "space_after": 8}),
        ("Local first: only a title query leaves the machine (OpenAlex)", {"bullet": True}),
    ], size=15)
    notes[10] = "Tiers and storage; all analysis runs on the local machine."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.9, 12.2, 1.2, [("Read PDF", K.FNAVY), ("Sections + features", K.FBLUE), ("Decision signal", K.GREEN), ("AI review (3 steps)", K.ORANGE), ("OpenAlex", K.PURPLE), ("Match + conflict", K.FBLUE), ("Store + export", K.FNAVY)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.4, 12.2, 3.4, [
        ("Deterministic rules always run; the local language model adds text only when it loads, and a visible notice replaces it otherwise: nothing is fabricated.", {"bullet": True, "space_after": 9}),
        ("Decision model: stratified 80/20 split, seed 42; extra measurements: five other splits, baselines, confidence threshold sweep.", {"bullet": True, "space_after": 9}),
        ("Matching evaluated on 40 held-out probe abstracts across six areas: top-1, top-3 and MRR for four score configurations and two embedders.", {"bullet": True, "space_after": 9}),
        ("Conflict handling tested by injecting 15 links into papers; false flags counted on 240 clean paper-reviewer pairs.", {"bullet": True, "space_after": 9}),
        ("Every number is written by scripts/measure_metrics.py to docs/metrics/metrics.json.", {"bullet": True}),
    ], size=16)
    notes[11] = "Workflow and the measurements added on top of the shipped model."

    # ---- 12 dataset, features, models
    s = S[11]
    set_title(s, "Dataset & Models")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.05, f"{D['rows']:,}", "synthetic labelled rows (fallback data)", K.FBLUE, 26)
    ftile(s, 0.55, 3.1, 2.9, 1.05, "12,000", "TF-IDF features: 8k word + 4k char", K.GREEN, 24)
    ftile(s, 0.55, 4.3, 2.9, 1.05, f"{D['train']} / {D['test']}", "train / test papers (80/20, seed 42)", K.ORANGE, 24)
    K.picture(s, F.fig("f06_dataset_structure.png"), 3.7, 1.85, 5.2, 2.2)
    rows = [["Component", "Choice"], ["Decision signal", "LogisticRegression, balanced, C = 1"], ["Embeddings", "all-MiniLM-L6-v2 (TF-IDF fallback)"], ["AI review", "Qwen2.5-1.5B-Instruct, CPU"], ["Literature", "OpenAlex API, 6 works"]]
    ftable(s, 9.1, 1.9, [1.5, 2.3], rows, size=11, row_h=0.62, first_bold=True)
    ftext(s, 3.7, 4.2, 5.3, 2.5, [
        (f"Class counts: {D['class_counts']['accept']} accept, {D['class_counts']['borderline']} borderline, {D['class_counts']['reject']} reject.", {"bullet": True}),
        (f"Each label comes from the same strength or weakness phrases that appear in the text; borderline is drawn from both groups, so accuracy cannot exceed about {ceil:.2f}.", {"bullet": True}),
        ("The public PeerRead probe returned no data, so this is the fallback.", {"bullet": True}),
    ], size=13)
    ftext(s, 0.55, 5.55, 3.0, 1.3, "Reviewer data: 6 labelled demo profiles (Reviewer Alpha to Zeta).", size=12, color=K.FNAVY, italic=True)
    notes[12] = "Be frank about the data: synthetic, and the label construction caps accuracy near 0.56. The reviewer pool is six demo profiles."

    # ---- 13 scoring workflow
    s = S[12]
    set_title(s, "Reviewer Scoring Workflow")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_matching.png"), 0.55, 1.8, 5.6, 5.1)
    ftext(s, 6.4, 1.95, 6.4, 4.9, [
        ("Embed paper profile and every reviewer profile; cosine = expertise similarity.", {"bullet": True, "space_after": 10}),
        ("Keyword overlap, method / topic overlap, availability = 1 - load / maximum.", {"bullet": True, "space_after": 10}),
        ("Conflict check: conflict terms, full name or affiliation found in the paper text: penalty 0.60.", {"bullet": True, "space_after": 10}),
        ("Score x 100, clipped 0-100; Strong >= 65, Good >= 45, Possible >= 25, else Weak.", {"bullet": True, "space_after": 10}),
        ("The UI shows each term, its weight and the matching terms for every recommendation.", {"bullet": True}),
    ], size=16)
    notes[13] = "The core algorithm of the matcher, in app/services/matching.py."

    # ---- 14 user-system interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_analyze.png"), 0.55, 1.8, 7.2, 5.1)
    K.picture(s, F.diag("08_use_case.png"), 7.9, 1.8, 4.9, 5.1)
    notes[14] = "Sequence of one analysis request and the use cases of the editor and the directory administrator."

    # ---- 15 database design
    s = S[14]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 7.0, 4.5)
    rows = [["Store", "Content"], ["table reviewers", "11 columns: profile, load, conflict terms"], ["table analyses", "9 columns incl. result_json"], ["processed_dataset.csv", "1,400 synthetic rows"],
            ["decision_model.joblib", "logistic regression"], ["tfidf_vectorizer.joblib", "word + char vectoriser"], ["metrics.json", "measured metrics"], ["models/hf_cache", "Qwen weights"]]
    ftable(s, 7.8, 1.9, [2.4, 2.6], rows, size=11, row_h=0.5)
    ftext(s, 0.55, 6.4, 12.2, 0.5, "No foreign key: an analysis stores the ranked reviewers inside its JSON, so later edits to the directory do not change past results.", size=13, color=K.FNAVY, italic=True)
    notes[15] = "Two SQLite tables plus file-based artefacts. The missing foreign key is deliberate: analyses are frozen snapshots."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("12", "REST routes (+ /docs)", K.FBLUE), (f"{F.PYTEST_TOTAL} + {F.SMOKE_TOTAL}", "pytest tests + smoke checks", K.GREEN), ("8", "React pages", K.ORANGE), (f"{F.LOC['backend_app']:,}", "lines of backend code", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("Upload validation: .pdf extension, content type, empty file, %PDF header, 20 MB limit (HTTP 413), warning when fewer than 50 words are extracted.", {"bullet": True, "space_after": 9}),
        ("Graceful degradation: local model missing -> visible notice and deterministic review; OpenAlex 8 s timeout -> literature 'unavailable'; MiniLM missing -> TF-IDF.", {"bullet": True, "space_after": 9}),
        ("Reviewer directory with CRUD, activate / deactivate, CSV import and export; analysis history with JSON and PDF export (reportlab).", {"bullet": True, "space_after": 9}),
        ("One command starts both servers (run.bat); a Docker image serves the API.", {"bullet": True}),
    ], size=17)
    notes[16] = "Highlights: validation, degradation paths, directory management and one-command start."

    # ---- 17 results: decision model
    s = S[16]
    set_title(s, "Results – Decision Model (synthetic data)")
    wipe(s)
    dec = D["decisive_only"]
    for i, (v, l, c) in enumerate([(F.pct(SH["accuracy"]), f"accuracy, n = {D['test']}", K.FBLUE), (F.f3(SH["f1_macro"]), "macro F1", K.GREEN), (F.f3(SH["roc_auc"]), "macro ROC-AUC", K.ORANGE), (F.pct(dec["accuracy"]), "accept vs reject only", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    K.picture(s, F.fig("f03_baselines.png"), 0.55, 3.1, 7.2, 3.3)
    K.picture(s, F.fig("f04_seed_study.png"), 7.95, 3.1, 4.85, 2.4)
    ftext(s, 7.95, 5.5, 4.85, 1.3, f"Five splits: accuracy {F.SEEDS['accuracy']['mean']:.3f} +/- {F.SEEDS['accuracy']['sd']:.3f}. Borderline recall {F.PER_CLASS['borderline']['recall']:.2f}: it cannot be told apart from text by construction.", size=12)
    ftext(s, 0.55, 6.45, 12.2, 0.5, f"Dashed line: best accuracy any text rule can reach on these labels (~{ceil:.2f}). Shows the pipeline works; not evidence of predicting real peer-review decisions.", size=12, color=K.FNAVY, italic=True)
    notes[17] = "Accuracy 0.55 sits next to the ceiling of about 0.56 set by the label construction; the model beats the majority baseline (0.44) and naive Bayes (0.46). On the four real papers it answered borderline every time."

    # ---- 18 confusion matrix & threshold
    s = S[17]
    set_title(s, "Confusion Matrix & Confidence Threshold")
    wipe(s)
    K.picture(s, F.fig("f01_confusion_matrix.png"), 0.55, 1.85, 5.0, 4.3)
    K.picture(s, F.fig("f05_threshold.png"), 5.8, 1.85, 7.0, 3.5)
    br = D["borderline_row"]
    t7 = F.thr_row(0.7)
    ftext(s, 5.8, 5.45, 7.0, 1.4, [
        (f"Of {sum(br.values())} borderline papers {br['predicted_accept']} are predicted accept and {br['predicted_reject']} reject; accept and reject are almost never confused.", {"bullet": True, "size": 13}),
        (f"Confidence >= 0.7 keeps {F.pct(t7['coverage'], 0)} of papers at {F.pct(t7['accuracy_on_kept'], 0)} accuracy (n = {t7['n']}).", {"bullet": True, "size": 13}),
    ], size=13)
    ftext(s, 0.55, 6.3, 5.0, 0.6, "Rows: true class; columns: predicted.", size=12, color=K.FNAVY, italic=True)
    notes[18] = "Rows are the true class. The error is almost entirely borderline papers pushed to accept or reject. Raising the confidence threshold trades coverage for accuracy."

    # ---- 19 reviewer matching results
    s = S[18]
    set_title(s, "Results – Reviewer Matching & Conflict Handling")
    wipe(s)
    K.picture(s, F.fig("f07_matching_configs.png"), 0.55, 1.8, 6.0, 2.5)
    K.picture(s, F.fig("f08_conflict_detection.png"), 6.9, 1.8, 5.9, 2.2)
    rows = [["Embedder", "Top-1", "Top-3", "MRR"], ["MiniLM (hybrid)", f"{hy['top1']:.2f}", f"{hy['top3']:.2f}", f"{hy['mrr']:.2f}"], ["TF-IDF fallback", f"{hyt['top1']:.2f}", f"{hyt['top3']:.2f}", f"{hyt['mrr']:.2f}"],
            ["Lexical only", f"{mm['lexical_only_keyword_and_method']['top1']:.2f}", f"{mm['lexical_only_keyword_and_method']['top3']:.2f}", f"{mm['lexical_only_keyword_and_method']['mrr']:.2f}"], ["Random", f"{mm['random_expectation_top1']:.2f}", f"{mm['random_expectation_top3']:.2f}", "-"]]
    ftable(s, 0.55, 4.5, [2.6, 1.0, 1.0, 1.0], rows, size=12, row_h=0.36, align=["l", "c", "c", "c"])
    ftext(s, 6.9, 4.1, 5.9, 2.8, [
        (f"Semantic similarity alone scores {mm['semantic_similarity_only']['top1']:.3f} top-1; the hybrid {hy['top1']:.2f}; lexical overlap alone only {mm['lexical_only_keyword_and_method']['top1']:.2f}.", {"bullet": True}),
        (f"Conflicts: {cx['conflict term']['detected']}/{cx['conflict term']['n']} terms, {cx['affiliation']['detected']}/{cx['affiliation']['n']} affiliations, {cx['full name']['detected']}/{cx['full name']['n']} names flagged; paraphrased links 0/3 missed; false flags 0 of {mm['conflict']['clean_pairs_checked']} clean pairs.", {"bullet": True}),
        (f"Ranking time: {mm['scaling_ms'][0]['median_ms']:.0f} ms for 6 reviewers, {mm['scaling_ms'][-1]['median_ms'] / 1000:.1f} s for 500 (embeds every profile each request).", {"bullet": True}),
        (f"Scope: {probe}; labels are the team's own, so figures are optimistic.", {"bullet": True, "italic": True}),
    ], size=12)
    notes[19] = "Top-1 0.95 with MiniLM, 0.75 with the offline fallback; both far above random (0.18). The probe is small and labelled by the team, so it is not comparable with the base paper."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{st['PDF extraction'] / 1000:.1f} s", "PDF extraction (3 pages, first call)", K.FBLUE), (f"{st['Decision signal']:.0f} ms", "decision signal", K.GREEN),
                                   (f"{st['Reviewer matching']:.0f} ms", "reviewer matching (6 reviewers)", K.ORANGE), (f"{st['Local AI review (3 steps)'] / 60000:.1f} min", "local AI review, 3 steps, CPU", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.15, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["Unit and API (pytest)", "extraction, features, matching, conflicts, decision service, API, CRUD, pipeline", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed in {F.PYTEST_SECONDS:.0f} s"],
            ["Smoke test", "running API and web app: CRUD, CSV, bad uploads, analysis, export, CORS", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks"],
            ["HTTP latency (LLM off)", f"analysis of 3 / 30 pages; list and health calls", f"{http['analyze_demo_3_pages']['median_ms'] / 1000:.1f} s / {http['analyze_survey_30_pages']['median_ms'] / 1000:.1f} s; {http['health']['median_ms']:.1f} ms"],
            ["HTTP latency (LLM on)", "full analysis of 30 / 30 / 17 pages", "534 s / 621 s / 946 s"],
            ["Real PDFs", "four papers through the pipeline", "found 2 defects (title '?', roman headings)"]]
    ftable(s, 0.55, 3.2, [2.6, 6.0, 3.6], rows, size=12, row_h=0.5)
    ftext(s, 0.55, 6.35, 12.2, 0.6, f"Intel Core i5-12500, 15.7 GB, CPU only. Tests ran with the language model disabled. Not tested: GPU, concurrent users, scanned PDFs, a user study.", size=12, color=K.FNAVY, italic=True)
    notes[20] = "The language model is about 97 percent of the time of a full analysis; everything else takes a few seconds."

    # ---- 21 comparison with the base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only – different data and scope)")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "This project (PeerScope)"],
            ["Scope", "Reviewer affinity scoring only", "Paper assessment + reviewer ranking + directory, history, export"],
            ["Keywords / model", "LLM ensemble and judge induce keywords", "Frequency and lexicon keywords; local LLM only writes the review text"],
            ["Matcher", "TF-IDF, Jaccard, SBERT (MiniLM), cross-encoder, keyword graphs", "MiniLM cosine + keyword + method overlap + availability - conflict"],
            ["Data", "663 papers, 524 reviewers, 1,989 assignments", f"{probe}"],
            ["Reported", "Best MRR@3 0.7778 (titles) / 0.7843 (abstracts)", f"Top-1 {hy['top1']:.2f}, MRR {hy['mrr']:.2f} (not comparable)"],
            ["Conflict / load", "Not benchmarked", "In the score; 12/12 literal links flagged, paraphrases missed"]]
    ftable(s, 0.55, 1.85, [1.9, 5.0, 5.3], rows, size=12, row_h=0.62)
    ftext(s, 0.55, 6.3, 12.2, 0.6, "Different data, labels and task scope: the numbers are context, not a ranking; no superiority over the base paper is claimed.", size=13, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that 0.95 top-1 on 40 team-written abstracts and 6 demo reviewers cannot be compared with MRR@3 on 663 real papers."

    # ---- 22-24 output screens
    s = S[21]
    set_title(s, "Output – Analysis Result and AI Review")
    wipe(s)
    K.picture(s, crop("06_analyze_result_overview.png", (264, 830, 1440, 1560)), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, crop("07_result_review.png", (270, 2380, 1440, 3010)), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.2, 12.2, 0.7, "Left: a 17-page paper analysed: structural score 65.2, decision signal 'borderline' (58%), review generated by Qwen2.5-1.5B. Right: the AI synthesis, which can contain errors (here it misdescribes the paper's datasets).", size=12, color=K.FNAVY)
    notes[22] = "Real screenshots of a real analysis (ReViewGraph paper, arXiv 2511.08317). The AI text is shown unedited, including its mistakes."
    s = S[22]
    set_title(s, "Output – Reviewer Ranking and Audit")
    wipe(s)
    K.picture(s, crop("09_result_reviewers.png", (270, 1140, 1440, 1930)), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, crop("10_result_audit.png", (270, 1100, 1440, 1620)), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.2, 12.2, 0.7, "Left: rank 1 reviewer with the score breakdown (0.55 x 0.260 + 0.15 x 0.275 + 0.10 x 1.0 = 28.4; low because no demo reviewer is close to this paper). Right: audit details and JSON / PDF export.", size=12, color=K.FNAVY)
    notes[23] = "Every recommendation exposes its terms. The low absolute scores are honest: the six demo reviewers do not cover this paper's topic."
    s = S[23]
    set_title(s, "Output – Model Performance and Dashboard")
    wipe(s)
    K.picture(s, crop("13_model_performance.png", (270, 320, 1440, 1280)), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("04_dashboard.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.2, 12.2, 0.7, "Left: model page with the measured metrics and the synthetic-data warning. Right: dashboard with three stored analyses of real papers, the language model loaded and MiniLM embeddings.", size=12, color=K.FNAVY)
    notes[24] = "The product itself says the accuracy comes from synthetic data. Dashboard shows real stored analyses."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 5.0, [
        ("**Delivered:** a working local application from PDF upload to assessment, literature context, auditable reviewer ranking, history and export, with 7 pytest tests and 24 smoke checks passing.", {"bullet": True, "space_after": 9}),
        (f"**Measured:** decision model {F.pct(SH['accuracy'])} on synthetic data (ceiling ~{ceil:.2f}); reviewer matching top-1 {hy['top1']:.2f} / {hyt['top1']:.2f} on a {probe}; conflict links 12/12 literal, 0/3 paraphrased.", {"bullet": True, "space_after": 9}),
        ("**Objectives:** 2, 3, 4 met; 5 met except novelty; 1 and 6 partly (demo profiles, team-labelled probe, no real expert judgement).", {"bullet": True, "space_after": 9}),
        ("**Limits:** synthetic training data; six demo reviewers; novelty not assessed; literal conflict matching; minutes per analysis with the language model on a CPU; no user study.", {"bullet": True, "space_after": 9}),
        ("**Position:** decision support only; the editor decides.", {"bullet": True}),
    ], size=19)
    notes[25] = "Be explicit about which objectives were met and which were not, and what was never measured."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 5.0, [
        ("Train and test the decision model on real peer-review records (e.g. PeerRead / OpenReview) and report accuracy on real decisions.", {"bullet": True, "space_after": 10}),
        ("Build reviewer profiles from real publication histories (OpenAlex, Semantic Scholar) and evaluate against expert or historical assignments.", {"bullet": True, "space_after": 10}),
        ("Fix the defects found: sanitise OpenAlex queries, recognise roman-numeral headings, fit the TF-IDF fallback on a stable corpus.", {"bullet": True, "space_after": 10}),
        ("Add a measured novelty signal from literature similarity; paraphrase-aware and co-authorship-aware conflict detection.", {"bullet": True, "space_after": 10}),
        ("Cache reviewer embeddings or use an index for large pools; quantised or GPU model for faster reviews; sign-in and multi-user support.", {"bullet": True}),
    ], size=20)
    notes[26] = "Concrete next steps, ordered by value."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = [1, 2, 6, 7, 10, 11, 13, 19, 20, 22, 24, 27, 29, 32]
    ftext(s, 0.55, 1.8, 6.0, 5.1, [(f"[{n}] {REFS[n - 1].replace(chr(42), chr(32)).replace(chr(32) * 2, chr(32))}", {"space_after": 5}) for n in ids[:7]], size=11)
    ftext(s, 6.8, 1.8, 6.0, 5.1, [(f"[{n}] {REFS[n - 1].replace(chr(42), chr(32)).replace(chr(32) * 2, chr(32))}", {"space_after": 5}) for n in ids[7:]], size=11)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "PeerScope")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
