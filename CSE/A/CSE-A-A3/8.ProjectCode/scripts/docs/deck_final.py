"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (letterhead, rule, title and footer chrome inherited)."""

import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .shared import OBJECTIVES, OBJECTIVE_STATUS, PROBLEM_STATEMENT, SYNTHETIC_NOTE

TEMPLATE = r"D:\abstracts\Templates\Final_PPT.pptx"
FONT = "Calibri"
TOP_BANNER, TOP_RULE, TOP_TITLE, TOP_FOOT = 73152, 979985, 1098857, 6446520
OLD_WORDS = ("Bank Transaction", "Fraud", "Batch D1")
X, R, API = F.X, F.REAL, F.API
DIS = F.DISEASES


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


def tiles(s, items, y=1.9, h=1.15, vsize=26):
    for i, (v, l, c) in enumerate(items):
        ftile(s, 0.55 + i * 3.08, y, 2.88, h, v, l, c, vsize)


def bullets(items, gap=10):
    out = []
    for i, t in enumerate(items):
        out.append((t, {"bullet": True, "space_after": gap if i < len(items) - 1 else 0}))
    return out


def screens(s, shots, y0=1.85):
    for i, (f, cap) in enumerate(shots):
        r, c = divmod(i, 3)
        x, y = 0.55 + c * 4.1, y0 + r * 2.6
        K.picture(s, F.shot(f), x, y, 3.95, 2.25, border=True)
        ftext(s, x, y + 2.27, 3.95, 0.3, cap, size=12, color=K.FNAVY, align="c")


