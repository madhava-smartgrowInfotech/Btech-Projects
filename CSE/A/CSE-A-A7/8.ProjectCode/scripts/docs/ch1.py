"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R


def _key(b):
    """First piece of text of a block, used to find blocks to drop or replace in report mode."""
    v = b[1]
    return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming. drop: block-text prefixes to remove; drop_sections: heading prefixes whose whole section
    (up to the next heading of the same or higher level) is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        k = _key(b)
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    b = _full()
    if not F.REPORT:
        return b
    return trim(
        b,
        drop=("Triage is only one step in a longer path", "The motivation for this project is therefore practical"),
        replace={
            "**Both inputs together.**": P("The work is needed because triage models built on structured fields cannot see what is written only in a scanned report; because a priority "
                                           "without reasons is hard to accept at the bedside; and because a model trained on generated data can look reasonable while saying nothing about "
                                           "real patients, so every figure must state the data behind it."),
            "Three objectives differ from the original wording": P("Three objectives differ from the original wording. Objective 1 asks for deep-learning OCR; the implementation uses RapidOCR, which runs "
                                                                   "PaddleOCR-family models through ONNX Runtime, and reads the text layer of a PDF directly. Objective 2 asks for a medical language model; "
                                                                   "the reader is a rule-based lexicon with negation handling, so this objective is only partly met. Objective 6 asks for accuracy against "
                                                                   "clinician-assigned priority; no clinician-labelled data was available, so accuracy is measured against the recorded priority of a "
                                                                   "synthetic dataset."),
            "**Chapter 2** surveys": P("The report continues with the literature survey (Chapter 2), the feasibility study and requirements (Chapters 3 and 4), the design (Chapter 5), the methodology and "
                                       "implementation (Chapter 6), testing (Chapter 7), results with the comparison against the base paper (Chapter 8), the conclusion and future scope "
                                       "(Chapters 9 and 10), the references and three appendices."),
        },
    )


