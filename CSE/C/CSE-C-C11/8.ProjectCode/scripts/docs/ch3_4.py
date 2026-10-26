"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for FINJARVIS."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import N as C


def blocks():
    return chapter3() + chapter4()


def lat(prefix, key="median_ms"):
    return F.lat(prefix, key)


# =====================================================================================================================
def chapter3():
    c = F.CLS
    imp = F.IMP
    s_dash, s_ana, s_txn = lat("GET /dashboard"), lat("GET /analytics"), lat("POST /transactions (auto")
    s_login, s_pdf, s_xl = lat("login"), lat("GET /reports/pdf"), lat("GET /reports/excel")
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical Feasibility"),
        P("Can the categoriser, forecast, health score, assistant and web console be built with tools that an ordinary desktop supports, and are they fast enough to feel interactive? Each part was built and measured; the table lists the evidence."),
        TAB("Technical feasibility: components and the evidence for each", ["Component", "Technology", "Evidence that it is feasible"],
            [["Web API", f"FastAPI, pydantic validation, one bearer-token dependency", f"{F.N_ROUTES} routes built; {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} smoke checks pass; dashboard answers in {s_dash:.1f} ms (median)"],
             ["Data store", f"SQLite file through SQLAlchemy 2 {C('sqla')}", f"{F.N_TABLES} tables, cascade delete, per-user scoping; transaction list {lat('GET /transactions'):.1f} ms (median)"],
             ["Categoriser", f"TF-IDF + logistic regression (scikit-learn) {C('sklearn')}", f"Trains in {c['retrain_ms_seed_only']:.1f} ms and predicts in {c['predict_ms_per_description']:.2f} ms on one CPU thread; {c['tfidf_lr']['accuracy'] * 100:.1f} % probe accuracy"],
             ["Forecast and health score", "NumPy least squares; pure-Python weighted sum", "No training; deterministic; 5,000 random profiles scored without error"],
             ["Passwords and sessions", f"bcrypt {C('bcrypt')}; HMAC-SHA256 tokens", f"Login takes {s_login:.0f} ms (median) because bcrypt is deliberately slow; tampered tokens rejected in tests"],
             ["Reports", "ReportLab (PDF), OpenPyXL (Excel), CSV", f"PDF {s_pdf:.0f} ms, Excel {s_xl:.0f} ms, CSV {lat('GET /reports/csv'):.0f} ms (median)"],
             ["Front end", "React 18, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Query", f"{F.N_PAGES} pages and 19 screens captured at 1440 x 900"],
             ["Import", "pandas file reading with row-level checks", f"1,000 rows with 84 bad rows: all 84 skipped, {imp['rows_imported']} imported and categorised"]],
            widths=[1.2, 2.2, 3.0], align=["l", "l", "l"], size=9.5),
        P("Three risks were examined. **Data volume**: no corpus of labelled narrations is available, so the model is small and its weakness is measured. "
          "**Library drift**: the pickled model was trained under scikit-learn 1.5.0 and loads under 1.9.1 with a warning; retraining takes milliseconds. "
          f"**Hashing library**: passlib needs bcrypt 4.0.1 (bcrypt 5 breaks it), which is pinned. The system is technically feasible on a single desktop with no GPU and no paid service."),
        H2("3.2 Economic Feasibility"),
        P("The whole stack is open source, so licence cost is zero. The remaining costs are the team's time and ordinary hardware."),
        TAB("Cost items", ["Item", "Cost for this project", "Note"],
            [["Software licences", "None", "Python, FastAPI, SQLAlchemy, scikit-learn, React, Vite and Tailwind are free and open source"],
             ["Cloud or hosting", "None", "Runs locally; a free tier of a platform host would suffice for a demonstration (a Procfile and railway.json are in the repository, not exercised here)"],
             ["Data", "None", "Seed list and demo data are the team's own; no data purchase"],
             ["Optional language model", "Pay-per-use if enabled", "Only if the user sets an API key; not used in any measurement"],
             ["Optional price refresh", "None", "yfinance reads public prices; needs internet; not exercised here"],
             ["Hardware", "Existing desktop", "Intel Core i5-12500, 15.7 GB, no GPU"],
             ["Team effort", "Four students over the project term", "Time cost only"]],
            widths=[1.6, 1.7, 3.1], align=["l", "l", "l"], size=10),
        P("For a user, the platform replaces a commercial subscription with a free application whose data stays in a local file; the cost of a hosted service was not measured. The batch abstract names affordability as a goal, and the stack meets it."),
        H2("3.3 Operational Feasibility"),
        P("A user needs only a browser. Setup is one command (run.bat) that builds a virtual environment, installs the dependencies, and starts the API and the web application. "
          "A demo account (demo / Demo@1234) is created on first start with fictional data for six months, so every screen has content. "
          f"Daily use is light: adding a transaction takes {s_txn:.0f} ms with automatic categorisation, and the dashboard loads in about {s_dash:.0f} ms. "
          "Entering transactions by hand remains the main effort; the CSV and Excel import, with a preview that lists skipped rows, removes most of it for users who can export statements."),
        P("The risks to operation are those of the design: a user who accepts every automatic category will see unseen merchants labelled Transport, and a user with fewer than three months of history sees no forecast and a message explaining why. "
          "The assistant and the health score carry a disclaimer that they are not financial advice."),
        H2("3.4 Schedule Feasibility"),
        TAB("Project phases", ["Phase", "Work", "Output"],
            [["1. Study", "Read the base paper, survey related work, fix objectives", "Batch abstract, survey, objectives"],
             ["2. Core application", "Database, services, categoriser, forecast, health score, Streamlit interface", "Original working application (app.py, ui/)"],
             ["3. Web platform", "FastAPI layer over the same services, React console, demo account, run.bat", f"{F.N_ROUTES} routes, {F.N_PAGES} pages, smoke test"],
             ["4. Evaluation", "Probe set, backtests, simulations, import and latency measurements, tests", "experiments/metrics.json, api_latency.json"],
             ["5. Documentation", "Diagrams, three decks, chapter documents, report, paper", "The submission set"]],
            widths=[1.2, 3.0, 2.2], align=["l", "l", "l"], size=10),
        P("The phases were sequential except that evaluation scripts were written alongside the web platform. Each module is small: the Python code base is about 2,400 lines and the tests run in under twelve seconds."),
        H2("3.5 Risk Analysis"),
        TAB("Project risks and mitigation", ["Risk", "Likelihood", "Effect", "Mitigation in the project"],
            [["Training data too small for the categoriser", "Certain", "Unseen merchants mislabelled", "Measure it (probe tiers), keep a keyword fallback, learn from corrections, document the gap"],
             ["No real transaction data for evaluation", "Certain", "Results cannot be generalised", "Use fictional demo data and a team-written probe set; label every result as such"],
             ["Library version drift (scikit-learn, bcrypt)", "Observed", "Warnings or broken hashing", "Pin bcrypt 4.0.1; retrain the model when the pickle is stale"],
             ["Forecast over-fits a handful of months", "Likely", "Wrong next-month figure", "Minimum of three months; compare with baselines; report MAPE"],
             ["Optional language model unavailable", "Likely", "Free-form answers missing", "Rule layer answers without it; fixed help text otherwise"],
             ["SQLite file lost or corrupted", "Low", "User records lost", "Single file, easy to back up; tests use a temp database per test"]],
            widths=[1.8, 0.8, 1.4, 2.4], align=["l", "c", "l", "l"], size=9.5),
        H2("3.6 Advantages and Constraints"),
        TAB("Advantages and constraints of the project", ["Advantages", "Constraints"],
            [["Free, local, inspectable models; every decision can be traced to a rule or a word weight", "A 51-example training set limits the categoriser to phrases it has seen"],
             ["One account, one file, one command to start", "Linear trend needs about seven months of history to beat a plain mean"],
             ["Health score with published weights and a named weakest area", "Weights are chosen by the team and not fitted to outcomes"],
             ["Own tests, probe set and measurements reported with their limits", "Probe set is team-written, not an independent benchmark"],
             ["Optional language-model layer without making it a dependency", "Anomaly detection and reinforcement-learning budgeting are not implemented"],
             ["Responsive React interface, light and dark theme, reports in three formats", "Single user per process, SQLite, no migrations, no loan tracker or scheduler"]],
            widths=[3.2, 3.2], align=["l", "l"], size=10),
    ]


