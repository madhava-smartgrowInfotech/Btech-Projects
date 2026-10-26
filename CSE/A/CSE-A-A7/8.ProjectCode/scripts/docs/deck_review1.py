"""7.Review_1_PPT.pptx: 16 slides, problem identification and research. Built from D:\\abstracts\\Templates\\Review_1_PPT.pptx."""

import os

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_1_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


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
    cp.keywords = "emergency triage, clinical decision support, OCR, XGBoost, SHAP, explainable AI"
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
            K.replace_text(sh, f"Guide: {F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def build(out_path):
    from .lit import GAPS, LIMITATIONS_OF_EXISTING, LIT_TABLE, OBJECTIVES, PROBLEM_STATEMENT
    from .refs import CITE as R
    from .refs import REFS

    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 1")
    S = list(prs.slides)
    assert len(S) == 16, len(S)
    notes = {}
    C = [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE]
    bp = F.BASE_PAPER_RESULTS

    # ---- 1 title
    title_slide(S[0], F.SUBTITLE, "REVIEW 1  ·  PROBLEM IDENTIFICATION AND RESEARCH")
    notes[1] = ("Introduce the team and the title. One sentence: ATHENA reads a scanned clinical report together with the patient's vitals, assigns an emergency triage priority "
                "from 1 to 5 with a calibrated confidence, and shows which findings drove the decision so that the clinician can accept or change it.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Abstract and overview"), ("02", "Base paper"), ("03", "Literature survey and evidence"), ("04", "Existing system and limitations"),
               ("05", "Research gap"), ("06", "Problem statement and objectives"), ("07", "Proposed approach and architecture"),
               ("08", "Expected outcomes"), ("09", "References")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda. This review is about why the problem matters and what is missing in current work; design details and measured results come in the later reviews."

    # ---- 3 abstract
    s = S[2]
    set_title(s, "Abstract: read the report, fuse the vitals, explain the priority")
    wipe(s)
    W, H = 3.85, 5.0
    for i, (t, body, col, gl) in enumerate([
        ("The problem", "An emergency department must decide within minutes who is seen first. Manual triage varies with the person on duty, and models built only on typed fields cannot see what is written in a scanned report. A prediction without reasons is not accepted at the bedside.", K.ORANGE, "!"),
        ("Our idea", "Read the scanned report (PDF text layer or local OCR), turn symptoms, findings, history and lab values into flags, fuse them with eight vitals, and let a calibrated gradient-boosted model assign priority 1 to 5. SHAP shows the strongest drivers for each patient.", K.BLUE, "i"),
        ("The deliverable", "ATHENA: a FastAPI service and a React console. The clinician uploads a report, enters vitals, sees priority, confidence and reasons, accepts or changes the priority with a reason, and watches a live queue. It supports the clinician and never replaces one.", K.GREEN, "✓"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, H, t, body, col, gl, body_size=18)
    notes[3] = "Three points: why triage is hard, the idea of fusing report and vitals with an explanation, and what is delivered. Everything runs locally without a GPU or an API key."

    # ---- 4 base paper
    s = S[3]
    set_title(s, "Base paper")
    wipe(s)
    K.box(s, 0.6, 1.4, 12.13, 1.2, fill=K.CARD)
    K.text(s, 0.82, 1.46, 11.7, 1.1, F.BASE_PAPER, size=13, color=K.INK, anchor="m")
    cw = 3.85
    cards = [
        ("Method", f"{bp['algorithms']} classifiers (tree, ensemble, linear, probabilistic, kernel, neural) tuned with Optuna on typed symptom indicators. A two-stage TOP-1 / TOP-3 ranking and a {bp['threshold']:.2f} confidence threshold express diagnostic uncertainty; SHAP and LIME explain the best models.", K.BLUE, "M"),
        ("Data and reported results", f"{bp['cases']:,} real cases (internal medicine {bp['internal']}, pediatrics {bp['pediatrics']:,}), {bp['classes']} ICD-10 classes. Best TOP-1: {bp['best_int'][0]} {bp['best_int'][1] * 100:.2f}% and {bp['best_ped'][0]} {bp['best_ped'][1] * 100:.2f}%. External check on {bp['ext_cases']} cases: TOP-3 {bp['ext_top3_int'] * 100:.2f}% and {bp['ext_top3_ped'] * 100:.2f}%.", K.GREEN, "R"),
        ("Relevance to this project", "Same clinical-decision-support goal: probability ranking, a confidence threshold, absent symptom treated as 0 with no imputation, and SHAP explanations. Different input and target: the paper works on typed indicators and ICD-10 diagnoses; ATHENA adds scanned reports and five-level triage.", K.ORANGE, "L"),
    ]
    for i, (t, b_, col, gl) in enumerate(cards):
        K.card(s, 0.6 + i * (cw + 0.29), 2.8, cw, 4.2, t, b_, col, gl, body_size=15)
    notes[4] = ("Read the citation. The paper compares 19 classifiers on 1,655 real cases and formalises uncertainty with TOP-1 and TOP-3. It reads only typed symptom indicators and says nothing about scanned reports, vitals fusion or processing time. "
                "Its numbers are for diagnosis, ours will be for triage priority, so they are never compared directly.")

    # ---- 5 literature survey table
    s = S[4]
    set_title(s, "Literature survey")
    wipe(s)
    rows = [["Work", "Year", "Approach", "Reported result / limitation"]]
    for r in LIT_TABLE[:10]:
        rows.append([r[0].replace(" (base paper)", " (base)"), r[1], r[2], r[3]])
    K.table(s, 0.6, 1.25, [2.6, 0.6, 4.4, 4.53], rows, font_size=11, row_h=0.5, header_size=12, align=["l", "c", "l", "l"])
    notes[5] = ("The survey covers the base paper, reviews and large retrospective studies of machine-learning triage, a companion multi-agent paper, and two process studies from the batch list. "
                "Figures are quoted only where they were read from the paper or its record. Two further batch entries (an obstetric triage article, which could not be located, and an equine veterinary chapter) are listed in the report but not used as evidence.")

    # ---- 6 supporting evidence (chart + list)
    s = S[5]
    set_title(s, "Supporting evidence: report and vitals carry different information")
    wipe(s)
    A = F.ABL
    vals = [A["Vitals only (8)"]["accuracy"], A["Report only (28)"]["accuracy"], A["Fused (36)"]["accuracy"]]
    gf = K.bar_chart(s, 0.6, 1.4, 6.1, 5.2, ["Vitals only\n(8 inputs)", "Report only\n(28 flags)", "Report + vitals\n(36 inputs)"],
                     [("Accuracy", vals)], colors=[K.BLUE], number_format="0.0%", font_size=12, max_value=1.0)
    pt = gf.chart.plots[0].series[0].points[2]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = K.ORANGE
    K.text(s, 7.0, 1.45, 5.75, 4.9, [
        ("**Pilot measurement of this project** (same model, exact-priority accuracy on 1,200 held-out synthetic cases):", {"space_after": 8}),
        (f"Fusing report flags with vitals gives {vals[2] * 100 :.2f}%, against {vals[0] * 100 :.2f}% for vitals alone.", {"bullet": True, "space_after": 8}),
        (f"Triage models built on structured fields (vitals, complaint, history) reach AUC about 0.87 for admission [{R['hong']}].", {"bullet": True, "space_after": 8}),
        (f"Sensitivity of five-level triage scales for critical illness is below 80% in the pooled review [{R['hinson']}].", {"bullet": True, "space_after": 8}),
        (f"The base paper reports TOP-1 accuracy up to {bp['best_ped'][1] * 100:.1f}% on typed symptoms [{R['base']}].", {"bullet": True}),
    ], size=15, color=K.INK)
    K.text(s, 7.0, 6.4, 5.75, 0.55, "Pilot numbers use seeded synthetic data, not patient records; they frame the problem, they are not final results.", size=12, color=K.TXT, italic=True)
    notes[6] = ("This is early evidence from our own prototype, shown because it frames the problem: the scanned report carries information that vitals alone do not. "
                "The 68% figure is on a seeded synthetic dataset and must not be read as clinical performance. The literature points come from the cited papers.")

    # ---- 7 existing system
    s = S[6]
    set_title(s, "Existing system and current approaches")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.1, [("Patient arrives", K.NAVY), ("Nurse reads report and vitals", K.NAVY), ("Scale-based priority (e.g. ESI)", K.NAVY), ("Queue and treatment", K.NAVY)], size=15, gap=0.5)
    K.card(s, 0.6, 2.95, 5.95, 3.8, "Manual triage",
           f"A five-level scale such as the Emergency Severity Index [{R['esi']}] is applied by the nurse on duty.\nThe result depends on experience and shift, and scanned reports are read by eye or filed unread.\nCritical illness is under-identified by all common scales [{R['hinson']}].", K.BLUE, "1", body_size=18)
    K.card(s, 6.78, 2.95, 5.95, 3.8, "Machine-learning triage",
           f"Models on structured fields predict admission or critical care [{R['hong']}], [{R['levin']}], [{R['raita']}].\nThe base paper ranks diagnoses from typed symptom indicators [{R['base']}].\nNone of them reads a scanned report, and many were never implemented in a workflow [{R['fernandes']}].", K.ORANGE, "2", body_size=18)
    notes[7] = "Today triage is manual and subjective. Machine-learning models exist but they use structured fields only; the scanned report stays outside the model."

    # ---- 8 limitations
    s = S[7]
    set_title(s, "Limitations of existing methods")
    wipe(s)
    heads = ["Subjective and variable", "Blind to the scanned report", "Rarely deployed", "Bare predictions"]
    L = LIMITATIONS_OF_EXISTING
    bodies = [
        f"Scale-based triage varies between nurses and shifts and under-identifies critical illness [{R['hinson']}].",
        f"Structured-field models cannot see what is only written in a scanned report [{R['hong']}], [{R['raita']}]. The base paper reads typed indicators only [{R['base']}].",
        f"Many intelligent triage systems were never implemented or evaluated in a clinical workflow [{R['fernandes']}].",
        "A prediction with no reasons is hard to accept at the bedside, and reported accuracies come from different data and tasks, so they cannot be lined up.",
    ]
    for i in range(4):
        r, c = divmod(i, 2)
        K.card(s, 0.6 + c * 6.18, 1.4 + r * 2.4, 5.95, 2.25, heads[i], bodies[i], C[i], str(i + 1), body_size=16)
    K.box(s, 0.6, 6.2, 12.13, 0.6, fill=K.CARD)
    K.text(s, 0.85, 6.2, 11.7, 0.6, "Result: delay in prioritising a critical patient directly worsens outcomes, yet no tool combines the report, the vitals and an explanation.", size=14, color=K.INK, anchor="m")
    notes[8] = "Four limitations from the survey and the batch problem statement. Each maps to a design choice: read the report, fuse it with vitals, give calibrated confidence and reasons, and keep the clinician in charge."

    # ---- 9 research gap
    s = S[8]
    set_title(s, "Research gap")
    wipe(s)
    for i, g in enumerate(GAPS):
        y = 1.35 + i * 1.12
        K.circle(s, 0.6, y + 0.1, 0.62, C[i % 4], str(i + 1), 18)
        K.text(s, 1.55, y, 11.15, 1.0, g, size=17, color=K.INK, anchor="m")
    notes[9] = ("The batch survey states the gap as: the surveyed models are evaluated on single-modality structured data, and nothing fuses OCR, clinical text and vitals while exposing the reasoning. "
                "The other points come from reading the survey papers: the target is rarely a five-level priority, and calibrated confidence, a clinician override record and processing time are seldom reported.")

    # ---- 10 problem statement
    s = S[9]
    set_title(s, "Problem statement")
    wipe(s)
    K.box(s, 0.6, 1.45, 12.13, 3.1, fill=K.CARD)
    K.text(s, 0.95, 1.6, 11.45, 2.85, [(p, {"bullet": True, "space_after": 8}) for p in PROBLEM_STATEMENT], size=18, color=K.INK, anchor="m")
    for i, (t, b_) in enumerate([("Input", "A scanned report (PDF, PNG or JPG, up to 15 MB) and eight vitals: age, heart rate, blood pressure, SpO2, temperature, respiratory rate, arrival mode"),
                                 ("Output", "Priority 1 (critical) to 5 (non-urgent), risk level, calibrated confidence and the factors that drove the decision"),
                                 ("Record", "Clinician accept or change with a reason, a live queue ordered by priority then arrival, and a triage-summary PDF")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 4.8, 3.85, 2.1)
        K.text(s, x + 0.25, 4.9, 3.4, 0.4, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 5.35, 3.4, 1.5, b_, size=13, color=K.TXT)
    notes[10] = "Read the statement slowly. The need is a multi-source triage assistant that reads scanned reports, assigns an explainable risk level and supports rather than replaces the clinician."

    # ---- 11 objectives
    s = S[10]
    set_title(s, "Objectives")
    wipe(s)
    K.text(s, 0.6, 1.4, 12.13, 4.9, [(f"{i}.  {o}", {"space_after": 16}) for i, o in enumerate(OBJECTIVES, 1)], size=24, color=K.INK)
    K.text(s, 0.6, 6.2, 12.13, 0.8, "Implementation note: the prototype reads reports with a local OCR engine and a clinical term lexicon instead of a medical language model, and is trained on synthetic data because no real triage records were available.", size=13, color=K.TXT, italic=True)
    notes[11] = ("The six objectives from the proposal. Later reviews report which were met. Objective 2 (a medical language model) is only partly met by a rule-based lexicon, and objective 6 can be checked only against a synthetic recorded priority; both are stated openly.")

    # ---- 12 proposed approach
    s = S[11]
    set_title(s, "Proposed approach")
    wipe(s)
    cw = 2.88
    for i, (t, b_, col, gl) in enumerate([
        ("Read", "PDF text layer, or local OCR for scans. A clinical lexicon finds 22 symptom, finding and history flags, drops negated ones and reads six lab values against reference ranges, keeping the page of each.", K.BLUE, "1"),
        ("Fuse", "Eight vitals and 28 report flags become one 36-input patient record, shown side by side so the clinician sees what the model saw.", K.GREEN, "2"),
        ("Decide", "Gradient-boosted trees give priority 1 to 5; isotonic calibration makes the confidence a probability; SHAP lists the strongest drivers.", K.ORANGE, "3"),
        ("Review", "The clinician accepts or changes the priority with a reason; the override is stored, the queue reorders and a summary PDF can be downloaded.", K.PURPLE, "4"),
    ]):
        K.card(s, 0.6 + i * (cw + 0.2), 1.45, cw, 3.9, t, b_, col, gl, body_size=15)
    K.box(s, 0.6, 5.5, 12.13, 1.3)
    K.circle(s, 0.85, 5.8, 0.7, K.NAVY, "E", 18)
    K.text(s, 1.8, 5.62, 10.7, 0.45, "Evaluation plan: accuracy, within-one-level accuracy, per-priority recall and time per patient", size=16, color=K.INK, bold=True)
    K.text(s, 1.8, 6.08, 10.7, 0.7, "Delivered as a FastAPI service with SQLite and a React console. No GPU, no external API key; decision support only.", size=14, color=K.TXT)
    notes[12] = ("Four stages. Reading, fusing, deciding, reviewing. The reader and the model run locally. The design keeps the clinician as the final decision maker, which is why the override and its reason are stored.")

    # ---- 13 architecture
    s = S[12]
    set_title(s, "High-level proposed architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.2, 7.5, 5.9)
    K.text(s, 8.3, 1.5, 4.4, 5.2, [
        ("**Layers**", {"space_after": 8}),
        (f"Presentation: React and Vite console (port {F.WEB_PORT}) with six screens.", {"bullet": True}),
        (f"Application: FastAPI service (port {F.API_PORT}) with sign-in, upload limits and input checks.", {"bullet": True}),
        ("Services: report reader, fused record, triage model with SHAP, summary PDF.", {"bullet": True}),
        ("Data: SQLite for users, patients and overrides; model file and sample reports on local disk.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[13] = "Follow the diagram top to bottom: the console calls the API, the API calls four services, and the services use a model file and a small database."

    # ---- 14 expected outcomes
    s = S[13]
    set_title(s, "Expected outcomes and contributions")
    wipe(s)
    heads = ["Working prototype", "Explained decisions", "Honest evaluation", "Comparison with base paper", "Stated limits"]
    bodies = [
        "Upload a report, enter vitals, get priority, risk level and calibrated confidence, review the case and see a live queue. A prototype already runs end to end.",
        "Per-patient SHAP reasons next to the decision, with the page each finding came from, and a stored accept-or-change record.",
        "Accuracy, within-one-level accuracy, per-priority recall, calibration and time per patient, with the weak points reported.",
        "Parallels with the base paper (probability ranking, confidence threshold, SHAP) with every difference in data and task stated.",
        "Trained on seeded synthetic data, rule-based report reader, no user study: each limit documented, not hidden.",
    ]
    for i, (h, b_) in enumerate(zip(heads, bodies)):
        if i < 3:
            K.card(s, 0.6 + i * 4.14, 1.5, 3.85, 2.75, h, b_, C[i % 4], str(i + 1), body_size=15)
        else:
            K.card(s, 0.6 + (i - 3) * 6.18, 4.4, 5.95, 2.4, h, b_, C[i % 4], str(i + 1), body_size=16)
    notes[14] = "These are the outcomes we commit to; they are targets at this stage. Review 2 and the final review report what was actually measured, including what could not be."

    # ---- 15 references
    s = S[14]
    set_title(s, "References")
    wipe(s)
    keys = sorted(["base", "fernandes", "hinson", "hong", "levin", "raita", "esi", "xgboost", "shap", "cheng"], key=lambda k: R[k])
    K.text(s, 0.6, 1.3, 12.13, 5.8, [(f"[{R[k]}] {REFS[R[k] - 1]}".replace("*", ""), {"space_after": 5}) for k in keys], size=12.5, color=K.INK)
    notes[15] = "Selected references; the complete numbered list, including the two survey entries that could not be verified, is in the project report."

    # ---- 16 thank you
    thank_you(S[15])
    notes[16] = ("Likely questions: why not BioBERT or an LLM (offline, no key, auditable lexicon; stated as a gap); why synthetic data (no real triage records available, results reported as such); "
                 "what the clinician still does (accepts or changes every priority).")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "7.Review_1_PPT.pptx")))
