"""Chapter 5: System Design for ATHENA.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
"""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    out = _full()
    return _report_trim(out) if F.REPORT else out


def _report_trim(bl):
    """Report mode: the two simplest diagrams side by side and slightly smaller figures."""
    out = []
    for b in bl:
        if b[0] == "fig":
            if b[1].endswith("03_dfd_level0.png"):
                out.append(("pair", [(b[1], "Data flow diagram, level 0 (context)."), (F.diag("08_use_case.png"), "Use-case diagram.")], 2.9))
                continue
            if b[1].endswith("08_use_case.png"):
                continue
            out.append(("fig", b[1], b[2], min(b[3], 4.8)))
            continue
        out.append(b)
    return out


def _full():
    sp = F.SHAP_TOP
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how ATHENA is built: the architecture and workflow, the data flow, the class and sequence design, the data design, the two core algorithms "
          "(report reading and triage scoring), the module and API design, the user interface and the security and error-handling design. Every diagram was drawn from the code "
          "(`backend/app/`, `ml/` and `frontend/src/`) and is reproduced with an explanation; the full set is also collected in the Block Diagrams document."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **one patient record from two sources**: the scanned report and the vitals must end up in a single representation that one model reads. "
          "Second, **a decision with its reasons**: the priority, a calibrated confidence and the factors behind it appear together on one screen, because a prediction that cannot be "
          "explained is not accepted into a clinical workflow. Third, **the clinician stays in charge**: every priority can be accepted or changed, a change needs a reason, and both are stored. "
          "Fourth, **runs offline on a CPU**: report reading uses a local OCR engine and no network call, so the system works on the ordinary workstation of a ward. Fifth, **small and runnable**: "
          "one API, one browser application and one SQLite file."),
        FIG(F.diag("01_system_architecture.png"), "Figure: three-tier architecture of ATHENA (React application, FastAPI services, SQLite and model files).", 5.4),
        P(f"The presentation tier is a React 19 and Vite single-page application on port {F.WEB_PORT}; it reaches the API through a Vite proxy on the path `/api`. The application tier is FastAPI on "
          f"port {F.API_PORT}. Its router (`routes/api.py`) calls four services: `extract.py` reads a report, `features.py` defines and builds the fused record, `triage.py` runs the calibrated "
          "XGBoost model and the SHAP explainer, and `pdf.py` renders the triage summary with ReportLab. Authentication (`auth.py`) issues and checks signed tokens. The data tier is a SQLite "
          "database (`data/app.db`) with three tables, plus the trained model file `models/triage_model.joblib` and the evaluation reports in `experiments/`."),
        P("The services do not import each other except through `features.py`, which is the single definition of the 36 model inputs. The model is trained offline by `ml/train.py`, so "
          "serving needs only the saved file, and the experiments in Chapter 8 can time each service on its own and together."),

        H2("5.2 High-Level Workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "Figure: workflow from a scanned report and vitals to a clinician-approved priority.", 5.6),
        P("A nurse signs in, opens *New patient*, and uploads a PDF or an image of the report (or picks one of the twelve generated sample reports). The server reads the report and returns "
          "symptoms, findings, history and lab values, each with the page it came from. The nurse enters eight vitals. The server fuses the 28 report flags and the vitals into 36 inputs, "
          "the model returns a priority from 1 to 5 with a calibrated confidence, and SHAP lists the strongest factors. The patient is stored and the queue, which is ordered by priority "
          "and then by arrival time, is updated. A clinician opens the result and either accepts the priority or changes it with a reason; the decision is stored with the patient and the "
          "model's original suggestion is kept."),
        P(f"Every step runs in the same request cycle as the screen that triggers it. Reading a PDF takes about {F.lat('extract_pdf'):.0f} ms and an image scan about "
          f"{F.lat('extract_scan_png') / 1000:.1f} s on the CPU of the measurement machine; assigning a priority takes about {F.lat('create_patient'):.0f} ms (medians over HTTP, Chapter 8)."),

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Figure: data flow diagram, level 0 (context).", 5.6),
        P("At the context level ATHENA is one process with three neighbours. The triage nurse provides a report file, the vitals and a sign-in, and receives the extracted findings, "
          "the priority with its reasons and the queue. The clinician provides a decision (accept or change, with a reason) and receives the patient record and a summary PDF. The "
          "administrator reads the performance figures. Training data enters only offline, when the model is built."),
        H3("5.3.2 Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Figure: data flow diagram, level 1.", 5.4),
        P("Level 1 shows the main processes: authentication, report reading, fusion and triage, queue management, clinician review, summary generation and metrics. The database holds "
          "the users, patients and overrides; the model file is read by the triage process; the evaluation reports are read by the metrics process. Review writes an override and updates "
          "the patient's current priority, which the queue process then uses for its ordering."),
        H3("5.3.3 Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Figure: data flow diagram, level 2, of report reading and triage.", 5.4),
        P("The second level follows one report through the system. Page text is read (text layer or OCR), wrapped lines are re-joined and split into sentences, each sentence is matched "
          "against the clinical lexicon and the lab patterns, matches preceded by a negation are dropped, and the surviving items become the 28 report flags. The fusion step adds the "
          "eight vitals, the model gives calibrated probabilities, the priority is their arg-max, and the explainer returns the attributions for that priority."),

        H2("5.4 UML Design"),
        H3("5.4.1 Class Diagram"),
        FIG(F.diag("06_uml_class.png"), "Figure: UML class diagram of the data model and services.", 5.2),
        P("Three persistent classes carry the data: `User` (name, e-mail, password hash, role), `Patient` (vitals, report, fused record, model priority, current priority, risk level, "
          "confidence, probabilities, SHAP list and timings) and `Override` (the old and new priority, the action, the reason and who made it). The Pydantic classes `LoginIn`, `VitalsIn`, "
          "`PatientIn` and `OverrideIn` validate every request; for example `VitalsIn` limits SpO2 to 50-100 and heart rate to 20-250. The services are modules of functions, not classes: "
          "`extract.parse` and `extract.extract_report`, `features.fuse`, `triage.predict` and `pdf.build_summary`."),
        H3("5.4.2 Sequence Diagram"),
        FIG(F.diag("07_sequence_flow.png"), "Figure: sequence diagram from report upload to clinician override.", 5.2),
        P("The sequence follows the main flow. The browser uploads the file to `/api/reports/extract` and receives the structured report. It then posts the vitals and the report flags "
          "to `/api/patients`; the server fuses them, calls the model, stores the patient and returns the full record. When the clinician decides, the browser posts to "
          "`/api/patients/{id}/override`; the server validates that a change carries a reason, writes an override row, updates the patient and returns the new record."),
        H3("5.4.3 Use-Case Diagram"),
        FIG(F.diag("08_use_case.png"), "Figure: use-case diagram.", 5.2),
        P("The nurse uses report intake, vitals entry and the queue; the clinician uses the result screen, the decision and the summary PDF; the administrator uses the performance page. "
          "Retraining the model is a command-line action of the developer and has no screen."),

        H2("5.5 Data Design"),
        P("ATHENA stores its data in SQLite through SQLAlchemy. The schema has three tables. Patient fields that are structured but variable (vitals, report, fused record, probabilities "
          "and the SHAP list) are kept as JSON columns, because they are always read and written together with the patient and never filtered on."),
        FIG(F.diag("09_er_diagram.png"), "Figure: entity-relationship diagram of the ATHENA database.", 5.6),
        TAB("Database tables and their columns", ["Table", "Columns", "Notes"], [
            ["`users`", "id, name, email (unique, indexed), password_hash, role", "roles: clinician, admin; passwords stored as bcrypt hashes; two demo users seeded"],
            ["`patients`", "id, name, created_at, created_by (FK users), source, vitals (JSON), report (JSON), fused (JSON), model_priority, priority (indexed), risk_level, confidence, "
                           "probabilities (JSON), shap (JSON), ocr_seconds, model_seconds, total_seconds, recorded_outcome",
             "`source` is live or sample; `priority` is the current value after any override, `model_priority` is never changed; `recorded_outcome` is set only on sample cases"],
            ["`overrides`", "id, patient_id (FK, indexed), user_id (FK), user_name, old_priority, new_priority, action, reason, created_at", "action is accept or change; reason required for a change"],
        ], widths=[1.1, 3.6, 1.7], size=9.5, align=["l", "l", "l"]),
        P("A user has many patients (through `created_by`) and many overrides; a patient has many overrides, ordered by id. A new database is seeded with the two demo users and twelve sample "
          "cases built from rows of `data/sample/holdout_sample.csv`; they carry `source = sample` and a `recorded_outcome`, so the queue and the performance page are not empty on the first run and "
          "sample cases are always labelled as such in the interface."),
        TAB("Other data structures", ["Structure", "Content", "Lives in"], [
            ["Fused record", "36 numbers in model column order: 8 vitals and 28 report flags", "built per request, stored with the patient"],
            ["Report flags", "28 flags: 11 symptom, 5 finding, 6 history, 6 lab", "`features.REPORT_FLAGS`"],
            ["Model bundle", "XGBoost base model, isotonic-calibrated wrapper and the feature list", "`models/triage_model.joblib`"],
            ["Evaluation reports", "held-out metrics, confusion matrix, reading and timing results", "`experiments/metrics.json`, `experiments/eval/metrics.json`"],
            ["Sample reports", "8 PDFs and 4 PNG scans with the expected flags and vitals", "`data/sample_reports/`"],
        ], widths=[1.4, 3.4, 1.6], size=9.5, align=["l", "l", "l"]),

        H2("5.6 Algorithm Design"),
        H3("5.6.1 Report reading"),
        FIG(F.diag("11_flowchart_report_reading.png"), "Figure: flowchart of report reading.", 5.0),
        P("A PDF page is read with its text layer; a page with fewer than 20 characters of text is treated as a scan and its first embedded image goes to OCR. An image upload goes straight "
          "to OCR. The OCR engine is RapidOCR, which runs PaddleOCR-family detection and recognition models on ONNX Runtime and needs no network [" + str(R['ppocr']) + "]; the image is enlarged by a factor of 1.6 "
          "when its longer side is under 2,000 pixels, and the recognised boxes are put in reading order by line. Wrapped lines are joined, the text is split into sentences, and each sentence "
          "is tested against a lexicon of 22 regular expressions for symptoms, findings and history. Spaces inside a phrase match zero or more whitespace characters, so a run-on such as "
          "\"shortnessofbreath\" still matches. A match is dropped when one of the words *no, denies, denied, without, negative for, absence of, not, nil, free of, ruled out* occurs within 45 "
          "characters before it in the same sentence. Six lab values (troponin, lactate, white cell count, glucose, creatinine, haemoglobin) are read with their value and compared with "
          "a reference limit; an abnormal value sets the lab flag. Every item keeps the page it was found on."),
        H3("5.6.2 Triage scoring"),
        FIG(F.diag("10_flowchart_triage.png"), "Figure: flowchart of triage scoring and the clinician decision.", 5.0),
        FIG(F.diag("12_model_architecture.png"), "Figure: architecture of the triage model (fusion, XGBoost, calibration, SHAP).", 5.6),
        P("`features.fuse` builds a dictionary in the fixed column order: the eight vitals (arrival mode coded walk-in 0, transfer 1, ambulance 2) followed by the 28 flags, each 0 or 1. "
          "A flag that the report does not mention is 0, which is the same rule the base paper applies to symptoms that were not documented [" + str(R['base']) + "]. The model is an "
          f"XGBoost classifier [{R['xgboost']}] with 220 trees of depth 4 that returns five scores; an isotonic calibrator fitted on a separate split turns them into probabilities "
          f"[{R['zadrozny']}], and the priority is the class with the largest probability. The risk level is High for priorities 1 and 2, Moderate for 3 and Low for 4 and 5. SHAP's tree "
          f"explainer [{R['treeshap']}] then gives the contribution of each of the 36 inputs towards the chosen priority; the list is sorted by absolute value, absent flags with a "
          "contribution below 0.15 are hidden, and the top eight are returned."),
        P(f"On the synthetic hold-out the factors with the largest mean absolute SHAP value over all five classes are {sp[0]['feature'].replace('spo2', 'SpO2')} ({sp[0]['mean_abs_shap']:.2f}), "
          f"arrival mode ({sp[1]['mean_abs_shap']:.2f}), shortness of breath ({sp[2]['mean_abs_shap']:.2f}), systolic blood pressure ({sp[3]['mean_abs_shap']:.2f}) and respiratory rate "
          f"({sp[4]['mean_abs_shap']:.2f}). This matches the weights used to build the synthetic labels, so it checks that the explainer reads the model correctly; it says nothing about clinical "
          "importance."),

        H2("5.7 Module Design"),
        TAB("Modules, responsibilities and size", ["Module / file", "Responsibility", "Lines"], [
            ["`backend/app/main.py`", "FastAPI application, start-up (create tables, warm the model and OCR engine, seed users and the sample queue), CORS", "84"],
            ["`backend/app/routes/api.py`", "13 routes, request schemas, serialisation, queue ordering, override rules, metrics", "225"],
            ["`backend/app/db.py`", "SQLAlchemy engine, session factory and the three models", "79"],
            ["`backend/app/auth.py`", "bcrypt hashing, HS256 token creation and checking, current-user dependency", "47"],
            ["`backend/app/services/extract.py`", "PDF text, OCR, lexicon, negation, lab parsing", "187"],
            ["`backend/app/services/features.py`", "vital and flag definitions, labels, arrival codes, risk level, `fuse`", "87"],
            ["`backend/app/services/triage.py`", "model loading, calibrated prediction, SHAP attribution", "73"],
            ["`backend/app/services/pdf.py`", "triage summary PDF (ReportLab)", "63"],
            ["`ml/make_data.py`, `ml/train.py`, `ml/eval.py`", "synthetic dataset, training and calibration, evaluation of reading and timing", "108 / 74 / 59"],
            ["`frontend/src/`", "31 files: 6 pages, a design kit of UI components, API client, auth, theme and storage helpers", "about 3,400"],
            ["`scripts/` and `tests/`", "sample reports, smoke test, screenshots, responsive check, experiments, API timing; 47 pytest tests", "see Chapter 7"],
        ], widths=[2.3, 3.4, 0.7], size=9.5, align=["l", "l", "c"]),
        P("The modules are small and each has one reason to change. `features.py` is the single source of the column order that `triage.py`, `make_data.py`, `train.py` and the tests "
          "import, so the schema cannot drift between training and serving. `routes/api.py` is the only module that touches HTTP."),

        H2("5.8 API Design"),
        P("The API is JSON over HTTP under the prefix `/api`, plus one multipart upload route and one PDF download. All routes except `health`, `public/stats` and `auth/login` need a bearer "
          "token. The routes fall into five groups; request and response details are in Chapter 6."),
        TAB("API route groups", ["Group", "Routes", "Purpose"], [
            ["Service", "GET /health, GET /public/stats", "liveness and model presence; headline numbers for the landing page"],
            ["Authentication", "POST /auth/login, GET /auth/me", "sign in, who am I"],
            ["Report intake", "POST /reports/extract, GET /samples, GET /samples/{file}", "read an upload; list and fetch the generated sample reports"],
            ["Patients", "POST /patients, GET /patients, GET /patients/{id}, GET /patients/{id}/summary.pdf, POST /patients/{id}/override", "triage, queue, record, summary, decision"],
            ["Evaluation", "GET /metrics", "offline evaluation and live counts"],
        ], widths=[1.2, 3.2, 2.0], size=9.5, align=["l", "l", "l"]),
        P("Validation is strict and returns a meaningful status instead of a stack trace: an empty upload is 400, an upload over 15 MB is 413, an unreadable file is 422, vitals outside "
          "their physical limits are 422, a missing patient is 404, and a missing or expired token is 401. A model that is not trained returns 503."),

        H2("5.9 User Interface Design"),
        P("The interface is a React single-page application built on the shared *Neo Brutal Grid* design kit: hard-edged boxes with a 3-pixel border and offset shadow, flat colour with no "
          "gradients, an Archivo Black display face with IBM Plex Sans and Mono for text, and one fixed colour for each priority (1 coral, 2 amber, 3 sky, 4 lime, 5 paper). A dark theme, "
          "reduced-motion support, a drawer navigation on narrow screens and visible keyboard focus are provided. The token is kept in the browser's local storage, and any 401 response "
          "signs the user out."),
        TAB("Application screens", ["Route", "Screen", "What the user does"], [
            ["`/`", "Landing", "reads what ATHENA does and the headline evaluation numbers, marked as synthetic"],
            ["`/login`", "Sign in", "enters credentials or uses a demo button"],
            ["`/app/new`", "New patient", "uploads or picks a report, reviews what was found (with pages), enters the vitals and assigns a priority"],
            ["`/app/patients/:id`", "Result", "sees priority, risk and confidence, the fused record, the SHAP bars and probabilities; accepts or changes the priority; downloads the PDF"],
            ["`/app/queue`", "Triage queue", "sees patients sickest first, filters by priority tab or search; the list refreshes every 15 seconds"],
            ["`/app/performance`", "Model performance", "reads accuracy, per-priority recall, the confusion matrix, seconds per patient and the live review counts"],
        ], widths=[1.4, 1.3, 3.7], size=9.5, align=["l", "l", "l"]),
        B("Every screen that shows model output carries the notice that the evaluation is on a seeded synthetic dataset.",
          "The result screen shows the report-derived and the vitals-derived halves of the fused record side by side, so a clinician can see what the model was given.",
          "Errors from the API are shown as messages with a retry action and never as blank screens; sample cases are labelled as samples in the queue."),

        H2("5.10 Key Design Decisions"),
        TAB("Decisions and their reasons", ["Decision", "Reason", "Consequence"], [
            ["Local OCR (RapidOCR) and a clinical lexicon instead of a cloud multimodal model", "no network, no API key, no patient text leaving the machine",
             "reading is rule-based: 100% on the generated samples but recall "
             f"{F.pct(F.STRESS['recall'])} on the hand-written stress set"],
            ["Fuse 28 report flags with 8 vitals in one table of 36 inputs", "one model sees both sources; flags are interpretable", "a missed flag is a 0, so reading errors reach the model"],
            ["XGBoost with isotonic calibration and a tree explainer", "calibrated probabilities and exact tree SHAP at millisecond cost; room for non-linearity on real data",
             f"on the synthetic data logistic regression scored higher ({F.pct(F.COMP['Logistic regression']['accuracy'])} against {F.pct(F.COMP['XGBoost (shipped config)']['accuracy'])})"],
            ["Five-level priority as the target", "matches the clinical scale and the batch objective", "ordinal errors matter: within-one accuracy is reported next to exact accuracy"],
            ["Priority and model suggestion stored separately", "overrides become feedback and agreement can be measured", "the live agreement rate needs real use to mean anything"],
            ["SQLite with JSON columns", "no database server; the demo runs from one folder", "single-writer; not a multi-site design"],
            ["Synthetic training data", "no real patient records were available", "all accuracy figures describe a simulated rule, not clinical performance"],
        ], widths=[2.0, 2.3, 2.1], size=9.2, align=["l", "l", "l"]),

        H2("5.11 Security and Error-Handling Design"),
        P("The security design is described against a simple threat model and the limits of that model are stated. The system is meant for a trusted ward network. Against a user "
          "without credentials it provides authentication on every patient route, bcrypt password hashes, signed tokens that expire after 12 hours, a path check on the sample-file route, a 15 MB "
          "upload limit and range validation on every vital. Database access goes through the ORM, so request values are never concatenated into SQL."),
        TAB("Controls and their limits", ["Control", "What it does", "Limit"], [
            ["Bearer token (HS256, 12 h)", "protects every patient, queue and metrics route", "default secret `dev-secret-change-me` when `JWT_SECRET` is unset; no refresh or revocation"],
            ["bcrypt password hashes", "no plain passwords in the database", "two demo accounts with a published password"],
            ["Role field (clinician, admin)", "stored with the user and the token", "routes do not yet check the role: any signed-in user can do everything"],
            ["Pydantic validation", "age, heart rate, blood pressure, SpO2, temperature and respiratory rate within physical limits", "limits are plausible bounds, not clinical alarms"],
            ["Upload limits", "15 MB, PDF / PNG / JPG only, empty file refused", "no virus scanning; no rate limiting"],
            ["CORS fixed to the two local origins", "browsers from other origins are refused", "plain HTTP; no TLS"],
            ["Override audit", "who, when, old and new priority, action and reason are stored", "no tamper-proofing of the log; the database is a single file"],
        ], widths=[1.9, 2.4, 2.1], size=9.3, align=["l", "l", "l"]),
        P("Errors follow one rule: a failure is reported with a status code and a short message the user can act on, and the server keeps running. If the model file is missing, scoring "
          "routes answer 503 with the instruction to train; at start-up a missing model only skips the warm-up and the sample queue. The browser shows API messages in the interface and "
          "turns a lost connection into a single *Cannot reach the ATHENA API* message."),
        P("None of this makes the system safe for real patients. There is no HTTPS, no rate limiting, no role enforcement, no audit beyond overrides and no regulatory review, and the model "
          "has never seen a real patient record. ATHENA is a decision-support prototype; the treating clinician makes the final triage decision."),
    ]
