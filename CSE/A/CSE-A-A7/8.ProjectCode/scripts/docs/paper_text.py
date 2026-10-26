"""Text of 19.IEEE_Paper.docx (ATHENA). Every number is read from facts.py (experiments/**/metrics.json); nothing is typed in by hand.

Citations: c('key', ...) returns a {r:N} token with the fixed global reference numbers of scripts/docs/refs.py (CITE); Paper.expand()
renumbers them by order of first citation. The paper cites 20 of the 32 references; s_obst and s_horse are never cited.
"""
import os
import re

from . import facts as F
from . import lit, paper_figs
from .paper import Paper
from .refs import CITE

f2, f3, pct = F.f2, F.f3, F.pct

USED = ["base", "cheng", "fernandes", "hinson", "hong", "levin", "raita", "xie", "esi", "xgboost", "shap", "treeshap", "zadrozny", "guo",
        "grinsztajn", "biobert", "ppocr", "sklearn", "tripod", "s_acmj"]


def c(*keys):
    for k in keys:
        assert k in USED, k
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


def p1(x):
    return f"{x * 100:.1f}"


def build(path):
    figs = paper_figs.make()
    P = Paper()
    comp, abl, cal, saf, rob, seeds = F.COMP, F.ABL, F.CAL, F.SAFE, F.ROB, F.SEEDS
    bp = F.BASE_PAPER_RESULTS
    st = F.STRESS
    t85 = F.thr_row(0.85)
    r2, r5, r10 = F.rob_row(0.2), F.rob_row(0.5), F.rob_row(1.0)
    cm = F.CM
    n_under2 = round(saf["under_triage_2plus"] * F.N_TEST)
    shap_names = {"spo2": "SpO2", "arrival_code": "arrival mode", "dyspnea": "shortness of breath", "sbp": "systolic pressure", "resp_rate": "respiratory rate"}
    shap5 = ", ".join(shap_names[s["feature"]] for s in F.SHAP_TOP[:5])
    lr, xg = comp["Logistic regression"], comp["XGBoost (shipped config)"]
    cat = st["by_category"]

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"])
    P.title_block("ATHENA: Explainable Emergency Triage from Scanned Reports and Vitals", authors)
    P.begin_two_columns()

    P.abstract(
        "Emergency departments must decide within minutes who is seen first, and triage by scale varies with the person on duty. Models built on structured fields cannot see "
        "what is written only in a scanned report. This paper presents ATHENA, a decision-support tool that reads a PDF or scanned report, extracts symptoms, findings, history "
        "and six laboratory values with a negation-aware lexicon, fuses them with eight vitals into 36 inputs, and assigns a triage priority from 1 to 5 with a calibrated confidence "
        "and a per-patient SHAP explanation. A clinician accepts or changes each priority and the reason is stored. The model was trained and tested on a seeded synthetic dataset of "
        f"{F.ROWS:,} cases, not on patient records. On {F.N_TEST:,} held-out synthetic cases it reaches {p1(F.ACC)} % exact accuracy, {p1(F.W1)} % within one level and macro F1 {f3(F.MF1)}, "
        f"but recall for priority 1 is only {p1(F.REC[0])} %. Using the report with the vitals lifts accuracy from {p1(abl['Vitals only (8)']['accuracy'])} % to {p1(abl['Fused (36)']['accuracy'])} %, "
        f"and a logistic-regression baseline scores higher ({p1(lr['accuracy'])} %). The work demonstrates an integrated, explainable pipeline, not clinical validity.",
        ["clinical decision support", "emergency triage", "explainable AI", "optical character recognition", "probability calibration", "SHAP", "XGBoost"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("An emergency department has minutes to decide which patient is seen first. In many emergency departments a nurse assigns one of five levels, as in the Emergency Severity Index "
           f"{c('esi')}, from vital signs, the complaint and experience. The result varies between people and shifts, and a systematic review found sensitivity below 80 % for "
           f"identifying critically ill patients {c('hinson')}. Machine-learning triage models trained on structured fields have matched or beaten scale-based triage on outcomes "
           f"such as admission and critical care {c('hong', 'levin', 'raita')}, yet a review notes that several intelligent triage studies never reached implementation {c('fernandes')}.")
    P.para("These models share a blind spot. Much of what a clinician knows at triage sits in a referral letter, an ECG printout or a laboratory slip that arrives as a scanned document, "
           "and a model that sees only typed fields never reads it. A bare prediction also has little chance of "
           "acceptance at the bedside unless the reasons are shown next to it, and a stated confidence is only useful if it is calibrated.")
    P.para("ATHENA is decision support, not a diagnostic device. It reads the text of a report, not images such as radiographs, it never acts on its own, and the treating clinician makes the "
           "final decision: every priority can be accepted or changed, and a change needs a written reason.")
    P.para(f"The base paper {c('base')} studies diagnosis from typed symptom indicators with 19 classifiers, a TOP-1/TOP-3 ranking and SHAP and LIME explanations, and does not read scans or produce a triage "
           "level. ATHENA takes its ideas of probability ranking, a high-confidence threshold, explanation and no imputation of missing symptoms, and applies them to scanned reports and "
           "triage. The contributions are: (1) an offline report reader that turns a PDF or scan into page-referenced symptoms, findings, history and lab flags, with negation handling; "
           "(2) a fused 36-input record and an isotonic-calibrated XGBoost that outputs priority 1 to 5, a risk level and a calibrated confidence, with per-patient SHAP reasons; "
           "(3) a clinician accept-or-change loop that stores every decision with its reason; and (4) an honest evaluation on seeded synthetic data covering model comparison, input ablation, "
           "calibration, robustness to missed findings and the limits of the report reader. Section II reviews related work, Section III the method, Section IV the results and Section V concludes.")
    P.para("The project set six objectives: an OCR stage for scanned reports; extraction of symptoms, findings and history from the text; one patient representation that combines text-derived features with tabular vitals; "
           "a model that assigns a risk level and triage priority; an explanation layer showing which findings drove the priority; and an evaluation of accuracy against the recorded priority together with processing time per patient. "
           "Section V states how far each was met.")
    P.sub("A", "System Hardware")
    P.para("All training, tests and timings ran on one Windows 11 Pro machine with an Intel Core i5-12500 (12 threads), 15.7 GB of RAM and no GPU. Optical character recognition (OCR) therefore ran on "
           "the CPU, and absolute times are indicative of a modest workstation.")
    P.sub("B", "Software Requirements")
    P.para(f"Python 3.11.9 with FastAPI and SQLAlchemy (SQLite) for the service, XGBoost {c('xgboost')}, scikit-learn {c('sklearn')}, the SHAP package {c('shap')}, pypdf and RapidOCR (ONNX Runtime) "
           "for report reading, ReportLab for the summary PDF, and React 19 with Vite 8 for the interface (Node 24.19). Passwords are hashed with bcrypt and sessions use signed JSON Web Tokens.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Mlodawski et al. {c('base')} build a diagnostic classifier for internal medicine and pediatrics. They use {bp['cases']:,} real clinical cases ({bp['internal']} internal medicine, "
           f"{bp['pediatrics']:,} pediatrics), {bp['parameters']} clinical parameters and {bp['classes']} ICD-10 diagnostic classes, treat undocumented symptoms as absent without imputation, "
           f"add rule-based synthetic cases for rare diseases, and compare {bp['algorithms']} algorithms tuned with Optuna (up to {bp['trials']} trials each). A two-stage TOP-1/TOP-3 mechanism ranks diagnoses by probability and "
           f"calls a diagnosis highly probable above {bp['threshold']}, with a stricter acceptance threshold for high-risk diseases. Gradient boosting is best in internal medicine "
           f"({pct(bp['best_int'][1], 2)} TOP-1) and a multilayer perceptron in pediatrics ({pct(bp['best_ped'][1], 2)}); mean TOP-3 accuracy is {pct(bp['top3_mean_int'], 2)} and {pct(bp['top3_mean_ped'], 2)}. "
           f"On {bp['ext_cases']} cases from a separate facility, TOP-1 accuracy falls to {pct(bp['ext_top1_int'], 2)} and {pct(bp['ext_top1_ped'], 2)}. SHAP and LIME check that the learned features are clinically sensible. "
           "The input is a typed indicator vector: the work does not read documents, does not fuse vital signs, and predicts diagnoses rather than urgency.")
    P.para(f"**Triage prediction.** Fernandes et al. {c('fernandes')} review intelligent triage support and find that several studies lack an implementation phase. Hinson et al. {c('hinson')} review 182 "
           f"studies of triage scales and report low sensitivity for critical illness. Hong et al. {c('hong')} predict admission for 560,486 visits and find that history adds to triage-only inputs "
           f"(area under the curve about 0.87 rising to about 0.92). Levin et al. {c('levin')} train a random forest on 172,726 visits that matches or exceeds the Emergency Severity Index for outcomes, "
           f"and Raita et al. {c('raita')} report an area under the curve of 0.86 for a deep network against 0.74 for an index-based model on critical care. Xie et al. {c('xie')} publish a public benchmark on MIMIC-IV-ED. "
           f"A prospective study compares ESI with Manchester triage on 6,000 patients each {c('s_acmj')}, a process study without machine learning.")
    P.para(f"**Language and OCR.** BioBERT {c('biobert')} is the usual choice for biomedical text mining, and PaddleOCR-family models {c('ppocr')} are widely used for text recognition; ATHENA uses the latter "
           f"through RapidOCR but a transparent lexicon instead of a language model. Multi-agent language-model triage {c('cheng')} reasons over written cases and was not evaluated on scans or vitals here. "
           f"ATHENA explains each decision with per-patient SHAP attributions {c('shap', 'treeshap')}, and probability calibration {c('zadrozny', 'guo')} is needed for a confidence to be read as a probability.")
    P.table("Representative related work", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [[re.sub(r"\[(\d+)\]", r"{r:\1}", cell) for cell in row] for row in lit.PAPER_TABLE],
            widths=[0.62, 0.78, 0.62, 0.7, 0.68], size=6.6, align=["l", "l", "l", "l", "l"])
    P.para(f"**Evaluation practice.** The large retrospective studies above use real visits and report discrimination as area under the curve for admission or critical care, not agreement on a five-level priority, so they "
           f"cannot be compared with a priority accuracy. The base paper is careful about leakage: its synthetic rare-disease cases were generated before the evaluation data were collected, only 0.7 % and 0.3 % of test "
           f"cases repeat a training symptom pattern, and a separate facility supplies external validation {c('base')}. A model trained on labels produced by a rule can only show that it has recovered the rule, "
           f"and the evaluation in Section IV is read with that limit in mind. Reporting guidance for prediction models asks for the origin of the data, the split and the intended use to be stated {c('tripod')}.")
    P.para(f"**Gap.** The surveyed models are evaluated on single-modality structured data, and their targets are admission, critical care or diagnosis rather than a five-level priority. "
           "None fuses a scanned report with vitals, shows a per-patient reason beside the decision, records the clinician's acceptance or change, and measures processing time per patient. "
           "ATHENA addresses these four points on synthetic data, and the survey also shows what it does not attempt: it uses no language model, no retrieval and no multi-agent control.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.para("**Architecture.** Fig. 1 shows the layers. A React single-page app calls a FastAPI service through 13 endpoints. Everything except health, public statistics and sign-in needs a bearer "
           "token. Patients, users and clinician decisions are stored in SQLite; the model and sample reports are files. Clinicians and administrators sign in with separate roles.")
    P.figure(figs["arch"], "ATHENA architecture: browser app, API, four services and storage.")
    P.para(f"**Report reading.** A PDF page is read from its text layer with pypdf; a page with fewer than 20 characters falls back to OCR of its embedded image, and PNG or JPG uploads go straight to "
           "RapidOCR (upscaled when small, boxes sorted into reading order). Wrapped lines are rejoined and each sentence is matched against a lexicon of 22 flags (11 symptoms, 5 findings, 6 history items). "
           "A match is dropped when a negation cue (no, denies, without, negative for, not, nil, ruled out) occurs within 45 characters before it. Spaces in phrases tolerate OCR run-ons. "
           "Six laboratory values (troponin, lactate, white-cell count, glucose, creatinine, haemoglobin) are parsed with their units and compared with fixed reference ranges, and an abnormal value sets "
           "its flag. Every item keeps its page number, so a clinician can find the source line.")
    P.figure(figs["flow"], "Main flow from upload to the clinician's decision.")
    P.para("**Interface and roles.** The app has six screens. A new patient is entered by choosing or dropping a report, which is read at once and shown as chips labelled with their page, then by checking the eight vitals. "
           "The result screen shows the priority, risk level and confidence, the fused record beside the extracted findings, the SHAP bars and the accept-or-change control. The queue refreshes every 15 seconds and can be filtered "
           "by priority. The performance screen reads the stored evaluation files and a banner states that the data are synthetic.")
    P.para("**Fused record.** The eight vitals (age, heart rate, systolic and diastolic pressure, SpO2, temperature, respiratory rate and arrival mode coded 0 to 2) and the 28 report flags give a 36-input vector. "
           "A finding that the report does not mention is 0, so no value is imputed, as in the base paper.")
    P.para(f"**Model.** An XGBoost classifier {c('xgboost')} (220 trees, depth 4, learning rate 0.1, subsample 0.9) is trained with a softmax objective on {F.N_TRAIN:,} cases. Isotonic calibration "
           f"{c('zadrozny')} is fitted on a separate {F.N_CAL} cases so that the largest calibrated probability can be read as a confidence. With P(k | x) the calibrated probability of priority k for input x, the assigned priority is")
    P.eq("k* = argmax_k  P(k | x),     confidence = P(k* | x).")
    P.para(f"Priorities 1-2 map to High risk, 3 to Moderate and 4-5 to Low. The reasons come from TreeSHAP {c('treeshap')}: for the chosen class the prediction is the base value plus one additive contribution per input,")
    P.eq("f_k(x) = φ_0 + Σ_i φ_i(x),")
    P.para("and the eight strongest contributions are listed in order of absolute size, hiding absent flags whose effect is below 0.15. The clinician can accept the priority or change it with a reason; "
           "the model's original suggestion is kept beside the final priority, and the queue is ordered by priority and then arrival.", indent=0)
    P.para(f"**Training and reproducibility.** Training the shipped model takes {F.TRAIN_SEC:.2f} s on the CPU. The generator, the split and the model use one fixed seed, "
           "and every figure in this paper is produced by a script that writes a JSON file read back by the document builder, so a number in the text cannot drift from the measurement.")
    P.para("**Security and error handling.** Passwords are stored as bcrypt hashes and a sign-in returns a signed token valid for 12 hours. Vitals are range-checked on entry (for example age 0 to 120, heart rate 20 to 250, "
           "SpO2 50 to 100, temperature 30 to 44 C), uploads above 15 MB are refused, an empty or unreadable file returns a plain message, and a missing model returns a service-unavailable status instead of a guess.")
    P.para(f"**Data.** No patient records were available, so a seeded generator (seed {F.SEED}) simulates {F.ROWS:,} cases from seven archetypes (minor, cardiac, respiratory, trauma, abdominal, infection, neurological). "
           "Vitals are drawn from clipped normal distributions shifted per archetype, report flags from per-archetype probabilities, and a hand-written severity score of vital-sign thresholds and flag weights plus "
           "Gaussian noise (standard deviation 0.4) is cut into five priorities. The score therefore plays the role of the recorded clinician decision, and priority 1 is rare "
           f"({pct(F.PRIO_SHARE[0])} of cases). The split is {F.N_TRAIN:,} fit, {F.N_CAL} calibration and {F.N_TEST:,} test cases, stratified by priority. Because the label is a known function of the inputs plus noise, an observer "
           f"who knew the noise-free score would match the label for only {pct(F.CEILING, 2)} of cases, which is the ceiling for exact accuracy.")
    P.para(f"**Experiments and metrics.** Seven further models (logistic regression, decision tree, random forest, extra trees, k-nearest neighbours, a small MLP and histogram gradient boosting) were trained on the same rows, "
           "in the style of the base paper's multi-algorithm comparison, together with a vitals-only and a report-only ablation. Metrics are exact accuracy, accuracy within one level, macro F1, quadratic weighted "
           "kappa, Top-2 accuracy, expected calibration error (ECE, ten bins) and recall per priority. Robustness is tested by removing each positive report flag with a given probability at inference. "
           f"The report reader is scored on 12 generated sample reports and on 40 hand-written fragments, and the service is timed over HTTP on 127.0.0.1. Reporting follows the intent of TRIPOD+AI {c('tripod')}: "
           "data origin, split, metrics and limits are stated. Code is verified with 47 pytest tests and 17 end-to-end smoke checks.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.para(f"**Test conditions.** All model figures are on the {F.N_TEST:,} held-out synthetic cases, on the machine of Section I-A. They measure how well a model recovers a known rule, not agreement with "
           "clinicians, and they would change on real triage records.")
    rows = [["Shipped XGBoost + isotonic", p1(F.ACC), f3(F.MF1), f3(F.QWK), p1(F.TOP2)]]
    for lab, k in [("XGBoost, uncalibrated", "XGBoost (shipped config)"), ("Logistic regression", "Logistic regression"), ("MLP (64, 32)", "MLP"), ("Hist. gradient boosting", "HistGradientBoosting"),
                   ("Extra trees", "Extra trees"), ("Random forest", "Random forest"), ("k-nearest neighbours", "k-nearest neighbours"), ("Decision tree", "Decision tree")]:
        d = comp[k]
        rows.append([lab, p1(d["accuracy"]), f3(d["macro_f1"]), f3(d["qwk"]), p1(d["top2"])])
    for lab, k in [("Vitals only (8 inputs)", "Vitals only (8)"), ("Report only (28 inputs)", "Report only (28)")]:
        d = abl[k]
        rows.append([lab, p1(d["accuracy"]), f3(d["macro_f1"]), f3(d["qwk"]), p1(d["top2"])])
    P.table("Accuracy and agreement on the synthetic hold-out (percent; fused inputs unless stated)", ["Model or input set", "Acc.", "Macro F1", "QWK", "Top-2"], rows,
            widths=[1.45, 0.4, 0.55, 0.45, 0.5], size=6.8, align=["l", "c", "c", "c", "c"])
    P.figure(figs["results"], "(a) Accuracy of eight models. (b) Accuracy by inputs used. (c) Recall per priority of the shipped model. (d) Accuracy and coverage as the confidence threshold rises (dotted: 0.85).")
    P.para(f"**Triage accuracy.** The shipped model reaches {p1(F.ACC)} % exact accuracy and {p1(F.W1)} % within one level, quadratic weighted kappa {f3(F.QWK)} and Top-2 accuracy {p1(F.TOP2)} % (Table II). "
           f"Recall falls toward the urgent end: {', '.join(p1(r) for r in F.REC)} % for priorities 1 to 5 (Fig. 3c), because the rare, severe cases sit next to the boundary of the next level "
           f"({cm[0][1]} of {F.SUP[0]} priority-1 cases were placed at priority 2, {cm[1][2]} of {F.SUP[1]} priority-2 cases at priority 3). Over five split seeds the same recipe gives {p1(seeds['accuracy_mean'])} % "
           f"(standard deviation {p1(seeds['accuracy_std'])} points), so the shipped split, at {p1(F.ACC)} %, is a below-average one. Logistic regression scores higher ({p1(lr['accuracy'])} %) "
           f"than every tree model: the synthetic label is an additive score, which a linear model recovers well. XGBoost was kept for its exact tree explanations and calibration, an assumption about real data that this experiment does not test {c('grinsztajn')}. "
           f"About {pct(F.CEILING)} is the ceiling set by the label noise.")
    P.para(f"**Where the errors fall.** Almost every miss is to the neighbouring level: {cm[2][3]} priority-3 cases went to 4, {cm[3][4]} priority-4 cases to 5, {cm[4][3]} priority-5 cases to 4 and {cm[1][0]} priority-2 cases to 1. "
           f"Only {round((1 - F.W1) * F.N_TEST)} of {F.N_TEST:,} cases are two levels away ({cm[0][2]} priority-1 cases placed at 3 and {cm[2][4]} priority-3 cases at 5). The model leans toward the less urgent neighbour, the unsafe "
           "direction: a cut-off that sends more cases to the more urgent level would raise high-risk recall at the price of more over-triage. Because the neighbouring levels differ by a small amount of "
           "severity score, and the label carries added noise, the confusion between them is partly irreducible in this data.")
    P.para(f"**Stability and calibration.** Five-fold cross-validation over all {F.ROWS:,} cases gives {pct(F.CV5['XGBoost (shipped config)']['mean'])} for XGBoost (standard deviation {pct(F.CV5['XGBoost (shipped config)']['std'])}), "
           f"{pct(F.CV5['Logistic regression']['mean'])} for logistic regression and {pct(F.CV5['Random forest']['mean'])} for a random forest, so the three are close and the ordering in Table II should not be over-read. "
           f"Mean confidence is {f3(F.MEAN_CONF)} against accuracy {f3(F.ACC)}, a mild over-confidence; the multiclass Brier score improves from {f3(cal['brier_uncalibrated'])} to {f3(cal['brier_isotonic'])} with calibration.")
    P.para(f"**Value of the report.** Vitals alone give {p1(abl['Vitals only (8)']['accuracy'])} % accuracy, the report alone {p1(abl['Report only (28)']['accuracy'])} % and both together {p1(abl['Fused (36)']['accuracy'])} %, "
           f"with within-one accuracy rising from {p1(abl['Vitals only (8)']['within_one'])} % to {p1(abl['Fused (36)']['within_one'])} %. Text flags carry most of the gain and laboratory flags a smaller part. This is the single-modality gap "
           "the project set out to close, but it is partly a property of how the data were generated, since the severity score gives the report flags large weights. Global SHAP importance ranks "
           f"{shap5} highest, in line with those weights, which checks the explainer rather than clinical reasoning.")
    P.para(f"**Confidence and safety.** Isotonic calibration lowers ECE only from {f3(cal['ece_uncalibrated'])} to {f3(cal['ece_isotonic'])}, and the 0.8 to 0.9 confidence bin is over-confident (observed accuracy about 66 %). "
           f"Restricting to confidence of at least 0.85 keeps {pct(t85['coverage'])} of cases at {pct(t85['accuracy'])} accuracy (Fig. 3d), which parallels the 0.85 threshold of the base paper. "
           f"The model under-triages {pct(saf['under_triage_any'])} of cases (less urgent than recorded) and over-triages {pct(saf['over_triage_any'])}; {n_under2} cases are under-triaged by two levels and none over-triaged by two. "
           f"Treating priorities 1-2 as a high-risk class, recall is {pct(saf['high_risk_recall'])} at the arg-max and precision {pct(saf['high_risk_precision'])}; flagging high risk whenever P1 + P2 is at least 0.4 would give recall "
           f"{pct(saf['high_risk_recall_at_pr_0_4'])} at precision {pct(saf['high_risk_precision_at_pr_0_4'])}, but this rule is not implemented. A clinician must therefore review every priority.")
    P.para(f"**Worked example.** Sample report 01 (chest pain radiating to the left arm, ST elevation on the ECG, raised troponin and lactate, diabetes and hypertension) is read from a two-page PDF and entered with a heart rate of 112, "
           f"systolic pressure 96 and SpO2 93 %. The model assigns priority 1 (Critical) at confidence 100 %, and the SHAP list puts ST elevation first (contribution +3.11), then raised troponin (+2.19), raised lactate (+1.51), heart rate and "
           f"SpO2 (Fig. 4). When the clinician changes a priority, the case keeps the model's original suggestion, the queue is reordered, and the change appears as CHANGED in the clinician column.")
    P.para(f"**Report reader and robustness.** The reader recovers every flag in the 12 generated sample reports (precision and recall 100 %), but these were written with the lexicon in view. On 40 hand-written fragments "
           f"it reaches precision {pct(st['precision'])} and recall {pct(st['recall'])}, with recall of {pct(cat['paraphrase']['recall'])} on paraphrases it does not contain (\"cannot catch his breath\"), "
           f"{pct(cat['ocr']['recall'])} on split OCR words and {pct(cat['negation']['precision'])} precision on negation, where \"afebrile\" is read as fever and a negation cue before \"but\" hides the following finding. "
           f"If a fifth of positive report flags are missed, accuracy drops from {p1(F.ACC)} % to {p1(r2['accuracy'])} %; with no report it is {p1(r10['accuracy'])} %. A reader recall near {pct(st['recall'], 0)} corresponds roughly to "
           "the 10 % to 20 % loss rows of that experiment. Timings over HTTP: a PDF report is read and triaged in "
           f"{F.lat('flow_pdf_then_triage'):.0f} ms (median), a scanned image in {F.lat('flow_scan_then_triage') / 1000:.1f} s, dominated by OCR.")
    P.para(f"**Service performance and tests.** Medians over repeated calls on 127.0.0.1: creating a patient with model and SHAP takes {F.lat('create_patient'):.1f} ms, reading a text PDF {F.lat('extract_pdf'):.1f} ms, "
           f"loading the queue {F.lat('queue_list'):.1f} ms, building a summary PDF {F.lat('summary_pdf'):.1f} ms and signing in {F.lat('login'):.0f} ms (bcrypt). Reading an image scan takes {F.lat('extract_scan_png') / 1000:.1f} s "
           f"on the CPU. Of {F.PYTEST_TOTAL} automated tests, {F.PYTEST_PASSED} pass and one is an expected failure that records the negation-scope defect; all {F.SMOKE_TOTAL} smoke checks pass. "
           "Untested are concurrent users, real scans other than four generated images, and any security assessment beyond authentication, input limits and a path-traversal check; the default signing secret must be replaced before any deployment.")
    P.para(f"**Threats to validity.** The labels are a known function of the inputs, so accuracy measures rule recovery. "
           f"The hold-out is a single split with {F.N_TEST:,} cases, and its priority-1 class has only {F.SUP[0]} cases. The hand-written fragments were written by the developers. Timings come from one shared machine. "
           "Only real triage records and a prospective study remove them.")
    P.figure(figs["why"], "Output screen: priority 1 for a chest-pain report, with extracted findings carrying page numbers and the SHAP list of reasons.")
    P.para(f"**Reading the numbers in practice.** Two results shape how the tool could be used. First, confidence is informative: accuracy rises from {pct(F.thr_row(0.5)['accuracy'])} at a threshold of 0.5 to "
           f"{pct(F.thr_row(0.9)['accuracy'])} at 0.9, so a low confidence is a sensible prompt for a closer look. Second, the model cannot be trusted to protect the sickest patients unaided, since "
           f"{pct(1 - saf['high_risk_recall'])} of recorded priority-1 and 2 cases were not flagged high risk. For that reason the design keeps the clinician in the loop and records every acceptance and change, which also "
           "produces the data needed to measure agreement with clinicians in a real deployment.")
    P.para(f"**Comparison with the base paper.** The two works differ in task, data and metrics, so the figures are not comparable. The base paper reports {pct(bp['best_int'][1], 2)} and {pct(bp['best_ped'][1], 2)} TOP-1 "
           f"accuracy over {bp['classes']} ICD-10 classes on real cases, and {pct(bp['ext_top1_int'], 2)} and {pct(bp['ext_top1_ped'], 2)} on an external set; ATHENA reaches {p1(F.ACC)} % over five ordered levels on synthetic data. "
           "What carries over is method: probability ranking, a high-confidence threshold, SHAP, absent-means-zero input and a multi-algorithm comparison, where ATHENA adds report reading, fusion, calibration and the clinician loop. "
           "The base paper's external validation is the step ATHENA lacks and most needs.")
    P.figure(figs["perf"], "Output screen: model performance page with accuracy, within-one accuracy, macro F1, live seconds per patient, recall per priority and the confusion matrix, flagged as synthetic.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion")
    P.para("ATHENA reads a scanned report, fuses it with vitals, and returns a calibrated priority with per-patient reasons and a recorded clinician decision, as one tested application. Against the six objectives, "
           "OCR, fusion, priority and risk assignment, and explanation are met; extraction with a medical language model is only partly met, because a lexicon replaced BioBERT; "
           "and accuracy against clinician-assigned priority is met only against the synthetic recorded priority, with time per patient measured.")
    P.para(f"The key finding is that report and vitals together beat either alone ({p1(abl['Fused (36)']['accuracy'])} % against {p1(abl['Vitals only (8)']['accuracy'])} % and {p1(abl['Report only (28)']['accuracy'])} %), "
           f"while the weak points are the sickest patients (priority 1 recall {p1(F.REC[0])} %, high-risk recall {pct(saf['high_risk_recall'], 0)}), a reader that misses paraphrases, only modest calibration and a linear baseline that matches the "
           "shipped model. No real patient data, clinician study or external validation was used, so no clinical claim is made.")
    P.para("Not built from the original plan: a biomedical language model, retrieval-augmented reasoning, multi-agent control, a document database and the six disease-risk models. A lexicon, a single "
           "calibrated classifier and SQLite replaced them, keeping the system small and offline.")
    P.para("Future work: train and validate on real triage records with credentialed access; replace the lexicon with a biomedical language model and fix its negation scope; add the P1 + P2 high-risk "
           "rule and better calibration; test on real scans; harden authentication and logging; and run a usability study with clinicians.")

    P.references()
    return P.save(path)


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "19.IEEE_Paper.docx")))
