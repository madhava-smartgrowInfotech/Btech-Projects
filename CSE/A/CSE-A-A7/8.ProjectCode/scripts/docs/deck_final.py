"""16.Final_PPT.pptx: 28 slides. Built from D:\\abstracts\\Templates\\Final_PPT.pptx (banner, rule, title and footer chrome inherited).

Every model number is read from scripts/docs/facts.py (experiments/*.json). All model results are on the seeded SYNTHETIC data.
"""

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
SYN = "synthetic hold-out"


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


def note_line(slide, text, y=6.5, size=12):
    ftext(slide, 0.55, y, 12.2, 0.5, text, size=size, color=K.FNAVY, italic=True)


CROPS = os.path.join(tempfile.gettempdir(), "a7_deck_crops")


def crop_shot(name, box=(250, 64, 1440, 900)):
    """Real screenshot with the sidebar and header cropped away so the content is larger on the slide."""
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


def build(out_path):
    prs = Presentation(TEMPLATE)
    S = list(prs.slides)
    assert len(S) == 28, len(S)
    cp = prs.core_properties
    cp.title = f"{F.TITLE} - Final Review"
    cp.author = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.comments = ""
    cp.last_modified_by = f"Batch {F.BATCH_NO}, Dept. of CSE, TKRCET"
    cp.subject = F.PRODUCT
    cp.keywords = "emergency triage, OCR, XGBoost, SHAP, calibration, clinical decision support"
    notes = {}
    bp = F.BASE_PAPER_RESULTS
    ab = F.ABL
    fused, vit, rep = ab["Fused (36)"], ab["Vitals only (8)"], ab["Report only (28)"]
    lr, xg = F.COMP["Logistic regression"], F.COMP["XGBoost (shipped config)"]
    s = F.SAFE
    t85 = F.thr_row(0.85)
    st = F.STRESS

    for sl in S:  # footers on every slide
        for sh in sl.shapes:
            if sh.top == TOP_FOOT and sh.has_text_frame and "Final Review" in sh.text_frame.text:
                K.replace_text(sh, f"Dept. of CSE  |  Batch {F.BATCH_NO}  |  Final Review")

    # ---- 1 title
    for sh in S[0].shapes:
        if sh.name == "Text 1":
            K.replace_text(sh, F.FULL_TITLE, 26)
        elif sh.name == "Text 2":
            K.replace_text(sh, f"Final Review  ·  {F.PRODUCT}")
        elif sh.name == "Text 3":
            K.replace_text(sh, f"Team Details : Batch {F.BATCH_NO}")
        elif sh.name == "Text 4":
            K.replace_text(sh, "\n".join(f"{r_}   {n_}" for n_, r_ in F.STUDENTS_UPPER))
        elif sh.name == "Text 5":
            K.replace_text(sh, f"Under the Esteemed Guidance of\n{F.GUIDE.upper()}\n{F.GUIDE_DESIGNATION}, Department of CSE")
        elif sh.name == "Text 6":
            K.replace_text(sh, f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING  ·  {F.COLLEGE_SHORT}  ·  Academic Year {F.YEAR}")
    notes[1] = "Introduce the team and ATHENA: an emergency triage assistant that reads a scanned report, fuses it with vitals, and explains the priority it assigns."

    # ---- 2 contents
    sl = S[1]
    set_title(sl, "Table of Contents")
    for sh in sl.shapes:
        if sh.name == "Text 4":
            K.replace_text(sh, "Abstract\nProblem Statement & Objectives\nBase Paper & Literature Survey\nResearch Gap & Proposed System\nArchitecture, Report Reading & Dataset\nFusion, Model & Data Design\nResults: Accuracy, Safety, Models, Ablation\nCalibration, Thresholds, Robustness & Reader\nExplainability, Performance & Testing\nComparison with Base Paper & Output Screens\nObjectives vs Outcomes, Limitations & Future Scope\nReferences", 17)
    notes[2] = "The agenda follows the report: problem, design, method, results, comparison, screens, conclusion."

    # ---- 3 abstract
    sl = S[2]
    set_title(sl, "Abstract")
    wipe(sl)
    ftext(sl, 0.55, 1.75, 12.2, 5.2, [
        ("Triage priority in the emergency department varies with the person on duty, and models built on structured fields cannot see what is written only in a scanned report.", {"bullet": True, "space_after": 7}),
        (f"ATHENA reads a PDF or scan (text layer or local OCR), fuses {F.N_FLAGS} report flags with {F.N_VITALS} vitals into {F.N_FEATURES} inputs, and a calibrated XGBoost assigns priority 1 to 5 with a confidence and per-patient SHAP reasons; the clinician accepts or changes it.", {"bullet": True, "space_after": 7}),
        (f"All model numbers are on seeded SYNTHETIC data: accuracy {F.pct(F.ACC)}, within one level {F.pct(F.W1)}, macro F1 {F.f3(F.MF1)}; P1 recall only {F.pct(F.REC[0])}.", {"bullet": True, "space_after": 7}),
        (f"Fusing report and vitals gives {F.pct(fused['accuracy'], 2)} against {F.pct(vit['accuracy'], 2)} for vitals alone; a plain logistic regression scores {F.pct(lr['accuracy'], 2)}, and no model can pass about {F.pct(F.CEILING, 2)} because of label noise.", {"bullet": True, "space_after": 7}),
        (f"The report reader is exact on 12 generated samples but reaches {F.pct(st['recall'])} recall on 40 hand-written fragments. A PDF-to-priority request takes about {F.lat('flow_pdf_then_triage'):.0f} ms; an OCR scan about {F.lat('flow_scan_then_triage') / 1000:.1f} s.", {"bullet": True}),
    ], size=18)
    notes[3] = "State at once that the data are synthetic; the accuracy measures recovery of a known rule, not agreement with clinicians."

    # ---- 4 problem statement and objectives
    sl = S[3]
    set_title(sl, "Problem Statement & Objectives")
    wipe(sl)
    fbox(sl, 0.55, 1.8, 5.9, 5.0)
    ftext(sl, 0.8, 1.9, 5.4, 0.4, "Problem statement", size=17, color=K.FNAVY, bold=True)
    ftext(sl, 0.8, 2.4, 5.4, 4.3, [(t, {"bullet": True, "space_after": 8}) for t in lit.PROBLEM_STATEMENT], size=15)
    fbox(sl, 6.7, 1.8, 6.1, 5.0, fill=K.FZEBRA)
    ftext(sl, 6.95, 1.9, 5.6, 0.4, "Objectives (batch document)", size=17, color=K.FNAVY, bold=True)
    ftext(sl, 6.95, 2.4, 5.7, 4.3, [(f"{i}.  {o}", {"space_after": 7}) for i, o in enumerate(lit.OBJECTIVES, 1)], size=14)
    notes[4] = "Four problem points and the need, then the six objectives as written in the batch document. Their real status is on slide 25."

    # ---- 5 base paper
    sl = S[4]
    set_title(sl, "Base Paper")
    wipe(sl)
    ftext(sl, 0.55, 1.75, 12.2, 0.8, F.BASE_PAPER, size=12, color=K.FNAVY)
    rows = [["Aspect", "Base paper (IEEE Access 2026)"],
            ["Task", f"Disease classification into ICD-10 codes ({bp['classes']} classes) from interview data of internal medicine and pediatrics; incomplete records, no imputation"],
            ["Data", f"{bp['cases']:,} real clinical cases ({bp['internal']} internal medicine, {bp['pediatrics']:,} pediatrics), {bp['parameters']} clinical parameters; 120 external cases"],
            ["Method", f"{bp['algorithms']} classifiers tuned with Optuna (TPE, {bp['trials']} trials each); two-stage TOP-1 / TOP-3 ranking; 0.85 confidence threshold; SHAP + LIME"],
            ["Reported", f"TOP-1: {bp['best_int'][0]} {p1(bp['best_int'][1])} (internal), {bp['best_ped'][0]} {p1(bp['best_ped'][1])} (pediatrics); TOP-3 up to {p1(bp['top3_best_int'])} / {p1(bp['top3_best_ped'])}; external TOP-1 {p1(bp['ext_top1_int'])} / {p1(bp['ext_top1_ped'])}"],
            ["Not covered (our reading)", "Input is typed symptom indicators: no scanned reports, no vitals fusion, no five-level triage target, no processing time"]]
    ftable(sl, 0.55, 2.6, [2.3, 9.9], rows, size=13, row_h=0.62)
    notes[5] = "Mlodawski et al., IEEE Access 2026. ATHENA borrows its probability-ranking and threshold ideas, SHAP, and the rule that an unreported symptom counts as absent; the task and data differ."

    # ---- 6 literature survey
    sl = S[5]
    set_title(sl, "Literature Survey")
    wipe(sl)
    pick = [0, 1, 2, 3, 4, 5, 7]
    rows = [["Work", "Year", "Approach", "Finding / limitation"]] + [lit.LIT_TABLE[i] for i in pick]
    ftable(sl, 0.55, 1.75, [2.9, 0.65, 4.2, 4.45], rows, size=11, row_h=0.55, align=["l", "c", "l", "l"])
    note_line(sl, f"Also in the batch survey: Anatolian Curr. Med. J. [{R['s_acmj']}] (ESI vs Manchester process study), Xie et al. [{R['xie']}] (MIMIC-IV-ED benchmark), a Nepal triage-knowledge study [{R['s_nepal']}]; an obstetric-triage entry [{R['s_obst']}] could not be verified and a veterinary chapter [{R['s_horse']}] is out of domain.", y=6.45, size=11)
    notes[6] = "Eight works shown; every figure is from the abstract or the paper itself. Two survey entries are unverified or out of domain and are not used as evidence."

    # ---- 7 research gap
    sl = S[6]
    set_title(sl, "Research Gap")
    wipe(sl)
    ftext(sl, 0.55, 1.9, 12.2, 4.9, [(g, {"bullet": True, "space_after": 14}) for g in lit.GAPS], size=19)
    notes[7] = "Five gaps. ATHENA addresses the first, the second (target is the five-level priority), the third, the fourth and the fifth - on synthetic data."

    # ---- 8 proposed system
    sl = S[7]
    set_title(sl, "Proposed System")
    wipe(sl)
    ftext(sl, 0.55, 1.7, 12.2, 0.4, "Report intake", size=15, color=K.FNAVY, bold=True)
    K.flow(sl, 0.55, 2.1, 12.2, 0.8, [("PDF / scan", K.FNAVY), ("Text layer or OCR", K.FBLUE), ("Lexicon + negation", K.GREEN), ("6 lab ranges", K.ORANGE), ("28 flags + pages", K.PURPLE)], size=13, gap=0.3, font=FONT)
    ftext(sl, 0.55, 3.1, 12.2, 0.4, "Triage", size=15, color=K.FNAVY, bold=True)
    K.flow(sl, 0.55, 3.5, 12.2, 0.8, [("8 vitals", K.FNAVY), ("Fused record: 36", K.FBLUE), ("XGBoost + isotonic", K.GREEN), ("Priority 1-5, risk", K.ORANGE), ("SHAP reasons", K.PURPLE), ("Accept / change", K.FNAVY)], size=13, gap=0.3, font=FONT)
    ftext(sl, 0.55, 4.65, 12.2, 2.3, [
        ("Decision support only: the clinician accepts or changes every priority, and a change needs a written reason that is stored.", {"bullet": True, "space_after": 7}),
        ("Priority 1 Critical to 5 Non-urgent; risk High for P1-2, Moderate for P3, Low for P4-5; the queue is ordered by priority, then arrival.", {"bullet": True, "space_after": 7}),
        ("Runs offline on a laptop: local OCR, no API key, no GPU. Triage-summary PDF per patient.", {"bullet": True}),
    ], size=16)
    notes[8] = "Two chains: report intake and triage. The clinician loop closes it."

    # ---- 9 architecture
    sl = S[8]
    set_title(sl, "System Architecture")
    wipe(sl)
    K.picture(sl, F.diag("01_system_architecture.png"), 0.55, 1.8, 7.2, 5.1)
    ftext(sl, 8.0, 1.95, 4.8, 4.9, [
        (f"Web app: React 19 + Vite on port {F.WEB_PORT}, six screens", {"bullet": True, "space_after": 8}),
        (f"API: FastAPI on port {F.API_PORT}, 13 endpoints, JWT sign-in (clinician, admin)", {"bullet": True, "space_after": 8}),
        ("Services: report reader, fused record, triage model + SHAP, summary PDF", {"bullet": True, "space_after": 8}),
        ("Storage: SQLite with users, patients, overrides; model and sample files on disk", {"bullet": True, "space_after": 8}),
        ("One command, run.bat, starts both servers", {"bullet": True}),
    ], size=15)
    notes[9] = "Browser, API, services, SQLite. The model is a joblib file loaded once; the SHAP explainer is warmed at start-up."

    # ---- 10 report reading
    sl = S[9]
    set_title(sl, "Report Reading")
    wipe(sl)
    K.picture(sl, F.diag("11_flowchart_report_reading.png"), 0.55, 1.8, 6.0, 5.1)
    ftext(sl, 6.8, 1.9, 6.0, 5.0, [
        ("PDF: text layer by page; a page with under 20 characters falls back to OCR on its image.", {"bullet": True, "space_after": 7}),
        ("Images: local RapidOCR (PaddleOCR-family models on ONNX Runtime), no network.", {"bullet": True, "space_after": 7}),
        ("22 lexicon flags (11 symptoms, 5 findings, 6 history); negation within 45 characters drops a flag.", {"bullet": True, "space_after": 7}),
        ("Six labs with units and reference ranges set a flag when abnormal; every item keeps its page.", {"bullet": True, "space_after": 7}),
        (f"Generated samples: precision {F.pct(F.READ['precision'], 0)}, recall {F.pct(F.READ['recall'], 0)} (12 of 12 exact). Hand-written stress set: precision {F.pct(st['precision'])}, recall {F.pct(st['recall'])}.", {"bullet": True}),
    ], size=14)
    notes[10] = "The reader is rule-based, not a medical language model. The generated samples were written with the lexicon in view, so 100% overstates it; 84% is the honest figure."

    # ---- 11 dataset
    sl = S[10]
    set_title(sl, "Dataset (Synthetic) & Split")
    wipe(sl)
    ftile(sl, 0.55, 1.8, 2.95, 1.0, f"{F.ROWS:,}", "seeded synthetic patients (seed 7307)", K.FBLUE, 26)
    ftile(sl, 0.55, 2.95, 2.95, 1.0, "7", "clinical archetypes (cardiac, trauma ...)", K.GREEN, 26)
    ftile(sl, 0.55, 4.1, 2.95, 1.0, f"{F.N_TRAIN:,} / {F.N_CAL} / {F.N_TEST:,}", "fit / calibration / test", K.ORANGE, 22)
    K.picture(sl, F.fig("f11_priority_distribution.png"), 3.75, 1.75, 9.05, 3.25)
    ftext(sl, 0.55, 5.2, 12.2, 1.8, [
        (f"Vitals and report flags are drawn per archetype; a hand-written severity score plus Gaussian noise (sd 0.4) is cut into priorities. P1 is only {F.pct(F.PRIO_SHARE[0])} of rows.", {"bullet": True, "space_after": 5}),
        (f"Noise ceiling: even knowing the clean score reproduces the label for {F.pct(F.CEILING, 2)} of rows, so exact accuracy cannot exceed about that.", {"bullet": True, "space_after": 5}),
        ("No real patient data was used; the Kaggle triage dataset script was never run. Real triage records would give different numbers.", {"bullet": True}),
    ], size=14)
    notes[11] = "The label plays the clinician's recorded outcome. That is why every result slide says synthetic."

    # ---- 12 fusion and model
    sl = S[11]
    set_title(sl, "Fusion, Model & Calibration")
    wipe(sl)
    K.picture(sl, F.diag("12_model_architecture.png"), 0.55, 1.8, 7.0, 4.9)
    ftext(sl, 7.8, 1.9, 5.0, 5.0, [
        (f"Fused record: {F.N_VITALS} vitals + {F.N_FLAGS} report flags = {F.N_FEATURES} inputs; an unreported flag counts as 0, as in the base paper.", {"bullet": True, "space_after": 7}),
        ("XGBoost multi-class: 220 trees, depth 4, learning rate 0.1.", {"bullet": True, "space_after": 7}),
        (f"Isotonic calibration on a separate {F.N_CAL}-row split so confidence is a probability.", {"bullet": True, "space_after": 7}),
        ("Priority = argmax of the calibrated probabilities; risk from the priority.", {"bullet": True, "space_after": 7}),
        (f"Training takes {F.TRAIN_SEC:.2f} s; model inference about {F.MODEL_SEC * 1000:.3f} ms per patient.", {"bullet": True}),
    ], size=14)
    notes[12] = "XGBoost was kept for the SHAP TreeExplainer and calibration; on this synthetic data a logistic regression actually scores higher (slide 16)."

    # ---- 13 data design and implementation
    sl = S[12]
    set_title(sl, "Data Design & Implementation")
    wipe(sl)
    K.picture(sl, F.diag("09_er_diagram.png"), 0.55, 1.8, 6.0, 4.6)
    for i, (v, l, c) in enumerate([("13", "API endpoints", K.FBLUE), (f"{F.PYTEST_TOTAL} + {F.SMOKE_TOTAL}", "pytest tests + smoke checks", K.GREEN), ("6", "screens, light and dark", K.ORANGE), ("~4,100", "lines of code and tests", K.PURPLE)]):
        ftile(sl, 6.8 + (i % 2) * 3.05, 1.8 + (i // 2) * 1.2, 2.9, 1.05, v, l, c, 24)
    ftext(sl, 6.8, 4.35, 6.0, 2.6, [
        ("Tables: users, patients (vitals, report, fused record, SHAP, timings as JSON) and overrides (old, new, action, reason).", {"bullet": True, "space_after": 5}),
        ("bcrypt hashes, HS256 JWT valid 12 h, pydantic range checks, 15 MB upload limit.", {"bullet": True, "space_after": 5}),
        ("Gaps: default JWT secret, no HTTPS, no rate limit.", {"bullet": True}),
    ], size=13)
    note_line(sl, "A fresh database is seeded with 12 labelled sample cases so the queue and performance pages are never empty.", y=6.5, size=12)
    notes[13] = "Three tables. Security is demo-grade and the slide says so."

    # ---- 14 results headline
    sl = S[13]
    set_title(sl, "Results – Shipped Model (Synthetic Hold-out)")
    wipe(sl)
    for i, (v, l, c) in enumerate([(F.pct(F.ACC), "exact priority", K.FBLUE), (F.pct(F.W1), "within one level", K.GREEN), (F.f3(F.MF1), "macro F1", K.ORANGE), (F.f3(F.QWK), "quadratic weighted kappa", K.PURPLE)]):
        ftile(sl, 0.55 + i * 3.1, 1.75, 2.9, 1.0, v, l, c, 26)
    K.picture(sl, F.fig("f01_confusion_matrix.png"), 0.55, 2.9, 6.2, 3.55)
    ftext(sl, 7.0, 2.95, 5.8, 3.6, [
        (f"Recall P1 to P5: {' / '.join(f'{r * 100:.0f}' for r in F.REC)} %. The sickest class is found least often.", {"bullet": True, "space_after": 7}),
        (f"Most errors are one level away: {F.pct(F.W1)} within one, top-2 accuracy {F.pct(F.TOP2)}.", {"bullet": True, "space_after": 7}),
        (f"{F.CM[0][1]} of {F.SUP[0]} recorded P1 cases land in P2; {F.CM[1][2]} of {F.SUP[1]} P2 cases land in P3.", {"bullet": True, "space_after": 7}),
        (f"Five other splits of the same recipe give {F.pct(F.SEEDS['accuracy_mean'])} (sd {F.pct(F.SEEDS['accuracy_std'])}); the shipped seed is a below-average split.", {"bullet": True}),
    ], size=14)
    note_line(sl, f"{F.N_TEST:,} held-out synthetic cases; rows are the recorded priority. Accuracy measures recovery of a known rule, not agreement with clinicians.", y=6.5, size=12)
    notes[14] = "Read the confusion matrix by row: recorded priority. P1 and P2 are the ones confused with their neighbours."

    # ---- 15 triage direction and safety
    sl = S[14]
    set_title(sl, "Safety View – Under- and Over-triage")
    wipe(sl)
    K.picture(sl, F.fig("f13_triage_direction.png"), 0.55, 1.75, 6.3, 4.6)
    rows = [["Measure (1,200 synthetic cases)", "Value"],
            ["Under-triage (model less urgent)", F.pct(s["under_triage_any"], 2)],
            ["Over-triage (model more urgent)", F.pct(s["over_triage_any"], 2)],
            ["Two or more levels under", F.pct(s["under_triage_2plus"], 2)],
            [f"Recorded P1 placed at P3 or lower urgency", f"{s['p1_predicted_p3_or_lower_urgency']} of {s['p1_support']}"],
            ["High-risk (P1-P2) recall / precision, argmax", f"{p1(s['high_risk_recall'])} / {p1(s['high_risk_precision'])}"],
            ["Flag when P(1)+P(2) ≥ 0.4 (not built)", f"{p1(s['high_risk_recall_at_pr_0_4'])} / {p1(s['high_risk_precision_at_pr_0_4'])}"]]
    ftable(sl, 7.0, 1.8, [3.9, 1.9], rows, size=12, row_h=0.52, align=["l", "c"])
    ftext(sl, 7.0, 5.55, 5.8, 1.3, "The model errs toward the less urgent side more than the more urgent side, and misses a third of high-risk cases at argmax. A clinician must review every priority.", size=13, color=K.FNAVY, italic=True)
    notes[15] = "The honest safety message. A lower flag threshold for high risk would raise recall to 84% at 82% precision, but it is not implemented in the product."

    # ---- 16 model comparison and ablation
    sl = S[15]
    set_title(sl, "Model Comparison & Modality Ablation")
    wipe(sl)
    K.picture(sl, F.fig("f03_model_comparison.png"), 0.55, 1.75, 6.1, 3.5)
    K.picture(sl, F.fig("f04_modality_ablation.png"), 6.75, 1.75, 6.1, 3.5)
    ftext(sl, 0.55, 5.4, 12.2, 1.6, [
        (f"Eight models, same split: logistic regression {F.pct(lr['accuracy'], 2)} beats the shipped XGBoost configuration ({F.pct(xg['accuracy'], 2)}) because the synthetic labels come from an additive score. XGBoost was kept for SHAP and calibration.", {"bullet": True, "space_after": 5}),
        (f"Fusion: fused {F.pct(fused['accuracy'], 2)}, report only {F.pct(rep['accuracy'], 2)}, vitals only {F.pct(vit['accuracy'], 2)} - the single-modality gap named in the survey, measured on synthetic data.", {"bullet": True, "space_after": 5}),
        (f"5-fold CV accuracy: logistic {F.pct(F.CV5['Logistic regression']['mean'])}, random forest {F.pct(F.CV5['Random forest']['mean'])}, XGBoost {F.pct(F.CV5['XGBoost (shipped config)']['mean'])}.", {"bullet": True}),
    ], size=13)
    notes[16] = "A linear model wins. We say so: the choice of XGBoost is about explanation and calibration, not about winning on this data."

    # ---- 17 calibration and threshold
    sl = S[16]
    set_title(sl, "Calibration & Confidence Threshold")
    wipe(sl)
    K.picture(sl, F.fig("f05_calibration_reliability.png"), 0.55, 1.75, 6.1, 3.6)
    K.picture(sl, F.fig("f06_threshold_coverage.png"), 6.75, 1.75, 6.1, 3.6)
    ftext(sl, 0.55, 5.5, 12.2, 1.5, [
        (f"Isotonic calibration helps modestly: ECE {F.f3(F.CAL['ece_uncalibrated'])} to {F.f3(F.CAL['ece_isotonic'])}; the 0.8-0.9 confidence bin is over-confident (66% observed).", {"bullet": True, "space_after": 5}),
        (f"Confidence threshold, as in the base paper's 0.85 rule: keeping only predictions at 0.85 or more covers {F.pct(t85['coverage'])} of cases at {F.pct(t85['accuracy'])} accuracy (all cases: {F.pct(F.ACC)}).", {"bullet": True, "space_after": 5}),
        ("The threshold is an analysis, not a gate in the product.", {"bullet": True}),
    ], size=13)
    notes[17] = "Parameter analysis: the confidence threshold trades coverage for accuracy. Analogous to the base paper's 0.85 threshold, on a different task and data."

    # ---- 18 robustness and reader
    sl = S[17]
    set_title(sl, "Robustness & Report-Reader Evaluation")
    wipe(sl)
    K.picture(sl, F.fig("f07_robustness_dropped_flags.png"), 0.55, 1.75, 6.1, 3.5)
    K.picture(sl, F.fig("f09_reader_stress_by_category.png"), 6.75, 1.75, 6.1, 3.5)
    r1, r2, r3 = F.rob_row(0.1), F.rob_row(0.2), F.rob_row(1.0)
    ftext(sl, 0.55, 5.4, 12.2, 1.6, [
        (f"Drop each positive report flag at random: accuracy {F.pct(F.ACC)} -> {F.pct(r1['accuracy'])} (10%) -> {F.pct(r2['accuracy'])} (20%); with no report at all {F.pct(r3['accuracy'])}. A missed finding is costly.", {"bullet": True, "space_after": 5}),
        (f"Reader on 40 hand-written fragments: {F.pct(st['precision'])} precision, {F.pct(st['recall'])} recall, {st['cases_read_exactly']} of {st['cases']} read exactly; paraphrases are the weak spot (recall {st['by_category']['paraphrase']['recall']:.2f}).", {"bullet": True, "space_after": 5}),
        ("Found defects: \"afebrile\" read as fever, \"chest pain: absent\" flagged, \"denies X but reports Y\" negates Y, split OCR words missed.", {"bullet": True}),
    ], size=13)
    notes[18] = "Robustness to incomplete input is the base paper's theme. The reader defects were found by our own stress set and left unfixed in the product; they are documented."

    # ---- 19 explainability and clinician loop
    sl = S[18]
    set_title(sl, "Explainability & Clinician Loop")
    wipe(sl)
    K.picture(sl, F.fig("f08_shap_global.png"), 0.55, 1.75, 6.1, 3.95)
    K.picture(sl, F.diag("07_sequence_flow.png"), 6.75, 1.7, 6.1, 4.05)
    ftext(sl, 0.55, 5.85, 12.2, 1.15, [
        ("Per patient: SHAP TreeExplainer lists the strongest drivers for the chosen priority (top 8, absent flags with tiny effect hidden). Globally SpO2, arrival mode, shortness of breath, blood pressure and ST elevation lead - matching the severity rule used to make the labels, which checks the explainer, not clinical validity.", {"bullet": True, "space_after": 3}),
        ("A change of priority needs a reason; accept or change is stored with who, when, old and new priority, and the queue reorders.", {"bullet": True}),
    ], size=12)
    notes[19] = "Explanation beside the decision, and the override loop that makes it decision support."

    # ---- 20 performance and testing
    sl = S[19]
    set_title(sl, "Performance & Testing")
    wipe(sl)
    for i, (v, l, c) in enumerate([(f"{F.lat('flow_pdf_then_triage'):.0f} ms", "PDF extract + triage (HTTP median)", K.FBLUE), (f"{F.lat('flow_scan_then_triage') / 1000:.2f} s", "scan: OCR + triage", K.GREEN),
                                   (f"{F.lat('create_patient'):.0f} ms", "triage + SHAP request", K.ORANGE), (f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest pass, {F.PYTEST_XFAIL} expected failure", K.PURPLE)]):
        ftile(sl, 0.55 + i * 3.1, 1.75, 2.9, 1.0, v, l, c, 24)
    K.picture(sl, F.fig("f10_latency.png"), 0.55, 2.9, 5.7, 3.3)
    rows = [["Check", "Result"],
            ["pytest: reader 20, triage 11, API 16", f"{F.PYTEST_PASSED} pass, {F.PYTEST_XFAIL} documented failure, {F.PYTEST_FAILED} fail ({F.PYTEST_SECONDS} s)"],
            ["Smoke test against running API", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks pass"],
            ["End to end, 12 samples (reader + model)", f"mean {F.E2E['mean']:.2f} s, median {F.E2E['median']:.3f} s, max {F.E2E['max']:.2f} s"],
            ["Not tested", "concurrency, real scans, fresh install, security audit, user study"]]
    ftable(sl, 6.45, 2.9, [2.6, 3.75], rows, size=11, row_h=0.62)
    note_line(sl, f"Measured on {F.MACHINE}, 127.0.0.1, medians of 10-50 calls.", y=6.45, size=11)
    notes[20] = "Model time is negligible; OCR dominates for image scans, bcrypt dominates login. Nothing here is load testing."

    # ---- 21 comparison with the base paper
    sl = S[20]
    set_title(sl, "Comparison with Base Paper")
    wipe(sl)
    rows = [["Aspect", "Base paper [1]", "ATHENA"],
            ["Task", f"ICD-10 diagnosis, {bp['classes']} classes", "Triage priority, 5 levels"],
            ["Data", f"{bp['cases']:,} real cases", f"{F.ROWS:,} synthetic rows"],
            ["Input", "Typed symptom indicators", "Scanned report + 8 vitals"],
            ["Algorithms", f"{bp['algorithms']} compared", "8 compared; XGBoost shipped"],
            ["Ranking", f"TOP-3 up to {p1(bp['top3_best_int'])} / {p1(bp['top3_best_ped'])}", f"Top-2 {F.pct(F.TOP2)}"],
            ["Top-1 / exact", f"{p1(bp['best_int'][1])} / {p1(bp['best_ped'][1])}", F.pct(F.ACC)],
            ["Confidence rule", "0.85 threshold", f"0.85: {F.pct(t85['coverage'])} coverage, {F.pct(t85['accuracy'])}"],
            ["Explanation", "SHAP + LIME, offline", "Per-patient SHAP beside the decision"]]
    ftable(sl, 0.55, 1.75, [1.6, 2.7, 2.9], rows, size=11, row_h=0.5)
    K.picture(sl, F.fig("f12_base_paper_context.png"), 8.0, 1.75, 4.85, 3.1)
    ftext(sl, 8.0, 4.95, 4.85, 2.0, [
        ("Different task, data and metrics: the numbers are indicative only and ATHENA is not claimed to beat the paper.", {"bullet": True, "space_after": 5}),
        ("Shared ideas: probability ranking, confidence threshold, SHAP, absent = 0, comparison of several algorithms.", {"bullet": True}),
    ], size=12)
    notes[21] = "Plainly: they diagnose 87 ICD-10 classes on 1,655 real cases; we assign five priorities on synthetic data. We borrow ideas, not a score to beat."

    # ---- 22-24 output screens
    sl = S[21]
    set_title(sl, "Output – Triage Queue and New Patient")
    wipe(sl)
    K.picture(sl, crop_shot("04_queue.png"), 0.55, 1.8, 6.0, 4.25, border=True)
    K.picture(sl, crop_shot("06_new_patient_filled.png"), 6.8, 1.8, 6.0, 4.25, border=True)
    ftext(sl, 0.55, 6.15, 12.2, 0.85, "Left: the queue of 12 labelled sample cases, ordered by priority then arrival, with main drivers, risk and confidence. Right: sample report 01 read in 0.234 s (2 pages); symptoms, findings, history and labs appear with their page numbers and the vitals are filled in.", size=13, color=K.FNAVY)
    notes[22] = "Real captures of the running app with data in it."
    sl = S[22]
    set_title(sl, "Output – Result and Why This Priority")
    wipe(sl)
    K.picture(sl, crop_shot("07_result.png"), 0.55, 1.8, 6.0, 4.25, border=True)
    K.picture(sl, crop_shot("08_result_why.png"), 6.8, 1.8, 6.0, 4.25, border=True)
    ftext(sl, 0.55, 6.15, 12.2, 0.85, "Left: Patient 013 assigned priority 1 Critical, high risk; the fused record lists report findings and vitals. Right: the SHAP list - ST elevation, raised troponin and lactate, heart rate - strongest first. The 100% is the calibrated confidence for this textbook STEMI sample report.", size=13, color=K.FNAVY)
    notes[23] = "The explanation sits next to the decision. Confidence near 100% on a textbook STEMI case does not mean the model is that sure in general (mean confidence is 0.73)."
    sl = S[23]
    set_title(sl, "Output – Clinician Decision and Model Performance")
    wipe(sl)
    K.picture(sl, crop_shot("10_result_decision.png"), 0.55, 1.8, 6.0, 4.25, border=True)
    K.picture(sl, crop_shot("12_performance.png"), 6.8, 1.8, 6.0, 4.25, border=True)
    ftext(sl, 0.55, 6.15, 12.2, 0.85, f"Left: the clinician changed priority 1 to 2; the model's suggestion is kept and the case is marked reviewed. Right: the performance page - accuracy {F.pct(F.ACC)}, within one level {F.pct(F.W1)}, macro F1 {F.f3(F.MF1)}, with a banner saying the data are synthetic.", size=13, color=K.FNAVY)
    notes[24] = "The override loop and the performance page, which carries the synthetic-data warning in the product itself."

    # ---- 25 objectives and conclusion
    sl = S[24]
    set_title(sl, "Conclusion & Objectives vs Outcomes")
    wipe(sl)
    ftext(sl, 0.55, 1.75, 12.2, 1.2, [
        (f"A working decision-support pipeline: report reading, fusion, calibrated priority, SHAP reasons and a stored clinician decision; {F.PYTEST_PASSED} tests and {F.SMOKE_PASSED} smoke checks pass.", {"bullet": True, "space_after": 4}),
        (f"Key finding: reports add {(fused['accuracy'] - vit['accuracy']) * 100:.1f} points over vitals alone, yet P1 recall is {F.pct(F.REC[0])} and a linear baseline wins on synthetic data.", {"bullet": True}),
    ], size=14)
    rows = [["#", "Objective", "Status and evidence"],
            ["1", "OCR stage for scanned reports", "Met: PDF text layer + local RapidOCR; 4 generated scans read exactly"],
            ["2", "Medical language model for extraction", f"Partly: rule-based lexicon (no BioBERT); recall {F.pct(st['recall'])} on stress set"],
            ["3", "Fused text + vitals representation", f"Met: {F.N_FEATURES} inputs; fusion beats either part alone"],
            ["4", "Model assigns risk level and priority", "Met on synthetic labels only"],
            ["5", "Explainability layer", "Met: per-patient SHAP; no LIME"],
            ["6", "Accuracy vs clinician priority; time per patient", f"Partly: accuracy vs synthetic label; time measured ({F.lat('flow_pdf_then_triage'):.0f} ms PDF, {F.lat('flow_scan_then_triage') / 1000:.1f} s scan)"]]
    ftable(sl, 0.55, 3.05, [0.5, 4.2, 7.5], rows, size=12, row_h=0.5, align=["c", "l", "l"])
    notes[25] = "Be explicit: two objectives are only partly met. BioBERT, RAG, multi-agent orchestration, MongoDB and the six disease models were not built."

    # ---- 26 limitations and future scope
    sl = S[25]
    set_title(sl, "Limitations & Future Scope")
    wipe(sl)
    fbox(sl, 0.55, 1.8, 6.0, 5.1, fill=K.FZEBRA)
    ftext(sl, 0.75, 1.9, 5.6, 0.4, "Known limitations", size=17, color=K.FNAVY, bold=True)
    ftext(sl, 0.75, 2.4, 5.6, 4.4, [
        ("Trained and tested on synthetic data; no clinician agreement measured", {"bullet": True, "space_after": 7}),
        (f"P1 recall {F.pct(F.REC[0])}; high-risk recall {F.pct(s['high_risk_recall'])}; under-triage {F.pct(s['under_triage_any'])}", {"bullet": True, "space_after": 7}),
        ("Rule-based reader; negation and OCR defects; only 4 generated scans tried", {"bullet": True, "space_after": 7}),
        ("Linear baseline beats XGBoost here; calibration only modest", {"bullet": True, "space_after": 7}),
        ("No BioBERT, RAG, multi-agent, LIME, MongoDB or disease models", {"bullet": True, "space_after": 7}),
        ("Demo-grade security; no user study", {"bullet": True}),
    ], size=15)
    fbox(sl, 6.8, 1.8, 6.0, 5.1, fill=K.FHEAD)
    ftext(sl, 7.0, 1.9, 5.6, 0.4, "Future scope", size=17, color=K.FNAVY, bold=True)
    ftext(sl, 7.0, 2.4, 5.6, 4.4, [
        ("Retrain and validate on real triage records (credentialed access needed)", {"bullet": True, "space_after": 7}),
        ("Medical language model for extraction; fix negation scope and OCR splits", {"bullet": True, "space_after": 7}),
        ("Flag high risk when P(1)+P(2) is 0.4 or more; better calibration", {"bullet": True, "space_after": 7}),
        ("Live vitals feed, multi-agent / RAG ideas, TOP-k style ranking", {"bullet": True, "space_after": 7}),
        ("Prospective user study with triage nurses", {"bullet": True, "space_after": 7}),
        ("Harden security: secrets, HTTPS, audit log, rate limits", {"bullet": True}),
    ], size=15)
    notes[26] = "Limitations first, then concrete next steps tied to measured weak points."

    # ---- 27 references
    sl = S[26]
    set_title(sl, "References")
    wipe(sl)
    keys = ["base", "cheng", "fernandes", "hinson", "hong", "levin", "raita", "xie", "esi", "xgboost", "shap", "treeshap", "zadrozny", "s_acmj"]
    short = [f"[{R[k]}] {clean_ref(REFS[R[k] - 1])}" for k in keys]
    short = [t if len(t) < 380 else t[:377] + "..." for t in short]
    ftext(sl, 0.55, 1.75, 6.0, 5.2, [(t, {"space_after": 5}) for t in short[:7]], size=11)
    ftext(sl, 6.8, 1.75, 6.0, 5.2, [(t, {"space_after": 5}) for t in short[7:]], size=11)
    notes[27] = "Selected references; the complete numbered list is in the report."

    # ---- 28 thank you
    for sh in S[27].shapes:
        if sh.name == "Text 2":
            K.replace_text(sh, "Questions & Suggestions")
    notes[28] = "Invite questions."

    for i, sld in enumerate(S, 1):
        K.set_notes(sld, notes.get(i, ""))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, "ATHENA")
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "16.Final_PPT.pptx")))
