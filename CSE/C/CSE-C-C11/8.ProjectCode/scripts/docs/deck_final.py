"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (letterhead, rule, title and footer chrome inherited)."""

import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import lit
from . import pptkit as K
from .refs import N, REFS, _IDX

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520


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


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26, lsize=12):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=lsize, color=K.DARK, font=FONT)


CROPS = os.path.join(tempfile.gettempdir(), "c11_deck_crops")


def crop_shot(name, box=(256, 56, 1440, 900)):
    """Real screenshot with the sidebar cropped away (left, top, right, bottom in pixels) so the content is larger on the slide."""
    from PIL import Image

    os.makedirs(CROPS, exist_ok=True)
    out = os.path.join(CROPS, f"{os.path.splitext(name)[0]}_crop.png")
    with Image.open(F.shot(name)) as im:
        im.crop(box).save(out)
    return out


def clean_ref(s):
    return " ".join(s.replace("*", "").split())


def bl(items, space=8):
    return [(t, {"bullet": True, "space_after": space}) for t in items]


def pic(slide, path, x, y, w, h, border=False):
    """Picture if the file exists; otherwise a visible placeholder note (the diagram fork may still be drawing)."""
    if os.path.exists(path):
        return K.picture(slide, path, x, y, w, h, border=border)
    fbox(slide, x, y, w, h, fill=K.FZEBRA)
    ftext(slide, x + 0.2, y + 0.2, w - 0.4, 0.6, "[missing: " + os.path.basename(path) + "]", size=12)


