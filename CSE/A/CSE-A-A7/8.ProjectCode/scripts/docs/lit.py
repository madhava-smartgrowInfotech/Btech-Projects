"""Literature and framing data for the decks (Review 1, Review 2, final) and the IEEE paper.

Reference numbers match scripts/docs/refs.py (CITE keys). Cells quote only what the sources say; where a source was not retrieved or
gave no figure the cell says so.
"""
from .refs import CITE as R

BASE_PAPER_TITLE = ("Multidimensional Analysis of the Diagnostic Performance of Machine Learning Models in Disease Classification: "
                    "Implications for Clinical Decision Support Systems")
BASE_PAPER_VENUE = "M. Mlodawski, S. Deniziak, M. Plaza et al. - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Mlodawski et al. [{R['base']}] (base paper)", "2026", "19 classifiers, TOP-1 / TOP-3 ranking, SHAP + LIME, on incomplete real records",
     "1,655 cases, 87 ICD-10 classes; GB 84.74%, MLP 87.20%; text and tabular only"],
    [f"Fernandes et al. [{R['fernandes']}]", "2020", "Review of intelligent clinical decision support for ED triage",
     "Many studies lacked an implementation phase; impact on care still to be shown"],
    [f"Hinson et al. [{R['hinson']}]", "2019", "Systematic review of triage scale performance (CTAS, ESI, MTS)",
     "182 studies; sensitivity for critical illness below 80%; scales perform alike"],
    [f"Hong et al. [{R['hong']}]", "2018", "Logistic regression, XGBoost, deep nets for admission at triage",
     "560,486 visits; triage-only AUC about 0.87; adding history lifts to about 0.92"],
    [f"Levin et al. [{R['levin']}]", "2018", "Random-forest e-triage on vitals, complaint and history",
     "172,726 visits; AUC 0.73-0.92; matched or beat ESI; outcomes, not 5-level labels"],
    [f"Raita et al. [{R['raita']}]", "2019", "Lasso, forest, boosting, deep net on triage data",
     "135,470 visits; deep net AUC 0.86 vs 0.74 for an ESI model (critical care)"],
    [f"Xie et al. [{R['xie']}]", "2022", "Public MIMIC-IV-ED benchmark for triage prediction tasks",
     "Hospitalisation, critical outcome, reattendance; structured fields only"],
    [f"Cheng et al. [{R['cheng']}]", "2025", "Multi-agent LLM dynamic matching for triage under uncertainty",
     "Cited from title only; text-only agents, no scanned-report input"],
    [f"Anatolian Curr. Med. J. [{R['s_acmj']}]", "2025", "Prospective ESI vs Manchester triage, 6,000 patients each",
     "Process study in one Turkish hospital; no machine learning"],
    [f"Nepal single-centre study [{R['s_nepal']}]", "2024", "Questionnaire on triage knowledge of 284 patient attendants",
     "Public awareness only; no prediction or decision support"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Base paper [{R['base']}]", "19 classifiers, TOP-1/TOP-3, SHAP, LIME", "1,655 real cases, ICD-10", "GB 84.74%, MLP 87.20%", "Text/tabular only; no OCR"],
    [f"Fernandes [{R['fernandes']}]", "Review of ED triage CDSS", "many studies", "no pooled figure used", "Few deployed systems"],
    [f"Hinson [{R['hinson']}]", "Review of triage scales", "182 studies", "sens. below 80% for critical illness", "Scales, not ML"],
    [f"Hong [{R['hong']}]", "LR, XGBoost, deep nets", "560,486 ED visits", "AUC about 0.87 to 0.92", "Admission, not priority"],
    [f"Levin [{R['levin']}]", "Random-forest e-triage", "172,726 visits", "AUC 0.73-0.92", "Outcomes, not 5 levels"],
    [f"Raita [{R['raita']}]", "Lasso, RF, GBDT, DNN", "135,470 visits", "DNN AUC 0.86 vs 0.74", "Structured fields only"],
    [f"Xie [{R['xie']}]", "Public benchmark, ML models", "MIMIC-IV-ED", "task AUCs (not quoted)", "No scanned reports"],
    [f"Cheng [{R['cheng']}]", "Multi-agent LLM matching", "text vignettes", "not read in full", "No vitals fusion"],
]

OBJECTIVES = [
    "Build an OCR stage that converts scanned medical reports into machine-readable clinical text",
    "Apply a medical language model to extract symptoms, findings and history from that text",
    "Combine text-derived features with tabular vitals in a single patient representation",
    "Train a model that assigns a clinical risk level and a triage priority to each patient",
    "Add an explainability layer that shows which findings drove the assigned priority",
    "Evaluate triage accuracy against clinician-assigned priority and measure processing time per patient",
]

PROBLEM_STATEMENT = [
    "Triage decisions are subjective and vary with the experience of the staff on duty",
    "Existing systems analyse only structured fields and ignore scanned reports and clinical narrative",
    "Predictions delivered without justification are not accepted into a clinical workflow",
    "Delay in prioritising a critical patient directly worsens outcomes",
    "Need: a multi-source triage assistant that reads scanned reports, assigns an explainable risk level and supports the clinician",
]

EXISTING_SYSTEM = [
    "Manual triage on a five-level scale such as ESI, applied by the nurse on duty",
    "Machine-learning triage models trained on structured fields: vitals, complaint code, history",
    "Diagnostic classifiers on typed symptom checklists (the base paper, 19 algorithms)",
    "Text-only LLM agents that reason over a written case description",
    "Scanned reports are filed or typed in by hand and rarely reach any model",
]

LIMITATIONS_OF_EXISTING = [
    "Scale-based triage varies between nurses and shifts; critical illness is under-identified [" + str(R['hinson']) + "]",
    "Structured-field models cannot see what is only written in a scanned report [" + str(R['hong']) + "], [" + str(R['raita']) + "]",
    "Many intelligent triage systems were never implemented or evaluated in a workflow [" + str(R['fernandes']) + "]",
    "The base paper works on typed symptom indicators, not on scans, and reports no processing time [" + str(R['base']) + "]",
    "A bare prediction with no reasons is hard to accept at the bedside",
    "Reported accuracies come from different data and tasks, so they cannot be compared directly",
]

GAPS = [
    "The surveyed models are evaluated on single-modality structured data: no pipeline fuses a scanned report with the vitals",
    "Triage priority (five levels) is rarely the target; most work predicts admission, critical care or ICD-10 diagnoses [" + str(R['hong']) + "], [" + str(R['base']) + "]",
    "Explanations are usually global or offline; a per-patient reason shown next to the decision is missing in deployed designs",
    "Calibrated confidence and an accept-or-change record for the clinician are seldom reported together",
    "Processing time per patient, including report reading, is almost never measured",
]
