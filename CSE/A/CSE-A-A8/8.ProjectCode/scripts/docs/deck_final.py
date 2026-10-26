"""16.Final_PPT.pptx: 28 slides, LabLens. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited).

Every number is read from facts.py (experiments/lablens/*.json); nothing from the template's old subject survives.
"""

import os

from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .refs import REFS

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520
CROPS = os.path.join(os.environ.get("TEMP", "."), "lablens_deck_crops")

OBJECTIVES = [
    "Accept lab reports in PDF or scanned image form and extract text using high-speed OCR.",
    "Apply named entity recognition to identify test parameters, values, units and reference ranges.",
    "Compare each extracted value against its reference range and flag abnormal results.",
    "Generate plain-language explanations for abnormal findings, grounded in trusted medical sources.",
    "Track parameters across successive reports to display health trends over time.",
    "Present results through a dashboard and evaluate extraction accuracy against manually labelled reports.",
]


def chrome(sh):
    return sh.top in (TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT)


def set_title(slide, text):
    for sh in slide.shapes:
        if sh.top == TOP_TITLE:
            K.replace_text(sh, text)
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


def crop(name, h, x0=248):
    """Main content area (the 248 px navigation sidebar is dropped) of a 1440-wide screenshot, first `h` pixels; saved outside the project."""
    os.makedirs(CROPS, exist_ok=True)
    out = os.path.join(CROPS, f"{h}_{x0}_{name}")
    with Image.open(F.shot(name)) as im:
        im.convert("RGB").crop((x0, 0, im.size[0], min(h, im.size[1]))).save(out)
    return out


def ref_no(fragment):
    for i, r in enumerate(REFS, 1):
        if fragment in r:
            return i
    raise KeyError(fragment)