# =====================================================================================================================
def chapter4():
    c = F.CLS
    s_dash, s_ana = lat("GET /dashboard"), lat("GET /analytics")
    s_login = lat("login")
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("Before this project the team's starting point was the original FINJARVIS application, a Streamlit program with ten pages (dashboard, transactions, analytics, budgets, goals, investments, assistant, reports, notifications, profile) over the same service layer and SQLite file. "
          "It already categorised transactions, forecast the next month and scored financial health, but it had no HTTP interface, so it could be driven only through Streamlit's own pages."),
        P("More broadly, personal finance is managed with four kinds of tools. **Paper and spreadsheets** need manual entry and formulas the user writes. "
          "**Bank and wallet apps** show a statement and sometimes a category chart, but only for that provider's accounts. **Commercial budgeting apps** add categorisation and budgets, usually behind a subscription with the data held by the vendor. "
          f"**Research prototypes** such as the base paper {C('base')} combine several models but run as notebooks or Streamlit demonstrations on unreleased data."),
        H2("4.2 Limitations of the Existing System"),
        B("Manual entry and manual categorisation make tracking tedious, and most users stop within weeks.",
          "Reports describe the past; few tools forecast the next month or check budgets against a forecast.",
          "Advice is generic and not tied to the user's income, commitments or goals.",
          "Commercial tools cost money and keep the data on the vendor's servers.",
          "Research prototypes cannot be run by an ordinary user, have no authentication and report metrics on data that cannot be checked.",
          "The original Streamlit version has no API and a fixed layout."),
        H2("4.3 Proposed System"),
        P(f"FINJARVIS keeps the service layer and adds a FastAPI application and a React console. A user signs up or logs in, enters or imports transactions, and sees the dashboard. "
          "Behind the screens, a categoriser labels each description, budgets raise alerts, a forecast estimates the next month, a health score summarises six components, and the assistant answers from the user's records. "
          "The back end holds no business logic of its own: each route calls the same service function that the Streamlit page calls."),
        TAB("Modules of the proposed system", ["Module", "File", "Responsibility"],
            [["API", "backend/main.py", f"{F.N_ROUTES} routes, request validation, bearer-token dependency, CORS for the web origin"],
             ["Authentication", "auth/authentication.py, utils/security.py", "Sign-up, login by username or e-mail, bcrypt hashing, password rules"],
             ["Transactions", "services/transaction_service.py", "Add, edit, delete, search, filter; auto-categorise; learn from correction"],
             ["Import", "services/data_import_service.py", "CSV and Excel parsing, row validation, preview and commit"],
             ["Categoriser", "ml/expense_classifier.py", "TF-IDF + logistic regression, keyword fallback, retraining"],
             ["Forecast", "ml/spending_prediction.py", "Linear trend over monthly totals, per-category forecast, budget-overrun check"],
             ["Health score", "ml/financial_health.py", "Six weighted components, bands, weakest-area explanation"],
             ["Budgets and goals", "services/budget_service.py, goal_service.py", "Monthly limits, 75/90/100 % alerts, savings progress"],
             ["Investments", "services/investment_service.py", "Manual holdings, optional live price refresh"],
             ["Analytics and assistant", "services/analytics_service.py, ai_service.py", "Totals, trend, category split; rule-routed answers, insights, optional language model"],
             ["Reports", "services/report_service.py", "PDF, Excel and CSV downloads"],
             ["Database", "database/models.py, database.py", f"{F.N_TABLES} SQLAlchemy models over one SQLite file"],
             ["Front end", "frontend/src", f"{F.N_PAGES} pages, charts, forms, demo-login button"]],
            widths=[1.3, 2.3, 2.8], align=["l", "l", "l"], size=9),
        H2("4.4 Advantages of the Proposed System"),
        TAB("Advantages and the evidence for each", ["Advantage", "Evidence"],
            [["Automatic categorisation", f"{c['tfidf_lr']['accuracy'] * 100:.1f} % probe accuracy against {c['keyword_table']['accuracy'] * 100:.1f} % for the keyword table; {c['tfidf_lr']['accuracy_by_tier']['B'] * 100:.0f} % on statement-style strings"],
             ["Learns from a correction", "Repeat-merchant test: 18.2 % before, 100.0 % after one correction (198 tests)"],
             ["Forward-looking", f"Forecast panel and per-category forecast; refuses with under {F.FC['min_months_required']} months"],
             ["Explainable health score", "Six components with weights; 5,000-profile check shows no violation when the savings rate rises"],
             ["Safe by default", "bcrypt, password rules, signed tokens, per-user scoping; a tampered token and a protected route without a token were rejected in the smoke test"],
             ["Fast", f"Dashboard {s_dash:.0f} ms, analytics {s_ana:.0f} ms (medians, single user)"],
             ["Free and local", "No licence, no cloud, one SQLite file"]],
            widths=[1.9, 4.5], align=["l", "l"], size=10),
        H2("4.5 Data Requirements"),
        P("The system stores six kinds of record and needs the following inputs. All are entered by the user or generated by the demo loader; nothing is fetched from a bank."),
        TAB("Data requirements", ["Data", "Fields", "Source", "Notes"],
            [["User", "name, e-mail, username, password hash, currency, monthly income, risk profile, savings target", "Sign-up form, profile page", "E-mail and username unique"],
             ["Transaction", "date, description, category, amount, type, payment method, notes", "Form, CSV or Excel import, demo loader", "Category suggested by the model"],
             ["Budget", "category, amount, month, year", "Budgets page", "One per category and month"],
             ["Goal", "name, target amount, current amount, target date, status", "Goals page", "Status active, completed or abandoned"],
             ["Investment", "name, symbol, type, quantity, purchase price, current price, date", "Investments page", "Price refresh optional"],
             ["Notification", "message, type, created time, read flag", "Written by budget checks", "De-duplicated by message text"]],
            widths=[1.0, 2.6, 1.6, 1.2], align=["l", "l", "l", "l"], size=9),
        H2("4.6 Functional Requirements"),
        TAB("Functional requirements and how each is met", ["ID", "Requirement", "Implemented by", "Verified by"],
            [["FR1", "Register with name, e-mail, username and a strong password", "POST /auth/signup, validators.py", "tests/test_auth.py; smoke (weak password rejected)"],
             ["FR2", "Log in by username or e-mail and receive a token", "POST /auth/login, authentication.py", "test_auth.py; smoke"],
             ["FR3", "Every data route requires a valid token and returns only the caller's data", "current_user dependency; user_id on every table", "Smoke: 401 without token, new-user isolation"],
             ["FR4", "Add, edit, delete, search and filter transactions", "transaction_service.py; /transactions", "test_transactions.py; smoke"],
             ["FR5", "Suggest a category from a description and learn from corrections", "expense_classifier.py; /transactions/predict-category", "test_ml.py; probe set"],
             ["FR6", "Import CSV or Excel with preview and row-level warnings", "data_import_service.py; /transactions/import/*", "Smoke; 1,000-row import test"],
             ["FR7", "Set monthly budgets and raise alerts at 75, 90 and 100 %", "budget_service.py; notifications", "test_budget.py; smoke"],
             ["FR8", "Create savings goals and update progress", "goal_service.py; /goals", "Smoke"],
             ["FR9", "Record investments and refresh prices when online", "investment_service.py; /investments", "Smoke (refresh not tested)"],
             ["FR10", "Show totals, monthly trend and category split for a period", "analytics_service.py; /analytics, /dashboard", "Smoke (bad range rejected)"],
             ["FR11", "Forecast next month and per-category spending", "spending_prediction.py", "test_ml.py; backtest"],
             ["FR12", "Compute a 0-100 health score with its components", "financial_health.py", "test_financial_health.py; sensitivity study"],
             ["FR13", "Answer questions from the user's data with a disclaimer", "ai_service.py; /assistant/ask", "26-question test"],
             ["FR14", "Download PDF, Excel and CSV reports", "report_service.py; /reports/{kind}", "Smoke"],
             ["FR15", "List notifications and mark all read", "/notifications", "Smoke"],
             ["FR16", "Edit profile (income, currency, risk profile, savings target) and load demo data", "/profile, /profile/demo-data", "Smoke (duplicate e-mail rejected)"]],
            widths=[0.5, 2.4, 1.9, 1.6], align=["c", "l", "l", "l"], size=8.5),
        P(f"Each requirement is traced to the route or module that meets it and to the test or measurement that checks it. The automated tests ({F.PYTEST_TOTAL} in five files: auth {F.PYTEST_FILES['test_auth.py']}, budget {F.PYTEST_FILES['test_budget.py']}, "
          f"financial health {F.PYTEST_FILES['test_financial_health.py']}, ML {F.PYTEST_FILES['test_ml.py']}, transactions {F.PYTEST_FILES['test_transactions.py']}) and the {F.SMOKE_TOTAL}-check smoke script together exercise FR1 to FR16 except the live price refresh in FR9 and the optional language-model layer in FR13."),
        H2("4.7 Non-Functional Requirements"),
        TAB("Non-functional requirements, measured values and status", ["ID", "Category", "Requirement", "Measured or observed", "Status"],
            [["NFR1", "Performance", "Common screens load in well under a second", f"Dashboard {s_dash:.0f} ms, analytics {s_ana:.0f} ms, transaction list {lat('GET /transactions'):.0f} ms (medians, 30 calls)", "Met"],
             ["NFR2", "Performance", "Bulk import stays usable", f"Preview of 100 rows {lat('POST /transactions/import/preview'):.0f} ms; commit {F.IMP['rows_per_second_commit']:.1f} rows/s (one session per row)", "Partly met"],
             ["NFR3", "Security", "Passwords hashed, weak passwords refused, routes require a token", f"bcrypt (login {s_login:.0f} ms); password rules tested; 401 without token", "Met"],
             ["NFR4", "Security", "No default secrets, revocable sessions", "Default development secret if APP_SECRET_KEY unset; 7-day tokens with no revocation or refresh", "Not met"],
             ["NFR5", "Correctness", "Reported numbers equal direct sums of the data", "Assistant food total INR 17,365 equals a direct sum; top category matches groupby", "Met"],
             ["NFR6", "Reliability", "Decline instead of guess", "Forecast refuses under 3 months; assistant declines 6 of 6 off-topic questions; categoriser never abstains", "Partly met"],
             ["NFR7", "Usability", "Clear states, light and dark theme, responsive layout", f"{F.N_PAGES} pages; 19 screens; theme toggle; no user study", "Met, no user study"],
             ["NFR8", "Portability", "Start with one command on Windows", "run.bat builds .venv and starts both servers", "Met"],
             ["NFR9", "Maintainability", "Small, tested code base", f"About 2,400 lines of Python, {F.PYTEST_TOTAL} tests in 11.5 s", "Met"],
             ["NFR10", "Scalability", "Serve more than one user at a time", "One process and SQLite; not measured", "Not evaluated"]],
            widths=[0.55, 0.85, 1.5, 2.6, 0.9], align=["c", "l", "l", "l", "l"], size=8.5),
        P("The status column is deliberately blunt: two requirements are not met or not evaluated and two are met only in part (see Chapters 7 and 8). Met means a measurement or test supports it."),
        H2("4.8 Hardware Requirements"),
        P("The system was developed and measured on one desktop; smaller machines were not tested, so no lower bound is claimed. No GPU is needed or used."),
        TAB("Hardware used for development and measurement", ["Item", "Configuration"],
            [["Processor", "12th Gen Intel Core i5-12500, 6 cores, 12 threads"],
             ["Memory", "15.7 GB"],
             ["Graphics", "Intel UHD 770 integrated; no discrete GPU, none used"],
             ["Storage", "Local disk; the database is a single file, finjarvis.db"],
             ["Operating system", "Windows 11 Pro"]],
            widths=[1.8, 4.6], align=["l", "l"], size=10),
        H2("4.9 Software Requirements"),
        TAB("Software used", ["Layer", "Software and version"],
            [["Language and runtime", "Python 3.11.9 (the code needs 3.11 or newer); Node.js 20 or newer for the front end (24.19.0 used)"],
             ["Back end", "FastAPI 0.110 or newer, uvicorn, SQLAlchemy 2.0, pydantic 2, python-multipart"],
             ["Data and ML", "pandas 2.2, NumPy 1.26, scikit-learn 1.4.2 or newer (the measurements ran under 1.9.1)"],
             ["Security and reports", "passlib with bcrypt 4.0.1, python-dotenv, ReportLab, OpenPyXL"],
             ["Optional", "yfinance (price refresh), anthropic (language-model layer)"],
             ["Front end", "React 18.3, TypeScript 5.9, Vite 8, Tailwind CSS 4, Recharts 3, TanStack Query 5, Axios, react-router 7"],
             ["Database", "SQLite file finjarvis.db (replaceable through FINJARVIS_DB)"],
             ["Testing and measurement", "pytest 8.2, matplotlib, Playwright with Google Chrome for the screenshots"]],
            widths=[1.8, 4.6], align=["l", "l"], size=10),
        H2("4.10 User Roles and System Constraints"),
        TAB("User roles", ["Role", "Can do", "Cannot do"],
            [["Visitor (not logged in)", "See the landing page and public showcase; sign up or log in; use the demo-login button", "Read or write any financial data"],
             ["User", "Manage own transactions, budgets, goals, investments, profile, reports and notifications; ask the assistant", "See another user's data (every query is filtered by user_id)"],
             ["Demo user", "Same as a user, on fictional data (demo / Demo@1234)", "Nothing is withheld; the data is fictional and can be reset"]],
            widths=[1.4, 3.1, 1.9], align=["l", "l", "l"], size=9.5),
        P("There is a single privilege level: the system has no administrator role. The constraints below are enforced by the validators and the schemas."),
        B("A username has 3 to 30 letters, digits or underscores; a password has at least 8 characters with an upper-case letter, a lower-case letter, a digit and a special character.",
          "A transaction needs a valid ISO date, a positive amount and a description; free text is trimmed and capped (255 characters for a description).",
          "An import file needs the columns date, description, amount, category and type; rows with an unparsable date, a non-numeric or non-positive amount or a blank description are skipped with a warning.",
          "The forecast needs at least 3 months of expense history.",
          "A session token is signed with HMAC-SHA256 and lasts 7 days; the development secret must be replaced through APP_SECRET_KEY before real use.",
          "One backend process serves all requests, and CORS allows only the web origin (port 5411)."),
    ]
