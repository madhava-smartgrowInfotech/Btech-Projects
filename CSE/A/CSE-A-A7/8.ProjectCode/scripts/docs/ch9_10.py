"""Novelty, contributions, scope, limitations, walkthroughs, decisions, conclusion (Chapter 9) and future scope (Chapter 10) of the ATHENA documents.

Every measured number comes from facts.py (F), which reads the stored experiment JSON. All model figures are on the seeded synthetic data set.
"""
import os

from . import facts as F
from .blocks import B, CODE, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    lines = open(os.path.join(F.CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")


def c(*keys):
    """Citation string such as [1], [6] from CITE keys."""
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _v():
    """Frequently quoted measured values (all synthetic-data figures unless the key says otherwise)."""
    abl, comp, cal, st = F.ABL, F.COMP, F.CAL, F.STRESS
    t85, t90 = F.thr_row(0.85), F.thr_row(0.9)
    return {
        "acc": F.pct(F.ACC), "w1": F.pct(F.W1), "f1": F.f3(F.MF1), "qwk": F.f3(F.QWK), "top2": F.pct(F.TOP2), "ceil": F.pct(F.CEILING, 2),
        "r1": F.pct(F.REC[0]), "r2": F.pct(F.REC[1]), "r5": F.pct(F.REC[4]),
        "fused": F.pct(abl["Fused (36)"]["accuracy"], 2), "vit": F.pct(abl["Vitals only (8)"]["accuracy"], 2), "rep": F.pct(abl["Report only (28)"]["accuracy"], 2),
        "gain_v": f"{(abl['Fused (36)']['accuracy'] - abl['Vitals only (8)']['accuracy']) * 100:.1f}",
        "gain_r": f"{(abl['Fused (36)']['accuracy'] - abl['Report only (28)']['accuracy']) * 100:.1f}",
        "lr": F.pct(comp["Logistic regression"]["accuracy"], 2), "xgb": F.pct(comp["XGBoost (shipped config)"]["accuracy"], 2), "mlp": F.pct(comp["MLP"]["accuracy"], 2),
        "cv_xgb": f"{F.pct(F.CV5['XGBoost (shipped config)']['mean'])} (sd {F.CV5['XGBoost (shipped config)']['std'] * 100:.1f})",
        "seed_mean": F.pct(F.SEEDS["accuracy_mean"]), "seed_sd": f"{F.SEEDS['accuracy_std'] * 100:.1f}",
        "ece0": F.f3(cal["ece_uncalibrated"]), "ece1": F.f3(cal["ece_isotonic"]),
        "hr_rec": F.pct(F.SAFE["high_risk_recall"]), "hr_prec": F.pct(F.SAFE["high_risk_precision"]),
        "hr_rec4": F.pct(F.SAFE["high_risk_recall_at_pr_0_4"]), "hr_prec4": F.pct(F.SAFE["high_risk_precision_at_pr_0_4"]),
        "under": F.pct(F.SAFE["under_triage_any"]), "over": F.pct(F.SAFE["over_triage_any"]), "under2": F.pct(F.SAFE["under_triage_2plus"], 2),
        "p1_miss": F.SAFE["p1_predicted_p3_or_lower_urgency"], "p1_n": F.SAFE["p1_support"],
        "t85_cov": F.pct(t85["coverage"]), "t85_acc": F.pct(t85["accuracy"]), "t90_cov": F.pct(t90["coverage"]), "t90_acc": F.pct(t90["accuracy"]),
        "rd10": F.pct(F.rob_row(0.1)["accuracy"]), "rd20": F.pct(F.rob_row(0.2)["accuracy"]), "rd0": F.pct(F.rob_row(1.0)["accuracy"]),
        "rd_none_w1": F.pct(F.rob_row(1.0)["within_one"]),
        "rd_prec": F.pct(st["precision"]), "rd_rec": F.pct(st["recall"]), "rd_exact": f"{st['cases_read_exactly']} of {st['cases']}",
        "read_rec": F.pct(F.READ["recall"], 0), "read_exact": F.READ["reports_read_exactly"],
        "para_rec": F.pct(st["by_category"]["paraphrase"]["recall"]), "neg_prec": F.pct(st["by_category"]["negation"]["precision"], 0),
        "lat_pdf": f"{F.lat('flow_pdf_then_triage'):.0f}", "lat_scan": f"{F.lat('flow_scan_then_triage') / 1000:.1f}",
        "lat_ocr": f"{F.lat('extract_scan_png') / 1000:.1f}", "lat_create": f"{F.lat('create_patient'):.0f}", "lat_pdfx": f"{F.lat('extract_pdf'):.0f}",
        "e2e_mean": f"{F.E2E['mean']:.2f}", "e2e_med": f"{F.E2E['median']:.3f}", "e2e_max": f"{F.E2E['max']:.2f}",
        "pytest": f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL}", "shap1": F.SHAP_TOP[0]["feature"],
    }


# ---------------------------------------------------------------- document 9: novelty and contributions
def novelty_blocks():
    v = _v()
    b = F.BASE_PAPER_RESULTS
    return [
        H2("2.1 What the base paper contributes"),
        P(f"The base paper {c('base')} studies diagnostic classification under incomplete clinical data. It takes {b['cases']:,} real clinical cases (internal medicine {b['internal']}, paediatrics {b['pediatrics']:,}), "
          f"each described by binary indicators of symptoms, examination findings and a few laboratory results (up to {b['parameters']} parameters), and maps them to ICD-10 diagnostic classes ({b['classes']} classes). "
          f"It compares {b['algorithms']} classifiers tuned with Optuna ({b['trials']} trials per model), reports a two-stage TOP-1 / TOP-3 evaluation that formalises differential diagnosis, and adds a confidence threshold of {b['threshold']} for accepting the first diagnosis, "
          f"with SHAP and LIME to explain the best models. Gradient Boosting scores {b['best_int'][1] * 100:.2f}% in internal medicine and the multi-layer perceptron {b['best_ped'][1] * 100:.2f}% in paediatrics; on {b['ext_cases']} external cases TOP-1 accuracy is "
          f"{b['ext_top1_int'] * 100:.2f}% and {b['ext_top1_ped'] * 100:.2f}%. A symptom absent from the record is treated as absent, with no imputation. "
          "The paper's own text states the limits that matter here: typed indicators only (no scans, no free text), diagnosis rather than urgency, and two specialties from one region."),
        H2("2.2 What ATHENA adopts from the base paper"),
        B("The principle of treating an unrecorded finding as absent rather than imputing it; ATHENA sets every unreported flag to 0.",
          "Comparing several algorithm families on the same split before choosing one (eight here, nineteen there).",
          "Reporting a ranked output next to the single best label (Top-2 accuracy here, TOP-3 there) and a high-confidence threshold (0.85 in both).",
          "Showing SHAP attributions so that a clinician can see why a label was proposed."),
        H2("2.3 What is new in ATHENA and what is not"),
        TAB("Novelty against the base paper", ["Aspect", "Base paper", "ATHENA", "New?"],
            [["Task", "ICD-10 diagnosis, 87 classes", "Five-level triage priority and a three-level risk", "Different task: not a claim of improvement"],
             ["Input", "Typed binary symptom indicators", f"Scanned PDF or image read by text layer or local OCR, fused with 8 vitals into {F.N_FEATURES} inputs", "Yes"],
             ["Models", "19 classifiers, Optuna tuning", "8 classifiers compared; XGBoost shipped without tuning", "No: narrower, standard methods"],
             ["Uncertainty", "TOP-1 / TOP-3, 0.85 threshold, entropy", f"Isotonic-calibrated probabilities, Top-2, confidence-coverage table, risk level", "Partly: calibration and risk level added"],
             ["Explanation", "SHAP and LIME, global and by class", "Per-patient SHAP beside the decision, plus global importance", "Per-patient view in the workflow is new; LIME not built"],
             ["Missing input", "No imputation; absent = 0", f"Same rule, plus a dropped-flag experiment: accuracy {v['rd10']} at 10% dropped, {v['rd0']} with no report", "Measured, not new"],
             ["Human in the loop", "Not part of the study", "Accept or change with a reason, stored with the case; queue reorders", "Yes"],
             ["Time per patient", "Not reported in the paper", f"Median {v['lat_pdf']} ms for a PDF and {v['lat_scan']} s for a scan, read plus triage, over HTTP", "Yes"],
             ["Data", f"{b['cases']:,} real cases and {b['ext_cases']} external cases", f"{F.ROWS:,} seeded synthetic cases; no real patient data", "Weaker: the main limitation"]],
            widths=[1.0, 1.6, 2.6, 1.3], align=["l", "l", "l", "l"], size=9.0),
        H2("2.4 Why the integration counts"),
        P("The literature survey of this batch found one gap: the surveyed models are evaluated on single-modality structured data, and nothing fuses a scanned report with the vitals while showing the reasons for the decision. "
          f"ATHENA closes that gap as a working pipeline and measures what fusion is worth on its data. With the same classifier, vitals alone reach {v['vit']} accuracy, the report alone {v['rep']} and the fused record {v['fused']}, "
          f"a gain of {v['gain_v']} points over vitals and {v['gain_r']} over the report. This is a property of how the synthetic labels were built as much as of the model, and it must be read that way, but it is the "
          "measurement the single-modality studies in the survey cannot make."),
        P(f"A second contribution is negative and easy to overlook: the same code shows that a linear baseline ({v['lr']}) beats the shipped XGBoost ({v['xgb']} uncalibrated), because the synthetic labels come from an additive severity score, and that the exact accuracy of any model "
          f"is capped near {v['ceil']} by the label noise. Reporting this is part of the method."),
        H2("2.5 Where this work is weaker than the base paper"),
        B("No real patient data. The base paper uses real records and an external validation set; ATHENA's figures describe how well a model recovers a known rule.",
          f"A narrower model study: no hyper-parameter search, eight classifiers instead of {b['algorithms']}, no significance tests.",
          "No medical language model. The batch abstract named BioBERT; the report reader is a lexicon, and LIME, RAG and multi-agent orchestration were not built.",
          "The comparison with the paper is therefore indicative at most: different task, different classes, different data."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The work makes the following contributions."),
        N(f"**A working triage pipeline.** A PDF or scanned report is read (text layer, or local RapidOCR for images), parsed into 22 clinical flags and 6 laboratory flags with negation handling, fused with eight vitals into {F.N_FEATURES} inputs, and turned into a priority from 1 to 5, a risk level and a confidence.",
          f"**A calibrated, explained decision.** XGBoost with isotonic calibration (ECE {v['ece0']} to {v['ece1']}) gives the priority; per-patient SHAP lists the strongest drivers, strongest first, next to every decision.",
          f"**A clinician-in-the-loop record.** Accept or change with a reason, stored with the case and the model's original suggestion; the queue reorders by priority then arrival; a triage-summary PDF can be downloaded.",
          f"**A measured fusion gain.** On the synthetic hold-out, fused inputs reach {v['fused']} exact accuracy against {v['vit']} for vitals only and {v['rep']} for the report only.",
          f"**An honest evaluation.** Eight-model comparison, 5-fold and five-seed stability, a noise ceiling of {v['ceil']}, calibration, confidence-coverage, under- and over-triage, dropped-report robustness, global SHAP, and a 40-fragment stress test of the reader.",
          f"**Measured cost per patient.** Median {v['lat_pdf']} ms for a PDF report and {v['lat_scan']} s for a scanned image, from upload to priority, over HTTP on a CPU-only machine.",
          f"**Reproducible tooling.** Seeded data generator, training, evaluation, experiment, latency and screenshot scripts, {F.PYTEST_TOTAL} automated tests ({F.PYTEST_PASSED} passing, 1 documented expected failure) and {F.SMOKE_TOTAL} smoke checks; every figure in the documents is generated from stored JSON."),
        P("None of these contributions is a new algorithm; they are integration, measurement and honest reporting around standard components. All model figures are on seeded synthetic data."),
    ]


# ---------------------------------------------------------------- document 10: scope and limitations
def scope_blocks():
    return [
        H2("1.1 What is in scope"),
        B("Reading a PDF or PNG/JPG report of up to 15 MB: symptoms, findings, history and six laboratory values, each kept with the page it came from.",
          "Entering eight vitals (age, heart rate, systolic and diastolic pressure, SpO2, temperature, respiratory rate, arrival mode) and fusing them with the report flags.",
          "Assigning a priority from 1 (Critical) to 5 (Non-urgent), a risk level (High, Moderate, Low), a calibrated confidence and a per-patient SHAP explanation.",
          "Accepting or changing the priority with a reason, a live queue ordered by priority then arrival, a performance page and a triage-summary PDF.",
          "Training and evaluating the model offline on a seeded synthetic data set, and measuring accuracy, calibration, robustness, reader quality and processing time on one machine."),
        H2("1.2 What is out of scope"),
        TAB("Items deliberately not covered", ["Item", "Why it is out", "Where it appears"],
            [["Training or testing on real patient records", "No real triage data set was obtained; the Kaggle download script exists but was never run", "Future scope"],
             ["A medical language model (BioBERT) for extraction", "A rule-based lexicon with negation was used; no model download or GPU", "Future scope"],
             ["RAG, multi-agent orchestration, LIME", "Named in the batch abstract; not built", "Future scope"],
             ["Risk models for six diseases (diabetes, heart, CKD, breast cancer, liver, sepsis)", "Only the five-level triage target was built", "Future scope"],
             ["MongoDB, Node.js and Flask services", "SQLite, FastAPI and a React single-page app were used instead", "Chapter 5"],
             ["Hospital integration (HL7, FHIR, EHR feeds, bedside monitors)", "Vitals are typed by the user", "Future scope"],
             ["Clinical validation, regulatory review, user study", "Decision support for a demonstration; no clinician took part", "Limitations"],
             ["Production security (TLS, rate limiting, secret management, audit)", "Local demonstration service", "Limitations"],
             ["Adversarial inputs and large-scale load testing", "Not attempted", "Limitations"]],
            widths=[2.4, 3.0, 1.1], align=["l", "l", "l"], size=9.5),
    ]


def assumption_blocks():
    return [
        P("The results and the design rest on the following assumptions."),
        B("The synthetic generator's seven archetypes and its severity rule are a stand-in for clinical triage. The recorded priority in the data is that rule plus noise, not a clinician's decision.",
          "Eight vitals and 28 report flags are enough to describe a patient at the door; real triage also uses the chief complaint wording, pain scores, mental status and the nurse's overall impression.",
          "A report finding that is not mentioned is absent (flag 0). This is the base paper's rule and ATHENA's, and it is wrong whenever the report is silent about something present.",
          "Clinical terms in a report appear in the lexicon's forms (including common abbreviations and OCR run-ons) and negation precedes the term within 45 characters in the same clause.",
          "Reference ranges for the six laboratory values are fixed adult values and do not depend on age, sex or units other than those the lexicon expects.",
          "The service is run locally by a trusted operator; there is no hostile client, and the demo accounts are the only users.",
          "A clinician reviews every priority before it is acted on; the system never replaces that review."),
    ]


def limitation_blocks():
    v = _v()
    return [
        H2("Data and model limitations"),
        B(f"**All model results are on synthetic data.** The {v['acc']} exact accuracy measures how well XGBoost recovers a known additive rule from 3,840 simulated cases; it says nothing about agreement with clinicians. A noise ceiling of {v['ceil']} caps exact accuracy for any model, and the shipped split (seed 7307) is a below-average split: five other seeds give {v['seed_mean']} on average (sd {v['seed_sd']} points).",
          f"**The sickest patients are under-triaged most often.** Recall for priority 1 is {v['r1']} and for priority 2 {v['r2']}; for the combined high-risk group (P1 and P2) recall is {v['hr_rec']} at argmax with precision {v['hr_prec']}. Overall {v['under']} of cases get a less urgent priority than recorded and {v['over']} a more urgent one; {v['p1_miss']} of {v['p1_n']} priority-1 cases were placed at priority 3 or lower urgency, none at 4 or 5.",
          f"**A linear model beats the shipped model on this data.** Logistic regression scores {v['lr']} against {v['xgb']} for uncalibrated XGBoost on the same split, because the labels come from an additive score. XGBoost was kept for SHAP tree explanations and calibration, not because it won.",
          f"**Calibration improves only modestly.** Expected calibration error falls from {v['ece0']} to {v['ece1']}; the 0.8 to 0.9 confidence bin is over-confident (66% observed accuracy), so a confidence figure must not be read as a probability of being right.",
          f"**Missing report findings are costly.** If 10% of positive report flags are dropped, accuracy falls to {v['rd10']}; at 20% to {v['rd20']}; with no report at all to {v['rd0']} (within one level {v['rd_none_w1']})."),
        H2("Report-reader limitations"),
        B(f"**Perfect scores on the samples are not a result.** The 12 generated sample reports are read exactly ({v['read_exact']} of 12, precision and recall 100%) because they were written with the lexicon in view.",
          f"**On 40 hand-written fragments** the reader reaches precision {v['rd_prec']} and recall {v['rd_rec']}, with {v['rd_exact']} fragments read exactly. Paraphrases outside the lexicon (\"cannot catch his breath\", \"crushing pain in the centre of the chest\") reach only {v['para_rec']} recall; the fragments were written by the developers, so this is not independent clinical text.",
          f"**Negation is the weakest category** (precision {v['neg_prec']} on the stress set): \"Afebrile\" is read as fever, \"Chest pain: absent\" still flags chest pain, \"denies syncope but reports chest tightness\" drops the chest pain because the 45-character window ignores \"but\" (one expected-failure test records this), and \"haematemesis\" also triggers vomiting.",
          "**OCR quality is untested on real scans.** Only four generated PNG scans were read; handwriting, stamps, tables, multi-column layouts and low-resolution phone photographs were not tried. Split words from OCR (\"vomit ing\") are missed.",
          "**The lexicon is English-only and fixed**: 22 flags and six laboratory tests, with adult reference ranges."),
        H2("System and security limitations"),
        B("**Demo-grade security.** The JWT secret defaults to `dev-secret-change-me` when `JWT_SECRET` is not set (PyJWT warns that the key is 22 bytes), there is no HTTPS, no rate limiting, CORS is fixed to localhost origins, and the two demo passwords are seeded. Passwords are bcrypt-hashed and every patient route needs a token.",
          "**No audit beyond overrides.** Who viewed or downloaded what is not logged.",
          "**SQLite and one process.** No concurrency, no migrations, no backup; the performance page's live averages come from this one database.",
          "**Vitals are typed.** There is no feed from a monitor, and the validation ranges (for example SpO2 50 to 100) are permissive.",
          f"**Latency is measured on one CPU-only machine**: scanned images take about {v['lat_ocr']} s to read, PDFs about {v['lat_pdfx']} ms."),
        H2("Evaluation limitations"),
        B("One synthetic data set from one generator; no real hold-out; no significance tests; no confidence intervals beyond the five-seed and five-fold spread.",
          "The comparison with the base paper is indicative only: it diagnoses ICD-10 classes on real records, ATHENA assigns five priorities on synthetic ones.",
          "No clinician took part: no usability study, no inter-rater comparison with nurses, no prospective trial."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured and are therefore stated as gaps, not as results."),
        B("Agreement with clinician-assigned priority on real patients (objective 6 is met only against the synthetic recorded priority).",
          "Reading accuracy on real scanned reports of varied quality, languages and layouts, or against a second reader.",
          "Performance on any real triage data set, including the Kaggle set the download script targets (the script was never run and its licence is not stated).",
          "Usability, workload and time saved for nurses, and the rate at which clinicians change the model's priority (the performance page can show it, but no clinician used the system).",
          "Behaviour under concurrent users, large queues, long uptime and database growth.",
          "Memory and energy use of the OCR engine and the model.",
          "Robustness to adversarial or deliberately misleading reports, and security testing beyond the checks in Chapter 7.",
          "A fresh-machine run of `setup.bat` and of the Kaggle download script; neither was tested in this documentation run.",
          "Statistical significance of differences between the eight models."),
    ]


# ---------------------------------------------------------------- document 12: walkthroughs and decisions
def walkthrough_blocks():
    v = _v()
    return [
        P("This section walks through the code that carries the design. The listings are copied from the repository at the state in which the results were measured."),
        H2("3.1 Reading a sentence: lexicon match and negation"),
        CODE(src("backend/app/services/extract.py", 39, 39), 8.5),
        CODE(src("backend/app/services/extract.py", 139, 152), 8.5),
        P("`NEGATION` matches a negating word followed by at most 45 characters up to the end of the text before the match. `parse` tests each of the 22 clinical flags in turn against the sentence; the first match is kept unless the text before it ends inside a negation window, in which case the flag stays 0. "
          "A brain bleed is excluded from the `bleeding` symptom so that it is read as the finding `ct_hemorrhage`. Each accepted item stores its text, its category and the page, which is how the interface shows `p.1` next to a finding. "
          f"The window is a deliberate simplification: it needs no parser and handles \"denies chest pain\" and \"no fever\", but it also swallows what follows \"but\" in the same clause, a defect the stress test records (negation precision {v['neg_prec']})."),
        H2("3.2 One patient representation"),
        CODE(src("backend/app/services/features.py", 76, 87), 8.5),
        P("`fuse` builds the dictionary of 36 inputs in the exact column order of the model: eight vitals, with the arrival mode coded 0, 1 or 2 and an unknown mode defaulting to walk-in, then 28 flags set to 1 if present and 0 otherwise. "
          "Because the order is fixed in one place (`FEATURES`), training, inference and the explanation use the same columns, and a report that mentions nothing gives all-zero flags rather than an error."),
        H2("3.3 Priority, confidence and explanation"),
        CODE(src("backend/app/services/triage.py", 35, 62), 8.5),
        P("The calibrated classifier returns five probabilities and the priority is the arg-max plus one. SHAP's `TreeExplainer` works on the underlying boosted trees and returns, for the chosen class, one contribution per input; they are sorted by absolute value. "
          "An absent flag with a negligible contribution (below 0.15) is hidden, since a long list of reasons that are not there would bury the useful ones. The function also returns the elapsed time, which feeds the performance page. "
          f"The explainer's cold start is several seconds, so the application warms it when the server starts; the measured median for creating a patient over HTTP is {v['lat_create']} ms."),
        H2("3.4 The clinician's decision"),
        CODE(src("backend/app/routes/api.py", 186, 200), 8.5),
        P("The override route decides the action from the numbers: the same priority is an acceptance, a different one is a change, and a change without a reason is refused with 422. The row written to `overrides` keeps the old and new priority, the clinician's name and the reason; "
          "the patient's `priority` and risk level update while `model_priority` keeps the model's original suggestion, so the performance page can report how often clinicians kept it. The queue is sorted by priority and arrival time on the next request."),
    ]


def decision_blocks():
    v = _v()
    rows = [["Report reading", "PDF text layer first, RapidOCR only for images and image-only pages", "Cloud multimodal model; BioBERT; PaddleOCR proper", "Runs offline with no key or model download; PDFs are instant. Cost: a lexicon misses paraphrases (recall " + v["para_rec"] + " on them). The Gemini path was dropped by choice."],
            ["Extraction", "Regex lexicon with a 45-character negation window", "Medical language model", "Transparent, testable, no GPU. Cost: the defects listed under limitations; BioBERT is future work."],
            ["Representation", "36 inputs: 8 vitals + 28 flags", "Embeddings of the report text", "Every input has a name a clinician can read, so SHAP reasons are readable."],
            ["Model", "XGBoost, 220 trees, depth 4", "Logistic regression; MLP; random forest", f"Fast ({F.TRAIN_SEC} s training), handles interactions, supports TreeExplainer. Cost: logistic regression is at least as accurate here ({v['lr']} against {v['xgb']})."],
            ["Confidence", "Isotonic calibration on a separate 20% split", "Raw probabilities; temperature scaling", f"Non-parametric and standard for boosted trees. Cost: only a small gain (ECE {v['ece0']} to {v['ece1']}) and a coarse step function."],
            ["Explanation", "Per-patient SHAP on the tree model", "LIME; global importance only", "Exact and fast for trees; fits beside each decision. LIME was not built."],
            ["Risk level", "P1-2 High, P3 Moderate, P4-5 Low", "A separate risk model", "A fixed mapping from priority keeps the two always consistent."],
            ["Human decision", "Accept or change, reason required for a change", "Automatic assignment", "Keeps the clinician responsible and gives feedback data."],
            ["Backend and storage", "FastAPI, SQLAlchemy, SQLite", "Flask, Node.js, MongoDB (batch brief)", "One Python process, typed requests, no database server to install. Cost: single-user scale."],
            ["Frontend", "React 19 + Vite single-page app with a shared design kit", "Server-rendered pages", "Fast queue and result views, dark mode, drawer navigation on small screens."],
            ["Training data", "Seeded synthetic generator, labelled as sample data in the UI", "Waiting for a real data set", "The product runs out of the box and is honest about it. Cost: every accuracy figure is about a rule, not about patients."],
            ["Security", "bcrypt, JWT bearer, input range checks, upload cap, path-traversal guard", "Full production hardening", "Enough for a demonstration. Cost: the gaps listed under limitations."]]
    return [
        P("Each design decision below was taken for a reason and has a cost; the table states both."),
        TAB("Implementation decisions and their reasons", ["Decision", "Chosen", "Alternative", "Reason and consequence"], rows, widths=[1.0, 1.5, 1.3, 2.7], align=["l", "l", "l", "l"], size=8.5),
        P("Two decisions were forced by the environment rather than chosen. The batch brief named Node.js, Flask and MongoDB; the product was built as a single Python service with SQLite so that it runs with one command on a Windows laptop. "
          "The measurements were made on a CPU-only machine, which is why scanned-image reading (about " + v["lat_ocr"] + " s) is the slowest step and why absolute timings are reported as indicative."),
    ]


# ---------------------------------------------------------------- chapter 9 and 10
def conclusion_blocks():
    v = _v()
    b = [
        H2("9.1 Summary of the work"),
        P("This project built ATHENA, a decision-support tool for emergency departments. It reads a scanned clinical report (PDF text layer or local OCR), parses symptoms, findings, history and six laboratory values with a lexicon that handles negation, "
          f"fuses them with eight vitals into {F.N_FEATURES} inputs, and uses an isotonic-calibrated XGBoost to give a triage priority from 1 to 5, a risk level and a calibrated confidence. Per-patient SHAP shows the strongest drivers, "
          "a clinician accepts or changes the priority with a reason, and the queue, the performance page and a summary PDF follow from that. "
          f"The system was measured on a seeded synthetic data set ({F.ROWS:,} cases, {F.N_TEST:,} held out), compared with seven other models, probed for calibration, robustness and safety, and verified with {F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks."),
        H2("9.2 Objectives achieved"),
        TAB("The six objectives of the batch against the outcome", ["#", "Objective", "Outcome"],
            [["1", "OCR stage for scanned reports", "Met: PDF text layer plus local RapidOCR (PaddleOCR-family models on ONNX Runtime); 12 of 12 generated samples read exactly; real scans untested"],
             ["2", "Medical language model to extract symptoms, findings, history", f"Partly met: a lexicon with negation, not BioBERT; precision {v['rd_prec']} and recall {v['rd_rec']} on 40 hand-written fragments"],
             ["3", "Fuse text features with vitals in one representation", f"Met: {F.N_FEATURES} inputs; fused {v['fused']} against {v['vit']} (vitals) and {v['rep']} (report)"],
             ["4", "Model assigns risk level and priority", f"Met on synthetic labels: {v['acc']} exact, {v['w1']} within one level, macro F1 {v['f1']}"],
             ["5", "Explanation layer showing what drove the priority", "Met: per-patient SHAP, strongest factor first, with the page each finding came from"],
             ["6", "Accuracy against clinician-assigned priority; time per patient", f"Partly met: accuracy against the synthetic recorded priority only; median {v['lat_pdf']} ms for a PDF and {v['lat_scan']} s for a scan, end to end over HTTP"]],
            widths=[0.35, 2.3, 3.9], align=["c", "l", "l"], size=9.5),
        H2("9.3 Key findings"),
        N(f"**Fusing the report with the vitals pays on this data.** Exact accuracy is {v['fused']} fused, {v['rep']} report only and {v['vit']} vitals only; within one level the fused model is right {F.pct(F.ABL['Fused (36)']['within_one'])} of the time.",
          f"**The shipped model recovers its rule well but not perfectly.** {v['acc']} exact, {v['w1']} within one level, macro F1 {v['f1']}, quadratic weighted kappa {v['qwk']}, Top-2 {v['top2']}; the label noise caps any model near {v['ceil']}.",
          f"**The sickest patients are the weak point.** Priority 1 recall is {v['r1']} and high-risk (P1 and P2) recall {v['hr_rec']}. Flagging high risk when P(1) + P(2) is at least 0.4 would raise recall to {v['hr_rec4']} at precision {v['hr_prec4']}; this threshold is not implemented.",
          f"**A simple baseline matches the chosen model.** Logistic regression {v['lr']}, MLP {v['mlp']}, XGBoost {v['xgb']} (uncalibrated); five-fold XGBoost accuracy is {v['cv_xgb']}.",
          f"**Confidence is informative but coarse.** Calibration lowers ECE only from {v['ece0']} to {v['ece1']}; keeping predictions with confidence of at least 0.85 covers {v['t85_cov']} of cases at {v['t85_acc']} accuracy, and 0.9 covers {v['t90_cov']} at {v['t90_acc']}.",
          f"**The reader is the fragile stage.** 100% on generated samples, recall {v['rd_rec']} on hand-written fragments, and the triage model loses accuracy quickly when findings are dropped ({v['rd10']} at 10%, {v['rd20']} at 20%, {v['rd0']} with no report).",
          f"**Against the base paper** ATHENA shares the ideas of ranked output, a 0.85 confidence threshold, SHAP and absent-equals-zero, but the task (five priorities against {F.BASE_PAPER_RESULTS['classes']} ICD-10 classes) and the data (synthetic against {F.BASE_PAPER_RESULTS['cases']:,} real cases) differ, so no accuracy comparison is claimed."),
        H2("9.4 Practical applications"),
        B("A teaching and prototyping platform for decision support that reads documents, fuses them with measurements, explains itself and records the clinician's decision.",
          "A reference design for triage software: queue ordered by priority then arrival, reasons beside each decision, override log, summary PDF.",
          "A starting point for training on real triage records once such a data set is available (Chapter 10), with the evaluation scripts already in place.",
          "A template for reporting a clinical-AI result honestly: data source in every sentence, baselines, ceiling, calibration, safety direction and robustness."),
        H2("9.5 Known limitations"),
        P(f"All model results are on synthetic data; priority-1 recall is {v['r1']} and under-triage {v['under']}; a linear model is as good as the shipped one; the reader is a lexicon with known negation and OCR defects; "
          "BioBERT, RAG, multi-agent orchestration, LIME, MongoDB and the six disease-risk models were not built; security is demo-grade; and no clinician used the system. Chapter 8 and the Scope and Limitations document give the full list."),
        H2("9.6 Lessons learned"),
        B("Write the data a number was measured on in the same sentence as the number; a synthetic 69% and a real-hospital 69% are different claims.",
          "Run the simple baseline first. Logistic regression beating XGBoost would have stayed hidden without a comparison table.",
          "Work out the noise ceiling of a synthetic data set before celebrating or lamenting an accuracy.",
          "Test the reader on text it was not written for; the generated samples gave 100% and the first honest stress test gave " + v["rd_rec"] + " recall.",
          "Keep experiments scripted and their output stored as JSON, so every number in the documents can be traced and regenerated."),
    ]
    return b


def future_blocks():
    v = _v()
    return [
        H2("10.1 Improvements to the existing system"),
        B("**Train and test on real triage records.** The Kaggle \"Hospital Triage and Patient History Data\" set is wired to `scripts/download_data.py` (never run; licence not stated); MIMIC-IV-ED is a public benchmark but needs credentialed access " + c("xie") + ". Report agreement with recorded triage levels, per-level recall and calibration on a patient-disjoint split.",
          f"**Add the high-risk safeguard.** Raise a High-risk flag when P(1) + P(2) is at least 0.4: on the synthetic hold-out this raises P1-P2 recall from {v['hr_rec']} to {v['hr_rec4']} at precision {v['hr_prec4']} (against {v['hr_prec']}); choose the threshold on validation data with clinicians.",
          "**Improve negation scope and OCR tolerance.** Stop the window at \"but\" and \"however\", handle post-positioned negation (\"absent\") and prefixes (\"afebrile\"), join split OCR words, and fix the `emesis` match inside `haematemesis`.",
          f"**Better calibration.** Compare temperature scaling and merged bins with isotonic regression; the 0.8 to 0.9 confidence bin is over-confident today (ECE {v['ece1']}).",
          "**Replace the lexicon by a clinical language model** (BioBERT-class " + c("biobert") + ") for extraction, keeping the lexicon as a fallback and the stress set as the regression test.",
          "**Strengthen security.** Require `JWT_SECRET`, add HTTPS, rate limiting, audit logging of views and downloads, and remove the seeded passwords."),
        H2("10.2 Additional features"),
        B("**Chief-complaint and pain-score inputs**, which real triage relies on, and free-text notes next to the scan.",
          "**Retrieval of guidance (RAG)** so that a priority comes with the relevant protocol passage, and **multi-agent checks** (for example a second reader that audits the first) as named in the batch abstract.",
          "**LIME or counterfactual explanations** next to SHAP, and an explanation of why a finding was *not* read.",
          "**Disease-risk modules** for diabetes, heart disease, chronic kidney disease, breast cancer, liver disease and sepsis, as named in the batch brief, each with its own evaluation.",
          "**Trend views** for repeated vitals and an alert when a waiting patient's risk changes."),
        H2("10.3 Scalability and deployment"),
        B(f"Move from SQLite to a server database, run several API workers behind a reverse proxy, and cache the OCR engine per worker; creating a patient already takes a median {v['lat_create']} ms, so reading scanned images (about {v['lat_ocr']} s each on this CPU) is the cost that needs a worker pool or a GPU.",
          "Integrate with hospital systems through HL7 or FHIR and a monitor feed instead of typed vitals.",
          "Containerise the service, publish the model bundle with its metrics and monitor the distribution of inputs and of clinician overrides in production, retraining when they drift."),
        H2("10.4 Further research"),
        B("A prospective, clinician-in-the-loop study: how often is the suggestion kept, and does the explanation change the clinician's decision?",
          "Fairness checks across age and arrival mode on real data, and measurement of under-triage by subgroup.",
          "Comparison of tree models, linear models and small networks on real triage records, following the tabular-data evidence " + c("grinsztajn") + ".",
          "Top-k and abstention policies: when the model should refuse to suggest a priority, building on the confidence-coverage curve measured here.",
          "Reporting to a clinical-AI standard such as TRIPOD+AI " + c("tripod") + " once real data are used."),
        H2("10.5 Suggested order of work"),
        TAB("Future work ranked by value and effort", ["Priority", "Item", "Effort", "Why first"],
            [["1", "Real triage data set and patient-disjoint evaluation", "Medium", "Turns every figure from a statement about a rule into one about patients"],
             ["2", "High-risk threshold and clinician review of it", "Small", f"Recall of P1-P2 {v['hr_rec']} to {v['hr_rec4']} on the synthetic hold-out"],
             ["3", "Negation, abbreviation and OCR fixes with a larger independent stress set", "Small to medium", f"Reader recall is {v['rd_rec']} on hand-written fragments"],
             ["4", "Security hardening and audit log", "Small to medium", "Closes the demo shortcuts that block any real use"],
             ["5", "Clinical language model for extraction", "Large", "Addresses paraphrases the lexicon cannot read"],
             ["6", "User study and prospective evaluation", "Large", "The only way to show the tool helps a clinician"]],
            widths=[0.7, 2.8, 1.1, 2.0], align=["c", "l", "l", "l"], size=9.5),
    ]


def _future_trim(bl):
    if not F.REPORT:
        return bl
    out, skip = [], False
    for x in bl:
        if x[0] == "h2" and x[1].startswith("10.5"):
            skip = True
            continue
        if not skip:
            out.append(x)
    return out


def chapter9_blocks():
    return [H1("CHAPTER 9: CONCLUSION")] + conclusion_blocks()


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + _future_trim(future_blocks())