def sweep(th):
    return [r for r in F.NAMES["threshold_sweep"] if abs(r["threshold"] - th) < 1e-9][0]


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.subject = F.TITLE
    cp.keywords = "lab report analysis, OCR, information extraction, health insights, trend tracking"
    cp.last_modified_by = ""
    notes = {}

    X = F.EXTRACTION
    O = X["overall"]
    L = X["per_layout"]
    N = F.NAMES
    LAT = F.LATENCY
    API = F.API_LAT["endpoints"]
    TS = F.TESTS
    INS = F.INSIGHT
    tp = round(O["row_precision"] * O["predicted_rows"])
    fn = O["reports_rows"] - tp
    fp = O["false_positive_rows"]
    FK = X["failure_kinds"]
    name_err = sum(v for k, v in FK.items() if k.startswith("field error") and "name" in k.split(": ")[1].split(","))
    unit_err = sum(v for k, v in FK.items() if k.startswith("field error") and "unit" in k.split(": ")[1].split(","))

    # layout chrome: template deck title in footers
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and "Fraud" in sh.text_frame.text:
                K.replace_text(sh, F.TITLE)
    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE)
        elif sh.name == "Text 2":
            K.replace_text(sh, "Final Review")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_.title()}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE}  ·  Academic Year 2026 – 2027")
    notes[1] = "Introduce the team and the project: LabLens reads a lab report, flags abnormal values, explains them in plain language and tracks them over time."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap & Problem Statement\nObjectives\nProposed System & Architecture\nMethodology, Data & Matching\nDecision Workflow, Interaction & Database\nImplementation Highlights\nResults, Error Analysis, Threshold Analysis, Performance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References")
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, [
        ("Patients receive lab reports full of parameters and reference ranges they cannot interpret; understanding one normally needs a follow-up visit.", {"bullet": True, "space_after": 8}),
        ("**LabLens** reads a PDF or scanned report (PDF text layer; OpenCV + Tesseract for scans), extracts test name, value, unit and reference range, and flags each result Low, Normal or High.", {"bullet": True, "space_after": 8}),
        (f"Abnormal results get plain-language explanations: curated rule-based text for {INS['dictionary_tests_with_specific_text']} of {INS['dictionary_tests']} known tests, generic text otherwise, optional LLM rewrite. Results are stored in SQLite and shown in a React dashboard with trends and report comparison.", {"bullet": True, "space_after": 8}),
        (f"On {len(L) * 15} generated reports ({O['reports_rows']:,} labelled rows): row F1 **{F.f3(O['row_f1'])}**, range accuracy **{F.f3(O['range_acc'])}**, status accuracy **{F.f3(O['status_acc'])}**, unit accuracy {F.f3(O['unit_acc'])}; **{LAT['end_to_end_pipeline_with_db']['median_ms']:.0f} ms** per report; {TS['pytest']['passed']} automated tests pass.", {"bullet": True, "space_after": 8}),
        ("Not built or not measured: PP-OCR, CRF, retrieval-augmented generation and Supabase named in the proposal; scanned-image accuracy (no Tesseract on the test machine); real manually labelled reports.", {"bullet": True}),
    ], size=19)
    notes[3] = "Read the first two bullets, then the headline numbers with their protocol (generated labelled corpus, text-layer PDFs). End on what was not built or measured."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.8, 12.2, 0.75, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper [1]"],
            ["Method", "Retrieval-augmented generation on LLaMA-3 8B; LangChain splitter (1,024 characters, overlap 100), ChromaDB vectors, top-3 chunks with a relevance threshold"],
            ["Knowledge base", "20 medical books, 383 YouTube transcripts (Whisper) and a 33-parameter range document; text extracted with PyMuPDF"],
            ["Scope", "Metabolic syndrome only: 33 blood parameters; personalised diet and lifestyle advice, source citations, login and encrypted storage"],
            ["Evaluation", "20 responses scored 1 to 100 by GPT-4 on correctness, clarity, helpfulness, completeness; no extraction accuracy or latency reported"],
            ["Stated future scope", "Multilingual support, personalisation from repeated tests over time, speech input"]]
    ftable(s, 0.55, 2.65, [2.2, 10.0], rows, size=13, row_h=0.68)
    notes[4] = "The base paper interprets blood reports with RAG for one condition. LabLens takes the goal of plain-language report explanation, but generalises the report parsing and adds the trend tracking the paper lists as future scope."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Author / Year", "Methodology", "Data", "Key result", "Limitation"],
            ["Karhade et al., 2025 [1]", "RAG on LLaMA-3 8B over books and transcripts", "33 metabolic-syndrome parameters", "GPT-4 scores 80 to 100 on 20 responses", "One condition; LLM-judged; no extraction metrics"],
            ["Ren et al., 2025 [2]", "Serialising phone-photographed lab report images into structured records", "Image-based lab reports", "Structured storage of report content", "Method details not reviewed beyond its abstract"],
            ["Xiang et al., 2026 [3]", "Constrained workflow turning check-up reports into action cards", "2,000 de-identified real reports", "Experts: 84% of outputs fully reasonable", "No model best on every dimension; safety limits recall"],
            ["Bakhsheshi & Beigy, 2025 [4]", "General vision-language models read report images; Sentence-BERT compares answers", "100 blood report images", "Practical for preliminary analysis", "Small dataset; answers compared to each other"],
            ["Nguyen et al., 2025 [5]", "Three fine-tuned FLAN-T5-Large models; web and mobile app", "Medical reports and conversations", "Lightweight report summarisation", "Summarises text; no value extraction or trends described"],
            ["Lewis et al., 2020 [6]", "Retrieval-augmented generation", "Knowledge-intensive NLP tasks", "Grounds generation in retrieved text", "Needs a curated corpus (not built here)"]]
    ftable(s, 0.55, 1.8, [2.0, 3.2, 2.2, 2.5, 2.3], rows, size=11, row_h=0.62)
    ftext(s, 0.55, 6.25, 12.2, 0.6, "Three further sources named in the batch survey (laboratory safety, RT-PCR statistics, device extraction testing) concern laboratory practice, not report analysis; they are listed in the report but not used as evidence.", size=11, color=K.FNAVY, italic=True)
    notes[5] = "Representative work on lab and check-up report understanding. Entries are summarised from their abstracts; limitations are those stated by the authors or visible in the setup."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [
        ("**Scope:** the base paper explains blood reports for a single condition; a general platform for arbitrary lab parameters is missing.", {"bullet": True, "space_after": 12}),
        ("**Extraction:** it is evaluated on the quality of generated advice, not on whether test names, values, units and ranges were read correctly.", {"bullet": True, "space_after": 12}),
        ("**History:** no longitudinal view; the base paper itself lists tracking tests over time as future work.", {"bullet": True, "space_after": 12}),
        ("**Digitising versus explaining:** report-digitising work stores values but does not say what an abnormal value means; explanation work does not parse reports.", {"bullet": True, "space_after": 12}),
        ("**Evidence:** generated explanations are rarely tied to a stated source or checked against a fixed rule for what is abnormal.", {"bullet": True}),
    ], size=22)
    notes[6] = "Five gaps drawn from the survey. LabLens addresses scope, extraction measurement, history and the digitise-plus-explain split; grounded retrieval is only partly addressed (curated text, no retrieval)."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.9, 12.2, 1.9)
    ftext(s, 0.85, 1.95, 11.6, 1.8, "Laboratory reports are written for clinicians. Given a PDF or scanned report, **extract every test with its value, unit and reference range, flag the abnormal ones, explain them in plain language, and keep the history** so a patient can see whether a parameter is improving or worsening.", size=19, anchor="m")
    for i, (t, b_) in enumerate([("Input", "PDF, JPG, JPEG or PNG report, up to 15 MB"), ("Output", "Structured results, Low / Normal / High status, explanation for each abnormal value"), ("Record", "Report library, dashboard, trends, side-by-side comparison")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.2, 3.9, 1.9, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.3, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 4.85, 3.5, 1.2, b_, size=15)
    ftext(s, 0.55, 6.3, 12.2, 0.5, "Manual reading is slow and error-prone; existing tools digitise reports but do not explain them and keep no history.", size=13, color=K.FNAVY, italic=True)
    notes[7] = "The statement has three parts: extract and flag, explain, record over time."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 16}) for i, o in enumerate(OBJECTIVES, 1)], size=22)
    notes[8] = "The six objectives of the proposal. The conclusion reports for each whether it was met; objectives 1, 2, 4 and 6 were met only in part."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.05, [("Upload report", K.FNAVY), ("Extract text", K.FBLUE), ("Parse test rows", K.GREEN), ("Classify vs range", K.ORANGE), ("Explain", K.PURPLE), ("Store + trend", K.FNAVY)], size=14, gap=0.3, font=FONT)
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("Text comes from the PDF text layer when there is one; scanned pages and photos go through OpenCV preprocessing and Tesseract.", {"bullet": True, "space_after": 9}),
        ("A line parser reads name, value, unit and range; a TF-IDF matcher snaps noisy names to a 55-name dictionary.", {"bullet": True, "space_after": 9}),
        ("Each value is compared with its range (inclusive limits); abnormal rows receive an explanation, with an optional LLM rewrite that falls back silently.", {"bullet": True, "space_after": 9}),
        ("FastAPI service over the same Python pipeline and SQLite database as the original Streamlit app; React interface with trends and comparison; a not-a-medical-device notice on every screen.", {"bullet": True}),
    ], size=19)
    notes[9] = "The proposed system in one line of boxes, then the four properties that matter."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.4, 1.7, 8.6, 5.25)
    ftext(s, 9.1, 1.95, 3.7, 4.8, [
        ("Presentation: React 18 + Vite + Recharts; original Streamlit app", {"bullet": True, "space_after": 8}),
        ("API: FastAPI, signed bearer token, upload validation", {"bullet": True, "space_after": 8}),
        ("Pipeline: ocr_processor, ner_processor, result_analyzer, ai_insights, report_processor", {"bullet": True, "space_after": 8}),
        ("Data: SQLite through SQLAlchemy, three tables", {"bullet": True}),
    ], size=15)
    notes[10] = "Four tiers. The pipeline modules are shared by the React interface (through FastAPI) and the original Streamlit interface."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.85, 12.2, 1.1, [("Validate (type, size)", K.FNAVY), ("PDF text / OCR", K.FBLUE), ("Parse rows", K.GREEN), ("Snap names", K.PURPLE), ("Classify", K.ORANGE), ("Explain", K.FBLUE), ("Store", K.FNAVY)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.25, 12.2, 3.6, [
        ("**Scans:** a page with fewer than 30 characters of text is rendered at 300 dpi, converted to grey, denoised, adaptively thresholded (Gaussian, block 31) and deskewed before Tesseract (page-segmentation mode 6).", {"bullet": True, "space_after": 8}),
        ("**Rows:** regular expressions read name, value, optional unit, and a range written as a-b, a to b, <x or >x; rows with neither range nor unit are dropped, duplicates removed, confidence 0.9 or 0.6.", {"bullet": True, "space_after": 8}),
        ("**Names:** character n-grams (2 to 4) with TF-IDF and cosine similarity against the dictionary; match accepted at 0.55 or above, otherwise the text is kept.", {"bullet": True, "space_after": 8}),
        ("**Evaluation:** a seeded generator writes labelled report PDFs; the unchanged pipeline reads them and the output is compared with the known answers.", {"bullet": True}),
    ], size=17)
    notes[11] = "The workflow, step by step. The scanned-image branch is implemented but could not be measured because Tesseract is not installed on the test machine."

    # ---- 12 data and matcher
    s = S[11]
    set_title(s, "Evaluation Data, Parser & Name Matcher")
    wipe(s)
    ftile(s, 0.55, 1.85, 2.9, 1.0, f"{O['reports_rows']:,}", "ground-truth rows in 120 generated PDFs", K.FBLUE, 26)
    ftile(s, 0.55, 3.0, 2.9, 1.0, f"{N['n_dictionary_names']}", "dictionary test names", K.GREEN, 26)
    ftile(s, 0.55, 4.15, 2.9, 1.0, f"{INS['knowledge_base_entries']}", "tests with specific explanation text", K.ORANGE, 26)
    ftile(s, 0.55, 5.3, 2.9, 1.0, "0.55", "name-match cosine threshold", K.PURPLE, 26)
    rows = [["Layout", "Example line in the PDF"],
            ["plain", "Hemoglobin 10.8 g/dL 12 - 16"],
            ["paren", "Hemoglobin 10.8 g/dL (12 - 16)"],
            ["flag", "Hemoglobin 10.8 L g/dL 12 - 16"],
            ["colon", "Hemoglobin: 10.8 g/dL   Ref: 12 - 16"],
            ["unit_last", "Hemoglobin 10.8 12 - 16 g/dL"],
            ["mixed_sep", "range written 12 - 16, 12 to 16 or 12-16"],
            ["tabular", "name, value, unit, range as separate text cells"],
            ["ocr_noise", "10% character noise on the test name"]]
    ftable(s, 3.8, 1.85, [1.6, 5.2], rows, size=12, row_h=0.42)
    ftext(s, 3.8, 5.75, 6.8, 1.1, "Each report: 12 dictionary tests + 2 unseen tests, header decoys and a date line; 15 reports per layout; seed 42. Values: about 55% in range, 25% low, 20% high.", size=12, color=K.FNAVY)
    ftext(s, 10.85, 1.85, 2.0, 4.8, [("Honest limit", {"bold": True, "color": K.FNAVY, "size": 14}), ("Labels are generated, not hand-labelled from real reports; PDFs carry a text layer.", {"size": 12})], size=12)
    notes[12] = "The evaluation corpus is synthetic with known answers, because no manually labelled real reports were available. Eight layouts probe the parser; the 'tabular' and 'ocr_noise' layouts are the hard ones."

    # ---- 13 decision workflow
    s = S[12]
    set_title(s, "Decision Workflow")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.55, 1.8, 5.0, 5.1)
    ftext(s, 5.9, 1.95, 6.9, 4.9, [
        ("**Classify:** LOW if value < low; HIGH if value > high; limits are inclusive; UNKNOWN when there is no range. Checked against an independent rule on 20,000 random cases: 0 disagreements.", {"bullet": True, "space_after": 10}),
        ("**Explain:** each LOW or HIGH row gets knowledge-base text or a generic non-specific text; an optional LLM call is used only when a key is configured.", {"bullet": True, "space_after": 10}),
        ("**Persist:** a failure at any stage marks the report Failed with a readable message and keeps the raw text.", {"bullet": True, "space_after": 10}),
        ("**Alert:** the dashboard calls a result critical if it is below half the lower limit or above 1.5 times the upper limit.", {"bullet": True}),
    ], size=16)
    notes[13] = "The core algorithm as a flowchart. The classification rule is deliberately simple and was verified against a separately written rule."

    # ---- 14 interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_diagram.png"), 0.55, 1.8, 7.9, 5.1)
    K.picture(s, F.diag("08_use_case_diagram.png"), 8.6, 1.8, 4.2, 5.1)
    notes[14] = "Left: the sequence of one report upload through the API and pipeline. Right: the use cases of the signed-in user."

    # ---- 15 database
    s = S[14]
    set_title(s, "Database Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 7.0, 4.9)
    rows = [["test_results column", "Type"], ["id, report_id (FK)", "INTEGER"], ["test_name", "TEXT"], ["result_value", "REAL"], ["unit", "TEXT"], ["reference_low / reference_high", "REAL (nullable)"], ["status", "LOW / NORMAL / HIGH / UNKNOWN"], ["test_date", "DATETIME"], ["confidence_score", "REAL 0 to 1"]]
    ftable(s, 7.8, 1.85, [3.1, 2.0], rows, size=12, row_h=0.42)
    ftext(s, 7.8, 6.3, 5.0, 0.8, "reports (1) to test_results (many) to health_insights (many); cascade delete removes a report with everything under it.", size=12, color=K.FNAVY)
    notes[15] = "Three tables. Deleting a report removes its results and insights, which is covered by a test."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("14", "REST endpoints", K.FBLUE), (str(TS["pytest"]["passed"]), "pytest tests passing", K.GREEN), ("10", "React screens", K.ORANGE), ("3", "database tables", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.25, 12.2, 3.6, [
        ("Bearer token signed with HMAC-SHA256 (12 h) and checked in constant time; CORS limited to the local front end; 15 MB limit and an extension whitelist on uploads.", {"bullet": True, "space_after": 9}),
        ("Sample-report loader renders five synthetic PDFs and runs them through the same pipeline, so every screen can be shown with real extracted data.", {"bullet": True, "space_after": 9}),
        ("Trend charts with the reference band, grouped comparison charts, sortable tables, light and dark themes, keyboard support.", {"bullet": True, "space_after": 9}),
        ("Authentication is a single demo account and the library is shared: not suitable for real patient data. One-click start with run.bat.", {"bullet": True}),
    ], size=19)
    notes[16] = "Highlights of the implementation. The last bullet is a limitation: the sign-in is demo-grade."

    # ---- 17 results: extraction performance
    s = S[16]
    set_title(s, "Results – Extraction Performance")
    wipe(s)
    rows = [["Metric (120 generated reports)", "Value"],
            ["Row precision", F.f3(O["row_precision"])],
            ["Row recall", F.f3(O["row_recall"])],
            ["Row F1", F.f3(O["row_f1"])],
            ["Name accuracy (found rows)", F.f3(O["name_acc"])],
            ["Unit accuracy", F.f3(O["unit_acc"])],
            ["Reference-range accuracy", F.f3(O["range_acc"])],
            ["Status accuracy", F.f3(O["status_acc"])],
            ["Exact rows (all four fields right)", F.f3(O["exact_row_rate"])]]
    ftable(s, 0.55, 1.85, [3.5, 1.1], rows, size=13, row_h=0.43, align=["l", "c"])
    order = ["plain", "paren", "flag", "colon", "unit_last", "mixed_sep", "tabular", "ocr_noise"]
    K.bar_chart(s, 5.4, 1.75, 7.4, 4.35, order, [("Row F1", [L[k]["row_f1"] for k in order]), ("Exact-row rate", [L[k]["exact_row_rate"] for k in order])],
                colors=[K.FBLUE, K.ORANGE], number_format="0.00", font_size=11, max_value=1.15, gap=50, label_size=9)
    ftext(s, 0.55, 5.9, 4.7, 1.0, f"Cell-per-line table layout: 0 of 210 rows read. Names of the {N['n_dictionary_names']} dictionary tests: {F.f3(O['name_acc_dict_tests'])}; unseen tests: {F.f3(O['name_acc_ood_tests'])}.", size=12, color=K.FNAVY)
    ftext(s, 5.4, 6.2, 7.4, 0.7, "Text-layer PDFs only; ground truth is generated. Scanned images were not measured (Tesseract not installed).", size=12, color=K.FNAVY, italic=True)
    notes[17] = "Protocol: 120 generated reports, 8 layouts x 15, 1,680 labelled rows, seed 42. Row F1 is high on every single-line layout; the table layout, where each cell is its own text line, scores zero."

    # ---- 18 error analysis
    s = S[17]
    set_title(s, "Error Analysis (Row-level Confusion)")
    wipe(s)
    ftile(s, 0.55, 1.85, 3.9, 1.05, f"{tp:,}", "rows found (true positives)", K.GREEN, 28)
    ftile(s, 4.7, 1.85, 3.9, 1.05, f"{fn}", "rows missed (false negatives)", K.ORANGE, 28)
    ftile(s, 8.85, 1.85, 3.9, 1.05, f"{fp}", "rows invented (false positives)", K.PURPLE, 28)
    rows = [["Error", "Rows", "Cause found in the failure cases"],
            ["Missed rows", f"{fn}", f"All 210 rows of the cell-per-line table layout (each cell is a separate text line); 2 more in the noisy-name layout"],
            ["Unit wrong or missing", f"{unit_err}", "Unit outside the regular-expression list (uIU/mL, mg/L, umol/L, ng/dL, ug/dL, pg/mL); a flag letter L or H between value and unit"],
            ["Name wrong", f"{name_err}", "Unseen tests snapped to a dictionary name (Sodium Bicarbonate read as Sodium); heavy character noise"],
            ["False rows", f"{fp}", "55 are the header date line (Sample Collected: 12-04-2026) read as a test with range -4 to 2026; 2 others (one mis-read name, one date row matched to a real RDW value of 12)"],
            ["Status wrong", "1", "Range and status are almost always right once a row is found"]]
    ftable(s, 0.55, 3.15, [2.3, 0.9, 9.0], rows, size=12, row_h=0.56, align=["l", "c", "l"])
    notes[18] = "A confusion-style breakdown: found, missed and invented rows, and the cause of each error class read from the failure cases saved in experiments/lablens/failure_cases.json. These are concrete defects, listed as future work."

    # ---- 19 threshold analysis
    s = S[18]
    set_title(s, "Threshold & Parameter Analysis (Name Matcher)")
    wipe(s)
    K.picture(s, F.fig("fig_threshold_sweep.png"), 0.55, 1.7, 6.1, 3.05)
    nz0 = F.NAMES["noise"]
    ftext(s, 6.75, 1.68, 6.0, 0.3, "Name accuracy against simulated per-character noise (55 names x 30 trials)", size=11, color=K.FNAVY, bold=True)
    K.bar_chart(s, 6.75, 1.95, 6.0, 2.85, ["0%", "5%", "10%", "20%"],
                [("TF-IDF 0.55 (shipped)", [nz0[r]["tfidf_0.55"] for r in ("0.0", "0.05", "0.1", "0.2")]),
                 ("difflib 0.60 (baseline)", [nz0[r]["difflib_0.60"] for r in ("0.0", "0.05", "0.1", "0.2")]),
                 ("Exact match", [nz0[r]["exact_match"] for r in ("0.0", "0.05", "0.1", "0.2")])],
                colors=[K.FBLUE, K.ORANGE, K.RGBColor(0x9E, 0x9E, 0x9E)], number_format="0.00", font_size=10, max_value=1.15, gap=60, label_size=8)
    a30, a55, a80 = sweep(0.3), sweep(0.55), sweep(0.8)
    nz = N["noise"]
    rows = [["Matcher / threshold", "Accuracy at 10% noise", "Accuracy at 20% noise", "Unseen names wrongly snapped", "Synonyms right"],
            ["TF-IDF 0.30", F.f3(a30["acc_noise_10"]), F.f3(a30["acc_noise_20"]), F.pct(a30["false_snap_rate_ood"], 0), F.pct(a30["synonym_acc"], 0)],
            ["TF-IDF 0.55 (shipped)", F.f3(a55["acc_noise_10"]), F.f3(a55["acc_noise_20"]), F.pct(a55["false_snap_rate_ood"], 0), F.pct(a55["synonym_acc"], 0)],
            ["TF-IDF 0.80", F.f3(a80["acc_noise_10"]), F.f3(a80["acc_noise_20"]), F.pct(a80["false_snap_rate_ood"], 0), F.pct(a80["synonym_acc"], 0)],
            ["difflib ratio 0.60 (baseline)", F.f3(nz["0.1"]["difflib_0.60"]), F.f3(nz["0.2"]["difflib_0.60"]), "not measured", "not measured"]]
    ftable(s, 0.55, 4.9, [3.2, 2.2, 2.2, 2.9, 1.7], rows, size=12, row_h=0.36, align=["l", "c", "c", "c", "c"])
    ftext(s, 0.55, 6.75, 12.2, 0.3, "Sweep and noise bars use separate random trials, so the 20% TF-IDF figure differs slightly (0.718 vs 0.731).", size=10, color=K.FNAVY, italic=True)
    notes[19] = ("The threshold is a trade-off: lower values rescue noisy names but wrongly rename unseen tests. 0.55 is a middle choice. A plain difflib matcher was more noise-tolerant on the dictionary names but was not adopted; its false-snap rate was not measured.")

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{LAT['text_layer_extraction']['median_ms']:.1f} ms", "PDF text layer (1 page)", K.FBLUE), (f"{LAT['field_extraction']['median_ms']:.1f} ms", "field extraction, 14 rows", K.GREEN),
                                   (f"{LAT['end_to_end_pipeline_with_db']['median_ms']:.0f} ms", "whole pipeline incl. database", K.ORANGE), (f"{API['POST /api/reports (PDF upload)']['median_ms']:.0f} ms", "HTTP PDF upload, median", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["pytest", "classification boundaries, extraction, name matching, OCR input checks, insights, pipeline, cascade delete, dashboard, API auth, upload, trend, compare, seed", f"{TS['pytest']['passed']} passed, {TS['pytest']['failed']} failed"],
            ["Live smoke test", "running API in a temporary copy, plus browser flow on the built front end", f"{TS['smoke_test']['api_checks_passed']} API + {TS['smoke_test']['browser_checks_passed']} browser checks passed"],
            ["Classification rule", "20,000 random value and range cases against an independent rule", f"{F.CLASSIF['disagreements_with_reference_rule']} disagreements"],
            ["Not measured", "scanned-image OCR speed and accuracy, LLM explanations, many users, real reports", "stated as gaps"]]
    ftable(s, 0.55, 3.2, [2.3, 7.0, 2.9], rows, size=12, row_h=0.62)
    ftext(s, 0.55, 6.4, 12.2, 0.5, f"The proposal's target of under 10 seconds per report is met for text-layer PDFs (field extraction grows linearly: about {F.LATENCY['field_extraction_scaling_by_rows']['200']['median_ms']:.0f} ms for 200 rows). Machine: i5-12500, 15.7 GB, no GPU.", size=12, color=K.FNAVY, italic=True)
    notes[20] = "All timings are medians on a CPU-only desktop, measured against 127.0.0.1. The test table shows what passed and, in the last row, what was never measured."

    # ---- 21 comparison with base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only – different task and data)")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "LabLens"],
            ["Task", "Answer questions about a blood report for metabolic syndrome with RAG", "Read any lab report, flag abnormal values, explain, track trends"],
            ["Input", "Blood test reports from users; 33 chosen parameters", f"PDF or image reports; {N['n_dictionary_names']} known test names, other tests kept as read"],
            ["Language model", "LLaMA-3 8B with retrieval over books and transcripts", "No generative model needed; rule-based text, optional LLM rewrite (not exercised)"],
            ["How quality was judged", "GPT-4 scored 20 responses, 1 to 100; stated averages 92.4 / 89.7 / 91.1 / 88.9 (Table 4 recomputes to 94.0 / 94.9 / 90.1 / 88.65)", f"Extraction row F1 {F.f3(O['row_f1'])}, status accuracy {F.f3(O['status_acc'])} on {O['reports_rows']:,} generated rows; explanation quality not scored"],
            ["History over time", "Listed as future scope", "Trend chart, direction and report comparison implemented"],
            ["Deliverable", "RAG chatbot with login", "Web application, 14 API endpoints, tests"]]
    ftable(s, 0.55, 1.8, [2.0, 5.4, 4.8], rows, size=12, row_h=0.66)
    ftext(s, 0.55, 6.5, 12.2, 0.45, "Not like-for-like: the scores measure different things on different data, so neither set of numbers ranks one system above the other.", size=13, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that tasks and data differ. The base paper's own stated averages differ from the averages recomputed from its Table 4; both are shown."

    # ---- 22-24 output screens
    def screens(slide, title, left, right, cap_l, cap_r, note):
        set_title(slide, title)
        wipe(slide)
        K.picture(slide, left, 0.55, 1.8, 6.0, 4.4, border=True)
        K.picture(slide, right, 6.8, 1.8, 6.0, 4.4, border=True)
        ftext(slide, 0.55, 6.3, 6.0, 0.6, cap_l, size=12, color=K.FNAVY)
        ftext(slide, 6.8, 6.3, 6.0, 0.6, cap_r, size=12, color=K.FNAVY)
        return note

    notes[22] = screens(S[21], "Output – Upload and Dashboard", crop("06_upload_done.png", 900), crop("04_dashboard.png", 900),
                        "Upload: pipeline stages completed, 14 tests extracted and classified.", "Dashboard: totals, critical-result alert and recent reports.",
                        "Left: a report processed; the stage list ends with database storage and health insights. Right: dashboard across six reports (82 tests, 28 abnormal, 2 critical). All data is synthetic.")
    notes[23] = screens(S[22], "Output – Report Analysis and Health Trends", crop("07_report_analysis.png", 900), crop("09_health_trends.png", 1000),
                        "Report analysis: each result with range and Low / High status.", "Trends: haemoglobin across six reports with the reference band.",
                        "Left: results table with explanations below for abnormal rows. Right: trend of one test over time, 10.8 to 13.1 g/dL.")
    notes[24] = screens(S[23], "Output – Report Comparison and Health Insights", crop("10_compare_reports.png", 900), crop("11_health_insights.png", 900),
                        "Compare: two reports side by side with change per test.", "Insights: every abnormal result with its plain-language explanation.",
                        "Left: change between the first and the fifth report. Right: consolidated insight cards with causes stated in general terms and a suggestion to see a doctor.")

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, [
        ("**Delivered:** a working report-to-insight pipeline with a React and FastAPI application: extraction, Low / Normal / High flagging, explanations, history, trends, comparison and tests.", {"bullet": True, "space_after": 8}),
        (f"**Measured:** row F1 {F.f3(O['row_f1'])}, range accuracy {F.f3(O['range_acc'])}, status accuracy {F.f3(O['status_acc'])}, {LAT['end_to_end_pipeline_with_db']['median_ms']:.0f} ms per report, on generated labelled reports.", {"bullet": True, "space_after": 8}),
        ("**Met:** objective 3 (flagging) and objective 5 (trends). **Partly met:** 1 (text-layer PDFs timed; scan OCR unmeasured), 2 (regex and TF-IDF, not CRF; tables fail), 4 (curated text for 17 of 55 tests, no retrieval), 6 (dashboard yes; evaluation on generated, not hand-labelled, reports).", {"bullet": True, "space_after": 8}),
        ("**Weak points found:** cell-per-line tables, missing units, date lines read as tests, unseen tests renamed to a similar known test.", {"bullet": True, "space_after": 8}),
        ("An educational tool, not a medical device; sign-in is demo-grade.", {"bullet": True}),
    ], size=19)
    notes[25] = "Objectives reported honestly: two met, four partly. The proposal named PP-OCR, CRF, RAG and Supabase; what was built instead is stated on the slide."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [
        ("Read table layouts by header and column, widen the unit list, and ignore date and patient lines (fixes the main measured errors).", {"bullet": True, "space_after": 10}),
        ("Measure scanned and photographed reports with Tesseract, and compare against PP-OCR or a vision-language model [4].", {"bullet": True, "space_after": 10}),
        ("Add retrieval over a curated, cited medical corpus for explanations [1][6]; extend text from 17 tests to the full dictionary and add a synonym table.", {"bullet": True, "space_after": 10}),
        ("Evaluate on consented, manually labelled real reports; fit the name-matcher threshold on them.", {"bullet": True, "space_after": 10}),
        ("Per-user accounts with database-level isolation, a hosted database, test-date axis and slope-based trend direction.", {"bullet": True}),
    ], size=21)
    notes[26] = "Concrete next steps, ordered by the measured errors first."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    left = [ref_no(f) for f in ("RAG-based blood test", "serialization method", "Checkup2Action", "blood report images", "Medalyze", "Retrieval-augmented generation for knowledge", "PP-OCR")]
    right = [ref_no(f) for f in ("Tesseract", "Conditional random fields", "Term-weighting", "Scikit-learn", "The OpenCV library", "Sentence-BERT", "PyMuPDF")]
    ftext(s, 0.55, 1.8, 6.0, 5.1, [(f"[{n}] {REFS[n - 1]}", {"space_after": 5}) for n in left], size=12)
    ftext(s, 6.8, 1.8, 6.0, 5.1, [(f"[{n}] {REFS[n - 1]}", {"space_after": 5}) for n in right], size=12)
    notes[27] = "Selected references; the complete list is in the report."

    # ---- 28 thank you
    s = S[27]
    for sh in s.shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path, "LabLens")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
