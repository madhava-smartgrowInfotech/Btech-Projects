"""Chapter 5 content: architecture, workflow, DFDs, UML, database, modules, user interface; plus the diagram registry."""
from __future__ import annotations

from doc_common import DIAG, LAT, PRODUCT, ROOT, ROUTES_PROTECTED, ROUTES_PUBLIC, RULE_ENTRIES, RULES_QUALITY, RULES_SECURITY, SHOTS, SIZE


def loc(*paths: str) -> int:
    """Non-blank lines of the given project files (so the module table never drifts from the code)."""
    n = 0
    for p in paths:
        n += sum(1 for ln in (ROOT / p).read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip())
    return n


ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]

DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of AutoSecAI",
                     ["The diagram shows five bands. At the top are the users: a developer who signs in (or uses the seeded demo account) and a visitor who sees "
                      "only the public landing page. Below is the React 19, TypeScript, Vite 8 and Tailwind 4 web application on port 5311, with lazily loaded "
                      "pages, a data layer (TanStack Query and axios) that attaches the JWT and polls background jobs, and the Aurora Glass interface kit.",
                      "The backend band is a FastAPI application on port 8311. A REST layer exposes authentication, metadata, reviews, jobs, exports, the codebase "
                      "assistant and the Model Lab; beside it sit `auth.py` (bcrypt and JWT) and the thread-based job runner. Beneath it are the seven engine "
                      "modules that already existed: input handling (`diffutil.py`), the AST and taint rule engine (`rules.py`), metrics and model "
                      "(`metrics.py`, `mlmodel.py`), the seven-agent pipeline (`agents.py`), the rule knowledge base (`knowledge.py`), repository retrieval "
                      "(`codeintel.py`) and exporters and history (`report.py`, `store.py`).",
                      "The optional language-model layer (`llm.py`) is used only when an Anthropic key is supplied. Storage is local (`app.db`, `history.db` and the "
                      "trained artefacts); the only external services are GitHub and, optionally, the Anthropic API."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow",
                 ["The ten steps run in two rows. Steps 1 and 2 are the user's: sign in and choose one of five inputs (the demo, a pasted diff, two versions of a "
                  "file, a GitHub pull-request link, or files, a zip or a folder). Steps 3 to 9 are the seven agents: Ingestion, Static Analysis, ML Risk, "
                  "Security Reasoner, Remediation, Quality Reviewer and Judge, run in a background job whose progress the interface polls. Step 10 is the review "
                  "screen. The grey strip names the two side paths, the codebase assistant and the Model Lab, and the top line states the design rule that "
                  "nothing is merged or posted automatically."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
             ["AutoSecAI is one process with four external entities. The developer sends credentials, pull-request URLs, diffs, files, questions and settings "
              "and receives a verdict, findings, patches, charts, exports and answers. Local files supply source code. GitHub returns a diff or a repository "
              "archive for a URL. The Anthropic API receives text only when the optional language-model mode is on."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1",
             ["Level 1 has six processes: authentication (1.0), ingestion (2.0), the seven-agent review (3.0), export and history (4.0), the codebase assistant "
              "(5.0) and the Model Lab (6.0), and six stores: users (D1), reviews (D2), model artefacts (D3), rule knowledge base (D4), job table (D5) and "
              "repository indexes (D6). Every result that must survive a restart goes through 4.0 into D2, while jobs and indexes stay in memory; the Model Lab "
              "only reads the artefacts and never writes to the history."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: the seven-agent review (process 3.0)",
             ["Process 3.0 is expanded into its seven agents, following `review_changes()`. The change set enters ingestion (3.1); hunks and line numbers go to "
              "static analysis (3.2); findings and functions go to ML risk (3.3), which reads the model artefacts. The reasoner (3.4) reads the knowledge base "
              "for CWE, OWASP, impact and flow text, and remediation (3.5) reads the fix templates. Quality issues pass from 3.2 to the quality reviewer "
              "(3.6). The judge (3.7) de-duplicates, computes the score and verdict and hands the review record to process 4.0."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram",
                ["The signed-in developer has eight use cases: sign in, register or use the demo account; start a review through any of five inputs; watch the "
                 "agents work; read findings, patches and ML evidence; export Markdown, SARIF, JSON, CSV or patched files; use the history; index a repository and "
                 "ask questions; and use the Model Lab. A visitor can only view the landing statistics. GitHub attaches to starting a review and the optional "
                 "Anthropic API to reading findings and repository questions."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram: running a review and opening the result",
                 ["The participants are the developer, the React app, FastAPI, a job thread, `review_changes` and the history database. The app posts the request "
                  "with the JWT; FastAPI checks the token and input, starts a job and answers `202` with a job identifier. The job thread runs `review_changes`, "
                  "which reports one message per agent, while the app polls the job and receives `running` with the messages so far. When the review is saved the "
                  "next poll returns `done`; the app loads the whole review and shows it, and the last arrow requests an export. The polling "
                  "interval of the implemented hook is 350 ms."]),
    "er": ("06_er_diagram.png", "Database design: two SQLite files",
           ["The file `app.db` holds one table, `users` (key, unique e-mail, name, bcrypt hash, creation time). The file `history.db` holds one table, `reviews` "
            "(eight-character identifier, creation time, title, source, score, verdict, two counters) and a `payload` column with the complete review as JSON. "
            "The lower box lists the logical parts of that payload (findings, ML rows, trace, files, statistics, patched files), which are not separate tables. "
            "The dotted note records a limitation: the tables are not linked, so a review has no user identifier and the history is shared by all accounts."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram",
            ["The upper row shows the domain types: `ChangedFile`, `Finding` (rule, location, confidence, severity, optional fix), `Trace` and the review record. "
             "The middle row shows `PyAnalyzer`, which walks the syntax tree and creates findings, the model module, and `RepoIndex` with its chunks, graph and "
             "TF-IDF matrix. The bottom row shows `review_changes()` with its agent functions, the backend objects (the job table and the table of six "
             "repository indexes) and the store and report functions. Dashed arrows are dependencies; 1..* records that a review contains many findings."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowchart of the core algorithm, review_changes()",
                  ["The left column shows the first half. After ingestion, a decision checks whether the full new source is known: if so the whole file is analysed "
                   "and each finding is marked inside or outside the change; otherwise each hunk is analysed with its line offset. If the ML agent is enabled every "
                   "function is scored. The right column continues with the reasoner, the remediation agent (apply a fix, re-scan, keep the patch only if the "
                   "finding is gone) and the quality and judge step.",
                   "The score is `round(100 x (1 - exp(-W / 18)))`, with W the sum of severity times confidence weights and findings outside the change counted at "
                   "15 %. A high or critical security finding in the change (medium or higher confidence), or a score of 70 or more, gives BLOCK; otherwise a "
                   "medium finding in the change, or a score of 30 or more, gives REQUEST_CHANGES; otherwise APPROVE. The record is then saved to the history."]),
}


def diagram(d, key, width=None):
    fname, caption, paras = DIAGRAMS[key]
    d.figure(DIAG / fname, caption, width=width, max_h=4.0)
    for p in paras:
        d.p(p)


def sec_arch(d):
    d.h2("System Architecture")
    d.paras(f"{PRODUCT} is a single-machine application with two front doors and one engine. The engine is a Python package of "
            f"{SIZE['engine_py']:,} non-blank lines in fourteen modules that already existed when the project began: it parses changes, analyses them, "
            "scores functions, explains and patches findings, indexes repositories and writes reports. The first front door was a Streamlit page, which was left unchanged; in the final phase a thin FastAPI layer "
            f"({SIZE['backend_py']} lines), accounts and a React application ({SIZE['frontend_ts']:,} lines in {SIZE['frontend_files']} files) were added. "
            "The figure below shows the layers.")
    diagram(d, "architecture")
    d.p("Four principles shaped the design. **Evidence before opinion**: every finding is tied to a rule, a line and, where possible, an independent "
        "signal from the metric model, so that a reviewer can see why it was raised. **Verify every fix**: a patch is offered only after it has been applied "
        "to a copy of the source and the analysis has been run again. **Keep the work local**: parsing, analysis, model scoring and retrieval run on "
        "the user's machine, and the optional language-model layer is off by default. **Say what is missing**: when an input cannot support a result "
        "(for example a bare diff cannot yield a whole-file fix), the interface says so instead of hiding it.")
    d.p("The seven agents are deterministic software components that pass results through a shared trace; they are not language-model processes. "
        "The optional language-model text layer was not measured, and every result in this document was obtained without it.")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    d.p("The workflow below is the path of a single review, from sign-in to the stored result.")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("The data-flow diagrams describe how data moves through AutoSecAI at three levels of detail: the context, the six main processes, and the "
        "expansion of the review process into its seven agents.")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("Three UML views describe the design: the use-case diagram shows who can do what, the sequence diagram shows how the main flow runs, and the "
        "class diagram shows what the code contains. The algorithm itself is shown as a flowchart in the methodology chapter and in the collection of "
        "diagrams.")
    diagram(d, "usecase")
    diagram(d, "sequence")
    diagram(d, "uml")


def sec_database(d):
    d.h2("Database Design")
    d.paras("Persistence uses SQLite through Python's standard library. Two files are used so that the account store, which belongs to the new web "
            "layer, is separate from the history store, which belongs to the original engine. A review is always read and written as a whole and is never "
            "queried field by field, so it is stored as one JSON document with a few indexed columns for the list view; this keeps the schema stable "
            "when the review structure grows.")
    diagram(d, "er")
    d.table([["File / table", "Column", "Type", "Notes"],
             ["app.db / users", "id", "INTEGER, primary key, auto-increment", "Subject of the JWT"],
             ["", "email", "TEXT, UNIQUE, NOT NULL", "Stored in lower case; format checked on registration"],
             ["", "name", "TEXT, NOT NULL", "At least two characters"],
             ["", "password_hash", "BLOB, NOT NULL", "bcrypt, 10 rounds; passwords cut at 72 bytes"],
             ["", "created", "TEXT, NOT NULL", "UTC ISO time"],
             ["history.db / reviews", "id", "TEXT, primary key", "Eight hexadecimal characters"],
             ["", "created, title, source", "TEXT", "Shown in the history table"],
             ["", "score, verdict", "INTEGER, TEXT", "Score 0-100; APPROVE, REQUEST_CHANGES or BLOCK"],
             ["", "n_findings, n_security", "INTEGER", "All findings; security findings inside the changed lines"],
             ["", "payload", "TEXT (JSON)", "Findings, ML rows, trace, files, statistics, patched files, summary"]],
            "Database tables and columns", widths=[0.2, 0.2, 0.28, 0.32], font=9)
    d.p("The demo account is inserted at start-up if it does not exist. Deleting a review removes its row; there is no cascade because there is no "
        "relation. Two further stores exist in memory only: the job table (jobs older than one hour are dropped whenever a new job starts) and the "
        "table of repository indexes, which keeps the six most recently created indexes. Both disappear when the API process stops, which is acceptable "
        "because a job is short and an index can be rebuilt in milliseconds.")


def sec_modules(d):
    d.h2("Module Design")
    d.p("The table lists the modules with their real size, counted as non-blank lines of the files in the repository.")
    rows = [["Module", "File", "Lines", "Responsibility"],
            ["Input handling", "autosecai/diffutil.py", str(loc("autosecai/diffutil.py")), "Unified-diff parser, before/after diff, zip and folder reader (up to 1,500 files of 800 KB), GitHub pull-request and archive download, fix application and patch generation"],
            ["Static analysis", "autosecai/rules.py", str(loc("autosecai/rules.py")), "Python AST analyser with taint levels, 30 security rules, quality rules, regex rules for JavaScript, PHP and Java, fix generators for SQL and shell calls"],
            ["Rule knowledge base", "autosecai/knowledge.py", str(loc("autosecai/knowledge.py")), f"{RULE_ENTRIES} entries ({RULES_SECURITY} security, {RULES_QUALITY} quality, 1 ML-derived) with CWE, OWASP, severity, explanation, impact, exploit sketch, fix and safe example; weights"],
            ["Metrics", "autosecai/metrics.py", str(loc("autosecai/metrics.py")), "The 14 source-code metrics per function from the Python AST"],
            ["Corpus generator", "autosecai/dataset.py", str(loc("autosecai/dataset.py")), "Generates the labelled Python corpus (8 vulnerability types, hard negatives, label noise)"],
            ["Model", "autosecai/mlmodel.py", str(loc("autosecai/mlmodel.py")), "SMOTE and Tomek links, seven feature selectors, nine classifiers, type classifier, ablation, persistence and prediction"],
            ["Agents", "autosecai/agents.py", str(loc("autosecai/agents.py")), "The seven-agent pipeline, risk score and verdict"],
            ["Codebase intelligence", "autosecai/codeintel.py", str(loc("autosecai/codeintel.py")), "Chunking, TF-IDF, concept detection, import and call graph, question answering, overview and onboarding guide"],
            ["Reports and history", "autosecai/report.py, store.py", str(loc("autosecai/report.py", "autosecai/store.py")), "Markdown, SARIF 2.1.0, JSON and CSV exporters; SQLite history"],
            ["Optional LLM", "autosecai/llm.py", str(loc("autosecai/llm.py")), "Thin client used only when a key is supplied"],
            ["Sample data", "autosecai/samples.py", str(loc("autosecai/samples.py")), "Demo pull request, before/after pair and demo repository"],
            ["REST API", "backend/main.py", str(loc("backend/main.py")), f"{ROUTES_PUBLIC} public and {ROUTES_PROTECTED} protected routes, job runner, repository indexes, uploads, exports"],
            ["Accounts", "backend/auth.py", str(loc("backend/auth.py")), "Registration, login, bcrypt, JWT, demo account"],
            ["Web application", "frontend/src", f"{SIZE['frontend_ts']:,}", f"{SIZE['frontend_files']} TypeScript files: ten pages, review components, lab tabs, charts, interface kit"],
            ["Original UI", "app.py, autosecai/ui.py", str(loc("app.py", "autosecai/ui.py")), "Streamlit front end (unchanged, not run in the final tests)"],
            ["Tests", "tests/", str(SIZE["tests_py"]), "Engine and API tests"]]
    d.table(rows, f"Modules of {PRODUCT} (non-blank lines)", widths=[0.15, 0.2, 0.07, 0.58], font=8.5)
    d.p("The dependencies run in one direction. The web application depends on the API; the API depends on the engine; the engine modules depend on each "
        "other in a simple chain (diffutil and rules feed agents; metrics feed mlmodel; knowledge is read by rules and agents). The engine has no "
        "knowledge of the API, which is why the Streamlit page and the API can coexist.")


def sec_ui(d):
    d.h2("User Interface Design")
    d.paras("The web application has ten screens: the public landing page and the sign-in page, and, behind the sign-in, the overview, the new-review "
            "page, the review result, the codebase assistant, the Model Lab, the history, the settings and the about page, plus a friendly not-found page. A "
            "sidebar on wide screens and a drawer on phones give access to the sections, and a skip link lets keyboard users jump to the content.",
            "The interface is built on a shared kit called Aurora Glass (translucent panels over a dark aurora background, with a light theme as well). "
            "Design decisions follow from the purpose of the product. The verdict is the first thing on a review page and uses both colour and a text "
            "label, so the meaning never depends on colour alone. Severities are shown as badges with their names. Every finding card expands to the "
            "explanation, impact, remediation, a safe pattern and, where one exists, a verified patch. Every asynchronous screen has a loading state, an "
            "empty state and an error state that says what failed and offers a retry; the 'API unreachable' case is covered by an automated test.")
    d.paras("Four non-negotiable properties were applied to all screens: the theme (dark by default, light on request) persists across reloads; the "
            "reduced-motion setting of the operating system is honoured, and the animated pinned section of the landing page falls back to a plain list; "
            "every screen is laid out from 360 pixels upwards without horizontal scrolling (checked at 360 and 768 pixels in light and dark mode); and every "
            "control is reachable and operable with the keyboard, with a visible focus ring and Escape closing dialogs and the mobile drawer.")
    d.figure_pair([(SHOTS / "04_overview.png", "Overview screen: three entry cards and the seven agents"),
                   (SHOTS / "05_review_new_demo.png", "New review screen with the five input modes")], width=3.1, max_h=2.3)
    d.figure_pair([(SHOTS / "26_review_verdict.png", "Review result: verdict banner, gauge and four counters"),
                   (SHOTS / "12_codebase_ask.png", "Codebase assistant: suggested questions and a cited answer")], width=3.1, max_h=2.3)
    d.p("The screens are shown in full size in the chapter on results and in the appendix of additional screens.")
