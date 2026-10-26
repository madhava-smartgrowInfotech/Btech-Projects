"""Chapter 5: System design. The diagram explanations are shared with '11. BLOCK DIAGRAMS ALL.docx'."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from . import facts as F

# (key, section title, file, caption, explanation)
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png", "System architecture of LabLens",
     "LabLens has four tiers. In the presentation tier the React single-page application (built with Vite, port 5308) is the main interface, and the original "
     "Streamlit application (`app.py`, port 8501) remains as a second front end that calls the same modules and uses the same SQLite file directly. The application "
     "tier holds the FastAPI service in `backend/main.py` (port 8308), which signs and checks bearer tokens, enforces CORS and the 15 MB upload limit, receives "
     "uploads and turns database rows into JSON, and `report_processor.py`, which coordinates the six pipeline stages and records a status and an error message for "
     "each report. The pipeline modules are `ocr_processor.py` (text extraction), `ner_processor.py` (row parsing and test-name matching), `result_analyzer.py` "
     "(status rules) and `ai_insights.py` (explanations). The data tier is the SQLite file `data/medical_lab.db`, reached through `database.py` and the ORM classes "
     "of `models.py`. Two services are optional and drawn with dashed outlines: the Tesseract engine, needed only for scanned pages and images, and the Anthropic "
     "API, used only to reword explanations; neither was exercised on the test machine. A note on the diagram lists what the abstract proposed but was not built "
     "(PP-OCR, a CRF tagger, retrieval, Supabase and serverless functions). After `npm run build` the API also serves the compiled interface from `frontend/dist`."),
    ("flow", "High-level workflow", "02_high_level_workflow.png", "High-level workflow of one report, from upload to review",
     "One report passes through eight steps. The user signs in with the demonstration account (step 1) and uploads a PDF, JPG, JPEG or PNG file of at most 15 MB "
     "(step 2). A report row is created at once, so that even a failed upload appears in the report list with its error. Text is then taken from the PDF text "
     "layer, or from OpenCV preprocessing followed by Tesseract for scanned pages and images (step 3). The parser turns each line into a candidate row (name, "
     "value, unit, reference range, confidence) and snaps the name to a dictionary of 55 test names (step 4). Each row is classified LOW, NORMAL, HIGH or UNKNOWN "
     "(step 5), explanations are generated for the LOW and HIGH rows only (step 6), and rows and insights are stored in SQLite (step 7). The user then reviews the "
     "results on the dashboard, analysis, trend, comparison and insight screens (step 8). Steps 3 to 7 run inside one call of `process_uploaded_report`. A failure "
     "in the steps that extract, parse, classify or store marks the report Failed with a readable message; a failure in the explanation step leaves the report Completed."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png", "Data flow diagram, level 0 (context diagram)",
     "The context diagram shows LabLens as one process with one external entity, the signed-in user. The user sends credentials, a lab report (PDF, JPG or PNG) "
     "and requests to view or delete reports. The system returns the extracted results, their status flags, plain-language explanations, trends, comparisons and "
     "statistics. Inside the boundary the process reads and writes one data store, D1, which holds the reports, test results and insights in SQLite. One optional "
     "external service, the Anthropic API, receives a test name and status and returns reworded text, but only when the user asks for it and a key is configured. "
     "The Tesseract engine is a local program called inside the process and is not drawn at this level."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png", "Data flow diagram, level 1",
     "Level 1 splits the system into four processes. Authenticate (1.0) compares the email and password with the configured demonstration account and returns a "
     "signed token that is valid for 12 hours. Process uploaded report (2.0) accepts a file and the token, runs the whole pipeline and writes rows to the report, "
     "test-result and insight stores (D1, D2, D3); it returns the results and a stage log, and sends a test name and status to the optional Anthropic API only "
     "when reworded text was requested. Present results, trends and statistics (3.0) reads the stored rows and returns the dashboard, analysis, trend, comparison "
     "and insight data as JSON. Delete or load sample reports (4.0) removes a report with its results and insights by cascade, or adds five synthetic reports. "
     "The note under the diagram records that every process except 1.0 needs a valid bearer token and otherwise answers HTTP 401."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png", "Data flow diagram, level 2: process 2.0 (process uploaded report) expanded",
     "Level 2 expands process 2.0 into the six steps of `process_uploaded_report`. Validate file (2.1) accepts only pdf, jpg, jpeg and png, a non-empty file and at most "
     "15 MB; a rejected file leads to a Failed report with a message. Extract text (2.2) reads the PDF text layer (at least 30 characters per page) or renders "
     "the page at 300 dpi and applies OpenCV preprocessing and Tesseract; an unreadable scan also leads to Failed. Parse test rows (2.3) applies the regular "
     "expressions and the TF-IDF name match and yields name, value, unit, range and confidence. Classify against range (2.4) adds the status. Generate insights "
     "(2.5) is applied to LOW and HIGH rows only. Store and set status (2.6) writes the result rows (D2), the insight rows (D3) and the report status, raw text and "
     "error message (D1)."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png", "UML class diagram (real classes plus modules drawn as classes)",
     "Most of the pipeline is function-oriented, so the diagram draws each module as a class stereotyped as a module and shows the real classes beside them. The "
     "modules are the FastAPI application, `report_processor`, `ocr_processor`, `ner_processor`, `result_analyzer`, `ai_insights` and `database`, each with its "
     "constants and public functions. `ProcessingResult` is the container returned by `report_processor`; it holds the report identifier, the raw text, the list "
     "of classified results, the stages completed, any error and the status. `ClassifiedResult` is the dataclass returned by `result_analyzer`. The dataclass "
     "`HealthInsight` of `ai_insights.py`, which carries the explanation text, is drawn as `InsightText` so that it is not confused with the ORM class of the same "
     "name. The three ORM classes `Report`, `TestResult` and `HealthInsight` (`models.py`) are linked one to many with cascading delete, and `OCRError` is the "
     "exception raised by the text-extraction stage."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png", "Sequence diagram: uploading and analysing one report",
     "The sequence follows one upload through seven participants. The user chooses a file on the Upload page, which posts it as multipart data to `POST /api/reports` with "
     "the bearer token. The API verifies the HMAC signature and expiry and calls `process_uploaded_report`, which creates the report row, extracts the text and rows, "
     "classifies them, saves them and then asks `ai_insights` for an explanation of each LOW or HIGH row; the insight is saved and the status becomes Completed. "
     "`ProcessingResult` returns to the API, which answers HTTP 200 with the results, the insights and the stage log, and the page shows the results table, the flags "
     "and the insight cards. The alternative box records the failure rules: any failing stage sets the status to Failed with the message and returns it with HTTP 200, "
     "a missing or expired token gives 401 before any processing, and an insight failure leaves the report Completed. The whole exchange is one synchronous request."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png", "Use-case diagram",
     "There is one actor, the signed-in user, and no roles. The user can sign in with the demonstration account, upload a lab report, view the extracted results with "
     "their LOW, NORMAL or HIGH flags, read the plain-language insights, track one test across reports on a trend chart, compare two reports, browse, open and "
     "delete reports, view the dashboard totals and critical alerts, and load the five sample reports. Every case except signing in requires a valid token. Two "
     "optional external systems appear on the right: the Anthropic API, which extends the insight text when requested, and Tesseract OCR, which the upload case "
     "includes for scanned pages and images."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png", "Entity-relationship diagram of the stored data",
     "Persistent data are in three tables. A `reports` row describes one uploaded file and owns zero or more `test_results` rows, one for each lab test extracted "
     "from it; a `test_results` row owns zero or more `health_insights` rows (the code writes one for every LOW or HIGH result). Both relationships are "
     "enforced by a foreign key and by the ORM cascade `all, delete-orphan`, so deleting a report removes its results and their insights. The demo user is not "
     "an entity: the account is configured through environment variables and exists only inside the signed token, so the database holds one shared library."),
    ("flowchart", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png", "Flowchart of the core algorithm: from a text line to a classified row",
     "The flowchart has three panels that follow the code. Panel A is the row parser of `ner_processor.py`: the report date is searched once, then each line is "
     "skipped if it is blank, shorter than three characters, header-only or without a digit, and must otherwise start with a name followed by a number. The "
     "range is searched in the remainder of the line (two-sided first, then one-sided), a unit is taken from the line or from its end, a row with neither range "
     "nor unit is skipped, and the others receive a confidence score. Panel B is the name matcher: the name is cleaned, vectorised as character 2-4-grams and "
     "compared with the 55 known names; a similarity of at least 0.55 snaps it to the canonical name, otherwise the cleaned name is kept. The row is appended "
     "and duplicates on name, value and unit are dropped. Panel C is `classify_result`: it returns UNKNOWN for a missing value, uses both limits when present, "
     "otherwise only the high or only the low limit, and UNKNOWN when there is no limit."),
]

SCHEMA = {
    "reports": [
        ["id", "INTEGER", "Primary key, auto-increment", "Report number shown in the interface"],
        ["file_name", "VARCHAR(255)", "NOT NULL", "Name of the uploaded file"],
        ["file_type", "VARCHAR(10)", "nullable", "pdf, jpg, jpeg or png"],
        ["upload_date", "DATETIME", "default UTC now", "Upload time (naive UTC); the x-axis of every trend"],
        ["processing_status", "VARCHAR(50)", "default Pending", "Pending, Processing, Completed or Failed"],
        ["error_message", "TEXT", "nullable", "Reason shown to the user when the status is Failed"],
        ["raw_text", "TEXT", "nullable", "Full extracted text, kept so a failure can be inspected"],
    ],
    "test_results": [
        ["id", "INTEGER", "Primary key, auto-increment", "Result identifier"],
        ["report_id", "INTEGER", "Foreign key to reports.id, NOT NULL", "Owning report"],
        ["test_name", "VARCHAR(255)", "NOT NULL", "Normalised test name; trends match on this exact string"],
        ["result_value", "FLOAT", "nullable", "Measured value"],
        ["unit", "VARCHAR(50)", "nullable", "Unit as printed, or null if none was recognised"],
        ["reference_low", "FLOAT", "nullable", "Lower limit; null for a one-sided upper limit"],
        ["reference_high", "FLOAT", "nullable", "Upper limit; null for a one-sided lower limit"],
        ["status", "VARCHAR(20)", "nullable", "LOW, NORMAL, HIGH or UNKNOWN"],
        ["test_date", "DATETIME", "nullable", "Date found in the report text, if any"],
        ["confidence_score", "FLOAT", "default 0.0", "Extraction confidence, 0.1 to 0.9"],
    ],
    "health_insights": [
        ["id", "INTEGER", "Primary key, auto-increment", "Insight identifier"],
        ["test_result_id", "INTEGER", "Foreign key to test_results.id, NOT NULL", "The abnormal result explained"],
        ["explanation", "TEXT", "nullable", "What the test measures and how the result was flagged"],
        ["possible_causes", "TEXT", "nullable", "General, non-diagnostic possible causes"],
        ["recommendations", "TEXT", "nullable", "Suggestion to discuss the result with a clinician"],
        ["created_at", "DATETIME", "default UTC now", "Creation time; the newest insight per result is read"],
    ],
}

MODULES = [
    ["`ocr_processor.py`", "225", "Upload validation, PDF text layer, OpenCV preprocessing, Tesseract", "`validate_file`, `extract_text`, `preprocess_image_for_ocr`"],
    ["`ner_processor.py`", "289", "Row parsing, test-name matching, date and patient name", "`extract_structured_tests`, `normalize_test_name`, `extract_test_date`"],
    ["`result_analyzer.py`", "100", "Status rules and summary counts", "`classify_result`, `analyze_results`, `summarize_statuses`"],
    ["`ai_insights.py`", "270", "Knowledge base, rule-based and optional LLM explanations", "`generate_insight`, `generate_rule_based_insight`"],
    ["`report_processor.py`", "148", "Pipeline coordination and failure handling", "`process_uploaded_report`"],
    ["`database.py`", "251", "Engine, sessions, CRUD helpers, dashboard totals", "`create_report`, `save_test_results`, `get_results_by_test_name`, `get_dashboard_stats`"],
    ["`models.py`", "97", "ORM tables", "`Report`, `TestResult`, `HealthInsight`"],
    ["`backend/main.py`", "352", "FastAPI routes, token authentication, JSON serialisers", "14 routes (Section 5.7)"],
    ["`backend/demo_data.py`", "98", "Five synthetic sample reports drawn as PDFs", "`render_pdf`, `seed_demo_reports`"],
    ["`app.py`", "523", "Original Streamlit interface", "Upload, analysis, history, trends, comparison pages"],
    ["`frontend/src/pages/`", "1,756", "Eleven React pages", "Landing, Login, Dashboard, Upload, Analysis, Reports, Trends, Compare, Insights, About, NotFound"],
]

ENDPOINTS = [
    ["GET", "/api/health", "No", "Liveness check; returns `{\"status\": \"ok\"}`"],
    ["GET", "/api/config", "No", "Disclaimer, accepted extensions, dictionary names, size limit, LLM availability, demo e-mail and password"],
    ["POST", "/api/auth/login", "No", "Checks the demo account; returns a signed token and the user"],
    ["GET", "/api/auth/me", "Yes", "The signed-in user, used to restore a session"],
    ["GET", "/api/dashboard", "Yes", "Totals and the ten most recent reports with test and abnormal counts"],
    ["GET", "/api/reports", "Yes", "All reports, newest first, with counts"],
    ["POST", "/api/reports", "Yes", "Multipart `file` and `use_llm`; runs the pipeline and returns status, stages, results and insights"],
    ["GET", "/api/reports/{id}", "Yes", "One report with its results, insights and the first 5,000 characters of raw text"],
    ["DELETE", "/api/reports/{id}", "Yes", "Deletes the report, its results and insights"],
    ["GET", "/api/tests", "Yes", "Distinct test names on file, for the trend selector"],
    ["GET", "/api/trends?test=", "Yes", "Values of one test across reports in upload order, with direction"],
    ["GET", "/api/compare?a=&b=", "Yes", "Tests common to two reports, with the change (second minus first)"],
    ["GET", "/api/insights", "Yes", "Every LOW or HIGH result with its insight, newest report first"],
    ["POST", "/api/demo/seed", "Yes", "Loads five synthetic reports through the real pipeline, only into an empty library"],
]

SCREENS = [
    ["Landing `/`", "01, 02", "Public introduction with a three-dimensional hero scene (static image when motion is reduced), how it works, disclaimer"],
    ["Sign in `/login`", "03", "Demo credentials with a one-click sign-in button"],
    ["Dashboard `/app`", "04, 13", "Report, test, normal, abnormal and critical totals, critical alert banner, recent reports, results by status; empty state with a button to load sample reports"],
    ["Upload `/app/upload`", "05, 06", "Drop area, accepted formats and size, optional LLM switch, six-step progress, results table after processing"],
    ["Analysis `/app/analysis/:id`", "07", "Report selector, counts, filterable results table, insight cards for abnormal results, raw text, disclaimer"],
    ["My reports `/app/reports`", "08", "Searchable list with status, counts, expandable results and a confirmed delete"],
    ["Trends `/app/trends`", "09", "Test selector, line chart with reference band, direction note, table of all values"],
    ["Compare `/app/compare`", "10", "Two report selectors, tests in common, change column, bar chart grouped by unit"],
    ["Insights `/app/insights`", "11", "Every abnormal result with its explanation, status tabs and search"],
    ["About `/app/about`", "12", "What the product does, pipeline, limits, disclaimer"],
]


def diagram_blocks(heading_level=3):
    out = []
    for key, title, file, caption, text in DIAGRAMS:
        out.append(("h3" if heading_level == 3 else "h2", f"{title}"))
        out.append(FIG(F.diag(file), caption, 5.2 if key not in ("uml", "arch") else 4.8))
        out.append(P(text))
    return out


def schema_blocks():
    out = []
    for name, rows in SCHEMA.items():
        out.append(TAB(f"Table `{name}`", ["Column", "Type", "Constraint", "Meaning"], rows, widths=[1.3, 1.0, 1.7, 2.3], size=9.5))
    out.append(P("The tables are created by `init_db()` with `Base.metadata.create_all`, so a fresh checkout needs no migration. Access goes through SQLAlchemy "
                 "sessions that commit on success and roll back on any exception, which removes string-built SQL and with it injection through file names or test "
                 "names. There are no secondary indexes and no unique constraint: the volumes of a personal library are small, and a repeated upload simply creates "
                 "a second report. The schema has no user column, because the product keeps one shared library."))
    return out


def blocks():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Architecture"),
        P("The design follows three rules: keep the pipeline in plain Python modules that can be tested without a web server, keep the web layer thin, and make "
          "every failure visible to the user instead of silent. The original Streamlit project already contained the pipeline and the database, so the "
          "FastAPI service and the React interface were added on top without changing them."),
        FIG(F.diag("01_system_architecture.png"), DIAGRAMS[0][3], 6.0),
        P(DIAGRAMS[0][4]),
        H2("5.2 High-level workflow"),
        FIG(F.diag("02_high_level_workflow.png"), DIAGRAMS[1][3], 6.0),
        P(DIAGRAMS[1][4]),
        H2("5.3 Data flow diagrams"),
        H3("Level 0"),
        FIG(F.diag("03_dfd_level0.png"), DIAGRAMS[2][3], 5.6),
        P(DIAGRAMS[2][4]),
        H3("Level 1"),
        FIG(F.diag("04_dfd_level1.png"), DIAGRAMS[3][3], 5.8),
        P(DIAGRAMS[3][4]),
        H3("Level 2"),
        FIG(F.diag("05_dfd_level2.png"), DIAGRAMS[4][3], 5.8),
        P(DIAGRAMS[4][4]),
        H2("5.4 UML diagrams"),
        H3("Class diagram"),
        FIG(F.diag("06_uml_class_diagram.png"), DIAGRAMS[5][3], 6.0),
        P(DIAGRAMS[5][4]),
        H3("Sequence diagram"),
        FIG(F.diag("07_sequence_diagram.png"), DIAGRAMS[6][3], 5.8),
        P(DIAGRAMS[6][4]),
        H3("Use-case diagram"),
        FIG(F.diag("08_use_case_diagram.png"), DIAGRAMS[7][3], 5.4),
        P(DIAGRAMS[7][4]),
        H3("Core algorithm flowchart"),
        FIG(F.diag("10_core_algorithm_flowchart.png"), DIAGRAMS[9][3], 4.6),
        P(DIAGRAMS[9][4]),
        H2("5.5 Database design"),
        FIG(F.diag("09_er_diagram.png"), DIAGRAMS[8][3], 5.4),
        P(DIAGRAMS[8][4]),
        *schema_blocks(),
        H2("5.6 Module design"),
        P("Each pipeline stage is one module with one public entry point, and each module imports only the stages before it. This is what lets the unit tests "
          "of Chapter 7 call `extract_structured_tests` or `classify_result` directly with no database and no server."),
        TAB("Modules, sizes and responsibilities", ["Module", "Lines", "Responsibility", "Key functions"], MODULES, widths=[1.5, 0.5, 2.3, 2.0], size=9, align=["l", "r", "l", "l"]),
        H2("5.7 API design"),
        P("The API is JSON over HTTP. Errors use the FastAPI body `{\"detail\": \"message\"}`; the interface shows the message as it is, so every message was written "
          "for the user: for example \"Please select two different reports.\" The status codes are 401 for a missing, forged or expired token, 404 for an unknown "
          "report, 400 when the two reports to compare are the same, 409 when sample reports are requested for a non-empty library, and 422 for a malformed "
          "request. A report that cannot be processed is **not** an HTTP error: `POST /api/reports` answers 200 with `status` set to `Failed` and the reason in `error`, "
          "because the failure is a normal outcome of a user-supplied file and the report is kept in the list."),
        TAB("REST endpoints", ["Method", "Path", "Token", "Purpose"], ENDPOINTS, widths=[0.7, 1.6, 0.5, 3.5], size=9, align=["c", "l", "c", "l"]),
        H2("5.8 User interface design"),
        P("The interface follows the Depth Studio design kit: layered dark surfaces with soft elevation, an emerald accent, the Sora, Inter and JetBrains Mono "
          "typefaces, and a light theme chosen with a toggle whose choice is stored in the browser (`ll-theme`). Status carries meaning through colour **and** text: "
          "green for Normal, amber for Low and red for High, each badge spelling the word, so colour is never the only signal. Every page repeats the "
          "reminder \"Educational tool - not a medical device\" in the header, and pages that show results end with the full medical disclaimer returned by `/api/config`."),
        P("The shell is a fixed sidebar with eight entries and a link back to the landing page; on narrow screens it becomes a drawer. Routes are code-split and loaded lazily, with a skeleton shown "
          "while a page loads. Every list has an empty state that says what to do next, and the empty dashboard offers to load the sample reports. Every request that "
          "can fail shows an error panel naming the problem (for example that the backend on port 8308 cannot be reached) with a Try again button."),
        TAB("Screens and the screenshots that show them (Chapter 8 and Appendix C)", ["Screen and route", "Screenshot nos.", "Content"], SCREENS, widths=[1.6, 0.7, 4.0], size=9),
        FIG(F.shot("04_dashboard.png"), "The dashboard: totals, a critical-result banner and the six reports of the demonstration library", F.shot_w(F.shot("04_dashboard.png"), 5.6)),
        FIG(F.shot_view("07_report_analysis.png", 1500), "The report analysis screen: extracted rows with status badges and insight cards (top of the page)", F.shot_w(F.shot_view("07_report_analysis.png", 1500), 5.6)),
        P("Accessibility was designed in: a skip link is the first tab stop, every control has a visible focus ring and a label, the navigation drawer closes with "
          "the Escape key, loading regions are marked busy, and motion is reduced when the operating system asks for it (the landing page then shows a static image "
          "instead of the three-dimensional scene). Chapter 7 lists the automated checks."),
        H2("5.9 Security design"),
        P("The product handles health data, so the design states what it protects and what it does not. Access is gated by a signed token (HMAC-SHA256, 12 hours) "
          "sent in the `Authorization` header; every route except health, configuration and login requires it. Uploads are limited to four extensions and 15 MB, "
          "all SQL goes through the ORM, and cross-origin requests are accepted only from the two local interface origins. The design does **not** provide "
          "per-user data separation, HTTPS, password hashing (there is one configured demonstration account) or an audit log, and the configuration route "
          "returns the demonstration password so that the sign-in page can offer a one-click button. These are limits of a demonstration build; Chapter 6 gives "
          "the controls in detail and Chapter 10 the steps needed for real use."),
    ]
