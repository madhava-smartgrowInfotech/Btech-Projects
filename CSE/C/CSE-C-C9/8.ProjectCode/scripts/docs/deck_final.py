"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited)."""

import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from . import shared as SH
from .refs import TEXT, n, num

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520


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


def bullets(items, gap=10):
    out = [(t, {"bullet": True, "space_after": gap}) for t in items]
    out[-1] = (items[-1], {"bullet": True})
    return out


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.subject = f"{F.PRODUCT}"
    cp.keywords = "financial identification, demographic analytics, economic forecasting, XGBoost, SHAP"
    cp.category = ""
    cp.last_modified_by = ""
    notes = {}

    M = F.METRICS
    C = F.CM[F.BEST]
    RM = F.RM
    MEAS = F.MEAS
    lat = MEAS["api_latency_ms_127_0_0_1"]
    env = MEAS["environment"]
    fb = RM["forecast_backtest"]
    sweep = {r["threshold"]: r for r in RM["threshold_sweep_xgboost"]}
    bands = RM["profile_band_counts_test"]
    bact = RM["profile_band_actual_positive_rate"]

    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh in S[0].shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE)
        elif sh.name == "Text 2":
            K.replace_text(sh, "Final Review")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_.title()}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE.title()}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and the project: FinSight AI, an explainable financial-profile and forecasting application."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap & Problem Statement\nObjectives\nProposed System & Architecture\nMethodology, Dataset & Model\nDecision Workflow, Interaction & Data Model\nImplementation Highlights\nResults, Threshold Analysis, Performance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", size=18)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, bullets([
        "Financial assessment relies on narrow parameters and static scores: non-linear demographic effects are missed, the future is ignored and results cannot be explained.",
        f"FinSight AI turns 12 demographic and financial inputs into a profile (Emerging, Developing, Established), a risk band and a strength score, explains it with live SHAP drivers, adds a what-if comparison and a 12-month Holt-Winters outlook.",
        f"Four models were compared on {F.N_ROWS:,} UCI Adult records inside leakage-safe pipelines; XGBoost was selected: **{F.pct(M['accuracy'])}** accuracy, **{F.f3(M['roc_auc'])}** ROC-AUC, F1 {F.f3(M['f1'])} on {F.N_TEST:,} held-out records (CV AUC {F.f3(M['cv_roc_auc_mean'])}).",
        f"Served by a Flask API and a React interface; {MEAS['pytest']['passed']} automated tests and a {MEAS['smoke_test']['total']}-check smoke test pass; a prediction takes a median {lat['POST /api/predict']['median']:.0f} ms on a CPU.",
        "Limits: income is a proxy, not creditworthiness; the forecast series is synthetic; sex, race and marital status are model inputs and no fairness audit was done.",
    ], 9), size=18)
    notes[3] = "Read the first two bullets, then the headline numbers with their protocol (stratified held-out split). End on the honest limits."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.8, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper"],
            ["Framework", "Four stages: domain-adaptive feature engineering, multi-model training, SHAP global and local interpretation, domain-specific validation"],
            ["Data", "165 Korean hospitals, 825 hospital-year rows (2019-2023), 236 line items reduced to 11 features; deficit target (41.2 % positive)"],
            ["Reported results", "Group K-Fold AUC: XGBoost 0.842, Gradient Boosting 0.840, Random Forest 0.831, Logistic Regression 0.776, MLP 0.772; 2023 hold-out 0.780; Altman Z'' 0.680"],
            ["Explanation", "SHAP: material cost ratio (0.777) and labor cost ratio (0.729) dominate; counterfactual subsidy analysis and fixed-effects regression"],
            ["Stated limits", "SHAP is associational; compositional ratios destabilise single attributions; ensembles cannot extrapolate; organisations, not individuals"]]
    ftable(s, 0.55, 2.75, [2.0, 10.2], rows, size=13, row_h=0.72)
    notes[4] = "The base paper is a framework for organisations. We keep its four stages and apply them to individuals, where validation by entity or time does not apply."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Work", "Methodology", "Dataset", "Key Results", "Limitations"]]
    for i in (0, 1, 2, 3, 4, 7):
        r = SH.LIT_TABLE[i]
        rows.append([r[0].replace(" (base paper)", " (base)"), r[1], r[2], r[3], r[4]])
    ftable(s, 0.55, 1.85, [1.9, 2.8, 2.1, 3.1, 2.3], rows, size=10.5, row_h=0.7)
    notes[5] = "Representative work on explainable and ensemble credit-risk models. Results marked as summarised in the base paper come from its own related-work section."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.8, bullets([
        "**Population:** explainable ML for financial distress targets organisations and sovereigns; individual demographic profiling is far less covered.",
        "**Explanation:** accuracy is the usual headline; per-person explanations a non-expert can read are rarely part of the tool.",
        "**Future view:** models describe the present; a forecast of economic conditions is seldom combined with the profile.",
        "**Usability:** few works deliver a reproducible, tested application with a validated input form.",
        "**Honest scope:** proxy targets are often presented as credit risk; the limits should be stated.",
    ], 12), size=20)
    notes[6] = SH.RESEARCH_GAP

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.95, 12.2, 2.0)
    ftext(s, 0.85, 2.0, 11.6, 1.9, "Given an individual's demographic and financial details, **identify a financial profile and risk band**, show **which factors drove it**, and **forecast how economic conditions may move**, through a web interface a non-expert can read and a regulator can question.", size=20, anchor="m")
    for i, (t, b_) in enumerate([("Input", "12 validated demographic and financial fields"), ("Output", "Profile, risk band, strength score, SHAP drivers, insights"), ("Context", "12-month forecast and what-if comparison")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.3, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.4, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 4.9, 3.5, 1.0, b_, size=15)
    notes[7] = "The statement has three parts: identify, explain, give context."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(SH.OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives of the proposal. The conclusion states for each whether it was met in full or in part."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 2.0, 12.2, 1.1, [("Validated inputs", K.FNAVY), ("Feature engineering", K.FBLUE), ("XGBoost score", K.GREEN), ("SHAP explanation", K.ORANGE), ("Forecast + what-if", K.PURPLE)], size=15, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, bullets([
        "Twelve inputs are validated server-side, engineered into 26 columns and scored by the best of four models selected on a held-out split.",
        "Score p becomes a profile and risk band (Established p >= 0.60, Developing 0.35 to 0.60, Emerging below 0.35) with a plain-language explanation.",
        "Holt-Winters 12-month outlook with a 95 % band and a what-if screen that compares a baseline with a changed scenario, both labelled as simulation.",
        "Flask JSON API and React interface with a sample login; informational use only.",
    ], 10), size=18)
    notes[9] = "The proposed system in one row of boxes, then the four properties that matter."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.85, 8.4, 5.0)
    ftext(s, 9.2, 2.0, 3.6, 4.7, bullets([
        "Presentation: React SPA (5409), Jinja pages",
        "Application: Flask API (8409), validation",
        "Services: predictor, SHAP, what-if, forecast",
        "Data: .pkl pipelines, JSON artifacts, UCI CSV",
    ], 8), size=16)
    notes[10] = "Four tiers; the online path only loads artifacts written by the offline training script."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.2, [("UCI Adult", K.FNAVY), ("Clean + derive", K.PURPLE), ("Stratified split", K.GREEN), ("4 pipelines", K.ORANGE), ("5-fold CV + test", K.FBLUE), ("SHAP + forecast", K.FNAVY), ("JSON artifacts", K.FNAVY)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, bullets([
        "Imputation, one-hot encoding and scaling live inside each scikit-learn Pipeline (fitted on training data only).",
        f"Stratified 80/20 split (seed 42): {F.N_TRAIN:,} train, {F.N_TEST:,} test; 5-fold stratified CV scored by ROC-AUC; selection by ROC-AUC.",
        "One row per person, so entity-grouped and temporal validation of the base paper do not apply; the forecast is validated separately by a hold-out of 12 months.",
        "Every metric, SHAP value and plot is written to JSON/PNG and re-derived by scripts/report_metrics.py.",
    ], 10), size=18)
    notes[11] = "The workflow and the reasons for the validation choices."

    # ---- 12 dataset, features, model
    s = S[11]
    set_title(s, "Dataset, Features & Model")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.1, f"{F.N_ROWS:,}", "UCI Adult records (1994 census)", K.FBLUE, 26)
    ftile(s, 0.55, 3.15, 2.9, 1.1, "26 columns", "14 raw + 12 derived features", K.GREEN, 24)
    ftile(s, 0.55, 4.4, 2.9, 1.1, F.pct(RM["positive_rate_all"]), "earn more than 50K", K.ORANGE, 26)
    K.bar_chart(s, 3.7, 1.85, 4.6, 3.0, ["<=50K", ">50K"], [("Test split", [F.TEST_NEG, F.TEST_POS])], colors=[K.FBLUE], number_format="#,##0", font_size=11, legend=False)
    rows = [["Model", "Setting"], ["Logistic Regression", "C 1.0, scaled"], ["Random Forest", "300 trees"], ["Gradient Boosting", "defaults"], ["XGBoost", "400 trees, depth 6, lr 0.05"]]
    ftable(s, 8.5, 1.9, [1.9, 2.4], rows, size=11, row_h=0.5)
    ftext(s, 3.7, 5.0, 9.1, 1.9, bullets([
        "Derived: net capital, capital intensity, log gains and losses, hours / age bands, education tier, region, employment stability, capital position.",
        "Missing '?' values (workclass 2,799; occupation 2,809; country 857) imputed inside the pipeline; census weight fnlwgt median-imputed.",
    ], 6), size=13)
    notes[12] = "Dataset and model families in one view. The data are 1994 US records; income above 50K is used as a financial-profile signal."

    # ---- 13 decision workflow
    s = S[12]
    set_title(s, "Decision Workflow")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.55, 1.8, 5.0, 5.1)
    ftext(s, 5.9, 2.0, 6.9, 2.9, bullets([
        "Validate: all 12 fields present, in the allowed set and range; otherwise HTTP 400 and no model call.",
        "Score: p = P(income > 50K) from the selected pipeline; strength = 100 p, risk = 100 (1 - p).",
        "Explain: live TreeSHAP; top five positive and negative contributions become sentences.",
    ], 10), size=16)
    rows = [["Score p", "Profile", "Risk", "Test rows", "Actual >50K"],
            ["p >= 0.60", "Established", "Low", f"{bands['Established']:,}", F.pct(bact['Established'])],
            ["0.35 to 0.60", "Developing", "Moderate", f"{bands['Developing']:,}", F.pct(bact['Developing'])],
            ["p < 0.35", "Emerging", "High", f"{bands['Emerging']:,}", F.pct(bact['Emerging'])]]
    ftable(s, 5.9, 5.0, [1.6, 1.5, 1.2, 1.3, 1.3], rows, size=12, row_h=0.42, align=["l", "c", "c", "c", "c"])
    notes[13] = "The prediction route as a decision. The right-hand table shows that the bands are meaningful: the share who actually earn above 50K rises from 7.2 % to 85.2 %."

    # ---- 14 interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_diagram.png"), 0.55, 1.8, 6.0, 5.1)
    K.picture(s, F.diag("08_use_case_diagram.png"), 6.8, 1.8, 6.0, 5.1)
    notes[14] = "Sequence of one assessment and the use cases of the user and the developer."

    # ---- 15 data model
    s = S[14]
    set_title(s, "Data Model (no relational database)")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 6.9, 4.9)
    rows = [["Stored item", "Where"], ["Trained pipelines (4 + best)", "models/*.pkl"], ["Metrics, validation, SHAP", "artifacts/*.json, *.png"], ["Forecast series + 95% band", "artifacts/forecast.json"],
            ["What-if baseline", "browser sessionStorage"], ["Theme, demo login", "browser localStorage"], ["Person's inputs / results", "not stored"]]
    ftable(s, 7.7, 1.9, [2.8, 2.3], rows, size=12, row_h=0.5)
    notes[15] = "The batch brief mentions MySQL; the delivered system stores no personal data on purpose, so the data model is request, response and JSON artifacts."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("16", "Flask routes (pages + JSON)", K.FBLUE), (str(MEAS["pytest"]["passed"]), "pytest tests", K.GREEN), ("11", "React pages", K.ORANGE), ("1", "command to start (run.bat)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.3, 12.2, 3.5, bullets([
        "Server-side validation of every field (required, allowed set, numeric range) with clear 400 messages; the form shows them inline.",
        "Model and explainer are loaded once at start-up; live SHAP per request, with one-hot features read correctly ('absence of occupation = Sales').",
        "What-if re-runs the same pipeline for baseline and scenario and reports score, profile and risk changes, labelled non-causal.",
        "Forecast and performance screens read the JSON artifacts written by training, so the screens always match the evaluated model.",
        "Sample login is a browser-only demo gate and not real authentication.",
    ], 8), size=16)
    notes[16] = "Highlights: validation, single model load, live SHAP wording, simulation labelling, artifacts as the single source of truth."

    # ---- 17 results: model performance
    s = S[16]
    set_title(s, "Results – Model Performance (held-out test split)")
    wipe(s)
    rows = [["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "CV AUC"]]
    for m in F.MODELS:
        c = F.COMPARE[m]
        rows.append([F.MODEL_LABEL[m] + (" *" if m == F.BEST else ""), F.f3(c["accuracy"]), F.f3(c["precision"]), F.f3(c["recall"]), F.f3(c["f1"]), F.f3(c["roc_auc"]), f"{c['cv_roc_auc_mean']:.3f} ± {c['cv_roc_auc_std']:.3f}"])
    ftable(s, 0.55, 1.85, [2.1, 1.0, 1.05, 0.9, 0.8, 1.0, 1.55], rows, size=11.5, row_h=0.55, align=["l", "c", "c", "c", "c", "c", "c"])
    ftext(s, 0.55, 4.75, 8.4, 0.6, f"* selected model. n = {F.N_TEST:,} ({F.TEST_POS:,} positive). PR-AUC {F.f3(C['pr_auc'])}, Brier score {F.f3(C['brier'])}, specificity {F.f3(C['specificity'])}.", size=12, color=K.FNAVY, italic=True)
    ftile(s, 0.55, 5.3, 2.4, 1.25, F.f3(M["roc_auc"]), "XGBoost ROC-AUC", K.FBLUE, 26)
    ftile(s, 3.1, 5.3, 2.4, 1.25, F.pct(M["accuracy"]), "accuracy", K.GREEN, 26)
    ftile(s, 5.65, 5.3, 2.4, 1.25, F.pct(M["recall"]), "recall at 0.5", K.ORANGE, 26)
    K.picture(s, F.fig("shap_top.png"), 9.2, 1.85, 3.7, 3.4)
    notes[17] = ("Protocol: stratified 80/20 split, seed 42; CV on the training split. XGBoost leads on every headline metric. The model was selected on the test AUC; the CV ranking is the same. "
                 "Right: global SHAP importance, led by marital status = Married-civ-spouse, age, years of education, investment gains and hours.")

    # ---- 18 confusion matrix
    s = S[17]
    set_title(s, "Confusion Matrix & Per-class Metrics")
    wipe(s)
    K.picture(s, F.fig("confusion_matrices.png"), 0.55, 1.8, 12.2, 3.3)
    rows = [["Class (XGBoost)", "Support", "Predicted correctly", "Precision", "Recall"],
            ["<=50K (negative)", f"{F.TEST_NEG:,}", f"{C['tn']:,}", F.f3(C["tn"] / (C["tn"] + C["fn"])), F.f3(C["specificity"])],
            [">50K (positive)", f"{F.TEST_POS:,}", f"{C['tp']:,}", F.f3(M["precision"]), F.f3(M["recall"])]]
    ftable(s, 0.55, 5.25, [3.0, 1.7, 2.6, 1.7, 1.7], rows, size=13, row_h=0.45, align=["l", "c", "c", "c", "c"])
    ftext(s, 11.4, 5.25, 1.5, 1.4, f"{C['fp']} false positives, {C['fn']} false negatives", size=12, color=K.FNAVY, italic=True)
    notes[18] = "Rows are the true class, columns the prediction. The model misses 780 of 2,338 high-income people and wrongly flags 410 of 7,431 others: recall is the weak side at the default threshold."

    # ---- 19 threshold and calibration
    s = S[18]
    set_title(s, "Threshold & Calibration Analysis")
    wipe(s)
    K.picture(s, F.fig("threshold_sweep.png"), 0.55, 1.75, 6.3, 3.4)
    K.picture(s, F.fig("calibration.png"), 7.0, 1.75, 3.6, 3.4)
    ftext(s, 10.75, 1.9, 2.1, 3.3, [("Predicted and observed rates track closely: 0.021 vs 0.022 in the lowest bin, 0.984 vs 0.987 in the highest; the largest gap is 0.447 vs 0.406.", {})], size=11, color=K.FNAVY, italic=True)
    rows = [["Threshold", "0.30", "0.35", "0.40", "0.50 (default)", "0.60", "0.70"]]
    for k, lab in (("precision", "Precision"), ("recall", "Recall"), ("f1", "F1")):
        rows.append([lab] + [F.f3(sweep[t][k]) for t in (0.3, 0.35, 0.4, 0.5, 0.6, 0.7)])
    ftable(s, 0.55, 5.3, [2.0, 1.6, 1.6, 1.6, 2.0, 1.6, 1.8], rows, size=12, row_h=0.38, align=["l", "c", "c", "c", "c", "c", "c"])
    notes[19] = "Lowering the threshold to 0.35 lifts recall to 78.1 % and F1 to 0.733 at the cost of precision (69.0 %). The application uses the 0.35 and 0.60 cut-offs for the profile bands, not a yes/no decision."

    # ---- 20 performance and testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{lat['POST /api/predict']['median']:.0f} ms", "median predict (p95 %.0f ms)" % lat["POST /api/predict"]["p95"], K.FBLUE),
                                   (f"{lat['POST /api/whatif']['median']:.0f} ms", "median what-if (two predictions)", K.GREEN),
                                   (f"{lat['GET /api/forecast']['median']:.0f} ms", "median forecast / performance read", K.ORANGE),
                                   (f"{RM['predict_profile_ms']['median']:.0f} ms", "in-process prediction incl. SHAP", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.15, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["Unit (pytest)", "derived features, missing-value handling in the pipeline", "2 passed"],
            ["API / page (pytest)", "health, 7 pages, hard-coded-output check, invalid input, /api/predict, /api/forecast, what-if, artifacts", "7 passed"],
            ["Live smoke test", "API on 8409 and proxy on 5409: options, dashboard, explain, performance, forecast, predict, what-if, errors", f"{MEAS['smoke_test']['passed']}/{MEAS['smoke_test']['total']} checks passed"],
            ["Forecast back-test", f"fit 2015-2024, predict 2025 of the synthetic series: MAE {fb['mae']:.2f}, MAPE {fb['mape_pct']:.2f} %, naive MAE {fb['naive_last_value_mae']:.2f}", "method check only"],
            ["Not done", "load or concurrency tests, browser matrix, user study, security audit", "stated as a limit"]]
    ftable(s, 0.55, 3.3, [2.4, 7.0, 2.8], rows, size=12, row_h=0.55)
    notes[20] = f"Latency measured on 127.0.0.1 with 40 calls each on {env['cpu']}, CPU only. The forecast back-test only shows that the method recovers its own synthetic generator; it says nothing about real data."

    # ---- 21 comparison with the base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only – different problems)")
    wipe(s)
    top_shap = F.SHAP["features"][0]
    rows = [["Aspect", "Base paper [1]", "This project"],
            ["Task and target", "Organisational distress: hospital deficit (net income < 0), 41.2 % positive", "Individual profile: income > 50K, 23.9 % positive"],
            ["Data", "165 hospitals, 825 hospital-year rows, 11 features", f"{F.N_ROWS:,} individuals, 26 columns"],
            ["Validation", "Hospital-level Group K-Fold; temporal 2019-22 to 2023", "Stratified 80/20 + 5-fold CV (one row per person)"],
            ["XGBoost AUC", "0.842 (Group K-Fold); 0.780 temporal", f"{F.f3(M['roc_auc'])} test; {F.f3(M['cv_roc_auc_mean'])} CV"],
            ["Logistic Regression AUC", "0.776", F.f3(F.COMPARE["logistic_regression"]["roc_auc"])],
            ["Top SHAP feature", "material cost ratio (0.777)", f"{top_shap['label']} ({top_shap['mean_abs_shap']:.3f})"],
            ["Beyond prediction", "Counterfactual subsidy analysis, fixed-effects regression", "Forecast, what-if, working web application"]]
    ftable(s, 0.55, 1.85, [2.4, 4.9, 4.9], rows, size=12, row_h=0.52)
    ftext(s, 0.55, 6.1, 12.2, 0.8, "Not a like-for-like comparison: different entities, target, size and validation. The higher AUC here reflects a larger, differently defined and easier problem, not a better method; the comparable finding is that boosted trees beat Logistic Regression in both studies.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that datasets and protocols differ. Where results are comparable in kind: XGBoost beats the linear baseline in both studies, by about 0.07 AUC in the base paper and 0.02 here."

    # ---- 22-24 output screens
    def two_shots(idx, title, a, b, ca, cb, note, h=3.75):
        s = S[idx]
        set_title(s, title)
        wipe(s)
        w = h * 1.6
        K.picture(s, F.shot(a), 0.55, 1.8, 6.0, h, border=True)
        K.picture(s, F.shot(b), 6.8, 1.8, 6.0, h, border=True)
        ftext(s, 0.55, 1.8 + 3.75 + 0.1, 6.0, 0.6, ca, size=12, color=K.FNAVY, italic=True, align="c")
        ftext(s, 6.8, 1.8 + 3.75 + 0.1, 6.0, 0.6, cb, size=12, color=K.FNAVY, italic=True, align="c")
        notes[idx + 1] = note

    two_shots(21, "Output – Assessment and Result", "05_assessment.png", "14_result-established.png",
              "Assessment form with 12 validated inputs", "Result: Established profile, Low risk, 99.9 % strength, live SHAP factors",
              "Left: the validated assessment form. Right: the result with the profile, risk band, strength score and the SHAP factors that strengthen or weaken it.")
    two_shots(22, "Output – Explainability and What-if", "07_explainability.png", "09_whatif.png",
              "Global SHAP importance and beeswarm", "What-if: gains 2,174 to 80,000 and hours 40 to 50 move the score from 1.1 % to 99.5 %",
              "Left: global SHAP. Right: baseline versus scenario; the large jump is a model simulation, not a causal prediction, and extrapolates from sparse high-gain data.")
    two_shots(23, "Output – Forecast and Performance", "08_forecast.png", "10_performance.png",
              f"12-month Holt-Winters forecast on the synthetic index (141.7 to {F.FORECAST['forecast'][-1]['value']:.1f}, +{F.FORECAST['forecast_pct_change']:.2f} %)", "Model comparison, validation protocol and statistics",
              f"The forecast screen is labelled as an illustrative series. Back-test on its own generator: MAE {fb['mae']:.2f}, MAPE {fb['mape_pct']:.2f} %.")

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, bullets([
        "**Delivered:** an end-to-end explainable financial-profile system: validation, feature engineering, four compared models, SHAP explanations, what-if, forecast, API, React interface, tests and documentation.",
        f"**Measured:** XGBoost reaches {F.pct(M['accuracy'])} accuracy, {F.f3(M['roc_auc'])} ROC-AUC and F1 {F.f3(M['f1'])} on {F.N_TEST:,} held-out records; the bands separate people well (observed >50K rate {F.pct(bact['Emerging'])} / {F.pct(bact['Developing'])} / {F.pct(bact['Established'])}).",
        "**Objectives:** 1 dataset (met in part: no transaction data), 2 preprocessing (met), 3 classification and risk (met in part: income proxy), 4 forecast (met in part: synthetic series), 5 explainability (met), 6 evaluation and deployment (met).",
        "**Finding:** boosted trees beat the linear baseline by about 0.02 AUC here (Random Forest does not); recall of the high-income class (66.6 % at 0.5) is the weak point and trades against precision.",
        "**Limits:** income is not creditworthiness; no fairness audit; no real macro data; not financial advice.",
    ], 12), size=18)
    notes[25] = "Five of six objectives were met in full or in part; none is claimed beyond what the data supports."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, bullets([
        "Real macroeconomic indicators (inflation, lending rates, GDP) and real time series to replace the synthetic index; panel or temporal models.",
        "A fairness audit of sex, race and marital-status effects with mitigation (for example equalised odds) before any use on people.",
        "A credit-specific target (repayment or default) on consented data, with calibration and external validation on current populations.",
        "Hyperparameter search, a separate validation set and significance tests (DeLong) for model selection.",
        "Persistence with user accounts, audit log and containerised deployment of the full stack.",
    ], 12), size=20)
    notes[26] = "Concrete next steps, ordered by value."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    keys = ["base", "abid", "maurino", "zhang", "altman", "breiman", "friedman", "xgboost", "barboza", "shap", "treeshap", "bussmann", "gramegna", "grinsztajn", "sklearn", "kohavi", "winters", "mehrabi"]
    half = len(keys) // 2
    left, right = keys[:half], keys[half:]
    ftext(s, 0.55, 1.8, 6.1, 5.1, [(f"[{num(k)}] {TEXT[k]}", {"space_after": 3}) for k in left], size=10)
    ftext(s, 6.8, 1.8, 6.1, 5.1, [(f"[{num(k)}] {TEXT[k]}", {"space_after": 3}) for k in right], size=10)
    notes[27] = "Selected references numbered as in the report; the complete list is in the project report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.scrub_theme(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
