"""Index of the ATHENA design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py, diagrams_dfd.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document (11) and the full report. Each paragraph describes what the code in 8.ProjectCode really does.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of ATHENA: React single-page app, FastAPI application, service modules and one SQLite file with files on disk.",
     "The presentation tier is the React 19 single-page app served by Vite on port 5307, with six lazy-loaded pages, a fetch wrapper that attaches the bearer token, and the shared "
     "interface kit. Every call goes through the /api proxy to the FastAPI application on port 8307, whose routes are grouped into authentication, report reading, patients and status. "
     "The routes call four service modules: extract reads reports, features builds the fused record, triage runs the calibrated model with SHAP, and pdf writes the summary. "
     "The data tier is one SQLite file with three tables, the saved model file, the twelve sample reports and the experiment results. There is no separate database server."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "From an uploaded report and eight vitals to a priority the clinician can accept or change.",
     "The nurse uploads a PDF, PNG or JPG report of up to 15 MB. The system reads each page, using the text layer of a PDF or OCR when a page has no text, and parses symptoms, findings, "
     "history and six lab values, dropping negated terms and keeping the page of every item. The nurse enters eight vitals. The 28 report flags and 8 vitals are fused into 36 inputs, and the "
     "calibrated XGBoost model returns a priority from 1 to 5, a risk level and a confidence, with the strongest SHAP drivers. The clinician accepts or changes the priority, and the decision "
     "feeds the queue, the override log, the summary PDF and the performance page."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): the triage system with four external entities.",
     "At level 0 the whole product is one process. The triage nurse or clinician sends the sign-in, a report file, the vitals and the accept or change decision, and receives findings with "
     "their pages, the priority with its reasons, the queue and the summary PDF. The administrator signs in and views performance, receiving model metrics and live counts. The developer, "
     "working offline, supplies the synthetic data set and a retrain command, and receives the model file and metrics. The sample report library is an input source: twelve generated PDFs and "
     "scans that can be loaded instead of an upload."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: seven processes and six data stores.",
     "Level 1 splits the system into seven processes that match the routes in routes/api.py. Process 1.0 checks credentials against the users store and issues a token. Process 2.0 reads a "
     "report, from an upload or a sample, and returns report flags. Process 3.0 combines the flags with the vitals and the saved model to produce the priority, risk and SHAP list, and process "
     "4.0 stores the patient and serves the queue. Process 5.0 records the clinician's decision in the overrides store and updates the patient. Process 6.0 reports metrics from the "
     "evaluation files and live counts, and process 7.0 builds the summary PDF."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: the report-reading process 2.0 expanded into seven sub-processes.",
     "Level 2 follows services/extract.py. The uploaded bytes and file name reach 2.1, which decides between a PDF and an image. A PDF goes to 2.2, which reads the text layer page by page; a "
     "page with almost no text, or an image upload, goes to 2.3, which runs the local OCR engine and returns text in reading order. Process 2.4 rejoins wrapped lines and splits the text into "
     "sentences. Process 2.5 matches the 22-term lexicon and drops negated terms; process 2.6 parses six lab values against reference ranges. Process 2.7 assembles the flags, items with page "
     "numbers and labs into the structured report that goes to the assessment step."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of the three database models, the four request schemas, the API router and the five service modules.",
     "The three tables are User, Patient and Override. A user can create many patients and make many overrides, and a patient can have many overrides. The Pydantic schemas validate input: "
     "LoginIn for sign-in, VitalsIn with range checks on each vital sign, PatientIn which contains VitalsIn and an optional report, and OverrideIn with a priority of 1 to 5 and a reason. "
     "The API router calls the auth module for passwords and tokens, extract for report reading, features for the fused record, triage for the model and SHAP, and pdf for the summary. The "
     "router is the only code that touches the database session."),
    ("seq", "Sequence diagram of one patient", "07_sequence_flow.png",
     "Sequence diagram: sign in, read a report, assess and store a patient, then record the clinician's decision.",
     "Four steps are shown between the browser, the FastAPI router, the extract service, the triage service and SQLite. The browser signs in and receives a token. It uploads the report, and the "
     "router passes the bytes to the extract service, which returns flags, items with pages and labs. The browser then posts the vitals with the report; the router asks the triage service for "
     "the priority, risk, confidence and SHAP list, inserts the patient and returns it. Finally the clinician posts a decision; a change without a reason is refused, otherwise an override row "
     "is inserted, the priority and risk are updated, and the queue reorders."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with the triage nurse or clinician, the administrator and the offline developer.",
     "The nurse or clinician can sign in, upload and read a report, try a sample report, enter vitals, assess the priority and see the reasons, accept or change the priority with a reason, "
     "download the summary PDF, view the queue and view model performance. Trying a sample report extends uploading a report, because it fills the same form from a generated file. The "
     "administrator can sign in, view the queue and view performance. The developer retrains the model from the command line, so that use case sits at the edge of the system boundary. "
     "Every use case other than sign-in needs a signed-in user."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the users, patients and overrides tables.",
     "The users table holds a name, a unique email, a password hash and a role. The patients table is the centre: it stores the vitals, the parsed report and the fused inputs as JSON, the "
     "model's first priority and the current priority, the risk level, the confidence, the probabilities and the SHAP list, three timings and, for the twelve sample cases, a recorded outcome. "
     "The overrides table stores who reviewed a patient, the old and new priority, the action (accept or change) and the reason. A user creates many patients, a patient has many overrides and "
     "a user makes many overrides; two of these links may be empty, for example when a sample case has no creator."),
    ("flow_triage", "Triage scoring flowchart", "10_flowchart_triage.png",
     "Flowchart of the scoring step, from the fused record to the priority and the filtered SHAP list.",
     "The vitals and the 28 report flags are fused into 36 values in the order the model expects. The calibrated model returns five probabilities, the largest of which gives the priority "
     "(class index plus one) and the confidence, and the risk level follows from the priority. A TreeExplainer on the same trees gives the contribution of every input toward the chosen "
     "priority. The contributions are sorted by size, and any report flag that is absent and has an effect below 0.15 is hidden, so the list shows what is present and what matters. Up to "
     "eight items are returned with the priority, probabilities, fused record and elapsed time."),
    ("flow_read", "Report-reading flowchart", "11_flowchart_report_reading.png",
     "Flowchart of the report reader: file type, text layer or OCR, sentence matching, negation and lab ranges.",
     "A file is treated as a PDF if its name ends in .pdf or it starts with the PDF header. Each PDF page is read from its text layer; a page with fewer than 20 characters and an embedded "
     "image is sent to OCR. Other uploads are opened as images, enlarged if small, and read by OCR in reading order. Wrapped lines are rejoined and split into sentences. In each sentence the "
     "lab patterns and the clinical lexicon are tried; a lexicon hit is dropped if a negation word appears in the 45 characters before it, and a lab value sets its flag only when it is outside "
     "the reference range. Every kept item carries its page number."),
    ("model", "Model architecture", "12_model_architecture.png",
     "Architecture of the triage model: fused record, XGBoost, isotonic calibration, argmax, risk level and SHAP.",
     "The eight vitals and 28 report flags form a 36-input fused record. An XGBoost classifier of 220 trees with depth 4, a learning rate of 0.1 and row and column sampling of 0.9 is fitted "
     "on 3,840 rows and outputs five raw probabilities. An isotonic calibrator, fitted on a separate 960 rows with the base model frozen, turns them into calibrated probabilities. The "
     "largest gives the priority and the confidence, and a fixed rule maps priority to risk level. A SHAP TreeExplainer reads the same trees to explain each prediction. The remaining 1,200 "
     "synthetic rows are held out for evaluation."),
]
