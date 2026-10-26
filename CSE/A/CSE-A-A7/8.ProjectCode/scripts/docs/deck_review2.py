"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers (prepare, set_title, wipe, agenda, title_slide, thank_you) are defined here so the deck does not depend on
the Review 1 module. All numbers come from facts.py (experiments/**/metrics.json); nothing is typed in by hand.
Every model number is measured on the seeded synthetic dataset; the deck says so wherever results appear.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "emergency triage, scanned reports, OCR, XGBoost, SHAP, explainable AI, clinical decision support"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 30)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 20)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched)."""
    import tempfile

    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"a7_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    C = F.COMP
    xgb, lr = C["XGBoost (shipped config)"], C["Logistic regression"]
    fused, vit, rep = F.ABL["Fused (36)"], F.ABL["Vitals only (8)"], F.ABL["Report only (28)"]
    t85, t70, t50 = F.thr_row(0.85), F.thr_row(0.7), F.thr_row(0.5)
    r10 = F.rob_row(0.1)
    SF = F.SAFE
    scan_ms, pdf_ms = F.lat("extract_scan_png"), F.lat("extract_pdf")

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a scanned report and eight vitals fused into an explainable priority from 1 to 5",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how ATHENA is designed and built, what is implemented, the first measured results and the open items. "
                "All model results are on a seeded synthetic dataset, and we say so on every results slide. Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Report reading and fusion"), ("04", "Model and training"),
               ("05", "Decision logic and data flow"), ("06", "Entities, UML, technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Triage decides who is seen first, but it varies with the person on duty and under-identifies critical illness. Models built on structured fields cannot see a scanned report, and a bare prediction with no reasons is not accepted at the bedside.", K.ORANGE, "!"),
        ("Proposed system", "ATHENA reads a PDF or scan, takes eight vitals, fuses them into 36 inputs, and gives a calibrated priority 1 to 5 with the strongest reasons (SHAP). The clinician accepts or changes it; the reason is stored.", K.BLUE, "i"),
        ("Base paper link [1]", "Mlodawski et al. compare 19 classifiers on typed symptoms, rank diagnoses (TOP-1 / TOP-3) and explain with SHAP and LIME. We keep ranking, a confidence threshold and SHAP, and add scanned reports, vitals and a priority target. Results are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=18)
    notes[3] = ("Recap of Review 1: the survey gap is that models are evaluated on single-modality structured data. ATHENA fuses a scanned report with the vitals and shows the reasoning. "
                "The base paper is a diagnostic comparison on typed data with a different target, so numbers are never put side by side without that caveat.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.0, 5.7)
    K.text(s, 7.9, 1.45, 4.85, 5.4, [
        ("**Three tiers, one file database**", {"space_after": 8}),
        (f"Browser: React 19 single-page app (port {F.WEB_PORT}), six screens, dark mode, proxy to /api.", {"bullet": True}),
        (f"Server: FastAPI (port {F.API_PORT}), 13 endpoints, JWT bearer tokens, 15 MB upload cap, pydantic range checks.", {"bullet": True}),
        ("Services: extract.py (report reading), features.py (fused record), triage.py (XGBoost, calibration, SHAP), pdf.py (summary).", {"bullet": True}),
        ("Storage: SQLite via SQLAlchemy (users, patients, overrides); model, sample reports and metrics are files.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "All routes live in backend/app/routes/api.py. There is no external service: OCR, model and explainer run locally, so the product works offline."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: from scan to decision")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.4, 5.0)
    for i, (t, b_) in enumerate([("1. Read", "PDF text layer, or local RapidOCR for images and image-only pages. A lexicon of 22 flags plus six lab rules turns text into report flags, each with its page."),
                                 ("2. Fuse and score", "28 report flags and 8 vitals make 36 inputs. Calibrated XGBoost gives priority, risk level and confidence; SHAP lists the drivers."),
                                 ("3. Decide", "The clinician accepts or changes the priority (reason required). The override is stored and the queue reorders.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.4, 0.45, "Workflow of one patient, as implemented in the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "The model never replaces the clinician: the priority is a suggestion shown with its reasons, and every change is logged with who, when and why."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: seeded synthetic triage records")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.ROWS:,}", "synthetic patients (seed 7307)", K.ORANGE), ("7", "clinical archetypes simulated", K.BLUE),
                                   (f"{F.N_TRAIN:,} / {F.N_CAL:,} / {F.N_TEST:,}", "fit / calibration / test split", K.GREEN), (str(F.N_FEATURES), "inputs: 8 vitals + 28 report flags", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=17 if "/" in v else 24, lsize=12)
    rows = [["", "How the data is made (ml/make_data.py)"],
            ["Archetypes", "minor 33.6%, cardiac 14.6%, respiratory 11.9%, trauma 11.7%, abdominal 10.3%, infection 9.4%, neuro 8.5%"],
            ["Vitals and flags", "vitals drawn from clipped normal distributions shifted per archetype; report flags drawn from per-archetype probabilities"],
            ["Label", "a hand-written severity score (vitals thresholds + flag weights + arrival bonus) plus noise (sd 0.4), cut into priorities 1 to 5"],
            ["Class balance", f"P1 {F.pct(F.PRIO_SHARE[0])}, P2 {F.pct(F.PRIO_SHARE[1])}, P3 {F.pct(F.PRIO_SHARE[2])}, P4 {F.pct(F.PRIO_SHARE[3])}, P5 {F.pct(F.PRIO_SHARE[4])}"],
            ["Ceiling", f"knowing the clean score reproduces the label for {F.pct(F.CEILING, 2)} of rows: no model can exceed that exact accuracy"]]
    K.table(s, 0.6, 2.95, [1.9, 10.23], rows, font_size=13, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.35, "No real patient data was used. Accuracy measures recovery of a known rule, not agreement with clinicians. Real triage records are future work.", size=12, color=K.TXT, italic=True)
    notes[6] = ("Be frank: the dataset is simulated. A Kaggle triage dataset was identified as the real-data entry point, but its download script was never run, so no real record was used. "
                "The generator is seeded so every number is reproducible.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Report reading and fusion")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Scanned report", K.NAVY), ("PDF text or OCR", K.PURPLE), ("Unwrap, split sentences", K.PURPLE),
                                       ("Lexicon + negation", K.GREEN), ("Lab values vs ranges", K.GREEN), ("36-input record", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("22", "lexicon flags: 11 symptoms, 5 findings, 6 history", K.BLUE), ("6", "lab values read with unit and reference range", K.GREEN),
                                   ("45", "characters of look-back for a negation word", K.ORANGE)]):
        K.tile(s, 0.6 + i * 4.1, 2.8, 3.9, 1.2, v, l, c, vsize=28, lsize=12)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("Images are upscaled if small and read with RapidOCR (ONNX, offline); text boxes are sorted into reading order. A PDF page with no text layer falls back to OCR.", {"bullet": True}),
        ("'Denies chest pain' or 'no fever' drops the flag; spaces in phrases tolerate OCR run-ons such as 'ofbreath'. Every item keeps the page it came from.", {"bullet": True}),
        ("An abnormal lab (troponin, lactate, WBC, glucose, creatinine, haemoglobin) sets a lab flag; an unreported flag is 0, as in the base paper (no imputation).", {"bullet": True}),
        (f"Known limits: recall {F.pct(F.STRESS['recall'])} and precision {F.pct(F.STRESS['precision'])} on 40 hand-written fragments; paraphrases and split OCR words are missed.", {"bullet": True}),
    ], size=15, color=K.INK, space_after=8)
    notes[7] = ("The reader is rule-based, not a medical language model. On the 12 generated sample reports it is 100 percent, but they were written with the lexicon in view; the 40-fragment stress set is the more honest figure.")

    # ---- 8 model
    s = S[7]
    set_title(s, "Model: calibrated XGBoost with SHAP")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**XGBoost**: 220 trees, depth 4, learning rate 0.1, subsample and column sample 0.9, multi-class softmax over 5 priorities.", {"bullet": True, "space_after": 8}),
        (f"**Isotonic calibration** on a separate {F.N_CAL} rows, so the confidence is a probability, not a raw score.", {"bullet": True, "space_after": 8}),
        ("**SHAP TreeExplainer** on the same trees: the push toward the chosen priority, strongest first, top 8.", {"bullet": True, "space_after": 8}),
        (f"A linear baseline scores higher on this data ({F.pct(lr['accuracy'])} vs {F.pct(xgb['accuracy'])} uncalibrated); trees were kept for SHAP and calibration.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Architecture of the triage model as built in ml/train.py and services/triage.py.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "XGBoost was chosen for SHAP's exact tree explainer and non-linearity headroom on real data, not because it won here: logistic regression is higher on the synthetic labels because they come from an additive score."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Data and split", f"{F.ROWS:,} synthetic rows; stratified 80/20 test split, then 80/20 of the training part for calibration; seed {F.SEED}"],
            ["XGBoost", "n_estimators 220, max_depth 4, learning_rate 0.1, subsample 0.9, colsample_bytree 0.9, objective multi:softprob"],
            ["Calibration", "scikit-learn CalibratedClassifierCV (isotonic) on a frozen base model, fitted on the 960 calibration rows"],
            ["Explainer", "shap.TreeExplainer(base); absent flags with |impact| < 0.15 hidden; warmed at server start (first call about 12 s in a fresh process)"],
            ["Cost on this PC", f"{F.MACHINE}: training {F.TRAIN_SEC:.2f} s; model inference {F.MODEL_SEC * 1000:.3f} ms per patient in batch"],
            ["Comparison runs", "8 model families, 5-fold CV, 5 split seeds, ablations: scripts/run_experiments.py; nothing tuned on the test set"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=14, row_h=0.72, first_bold=True)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Hyper-parameters are fixed in the code and were not searched; the test rows are used only for the reported metrics.", size=12, color=K.TXT, italic=True)
    notes[9] = "The base paper tunes each of 19 algorithms with Optuna (100 trials). We did not tune: one fixed configuration, so our numbers carry no tuning advantage."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: priority, risk and confidence")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_triage.png"), "10"), 0.6, 1.3, 5.9, 5.65)
    K.text(s, 6.8, 1.45, 5.95, 2.2, [
        ("**Priority.** The arg-max of the calibrated probabilities: 1 Critical, 2 Emergent, 3 Urgent, 4 Less urgent, 5 Non-urgent.", {"bullet": True, "space_after": 6}),
        ("**Risk level.** High for priorities 1 and 2, Moderate for 3, Low for 4 and 5.", {"bullet": True, "space_after": 6}),
        ("**Clinician.** Accept, or change with a reason; the model's own suggestion is always kept.", {"bullet": True}),
    ], size=14, color=K.INK)
    rows = [["Confidence >=", "Coverage", "Accuracy", "Within 1"]] + [
        [f"{t:.2f}", F.pct(F.thr_row(t)["coverage"]), F.pct(F.thr_row(t)["accuracy"]), F.pct(F.thr_row(t)["within_one"])] for t in (0.5, 0.7, 0.85)]
    K.table(s, 6.8, 3.85, [1.75, 1.45, 1.4, 1.35], rows, font_size=13, row_h=0.46, align=["l", "c", "c", "c"])
    K.text(s, 6.8, 5.85, 5.95, 1.1, f"Synthetic hold-out. Like the base paper's 0.85 threshold, a high-confidence cut keeps {F.pct(t85['coverage'])} of cases at {F.pct(t85['accuracy'])} accuracy. No threshold is applied in the product: every priority goes to the clinician.", size=12.5, color=K.TXT)
    notes[10] = "The flowchart mirrors triage.predict. The threshold table is analysis only. A separate high-risk rule (flag when P1+P2 is at least 0.4) was measured but is not implemented."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["services/extract.py", "PDF / OCR, lexicon, labs"], ["services/features.py", "36-input fused record"], ["services/triage.py", "calibrated XGBoost + SHAP"],
            ["services/pdf.py", "triage summary PDF"], ["routes/api.py", "13 endpoints, overrides"], ["db.py, auth.py", "SQLite models, bcrypt, JWT"], ["ml/ (make_data, train, eval)", "data, model, metrics"],
            ["frontend/src", "React pages and API client"]]
    K.table(s, 7.9, 1.45, [2.45, 2.38], rows, font_size=12, row_h=0.55, first_bold=True)
    K.text(s, 7.9, 6.5, 4.83, 0.5, "Level-1 data-flow diagram of the platform.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1 splits the system into request validation, report reading, triage scoring, patient storage, override handling, metrics and offline training."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database and UML")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 0.6, 1.3, 6.0, 4.95)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 6.75, 1.3, 6.0, 5.2)
    K.text(s, 0.6, 6.35, 6.0, 0.7, "Three tables: users, patients (vitals, report, fused record, probabilities, SHAP as JSON) and overrides (old and new priority, action, reason, who, when).", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.75, 6.55, 6.0, 0.5, "Core classes: User, Patient, Override, request schemas, and the service modules.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "The patient row stores the model's own suggestion next to the current priority, so every clinician change can be audited against what the model said."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Server", "Python 3.11, FastAPI, Uvicorn, SQLAlchemy 2 on SQLite, pydantic, PyJWT, bcrypt, python-multipart"],
            ["Report reading", "pypdf (text layer), RapidOCR on ONNX Runtime (PaddleOCR-family models, CPU), Pillow, a regex clinical lexicon"],
            ["Machine learning", "XGBoost, scikit-learn (calibration, baselines, metrics), SHAP, pandas, NumPy, joblib"],
            ["Summary report", "ReportLab for the downloadable triage-summary PDF"],
            ["Front end", "React 19, Vite 8, React Router 7, Recharts, Framer Motion, GSAP, lucide-react; 'Neo Brutal Grid' design kit"],
            ["Testing and capture", "pytest with FastAPI TestClient, requests smoke script, Playwright captures at 1440 x 900"],
            ["Run", f"run.bat (virtual environment, training if needed, both servers); ports {F.API_PORT} and {F.WEB_PORT}"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=14, row_h=0.65, first_bold=True)
    notes[13] = "Versions are pinned in requirements.txt and package.json. The original plan named Node, Flask, MongoDB, BioBERT and PaddleOCR; FastAPI, SQLite, a lexicon and RapidOCR were used instead."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Report intake: PDF text, OCR for scans, lexicon, labs, pages", "Done", f"12/12 sample reports read exactly; {F.pct(F.STRESS['recall'])} recall on 40 stress fragments"],
            ["Fused record, calibrated XGBoost, per-patient SHAP", "Done", f"accuracy {F.pct(F.ACC)}, within one level {F.pct(F.W1)} (synthetic hold-out)"],
            ["Clinician accept / change with reason, queue, summary PDF", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks; 16 API tests"],
            ["React app: landing, login, new patient, result, queue, performance", "Done", "12 screenshots; 360 / 768 / 1440 px and dark mode checked"],
            ["Experiments: 8 models, ablation, calibration, robustness", "Done", "scripts/run_experiments.py, experiments/extra/"],
            ["Real triage data, medical language model (BioBERT), LIME", "Not done", "synthetic data and a lexicon used; no real records"],
            ["RAG, multi-agent orchestration, six disease-risk models, MongoDB", "Not done", "outside the built scope; listed as future work"]]
    K.table(s, 0.6, 1.4, [5.2, 1.55, 5.38], rows, font_size=12.5, row_h=0.6)
    notes[14] = "State of the code base. The last two rows are the honest gaps against the original abstract: a lexicon replaces the medical language model, and the agent, RAG and disease-risk parts were not built."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results (synthetic hold-out)")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.pct(F.ACC), f"exact priority, {F.N_TEST:,} held-out cases", K.ORANGE), (F.pct(F.W1), "within one priority level", K.BLUE),
                                   (F.f3(F.MF1), "macro F1 (P1 recall only " + F.pct(F.REC[0], 0) + ")", K.GREEN), (F.f3(F.QWK), "quadratic weighted kappa", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.2, v, l, c, vsize=26, lsize=11.5)
    K.picture(s, trim(F.fig("f03_model_comparison.png"), "f03"), 0.6, 2.7, 6.0, 3.3)
    K.picture(s, trim(F.fig("f04_modality_ablation.png"), "f04"), 6.75, 2.7, 6.0, 3.3)
    K.text(s, 0.6, 6.1, 12.13, 0.95, [
        (f"Fusing report and vitals gives {F.pct(fused['accuracy'])} against {F.pct(vit['accuracy'])} for vitals alone and {F.pct(rep['accuracy'])} for the report alone. "
         f"A logistic baseline reaches {F.pct(lr['accuracy'])}, and {F.pct(F.CEILING)} is the ceiling set by label noise. High-risk (P1 or P2) recall is only {F.pct(SF['high_risk_recall'])}: "
         f"the model under-triages the sickest patients most often. All on synthetic data.", {}),
    ], size=12.5, color=K.TXT)
    notes[15] = (f"Headline findings. 1) {F.pct(F.ACC)} exact and {F.pct(F.W1)} within one level on the held-out synthetic cases. 2) The report adds {fused['accuracy'] * 100 - vit['accuracy'] * 100:.1f} points over vitals alone. "
                 f"3) Linear baseline is higher, so the label rule is nearly linear. 4) P1 recall {F.pct(F.REC[0])} and high-risk recall {F.pct(SF['high_risk_recall'])} are the weak points; flagging when P1+P2 is at least 0.4 "
                 f"would give {F.pct(SF['high_risk_recall_at_pr_0_4'])} recall at {F.pct(SF['high_risk_precision_at_pr_0_4'])} precision, not implemented yet.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("04_queue.png", "Triage queue: ordered by priority, drivers and confidence"), ("06_new_patient_filled.png", "New patient: sample report read, vitals filled"),
            ("07_result.png", "Result: priority 1 Critical, risk and fused record"), ("08_result_why.png", "Why this priority: SHAP drivers, findings with pages"),
            ("09_override_modal.png", "Clinician override: change needs a reason"), ("12_performance.png", "Performance: metrics and confusion matrix")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900, with the seeded sample queue and one live patient entered.", size=11, color=K.TXT, italic=True)
    notes[16] = "Real screenshots of the running app. The queue holds 12 labelled sample cases plus the patient entered during the capture; the performance page shows the synthetic hold-out numbers with a banner saying so."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests passed, {F.PYTEST_XFAIL} expected failure", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed", K.BLUE),
                                   (f"{F.lat('flow_pdf_then_triage'):.0f} ms", "median, PDF read + triage over HTTP", K.ORANGE),
                                   (f"{scan_ms / 1000:.1f} s", "median OCR of one image scan on CPU", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["'Afebrile' is read as fever; 'denies X but reports Y' also drops Y", "Documented as reader defects; test marked expected failure"],
            ["'Haematemesis' also raises the vomiting flag; split OCR words are missed", "Listed with the stress-test results, not hidden"],
            ["Logistic regression beats the shipped XGBoost on the synthetic labels", "Stated in the results; the shipped model is unchanged"],
            ["Default JWT secret and no rate limiting or HTTPS", "Listed as demo-grade security in the limitations"]]
    K.table(s, 0.6, 2.95, [6.4, 5.73], rows, font_size=14, row_h=0.78)
    notes[17] = "Tests cover the reader, the model wrapper and the API; the smoke script runs against the live server. Each observation came from running the code and is recorded rather than fixed silently."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["No real triage records available; the product had to run offline", "Seeded synthetic archetypes, with the label-noise ceiling and a 'synthetic' banner in the app"],
            ["Gemini reading was dropped (no key, offline)", f"RapidOCR + lexicon; {F.pct(F.STRESS['recall'])} stress recall, defects listed"],
            [f"P1 recall {F.pct(F.REC[0])}; high-risk recall {F.pct(SF['high_risk_recall'])}", f"Reported plainly; P1+P2 >= 0.4 rule would give {F.pct(SF['high_risk_recall_at_pr_0_4'])}, planned"],
            ["SHAP explainer cold start of about 12 s on the first patient (measured in a fresh process)", "Warmed in the server start-up; first request is no longer slow"],
            [f"OCR of an image scan takes about {scan_ms / 1000:.1f} s on a CPU", f"PDFs with a text layer take {pdf_ms:.0f} ms; scans reported separately"],
            ["Medical language model and agents in the abstract were out of reach", "Stated as not built; lexicon used and future work listed"]]
    K.table(s, 0.6, 1.4, [5.7, 6.43], rows, font_size=13.5, row_h=0.8)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Real data", "Train and test on real triage records (credentialed or public sets), and compare against recorded nurse priorities.", K.BLUE, "1"),
        ("Better reading", "Replace the lexicon by a medical language model, fix negation scope and the known defects, test on real scans.", K.GREEN, "2"),
        ("Safer thresholds", "Add the high-risk rule (P1+P2 at least 0.4), improve calibration, and always show the second-best priority.", K.ORANGE, "3"),
        ("Evaluate with users", "A clinician usability study, security hardening (secrets, HTTPS, rate limits) and an audit log.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=17)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 3 close the largest honest gaps, the synthetic training data and the weak recall for the most urgent patients.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. Real data is the largest gap; the high-risk rule is the cheapest safety gain because its effect was already measured."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Likely questions: why XGBoost when logistic regression scored higher; why synthetic data; why a lexicon instead of BioBERT; how the numbers relate to the base paper (they do not, different task and data)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
