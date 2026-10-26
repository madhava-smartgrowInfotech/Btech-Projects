"""Chapters 3 (feasibility) and 4 (requirements and analysis)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

FUNCTIONAL = [
    ["FR1", "Sign in with the demo account (e-mail and password, or the demo button) and sign out; every route except health, config and login needs a bearer token.", "Must"],
    ["FR2", "Upload a report by file picker or drag and drop; accept PDF, JPG, JPEG and PNG up to 15 MB.", "Must"],
    ["FR3", "Validate the upload and give a readable reason on failure: unsupported type, empty file, oversize file, unreadable PDF, no recognisable test rows.", "Must"],
    ["FR4", "Extract text: PDF text layer first; pages with fewer than 30 characters, and image files, go through OpenCV pre-processing and Tesseract OCR.", "Must"],
    ["FR5", "Extract test name, numeric result, unit, reference range (two-sided and one-sided) and report date from each line, with a confidence score.", "Must"],
    ["FR6", "Normalise noisy test names to the 55-name dictionary and keep unseen names as printed text in title case.", "Should"],
    ["FR7", "Classify each result as LOW, NORMAL, HIGH or UNKNOWN against its own reference range.", "Must"],
    ["FR8", "Generate a plain-language insight (what it measures, general causes, suggestion) for every LOW and HIGH result; offer an optional LLM rewrite when a key is configured.", "Must"],
    ["FR9", "Store every report, its test results, insights, raw text and processing status (Pending, Processing, Completed, Failed) in the database.", "Must"],
    ["FR10", "Show a dashboard: report, test, normal, abnormal and critical counts, recent reports and a status breakdown.", "Should"],
    ["FR11", "List reports with search, sort and delete (after confirmation); open one report with its results table and insight cards.", "Must"],
    ["FR12", "Show the trend of one test across all reports as a chart with the reference band and an overall direction.", "Must"],
    ["FR13", "Compare two different reports test by test and show the change in each value.", "Should"],
    ["FR14", "Show an insights page that covers every abnormal result across all reports.", "Should"],
    ["FR15", "Offer to load five synthetic sample reports when the library is empty, by running them through the real pipeline.", "Should"],
    ["FR16", "Show the medical disclaimer on every screen; offer light and dark themes.", "Must"],
    ["FR17", "Return a clear not-found response for an unknown report id.", "Must"],
]

NONFUNCTIONAL = [
    ["Performance", "A text-layer PDF passes the whole pipeline in well under the 10 s of the abstract.", "Median 52.7 ms for a 14-row report including the database write; 209.8 ms median (p95 414.2 ms) through the HTTP upload"],
    ["Reliability", "A failed upload keeps its error message and never breaks the library; every stage failure marks the report Failed.", "tests/test_lablens.py (blank, corrupt, oversize, wrong type); smoke checks on failed reports"],
    ["Security", "Signed 12-hour token, tampered token rejected, CORS limited to the local front end, file-type whitelist and size limit.", "test_api_requires_login, test_api_tampered_token_rejected; shared demo account only"],
    ["Usability", "Every screen usable from 360 px to 1440 px, by keyboard, in light and dark themes, with reduced motion respected.", "scripts/ui_check.py exists; not re-run in the documentation pass"],
    ["Portability", "Windows start-up with one script; manual start on any operating system.", "run.bat; docs/03_HOW_TO_RUN.md"],
    ["Maintainability", "Pipeline modules, API layer and front end are separate; behaviour is covered by automated tests.", "36 pytest tests; 24 API and 7 browser smoke checks"],
    ["Privacy", "Reports stay in a local SQLite file; nothing leaves the machine unless the optional LLM switch is used.", "Code review of backend/main.py and ai_insights.py"],
    ["Honesty of output", "Insights must not diagnose and must carry a disclaimer; accuracy figures must say how they were measured.", "Disclaimer on every output; Chapters 7 and 8"],
]


def blocks():
    lat = F.LATENCY["end_to_end_pipeline_with_db"]["median_ms"]
    up = F.API_LAT["endpoints"]["POST /api/reports (PDF upload)"]["median_ms"]
    ch3 = [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical feasibility"),
        P("The abstract proposes PP-OCR, a CRF-based named-entity recogniser, retrieval-augmented generation, Supabase, Tailwind CSS and Google Cloud Functions. "
          "The project that was built uses lighter tools for each, chosen after checking what each proposed component would need."),
        TAB("Proposed technology and what was built", ["Abstract proposes", "Built", "Reason and consequence"], [
            ["PP-OCR [12]", "PyMuPDF text layer, plus OpenCV clean-up and Tesseract [13] for images", "Digital PDFs already contain exact text, read in about 1.5 ms, so OCR is not needed for them. Tesseract is one executable; PP-OCR needs a deep-learning runtime. Consequence: image OCR is implemented but was not measured, because Tesseract was not installed on the test machine."],
            ["CRF-based NER [14]", "Regular-expression line parser plus a TF-IDF matcher [15], [16]", "A CRF needs an annotated corpus of report lines, and none exists for this project. The parser is transparent and fast but layout-dependent (Chapter 8)."],
            ["RAG over trusted sources [1], [6]", "Rule-based knowledge text for 17 tests plus a generic fallback; optional LLM rewrite", "A retrieval corpus (the base paper used 20 books and 383 transcripts) was not available. Hand-written text cannot hallucinate but covers only 30.9% of the dictionary tests, and there are no citations."],
            ["Supabase (PostgreSQL, row-level security)", "SQLite through SQLAlchemy [19]", "No account or network needed; consequence: one shared library, no per-user isolation."],
            ["React, Tailwind, Recharts", "React 18.3, Vite 5.4, Recharts 2.15 [22], hand-written CSS", "Same front-end stack except Tailwind."],
            ["Google Cloud Functions, under 10 s", "FastAPI [21] with Uvicorn on a local machine", "Not serverless and not deployed. The 10 s target is met for text-layer PDFs; it is not tested for scans."],
        ], widths=[1.4, 1.8, 3.1], size=9),
        P("Every library used is mature and open source, and the whole stack ran on one ordinary desktop without a GPU. The technical risks found were: the absence of "
          "labelled data for evaluation, which was handled by generating a labelled corpus; the lack of Tesseract on the development machine, which leaves the image path unmeasured; and "
          "layout sensitivity of the parser, which is measured and reported rather than hidden."),
        H2("3.2 Economic feasibility"),
        P("No licence, cloud service or special hardware was bought. Python, PyMuPDF, OpenCV, scikit-learn, SQLAlchemy, FastAPI, React and Vite are open source, and "
          f"the machine already existed. A report costs only processor time: a median of {lat:.1f} ms for a 14-row PDF. The single optional cost is the LLM rewrite, which calls "
          f"a paid API {n(23)} only if a key is set and the user turns the switch on; without it nothing is charged and the built-in text is used."),
        TAB("Cost view", ["Item", "Cost to the project", "Remark"], [
            ["Software and libraries", "None", "Open-source licences"],
            ["Training data", "None", "No model is trained; the evaluation corpus is generated by script"],
            ["Hardware", "None additional", "Intel Core i5-12500, 15.7 GB RAM, no GPU"],
            ["Hosting", "None", "Runs locally on ports 8308 (API) and 5308 (interface)"],
            ["Optional LLM rewrite", "Pay per call, off by default", "Requires `ANTHROPIC_API_KEY`; not exercised in this work"],
            ["Clinical validation and certification", "Not budgeted", "Out of scope (Section 1.6)"],
        ], widths=[2.4, 1.6, 2.4]),
        H2("3.3 Operational feasibility"),
        P("A person with no technical background can use the interface: one clear upload action, plain-language result cards, a visible disclaimer and explicit empty, loading and "
          "error states. On an empty library the screens offer to load sample reports, so the product can be seen working before any real file is uploaded. Start-up is a single "
          "script, `run.bat`, which builds the Python environment, installs the packages and opens the browser. There is nothing to administer, because the SQLite file is created on first run. "
          "The operating limits are a shared demo account and local, unbacked-up storage."),
        H2("3.4 Schedule feasibility"),
        P("The work divides into: selecting the base paper and writing the abstract, objectives and survey; the extraction and classification pipeline; the explanation module and "
          "database; the web interface; testing and measurement; and documentation. Interfaces between the pipeline modules are narrow, so the web interface could be built over "
          "them without changing them. The table below lists the stages with the last-modified dates of the artefacts that record them."),
        TAB("Schedule, from the last-modified dates of the project artefacts", ["Stage", "Artefact", "Date (2026)"], [
            ["Abstract, base paper record, introduction, survey, objectives", "Batch documents 2 to 6", "31 August"],
            ["Batch details and team confirmed; first review deck", "1.A8_BATCH_DETAILS.docx, 7.Review_1_PPT.pptx", "19 September"],
            ["Pipeline modules (OCR, extraction, classification, insights, database)", "Python modules in 8.ProjectCode", "14 October"],
            ["FastAPI layer, React interface, screenshots", "backend/, frontend/, docs/screenshots", "24 October"],
            ["Measurements, tests and report facts", "experiments/lablens, tests/, docs/REPORT_FACTS.md", "25 October"],
        ], widths=[2.8, 2.5, 1.0], size=10),
        P("The dates are file timestamps, not a project plan. They show that the stages ran in the order above and that measurement came last, which is why the evaluation uses a "
          "generated corpus: there was no time budget to collect and hand-label real reports."),
        H2("3.5 Legal and ethical considerations"),
        P("Lab reports are personal health information. The system keeps them on the local machine and sends nothing to third parties unless the optional LLM rewrite is switched on, "
          "in which case only the test name, its status and the built-in explanation text are sent, not the numeric result, the patient name or the report. All sample data and the evaluation corpus are invented. Because health decisions are "
          "involved, every page states that the output is educational, and the explanations avoid diagnosis, in line with the safety trade-off reported for check-up action cards "
          f"{n(3)}."),
        H2("3.6 Advantages and constraints"),
        B("**Advantages:** open and inspectable code; no GPU or paid service; fast (median 52.7 ms per text-layer report); a complete path from file to trend; automated tests; measured and published failure modes.",
          "**Constraints:** parser tied to line-per-test layouts; unit list incomplete; explanations cover 17 of 55 tests; image OCR unmeasured; evaluation on generated data; one shared demo account."),
    ]

    ch4 = [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing system and its limitations"),
        P("Today a patient receives a report as a PDF or a printout and either waits for a consultation or searches each test name online. Laboratory portals digitise the values "
          f"but rarely explain them. Research prototypes explain reports with language models {n(1, 3, 4, 5)} but are distributed as papers, not as running applications, and "
          "none keeps a patient's history."),
        B("**Manual reading:** slow, and prone to over- or under-reacting to a flagged value.",
          "**Digitisation without explanation:** values are stored but their meaning is not given.",
          "**Explanation without extraction or history:** the base paper [1] explains one condition and keeps no record of values across reports.",
          "**The original project code:** the Streamlit prototype (`app.py`) had the pipeline but no login, no API and no tests."),
        H2("4.2 Proposed system and its advantages"),
        P("The proposed system, LabLens, keeps the original pipeline modules unchanged and adds a FastAPI service and a React interface over them, a demo login, trends, comparison, an "
          "insights page, sample data, measurements and tests."),
        B("One upload turns a PDF or an image into a table of tests with a status for each.",
          "Every abnormal value gets a plain-language card with a disclaimer.",
          "Each test can be followed across reports on a chart with its reference band, and two reports can be compared directly.",
          "The accuracy, speed and failure modes of each stage are measured and reproducible by one script.",
          "Everything runs locally with open-source software."),
        H2("4.3 Functional requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Priority"], FUNCTIONAL, widths=[0.5, 4.8, 0.8], align=["c", "l", "c"], size=10),
        H2("4.4 Non-functional requirements"),
        TAB("Non-functional requirements and how each is verified", ["Quality", "Requirement", "Evidence"], NONFUNCTIONAL, widths=[1.1, 2.6, 2.6], size=9),
        H2("4.5 Hardware requirements"),
        TAB("Hardware", ["Item", "Used for development and measurement", "Suggested minimum (not tested)"], [
            ["Processor", "Intel Core i5-12500 (6 cores, 12 threads)", "Any recent dual-core x86-64 processor"],
            ["Memory", "15.7 GB RAM", "4 GB"],
            ["Graphics", "None used", "Not required"],
            ["Storage", "A few hundred MB for the Python and Node environments", "2 GB free"],
            ["Display", "1440 x 900 reference; layout checked down to 360 px", "Any modern browser"],
        ], widths=[1.3, 3.0, 2.0]),
        H2("4.6 Software requirements"),
        TAB("Software", ["Layer", "Software"], [
            ["Operating system", "Windows 11 Pro (development and measurement); any system that runs Python and Node.js"],
            ["Language and runtime", "Python 3.11.9; Node.js 24 used, 20 or newer required"],
            ["Reading and recognition", "PyMuPDF 1.28, OpenCV 4.11 (headless), Pillow, pytesseract with the Tesseract OCR program (optional, for images and scans)"],
            ["Language processing", "scikit-learn 1.5 (TF-IDF matcher), NumPy 1.26; spaCy optional for the patient name; Anthropic SDK optional"],
            ["Web back end", "FastAPI 0.143, Uvicorn 0.54, python-multipart, python-dotenv, SQLAlchemy 2.0 with SQLite; Streamlit for the original interface"],
            ["Front end", "React 18.3, Vite 5.4, React Router 6, Recharts 2.15, Framer Motion, GSAP, Lenis, three.js (landing visual), lucide-react"],
            ["Testing", "pytest, FastAPI TestClient, Playwright for the browser checks, matplotlib for the measurement figures"],
        ], widths=[1.6, 4.7], size=10),
        H2("4.7 User roles"),
        TAB("Roles", ["Role", "Description", "Access"], [
            ["Patient or reader", "Signs in with the demo account, uploads reports, reads results, trends and insights", "All screens of the web application"],
            ["Developer", "Starts the servers, runs the tests and the measurement scripts", "Command line (`run.bat`, `scripts/`)"],
        ], widths=[1.5, 3.2, 1.6]),
        H2("4.8 Constraints"),
        B("The parser expects one test per line in name, result, unit, range order or a close variant.",
          "Inputs are PDF, JPG, JPEG or PNG files of at most 15 MB, in English.",
          "The reference range printed on the report is trusted as given.",
          "The system is a research prototype and must not be used for clinical decisions.",
          f"One shared demo account; there is no registration and no per-user separation of data. Through the HTTP interface a PDF upload takes a median of {up:.0f} ms."),
    ]
    return ch3 + ch4
