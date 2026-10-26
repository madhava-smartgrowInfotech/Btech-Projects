"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for ATHENA.

Requirement identifiers FR-1..FR-12 and NFR-1..NFR-11 are defined here (FR_IDS, NFR_IDS) and reused by Chapter 7 where each is tested.
"""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

_E2E_PDF = F.lat("flow_pdf_then_triage")
_E2E_SCAN = F.lat("flow_scan_then_triage")
_CREATE = F.lat("create_patient")
_OCR = F.lat("extract_scan_png")
_PDF = F.lat("extract_pdf")
_FUSED = F.ABL["Fused (36)"]["accuracy"]
_VIT = F.ABL["Vitals only (8)"]["accuracy"]

FR_IDS = ["FR-1", "FR-2", "FR-3", "FR-4", "FR-5", "FR-6", "FR-7", "FR-8", "FR-9", "FR-10", "FR-11", "FR-12"]
NFR_IDS = ["NFR-1", "NFR-2", "NFR-3", "NFR-4", "NFR-5", "NFR-6", "NFR-7", "NFR-8", "NFR-9", "NFR-10", "NFR-11"]


def blocks():
    out = chapter3() + chapter4()
    return _report_trim(out) if F.REPORT else out


def _report_trim(bl):
    """Report mode: drop the least essential sections and one table so the full report stays within its page budget."""
    drop_h2 = ("3.6 Risk Assessment", "4.8 Usage Scenarios")
    out, skipping = [], False
    for b in bl:
        if b[0] in ("h1", "h2"):
            skipping = b[0] == "h2" and b[1] in drop_h2
        if skipping:
            continue
        if b[0] == "tab" and b[1].startswith("Work packages in the order"):
            continue
        out.append(b)
    return out


# =====================================================================================================================
def chapter3():
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether a project can be built, run and maintained with the resources at hand. For ATHENA the question was answered partly by analysis and partly by "
          "building the system and measuring it on the development machine, so most entries below carry a measured value rather than an estimate. Where a question could not be "
          "settled with the data available to the team, the entry says so."),

        H2("3.1 Technical Feasibility"),
        P("The technical risk lay in five places: whether a scanned report could be read well enough on an ordinary processor without a cloud service; whether the text could be turned "
          "into clinical flags reliably with rules; whether a calibrated, explainable multi-class model could be trained and served on a CPU; whether report features and vitals could be "
          "fused in one representation; and whether the pieces could be combined behind one API and one web application. The development machine is "
          f"{F.MACHINE}. It was shared with other jobs during every measurement, so the figures are indicative."),
        TAB("Technical feasibility checks and what was measured", ["Question", "Measurement", "Verdict"], [
            ["Can a scan be read offline on a CPU?",
             f"RapidOCR (ONNX Runtime) reads a generated PNG scan in a median {_OCR / 1000:.2f} s over HTTP; text-layer PDFs are read in {_PDF:.1f} ms", "Feasible; scans are the slow path"],
            ["Can the report be turned into clinical flags?",
             f"22 text flags and 6 lab flags by lexicon and parsers: precision {F.pct(F.READ['precision'], 0)} and recall {F.pct(F.READ['recall'], 0)} on the 12 generated samples; "
             f"precision {F.pct(F.STRESS['precision'])} and recall {F.pct(F.STRESS['recall'])} on 40 hand-written fragments", "Feasible for known wording; weaker for paraphrase"],
            ["Can a calibrated multi-class model be trained on a CPU?",
             f"XGBoost with 220 trees trains in {F.TRAIN_SEC:.2f} s on {F.N_TRAIN:,} rows; calibration on {F.N_CAL} more", "Feasible"],
            ["Is inference fast enough for a nurse waiting at a desk?",
             f"Model alone about {F.MODEL_SEC * 1000:.3f} ms per patient; POST /patients with SHAP {_CREATE:.1f} ms median over HTTP; a PDF report is read and triaged in {_E2E_PDF:.0f} ms, "
             f"a scan in {_E2E_SCAN / 1000:.1f} s", "Feasible"],
            ["Can report features and vitals be fused?",
             f"One 36-input record; on the synthetic data the fused model reaches {F.pct(_FUSED)} against {F.pct(_VIT)} for vitals alone", "Feasible; gain is measured on synthetic data"],
            ["Can everything run behind one API and one web application?",
             "FastAPI with 13 routes and React 19 with six screens; smoke test of 17 checks and 47 automated tests pass", "Feasible"],
            ["Was real clinical data available?", "No. The Kaggle triage dataset needs a user token and its licence is not stated; the download script was never run", "Not feasible within the project; synthetic data used"],
        ], widths=[1.8, 3.4, 1.1], size=9.5, align=["l", "l", "l"]),
        P("The one technical question that was not settled in the project's favour is data. Without clinician-recorded priorities the model can only be trained and tested against a "
          "rule the team wrote, and the report says so wherever a result is quoted."),

        H2("3.2 Economic Feasibility"),
        P("The project was built with open-source software only and runs on a standard desktop. No licence, cloud service or GPU was bought. The only paid component that was considered, a "
          "multimodal language-model API for reading reports, was dropped, which removed both a recurring cost and a dependence on the network."),
        TAB("Components, licences and cost to the project", ["Item", "Role", "Licence", "Cost"], [
            ["Python, FastAPI, SQLAlchemy, SQLite", "Backend, storage", "Open source", "Nil"],
            ["XGBoost, scikit-learn, SHAP", "Model, calibration, explanation", "Open source", "Nil"],
            ["RapidOCR, ONNX Runtime, pypdf, Pillow", "Report reading", "Open source", "Nil"],
            ["ReportLab", "Triage-summary PDF", "Open source", "Nil"],
            ["React, Vite, Recharts, Framer Motion, GSAP", "Web application", "Open source", "Nil"],
            ["Development machine", f"{F.MACHINE}", "Owned", "No new purchase"],
            ["Training data", "Seeded synthetic data generated by `ml/make_data.py`", "Own work", "Nil"],
        ], widths=[2.3, 2.2, 1.0, 0.8], size=10, align=["l", "l", "l", "c"]),
        P("Operating costs would arise only in a real deployment: clinical data under a governance process, hosting with encryption in transit, an audit trail, and clinician time for validation. "
          "None of these was costed, because the project is not a deployment."),

        H2("3.3 Operational Feasibility"),
        P("The system is meant to be used by a triage nurse or clinician in the role of the user, and by an administrator who watches queue load and model performance. The operator "
          f"starts the application with `run.bat`, which creates a virtual environment, installs the packages, trains the model if the file is missing, starts the API on port {F.API_PORT} "
          f"and the web application on port {F.WEB_PORT}, and opens the browser. From the web application the user can pick a sample report or upload a PDF or image, enter the vitals, read the "
          "priority with its reasons, accept or change it, watch the queue reorder, download the summary and read the performance page."),
        B("**Skills needed:** none beyond using a browser; Python 3.11 or newer and Node.js 18 or newer must be installed once.",
          "**Resources:** about 1.5 GB of disk for the Python environment; the model file is about 1.6 MB; an internet connection only for the first installation.",
          "**Maintenance:** retraining is two commands (`ml/make_data.py`, `ml/train.py`); the database is reset by deleting `data/app.db`.",
          "**What operations would still need:** real data, integration with the hospital's records, a clinician validation study, stronger security (HTTPS, a configured secret, rate limiting) and an "
          "audit trail. None of these exists yet (Chapter 10)."),
        P("The fresh-environment path of `setup.bat` and the Kaggle download script were not exercised during the documentation run, so operational feasibility from a clean machine is untested."),

        H2("3.4 Schedule Feasibility"),
        P("The repository does not record a calendar plan, and inventing dates would be misleading. The table below therefore gives the order in which the work was done, as the "
          "documents and the version-control history show, with a planning estimate of relative effort in weeks. The estimates are the team's allocation and not a measured record."),
        TAB("Work packages in the order they were completed", ["Phase", "Work", "Planned effort", "Outcome"], [
            ["1", "Problem identification, survey and objectives (batch documents 2 to 6)", "2 weeks", "abstract, base paper, introduction, five-paper survey, six objectives"],
            ["2", "Backend, report reader, synthetic data, model, calibration, SHAP", "4 weeks", "FastAPI application, 36-input pipeline, trained model, 12 sample reports"],
            ["3", "Web application on the design kit", "3 weeks", "landing, sign-in, new patient, result, queue, performance"],
            ["4", "Experiments, tests, diagrams and documents", "3 weeks", f"{F.PYTEST_TOTAL} tests, {F.SMOKE_TOTAL} smoke checks, `experiments/**/metrics.json`, eleven documents"],
        ], widths=[0.6, 2.7, 1.0, 2.0], size=10, align=["c", "l", "c", "l"]),
        P("The plan held because the design is small: a reader, a model, a database and six screens. The part that could not be scheduled, obtaining real clinical data, was left out of the plan."),

        H2("3.5 Advantages and Constraints"),
        H3("3.5.1 Advantages"),
        B("The report, the vitals, the priority, the reasons and the clinician's decision sit in one record, so disagreement between model and clinician can be counted.",
          "Everything runs offline after installation: no cloud OCR, no language-model API and no patient data leave the machine.",
          f"The whole path is quick on a PDF ({_E2E_PDF:.0f} ms median) and usable on a scan ({_E2E_SCAN / 1000:.1f} s median), and the model itself takes about {F.MODEL_SEC * 1000:.3f} ms.",
          "Each priority comes with a per-patient explanation and a calibrated confidence, and the performance page states that its numbers are synthetic.",
          "Everything is open source, small and reproducible from a seed, and runs on one ordinary machine."),
        H3("3.5.2 Constraints"),
        B("The model is trained and tested on synthetic data; its accuracy is not clinical accuracy.",
          "The report reader is a lexicon and does not understand wording it does not contain.",
          f"Recall for priority 1 is {F.pct(F.REC[0])} on the synthetic hold-out, so the model is a second opinion and not a gatekeeper.",
          "No clinician has used the system, and no regulatory review has taken place.",
          "Security is demonstration grade: seeded demo accounts, a default signing secret unless one is configured, no HTTPS."),
        P(f"The base paper [{R['base']}] states that its synthetic-to-real route is a feasibility approach and that no claim of clinical utility can be made without a prospective study on real data; "
          "the feasibility judgement here is the same in spirit: the engineering is feasible and measured, the clinical value is not shown."),

        H2("3.6 Risk Assessment"),
        P("The risks that could have stopped the project, and what happened to each, are listed below. Several of them materialised, and each is documented as a finding instead of being hidden."),
        TAB("Risks and outcomes", ["Risk", "Likelihood and impact", "What happened"], [
            ["Real clinical data unavailable", "high; the model has no credible evaluation", "materialised: synthetic data used and flagged on every results page"],
            ["Synthetic labels reward the wrong thing", "high; accuracy would measure the rule", f"materialised: a logistic regression scores {F.pct(F.COMP['Logistic regression']['accuracy'])} against {F.pct(F.ACC)} for the shipped model, and a noise ceiling of {F.pct(F.CEILING, 2)} applies"],
            ["Reader misses wording", "medium; findings never reach the model", f"materialised on the stress set: recall {F.pct(F.STRESS['recall'])}; dropped-flag experiment shows the cost"],
            ["Sickest patients under-triaged", "medium; patient-safety impact", f"materialised: priority 1 recall {F.pct(F.REC[0])}, high-risk recall {F.pct(F.SAFE['high_risk_recall'])}; documented, clinician review required"],
            ["Library incompatibility between training and serving", "medium", "avoided: the model loads in the pinned environment; the scikit-learn frozen-estimator wrapper is used for calibration"],
            ["Over-claiming against the base paper", "medium", "avoided: the comparison states that task, data and conditions differ"],
        ], widths=[1.9, 1.7, 2.7], size=9.5, align=["l", "l", "l"]),
        P("The conclusion of the feasibility study is that the project was feasible as a measured engineering study: the reader, the model, the application and the evaluation were built and "
          "tested with free tools on one machine. It was not shown feasible, and the project does not claim it, to improve triage in a real emergency department."),
    ]


# =====================================================================================================================
def chapter4():
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        P("This chapter describes the situation the project starts from, the system that was built in response, the functional and non-functional requirements it was built "
          "to meet, and the hardware, software, users and constraints involved. Requirement identifiers (FR-n and NFR-n) are used again in Chapter 7 where each is tested."),

        H2("4.1 Existing System and Its Limitations"),
        P(f"In most emergency departments triage is done by a nurse using a five-level scale such as ESI [{R['esi']}]. The nurse measures the vitals, asks about the complaint, looks at "
          "whatever the patient has brought and assigns a level. Where an electronic record exists it holds structured fields; the scanned or photographed reports the patient brings are "
          "viewed as images or files, and the findings in them reach the decision only if the nurse reads them. Research systems add machine-learning models trained on structured fields "
          f"[{R['hong']}], [{R['levin']}], [{R['raita']}], and the base paper adds a comparison of 19 classifiers on typed symptom indicators [{R['base']}]."),
        TAB("Limitations of the existing approach", ["Limitation", "Consequence"], [
            ["The level depends on the person on duty", f"Sensitivity for critical illness below 80 % in many studies [{R['hinson']}]"],
            ["Scanned reports are not machine-readable", "Findings such as ST elevation, raised troponin or an anticoagulant do not reach any model"],
            ["Structured-field models see only the fields", "A model cannot weigh what is written only in a report"],
            ["Output is a label or a score with no reasons", "The clinician cannot see why, and so cannot challenge it quickly"],
            ["Confidence is not calibrated", f"A score of 0.9 may not mean nine in ten; calibration is a known need [{R['guo']}]"],
            ["No record of agreement", "Nobody can count how often the clinician changes the machine's priority, or why"],
            ["Time per patient is not reported", "A tool that is accurate but slow cannot be judged for a triage desk"],
        ], widths=[2.4, 3.9], size=10, align=["l", "l"]),

        H2("4.2 Proposed System and Its Advantages"),
        P(f"ATHENA is a decision-support application with six screens and thirteen API routes. A nurse picks a sample report or uploads a PDF or image; the system reads it, shows the "
          "symptoms, findings, history and lab values it found with their page numbers, and fills the form with the vitals. On request it assigns a priority from 1 to 5 with a risk level and "
          "a calibrated confidence, and shows the factors behind the priority, strongest first. The clinician accepts the priority or changes it with a reason; the change is stored, the "
          "queue reorders, and a one-page triage summary can be downloaded. A performance page shows the offline metrics, a confusion matrix and the live counts."),
        TAB("Advantages of the proposed system over the existing practice", ["Advantage", "Evidence"], [
            ["Reads the scanned report", f"22 text flags and 6 lab flags; {F.pct(F.READ['recall'], 0)} recall on the generated samples, {F.pct(F.STRESS['recall'])} on the stress set"],
            ["Fuses report and vitals", f"Synthetic hold-out accuracy {F.pct(_FUSED)} fused against {F.pct(_VIT)} vitals-only and {F.pct(F.ABL['Report only (28)']['accuracy'])} report-only"],
            ["Shows the reasons", "Per-patient SHAP list on the result screen, strongest first"],
            ["Calibrated confidence", f"Isotonic calibration; ECE {F.f3(F.CAL['ece_isotonic'])} against {F.f3(F.CAL['ece_uncalibrated'])} before it"],
            ["Records the clinician's decision", "Accept or change with a required reason, stored with the old and new priority"],
            ["Fast", f"Median {_E2E_PDF:.0f} ms for a PDF report and {_E2E_SCAN / 1000:.1f} s for a scan, end to end over HTTP"],
            ["Offline and inspectable", "No cloud service or key; every rule is in the repository"],
        ], widths=[2.0, 4.3], size=10, align=["l", "l"]),

        H2("4.3 Functional Requirements"),
        P("The functional requirements follow the seven features of the overview document (F1 to F7) and the supporting needs of sign-in and demonstration. Every requirement is met in the "
          "build; the evidence column names where it is shown."),
        TAB("Functional requirements", ["ID", "Requirement", "Status and evidence"], [
            ["FR-1", "A user signs in with email and password; roles clinician and administrator; every patient route needs a token", "Met; bcrypt hashes, 12-hour JWT; API tests of 401 on missing and invalid tokens"],
            ["FR-2", "Upload a PDF, PNG or JPG report of at most 15 MB; read its text by text layer or OCR", "Met; empty (400) and unsupported (422) uploads tested; 15 MB cap in code; 12 samples read"],
            ["FR-3", "Extract symptoms, findings, history and six lab values with the page of each item, handling negation and reference ranges", "Met for known wording (Chapter 7); defects listed"],
            ["FR-4", "Enter age, heart rate, systolic and diastolic blood pressure, SpO2, temperature, respiratory rate and arrival mode, with range checks", "Met; out-of-range values rejected with 422"],
            ["FR-5", "Build one fused record of 36 inputs from the vitals and the report flags", "Met; shown side by side on the result screen"],
            ["FR-6", "Assign priority 1 to 5, a risk level and a calibrated confidence", "Met on synthetic data (Chapter 8)"],
            ["FR-7", "Explain the priority for that patient with signed contributions, strongest first", "Met; SHAP TreeExplainer; order tested"],
            ["FR-8", "Let the clinician accept or change the priority, requiring a reason for a change, and store the decision", "Met; 422 without a reason; override log per patient"],
            ["FR-9", "Show a queue ordered by priority then arrival, with filter and search", "Met; order tested on the sample queue"],
            ["FR-10", "Download a one-page triage summary as a PDF", "Met; the response starts with the PDF header and is tested"],
            ["FR-11", "Show model performance (accuracy, recall per priority, confusion matrix) and live counts (overrides, seconds per patient)", "Met; page labels the data as synthetic"],
            ["FR-12", "Provide labelled sample reports and a seeded sample queue so the application is not empty", "Met; 12 reports and 12 sample cases, marked as samples"],
        ], widths=[0.6, 3.2, 2.5], size=9.5, align=["c", "l", "l"]),

        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and the evidence", ["ID", "Requirement", "Measured evidence"], [
            ["NFR-1", "A PDF report is read and triaged in well under a second; a scan in under five seconds", f"Median {_E2E_PDF:.0f} ms (p95 {F.lat('flow_pdf_then_triage', 'p95_ms'):.0f} ms) for a PDF; median {_E2E_SCAN / 1000:.2f} s for a scan; end-to-end maximum {F.E2E['max']:.2f} s on the samples"],
            ["NFR-2", "Model inference does not dominate the path", f"About {F.MODEL_SEC * 1000:.3f} ms per patient in batch; POST /patients {_CREATE:.1f} ms median including SHAP and the database write"],
            ["NFR-3", "Priority errors stay small: nearly all predictions within one level", f"{F.pct(F.W1, 2)} within one level on the synthetic hold-out; exact accuracy {F.pct(F.ACC)}"],
            ["NFR-4", "Every result carries an explanation", "SHAP list returned with every POST /patients; tested"],
            ["NFR-5", "Displayed confidence behaves like a probability", f"ECE {F.f3(F.CAL['ece_isotonic'])}; the 0.8 to 0.9 bin is over-confident (Chapter 8)"],
            ["NFR-6", "Basic security: authentication on patient routes, hashed passwords, input validation, upload limit, no path traversal", "Tested; known gaps listed (default secret, no HTTPS, no rate limiting)"],
            ["NFR-7", "Clear errors instead of crashes", "400, 401, 404, 413, 422 and 503 paths with plain messages; empty and unsupported uploads tested"],
            ["NFR-8", "Usable at phone, tablet and desktop widths, in light and dark, by keyboard", "Responsive check at 360, 768 and 1440 px passed when the interface was built; not re-run in this session"],
            ["NFR-9", "Runs offline on a Windows desktop after installation", "Yes; no network call at run time; Windows only was tried"],
            ["NFR-10", "Maintainable and testable", f"{F.PYTEST_TOTAL} pytest tests ({F.PYTEST_PASSED} pass, {F.PYTEST_XFAIL} expected failure) in about {F.PYTEST_SECONDS} s; retraining in two commands"],
            ["NFR-11", "Honest about data: synthetic data labelled wherever numbers appear", "Performance page banner and landing text state it; results documents repeat it"],
        ], widths=[0.7, 2.6, 3.0], size=9.5, align=["c", "l", "l"]),

        H2("4.5 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum stated by the project", "Machine used for all measurements"], [
            ["Processor", "Not stated; CPU only", "Intel Core i5-12500, 12 threads"],
            ["Memory", "Not stated", "15.7 GB"],
            ["Disk", "About 1.5 GB for the Python environment and packages", "Local SSD"],
            ["Graphics processor", "Not needed", "Not used"],
            ["Display", "Any modern browser, 360 px wide or more", "1440 x 900 for the screenshots"],
        ], widths=[1.4, 2.6, 2.3], size=10, align=["l", "l", "l"]),

        H2("4.6 Software Requirements"),
        TAB("Software: versions that ran", ["Component", "Requirement", "Used for the measurements"], [
            ["Operating system", "Windows with `run.bat`", "Windows 11 Pro"],
            ["Python", "3.11 or newer", "3.11.9"],
            ["Node.js", "18 or newer", "24.19.0"],
            ["FastAPI / Uvicorn / SQLAlchemy / Pydantic", "listed in `requirements.txt` (unpinned)", "0.162.0 / 0.54.0 / 2.1.6 / 2.14.1"],
            ["XGBoost / scikit-learn / SHAP", "listed (unpinned)", "3.2.0 / 1.9.1 / 0.51.0"],
            ["NumPy / pandas", "listed (unpinned)", "2.4.6 / 3.1.0"],
            ["RapidOCR with ONNX Runtime / pypdf / Pillow", "listed (unpinned)", "onnxruntime 1.31.0 / 6.21.2 / 13.0.0"],
            ["ReportLab / PyJWT / bcrypt", "listed; bcrypt pinned to 4.0.1", "5.1.0 / 2.15.1 / 4.0.1"],
            ["React / Vite", "package.json", "React 19.3 / Vite 8"],
            ["pytest", "development only", "9.1.1"],
        ], widths=[2.4, 2.0, 1.9], size=10, align=["l", "l", "l"]),

        H2("4.7 User Roles and Constraints"),
        TAB("User roles", ["Role", "What the role does", "Interface"], [
            ["Clinician", "Enters patients, reads the result and the reasons, accepts or changes the priority, downloads the summary", "New patient, Result, Queue"],
            ["Administrator", "Watches queue load and the performance page; seeded with the same rights in this build", "Queue, Performance"],
            ["Developer", "Retrains the model, regenerates data and samples, runs the tests", "Command line"],
        ], widths=[1.3, 3.5, 1.5], size=10, align=["l", "l", "l"]),
        B("The application never replaces the clinician: the final priority is always the clinician's, and a change needs a stated reason.",
          "Both roles have the same rights in this build; role-based permissions are future work.",
          f"Ports are fixed: API {F.API_PORT}, web application {F.WEB_PORT}.",
          "The demo accounts are seeded and their password is documented, which is acceptable for a demonstration and not for a deployment."),

        H2("4.8 Usage Scenarios"),
        B("**Chest pain by ambulance.** A nurse selects the chest-pain sample report, the reader finds chest pain, shortness of breath, ST elevation, raised troponin and raised lactate with "
          "their pages, the vitals fill in, and the system returns priority 1 with the ST elevation as the strongest driver.",
          "**Clinician disagrees.** The clinician changes a priority from 2 to 3 and types the reason; the override is stored, the queue reorders, and the performance page counts one change.",
          "**Poor scan.** A photographed report is read by OCR in a few seconds; findings the lexicon does not know are missing, which the nurse can see because the extracted items are listed."),

        H2("4.9 Data Requirements"),
        P(f"The model needs, for each patient, the eight vitals and the 28 report flags, with the unreported flags set to 0, as in the base paper. Training needs a priority for every row. The "
          f"project generates {F.ROWS:,} rows from seven clinical archetypes: minor {F.pct(F.ARCH_SHARE['minor'])}, cardiac {F.pct(F.ARCH_SHARE['cardiac'])}, respiratory {F.pct(F.ARCH_SHARE['respiratory'])}, "
          f"trauma {F.pct(F.ARCH_SHARE['trauma'])}, abdominal {F.pct(F.ARCH_SHARE['abdominal'])}, infection {F.pct(F.ARCH_SHARE['infection'])} and neuro {F.pct(F.ARCH_SHARE['neuro'])}. "
          "The priority is a noisy function of a hand-written severity score. Real data would replace these rows with clinician-recorded priorities and with reports that were scanned in the "
          "department, under ethical and data-protection approval that this project did not seek."),
    ]
