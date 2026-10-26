"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (letterhead, rule, title and footer chrome inherited)."""

import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from . import facts as F
from . import lit
from . import pptkit as K
from .refs import CITE as R
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


def ftile(slide, x, y, w, h, value, label, color=K.FBLUE, vsize=26, lsize=12):
    K.box(slide, x, y, w, h, fill=K.FHEAD, line=None, radius=0.05)
    K.box(slide, x, y, 0.08, h, fill=color, line=None, shape=MSO_SHAPE.RECTANGLE)
    K.text(slide, x + 0.2, y + 0.06, w - 0.3, h * 0.55, value, size=vsize, color=K.FNAVY, bold=True, anchor="m", font=FONT)
    K.text(slide, x + 0.2, y + h * 0.58, w - 0.3, h * 0.4, label, size=lsize, color=K.DARK, font=FONT)


CROPS = os.path.join(tempfile.gettempdir(), "c15_deck_crops")


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


def p1(x):
    return f"{x * 100:.1f}%"


def p2(x):
    return f"{x * 100:.2f}%"


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.comments = ""
    cp.last_modified_by = f"Batch {F.BATCH_NO}, Dept. of CSE"
    cp.subject = F.PRODUCT
    cp.keywords = "DDoS detection, Random Forest, CICIDS2017, Scapy, adaptive mitigation, carpet bombing"
    notes = {}
    k = F.K()
    RL, W, H, L, A = F.REAL, F.WIN, F.HYB, F.LAT, F.API
    w2, w5, w10 = W["window_2s"], W["window_5s"], W["window_10s"]
    lat = {(d["method"], d["path"]): d for d in A["latency"]}
    st_lat = lat[("GET", "/api/status")]
    bl = RL["baselines_seed42"]
    abl = RL["ablation_seed42"]
    sr = RL["shipped_on_real_all"]
    rs = RL["real_rf_seed42"]

    for sl in S:  # footers on every slide
        for sh_ in sl.shapes:
            if sh_.top == TOP_FOOT and sh_.has_text_frame and "Final Review" in sh_.text_frame.text:
                K.replace_text(sh_, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh_ in S[0].shapes:
        if sh_.name == "Text 1":
            K.replace_text(sh_, F.FULL_TITLE, 26)
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
    notes[1] = "Introduce the team and SentinelFlow: a working real-time DDoS detection and adaptive mitigation system, with an honest evaluation on real CICIDS2017 flows."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Table of Contents")
    for sh_ in s.shapes:
        if sh_.name == "Text 4":
            K.replace_text(sh_, "Abstract\nBase Paper & Literature Survey\nResearch Gap, Problem Statement & Objectives\nProposed System & Architecture\nMethodology, Data & Algorithm Workflow\nInteraction & Data Design\nImplementation Highlights\nResults: Real-Data Check, Confusion Matrix, Classifiers\nParameter Analysis: Window Length & Severity\nPerformance, Testing & Comparison with Base Paper\nOutput Screens\nConclusion, Limitations, Future Scope & References", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract")
    wipe(s)
    ftext(s, 0.55, 1.8, 12.2, 5.1, [
        ("DDoS attacks flood a service from many sources; detection without action leaves it down, and blocking legitimate users is itself a denial of service. SentinelFlow classifies rolling traffic windows (Scapy or a built-in simulator) with a 200-tree Random Forest, scores how distributed the traffic is, assigns an explainable severity and quarantines the worst sources temporarily, with automatic recovery.", {"bullet": True, "space_after": 7}),
        (f"Honest result: the shipped model was trained on a synthetic fallback. It scores {p2(k['ship_acc'])} on its own split but {p1(k['shipreal_acc'])} accuracy ({p1(k['shipreal_rec'])} recall, {p1(k['shipreal_fpr'])} false positives) on {k['real_rows']:,} real CICIDS2017 DDoS-day flows.", {"bullet": True, "space_after": 7}),
        (f"Retrained on those flows with the same features and settings the forest reaches {p2(k['rr_acc'][0])} over five seeds ({p2(k['blk_acc'])} on a chronological block split).", {"bullet": True, "space_after": 7}),
        (f"Window length matters: at 5 s windows the forest alone flags {p1(k['w5_fpr_ml'])} of benign windows; the severity layer cuts that to {p2(k['w5_fpr_act'])}.", {"bullet": True, "space_after": 7}),
        (f"{F.PYTEST_PASSED} pytest tests and {F.SMOKE_PASSED} smoke checks pass. Mitigation is application-level only (the OS firewall is never touched) and live capture could not be run end to end here (no Npcap).", {"bullet": True}),
    ], size=16)
    notes[3] = "Product first, then the headline honest results: synthetic-trained model does not transfer, retraining fixes it, severity layer removes false alarms, and the limits."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base Paper")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.8, F.BASE_PAPER, size=13, color=K.FNAVY)
    rows = [["Aspect", "Base paper: resource-aware ensemble framework for DDoS detection in SDN"],
            ["Method", "Random Forest importance combined with the Banzhaf Power Index for feature selection; XGBoost, RF, Gradient Boosting, SVM, kNN, AdaBoost, Naive Bayes; four hard-voting ensembles (clf1-clf4)"],
            ["Data", "SDN flow dataset (104,345 records, 23 features) and a CIC-DDoS2023 subset (1,754,109 rows, 47 features); separate models per dataset"],
            ["Reported", "All four ensembles reach 100% accuracy, precision, recall and F1 on both datasets; differences lie in resources"],
            ["Resources", "clf3 and clf4 (SVM) need over 4,000 s to train on the SDN data; clf2 (kNN) over 150 s to classify the SDN test set; clf1 is the lightest and is recommended"],
            ["Stated future work", "Multi-class detection, online learning, federated SDN, a sidecar next to the controller, live testbeds and production traces; mitigation is only outlined"]]
    ftable(s, 0.55, 2.6, [1.9, 10.3], rows, size=12, row_h=0.7)
    notes[4] = "Trigui et al., IEEE Access 2026. The paper stops at offline detection; closing the loop to mitigation and measuring it is what SentinelFlow adds."

    # ---- 5 literature survey
    s = S[4]
    set_title(s, "Literature Survey")
    wipe(s)
    idx = [0, 1, 2, 3, 5, 7, 8, 11]
    rows = [["Work", "Year", "Approach", "Finding / limitation"]] + [list(lit.LIT_TABLE[i]) for i in idx]
    ftable(s, 0.55, 1.75, [2.9, 0.7, 4.5, 4.1], rows, size=10, row_h=0.55, align=["l", "c", "l", "l"])
    notes[5] = "Rows marked title-only could not be verified beyond their bibliographic records, so no result is quoted. All other figures come from the PDFs or abstracts we read."

    # ---- 6 research gap
    s = S[5]
    set_title(s, "Research Gap")
    wipe(s)
    ftext(s, 0.55, 1.85, 12.2, 5.0, [(g, {"bullet": True, "space_after": 18}) for g in lit.GAPS], size=21)
    notes[6] = "The gap from the batch survey: closing the loop from real-time detection to adaptive mitigation with measured latency, and measuring false-positive cost."

    # ---- 7 problem statement
    s = S[6]
    set_title(s, "Problem Statement")
    wipe(s)
    fbox(s, 0.55, 1.85, 12.2, 2.5)
    ftext(s, 0.85, 1.9, 11.6, 2.4, lit.PROBLEM_STATEMENT, size=16, anchor="m", bullets=True)
    for i, (t, b_) in enumerate([("Input", "Rolling windows of packets (Scapy capture or simulator) reduced to ten flow features"), ("Output", "Benign/Attack label, distributed-risk score, severity with factors, quarantine or advice, history"), ("Need", lit.NEED)]):
        x = 0.55 + i * 4.1
        fbox(s, x, 4.6, 3.9, 2.0, fill=K.FZEBRA)
        ftext(s, x + 0.2, 4.68, 3.5, 0.4, t, size=17, color=K.FNAVY, bold=True)
        ftext(s, x + 0.2, 5.15, 3.5, 1.4, b_, size=14)
    notes[7] = "The batch's problem statement and need, then the input and output of the system."

    # ---- 8 objectives
    s = S[7]
    set_title(s, "Objectives")
    wipe(s)
    ftext(s, 0.55, 1.9, 12.2, 4.9, [(f"{i}.  {o}", {"space_after": 12}) for i, o in enumerate(lit.OBJECTIVES, 1)], size=20)
    notes[8] = "The six objectives from the batch document. The conclusion slide gives the status of each."

    # ---- 9 proposed system
    s = S[8]
    set_title(s, "Proposed System")
    wipe(s)
    ftext(s, 0.55, 1.75, 12.2, 0.4, "Per-window pipeline", size=15, color=K.FNAVY, bold=True)
    K.flow(s, 0.55, 2.15, 12.2, 0.85, [("Scapy / simulator", K.FNAVY), ("10-s window", K.FBLUE), ("10 features", K.GREEN), ("Random Forest", K.ORANGE), ("Risk + severity", K.PURPLE), ("Action + SQLite", K.FNAVY)], size=13, gap=0.3, font=FONT)
    ftext(s, 0.55, 3.2, 12.2, 0.4, "Mitigation and presentation", size=15, color=K.FNAVY, bold=True)
    K.flow(s, 0.55, 3.6, 12.2, 0.85, [("Low: monitor", K.GREEN), ("Medium: advise rate limit", K.GOLD), ("High: quarantine top 3", K.ORANGE), ("Critical: 2x duration", K.PURPLE), ("Auto recovery 40 s", K.FBLUE), ("Flask + React console", K.FNAVY)], size=12, gap=0.3, font=FONT)
    ftext(s, 0.55, 4.8, 12.2, 2.1, [
        ("Distributed-risk layer scores source diversity, destination diversity, rate pressure and baseline deviation: the carpet-bombing signature the forest does not see.", {"bullet": True, "space_after": 7}),
        ("Severity is explainable: every contributing factor is listed next to the verdict, and a benign window can never exceed Medium.", {"bullet": True, "space_after": 7}),
        ("Safe by design: quarantine lives inside SentinelFlow, expires on its own and never touches the OS firewall; Simulation Mode emits no packets.", {"bullet": True}),
    ], size=16)
    notes[9] = "The proposed system as two chains. Be explicit that mitigation is an application-level denylist, not a network-level block."

    # ---- 10 architecture
    s = S[9]
    set_title(s, "System Architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.55, 1.8, 7.2, 5.1)
    ftext(s, 7.95, 1.95, 4.9, 4.9, [
        (f"Console: React 19 + Vite, port {F.WEB_PORT}; nine pages plus the legacy dashboard", {"bullet": True, "space_after": 8}),
        (f"API: Flask, port {F.API_PORT}; 12 JSON endpoints, polled every 2 s", {"bullet": True, "space_after": 8}),
        ("Pipeline modules: monitoring, ml, security; one shared process_window()", {"bullet": True, "space_after": 8}),
        ("State: SQLite (4 tables), joblib model, JSON and PNG results", {"bullet": True, "space_after": 8}),
        ("No authentication on the API; it binds to 127.0.0.1", {"bullet": True}),
    ], size=15)
    notes[10] = "Four tiers in one process. The React login is a browser-side demo gate; the API itself has no authentication and is localhost-only."

    # ---- 11 methodology
    s = S[10]
    set_title(s, "Methodology")
    wipe(s)
    K.picture(s, F.diag("02_high_level_workflow.png"), 0.55, 1.8, 7.3, 4.9)
    ftext(s, 8.1, 1.9, 4.7, 5.0, [
        ("Training: clean and map CICIDS2017 flows to ten features (forward = sent, backward = received), add 6,000 simulator windows, stratified 80/20, 200 trees, seed 42.", {"bullet": True, "space_after": 8}),
        ("Online: 10-s windows (2-120 s allowed), same schema, model loaded once.", {"bullet": True, "space_after": 8}),
        ("Added for the evaluation: real-flow check, five seeds, classifier comparison, window-length study, latency and API probes.", {"bullet": True}),
    ], size=14)
    notes[11] = "Offline training once, then a repeating online cycle. The extra measurements were added so that every claim rests on real data."

    # ---- 12 dataset & models
    s = S[11]
    set_title(s, "Dataset & Models")
    wipe(s)
    ftile(s, 0.55, 1.8, 3.9, 1.0, f"{k['ship_n_train'] + k['ship_n_test']:,}", "rows behind the shipped model: synthetic flows + 6,000 windows", K.ORANGE, 24)
    ftile(s, 4.7, 1.8, 3.9, 1.0, f"{k['real_rows']:,}", "real CICIDS2017 Friday DDoS-day flows (evaluation)", K.GREEN, 24)
    ftile(s, 8.85, 1.8, 3.9, 1.0, "10", "flow features shared by training and live windows", K.FBLUE, 24)
    rows = [["Data", "Size", "Used for"],
            ["Synthetic fallback flows", "18,000 + 6,000 windows", "shipped model (CICIDS2017 unreachable at build time)"],
            ["CICIDS2017 Friday-DDoS [8]", f"{k['real_benign']:,} benign / {k['real_attack']:,} DDoS", "real-data check, retraining, classifier comparison"],
            ["Simulator windows", "4,000 per length", "window-length and severity study"],
            ["Models", "RF 200 trees", "shipped; plus DT, HistGB, GaussianNB, LogReg on real flows"]]
    ftable(s, 0.55, 3.0, [2.2, 2.0, 2.9], rows, size=11, row_h=0.6)
    K.picture(s, F.fig("f04_feature_importance_compare.png"), 7.9, 3.0, 4.9, 2.9)
    ftext(s, 0.55, 6.15, 12.2, 0.8, "Importance differs: the shipped forest weights sent_packets (0.21) and received_packets (0.18) most; the forest retrained on real flows relies on average sent packet size (0.23), sent packets and sent bytes. Dataset licence: 'other' (Hugging Face mirror card); the CSV is not committed.", size=12, color=K.FNAVY, italic=True)
    notes[12] = "The shipped model was trained on a labelled synthetic fallback. The real file is used only for evaluation and retraining in the documentation run."

    # ---- 13 core algorithm
    s = S[12]
    set_title(s, "Core Algorithm and Severity Logic")
    wipe(s)
    K.picture(s, F.diag("10_flowchart_core_algorithm.png"), 0.55, 1.75, 4.5, 5.2)
    ftext(s, 5.3, 1.85, 7.5, 5.0, [
        ("Distributed risk = 0.30 x sources/30 + 0.30 x destinations/15 + 0.25 x rate/1500 + 0.15 x baseline deviation (each capped at 1); Medium from 0.4, High from 0.7.", {"bullet": True, "space_after": 8}),
        ("Severity score: +30 for an Attack label, +15 / +8 for confidence of 90% / 75%, rate steps at 400 / 1,200 / 3,000 packets/s, +10 / +20 for risk of 0.4 / 0.7, +8 for wide spread, +5 / +10 for 2 / 3 persistent windows.", {"bullet": True, "space_after": 8}),
        ("Thresholds: Medium 28, High 50, Critical 70; a Benign window is capped at 45.", {"bullet": True, "space_after": 8}),
        ("High and Critical quarantine the three busiest non-protected sources for 40 s (80 s for Critical); expiry marks the row 'recovered'.", {"bullet": True, "space_after": 8}),
        ("Errors (capture failure, missing model, invalid features) return an error record and store nothing.", {"bullet": True}),
    ], size=14)
    notes[13] = "The one function every window passes through. Weights and thresholds are rule-based and visible on the Threat Detail screen."

    # ---- 14 interaction
    s = S[13]
    set_title(s, "User – System Interaction")
    wipe(s)
    K.picture(s, F.diag("07_sequence_main_flow.png"), 0.55, 1.8, 6.4, 5.1)
    K.picture(s, F.diag("08_use_case.png"), 7.1, 1.8, 5.7, 5.1)
    notes[14] = "Sequence of one window in Simulation Mode and the use cases of the administrator."

    # ---- 15 design
    s = S[14]
    set_title(s, "Data and Class Design")
    wipe(s)
    K.picture(s, F.diag("09_er_diagram.png"), 0.55, 1.8, 6.2, 4.4, border=False)
    K.picture(s, F.diag("06_uml_class.png"), 6.95, 1.75, 5.85, 4.5)
    ftext(s, 0.55, 6.3, 12.2, 0.7, "SQLite holds four tables (detections, mitigations, health_samples, settings) with no foreign keys; the settings table exists but the API keeps settings in memory. Four real classes plus function modules drawn as <<module>>.", size=12, color=K.FNAVY, italic=True)
    notes[15] = "ER diagram of the database and the class diagram of the code."

    # ---- 16 implementation highlights
    s = S[15]
    set_title(s, "Implementation Highlights")
    wipe(s)
    for i, (v, l, c) in enumerate([("12", "JSON endpoints", K.FBLUE), (f"{F.PYTEST_TOTAL} + {F.SMOKE_TOTAL}", "pytest tests + smoke checks", K.GREEN), ("8", "React screens", K.ORANGE), (f"{st_lat['p50_ms']:.1f} ms", "median /api/status over HTTP", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.85, 2.9, 1.1, v, l, c, 28)
    ftext(s, 0.55, 3.25, 12.2, 3.6, [
        ("One process_window() serves live capture and Simulation Mode, so the demo exercises the real model, severity and mitigation code.", {"bullet": True, "space_after": 9}),
        ("Settings are validated (window 2-120 s, quarantine 5-3600 s); a second Start returns 409; capture failures surface the real reason (Npcap missing).", {"bullet": True, "space_after": 9}),
        ("Threat Detail lists every severity factor and the distributed-risk components for any stored window.", {"bullet": True, "space_after": 9}),
        ("run.bat prepares the environment, starts the API (8415) and the console (5415); Docker files exist but were not run here.", {"bullet": True, "space_after": 9}),
        ("Not present: OS-level blocking, API authentication, tested live capture, multi-class detection.", {"bullet": True}),
    ], size=16)
    notes[16] = "Highlights and honest absences."

    # ---- 17 results: real-data check
    s = S[16]
    set_title(s, "Results – Synthetic Split versus Real Flows")
    wipe(s)
    for i, (v, l, c) in enumerate([(p2(k["ship_acc"]), f"shipped model, own synthetic test ({k['ship_n_test']:,} rows)", K.FBLUE),
                                   (p1(k["shipreal_acc"]), f"shipped model on {k['real_rows']:,} real flows", K.ORANGE),
                                   (p2(k["rr_acc"][0]), "retrained RF on real flows, 5-seed mean", K.GREEN),
                                   (p2(k["blk_acc"]), "retrained, chronological block split", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.8, 2.9, 1.1, v, l, c, 26, lsize=11)
    K.picture(s, F.fig("f01_domain_gap.png"), 0.55, 3.0, 6.9, 3.2)
    ftext(s, 7.7, 3.05, 5.1, 3.2, [
        (f"On real flows the shipped model keeps only {p1(k['shipreal_rec'])} recall and raises {p1(k['shipreal_fpr'])} false positives; ROC-AUC is {p1(k['shipreal_auc'])}, so the 0.5 threshold, not the ranking, is the main problem.", {"bullet": True, "space_after": 6}),
        (f"Retraining with the product's own features and settings gives {p2(k['rr_acc'][0])} (±{k['rr_acc'][1] * 100:.2f}), FPR {p2(k['rr_fpr'][0])}.", {"bullet": True, "space_after": 6}),
        ("Caveats: one attack type, random flow splits overlap in time, and CICIDS2017 labels have known flaws [9].", {"bullet": True}),
    ], size=13)
    ftext(s, 0.55, 6.3, 12.2, 0.7, f"A flow-trained forest applied to simulator windows calls every window benign (recall 0.0%, ROC-AUC 100%): flow-scale and window-scale features differ, which is why the product adds window rows to training.", size=12, color=K.FNAVY, italic=True)
    notes[17] = "The central honest finding. 99.71 percent on the synthetic split does not carry over; the same forest retrained on real flows reaches 99.94 percent."

    # ---- 18 confusion matrix and classifiers
    s = S[17]
    set_title(s, "Confusion Matrices & Classifier Comparison")
    wipe(s)
    K.picture(s, F.fig("f06_confusion_matrices.png"), 0.55, 1.75, 7.4, 2.3)
    rows = [["Experiment", "Acc.", "Prec.", "Recall", "F1", "FPR"]]
    for nm, d in [("Shipped, own split", None), ("Shipped, real flows", sr), ("Retrained RF, seed 42", rs), ("Block split", RL["real_rf_block_split"])]:
        if d is None:
            rows.append([nm, p2(k["ship_acc"]), p2(k["ship_prec"]), p2(k["ship_rec"]), p2(k["ship_f1"]), p2(k["ship_fpr"])])
        else:
            rows.append([nm] + [p2(d[m]) for m in ("accuracy", "precision", "recall", "f1", "fpr")])
    ftable(s, 0.55, 4.15, [2.3, 0.97, 0.97, 0.97, 0.97, 0.97], rows, size=11, row_h=0.34, align=["l", "c", "c", "c", "c", "c"])
    K.picture(s, F.fig("f03_classifier_comparison.png"), 8.15, 1.75, 4.65, 2.0)
    ftext(s, 8.15, 3.95, 4.65, 2.9, [
        (f"Same real split: decision tree {p2(bl['DecisionTree']['accuracy'])}, RF {p2(bl['RandomForest(200)']['accuracy'])}, HistGradientBoosting {p2(bl['HistGradientBoosting']['accuracy'])}; logistic regression {p2(bl['LogisticRegression(scaled)']['accuracy'])}; Gaussian NB {p1(bl['GaussianNB']['accuracy'])}.", {"bullet": True, "space_after": 5}),
        (f"Counts and bytes alone give {p2(abl['counts_and_bytes_only']['accuracy'])}: the DDoS day separates on size and count.", {"bullet": True, "space_after": 5}),
        ("Random Forest is kept for the product: tree models tie, the RF gives a calibrated confidence for severity.", {"bullet": True}),
    ], size=11)
    ftext(s, 0.55, 6.1, 7.4, 0.8, f"False-positive rate = FP / (FP + TN). Shipped on its own split: {k['ship_fp']} false positive and {k['ship_fn']} false negatives in {k['ship_n_test']:,} windows.", size=11, color=K.FNAVY, italic=True)
    notes[18] = "Confusion matrices for the three situations, the precision/recall/F1 table, and a comparison with other classifiers on the same real split (the base paper compared classifiers too)."

    # ---- 19 parameter analysis
    s = S[18]
    set_title(s, "Parameter Analysis – Window Length and Severity Thresholds")
    wipe(s)
    K.picture(s, F.fig("f02_window_size_effect.png"), 0.55, 1.75, 6.3, 2.65)
    K.picture(s, F.fig("f07_severity_by_style.png"), 7.0, 1.75, 5.8, 2.65)
    rows = [["Window", "RF label: FPR", "High/Critical: FPR", "High/Critical: recall", "Risk >= 0.7 alone: recall"]]
    for nm, d in (("2 s", w2), ("5 s", w5), ("10 s", w10)):
        rows.append([nm, p1(d["ml_only"]["fpr"]), p2(d["actionable_high_or_critical"]["fpr"]), p1(d["actionable_high_or_critical"]["recall"]), p1(d["distributed_risk_ge_0.7_only"]["recall"])])
    ftable(s, 0.55, 4.55, [0.8, 1.2, 1.5, 1.6, 1.9], rows, size=10, row_h=0.4, align=["c", "c", "c", "c", "c"])
    ftext(s, 8.0, 4.5, 4.8, 2.5, [
        ("4,000 simulator windows per length (35% attack); model calibrated on 10 s windows.", {"bullet": True, "space_after": 4}),
        ("The severity layer removes most false alarms; at 10 s, 44 weaker attack windows stay at Medium.", {"bullet": True, "space_after": 4}),
        ("10 s RF accuracy is 100% only because training rows came from the same generator.", {"bullet": True, "space_after": 4}),
        ("The risk score alone is precise but misses most attacks.", {"bullet": True}),
    ], size=11)
    ftext(s, 0.55, 6.3, 7.5, 0.7, "Left chart: false positives on benign windows and attack windows reaching High/Critical. Right chart: severity per traffic style at 5 s.", size=11, color=K.FNAVY, italic=True)
    notes[19] = "Window length is the key parameter: at 2 s and 5 s the forest alone raises many false alarms; the severity thresholds absorb most of them. The distributed-risk score alone is a weak detector."

    # ---- 20 performance & testing
    s = S[19]
    set_title(s, "Performance & Testing")
    wipe(s)
    d2m = L["detect_to_mitigation_ms"]
    for i, (v, l, c) in enumerate([(f"{d2m['p50']:.0f} ms", f"features to mitigation decision, median (p95 {d2m['p95']:.0f})", K.FBLUE),
                                   (f"{L['single_inference_ms_n_jobs_-1']['p50']:.0f} vs {L['single_inference_ms_n_jobs_1']['p50']:.0f} ms", "one-window inference, n_jobs=-1 (as saved) vs 1", K.ORANGE),
                                   (f"{st_lat['p50_ms']:.1f} ms", "/api/status median, 100 calls", K.GREEN),
                                   (f"{A['probes_ok']}/{A['probes_total']}", "malformed-input probes handled", K.PURPLE)]):
        ftile(s, 0.55 + i * 3.1, 1.8, 2.9, 1.0, v, l, c, 22, lsize=11)
    K.picture(s, F.fig("f08_latency_breakdown.png"), 0.55, 2.9, 6.3, 2.3)
    K.picture(s, F.fig("f09_api_latency.png"), 7.0, 2.9, 5.8, 2.3)
    rows = [["Check", "Result"],
            ["pytest (units + API, scratch SQLite)", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed; smoke test {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} backend checks on the running server"],
            ["Not tested", "live capture end to end (no Npcap), load, concurrent users, Docker build, real attack timeline"]]
    ftable(s, 0.55, 5.3, [4.3, 7.9], rows, size=11, row_h=0.4)
    ftext(s, 0.55, 6.6, 12.2, 0.4, "Measured on an i5-12500 with the CPU at 100% from other jobs, so absolute times are upper bounds. The real delay is the window length (10 s default).", size=11, color=K.FNAVY, italic=True)
    notes[20] = "Decision latency is dominated by forest inference with the saved n_jobs=-1. Detection to mitigation here means from the finished feature vector to the decision; a window must close first."

    # ---- 21 comparison with base paper
    s = S[20]
    set_title(s, "Comparison with Base Paper")
    wipe(s)
    rows = [["Aspect", "Base paper [1]", "SentinelFlow (this project)"],
            ["Data", "SDN flows (104,345 rows) and CIC-DDoS2023 subset (1.75 M rows)", f"CICIDS2017 DDoS day ({k['real_rows']:,} flows) and a synthetic fallback"],
            ["Features", "23 and 47 columns, RF + Banzhaf selection", "10 fixed flow features shared with live windows"],
            ["Models", "Seven classifiers, four voting ensembles", f"One 200-tree RF; DT, HistGB, NB, LogReg compared (RF {p2(k['rr_acc'][0])})"],
            ["Result", "100% on both datasets", f"{p2(k['rr_acc'][0])} retrained on real flows; {p1(k['shipreal_acc'])} for the shipped synthetic model"],
            ["Resources", "SVM ensembles over 4,000 s training; kNN over 150 s inference", f"RF trains in {RL['real_rf_per_seed'][0]['train_seconds']:.1f} s; model {RL['real_rf_model_mb']} MB"],
            ["Mitigation", "Future work (throttling or blackholing outlined)", "Implemented: application-level quarantine with recovery"]]
    ftable(s, 0.55, 1.8, [1.4, 4.4, 4.6], rows, size=11, row_h=0.62)
    ftext(s, 11.1, 1.85, 1.8, 4.3, [("Datasets and protocols differ: indicative only.", {"space_after": 8}), ("Our result is lower than 100%.", {"space_after": 8}), ("No superiority is claimed.", {})], size=12, color=K.FNAVY, italic=True)
    ftext(s, 0.55, 6.3, 12.2, 0.7, "Not taken from the base paper: Banzhaf feature selection and voting ensembles. Added against it: severity, mitigation, recovery, a simulator and an evaluation that separates synthetic from real data.", size=12, color=K.FNAVY, italic=True)
    notes[21] = "State plainly that datasets and protocols differ. Their 100 percent is on SDN and CIC-DDoS2023; ours is CICIDS2017 DDoS-day flows."

    # ---- 22-24 output screens
    cap = "Simulation Mode data scored by the real model"
    s = S[21]
    set_title(s, "Output – Landing Page and Threat Overview")
    wipe(s)
    K.picture(s, F.shot("01_landing_light.png"), 0.55, 1.8, 6.0, 3.75, border=True)
    K.picture(s, crop_shot("04_overview.png"), 6.8, 1.8, 6.0, 4.25, border=True)
    ftext(s, 0.55, 6.15, 12.2, 0.85, f"Left: landing page with live counters from the API (attack/benign windows, F1 and ROC-AUC of the shipped model). Right: threat overview ({cap}); the red banner is the real 'capture problem' message because Npcap is not installed.", size=13, color=K.FNAVY)
    notes[22] = "Real captures of the running console. The overview banner is the genuine capture error; live capture could not be run on this machine."
    s = S[22]
    set_title(s, "Output – Detections and Threat Detail")
    wipe(s)
    K.picture(s, crop_shot("05_detections.png"), 0.55, 1.8, 6.0, 4.25, border=True)
    K.picture(s, crop_shot("06_threat_detail.png"), 6.8, 1.8, 6.0, 4.25, border=True)
    ftext(s, 0.55, 6.15, 12.2, 0.85, f"Left: every scored window with prediction, confidence and severity ({cap}). Right: Threat Detail of one window with measured traffic, distributed-risk components and the severity factors behind the verdict.", size=13, color=K.FNAVY)
    notes[23] = "The detection log and the explanation drawer. Each verdict lists its factors."
    s = S[23]
    set_title(s, "Output – Mitigation Center and Model Performance")
    wipe(s)
    K.picture(s, crop_shot("09_mitigation.png"), 0.55, 1.8, 6.0, 4.25, border=True)
    K.picture(s, crop_shot("10_model.png"), 6.8, 1.8, 6.0, 4.25, border=True)
    ftext(s, 0.55, 6.15, 12.2, 0.85, f"Left: active quarantines with countdowns and automatic recovery ({cap}); application-level only. Right: Model page with the shipped metrics and the 'synthetic training data' warning.", size=13, color=K.FNAVY)
    notes[24] = "Quarantines count down and expire. The model page warns that the displayed metrics describe synthetic data."

    # ---- 25 conclusion and objectives
    s = S[24]
    set_title(s, "Conclusion & Objectives vs Outcomes")
    wipe(s)
    ftext(s, 0.55, 1.8, 12.2, 1.2, [
        (f"A working, tested detection and mitigation system ({F.PYTEST_PASSED} tests, {F.SMOKE_PASSED} smoke checks); retrained on real flows the forest reaches {p2(k['rr_acc'][0])}, but the shipped synthetic-trained model scores {p1(k['shipreal_acc'])} on them.", {"bullet": True, "space_after": 3}),
        (f"The severity layer cuts false alarms (5 s windows: {p1(k['w5_fpr_ml'])} to {p2(k['w5_fpr_act'])}); mitigation is an application-level quarantine; live capture is untested.", {"bullet": True}),
    ], size=13)
    rows = [["#", "Objective", "Outcome"],
            ["1", "Acquire dataset, extract flow features", "Partly: pipeline reads CICIDS2017; shipped model synthetic; real file evaluated here"],
            ["2", "Capture live traffic, same features", "Implemented (Scapy); not verified live; verified via simulator and unit tests"],
            ["3", "Train DDoS classifier", f"Achieved: {p2(k['rr_acc'][0])} on real flows after retraining; shipped model {p1(k['shipreal_acc'])}"],
            ["4", "Adaptive mitigation (rate limit / block)", "Partly: quarantine with auto recovery inside the app; rate limiting only advised"],
            ["5", "Dashboard of traffic, detections, mitigation", "Achieved: nine-page React console plus legacy dashboard"],
            ["6", "Evaluate accuracy, FPR, detection-to-mitigation time", f"Achieved offline (FPR {p2(k['rr_fpr'][0])} real; {F.WIN['window_5s']['actionable_high_or_critical']['fpr'] * 100:.2f}% pipeline at 5 s); decision {d2m['p50']:.0f} ms, no real attack timeline"]]
    ftable(s, 0.55, 2.95, [0.5, 3.9, 7.8], rows, size=11, row_h=0.52, align=["c", "l", "l"])
    notes[25] = "Be explicit about which objectives were met, partly met or not met."

    # ---- 26 limitations and future scope
    s = S[25]
    set_title(s, "Limitations & Future Scope")
    wipe(s)
    fbox(s, 0.55, 1.8, 6.0, 5.1, fill=K.FZEBRA)
    ftext(s, 0.75, 1.9, 5.6, 0.4, "Known limitations", size=17, color=K.FNAVY, bold=True)
    ftext(s, 0.75, 2.4, 5.6, 4.4, [
        ("Shipped model trained on synthetic data; landing page shows 99.71% without that caveat", {"bullet": True, "space_after": 6}),
        ("One real attack type (DDoS day); CICIDS2017 label flaws; random splits overlap in time", {"bullet": True, "space_after": 6}),
        ("Calibrated on 10 s windows; short windows raise false alarms before severity", {"bullet": True, "space_after": 6}),
        ("Quarantine never changes the OS firewall; no packet is dropped", {"bullet": True, "space_after": 6}),
        ("Live capture untested (no Npcap); saved n_jobs=-1 slows inference", {"bullet": True, "space_after": 6}),
        ("API has no authentication; interface setting not length-checked", {"bullet": True, "space_after": 6}),
        ("No real attack timeline, SDN deployment or multi-class detection", {"bullet": True}),
    ], size=14)
    fbox(s, 6.8, 1.8, 6.0, 5.1, fill=K.FHEAD)
    ftext(s, 7.0, 1.9, 5.6, 0.4, "Future scope", size=17, color=K.FNAVY, bold=True)
    ftext(s, 7.0, 2.4, 5.6, 4.4, [
        ("Retrain on real labelled captures and ship the real-data model", {"bullet": True, "space_after": 6}),
        ("Train on several window lengths; set n_jobs=1 for single-window inference", {"bullet": True, "space_after": 6}),
        ("Optional OS-firewall or SDN rule installation behind an explicit opt-in", {"bullet": True, "space_after": 6}),
        ("Test live capture with Npcap and a controlled traffic generator; measure real recovery time", {"bullet": True, "space_after": 6}),
        ("Multi-class attacks, online learning and a sidecar next to an SDN controller", {"bullet": True, "space_after": 6}),
        ("Authentication, input-length checks and use of the settings table", {"bullet": True, "space_after": 6}),
        ("Retest on newer datasets such as CIC-DDoS2023", {"bullet": True}),
    ], size=14)
    notes[26] = "Limitations first, then concrete next steps."

    # ---- 27 references
    s = S[26]
    set_title(s, "References")
    wipe(s)
    ids = sorted(R[x] for x in ("base", "s_wisne", "carpet", "rahman", "cicids", "engelen", "sommer", "mirkovic", "breiman", "sklearn", "zaman", "alduailij", "becerra", "scapy"))
    short = [f"[{n}] {clean_ref(REFS[n - 1])}" for n in ids]
    short = [t if len(t) < 340 else t[:337] + "..." for t in short]
    ftext(s, 0.55, 1.8, 6.0, 5.1, [(t, {"space_after": 5}) for t in short[:7]], size=11)
    ftext(s, 6.8, 1.8, 6.0, 5.1, [(t, {"space_after": 5}) for t in short[7:]] + [(f"The full numbered list of {len(REFS)} references is in the report.", {"italic": True})], size=11)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh_ in S[27].shapes:
        if sh_.name == "Text 2":
            K.replace_text(sh_, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "SentinelFlow")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
