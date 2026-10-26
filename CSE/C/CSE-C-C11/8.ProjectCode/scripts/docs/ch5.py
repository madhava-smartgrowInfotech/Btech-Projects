"""Chapter 5: System Design for FINJARVIS.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
Line counts are measured from the code at build time; diagrams are drawn by make_diagrams.py (file names are fixed by the batch contract).
"""

import os

from . import facts as F
from .blocks import FIG, H1, H2, H3, P, TAB
from .refs import N as cite

# diagram key -> (file, caption)
_D = {
    "arch": ("01_system_architecture.png", "Layered architecture of FINJARVIS: React single-page app, Vite proxy, FastAPI application with 33 routes, service layer, ML modules, SQLAlchemy and SQLite."),
    "flow": ("02_high_level_workflow.png", "High-level workflow: record or import a transaction, categorise it, update budgets, forecast, score and answer questions."),
    "dfd0": ("03_dfd_level0.png", "Data flow diagram, level 0: FINJARVIS as one process between the user, the optional LLM provider and the market-data source."),
    "dfd1": ("04_dfd_level1.png", "Data flow diagram, level 1: the main processes and the six data stores."),
    "dfd2": ("05_dfd_level2.png", "Data flow diagram, level 2: adding a transaction (validation, categorisation, learning, storage)."),
    "uml": ("06_uml_class.png", "UML class diagram: the six ORM classes, the service functions and the three ML modules."),
    "seq": ("07_sequence_diagram.png", "Sequence diagram of the main flow: login, add a transaction with auto-categorisation, then read the dashboard."),
    "usecase": ("08_use_case.png", "Use-case diagram: the registered user, the demo visitor and the optional external services."),
    "er": ("09_er_diagram.png", "Entity-relationship diagram of the six tables."),
    "algo": ("10_flowchart_algorithm.png", "Flowchart of the core algorithms: categoriser, forecast, health score and budget alerts."),
    "cat": ("11_categoriser_pipeline.png", "Categoriser pipeline: description, TF-IDF, logistic regression, label, optional correction and retraining."),
    "health": ("12_health_score_model.png", "Financial health score model: six weighted components, clipped sum, rating band."),
}


def _lines(rel):
    path = os.path.join(F.CODE, rel)
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def _tree_lines(rel, exts):
    total = 0
    for root, dirs, files in os.walk(os.path.join(F.CODE, rel)):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", "__pycache__", "docs")]
        for f in files:
            if f.endswith(exts):
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    total += sum(1 for _ in fh)
    return total


def _dg(key, width=5.4):
    """Diagram figure block, or nothing if the file has not been drawn yet."""
    f, cap = _D[key]
    path = F.diag(f)
    return [FIG(path, cap, width)] if os.path.exists(path) else []