def build(out_path=None):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.last_modified_by = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.subject = F.PRODUCT
    cp.keywords = "personal finance, expense categorisation, spending forecast, financial health score, FastAPI, React"
    notes = {}

    CL = F.CLS
    TF, KW, MJ = CL["tfidf_lr"], CL["keyword_table"], CL["majority_class"]
    bt = F.FC["demo_backtest"]
    app_pred = bt["app_prediction_for_next_month"]

    for sl in S:  # footers on every slide except the title
        for sh_ in sl.shapes:
            if sh_.top == TOP_FOOT and sh_.has_text_frame and "Final Review" in sh_.text_frame.text:
                K.replace_text(sh_, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh_ in S[0].shapes:
        if sh_.name == "Text 1":
            K.replace_text(sh_, F.FULL_TITLE, 30)
        elif sh_.name == "Text 2":
            K.replace_text(sh_, f"Final Review  ·  {F.PRODUCT}")
        elif sh_.name == "Text 3":
            K.replace_text(sh_, f"Team Details : Batch {F.BATCH_NO}")
        elif sh_.name == "Text 4":
            K.replace_text(sh_, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS_UPPER))
        elif sh_.name == "Text 5":
            K.replace_text(sh_, f"Under the Esteemed Guidance of\n{F.GUIDE}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh_.name == "Text 6":
            K.replace_text(sh_, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and FINJARVIS: a personal finance manager that categorises spending, forecasts the next month, scores financial health and answers questions from the user's own data."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh_ in s.shapes:
        if sh_.name == "Text 4":
            K.replace_text(sh_, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Data & Core Algorithms\nInteraction & Data Design\nImplementation, Performance & Testing\nResults: Categoriser, Threshold Analysis, Forecast, Health Score, Assistant\nComparison with the Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.8, 12.2, 5.1, bl([
        "Managing money across many digital transactions is tedious, and most tools only report the past. FINJARVIS is a web platform where a user records or imports transactions, sees a dashboard, sets budgets and goals, tracks investments, asks questions and downloads reports. FastAPI + SQLite backend, React console, 33 API routes, 6 tables.",
        "Three data-driven parts: a TF-IDF + logistic-regression expense categoriser (51 seed examples, 11 categories), a least-squares linear-trend forecast of next month's spending, and a 0-100 financial health score from six weighted, explainable components. A rule-routed assistant answers from the user's own records.",
        f"Verified by {F.PYTEST_PASSED} pytest tests and {F.SMOKE_PASSED} smoke checks; API calls take {F.lat('GET /dashboard'):.0f} ms (dashboard) to {F.lat('GET /reports/pdf'):.0f} ms (PDF report) median on 127.0.0.1.",
        f"Measured honestly: the categoriser scores {TF['accuracy'] * 100:.1f} % on a 198-description probe set but only {TF['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants; the linear trend is no better than a plain average with fewer than ~7 months of history.",
        "Not built: anomaly detection, reinforcement-learning budgeting, LSTM or BERT models, loan tracking, scheduled digests. The abstract's Flask + MySQL became FastAPI + SQLite. The optional LLM layer was not tested.",
    ], 8), size=16)
    notes[3] = "Product first, then the three data-driven modules, the evidence and the honest limits, including what was not built."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.75, F.BASE_PAPER, size=12, color=K.FNAVY)
    rows = [["Aspect", "Kharat et al.: multi-model AI personal finance assistant (IJRASET, Nov. 2025)"],
            ["Problem", "Manual categorisation and static budgeting make personal financial planning inefficient and impersonal"],
            ["Method", "Four modules: fine-tuned BERT categoriser (16 -> 50 classes, SMOTE), Q-learning budget recommender, LSTM savings forecaster, Isolation Forest anomaly detector; Streamlit UI"],
            ["Evaluation", "BERT accuracy 92.3 %, precision 90.8 %, recall 91.5 %, F1 91.1 %; LSTM RMSE 137.2, MAE 89.5, R2 0.63; Isolation Forest precision 93 %, recall 94 %, F1 94 %"],
            ["Data", "Synthetic and real-world transactions labelled by the authors; synthetic savings series; synthetic outliers; 80/20 splits; none released"],
            ["Not covered", "A runnable open web product, authentication, import, reports, and a measurement of how the simple baselines behave"],
            ["Also read", f"To (2026) goal-directed design and gamification {N('to')}; Theerthala (2025) behaviourally grounded finance LLM data {N('theerthala')}"]]
    ftable(s, 0.55, 2.6, [1.7, 10.5], rows, size=12, row_h=0.62)
    notes[4] = "Registered base paper from the batch documents. Its numbers are quoted as reported; the data are the authors' own and not released."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Work", "Approach", "Reported result / limitation"],
            [f"Kharat et al. {N('base')} (base)", "BERT + Q-learning + LSTM + Isolation Forest, Streamlit", "92.3 % categoriser accuracy; LSTM R2 0.63; IF F1 94 %; synthetic or private data"],
            [f"Dilip and Janaki {N('finsense')}", "XGBoost + LSTM hybrid with SHAP explanations", "Metrics named (RMSE, MAE, MAPE, R2) but no numeric results in the text read"],
            [f"Abiya et al. {N('leak')}", "Isolation Forest + K-Means for expense leakage", "Synthetic data; no metrics in the abstract"],
            [f"To {N('to')}", "Goal-directed design and gamification for a finance app", "Usability study (small samples); no forecasting or categorisation model"],
            [f"Theerthala {N('theerthala')}", "Behavioural-finance data for a personal-finance LLM", "8B model comparable to 14-32B baselines at ~80 % lower cost; advice text only"],
            [f"Devlin et al. {N('bert')}; Liu et al. {N('iforest')}", "BERT and Isolation Forest (methods)", "General methods used by the base paper; not implemented here"],
            [f"Hyndman and Koehler {N('hk')}; Makridakis et al. {N('makri')}", "Forecast accuracy measures; simple vs complex methods", "Basis for comparing the linear trend with simple averages (MAPE, MAE)"],
            [f"Batch survey {N('s2')}, {N('s3')}", "Two further titles", "Not verified; no result quoted"]]
    ftable(s, 0.55, 1.8, [3.4, 4.3, 4.5], rows, size=11, row_h=0.52, align=["l", "l", "l"])
    notes[5] = "Only what the papers themselves state is quoted. FinSenseAI's text says its models are 'intended to be evaluated', so no number is attributed to it."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(g, {"bullet": True, "space_after": 14}) for g in [
        "The base paper builds four models but releases no running application; its data are synthetic or private and cannot be re-measured.",
        "Related systems report either no number (FinSenseAI, leakage detection) or usability findings without any model (To).",
        "Commercial finance applications are costly and closed; students and individuals lack an open, customisable web platform.",
        "Nobody reports how a simple, inspectable categoriser or trend model behaves on input it has not seen, or with short histories.",
        "Advice should come from the user's own recorded data, with a disclaimer, not from a generic template.",
        "Gap: an affordable, runnable web platform that delivers categorisation, forecasting, health scoring and advice, and measures where each simple module breaks."]], size=17)
    notes[6] = "The gap from the batch literature survey, made concrete."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.85, 12.2, 2.6)
    ftext(s, 0.85, 1.9, 11.6, 2.5, [
        "Manual expense recording is tedious and is quickly abandoned.",
        "Existing applications report past spending but do not forecast what is coming.",
        "Generic budgeting advice ignores individual income patterns and commitments.",
        "Unusual transactions go unnoticed until the statement is reviewed much later.",
        "Need: a personal finance platform that categorises spending automatically, forecasts future expenditure and gives advice grounded in the user's own data."], size=16, anchor="m", bullets=True)
    for i, (t, b_) in enumerate([("Input", "Sign-up, manual or imported (CSV / Excel) transactions, budgets, goals, holdings, questions"),
                                 ("Output", "Auto-category, dashboard, next-month forecast, health score, alerts, assistant answers, PDF / Excel / CSV reports"),
                                 ("Record", f"{F.PYTEST_PASSED} tests, {F.SMOKE_PASSED} smoke checks, experiment metrics (JSON), 19 screenshots of the running app")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.7, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.8, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.3, 3.5, 1.0, b_, size=14)
    notes[7] = "The four problem points are taken from the batch problem statement. The fourth (unnoticed unusual transactions) is NOT solved: no anomaly detector was built."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate([
        "Build secure user accounts with transaction import and manual entry.",
        "Categorise expenses automatically from transaction descriptions using text classification.",
        "Forecast upcoming expenses and savings using time-series models over spending history.",
        "Detect anomalous transactions that deviate from a user's established pattern.",
        "Generate personalised budget recommendations and alerts on threshold breaches.",
        "Visualise spending, category breakdown and forecasts on an interactive dashboard."], 1)], size=22)
    notes[8] = "The six objectives from the batch document. The conclusion slide gives the status of each, including the gaps."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.4, "User journey", size=15, color=K.FNAVY, bold=True)
    K.flow(s, 0.55, 2.15, 12.2, 0.85, [("Sign up / log in", K.FNAVY), ("Add or import", K.FBLUE), ("Auto-categorise", K.GREEN), ("Budgets + alerts", K.ORANGE), ("Dashboard + forecast", K.PURPLE), ("Ask + report", K.FNAVY)], size=13, gap=0.3, font=FONT)
    ftext(s, 0.55, 3.2, 12.2, 0.4, "Intelligence layer (ml/ and services/)", size=15, color=K.FNAVY, bold=True)
    K.flow(s, 0.55, 3.6, 12.2, 0.85, [("TF-IDF + LR categoriser", K.FNAVY), ("Linear-trend forecast", K.FBLUE), ("Health score (6 parts)", K.GREEN), ("Budget alerts 75/90/100 %", K.ORANGE), ("Rule-routed assistant", K.PURPLE), ("Insights + disclaimer", K.FNAVY)], size=12, gap=0.3, font=FONT)
    ftext(s, 0.55, 4.8, 12.2, 2.1, bl([
        "Auto-detect uses the classifier's label; a manual category that differs from the prediction retrains the model on the user's history plus the correction.",
        "The forecast refuses to predict with fewer than 3 months of data; the assistant answers only from the user's own records and always shows a disclaimer.",
        "Alerts are written to notifications (on dashboard or notification read) when a budget reaches 75, 90 and 100 % of its limit (one per identical message).",
        "Every table and query is scoped by user_id; passwords are bcrypt-hashed; tokens are signed bearer tokens (7-day expiry).",
    ], 7), size=15)
    notes[9] = "The proposed system as two chains: what the user does, and which module answers each need."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    pic(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 7.2, 5.1)
    ftext(s, 7.95, 1.95, 4.9, 4.9, bl([
        f"Console: React 18 + TypeScript (Vite, Tailwind, Recharts), port {F.WEB_PORT}; {F.N_PAGES} pages",
        f"API: FastAPI, port {F.API_PORT}; {F.N_ROUTES} routes; bearer-token dependency",
        "Services: transaction, budget, goal, investment, analytics, AI, report, import",
        "ML: expense_classifier, spending_prediction, financial_health",
        f"Data: SQLAlchemy over one SQLite file, {F.N_TABLES} tables; the original Streamlit app shares the same code",
    ], 8), size=15)
    notes[10] = "Layers; the backend folder holds no business logic, every route calls the same service function the Streamlit pages call."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    pic(s, F.diag("02_high_level_workflow.png"), 0.55, 1.8, 7.3, 4.9)
    ftext(s, 8.1, 1.9, 4.7, 5.0, bl([
        "Categoriser: TF-IDF (word 1-2-grams) + logistic regression (C = 1) on 51 seed pairs.",
        "Forecast: slope, intercept = polyfit(month index, expense total, 1); next = max(0, slope x n + intercept); trend label if |slope| > 1.",
        "Health = sum of six weights (0.30, 0.20, 0.15, 0.15, 0.10, 0.10) x component score, bands at 40 / 60 / 75 / 90.",
        "Evaluation: probe set, leave-one-out, backtest, simulation, sensitivity sweeps, API timing, tests.",
    ], 8), size=14)
    notes[11] = "Method in one picture and the formulas that define the three modules."

    # ---- 12 data
    s = S[11]
    set_title(s, "Data and Datasets")
    wipe(s)
    ftile(s, 0.55, 1.8, 2.1, 1.0, f"{CL['seed_examples']}", "seed examples, 11 categories", K.FBLUE, 22, 11)
    ftile(s, 2.8, 1.8, 2.1, 1.0, f"{CL['probe_examples']}", "probe descriptions (3 tiers x 66)", K.GREEN, 22, 11)
    ftile(s, 5.05, 1.8, 2.1, 1.0, "68", "demo-account transactions", K.ORANGE, 22, 11)
    rows = [["Item", "Detail"],
            ["Training data", "51 hand-written (description, category) pairs in ml/expense_classifier.py, 3 to 6 per class"],
            ["Probe set", "198 descriptions written by the team: A seed-like, B bank-statement strings, C unseen merchants; never used for training"],
            ["Sample CSV", "34 fictional rows (Jun-Aug 2026); demo user has 6 monthly totals, 5 budgets, 3 goals, 4 holdings"],
            ["Licence", "Own work; all demo data fictional, no real personal data"],
            ["No split", "Nothing is trained on a split; the probe set is not an independent benchmark"]]
    ftable(s, 0.55, 3.0, [1.5, 5.2], rows, size=11, row_h=0.5)
    pic(s, F.fig("f13_seed_distribution.png"), 7.5, 1.8, 5.35, 3.6)
    ftext(s, 7.5, 5.5, 5.35, 1.4, "The whole training set is tiny: 3 to 6 examples per category, so the model can only recognise words it has seen.", size=13, color=K.FNAVY, italic=True)
    notes[12] = "There is no public corpus. The probe set measures the shipped model but is written by the team, so it is optimistic for tiers A and B and a fair stress test for tier C."

    # ---- 13 core algorithms
    s = S[12]
    set_title(s, "Core Algorithms: Add Transaction, Categoriser, Health Score")
    wipe(s)
    pic(s, F.diag("10_flowchart_algorithm.png"), 0.45, 1.75, 6.3, 5.2)
    pic(s, F.diag("11_categoriser_pipeline.png"), 6.85, 1.75, 6.0, 2.55)
    ftext(s, 6.85, 4.4, 6.0, 2.6, bl([
        "Add: validate, predict category if 'Auto-detect', store, check budget thresholds, write alerts.",
        "Predict order: ML model, keyword table only if the model cannot load, else 'Other'; the ML model never outputs 'Other'.",
        f"Prediction {CL['predict_ms_per_description']:.2f} ms per description in-process; retrain from the seed {CL['retrain_ms_seed_only']:.1f} ms.",
        "Correction: retrain on seed + the user's history + the correction.",
    ], 5), size=12)
    notes[13] = "The add-transaction flow and the categoriser pipeline. Implemented in services/transaction_service.py and ml/expense_classifier.py."

    # ---- 14 interaction and data design
    s = S[13]
    set_title(s, f"User - System Interaction and Data Design ({F.N_TABLES} tables)")
    wipe(s)
    pic(s, F.diag("07_sequence_diagram.png"), 0.45, 1.75, 6.4, 4.7)
    pic(s, F.diag("09_er_diagram.png"), 7.0, 1.75, 5.85, 4.7)
    ftext(s, 0.45, 6.5, 12.4, 0.5, "Left: sequence of adding a transaction. Right: six tables (users, transactions, budgets, financial_goals, investments, notifications); every child table carries user_id and cascades on delete.", size=12, color=K.FNAVY, italic=True)
    notes[14] = "Sequence of adding a transaction and the six-table schema in one SQLite file, created by SQLAlchemy at start-up. The use-case diagram is in the report."

    # ---- 15 implementation, performance & testing
    s = S[14]
    set_title(s, "Implementation, Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.N_ROUTES}", f"API routes, {F.N_TABLES} tables, {F.N_PAGES} pages", K.FBLUE), (f"{F.PYTEST_PASSED} + {F.SMOKE_PASSED}", "pytest tests + smoke checks, all pass", K.GREEN),
                                   (f"{F.lat('GET /dashboard'):.0f} ms", "median dashboard request", K.ORANGE), (f"{F.lat('login'):.0f} ms", "median login (bcrypt verify)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    names = [("GET /dashboard", "Dashboard"), ("GET /analytics", "Analytics + forecast"), ("POST /transactions/predict-category", "Predict category"),
             ("POST /transactions (auto", "Add transaction (auto-categorise)"), ("POST /assistant/ask (analytics", "Assistant question"),
             ("GET /reports/pdf", "PDF report"), ("GET /reports/excel", "Excel report"), ("POST /transactions/import/preview", "Import preview, 100 rows")]
    rows = [["Endpoint (127.0.0.1)", "median ms", "p95 ms"]]
    for pre, lab in names:
        rows.append([lab, f"{F.lat(pre):.1f}", f"{F.lat(pre, 'p95_ms'):.1f}"])
    ftable(s, 0.55, 3.15, [3.9, 1.0, 1.0], rows, size=11, row_h=0.38, align=["l", "r", "r"])
    ftext(s, 6.7, 3.15, 6.1, 3.8, bl([
        "pytest 38: auth 9, budget 6, financial health 6, ML 9, transactions 8; one temporary SQLite file per test.",
        "Smoke test of 49 checks on a throw-away backend: weak password, wrong password and tampered token rejected; user isolation; CSV import; reports.",
        f"Import of 1,000 rows with 84 injected bad rows: all 84 skipped, 916 saved at {F.IMP['rows_per_second_commit']:.1f} rows/s (one session per row).",
        "Machine: i5-12500, 15.7 GB, Python 3.11.9; single user, warm server. Not tested: load, concurrency, penetration scan, other browsers.",
    ], 7), size=13)
    notes[15] = "Implementation facts and the testing that was actually run, with its limits."

    # ---- 16 results: categoriser
    s = S[15]
    set_title(s, "Results - Expense Categoriser (198-description probe set)")
    wipe(s)
    rows = [["Model", "Accuracy", "Macro-F1", "Tier A", "Tier B", "Tier C"]]
    for nm, d in (("TF-IDF + LR (shipped)", TF), ("Keyword table", KW), ("Majority class (Food)", MJ)):
        rows.append([nm, f"{d['accuracy'] * 100:.1f}%", f"{d['macro_f1']:.3f}", f"{d['accuracy_by_tier']['A'] * 100:.1f}%", f"{d['accuracy_by_tier']['B'] * 100:.1f}%", f"{d['accuracy_by_tier']['C'] * 100:.1f}%"])
    ftable(s, 0.55, 1.8, [2.6, 1.0, 1.0, 0.9, 0.9, 0.9], rows, size=12, row_h=0.42, align=["l", "r", "r", "r", "r", "r"])
    ftext(s, 8.2, 1.8, 4.6, 2.5, bl([
        f"Tier C (unseen merchants) falls to {TF['accuracy_by_tier']['C'] * 100:.1f} %: the shipped model is barely better than the majority class there.",
        f"Leave-one-out on the 51 seed pairs: {CL['loo_cv_accuracy_on_seed'] * 100:.1f} %; the 34-row sample CSV: {CL['sample_csv_accuracy'] * 100:.0f} % (optimistic, same vocabulary).",
        f"Mean confidence {CL['mean_confidence_correct']:.3f} when right vs {CL['mean_confidence_wrong']:.3f} when wrong.",
    ], 4), size=12)
    pic(s, F.fig("f01_classifier_tiers.png"), 0.55, 3.75, 6.6, 3.25)
    pic(s, F.fig("f03_per_category_prf.png"), 7.2, 4.0, 5.7, 2.95)
    notes[16] = "The classifier headline is 71.7 %, but the breakdown by tier is the honest result. The probe set is team-written, not an independent benchmark."

    # ---- 17 confusion matrix
    s = S[16]
    set_title(s, "Confusion Matrix - Where the Categoriser Fails")
    wipe(s)
    pic(s, F.fig("f02_confusion_matrix.png"), 0.45, 1.75, 6.0, 5.2)
    ftext(s, 6.7, 1.9, 6.1, 5.0, bl([
        f"{CL['errors_predicted_as_transport']} of the {len(CL['errors'])} errors are predicted as Transport: a text with no known word gives a zero feature vector and the decision comes from the intercepts, where Transport is highest.",
        "Transport has recall 1.00 but precision 0.273; Healthcare, Rent, Travel, Investments and Salary have precision 1.00.",
        "Per-category recall ranges from 0.611 (Shopping) to 0.778 (Education).",
        "Tier-B slips: UPI-AMAZON-PAY-8821 -> Entertainment (the seed has 'amazon prime video'); UPI-HOSPITAL-BILL -> Bills.",
        "The ML model never predicts 'Other', and the app applies no confidence threshold, so unseen merchants are labelled silently.",
    ], 8), size=13)
    notes[17] = "Rows are true categories, 18 per class. The Transport column is the 'dump' class for unseen text."

    # ---- 18 threshold and parameter analysis
    s = S[17]
    set_title(s, "Threshold and Parameter Analysis")
    wipe(s)
    pic(s, F.fig("f04_confidence_coverage.png"), 0.45, 1.75, 6.1, 3.3)
    pic(s, F.fig("f05_learning_from_corrections.png"), 6.7, 1.75, 6.15, 2.9)
    ftext(s, 0.55, 5.2, 6.0, 1.9, bl([
        "Keeping only predictions with top probability >= 0.15 keeps 62.1 % of items at 94.3 % accuracy; >= 0.20 keeps 32.3 % at 98.4 %; >= 0.25 keeps 7.6 % at 100 %.",
        "The app applies no threshold today; abstaining would send the rest to the user.",
    ], 5), size=12)
    ftext(s, 6.8, 4.8, 6.0, 2.3, bl([
        "Adding 48 random corrections of unseen merchants lifts tier-C accuracy only from 18.2 % to 21.5 %.",
        "One correction fixes the same merchant written three other ways: 18.2 % -> 100 % (198 tests); easy, as variants share tokens.",
        "The 3-month minimum for the forecast is a parameter that proved too low (next slide).",
    ], 5), size=12)
    notes[18] = "Threshold analysis of the confidence cut-off and the effect of user corrections. Probabilities are low because there are 11 classes and 51 examples."

    # ---- 19 forecast results
    s = S[18]
    set_title(s, "Results - Spending Forecast")
    wipe(s)
    pic(s, F.fig("f06_forecast_backtest.png"), 0.45, 1.75, 6.2, 3.1)
    pic(s, F.fig("f08_sim_mape_history.png"), 6.75, 1.75, 6.1, 3.1)
    rows = [["Backtest (3 test points)", "MAE (INR)", "MAPE"]]
    for key, nm in (("linear_trend (app)", "Linear trend (app)"), ("mean_of_all", "Mean of all history"), ("mean_of_last_3", "Mean of last 3"), ("last_value", "Last value")):
        rows.append([nm, f"{bt['mae'][key]:,.0f}", f"{bt['mape_pct'][key]:.1f}%"])
    ftable(s, 0.55, 5.0, [2.8, 1.2, 1.0], rows, size=11, row_h=0.4, align=["l", "r", "r"])
    ftext(s, 6.0, 5.0, 6.85, 2.1, bl([
        f"App output on the full 6-month demo history: next month INR {app_pred['predicted_next_month_expense']:,.0f} (recent 3-month average {app_pred['recent_average']:,.0f}, trend {app_pred['trend']}).",
        "Simulation (2,000 users): the trend beats a plain average only once ~7+ months exist; a 3-month mean was at least as good in every setting.",
        "Only 3 backtest points: indicative, not conclusive. The base paper's savings LSTM is not comparable.",
    ], 4), size=12)
    notes[19] = "The linear trend followed the Aug-Sep rise and overshot October. The 3-month minimum is too low for this method."

    # ---- 20 health, assistant, import
    s = S[19]
    set_title(s, "Results - Health Score, Assistant and Import")
    wipe(s)
    pic(s, F.fig("f09_health_sensitivity.png"), 0.45, 1.7, 12.4, 2.45)
    pic(s, F.fig("f10_health_distribution.png"), 0.45, 4.25, 3.9, 2.0)
    pic(s, F.fig("f12_assistant_coverage.png"), 4.45, 4.25, 3.9, 2.0)
    ftext(s, 8.5, 4.25, 4.35, 2.9, bl([
        f"Demo account health score {F.LAT['demo_dashboard']['health_score']:.1f} / 100 (Excellent); weakest area goal progress (24).",
        "5,000 random profiles: 8.7 to 98.2, never lower after +5 points of savings rate; saturates at 20 %.",
        f"Assistant answered {F.AS['answerable_handled_by_analytics']} of {F.AS['answerable']} answerable questions; declined 6 of 6 off-topic; 0 wrong.",
        "Numbers match direct SQL sums (Food INR 17,365; top category Rent INR 108,000).",
    ], 4), size=11)
    ftext(s, 0.55, 6.35, 7.8, 0.7, "Weights are expert-chosen, not fitted; savings rate and expense ratio carry 50 % of the score and are correlated. The LLM layer was not run.", size=11, color=K.FNAVY, italic=True)
    notes[20] = "Sensitivity sweeps of the health score, the rule-layer assistant test and the import pipeline result. The assistant missed groceries, biggest expense, eating out, largest purchase, run out of money and which category to cut."

    # ---- 21 comparison with base paper
    s = S[20]
    set_title(s, "Comparison with the Base Paper (different data and models)")
    wipe(s)
    rows = [["Module", "Kharat et al. (base paper)", "FINJARVIS (this work)", "Comparable?"],
            ["Categoriser", "BERT, 50 classes, own data, 80/20: accuracy 92.3 %, F1 91.1 %", f"TF-IDF + LR, 11 classes, 51 seeds: probe accuracy {TF['accuracy'] * 100:.1f} %, macro-F1 {TF['macro_f1']:.3f}; unseen merchants {TF['accuracy_by_tier']['C'] * 100:.1f} %", "No: data, labels, model differ"],
            ["Forecast", "LSTM on synthetic savings: RMSE 137.2, MAE 89.5, R2 0.63", f"Linear trend on monthly expenses: MAPE {bt['mape_pct']['linear_trend (app)']:.1f} % (3 points), MAE INR {bt['mae']['linear_trend (app)']:,.0f}", "No: target, units, data differ"],
            ["Budgeting", "Q-learning agent (state, action, reward)", "User-set budgets, alerts at 75 / 90 / 100 %, rule-based advice", "No RL built"],
            ["Anomalies", "Isolation Forest: P 0.93, R 0.94, F1 0.94", "Not implemented (largest expense only)", "Gap"],
            ["Product", "Streamlit prototype, Flask API mention", f"FastAPI + React, {F.N_ROUTES} routes, auth, import, reports, {F.PYTEST_PASSED} tests", "Beyond the paper"],
            ["Data", "Synthetic or private, unreleased", "Fictional demo data, probe set and scripts in the repository", "Re-measurable"]]
    ftable(s, 0.55, 1.8, [1.4, 3.6, 4.7, 2.5], rows, size=11, row_h=0.62)
    ftext(s, 0.55, 6.35, 12.2, 0.65, "Different problems, data and models: no figure of FINJARVIS is claimed to match or beat the base paper. Its BERT, Q-learning, LSTM and Isolation Forest modules were not built here.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "Say plainly that datasets, label sets and model sizes differ, so the numbers are not comparable. Three of the four base-paper modules are not implemented."

    # ---- 23-25 output screens
    def two_shots(slide, title, a, b, cap_a, cap_b, box_a=(256, 76, 1440, 900), box_b=(256, 76, 1440, 900)):
        set_title(slide, title)
        wipe(slide)
        K.picture(slide, crop_shot(a, box_a), 0.45, 1.75, 6.0, 3.75, border=True)
        K.picture(slide, crop_shot(b, box_b), 6.85, 1.75, 6.0, 3.75, border=True)
        ftext(slide, 0.45, 5.65, 6.0, 1.0, cap_a, size=13, color=K.FNAVY, bold=True)
        ftext(slide, 6.85, 5.65, 6.0, 1.0, cap_b, size=13, color=K.FNAVY, bold=True)

    two_shots(S[21], "Output - Dashboard and Spending Forecast", "05_dashboard.png", "11_analytics-prediction.png",
              "Dashboard (demo account, Oct 2026): income INR 65,000, expenses 30,080, savings rate 53.7 %, health score 90 Excellent, weakest area Goal Progress",
              f"Analytics: six-month spending trend and ML prediction, next month INR {app_pred['predicted_next_month_expense']:,.0f}, recent 3-month average {app_pred['recent_average']:,.0f}, trend Increasing",
              box_b=(256, 150, 1440, 880))
    notes[22] = "Real screens of the running app with the fictional demo account."
    two_shots(S[22], "Output - CSV Import and AI Assistant", "09_transactions-import.png", "15_assistant.png",
              "Import preview: 4 valid rows ready, row 6 skipped (invalid date, amount or description); blank categories are filled by the classifier",
              "Assistant: top category Rent INR 108,000 and health score 90.4 / 100, each marked 'Calculated from your data'; built-in analytics only (no API key)")
    notes[23] = "The import preview shows nothing is saved until confirmed; the assistant banner states the LLM layer is off."
    two_shots(S[23], "Output - Budgets and Reports", "12_budgets.png", "16_reports.png",
              "Budget status for October 2026: Food 15 % used, Entertainment 88 % ('Getting close'), Bills 65 %; alerts at 75, 90 and 100 %",
              "Reports: monthly PDF summary, Excel workbook and transactions CSV for the chosen month",
              box_b=(256, 76, 1440, 620))
    notes[24] = "Budgets and downloads. PDF, Excel and CSV generation were timed (135 ms, 209 ms, 18 ms median)."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.8, "FINJARVIS is a working, tested personal finance manager whose measurements show where each simple module helps and where it falls short.", size=17, color=K.FNAVY, bold=True)
    rows = [["#", "Objective", "Outcome"],
            ["1", "Secure accounts, import and manual entry", "Met: bcrypt, signed tokens, CSV / Excel import with preview, 49 / 49 smoke checks"],
            ["2", "Automatic categorisation", f"Partly met: {TF['accuracy'] * 100:.1f} % on probe set, but {TF['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants"],
            ["3", "Forecast expenses and savings (time series)", "Partly met: linear trend on expenses only; no ARIMA / LSTM; not better than a mean under ~7 months"],
            ["4", "Detect anomalous transactions", "Not met: no anomaly detector was built"],
            ["5", "Budget recommendations and alerts", "Partly met: user-set budgets, threshold alerts, rule-based advice; no RL"],
            ["6", "Interactive dashboard", "Met: 13 pages, charts, 19 captured screens"]]
    ftable(s, 0.55, 2.6, [0.5, 4.5, 7.2], rows, size=12, row_h=0.5, align=["c", "l", "l"])
    ftext(s, 0.55, 6.2, 12.2, 0.8, "Key findings: a tiny seed list limits the categoriser to known vocabulary; corrections help repeat merchants but not new ones; the 3-month forecast minimum is too low.", size=13, color=K.FNAVY, italic=True)
    notes[25] = "Be explicit about which objectives were met, partly met or not met."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Limitations & Future Scope")
    wipe(s)
    fbox(s, 0.55, 1.8, 6.0, 4.6, fill=K.FZEBRA)
    ftext(s, 0.75, 1.9, 5.6, 0.4, "Known limitations", size=17, color=K.FNAVY, bold=True)
    ftext(s, 0.75, 2.4, 5.6, 4.4, bl([
        "51-example seed list; unseen merchants labelled silently (mostly Transport)",
        "No anomaly detection, RL budgeting, LSTM or BERT; no loans or scheduler",
        "Demo data synthetic; probe set team-written; 3 backtest points",
        "Import commits one row at a time (35 rows/s)",
        "Home-made bearer tokens; default secret if APP_SECRET_KEY unset",
        "Single-user SQLite, no migrations; LLM layer and live prices untested",
    ], 9), size=15)
    fbox(s, 6.8, 1.8, 6.0, 4.6, fill=K.FHEAD)
    ftext(s, 7.0, 1.9, 5.6, 0.4, "Future scope", size=17, color=K.FNAVY, bold=True)
    ftext(s, 7.0, 2.4, 5.6, 4.4, bl([
        "Train on a public transaction corpus or user-labelled history; add a confidence threshold with abstain",
        "Add an anomaly detector (z-score or Isolation Forest) on the user's own history",
        "Raise the forecast minimum or blend the trend with a moving average",
        "Batch import commits; refresh tokens and a managed secret",
        "Loan tracker, recurring-bill scheduler, bank statement parsing",
        "Run the assistant's LLM layer under test; user study; PostgreSQL",
    ], 9), size=15)
    notes[26] = "Limitations first, then concrete next steps drawn from the measured defects."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    keys = ["base", "to", "theerthala", "finsense", "leak", "bert", "iforest", "lstm", "qlearn", "smote", "sklearn", "tfidf", "hk", "makri", "lusardi", "bcrypt"]
    short_ = [f"[{_IDX[k]}] {clean_ref(REFS[_IDX[k] - 1])}" for k in keys]
    short_ = [x if len(x) < 300 else x[:297] + "..." for x in short_]
    ftext(s, 0.55, 1.75, 6.0, 5.2, [(x, {"space_after": 4}) for x in short_[:8]], size=11)
    ftext(s, 6.8, 1.75, 6.0, 5.2, [(x, {"space_after": 4}) for x in short_[8:]] + [(f"The full numbered list of {len(REFS)} references, including the batch survey titles {N('s2')}, {N('s3')} (not verified), is in the report.", {"italic": True})], size=11)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh_ in S[27].shapes:
        if sh_.name == "Text 2":
            K.replace_text(sh_, "Questions & Suggestions")
    notes[28] = "Invite questions."
    return prs, S, notes


def finish(prs, S, notes, out_path):
    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "FINJARVIS")
    return out_path


def build_all(out_path):
    return finish(*build(out_path), out_path)


if __name__ == "__main__":
    print(build_all(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
