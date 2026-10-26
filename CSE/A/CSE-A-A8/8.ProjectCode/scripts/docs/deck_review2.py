"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, fill_title_slide, finish, prepare, set_title, thank_you, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"

LAYOUTS = ["plain", "paren", "flag", "colon", "unit_last", "mixed_sep", "tabular", "ocr_noise"]


def crop_shot(name, box, out_name):
    """Crop a real screenshot (no editing of content) so a tall page fits a slide."""
    from PIL import Image

    os.makedirs(os.path.join(F.FIGS, "_crops"), exist_ok=True)
    out = os.path.join(F.FIGS, "_crops", out_name)
    with Image.open(F.shot(name)) as im:
        im.convert("RGB").crop(box).save(out)
    return out


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    X = F.EXTRACTION
    O = X["overall"]
    L = X["per_layout"]
    tests = F.TESTS or {}
    n_py = tests.get("pytest", {}).get("passed", 0)
    n_api = tests.get("smoke_test", {}).get("api_checks_passed", 0)
    n_ui = tests.get("smoke_test", {}).get("browser_checks_passed", 0)
    lat = F.LATENCY
    api = (F.API_LAT or {}).get("endpoints", {})
    up = api.get("POST /api/reports (PDF upload)", {})

    # ---- 1 title
    fill_title_slide(S[0], "Design, methodology and progress: a working pipeline from uploaded report to flagged results, explanations and trends",
                     "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how the system is designed and built, what was implemented against the abstract, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and extraction model"), ("04", "Configuration and decision logic"),
               ("05", "Data flow, database and UML"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Lab reports are written for clinicians. Patients cannot interpret them, manual reading is slow and error-prone, digitising tools do not explain, and no history is kept.", K.ORANGE, "!"),
        ("Proposed system", "Read the report, extract test, value, unit and range, flag Low, Normal or High, explain abnormal values in plain language and track every parameter across reports.", K.BLUE, "i"),
        ("Link to the base paper", "Keeps its idea of patient-friendly explanation from curated knowledge, but covers any lab parameter, measures extraction, and adds trends. Its LLaMA-3 retrieval pipeline is not reproduced.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.7, t, b_, col, gl, body_size=20)
    notes[3] = "One-minute recap of Review 1. The base paper handles one condition with RAG; this project is a general platform whose extraction is measured."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.7, 5.5)
    K.text(s, 8.55, 1.5, 4.2, 5.3, [
        ("**Tiers**", {"space_after": 8}),
        ("React single-page app, port 5308.", {"bullet": True}),
        ("FastAPI service, port 8308, signed-token login, upload validation.", {"bullet": True}),
        ("Pipeline modules: ocr_processor, ner_processor, result_analyzer, ai_insights, report_processor.", {"bullet": True}),
        ("SQLite through SQLAlchemy: reports, test results, insights.", {"bullet": True}),
        ("The original Streamlit app runs on the same modules and database.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The API layer imports the same pipeline modules as the original Streamlit app, so both interfaces give identical results on the same file."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: end-to-end workflow")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.35, [("Upload and validate", K.NAVY), ("Text: PDF layer or OCR", K.PURPLE), ("Parse test rows", K.BLUE), ("Classify against range", K.GREEN),
                                      ("Explain abnormal values", K.ORANGE), ("Store in SQLite", K.NAVY), ("Dashboard, trends, compare", K.BLUE)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("Fail-safe stages", "Any stage failure marks the report Failed with a readable message and keeps the raw text when there is any; nothing partial is shown as a result."),
                                 ("One pipeline", "Web upload, the Streamlit app and the demo-data seeder all call the same process_uploaded_report function."),
                                 ("Measured, not assumed", "A generated corpus of labelled PDFs (seed 42) scores each stage: row recall, field accuracy, name matching, latency.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.3, 3.85, 3.2)
        K.text(s, x + 0.25, 3.45, 3.4, 0.5, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 4.05, 3.4, 2.3, b_, size=17, color=K.TXT)
    notes[5] = "Seven steps from upload to dashboard. The same function runs for every entry point, so the evaluation of the pipeline applies to all of them."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: a generated, labelled evaluation corpus")
    wipe(s)
    for i, (v, l, c) in enumerate([("120", "synthetic lab-report PDFs", K.BLUE), ("1,680", "ground-truth test rows", K.GREEN), ("8", "report layouts, 15 reports each", K.ORANGE), ("55", "names in the test dictionary", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.4, 2.9, 1.2, v, l, c, vsize=28, lsize=12)
    rows = [["Layout", "Example line"],
            ["plain", "Hemoglobin 10.8 g/dL 12 - 16"], ["paren", "... g/dL (12 - 16)"], ["flag", "Sodium 134 L mEq/L 135 - 145"], ["colon", "Hemoglobin: 10.8 g/dL   Ref: 12 - 16"],
            ["unit_last", "Hemoglobin 10.8 12 - 16 g/dL"], ["mixed_sep", "range written 12 - 16, 12 to 16 or 12-16"], ["tabular", "name, value, unit, range on separate lines"], ["ocr_noise", "10 % character noise on test names"]]
    K.table(s, 0.6, 2.85, [1.5, 4.7], rows, font_size=13, row_h=0.45, first_bold=True)
    K.text(s, 7.2, 2.9, 5.5, 3.9, [
        ("Each report has 12 dictionary tests and 2 tests outside it, plus header decoys and a date line.", {"bullet": True}),
        ("Values: about 55 % in range, 25 % low, 20 % high; ground truth is generated with the PDF.", {"bullet": True}),
        ("Five 14-test demo reports (April to October 2026) feed the screenshots.", {"bullet": True}),
        ("**Limit:** no manually labelled real reports were available, so these numbers describe the parser on clean digital PDFs, not on real scans.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[6] = "All data is invented and reproducible from scripts/run_experiments.py. It is the only labelled data the project has; real scanned reports are not measured."

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing: text layer, then image clean-up")
    wipe(s)
    K.flow(s, 0.6, 1.4, 12.13, 0.95, [("PDF page", K.NAVY), ("30+ characters in text layer?", K.PURPLE), ("Yes: use text", K.GREEN), ("No: render 300 dpi", K.ORANGE), ("Clean up + Tesseract", K.BLUE)], size=13, gap=0.25)
    K.picture(s, F.fig("ocr_preprocess_demo.png"), 0.6, 2.6, 8.0, 3.3)
    K.text(s, 8.9, 2.65, 3.85, 3.3, [
        ("1  Grayscale", {}), ("2  Denoise (non-local means, h = 10)", {}), ("3  Gaussian adaptive threshold, block 31, C = 15", {}), ("4  Deskew with minAreaRect (if skew is 0.5 degrees or more)", {}), ("5  Tesseract, page-segmentation mode 6", {}),
    ], size=16, color=K.INK, space_after=8)
    K.text(s, 0.6, 6.05, 12.13, 0.8, "The left image is a clean rendered page with a simulated scan defect (2 degree rotation, noise, uneven light); the right image is the real output of preprocess_image_for_ocr. Tesseract is not installed on the build machine, so OCR accuracy on scans is not measured.", size=12, color=K.TXT, italic=True)
    notes[7] = "Digital PDFs skip the image path completely. The image path exists and its first stage works as shown, but scan accuracy is a stated gap."

    # ---- 8 extraction model
    s = S[7]
    set_title(s, "Extraction model: parser and name matcher")
    wipe(s)
    rows = [["Component", "Technique", "Setting"],
            ["Row parser, stage 1", "Regular expression: name, value, optional unit", "line starts with a letter; header lines skipped"],
            ["Row parser, stage 2", "Range: a-b, a to b, a – b, <x, >x; trailing unit", "rows with neither range nor unit dropped"],
            ["Name matcher", "TF-IDF on character n-grams, cosine similarity", "n-grams 2-4, 55 names, threshold 0.55"],
            ["Confidence score", "0.9 with two-sided range, 0.6 otherwise", "minus 0.1 when no unit is found"],
            ["Classifier", "Low / Normal / High / Unknown by reference range", "limits inclusive"],
            ["Explanation", "Rule-based text, optional LLM rewrite", "17 test entries plus generic wording"]]
    K.table(s, 0.6, 1.4, [2.35, 5.3, 4.48], rows, font_size=14, row_h=0.58, first_bold=True)
    for i, (v, l, c) in enumerate([("55", "dictionary names", K.BLUE), ("17", "tests with specific explanation text", K.GREEN), ("0", "learned weights: nothing is trained", K.ORANGE)]):
        K.tile(s, 0.6 + i * 4.14, 5.65, 3.85, 1.15, v, l, c, vsize=26, lsize=12)
    notes[8] = ("A hybrid of rules and a small similarity model. The abstract planned a CRF tagger; none was built, and the module comment says a CRF can be swapped in later. "
                "The only fitted component is the TF-IDF vocabulary over the 55 dictionary names.")

    # ---- 9 configuration
    s = S[8]
    set_title(s, "Configuration: parameters, not training")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Scanned-page resolution", "300 dpi; a page is OCR'd when its text layer has fewer than 30 characters"],
            ["Image clean-up", "denoise h = 10; Gaussian adaptive threshold, block 31, C = 15; deskew from 0.5 degrees"],
            ["Name matcher", "character n-grams 2 to 4, cosine similarity at least 0.55, 55 dictionary names"],
            ["Upload limits", "PDF, JPG, JPEG or PNG; at most 15 MB; empty and corrupt files rejected"],
            ["Critical alert", "Low below 0.5 x lower limit or High above 1.5 x upper limit"],
            ["Evaluation", "seed 42, 120 generated reports, 1,680 rows, one CPU (Intel Core i5-12500), no GPU"]]
    K.table(s, 0.6, 1.5, [3.0, 9.13], rows, font_size=15, row_h=0.7, first_bold=True)
    notes[9] = "There is no training stage, so this slide lists the tunable values instead. The threshold 0.55 is analysed on the results slide."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.4, 5.55)
    K.text(s, 6.3, 1.5, 6.4, 5.3, [
        ("**Validate.** Extension, size and readability are checked; each failure gives a clear message and the report is marked Failed.", {"bullet": True, "space_after": 10}),
        ("**Classify.** Below the lower limit is LOW, above the upper limit is HIGH, otherwise NORMAL; a one-sided range such as <100 uses only its bound; no range gives UNKNOWN.", {"bullet": True, "space_after": 10}),
        ("**Explain.** LOW and HIGH rows get a knowledge-base entry or generic wording; the text states it is educational and never names a disease.", {"bullet": True, "space_after": 10}),
        ("**Check.** The rule agreed with an independent reference on 20,000 random cases with 0 differences.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[10] = "The decision rule is deliberately simple and deterministic. The explanation text is the only part that can optionally use a language model."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 7.2, 5.5)
    rows = [["Module", "Role"], ["ocr_processor.py", "validate, PDF text, OCR"], ["ner_processor.py", "rows, units, ranges, names"], ["result_analyzer.py", "Low / Normal / High"], ["ai_insights.py", "explanations"],
            ["report_processor.py", "stage orchestration"], ["database.py", "SQLAlchemy storage"], ["backend/main.py", "API and login"]]
    K.table(s, 8.1, 1.4, [2.35, 2.28], rows, font_size=12, row_h=0.5)
    notes[11] = "Level-1 data flow. Levels 0 and 2 are in the report. The module table lists where each process lives."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.6, 1.35, 5.4, 5.1)
    K.picture(s, F.diag("06_uml_class_diagram.png"), 6.1, 1.3, 6.63, 5.2)
    K.text(s, 0.6, 6.55, 12.13, 0.35, "Three tables: reports, test_results, health_insights; deleting a report cascades to its results and insights.", size=12, color=K.TXT, align="c", italic=True)
    notes[12] = "Each report owns many test results; each abnormal result owns one insight. The class diagram shows the code-level structure."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    m = (F.TESTS or {}).get("machine", {})
    rows = [["Layer", "Technology"],
            ["PDF and images", f"PyMuPDF {m.get('pymupdf', '')}, OpenCV {m.get('opencv', '')}, pytesseract with Tesseract (optional)"],
            ["Parsing and matching", f"regular expressions, scikit-learn {m.get('scikit_learn', '')} TF-IDF; spaCy optional (patient name only)"],
            ["API", f"FastAPI {m.get('fastapi', '')}, Uvicorn, python-multipart"],
            ["Database", f"SQLite with SQLAlchemy {m.get('sqlalchemy', '')}"],
            ["Front end", f"React {m.get('react', '')}, Vite {m.get('vite', '')}, React Router, Recharts {m.get('recharts', '')}"],
            ["Optional LLM", "Anthropic API for rewriting explanations; falls back silently without a key"],
            ["Testing and run", "pytest, Playwright browser smoke test; run.bat starts both servers"]]
    K.table(s, 0.6, 1.5, [2.9, 9.23], rows, font_size=15, row_h=0.62, first_bold=True)
    notes[13] = "Open-source stack. The abstract named Supabase, Tailwind and cloud functions; the implementation uses SQLite, hand-written styles and a local FastAPI service."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress against the abstract")
    wipe(s)
    rows = [["Component", "Abstract", "Built", "Status"],
            ["Text extraction", "PP-OCR", "PyMuPDF text layer, Tesseract fallback", "Built; scans unmeasured"],
            ["Field extraction", "CRF NER", "regex parser + TF-IDF name matcher", "Built; no CRF"],
            ["Flagging", "range comparison", "classify_result rule", "Done, 0 / 20,000 differ"],
            ["Explanations", "RAG + LLM", "17-entry rule base, optional LLM", "Partial: no retrieval"],
            ["Storage", "Supabase", "SQLite + SQLAlchemy", "Done; no row-level security"],
            ["Interface", "React, Tailwind", "React, Vite, Recharts, 11 pages", "Done; no Tailwind"],
            ["Deployment", "Cloud Functions", "local FastAPI via run.bat", "Not serverless"],
            ["Speed", "under 10 s", f"{lat['end_to_end_pipeline_with_db']['median_ms']:.0f} ms pipeline, {up.get('median_ms', 0):.0f} ms upload", "Met for text PDFs"]]
    K.table(s, 0.6, 1.4, [2.1, 2.3, 4.5, 3.23], rows, font_size=14, row_h=0.6, first_bold=True)
    notes[14] = "The honest comparison with the abstract. Timings are medians on the build machine for a 14-row digital PDF."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: field extraction on 120 reports")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.f3(O["row_f1"]), "row F1", K.BLUE), (F.f3(O["row_precision"]), "row precision", K.GREEN), (F.f3(O["row_recall"]), "row recall", K.ORANGE), (F.pct(O["exact_row_rate"]), "rows fully correct", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.4, 2.9, 1.2, v, l, c, vsize=28, lsize=12)
    cats = LAYOUTS
    K.bar_chart(s, 0.6, 2.8, 8.0, 4.1, [c.replace("_", " ") for c in cats],
                [("Row recall", [L[c]["row_recall"] for c in cats]), ("Unit accuracy", [L[c]["unit_acc"] or 0 for c in cats]), ("Rows fully correct", [L[c]["exact_row_rate"] for c in cats])],
                colors=[K.BLUE, K.GREEN, K.ORANGE], number_format="0.00", font_size=10, max_value=1.15, gap=40, label_size=8)
    K.card(s, 8.9, 2.85, 3.83, 4.0, "Reading", f"Single-line layouts: recall 1.00. The tabular layout, with one cell per line, yields 0 rows. Units are the weak field ({F.pct(O['unit_acc'])}); range and status are {F.pct(O['range_acc'])} and {F.pct(O['status_acc'])}. Clean digital PDFs only.", K.BLUE, "i", body_size=15)
    notes[15] = ("1,680 ground-truth rows, 1,525 predicted. Precision is limited by 57 false rows (55 of them a date line read as a test). The grouped chart shows the tabular layout failing "
                 "completely and the flag layout losing units because the L/H letter sits between value and unit.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    a = crop_shot("07_report_analysis.png", (0, 0, 1440, 1000), "r2_report_analysis_top.png")
    t_ = crop_shot("09_health_trends.png", (0, 0, 1440, 900), "r2_health_trends_top.png")
    K.picture(s, a, 0.6, 1.3, 5.9, 4.3, border=True)
    K.picture(s, F.shot("04_dashboard.png"), 6.75, 1.3, 5.98, 2.7, border=True)
    K.picture(s, t_, 6.75, 4.25, 5.98, 2.7, border=True)
    K.text(s, 0.6, 5.7, 5.9, 1.2, "Report analysis: the extracted table with Low / High flags (cropped from the full page)", size=13, color=K.TXT, italic=True)
    notes[16] = "Real screenshots of the running application with the five sample reports plus one uploaded report: report analysis, dashboard and a trend chart. The data is synthetic."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(str(n_py), "pytest tests passed", K.GREEN), (f"{n_api} + {n_ui}", "API + browser smoke checks passed", K.BLUE), ("20,000", "random classification cases, 0 differences", K.ORANGE), ("0", "failures in the final runs", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.4, 2.9, 1.2, v, l, c, vsize=26, lsize=12)
    rows = [["Layer", "What the tests check"],
            ["Classification and parsing", "range boundaries, one-sided ranges, header lines, duplicates, test dates, noisy names"],
            ["Input handling", "unsupported type, empty file, oversize file, corrupt PDF"],
            ["Pipeline and database", "stored rows and statuses, failed report, cascade delete, critical-alert count"],
            ["API", "login, tampered token, upload to trend to compare to insights, demo seeding"],
            ["Browser", "login redirect, charts render, wrong file type rejected, Escape closes dialog, no console errors"]]
    K.table(s, 0.6, 2.85, [3.2, 8.93], rows, font_size=14, row_h=0.62, first_bold=True)
    notes[17] = "All tests run offline against a temporary database. The browser checks need a built frontend. Scanned-image OCR is not covered because Tesseract is not installed on the build machine."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges found and responses")
    wipe(s)
    rows = [["Challenge", "Measured evidence", "Response"],
            ["Table PDFs with one cell per line", "0 of 210 rows read", "documented; joining cells by position planned"],
            ["Date line parsed as a test row", f"55 of {O['false_positive_rows']} false rows", "documented; date filter planned"],
            ["Units missing from the list", f"unit accuracy {F.pct(O['unit_acc'])}", "list extension planned (mg/L, ng/dL, uIU/mL ...)"],
            ["Unseen names snapped to a dictionary entry", "Sodium Bicarbonate read as Sodium", "threshold trade-off analysed (0.55 shipped)"],
            ["Only 17 of 55 tests have explanations", f"{F.pct(F.INSIGHT['abnormal_rows_specific_rate'])} of abnormal rows specific", "generic wording used; base to be expanded"],
            ["No real labelled or scanned reports", "corpus is generated; OCR unmeasured", "stated as a limit"]]
    K.table(s, 0.6, 1.4, [3.9, 3.9, 4.33], rows, font_size=15, row_h=0.78)
    notes[18] = "These came out of the measurements, not from guesswork. The first three are bugs or gaps in the parser; the last two are limits of the data and the explanation base."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Fix the parser", "Handle cell-per-line tables, skip date lines, extend the unit list, then re-run the same 120-report corpus.", K.BLUE, "1"),
        ("Measure scans", "Install Tesseract and build a small set of labelled scanned reports to measure OCR accuracy and latency.", K.GREEN, "2"),
        ("Better matching", "Compare the TF-IDF matcher with an edit-distance matcher, which scored higher under noise in our test.", K.ORANGE, "3"),
        ("Final documents", "Final report, paper and deck with every number regenerated from the experiment files.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.083, 1.6, 2.88, 4.6, t, b_, col, gl, body_size=18)
    notes[19] = "The plan to the final review. Real-report labelling and the retrieval-based explanation of the base paper remain future work."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why no CRF; why TF-IDF for names; why SQLite; how the explanations avoid diagnosis; what is not measured."

    return finish(prs, S, notes, out_path)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