def _full():
    base = R["base"]
    sh = F.SHIPPED
    obj_rows = [
        ["1", "Build an OCR stage that converts scanned medical reports into machine-readable clinical text",
         "PDF text layer read with pypdf; image scans and image-only pages read by RapidOCR (ONNX, local, no network). Met."],
        ["2", "Apply a medical language model to extract symptoms, findings and history from that text",
         f"Rule-based lexicon of 22 flags with negation handling and six lab parsers; no BioBERT. Partly met: precision {F.pct(F.READ['precision'], 0)} and recall {F.pct(F.READ['recall'], 0)} "
         f"on the 12 generated samples, {F.pct(F.STRESS['recall'], 1)} recall on 40 hand-written fragments."],
        ["3", "Combine text-derived features with tabular vitals in a single patient representation",
         "Fused record of 36 inputs: 8 vitals and 28 report flags (11 symptom, 5 finding, 6 history, 6 lab). Met."],
        ["4", "Train a model that assigns a clinical risk level and a triage priority to each patient",
         f"XGBoost with isotonic calibration, priority 1 to 5, risk High / Moderate / Low, trained on synthetic data: accuracy {F.pct(F.ACC)} on the synthetic hold-out. Met on synthetic labels."],
        ["5", "Add an explainability layer that shows which findings drove the assigned priority",
         "Per-patient SHAP contributions, strongest first, beside the decision on the result screen. Met."],
        ["6", "Evaluate triage accuracy against clinician-assigned priority and measure processing time per patient",
         f"Accuracy measured against the recorded priority of the synthetic data only; time per patient measured (PDF flow {F.lat('flow_pdf_then_triage'):.0f} ms, "
         f"scan flow {F.lat('flow_scan_then_triage'):.0f} ms, HTTP medians). Partly met."],
    ]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that "
          "was actually delivered, its contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report. "
          "One fact shapes everything that follows and is therefore stated at the start: the triage model was trained and evaluated on a seeded synthetic dataset, because no real patient "
          "records were available to the team. Every accuracy figure in this report describes that dataset."),

        H2("1.1 Domain"),
        P("An emergency department receives patients in no useful order. Someone with a sprained ankle may arrive just before someone with a heart attack, and the department has to "
          "decide within minutes who is seen first. That decision is called triage. Most departments use a five-level scale such as the Emergency Severity Index "
          f"[{R['esi']}], in which level 1 is a patient who needs immediate life-saving action and level 5 is a patient who can safely wait. The nurse on duty assigns the level from the "
          "patient's vitals (heart rate, blood pressure, oxygen saturation, temperature, respiratory rate), the complaint, and whatever the patient or the paperwork says about their "
          "history."),
        P("The paperwork is the difficult part. Patients arrive with referral letters, discharge summaries and laboratory printouts, many of them scanned or photographed, and the "
          "findings that matter (an ST elevation on an ECG, a raised troponin, a prior stroke, an anticoagulant) are written in free text. Reading them takes time that a busy "
          "triage desk does not have, and when they are not read the priority is set from the vitals and the first impression alone."),
        P("This project sits in the field of clinical decision support and medical informatics. A decision support system does not decide; it reads the available data, "
          "proposes a priority, and shows the reasons so that the clinician can accept it or change it. The base paper of the project "
          f"[{base}] is a large comparison of machine-learning classifiers for exactly this kind of support, applied to the diagnosis of disease categories from incomplete medical "
          "histories."),

        H2("1.2 Background and Motivation"),
        P(f"Triage by scale is known to be uneven. A systematic review of triage performance [{R['hinson']}] found that the three most studied scales behave alike, that sensitivity "
          "for patients who later turn out to be critically ill is below 80 % in many studies, and that a substantial proportion of patients who die or become critically ill "
          "were not designated as high acuity at triage. The same review points to room for improvement in interrater reliability, which is what the batch problem statement means when "
          "it calls triage subjective."),
        P(f"Machine learning has been applied to the problem for several years. Models trained on triage data predict hospital admission [{R['hong']}], critical care and emergency "
          f"procedures [{R['levin']}], [{R['raita']}], and public benchmarks now exist for such tasks [{R['xie']}]. A review of intelligent triage systems [{R['fernandes']}] concludes "
          "that the contributions range from improved triage to prediction of critical care, but that many studies stop before an implementation phase and that the effect on quality "
          "of care has still to be assessed. Almost all of this work uses structured fields: vitals, an age, a coded complaint, a few history flags. What is written only in a "
          "scanned report does not reach the model."),
        P("Two further requirements decide whether such a tool is used at all. The first is explanation. A clinician will not act on a priority that cannot be explained, and a "
          f"model-agnostic attribution method such as SHAP [{R['shap']}], [{R['treeshap']}] makes it possible to show, for one patient, which findings pushed the priority up or down. "
          f"The second is a trustworthy confidence. A score of 0.9 should mean that about nine such predictions in ten are right, and calibration methods [{R['zadrozny']}], [{R['guo']}] "
          "exist to make that so."),
        P("Triage is only one step in a longer path, but it is the step where minutes matter most. A tool that reads the report while the nurse enters the vitals, proposes a priority "
          "with its reasons, and records whether the clinician agreed, could shorten that step and also create a record of how often the model and the clinician disagree. That is "
          "the motivation for ATHENA."),
        P("The motivation for this project is therefore practical: build one working pipeline that takes a scanned report and the vitals, produces an explainable and calibrated "
          "priority, lets the clinician override it, and measures what the whole path costs in time. A second motivation is honesty about evaluation. Reported accuracies in this "
          "field come from different data, tasks and splits, so every number in this report states its data and its protocol."),

        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of current practice:"),
        B("triage decisions are subjective and vary with the experience of the staff on duty;",
          "existing systems analyse only structured fields and ignore scanned reports and clinical narrative;",
          "predictions delivered without justification are not accepted into a clinical workflow;",
          "delay in prioritising a critical patient directly worsens outcomes."),
        P("The problem addressed here is to build and evaluate a multi-source triage assistant that reads a scanned report and the vitals, assigns an explainable priority and risk level, "
          "and supports the clinician rather than replacing them."),

        H2("1.4 Need for the Work"),
        B("**Both inputs together.** The literature survey of this project found that triage models work on structured fields, that the base paper works on typed symptom indicators, "
          "and that no surveyed work fuses a scanned report with the vitals. This report builds that fusion and measures what it adds: on the synthetic data, vitals alone give "
          f"{F.pct(F.ABL['Vitals only (8)']['accuracy'])} accuracy, the report alone {F.pct(F.ABL['Report only (28)']['accuracy'])} and the fused record {F.pct(F.ABL['Fused (36)']['accuracy'])}.",
          "**Reasons beside the decision.** A priority is shown with the factors behind it for that one patient, and the clinician's accept-or-change decision is stored with a reason, "
          "so disagreement can be counted.",
          "**Honest evaluation.** A model trained on generated data can look reasonable and say nothing about real patients. The project states this limit on the page that shows the "
          "numbers, and adds experiments that expose weaknesses: per-priority recall, safety counts, robustness to a report that is read badly, and a stress test of the reader.",
          "**A tool a reviewer can run.** An intake screen, a result screen, a live queue and a performance page make the system inspectable by people who do not read code."),

        H2("1.5 Objectives"),
        P("The six objectives set for the project, and what each became, are summarised in the table below. Chapter 8 returns to it with the measured outcome for each."),
        TAB("Project objectives and how each was addressed", ["No.", "Objective", "How it was addressed"], obj_rows, widths=[0.5, 2.5, 3.3], align=["c", "l", "l"], size=10),
        P("Three objectives differ from the original wording and the report says so plainly. Objective 1 asks for deep-learning OCR; the implementation uses RapidOCR, which runs "
          f"PaddleOCR-family models [{R['ppocr']}] through ONNX Runtime, and reads the text layer of a PDF directly when one exists. Objective 2 asks for a medical language model such as "
          f"BioBERT [{R['biobert']}]; the reader is a rule-based lexicon with negation handling, so this objective is only partly met. Objective 6 asks for accuracy against "
          "clinician-assigned priority; no clinician-labelled data was available, so accuracy is measured against the recorded priority of a synthetic dataset."),
        P("The abstract of the batch also mentions retrieval-augmented generation, a multi-agent architecture, LIME, MongoDB, a Node.js and Flask pair of services and risk models "
          "for six diseases. None of these was built; the product uses FastAPI, React and SQLite, and the report treats the others as future work."),

        H2("1.6 Scope"),
        P(f"{F.PRODUCT} consists of four parts:"),
        B("**Report reader**: PDF text layer or local OCR, a lexicon of 22 clinical flags with negation handling, six laboratory parsers with reference ranges, and the page number of every "
          "item found.",
          f"**Triage model**: the fused record of {F.N_FEATURES} inputs, an XGBoost classifier of 220 trees and depth 4, isotonic calibration on a separate split, risk level and a per-patient "
          "SHAP explanation.",
          "**Clinician workflow**: accept or change the priority with a stored reason, a live queue ordered by priority and then arrival, and a downloadable triage-summary PDF.",
          f"**Interfaces**: a FastAPI service on port {F.API_PORT} with 13 routes, SQLite storage of users, patients and overrides, JWT sign-in for a clinician and an administrator, and a "
          f"React 19 application on port {F.WEB_PORT} with landing, sign-in, new patient, result, queue and performance screens."),
        P("Out of scope are real patient data, integration with a hospital information system, retrieval-augmented generation, a medical language model, multi-agent orchestration, "
          "disease-specific risk models, audit-grade security, a user study with clinicians and any regulatory approval. The system is decision support: the treating clinician makes the final "
          "triage decision."),

        H2("1.7 Contributions"),
        N("A working pipeline that reads a scanned report, fuses it with the vitals and returns a calibrated priority with a per-patient explanation, a clinician override loop and a "
          f"live queue, tested by {F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks.",
          f"A measured effect of fusion on the synthetic data: {F.pct(F.ABL['Fused (36)']['accuracy'])} accuracy for the fused record against {F.pct(F.ABL['Vitals only (8)']['accuracy'])} for vitals alone, "
          f"with within-one-level agreement of {F.pct(F.W1)} and macro F1 {F.f3(F.MF1)} for the shipped model.",
          f"An honest evaluation that reports weaknesses: recall for priority 1 of {F.pct(F.REC[0])}, high-risk recall of {F.pct(F.SAFE['high_risk_recall'])}, a logistic-regression baseline that "
          f"scores {F.pct(F.COMP['Logistic regression']['accuracy'])}, a label-noise ceiling of {F.pct(F.CEILING, 2)}, and the defects found by a 40-fragment stress test of the reader.",
          f"Measured processing time: a PDF report is read and triaged in {F.lat('flow_pdf_then_triage'):.0f} ms and an image scan in {F.lat('flow_scan_then_triage') / 1000:.1f} s (HTTP medians on the development machine)."),

        H2("1.8 Limitations and Assumptions"),
        P("The conclusions of this report hold under the following limitations and assumptions."),
        B(f"The model is trained and tested on a seeded synthetic dataset of {F.ROWS:,} rows built from seven clinical archetypes and a hand-written severity rule. Accuracy measures recovery of "
          "that rule, not agreement with clinicians, and real hospital data would give different numbers.",
          f"The labels contain noise by design, so no model can exceed {F.pct(F.CEILING, 2)} exact accuracy on them; the shipped model reaches {F.pct(F.ACC)}.",
          f"Recall for the most urgent priority is low ({F.pct(F.REC[0])}), and the model places the sickest patients one level too low more often than any other group; a clinician must review "
          "every priority.",
          "The report reader is a rule-based lexicon. It is exact on the generated samples it was written with and weaker on wording it does not contain; it was not tested on real scans.",
          "Security is demonstration grade: a default signing secret unless one is configured, no HTTPS, no rate limiting, seeded demo accounts.",
          f"Timings were measured on one shared machine ({F.MACHINE}) and are indicative; no multi-user load, clinician usability study or prospective evaluation was done."),
        P("The base paper's task is the diagnosis of ICD-10 categories from real clinical records; ATHENA's task is five-level triage on synthetic records. Where this report compares the two "
          "it says that the tasks, the data and the conditions differ."),

        H2("1.9 Organisation of the Report"),
        B("**Chapter 2** surveys the literature, analyses the base paper and states the research gap.",
          "**Chapter 3** studies feasibility; **Chapter 4** analyses the existing system and the requirements of the proposed one.",
          "**Chapter 5** presents the system design: architecture, data flow diagrams, UML, entities, modules and screens.",
          "**Chapter 6** describes the methodology and the software implementation: data, report reading, fused record, model, API and security handling.",
          "**Chapter 7** reports system testing; **Chapter 8** reports results and output screens, with the comparison against the base paper.",
          "**Chapters 9 and 10** give the conclusion and the future scope, followed by the references and three appendices (important code, installation and user guide, additional screens)."),
    ]
