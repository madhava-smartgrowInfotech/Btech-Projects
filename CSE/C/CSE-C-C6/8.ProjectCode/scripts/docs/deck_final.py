"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited)."""

import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import pptkit as K
from .lit import GAP, OBJECTIVES, PROBLEM_POINTS, PROBLEM_STATEMENT
from .refs import REFS

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


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=12, color=K.DARK, font=FONT)


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.comments = ""
    cp.subject = F.PRODUCT
    cp.keywords = "fake news detection, MSVM, PCA, Firefly algorithm"
    cp.last_modified_by = ""
    notes = {}
    A, LV, EA = F.A, F.LV, F.EA
    PT, PCN = A["proposed_test"], A["per_class_test"]
    LAT = F.LAT[0]
    LR_FULL = A["ref_full_LogisticRegression_test"]
    pc_f1 = {c: PCN[c]["f1-score"]["mean"] for c in F.CLASSES}

    # footers on every slide except the title
    for sl in S:
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    s = S[0]
    for sh in s.shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.TITLE, 28)
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
    notes[1] = "Introduce the team and the project: TruthGlow, a fake news detector built on PCA, the Firefly algorithm and a multi-class SVM, with a complete web application."

    # ---- 2 table of contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh in s.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Dataset & Model\nFirefly Workflow, Interaction & Data Design\nImplementation Highlights\nResults, Confusion Matrix & Parameter Analysis\nPerformance & Testing\nComparison with Base Paper\nOutput Screens\nConclusion, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [
        ("Fabricated news spreads faster than fact-checks, and detectors are often heavy neural models that report accuracy without their cost.", {"bullet": True, "space_after": 10}),
        ("TruthGlow is a light pipeline: TF-IDF and 25 stylometric features are reduced by PCA, the Firefly algorithm selects the components and tunes C and gamma, and a multi-class SVM returns REAL, PARTIALLY TRUE or FAKE with a confidence.", {"bullet": True, "space_after": 10}),
        (f"On real fact-checked statements (LIAR2, 3,000 training statements, {len(F.SEEDS)} seeds) it reaches macro-F1 **{F.pm(PT)}** and accuracy {F.pm(PT, 'accuracy')} on {F.NTEST:,} test statements; the task is hard and PARTIALLY TRUE is the weakest class.", {"bullet": True, "space_after": 10}),
        (f"The optimiser gave no clear gain over PCA with a default SVM or random search, and simple TF-IDF linear models score higher at a tiny fraction of the cost.", {"bullet": True, "space_after": 10}),
        (f"A FastAPI service and React web app add batch checking, analytics and retraining; {F.N_TESTS} automated checks pass.", {"bullet": True}),
    ], size=18)
    notes[3] = "Read the pipeline bullet, then give the headline number with its protocol, then say plainly that the optimiser's gain is not demonstrated."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 0.95, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper (Saad et al., 2026)"],
            ["Method", "CAMeLBERT contextual embeddings as fixed features, a neural-network classifier, class weighting for imbalance; compared with AraBERT, AraELECTRA, MARBERTv2 and resampling (over, under, SMOTE)"],
            ["Data", "7,474 Arabic news articles (2015-2025; trusted sources, unverified online content, part translated from LIAR and WELFake); Fleiss' kappa 0.80; binary real / fake; 80 / 20 split"],
            ["Reported results", "F1 96.19 %, accuracy 95.52 %, precision 95.48 %, recall 96.90 %; TF-IDF + NN baseline accuracy 90.97 %; LIME and SHAP explanations"],
            ["Stated limits", "Cross-domain generalisation and real-time deployment left for future work; trained on a Tesla T4 GPU"]]
    ftable(s, 0.55, 2.9, [2.0, 10.2], rows, size=14, row_h=0.78)
    notes[4] = "An Arabic, binary, transformer-based detector. We adopt its use of class weighting and its habit of reporting several metrics against baselines, not its model or data."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    rows = [["Author / Year", "Methodology", "Dataset", "Key Results", "Limitations"],
            ["Saad et al. 2026 [1]", "CAMeLBERT embeddings + NN, class weighting", "7,474 Arabic articles, binary", "F1 96.19 %, acc. 95.52 %", "Arabic, binary, GPU transformer"],
            ["Dell'Oglio et al. 2026 [2]", "12 approaches compared (ML, DL, transformers, LLMs)", "10 English datasets incl. LIAR-PLUS", "LIAR-PLUS hardest: F1 0.56 (LR), 0.57 (SVM)", "Binary labels hide half-truths"],
            ["Huang et al. 2025 [3]", "TF-IDF + Transformer / BiGRU + Bayesian optimisation", "Fake / real news corpus", "99.73 % test accuracy", "Binary; near-perfect score on easy data"],
            ["Xu and Kechadi 2024 [4]", "Fuzzy deep hybrid network; releases LIAR2", "LIAR2, 18,369 / 2,297 / 2,296", "Benchmark used here", "Deep model; no cheap baseline"],
            ["Ahmed et al. 2017 [19]", "N-gram TF-IDF with classical classifiers", "News article corpora", "Linear SVM among the best classical", "Binary, article level"],
            ["Zhang et al. 2018 [25]", "Firefly feature selection for classification", "Benchmark datasets", "Smaller feature sets at similar accuracy", "Search cost; data dependent"]]
    ftable(s, 0.55, 1.85, [2.0, 3.1, 2.4, 2.5, 2.2], rows, size=11, row_h=0.66)
    notes[5] = "Representative work with figures taken from the papers themselves. Four further 2024-2025 papers named in the project survey could not be verified and are listed in the report with that caveat."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.8, [
        (f"**Stated gap:** {GAP}", {"bullet": True, "space_after": 12}),
        ("**Middle verdict:** binary detectors have no place for half-true claims, which are common in fact-checking.", {"bullet": True, "space_after": 12}),
        ("**Cost is rarely reported:** training time and inference latency are seldom given next to accuracy.", {"bullet": True, "space_after": 12}),
        ("**Fair baselines:** metaheuristic tuning is rarely compared with plain random search or with a linear model on the same data.", {"bullet": True, "space_after": 12}),
        ("**Usability:** few works package the detector so that a non-expert can check text, screen a file and retrain.", {"bullet": True}),
    ], size=18)
    notes[6] = "Five gaps. We build for the first, second and fifth, and test the third and fourth honestly."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.95, 12.2, 2.1)
    ftext(s, 0.85, 2.0, 11.6, 2.0, PROBLEM_STATEMENT, size=17, anchor="m")
    for i, (t, b_) in enumerate([("Input", "News headline and text, one item or a CSV of items"), ("Output", "REAL / PARTIALLY TRUE / FAKE, confidence, class probabilities, cue words"), ("Evidence", "Held-out metrics, baselines, latency, tests, retraining on new data")]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.35, 3.9, 1.7, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.45, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 4.95, 3.5, 1.0, b_, size=15)
    ftext(s, 0.55, 6.15, 12.2, 0.5, "Need: " + PROBLEM_POINTS[3][:0] + "an optimised classifier that reduces dimensionality and tunes its own parameters to detect fabricated news accurately and efficiently.", size=13, color=K.FNAVY, italic=True)
    notes[7] = "The statement has three parts: classify into three verdicts, stay light, and report the evidence honestly."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives of the proposal. The conclusion reports which were met: stemming (objective 2) was not implemented and the accuracy/cost advantage in objective 4 and 6 was not demonstrated."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    K.flow(s, 0.55, 2.0, 12.2, 1.1, [("Text", K.FNAVY), ("TF-IDF + stylometric", K.FBLUE), ("Scaler + PCA", K.GREEN), ("Firefly search", K.ORANGE), ("RBF MSVM", K.PURPLE)], size=15, gap=0.35, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, [
        ("Clean text, TF-IDF over 1-2 grams (4,000 terms) plus 25 stylometric signals: capitals, exclamation marks, lexicon ratios, length.", {"bullet": True, "space_after": 10}),
        ("PCA to 95 % variance (capped at 300 components); the Firefly algorithm jointly selects components and tunes C and gamma.", {"bullet": True, "space_after": 10}),
        ("Multi-class RBF SVM with balanced class weights and an explicit PARTIALLY TRUE class; probabilities from Platt scaling.", {"bullet": True, "space_after": 10}),
        ("FastAPI service over the library; React web app with Detect, Batch check, Analytics, Retrain and About screens.", {"bullet": True}),
    ], size=18)
    notes[9] = "The pipeline as a row of boxes, then four properties that matter."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.85, 8.3, 5.0)
    ftext(s, 9.1, 2.0, 3.7, 4.7, [
        ("Presentation: React app, six screens", {"bullet": True, "space_after": 8}),
        ("Application: FastAPI, 8 endpoints, one model held in memory", {"bullet": True, "space_after": 8}),
        ("Domain: src/ library shared with the CLI and Streamlit app", {"bullet": True, "space_after": 8}),
        ("Storage: one joblib model bundle; no database", {"bullet": True}),
    ], size=16)
    notes[10] = "Three tiers plus storage; the domain library is shared by the web app, the CLI and the original Streamlit app."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.flow(s, 0.55, 1.95, 12.2, 1.2, [("LIAR2 statements", K.FNAVY), ("3-class mapping", K.FNAVY), ("Clean + features", K.PURPLE), ("Scaler + PCA", K.GREEN), ("Firefly search", K.ORANGE), ("RBF MSVM", K.FBLUE), ("Test once", K.FNAVY)], size=13, gap=0.2, font=FONT)
    ftext(s, 0.55, 3.5, 12.2, 3.3, [
        ("Real data: LIAR2 (Apache-2.0), PolitiFact statements; true and mostly-true = REAL, half-true = PARTIALLY TRUE, the rest = FAKE.", {"bullet": True, "space_after": 10}),
        (f"{F.NTRAIN:,} training statements drawn stratified from {F.NTRAIN_FULL:,} (the Firefly search needs thousands of SVM fits); scored on the official validation and test splits.", {"bullet": True, "space_after": 10}),
        (f"Firefly: 10 fireflies x 12 generations, about {A['n_firefly_evals']['mean']:.0f} fitness evaluations; fitness = 3-fold CV macro-F1 - 0.02 x share of components kept.", {"bullet": True, "space_after": 10}),
        (f"Baselines on the same split: PCA + default SVM, Firefly mask only, equal-budget random search, TF-IDF linear models; seeds {', '.join(str(x) for x in sorted(F.SEEDS))}.", {"bullet": True}),
    ], size=17)
    notes[11] = "The method and, as important, the fair comparisons we added around it."

    # ---- 12 dataset, features, model
    s = S[11]
    set_title(s, "Dataset, Features & Model")
    wipe(s)
    ftile(s, 0.55, 1.9, 2.9, 1.1, f"{F.NTRAIN_FULL:,}", f"LIAR2 train; {F.NVALID:,} valid; {F.NTEST:,} test", K.FBLUE, 26)
    ftile(s, 0.55, 3.15, 2.9, 1.1, "4,025", "4,000 TF-IDF + 25 stylometric", K.GREEN, 26)
    ftile(s, 0.55, 4.4, 2.9, 1.1, f"{A['n_pca']['mean']:.0f} → {A['n_selected']['mean']:.0f}", f"PCA components → Firefly-selected ({F.pct(A['pca_variance']['mean'])} variance)", K.ORANGE, 24)
    K.picture(s, F.diag("11_feature_pipeline.png"), 3.7, 1.85, 9.1, 3.1)
    K.picture(s, F.fig("f08_feature_funnel.png"), 3.7, 4.95, 4.2, 1.95)
    ftext(s, 8.1, 5.0, 4.7, 1.9, [
        (f"Test classes REAL / PARTIALLY TRUE / FAKE: {F.A['test_class_counts'][0]} / {F.A['test_class_counts'][1]} / {F.A['test_class_counts'][2]}.", {"bullet": True}),
        ("The PCA cap of 300 keeps under a third of the variance on real text.", {"bullet": True}),
        ("RBF SVM, one-vs-rest shape, balanced class weights.", {"bullet": True}),
    ], size=13)
    ftext(s, 0.55, 5.65, 3.0, 1.2, "Means over three seeds; training subsample of 3,000 statements.", size=11, color=K.FNAVY, italic=True)
    notes[12] = "Dataset, feature pipeline and model. The funnel shows 4,025 features reduced to 300 PCA components, then to about 150 selected components."

    # ---- 13 firefly workflow
    s = S[12]
    set_title(s, "Decision Logic: Firefly Search")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.55, 1.8, 5.0, 5.1)
    ftext(s, 5.9, 2.0, 6.9, 4.8, [
        ("Each firefly is a vector: a mask over the PCA components plus log10 C and log10 gamma.", {"bullet": True, "space_after": 10}),
        ("Brightness = 3-fold CV macro-F1 minus 0.02 x the share of components kept.", {"bullet": True, "space_after": 10}),
        ("Dimmer fireflies move towards brighter ones with attractiveness beta0 exp(-gamma r^2); random step alpha decays by 0.97 per generation.", {"bullet": True, "space_after": 10}),
        ("The best vector gives the final mask, C and gamma; the final SVC is fitted on the masked training data and scored once on the test split.", {"bullet": True, "space_after": 10}),
        ("Verdict = class chosen by the SVC; confidence = highest Platt probability.", {"bullet": True}),
    ], size=17)
    notes[13] = "The core algorithm. Note the last bullet: the verdict and the confidence come from two different mechanisms, which matters on slide 19."

    # ---- 14 user-system interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_diagram.png"), 0.55, 1.8, 6.6, 5.1)
    K.picture(s, F.diag("08_use_case_diagram.png"), 7.4, 1.8, 5.4, 5.1)
    notes[14] = "Sequence of one detection request and the use cases of the reader and the model owner. There is no login."

    # ---- 15 data design
    s = S[14]
    set_title(s, "Data Design (file based)")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 7.0, 4.5)
    rows = [["Store", "Content"], ["models/msvm_model.pkl", "shipped demo model bundle"], ["models/liar2_msvm_model.pkl", "model trained on LIAR2 (seed 42)"], ["models/metrics.json", "demo model statistics"],
            ["experiments/liar2/", "seed runs, predictions, latency"], ["uploaded CSV", "temp file, deleted after use"], ["memory: job table", "retrain status"]]
    ftable(s, 7.8, 1.9, [2.7, 2.3], rows, size=11, row_h=0.5)
    ftext(s, 0.55, 6.35, 12.2, 0.5, "There is no SQL database: the diagram models the file and in-memory entities. Predictions are not stored.", size=13, color=K.FNAVY, italic=True)
    notes[15] = "Honest point: the product stores files, not rows."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("8", "REST endpoints (+ /docs)", K.FBLUE), (str(F.N_TESTS), "automated checks", K.GREEN), ("6", "React screens", K.ORANGE), ("1", "command to start (run.bat)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.9, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.3, 12.2, 3.5, [
        ("The existing library is reused unchanged: the API calls the same fit and predict functions as the CLI and Streamlit app.", {"bullet": True, "space_after": 9}),
        ("Validation: at least 5 words per article; CSV only, at most 20,000 rows and 25 MB; retrain limits (4-20 fireflies, 3-30 generations, 1,000-8,000 terms); one retrain at a time (409).", {"bullet": True, "space_after": 9}),
        ("Retraining runs in a background thread; the new model is saved to a temporary file, swapped in atomically and used without a restart.", {"bullet": True, "space_after": 9}),
        ("Each result shows verdict, confidence, class probabilities and the sensational or credibility cue words found.", {"bullet": True}),
    ], size=17)
    notes[16] = "Highlights: reuse of the library, input validation, background retraining and explained results."

    # ---- 17 results: model performance
    s = S[16]
    set_title(s, "Results – Model Performance (LIAR2 test split)")
    wipe(s)
    for i, (v, l, c) in enumerate([(F.f3(PT["f1_macro"]["mean"]), f"macro-F1, ± {PT['f1_macro']['std']:.3f} over {len(F.SEEDS)} seeds", K.FBLUE), (F.f3(PT["accuracy"]["mean"]), "accuracy (majority class: 0.576)", K.GREEN),
                                   (F.f3(LR_FULL["f1_macro"]["mean"]), "macro-F1 of logistic regression, all data", K.ORANGE), (f"{A['train_time_s']['mean']:.0f} s", "training time of the pipeline", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    K.picture(s, F.fig("f01_model_comparison.png"), 0.55, 3.1, 7.6, 3.75)
    ftext(s, 8.4, 3.15, 4.4, 3.7, [
        ("Majority class gets the best accuracy but macro-F1 0.244: accuracy alone misleads on this data.", {"bullet": True, "space_after": 6}),
        ("PCA + default SVM, random search and Firefly are within about 0.01 macro-F1 of each other.", {"bullet": True, "space_after": 6}),
        ("TF-IDF linear models are better; trained on all 18,369 statements logistic regression reaches 0.500.", {"bullet": True, "space_after": 6}),
        (f"Test = {F.NTEST:,} statements never used for training or tuning.", {"bullet": True}),
    ], size=13)
    notes[17] = "Headline: macro-F1 0.43 and accuracy 0.49 for the proposed pipeline. Its optimiser gives no clear gain over its own simpler variants, and linear TF-IDF models do better."

    # ---- 18 confusion matrix & per-class
    s = S[17]
    set_title(s, "Confusion Matrix & Per-Class Results")
    wipe(s)
    K.picture(s, F.fig("f03_confusion_matrix.png"), 0.55, 1.85, 5.2, 4.4)
    K.picture(s, F.fig("f04_per_class_prf.png"), 6.0, 1.85, 6.8, 3.2)
    pr = EA["pairs"]
    ftext(s, 6.0, 5.15, 6.8, 1.7, [
        (f"F1 by class: FAKE {pc_f1['FAKE']:.2f}, REAL {pc_f1['REAL']:.2f}, PARTIALLY TRUE {pc_f1['PARTIALLY TRUE']:.2f} (hardest; recall {PCN['PARTIALLY TRUE']['recall']['mean']:.2f}).", {"bullet": True, "size": 14}),
        (f"Most frequent errors (seed 42): FAKE read as REAL {pr['FAKE -> REAL']}, FAKE as PARTIALLY TRUE {pr['FAKE -> PARTIALLY TRUE']}, REAL as FAKE {pr['REAL -> FAKE']}.", {"bullet": True, "size": 14}),
        ("Barely-true statements (labelled FAKE) are split across all three verdicts, so the classes overlap.", {"bullet": True, "size": 14}),
    ], size=14)
    ftext(s, 0.55, 6.35, 5.2, 0.5, "Seed 42; rows = true class, columns = predicted.", size=12, color=K.FNAVY, italic=True)
    notes[18] = "Rows are the true class. FAKE is recognised best because it is the majority class; PARTIALLY TRUE is recognised least, and confused with both neighbours."

    # ---- 19 parameter / confidence analysis
    s = S[18]
    set_title(s, "Parameter & Confidence Analysis")
    wipe(s)
    K.picture(s, F.fig("f02_firefly_convergence.png"), 0.55, 1.85, 4.0, 3.0)
    bins = EA["by_confidence"]
    cats = [f"{b['bin'].replace('[', '').replace(')', '').replace(', ', '-').replace('1.01', '1.0')}\n(n={b['n']})" for b in bins]
    K.bar_chart(s, 4.65, 1.85, 4.2, 3.0, cats, [("Accuracy", [b["accuracy"] for b in bins])], colors=[K.FBLUE], number_format="0%", font_size=9, legend=False, max_value=1.1)
    K.picture(s, F.fig("f11_label_vs_probability.png"), 8.95, 1.85, 3.9, 3.0)
    ftext(s, 0.55, 4.95, 4.0, 0.4, "Firefly fitness per generation, 3 seeds (dotted = random search)", size=10, color=K.FNAVY, italic=True)
    ftext(s, 4.65, 4.95, 4.2, 0.4, "Accuracy by confidence bin (seed 42)", size=10, color=K.FNAVY, italic=True)
    ftext(s, 8.95, 4.95, 3.9, 0.4, "Verdict vs highest-probability class", size=10, color=K.FNAVY, italic=True)
    ftext(s, 0.55, 5.4, 12.2, 1.5, [
        (f"No decision threshold exists in TruthGlow; the closest analogue is confidence: accuracy is 0.37 at confidence 0.4-0.5 and 0.68-0.79 at 0.6-0.8, so high confidence is informative.", {"bullet": True, "size": 13}),
        (f"Firefly keeps {A['n_selected']['mean']:.0f} ± {A['n_selected']['std']:.0f} of 300 components (C {A['best_C']['mean']:.1f}, gamma {A['best_gamma']['mean']:.4f}); its training fitness {A['firefly_fitness_best']['mean']:.3f} beats random search {A['random_fitness_best']['mean']:.3f}, but test macro-F1 does not.", {"bullet": True, "size": 13}),
        (f"Verdict (SVC.predict) and probabilities (Platt) disagree on {LV['disagree_rate'] * 100:.1f}% of test statements; the probabilities almost always favour FAKE and never favour PARTIALLY TRUE.", {"bullet": True, "size": 13}),
    ], size=13)
    notes[19] = "Three analyses in place of a threshold sweep. The mismatch between verdict and probability is a defect found by this evaluation, not hidden."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{LAT['predict_server_ms']['mean']:.1f} ms", "server time per article (mean)", K.FBLUE), (f"{LAT['predict_client_ms']['p50']:.1f} ms", f"round trip, median (p95 {LAT['predict_client_ms']['p95']:.0f} ms)", K.GREEN),
                                   (f"{LAT['batch']['2296']['server_s']:.1f} s", "batch of 2,296 statements", K.ORANGE), (f"{A['train_time_s']['mean']:.0f} s", "training incl. Firefly (CPU)", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 26)
    rows = [["Test layer", "What it covers", "Result"],
            ["Smoke test", "running server: all endpoints, retrain, errors", f"{F.N_SMOKE} / {F.N_SMOKE} checks"],
            ["Unit tests", "cleaning, features, labels, Firefly, pipeline, save/load", f"{F.N_UNIT_LIB} / {F.N_UNIT_LIB} checks"],
            ["API edge tests", "limits, empty or garbage input, non-English text, 413 / 422 / 400", f"{F.N_UNIT_API} / {F.N_UNIT_API} checks"],
            ["Build", "npm run build (tsc + vite)", "passes"]]
    ftable(s, 0.55, 3.2, [2.1, 5.2, 2.0], rows, size=12, row_h=0.46)
    K.picture(s, F.fig("f07_training_time.png"), 9.95, 3.1, 2.9, 1.7)
    ftext(s, 0.55, 5.65, 12.2, 1.2, [
        ("Linear models train in 0.1-1 s on the same data, against about 500 s for the Firefly pipeline (random search alone: 480 s).", {"bullet": True, "size": 13}),
        (f"Measured on 127.0.0.1 on an Intel Core i5-12500 (6 cores, 12 threads) with the CPU idle. Not tested: load, a user study, React component tests; one known library issue (true/false-only label columns).", {"bullet": True, "size": 13}),
    ], size=13)
    notes[20] = "Inference is cheap; training with the Firefly search is the costly step. The tests cover the library and API, not the browser."

    # ---- 21 comparison with the base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper (context only – different task and data)")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", f"This project ({F.PRODUCT})"],
            ["Language / data", "Arabic, 7,474 articles, multi-source", f"English, LIAR2: {F.NTRAIN_FULL:,} / {F.NVALID:,} / {F.NTEST:,} statements"],
            ["Task", "Binary real / fake", "Three classes: REAL / PARTIALLY TRUE / FAKE"],
            ["Features", "CAMeLBERT contextual embeddings", "TF-IDF 1-2 grams + 25 stylometric, PCA"],
            ["Classifier", "Neural network with class weights", "RBF multi-class SVM, balanced weights, Firefly tuned"],
            ["Reported", "Accuracy 95.52 %, F1 96.19 %", f"Accuracy {F.pct(PT['accuracy']['mean'])}, macro-F1 {F.pct(PT['f1_macro']['mean'])} (3 seeds)"],
            ["Compute", "Tesla T4 GPU", "CPU only; training about 500 s, inference about 4 ms"]]
    ftable(s, 0.55, 1.85, [2.0, 4.7, 5.5], rows, size=13, row_h=0.62)
    ftext(s, 0.55, 6.3, 12.2, 0.6, "Different language, data, task (binary vs three classes), model family and hardware: the figures are context, not a ranking. The related binary LIAR-PLUS result in [2] (LR F1 0.56) shows how hard this kind of data is.", size=13, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that the datasets and tasks differ; no superiority or inferiority claim is possible from these numbers."

    # ---- 22-24 output screens
    s = S[21]
    set_title(s, "Output – Detect")
    wipe(s)
    K.picture(s, F.shot("11_liar2_detect_fake.png"), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("13_liar2_detect_partial.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.15, 12.2, 0.8, "Left: a real LIAR2 test statement (Ron DeSantis shirt photo, true label FAKE) judged FAKE with 83.8 % confidence. Right: a PARTIALLY TRUE verdict shown at 47.2 % while the FAKE bar is tallest: the verdict-probability mismatch of slide 19.", size=12, color=K.FNAVY)
    notes[22] = "Real screenshots from the app running the LIAR2 model. The right-hand screen illustrates the verdict/probability disagreement."
    s = S[22]
    set_title(s, "Output – Batch Check and Model Analytics")
    wipe(s)
    K.picture(s, F.shot("16_liar2_batch_results.png"), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("18_liar2_analytics_charts.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.15, 12.2, 0.8, "Left: 120 real test statements screened (44 REAL, 24 PARTIALLY TRUE, 52 FAKE); the 1.51 s shown was captured while another job was running; the idle server needed about 0.13 s per 100 rows. Right: confusion matrix, Firefly curve, class report and baseline-vs-proposed table of the loaded model.", size=12, color=K.FNAVY)
    notes[23] = "The analytics screen reads its numbers live from the loaded model and shows the gain from optimisation honestly (negative on that seed)."
    s = S[23]
    set_title(s, "Output – Retrain")
    wipe(s)
    K.picture(s, F.shot("20_liar2_retrain.png"), 0.55, 1.85, 6.0, 4.2, border=True)
    K.picture(s, F.shot("22_liar2_retrain_done.png"), 6.8, 1.85, 6.0, 4.2, border=True)
    ftext(s, 0.55, 6.15, 12.2, 0.8, "Left: a 600-statement LIAR2 CSV attached, 4 fireflies, 3 generations. Right: the finished job (137 s): accuracy 42.50 %, macro-F1 0.4113, 147 of 300 components kept; the new model replaced the one in memory without a restart (run on a copy of the model file).", size=12, color=K.FNAVY)
    notes[24] = "Retraining on a user CSV from the browser. The small sample explains the lower scores."

    # ---- 25 conclusion
    s = S[24]
    set_title(s, "Conclusion")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [
        ("**Delivered:** a working fake news detector: cleaning, TF-IDF + stylometric features, PCA, Firefly search, MSVM with a PARTIALLY TRUE class, a FastAPI service and a six-screen web app with batch checking, analytics and retraining.", {"bullet": True, "space_after": 9}),
        (f"**Measured:** macro-F1 {F.pm(PT)} and accuracy {F.pm(PT, 'accuracy')} on LIAR2; about 4 ms per article on the server; {F.N_TESTS} automated checks pass.", {"bullet": True, "space_after": 9}),
        ("**Objectives:** 1 (with LIAR2; the shipped demo corpus is synthetic), 3, 5 met; 2 partly (no stemming); 4 and 6 done but the expected benefit was not shown: Firefly tuning is within noise of random search and of a default SVM, and linear TF-IDF models score higher at far lower cost.", {"bullet": True, "space_after": 9}),
        ("**Limits:** 3,000-statement training subsample, three seeds, PARTIALLY TRUE recognised poorly, verdict and probabilities disagree, no user study. Not a fact-checker.", {"bullet": True}),
    ], size=18)
    notes[25] = "Be explicit: the system works, the accuracy/cost advantage of the optimiser was not demonstrated on real data."

    # ---- 26 future scope
    s = S[25]
    set_title(s, "Future Scope")
    wipe(s)
    ftext(s, 0.55, 1.95, 12.2, 4.9, [
        ("Make verdict and probability consistent: calibrate probabilities with class-prior correction, or derive the verdict from the calibrated scores.", {"bullet": True, "space_after": 12}),
        ("Test PCA without the 300 cap, or sparse linear / Complement NB models with the Firefly feature search, against the same baselines.", {"bullet": True, "space_after": 12}),
        ("Train on all 18,369 statements with a cheaper fitness; tune the Firefly parameters; add ISOT and cross-dataset tests and a significance test.", {"bullet": True, "space_after": 12}),
        ("Add stemming (objective 2) and richer, fact-checking-aware features such as source and evidence cues.", {"bullet": True, "space_after": 12}),
        ("User study with fact-checkers; update the fixed UI wording for non-demo models.", {"bullet": True}),
    ], size=19)
    notes[26] = "Concrete next steps, the first three follow directly from the findings."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = [1, 2, 3, 4, 5, 6, 8, 10, 12, 13, 14, 15, 16, 19]
    ftext(s, 0.55, 1.85, 6.0, 5.0, [(f"[{n}] {REFS[n - 1]}", {"space_after": 3}) for n in ids[:7]], size=11)
    ftext(s, 6.8, 1.85, 6.0, 5.0, [(f"[{n}] {REFS[n - 1]}", {"space_after": 3}) for n in ids[7:]], size=11)
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
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