def _trim(out):
    """Report variant: same 12 diagrams, no design screenshots (Chapter 8 shows the screens)."""
    return [b for b in out if not (b[0] == "fig" and os.sep + "screenshots" + os.sep in b[1])]


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    shot = lambda n, cap, base=5.0, mh=3.4: [FIG(F.shot(n), cap, F.shot_w(F.shot(n), base, mh))] if os.path.exists(F.shot(n)) else []  # noqa: E731

    mods = [
        ("`backend/main.py`", "backend/main.py", "FastAPI application: 33 routes, token helpers, pydantic input models, `current_user` dependency, JSON clean-up"),
        ("`backend/demo_seed.py`", "backend/demo_seed.py", "Demo account and demo-data loader (shifted sample CSV plus synthetic earlier months)"),
        ("`auth/authentication.py`", "auth/authentication.py", "`signup` and `login` with validation and duplicate checks"),
        ("`utils/security.py`, `utils/validators.py`", "utils/validators.py", "bcrypt hashing through passlib; e-mail, username, password-strength and amount validators"),
        ("`database/models.py`, `database/database.py`", "database/models.py", "Six SQLAlchemy models; SQLite engine, session factory and `get_session` context manager"),
        ("`services/transaction_service.py`", "services/transaction_service.py", "Add, edit, delete and filter transactions, every query scoped by `user_id`"),
        ("`services/budget_service.py`", "services/budget_service.py", "Budget upsert, usage per category, 75/90/100 % alert notifications"),
        ("`services/goal_service.py`, `services/investment_service.py`", "services/goal_service.py", "Goals with required monthly saving; holdings, portfolio profit and loss, optional price refresh"),
        ("`services/analytics_service.py`", "services/analytics_service.py", "Monthly metrics, category totals, monthly trend, range overview"),
        ("`services/ai_service.py`", "services/ai_service.py", "Rule-routed assistant (five handlers), insights, optional LLM layer, disclaimer"),
        ("`services/data_import_service.py`, `services/report_service.py`", "services/data_import_service.py", "CSV/Excel import with row-level warnings; PDF, Excel and CSV reports"),
        ("`ml/expense_classifier.py`", "ml/expense_classifier.py", "TF-IDF and logistic-regression categoriser, 51-pair seed, keyword fallback, `learn_from_correction`"),
        ("`ml/spending_prediction.py`", "ml/spending_prediction.py", "Linear-trend forecast of next month's expenses, per-category forecast, budget-overrun check"),
        ("`ml/financial_health.py`", "ml/financial_health.py", "Six sub-scores, weights, rating bands and weakest-area explanation"),
        ("`scripts/smoke_test.py`", "scripts/smoke_test.py", f"{F.SMOKE_TOTAL}-check end-to-end test against a throw-away database"),
        ("`scripts/run_experiments.py`, `scripts/measure_api.py`", "scripts/run_experiments.py", "Offline experiments (categoriser, forecast, health score, assistant, import) and API latency"),
    ]
    mod_rows = [[n, str(_lines(rel)), d] for n, rel, d in mods]
    fe_lines, test_lines = _tree_lines("frontend/src", (".ts", ".tsx")), _tree_lines("tests", (".py",))
    ui_lines = _tree_lines("ui", (".py",)) + _lines("app.py")
    mod_rows.append(["`frontend/src/`", f"{fe_lines:,}", f"React 18 and TypeScript console: {F.N_PAGES} pages plus a not-found page, UI kit, charts, API client, auth and theme providers"])
    mod_rows.append(["`app.py`, `ui/`", f"{ui_lines:,}", "The original Streamlit front end over the same services (kept, not extended)"])
    mod_rows.append(["`tests/`", str(test_lines), f"{F.PYTEST_TOTAL} pytest tests (auth 9, budget 6, financial health 6, ML 9, transactions 8)"])

    routes = [  # (methods, path, auth, purpose, errors, number of routes)
        ["GET", "/api/health", "-", "Service status and whether the LLM key is set", "-", 1],
        ["GET", "/api/public/showcase", "-", "Landing-page figures from the fictional demo account, plus one assistant answer", "404 no demo account", 1],
        ["POST", "/api/auth/signup", "-", "Validate, hash the password with bcrypt, create the account", "400 validation; 409 duplicate", 1],
        ["POST", "/api/auth/login", "-", "Username or e-mail plus password; returns a signed token and the user", "401", 1],
        ["GET", "/api/auth/me", "token", "The signed-in user's profile", "401", 1],
        ["GET", "/api/meta", "token", "Categories, payment methods, asset types, currencies, risk profiles, goal presets", "401", 1],
        ["PUT, POST", "/api/profile, /api/profile/demo-data", "token", "Update the profile; load the shifted sample data, budgets, goals and holdings", "400; 409; 422", 2],
        ["GET", "/api/dashboard", "token", "Month metrics, health score, budget alerts and six chart datasets", "401", 1],
        ["GET, POST", "/api/transactions", "token", "Filter, sort and total; create ('Auto-detect' uses the classifier, a differing manual category triggers learning)", "422 bad date; 400", 2],
        ["PUT, DELETE", "/api/transactions/{id}", "token", "Edit selected fields; delete one transaction", "400; 404", 2],
        ["POST", "/api/transactions/predict-category", "token", "Category the model would assign to a description", "401", 1],
        ["POST", "/api/transactions/import/preview, /commit", "token", "Parse and clean a CSV/Excel file and label blanks; insert the cleaned rows", "400 empty, missing columns, no valid rows", 2],
        ["GET", "/api/analytics", "token", "Overview, category split, trend, next-month and category forecasts, overrun risks", "400 start after end", 1],
        ["GET, POST", "/api/budgets", "token", "Usage per category for a month; create or update (upsert by category, month, year)", "422; 400 amount", 2],
        ["DELETE", "/api/budgets/{id}", "token", "Delete a budget", "404", 1],
        ["GET, POST", "/api/goals", "token", "Goals with percent complete and required monthly saving; create a goal", "400", 2],
        ["PUT, DELETE", "/api/goals/{id}", "token", "Set the saved amount (completes at target); delete a goal", "404", 2],
        ["GET, POST", "/api/investments", "token", "Holdings and portfolio totals; add a holding", "400", 2],
        ["POST, DELETE", "/api/investments/{id}/refresh, /{id}", "token", "Try a live price through yfinance (degrades to a message); delete a holding", "404", 2],
        ["GET, POST", "/api/assistant/insights, /ask", "token", "Rule-based insights plus the disclaimer; answer a question from the user's own data", "401", 2],
        ["GET", "/api/reports/{pdf|excel|csv}", "token", "Download a monthly report (CSV: all transactions)", "400 nothing to export; 500", 1],
        ["GET, POST", "/api/notifications, /read-all", "token", "Raise budget alerts, then list notifications and the unread count; mark all read", "401", 2],
    ]
    assert sum(r[5] for r in routes) == F.N_ROUTES
    routes = [r[:5] for r in routes]

    out = [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes the architecture and workflow, the data flow, the UML and database design, the core algorithms, the modules, the API and the user interface. "
          "The diagrams were drawn from the code in `backend/`, `services/`, `ml/`, `database/` and `frontend/src/`. "
          "FINJARVIS is a single-role, multi-user web application: every registered user sees only their own records, and all state lives in one SQLite file. "
          "The design is stated as built, including where it differs from the batch abstract (Flask and MySQL, loan tracking, scheduled alerts)."),

        H2("5.1 Design goals and architecture"),
        P("Five goals shaped the design. **Every number on screen is computed from the user's own records**: the dashboard, the forecast, the health score and the assistant call the same service functions over the same tables. "
          "**The models are simple enough to inspect**: a TF-IDF and logistic-regression categoriser, a least-squares trend and a six-term weighted sum can each be re-computed by hand, which is why none of the heavier models of the base paper " + cite("base") + " was built. "
          "**One code path serves two front ends**: the Streamlit pages and the React console call the same `services/` and `ml/` modules, and the FastAPI layer holds no business rules. "
          "**Per-user isolation**: every table carries a `user_id` and every service query filters on it. "
          "**Zero-configuration deployment**: SQLite, a bundled sample file and a seeded demo account run on a laptop with one launcher script."),
        *_dg("arch", 5.6),
        P(f"The React console on port {w} reaches the FastAPI application on 127.0.0.1:{a} through the Vite development proxy (`/api` is forwarded), so the browser sees one origin; cross-origin calls are allowed from `localhost:{w}` and `127.0.0.1:{w}` only. "
          f"The application exposes {F.N_ROUTES} routes in `backend/main.py`. Each route validates input with pydantic, resolves the caller through the `current_user` dependency, calls one service or ML function and returns JSON after a `clean` step that converts NumPy and pandas values. "
          "The rules live in `services/` and `ml/`, so they can be tested without HTTP. "
          "The style is a stateless REST interface " + cite("rest") + " over one relational store accessed through an object-relational mapper " + cite("sqla") + "."),
        P("The deliberate gaps are worth stating. There is one backend process and one SQLite file, so there is no horizontal scaling. "
          "The categoriser is a single pickled file, `ml/expense_model.pkl`, shared by every account: `learn_from_correction` retrains on the seed list plus one user's history and overwrites it, so one user's correction changes every user's predictions (read from the code, not exercised in a multi-user test). "
          "Tokens are home-made HMAC bearer tokens with a 7-day lifetime and no revocation, and there is no scheduler: budget alerts are raised when the dashboard or the notification list is requested."),

        H2("5.2 High-level workflow"),
        *_dg("flow", 5.6),
        P("The workflow has six stages and every stage maps to a route and a page. **Record**: a transaction is typed in or imported from CSV or Excel (preview, then commit). "
          "**Categorise**: with 'Auto-detect' the classifier labels the description; a manual category that differs from the model's prediction is stored as chosen and also used to retrain the model, so the classifier is called for every new transaction. "
          "**Watch**: budgets are compared with the month's spending and a notification is written when a category crosses 75, 90 or 100 % of its budget. "
          "**Forecast**: a straight line over the monthly expense totals, refused below three months of history. "
          "**Score**: the dashboard turns the month's metrics, budgets, holdings and goals into the 0-100 health score. "
          "**Ask and export**: the assistant answers from the user's records, and the reports routes produce PDF, Excel or CSV files."),

        H2("5.3 Data flow diagrams"),
        H3("5.3.1 Level 0: context"),
        *_dg("dfd0", 4.8),
        P("At level 0 FINJARVIS is one process with three external entities. The **user** supplies credentials, transactions, files, budgets, goals, holdings and questions, and receives the dashboard, forecasts, alerts, answers and report files. "
          "The **LLM provider** is optional: with `AI_API_KEY` set, a question the rule layer cannot match is sent with a short summary of the user's figures; without a key nothing leaves the machine. "
          "The **market-data source** (`yfinance`) is also optional and used only when the user refreshes a holding's price."),
        H3("5.3.2 Level 1: main processes"),
        *_dg("dfd1", 5.4),
        P("Level 1 shows the processes that read and write the six data stores. Authentication uses the users store; transaction handling writes transactions and calls the categoriser; "
          "budget monitoring reads budgets and transactions and writes notifications; analytics reads transactions and holdings and calls the forecast and health modules; the assistant reads the same stores through the analytics functions; reporting writes files only."),
        H3("5.3.3 Level 2: adding a transaction"),
        *_dg("dfd2", 5.4),
        P("The transaction process holds the main input rules. The description must not be blank and the amount must be above zero (HTTP 400 otherwise). 'Auto-detect' or an empty category takes the model's label, any other value is kept. "
          "If the user's value differs from the model's prediction, the model is retrained on the seed plus the user's history plus the new pair; a retraining failure is swallowed so that it never blocks the insert. "
          "The file import follows the same path row by row, except that a bad row is skipped with a warning instead of failing the file."),

        H2("5.4 UML design"),
        H3("5.4.1 Class diagram"),
        *_dg("uml", 5.6),
        P("Six SQLAlchemy classes map to six tables " + cite("sqla") + ". Behaviour is kept out of the model classes and placed in `services/` as functions that open a session through `get_session`, which commits on success and rolls back on any exception. "
          "The only other classes are the pydantic input models of the API (`SignupIn`, `LoginIn`, `TransactionIn`, `BudgetIn`, `GoalIn`, `InvestmentIn`, `AskIn` and others), which carry type and range limits, and the small `AuthResult` dataclass. "
          "The ML modules are plain functions; the categoriser holds a scikit-learn `Pipeline` of a `TfidfVectorizer` and a `LogisticRegression`."),
        H3("5.4.2 Sequence diagram"),
        *_dg("seq", 5.4),
        P("The browser posts the login form; the server checks the bcrypt hash and returns a signed token that the console attaches to every later call. "
          "A new transaction passes the token check, the field validation, the classifier call and, when the user overrides the label, the retraining attempt. "
          "The dashboard request then recomputes the month's metrics, budget status, health score and chart data in one call and raises any budget alert not yet raised."),
        H3("5.4.3 Use-case diagram"),
        *_dg("usecase", 4.8),
        P("There is one human role, the registered user, and one visitor role: a person without an account can open the landing and login pages and sign in to the fictional demo account. "
          "A registered user can manage transactions, import files, set budgets and goals, record holdings, view analytics, ask the assistant, download reports and read notifications. "
          "The LLM provider and market-data source are secondary actors. There is no administrator role."),

        H2("5.5 Database design"),
        *_dg("er", 5.4),
        P("The schema has six tables in one SQLite file, `finjarvis.db`, created at start-up by `init_db`; the path can be redirected with `FINJARVIS_DB` (used by the tests and screenshot scripts). "
          "A user has many transactions, budgets, goals, investments and notifications; each child row has an indexed, non-null `user_id` foreign key and is removed with its user through the ORM cascade (no route deletes accounts)."),
        TAB("The six tables and their columns.",
            ["Table", "Columns", "Keys, defaults"],
            [["users", "id, name(120), email(255), username(80), password_hash(255), currency, monthly_income, risk_profile, savings_target, created_at",
              "PK id; unique and indexed email and username; currency INR; risk profile Moderate"],
             ["transactions", "id, user_id, date, description(255), category(80), amount, transaction_type, payment_method, notes",
              "PK id; FK user_id (indexed); type income or expense; payment method Other"],
             ["budgets", "id, user_id, category(80), budget_amount, month, year",
              "PK id; FK user_id (indexed); month 1-12; one row per user, category, month and year is enforced in code (`set_budget` updates the existing row), not by a constraint"],
             ["financial_goals", "id, user_id, goal_name(120), target_amount, current_amount, target_date, status",
              "PK id; FK user_id (indexed); status active, completed or abandoned; current amount 0"],
             ["investments", "id, user_id, asset_name(120), symbol(20), asset_type(30), quantity, purchase_price, current_price, purchase_date",
              "PK id; FK user_id (indexed); asset types Stock, Mutual Fund, ETF, Gold, Fixed Deposit, Other"],
             ["notifications", "id, user_id, message(255), notification_type, created_at, is_read",
              "PK id; FK user_id (indexed); type info, warning, danger or success; unread by default"]],
            widths=[1.2, 3.3, 1.9], align=["l", "l", "l"], size=9),
        P("Three design points deserve a note. Money is stored as floating-point numbers, adequate for a display tool but not for ledger accounting. "
          "Monthly queries use string bounds such as `YYYY-MM-31`, which SQLite compares correctly but a stricter database would reject for shorter months. "
          "Alerts are de-duplicated by identical message text, so a budget that crosses the same threshold again in a later month raises no new alert."),

        H2("5.6 Core algorithm design"),
        *_dg("algo", 5.4),
        P("Three small algorithms carry the intelligence of the product: the **categoriser** (a description to one of eleven labels), the **forecast** (monthly expense totals to a next-month figure) and the **health score** (the month's records to a 0-100 number and the weakest area). "
          "The flowchart shows how routes call them; Chapter 6 gives formulas and parameters."),
        *_dg("cat", 5.4),
        P("The categoriser lowercases the text and builds word unigrams and bigrams; TF-IDF weighting " + cite("tfidf") + " gives each term a weight that falls with how many descriptions contain it; a logistic-regression classifier " + cite("sklearn") + " maps the weights to a probability per label and the highest wins. "
          "The prediction order is fixed: model, then a keyword table if the model fails, then 'Other'; a model trained on 51 examples never outputs 'Other'. "
          "The design choice that matters most is text with no known words: the feature vector is all zeros and the label comes from the intercepts alone. Chapter 8 measures what that costs."),
        *_dg("health", 5.4),
        P("The health score is a weighted sum of six sub-scores, each clipped to 0-100: savings rate (weight 0.30), expense ratio (0.20), budget adherence (0.15), emergency fund (0.15), investment diversification (0.10) and goal progress (0.10). "
          "The weights are chosen by the team, not fitted to data. The result carries a rating band (Excellent from 90, Good from 75, Fair from 60, Needs Improvement from 40, otherwise Critical) and the name and reason of the lowest component, so the number is always explained. "
          "The forecast follows the same philosophy: a straight line with an explicit refusal below three months is more honest than a deeper model that would fit noise; "
          "Chapter 8 tests that claim and shows the refusal threshold is too low for the method."),

        H2("5.7 Module design"),
        P("Each file has one reason to change. Line counts were measured from the repository when this report was built."),
        TAB("Modules, sizes and responsibilities.", ["Module", "Lines", "Responsibility"], mod_rows, widths=[2.2, 0.6, 3.6], align=["l", "r", "l"], size=9),

        H2("5.8 API design"),
        P(f"All routes live under `/api`; reads are GET, actions POST, edits PUT and removals DELETE. Every route except `health`, `public/showcase`, `auth/signup` and `auth/login` needs an `Authorization: Bearer` token. "
          "Failures return the FastAPI `detail` string, which the console shows verbatim, so messages are written for the user. "
          "401 means the token is missing, tampered or expired (the console returns to login), 404 means the object does not exist or belongs to another user, 409 a duplicate e-mail or username, "
          "400 a well-formed but unacceptable request, and 422 failed type validation."),
        TAB(f"The {F.N_ROUTES} routes of the FINJARVIS API.", ["Method", "Path", "Auth", "Purpose", "Errors"], routes, widths=[0.55, 1.75, 0.45, 2.55, 1.1], align=["c", "l", "c", "l", "l"], size=8),
        P("`GET /api/public/showcase` needs no login so that the landing page can show live figures; it reads only the fictional demo account. Import `preview` and `commit` parse the same upload twice, so the user sees the cleaned rows and warnings before deciding."),

        H2("5.9 User interface design"),
        P(f"The console has {F.N_PAGES} pages and a not-found page: a public landing page, log-in and sign-up pages, and ten pages behind the login. "
          "A route guard sends signed-out visitors to the login page, and a 401 from the API clears the stored token. "
          "The interface is dark with a light theme, one gradient accent and a collapsible sidebar; amounts use Indian digit grouping and a compact K, L and Cr notation on charts."),
        TAB("Pages, routes and the endpoints they use.", ["Page", "Route", "Endpoints used"],
            [["Landing", "/", "GET /api/public/showcase"],
             ["Log in, Sign up", "/login, /signup", "POST /api/auth/login, POST /api/auth/signup"],
             ["Dashboard", "/app", "GET /api/dashboard"],
             ["Transactions", "/app/transactions", "GET, POST /api/transactions, PUT, DELETE /api/transactions/{id}, POST predict-category, import preview and commit"],
             ["Analytics", "/app/analytics", "GET /api/analytics"],
             ["Budgets", "/app/budgets", "GET, POST /api/budgets, DELETE /api/budgets/{id}"],
             ["Goals", "/app/goals", "GET, POST /api/goals, PUT, DELETE /api/goals/{id}"],
             ["Investments", "/app/investments", "GET, POST /api/investments, POST refresh, DELETE"],
             ["AI Assistant", "/app/assistant", "GET /api/assistant/insights, POST /api/assistant/ask"],
             ["Reports", "/app/reports", "GET /api/reports/{pdf|excel|csv}"],
             ["Notifications", "/app/notifications", "GET /api/notifications, POST read-all"],
             ["Profile", "/app/profile", "GET /api/auth/me, PUT /api/profile, POST /api/profile/demo-data"]],
            widths=[1.5, 1.6, 3.3], align=["l", "l", "l"], size=9.5),
        P("Every page opens with its purpose in one sentence, long actions show a busy state and finish with a toast, money is formatted the same way everywhere, and API errors appear as a sentence next to the control that caused them. "
          "Chapter 8 shows the working pages with real data; the screens below illustrate the design itself."),
        *shot("05_dashboard.png", "Dashboard: month metrics, financial health score with its six components, and budget alerts, all computed from the demo account's own records.", 5.0, 3.4),
        *shot("07_transactions-add.png", "Add-transaction form with 'Auto-detect' category: the model's label is shown before the row is saved.", 5.0, 3.4),
        *shot("12_budgets.png", "Budgets page: usage per category against the monthly budget with the 75, 90 and 100 % alert bands.", 5.0, 3.4),

        H2("5.10 Design decisions and trade-offs"),
        P("The table records the main decisions, what each bought and what it cost, so that the limitations in Chapter 9 trace back to a choice."),
        TAB("Principal design decisions.",
            ["Decision", "Reason", "Cost"],
            [["FastAPI, React and SQLite instead of the abstract's Flask and MySQL", "The existing service code was Python and database-agnostic; SQLite needs no server; FastAPI gives typed input models and automatic documentation", "A deviation from the registered abstract; single-file, single-writer storage; no migrations"],
             ["Logistic regression on TF-IDF instead of BERT", "Trains in milliseconds on a CPU laptop, needs no GPU and no labelled corpus of thousands; predictions are inspectable", "A 51-example seed gives 18.2 % accuracy on unseen merchants; no pre-trained language knowledge"],
             ["Straight-line trend with a three-month minimum", "Honest about small histories and trivial to explain", "Not better than a plain average below about seven months in the simulation; no seasonality, no uncertainty range"],
             ["Weighted explainable health score", "Every point of the score can be traced to a component and a reason", "Weights are chosen, not fitted; savings rate and expense ratio are strongly correlated and carry half the score"],
             ["Rule-routed assistant with an optional LLM", "Answers are computed from the user's own data and work offline", "Only five question patterns; 14 of 20 answerable test questions were handled"],
             ["Single shared model file", "Simple persistence, no per-user model management", "One user's correction changes every user's predictions"],
             ["Home-made HMAC token instead of a standard JWT library", "No extra dependency; short and auditable", "No refresh or revocation; the default secret must be replaced through `APP_SECRET_KEY`"],
             ["Alerts raised on read, not on a timer", "No scheduler process to run or fail", "No alert if the user never opens the dashboard or notifications; the abstract's scheduled digests are not provided"]],
            widths=[2.0, 2.4, 2.0], align=["l", "l", "l"], size=9),
        P("Outside the delivered design: no anomaly detector (objective 4), no time-series model beyond the linear trend (objective 3), no reinforcement-learning budget recommender, no loan or debt tracker, "
          "no bank or SMS integration and no scheduled digest. Budget advice is rule-based: the assistant suggests trimming the top one or two categories by 10 to 15 % and the budget screen alerts at fixed thresholds."),
    ]
    return _trim(out) if F.REPORT else out