def ref_entries():
    from . import refs

    return refs


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.comments = ""
    cp.subject = F.TITLE
    cp.keywords = "multi-disease prediction, machine learning, diabetes, heart disease, liver disease, kidney disease"
    cp.last_modified_by = ""
    notes = {}
    H = X  # extended measurements
    best = F.BEST

    def ho(d, k, m=None):
        return H[d]["holdout"][m or best[d]][k]

    # footers on every slide
    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")
    for lay in list(prs.slide_layouts) + [prs.slide_master]:
        for sh in lay.shapes:
            if sh.has_text_frame and any(w in sh.text_frame.text for w in OLD_WORDS):
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE)
        elif sh.name == "Text 2":
            K.replace_text(sh, "Final Review")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO} ({F.SECTION})")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_.title()}" for n_, r_ in F.STUDENTS))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE.title()}\n{F.GUIDE_DESIGNATION}")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and the project: a web application that screens four chronic conditions from routine clinical values with machine learning."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap & Problem Statement\nObjectives\nProposed System & Architecture\nMethodology, Dataset & Drivers\nDecision Workflow, Use Cases & Data Model\nImplementation Highlights\nResults: Metrics, Confusion, Stability, Threshold & Parameters\nReal-Data Check, Testing & Comparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References")
    notes[2] = "The agenda follows the report: problem, design, method, results, honest limits, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.95, bullets([
        "Chronic diseases are found late, and screening tools usually cover one condition at a time. We built an Intelligent Health Assistant that screens four conditions - diabetes, heart, liver and kidney disease - from routine clinical values in one web interface.",
        "Per disease, Logistic Regression, Decision Tree, Random Forest and an RBF SVM are trained on standardised inputs and compared on a stratified 80/20 split; the best model by F1 is saved and served by a FastAPI service and a React interface.",
        f"The data are synthetic (2,000 rows per disease, linear risk rule, 8% flipped labels, so about 92% is the ceiling). Selected models reach {F.pct(ho('diabetes','accuracy'))}, {F.pct(ho('heart','accuracy'))}, {F.pct(ho('liver','accuracy'))} and {F.pct(ho('kidney','accuracy'))} accuracy: a check on the pipeline, not clinical performance.",
        f"On real public data the same algorithms reach 72-99%, and the shipped models transfer only partly. API checks: {F.API_CHECKS[0]}/{F.API_CHECKS[1]} passed.",
        "Not implemented: per-prediction explanations, recommendations, imputation, range validation. A teaching demonstration, not a diagnostic tool.",
    ], 8), size=17)
    notes[3] = "Read the first two bullets, then the headline numbers with their protocol, and end on the honest limits: synthetic data, no explanations."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.95, F.BASE_PAPER, size=14, color=K.FNAVY)
    rows = [["Aspect", "Base paper (thyroid disease, IEEE Access 2026)"],
            ["Method", "Five classifiers (SVC, Random Forest, Extra Trees, AdaBoost, CatBoost), nested cross-validation (5 outer, 3 inner folds), SHAP and counterfactual explanations"],
            ["Data", "Real UCI thyroid data, 7,200 samples, 21 features, three classes; full feature set and a TOP-10 consensus set"],
            ["Reported results", "Random Forest and CatBoost 0.996-0.997 accuracy / F1, AUC 0.999-1.000; SVC 0.965-0.967 accuracy; SMOTE tried and rejected"],
            ["Stated limits", "Class imbalance, no external validation, one disease; explanations aligned with TSH / FTI physiology"]]
    ftable(s, 0.55, 2.9, [2.0, 10.2], rows, size=14, row_h=0.8)
    notes[4] = "A rigorous single-disease study on real data. We take its idea of comparing classical classifiers under held-out evaluation and widen it to four diseases behind one interface; we do not reproduce its nested CV or explanations."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    from . import lit

    rows = [lit.LIT_HEADER] + [list(r) for r in lit.LIT_TABLE[:8]]
    ftable(s, 0.45, 1.75, [2.3, 3.3, 2.0, 2.8, 1.95], rows, size=10, row_h=0.52)
    ftext(s, 0.45, 6.76, 12.4, 0.3, "Details as read from each source; datasets and protocols differ, so the reported numbers are not comparable with each other or with ours.", size=10.5, color=K.FNAVY, italic=True)
    notes[5] = "Results are quoted as the authors report them. Survey items that could not be verified are listed in the report and not cited."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.8, bullets([
        "**One disease at a time:** the surveyed papers each target a single condition; a separate tool and workflow is needed per disease.",
        "**Screening plus explanation:** the gap is a single pipeline that screens several conditions from routine values and explains which parameters drove each prediction - the base paper does the explaining (SHAP, counterfactuals) for thyroid only.",
        "**Evidence quality:** many small demonstrations report one split on one dataset; model choice on a single split is fragile and synthetic data is rarely audited against real data.",
        "**Usability:** few works deliver a running interface that a non-programmer can use.",
    ], 14), size=20)
    notes[6] = "This project covers the first and the last gap; explanation is only partly addressed (offline permutation importance, not in the app)."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.95, 12.2, 2.4)
    ftext(s, 0.85, 2.0, 11.6, 2.3, PROBLEM_STATEMENT, size=17, anchor="m")
    for i, (t, b_) in enumerate([("Input", "One patient's routine clinical values (8-13 fields per disease)"), ("Output", "High-risk / low-risk class and the model's confidence, per disease"), ("Record", "Metrics per algorithm, saved model, model-comparison page")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.65, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.75, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.25, 3.5, 1.1, b_, size=15)
    notes[7] = "Three parts: predict the class, say how confident the model is, and do it in one interface."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=19)
    notes[8] = "Six objectives from the proposal. The conclusion slide states how each was met: three achieved or partly, honestly marked."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 2.0, 12.2, 1.1, [("Enter values", K.FNAVY), ("Check + scale", K.FBLUE), ("Predict (4 models)", K.GREEN), ("Best-by-F1 model", K.ORANGE), ("Risk class + confidence", K.PURPLE)], size=14, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, bullets([
        "Four scikit-learn classifiers per disease (LR, Decision Tree, Random Forest, RBF SVM); the best on F1 is saved with joblib and loaded at start-up.",
        "FastAPI service with seven routes imports the original Flask module, so predictions match the earlier pages exactly.",
        "React interface: landing page, overview, one prediction form per disease with real-record samples, model comparison, dataset page; dark and light themes, phone layout.",
        "Every result carries a not-a-diagnosis notice; no data are stored.",
    ], 10), size=18)
    notes[9] = "The proposed system in one line of boxes, then the four properties that matter."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.85, 6.0, 5.1)
    ftext(s, 6.9, 2.0, 5.9, 4.7, bullets([
        "**Presentation:** React 19 + Vite (port 5303); original Flask pages (5000)",
        "**Application:** FastAPI (8303), 7 routes, CORS limited to the local front end",
        "**Core:** app.py model bundles (model, scaler, features) and field metadata",
        "**Data and models:** four CSV files, joblib pickles, training_report.json; no database, no login",
    ], 12), size=17)
    notes[10] = "Four tiers. The API wraps the Flask module; nothing is persisted."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.2, [("Generate CSVs", K.FNAVY), ("Split 80/20", K.PURPLE), ("StandardScaler", K.GREEN), ("Train 4 models", K.ORANGE), ("Evaluate", K.FBLUE), ("Pick max F1", K.FNAVY), ("Save + serve", K.GREEN)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, bullets([
        f"{F.SPLIT}. Scaler fitted on the training part only; nothing else (no imputation, feature selection, tuning or class weights).",
        "Settings: LR max_iter 1000; Decision Tree depth 6; Random Forest 200 trees, depth 8; SVM RBF, C = 1, probability on.",
        "Beyond the shipped script we added ROC-AUC, confusion matrices, 5-fold CV, ten random splits, threshold and parameter sweeps, permutation importance, and a real-data check.",
        "All numbers are written to JSON by scripts/run_experiments.py and read into the documents.",
    ], 10), size=17)
    notes[11] = "The shipped pipeline is deliberately simple. The extra protocols exist because selecting on one 400-row split is fragile."

    # ---- 12 dataset, features and drivers
    s = S[11]
    set_title(s, "Dataset, Features & Drivers")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.1, "4 x 2,000", "rows, synthetic, no missing / duplicates", K.FBLUE, 24)
    ftile(s, 0.55, 3.15, 2.9, 1.1, "8 % flipped", "label noise: ceiling about 92% accuracy", K.GREEN, 24)
    ftile(s, 0.55, 4.4, 2.9, 1.1, "8 - 13", "features per disease (4 sets)", K.ORANGE, 24)
    K.picture(s, F.fig("importance.png"), 3.65, 1.75, 5.8, 3.9)
    ftext(s, 9.6, 1.9, 3.3, 3.6, bullets([
        "Positive rate: diabetes 40.6%, heart 73.1%, liver 28.1%, kidney 59.8%.",
        "Top drivers (permutation): glucose; ca, age; alkaline phosphatase; albumin, haemoglobin.",
    ], 8), size=12)
    ftext(s, 0.55, 5.65, 12.2, 1.3, bullets([
        "Labels come from a hand-written linear risk rule, so recovering these drivers checks the pipeline: it is not evidence about real patients.",
        "Permutation importance was run offline; the application does not show it.",
    ], 6), size=14)
    notes[12] = "Be explicit: the rows are generated. " + SYNTHETIC_NOTE

    # ---- 13 decision workflow + interaction
    s = S[12]
    set_title(s, "Decision Workflow & Interaction")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.45, 1.75, 3.9, 5.2)
    K.picture(s, F.diag("07_sequence_diagram.png"), 4.55, 1.75, 4.2, 4.2)
    ftext(s, 8.95, 1.9, 3.95, 4.9, bullets([
        "Validate: required and numeric in the form; missing or non-finite values give HTTP 422.",
        "Scale with the stored scaler, predict, and take max(predict_proba) as the confidence.",
        "Class 1 = Positive (High Risk); class 0 = Negative (Low Risk).",
        "No range check: glucose 100,000 mg/dL is accepted by the API (UI shows a warning only).",
    ], 8), size=13)
    notes[13] = "Left: training and serving path. Middle: one prediction as a sequence. Right: what the decision rule does and does not check."

    # ---- 14 use cases + data model
    s = S[13]
    set_title(s, "Use Cases & Data Model (logical)")
    wipe(s)
    K.picture(s, F.diag("08_use_case_diagram.png"), 0.45, 1.8, 6.2, 4.0)
    K.picture(s, F.diag("09_er_diagram.png"), 6.85, 1.8, 6.0, 4.0)
    ftext(s, 0.55, 6.0, 12.2, 0.95, "There is no SQL database and no user accounts: the data model describes CSV files, pickled model bundles and the JSON training report. Predictions are transient and never stored.", size=14, color=K.FNAVY, italic=True)
    notes[14] = "Use cases of the user and the developer; the ER diagram is a logical model of files and in-memory objects, not a database."

    # ---- 15 implementation highlights
    s = S[14]
    set_title(s, "Implementation Highlights")
    wipe(s)
    tiles(s, [(str(F.N_ENDPOINTS), "API routes (FastAPI)", K.FBLUE), (f"{F.API_CHECKS[0]}/{F.API_CHECKS[1]}", "API checks passed", K.GREEN), ("7", "front-end page components", K.ORANGE), ("1", "command to start (run.bat)", K.PURPLE)], 1.9, 1.1, 28)
    ftext(s, 0.55, 3.3, 6.6, 3.6, bullets([
        "API imports app.py, so Flask and React give identical predictions (40 of 40 sampled rows agree).",
        "Form fields (label, min, max, median, options) are generated from FIELD_META and the CSV ranges.",
        "'Positive / Negative sample' buttons pre-fill a real CSV row.",
        "Out-of-training-range values trigger a warning; the server rejects missing or non-finite input.",
    ], 8), size=14)
    K.picture(s, F.fig("api_latency.png"), 7.4, 3.3, 5.4, 2.2)
    ftext(s, 7.4, 5.6, 5.4, 1.2, "Latency on 127.0.0.1, 200 calls per route. No authentication, persistence or audit log (honest limits).", size=12, color=K.FNAVY, italic=True)
    notes[15] = "Highlights: shared model module, generated forms, samples, validation. Latency measured while the PC was under memory pressure; Windows timer resolution is about 15 ms, so treat as upper bounds."

    # ---- 16 results: model performance
    s = S[15]
    set_title(s, "Results – Model Performance (400-row test sets)")
    wipe(s)
    rows = [["Disease", "Selected model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]]
    for d in DIS:
        m = F.HO[d][best[d]]
        rows.append([F.NAME[d], best[d], f"{m['accuracy']:.4f}", f"{m['precision']:.4f}", f"{m['recall']:.4f}", f"{m['f1']:.4f}", f"{ho(d, 'roc_auc'):.4f}"])
    ftable(s, 0.55, 1.85, [1.6, 2.2, 1.0, 1.0, 0.9, 0.85, 1.0], rows, size=12, row_h=0.45, align=["l", "l", "c", "c", "c", "c", "c"])
    K.bar_chart(s, 9.3, 1.75, 3.7, 2.6, [F.NAME[d].split()[0] for d in DIS],
                [(F.SHORT[m], [F.HO[d][m]["f1"] for d in DIS]) for m in F.MODEL_ORDER],
                colors=[K.FBLUE, K.GOLD, K.GREEN, K.PURPLE], number_format="0.00", font_size=8, max_value=1.0, label_size=6)
    ftext(s, 0.55, 4.5, 12.2, 2.4, bullets([
        "Logistic Regression is selected for heart, liver and kidney; SVM for diabetes (F1 0.8636 vs 0.8599, a gap well inside split noise).",
        "The Decision Tree is weakest everywhere (accuracy 74.5-86.0%); Random Forest over-fits the noisy labels (train 93.6-95.9%, test 81.5-88.3%).",
        "Accuracy 88.3-91.8% sits close to the 92% noise ceiling: the models recover the rule, they do not detect disease.",
        "Selection used the same test set that reports the scores, so the best-model figures are slightly optimistic.",
    ], 8), size=14)
    notes[16] = "Protocol: 1,600 train, 400 test rows per disease, seed 42, fixed settings. Numbers match models/training_report.json exactly; ROC-AUC was measured afterwards by run_experiments.py."

    # ---- 17 confusion matrices and ROC
    s = S[16]
    set_title(s, "Confusion Matrices & ROC Curves")
    wipe(s)
    K.picture(s, F.fig("confusion_matrices.png"), 0.45, 1.8, 8.3, 2.15)
    K.picture(s, F.fig("roc_curves.png"), 8.95, 1.75, 4.0, 3.5)
    cm = {d: H[d]["confusion"][best[d]] for d in DIS}
    ftext(s, 0.55, 4.2, 8.2, 2.7, bullets([
        f"Diabetes (SVM): {cm['diabetes'][1][0]} of 162 diabetic test cases missed, only {cm['diabetes'][0][1]} false alarms. Heart (LR): {cm['heart'][0][1]} of 108 low-risk rows flagged (the model favours recall, 0.9589).",
        f"Liver (LR): {cm['liver'][1][0]} of 112 positives missed, {cm['liver'][0][1]} false alarms. Kidney (LR): {cm['kidney'][1][0]} missed, {cm['kidney'][0][1]} false alarms.",
        "ROC-AUC of the selected models 0.85-0.91; Random Forest and SVM curves are close to LR, the tree is lower.",
    ], 6), size=14)
    ftext(s, 8.95, 5.35, 4.0, 1.5, "ROC curves of all four algorithms for each disease (test set); AUC in the legends.", size=12, color=K.FNAVY, italic=True)
    notes[17] = "Rows are the true label, columns the prediction. For a screening aid a miss is costlier than a false alarm; the costs were not measured."

    # ---- 18 stability
    s = S[17]
    set_title(s, "Stability: 5-Fold CV and Ten Random Splits")
    wipe(s)
    K.picture(s, F.fig("stability.png"), 0.55, 1.8, 8.4, 2.6)
    rows = [["Disease", "Served model", "Served: hold-out acc.", "LR: 5-fold CV acc.", "LR: 10 splits acc.", "LR best F1 (of 10)"]]
    for d in DIS:
        rows.append([F.NAME[d], best[d], f"{ho(d, 'accuracy'):.3f}",
                     f"{H[d]['cv5']['Logistic Regression']['accuracy_mean']:.3f} ± {H[d]['cv5']['Logistic Regression']['accuracy_std']:.3f}",
                     f"{H[d]['seed_study']['Logistic Regression']['accuracy_mean']:.3f} ± {H[d]['seed_study']['Logistic Regression']['accuracy_std']:.3f}",
                     H[d]["seed_winners"]["Logistic Regression"]])
    ftable(s, 0.55, 4.55, [1.8, 2.2, 2.1, 2.2, 2.1, 1.8], rows, size=12, row_h=0.45, align=["l", "l", "c", "c", "c", "c"])
    ftext(s, 9.2, 1.85, 3.7, 2.6, bullets([
        "Logistic Regression has the best F1 on 10 of 10 splits for every disease.",
        "For diabetes SVM was shipped from one split; CV and the other nine splits favour LR (0.8955 vs 0.8765 accuracy in CV).",
    ], 8), size=13)
    notes[18] = "Cross-validation re-fits the scaler inside each fold. Error bars are one standard deviation. The shipped diabetes model is within noise of LR but is not the best by CV."

    # ---- 19 threshold and parameter analysis
    s = S[18]
    set_title(s, "Threshold & Parameter Analysis")
    wipe(s)
    K.picture(s, F.fig("threshold_sweep.png"), 0.55, 1.8, 8.3, 2.17)
    K.picture(s, F.fig("sensitivity.png"), 0.55, 4.1, 8.3, 2.35)
    bf = {}
    for d in DIS:
        sw = H[d]["threshold_sweep"]
        bf[d] = max(sw, key=lambda t: t["f1"])
    ftext(s, 9.1, 1.85, 3.8, 5.0, bullets([
        "Best-F1 threshold (0.20-0.80): " + "; ".join(f"{F.NAME[d].split()[0].lower()} {bf[d]['threshold']:.2f}" for d in DIS) + ". The app always uses 0.50.",
        "Trees peak at depth 4-8 and drop when deeper (they fit label noise); RF is flat beyond 50 trees.",
        "SVM is best at C 0.3-1 and falls to 77-83% accuracy at C = 100.",
        "No grid search was run: shipped settings are reasonable but untuned.",
    ], 8), size=13)
    notes[19] = "Threshold sweep is on the test predictions of the served model (precision, recall, F1). Sensitivity: test accuracy, seed-42 split, one parameter varied at a time."

    # ---- 20 real-data check
    s = S[19]
    set_title(s, "Supplementary Check on Real Public Data")
    wipe(s)
    K.picture(s, F.fig("real_vs_synthetic.png"), 0.45, 1.8, 7.3, 3.05)
    rows = [["Disease", "Real data", "Shipped acc.", "AUC", "Majority"]]
    src = {"diabetes": "Pima, 768", "heart": "Cleveland, 303", "liver": "ILPD, 583", "kidney": "UCI CKD, 400"}
    for d in DIS:
        sh_ = R[d]["shipped_on_real"]
        rows.append([F.NAME[d].split()[0], src[d], F.pct(sh_['accuracy']), f"{sh_['roc_auc']:.3f}", F.pct(R[d]['majority_rate'])])
    ftable(s, 7.95, 1.9, [1.0, 1.4, 1.05, 0.65, 0.8], rows, size=11, row_h=0.45, align=["l", "l", "c", "c", "c"])
    ftext(s, 0.55, 5.0, 12.3, 1.9, bullets([
        "Same four algorithms, 5-fold CV x 3 on real data: best accuracy 76.5% (diabetes), 84.3% (heart), 71.8% (liver), 98.8% (kidney) - far below 88-92% on synthetic data except for kidney.",
        "Shipped synthetic-trained models keep some ranking power (AUC 0.75-0.99) but the 0.5 rule transfers badly: liver accuracy 54.0% is below the 71.4% majority baseline.",
        "Not used by the application; it shows why synthetic scores must not be read as clinical performance.",
    ], 6), size=13)
    notes[20] = "Scripts/real_data_check.py. Heart codes (cp, slope, thal) had to be mapped; the thal mapping is arbitrary. Sources: Pima (NIDDK), UCI Cleveland, UCI ILPD, UCI CKD."

    # ---- 21 performance and testing
    s = S[20]
    set_title(s, "Performance & Testing")
    wipe(s)
    lat = API["latency"]
    p = lat["POST /api/predict/diabetes"]
    c4 = lat["POST /api/predict/diabetes (4 concurrent clients)"]
    tiles(s, [(f"{F.API_CHECKS[0]}/{F.API_CHECKS[1]}", "API checks passed (api_tests.py)", K.FBLUE), (str(F.SMOKE_CHECKS), "smoke-test checks passed", K.GREEN),
              (f"{p['p50_ms']:.1f} ms", "median predict call (127.0.0.1)", K.ORANGE), (f"{c4['throughput_rps']:.0f} /s", "requests per second, 4 clients", K.PURPLE)], 1.9, 1.15, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["Model reproduction", "all 16 model / disease cells re-computed; shipped pickles re-scored", "16 of 16 match training_report.json"],
            ["API tests (api_tests.py)", "every route, both classes, invalid input (abc, nan, inf, null), 404/405/422, API = direct model on 40 rows", f"{F.API_CHECKS[0]}/{F.API_CHECKS[1]} passed"],
            ["Browser walk (Playwright, Chrome)", "20 screens at 1440 x 900 plus a 390 px phone view, real CSV rows", "all screens captured"],
            ["Not done", "pytest suite, load / security test, user study, clinical validation", "stated as limits"]]
    ftable(s, 0.55, 3.3, [3.1, 6.3, 2.8], rows, size=12, row_h=0.62)
    ftext(s, 0.55, 6.62, 12.2, 0.4, "Measured on an i5-12500 CPU while the PC was under memory pressure; timer resolution about 15 ms. A prediction takes well under 25 ms end to end.", size=11, color=K.FNAVY, italic=True)
    notes[21] = "Observations, not failures: the API accepts impossible values such as glucose 100,000 or age -5, because there is no clinical range validation."

    # ---- 22 comparison with the base paper
    s = S[21]
    set_title(s, "Comparison with Base Paper (context only – different data)")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "This project"],
            ["Disease and data", "Thyroid; real UCI data, 7,200 samples, 21 features", "Four diseases; synthetic, 4 x 2,000 rows, 8-13 features"],
            ["Task", "Three classes (normal / hypo / hyperthyroid)", "Binary high-risk / low-risk per disease"],
            ["Protocol", "Nested CV: 5 outer, 3 inner folds with grid search", "One stratified 80/20 split, fixed settings; CV and 10 splits added by us"],
            ["Models", "SVC, RF, Extra Trees, AdaBoost, CatBoost", "LR, Decision Tree, RF, SVM"],
            ["Reported", "RF / CatBoost accuracy 0.996-0.997, AUC 0.999-1.000", f"Accuracy {F.pct(min(ho(d, 'accuracy') for d in DIS))}-{F.pct(max(ho(d, 'accuracy') for d in DIS))}; real-data CV 72-99%"],
            ["Explanation", "SHAP and counterfactual 'what-if' analysis", "None in the app (offline permutation importance only)"],
            ["Beyond the paper", "-", "One interface for four diseases; synthetic-vs-real audit; selection-robustness study"]]
    ftable(s, 0.55, 1.85, [2.0, 5.0, 5.2], rows, size=12, row_h=0.56)
    ftext(s, 0.55, 6.45, 12.2, 0.5, "Not comparable: different disease, data, class count and protocol. The numbers are context, not a ranking; we do not claim to match the paper.", size=13, color=K.FNAVY, italic=True)
    notes[22] = "State plainly that the base paper uses real thyroid data with nested cross-validation. Our data are synthetic, so no like-for-like comparison is possible."

    # ---- 23-25 output screens
    s = S[22]
    set_title(s, "Output Screens – Predictions (high risk) & Analysis")
    wipe(s)
    screens(s, [("05_predict-diabetes.png", "Diabetes: High Risk 90.71% (SVM)"), ("06_predict-heart.png", "Heart disease prediction"), ("07_predict-liver.png", "Liver disease prediction"),
                ("08_predict-kidney.png", "Kidney disease prediction"), ("09_models.png", "Model comparison"), ("10_datasets.png", "Datasets, with synthetic-data warning")])
    notes[23] = "Real screenshots: each prediction page filled from a real CSV row ('Positive sample'), the model-comparison page and the dataset page that states the data are synthetic."
    s = S[23]
    set_title(s, "Output Screens – Low-Risk Results & Navigation")
    wipe(s)
    screens(s, [("01_landing-dark.png", "Landing page (dark)"), ("04_overview.png", "Overview"), ("13_predict-diabetes-low-risk.png", "Diabetes: Low Risk 88.18%"),
                ("14_predict-heart-low-risk.png", "Heart disease: Low Risk"), ("15_predict-liver-low-risk.png", "Liver: Low Risk 87.07%"), ("16_predict-kidney-low-risk.png", "Kidney: Low Risk")])
    notes[24] = "Landing and overview pages, then label-0 samples scored by the models."
    s = S[24]
    set_title(s, "Output Screens – Failure Case, Validation & Phone Layout")
    wipe(s)
    for i, (f, cap) in enumerate([("20_predict-heart-false-positive.png", "Failure: label-0 heart row scored High Risk 99.53%"), ("17_validation-error.png", "Empty form: 'Required.' on every field"),
                                  ("18_out-of-range-warning.png", "Glucose 900: outside-training-range warning")]):
        x = 0.55 + i * 4.1
        K.picture(s, F.shot(f), x, 1.85, 3.95, 2.25, border=True)
        ftext(s, x, 4.12, 3.95, 0.45, cap, size=12, color=K.FNAVY, align="c")
    K.picture(s, F.shot("19_predict-heart-mobile.png"), 0.9, 4.65, 1.15, 2.3, border=True)
    ftext(s, 2.2, 4.8, 3.0, 1.5, "Phone layout (390 px): the form stacks in one column.", size=12, color=K.FNAVY)
    K.picture(s, F.shot("12_not-found.png"), 5.3, 4.65, 3.95, 2.25, border=True)
    ftext(s, 9.6, 4.8, 3.3, 1.9, "Honest note: the false positive is a genuine miss of the model on a label-0 record; the app warns that the model may disagree with the label.", size=12, color=K.DARK)
    notes[25] = "The third output slide shows failure and edge cases: a real false positive, validation errors, out-of-range warning, the phone layout and the 404 page."

    # ---- 26 conclusion and future scope
    s = S[25]
    set_title(s, "Conclusion & Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.85, 6.3, 5.1, [("Conclusion", {"bold": True, "color": K.FNAVY, "size": 18, "space_after": 6})] + bullets([
        "**Delivered:** a four-disease risk-screening app: 16 models, FastAPI + React, 7 routes, 41/41 API checks.",
        f"**Measured (synthetic):** accuracy {F.pct(ho('diabetes','accuracy'))} / {F.pct(ho('heart','accuracy'))} / {F.pct(ho('liver','accuracy'))} / {F.pct(ho('kidney','accuracy'))}; near the 92% ceiling.",
        "**Finding:** Logistic Regression is the best model for all four diseases on CV and 10 splits; RF over-fits noisy labels.",
        "**Objectives:** model comparison and one interface achieved; benchmark data, preprocessing, ROC-AUC selection and explanations only partly.",
        "**Not done:** real clinical data, calibration, range validation, recommendations, clinical validation.",
    ], 8), size=15)
    ftext(s, 7.1, 1.85, 5.8, 5.1, [("Future scope", {"bold": True, "color": K.FNAVY, "size": 18, "space_after": 6})] + bullets([
        "Train on real data (UCI / Pima) with imputation, outlier handling and nested CV.",
        "Add explanations: SHAP, counterfactuals as in the base paper.",
        "Calibrate probabilities; choose thresholds by clinical cost.",
        "Add range validation, authentication and persistence.",
        "Score one record against all four diseases at once; add more conditions.",
        "Clinical validation with clinicians before any use.",
    ], 10), size=16)
    notes[26] = "Status of each objective: " + " | ".join(f"{i}: {st}" for i, (st, _) in enumerate(OBJECTIVE_STATUS, 1)) + ". Evaluation is on synthetic data and says so."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    rf = ref_entries()
    keys = sorted([k for k in ("base", "bangla", "pima", "cleveland", "ilpd", "ckd", "scikit", "rf", "svm", "shap", "smote", "varma") if k in rf.NUM], key=lambda k: rf.NUM[k])
    half = (len(keys) + 1) // 2
    ftext(s, 0.55, 1.85, 6.1, 5.1, [(f"[{rf.NUM[k]}] {rf.REFS[rf.NUM[k] - 1]}", {"space_after": 5}) for k in keys[:half]], size=12)
    ftext(s, 6.8, 1.85, 6.0, 5.1, [(f"[{rf.NUM[k]}] {rf.REFS[rf.NUM[k] - 1]}", {"space_after": 5}) for k in keys[half:]], size=12)
    ftext(s, 0.55, 6.7, 12.2, 0.3, "Selected references; the complete list is in the project report.", size=10.5, color=K.FNAVY, italic=True)
    notes[27] = "Selected references; the complete list is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for sl in S:  # the letterhead picture's alt text carries a path from the template's author; replace it
        for el in sl._element.iter():
            d_ = el.get("descr")
            if d_ and ("CSE-D" in d_ or "\\" in d_ or "/" in d_):
                el.set("descr", "College letterhead")
    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
