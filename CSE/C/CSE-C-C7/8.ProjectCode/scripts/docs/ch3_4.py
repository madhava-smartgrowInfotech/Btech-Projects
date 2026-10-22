"""Chapters 3 (feasibility) and 4 (requirements and analysis)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import c

_EP = F.API_LAT["endpoints"]
_ENV = F.ENV
_PK = _ENV["packages"]
_REC_LAT = _EP["GET /api/recommendations?top_n=8"]


def _ms(key, field="mean_ms"):
    return f"{_EP[key][field]:.1f}"


# Requirement, source in the code, priority. Used again by the testing chapter.
FUNCTIONAL = [
    ["FR1", "Register with a name, an e-mail address and a password (at least 6 characters, confirmed); reject a duplicate e-mail and a mismatch.", "POST /api/auth/register", "Must"],
    ["FR2", "Sign in and out; keep the session in an HttpOnly cookie; report the current user.", "POST /api/auth/login, /logout; GET /api/me", "Must"],
    ["FR3", "Create and update a learner profile of ten fields (education, skill level, interests, preferred topics, learning style, goals, course preferences, weekly hours, age band, gender).", "GET, PUT /api/profile", "Must"],
    ["FR4", "Browse the catalogue of 24 courses and filter it by text, category and level; open one course with its prerequisites, outcomes and tags; return 404 for an unknown course.", "GET /api/courses, /api/courses/{id}", "Must"],
    ["FR5", "Rank the whole catalogue for the signed-in learner and return, for each course, the match score, the eight score parts, the success probability, a suggested action, its estimated benefit and up to three reasons.", "GET /api/recommendations?top_n", "Must"],
    ["FR6", "Reload the trained models and recompute the ranking on request.", "POST /api/recommendations/refresh", "Should"],
    ["FR7", "Record a learner event (view, open, start, content, quiz, forum, save, complete, dismiss) for a course; reject any other event type.", "POST /api/interactions", "Must"],
    ["FR8", "Change later rankings and the engagement level as events accumulate (behavioural boost and engagement score).", "recommender.behavioral_boost, engagement_level", "Must"],
    ["FR9", "Arrange the best courses into a staged learning path of up to six steps, with the next best action.", "GET /api/learning-path", "Must"],
    ["FR10", "Show insights: engagement level, success probability and risk, estimated benefit of five actions, strengths, areas to attend to and event counts.", "GET /api/insights", "Should"],
    ["FR11", "Show the learner's own activity log and the history of recommendations given.", "GET /api/activity, /api/history", "Should"],
    ["FR12", "Show model transparency: model comparison, confusion matrices, ROC curve, the stored feature-importance values and plot (absolute coefficients of the selected logistic regression), offline policy evaluation and a fairness audit.", "GET /api/metrics, /api/fairness, /static/*.png", "Should"],
    ["FR13", "Report service health and whether the model files are loaded.", "GET /api/health", "Should"],
    ["FR14", "Show a dashboard of engagement, success estimate, event counts, the next action and the top recommendations.", "React page Dashboard", "Should"],
    ["FR15", "Work at phone, tablet and desktop widths in light and dark themes.", "React front end; scripts/check_responsive.py", "Could"],
]

NONFUNCTIONAL = [
    ["Performance", f"A ranking of the 24-course catalogue returns in well under 100 ms on a desktop CPU: measured mean {_ms('GET /api/recommendations?top_n=8')} ms, 95th percentile {_ms('GET /api/recommendations?top_n=8', 'p95_ms')} ms (30 requests).", "scripts/measure_api.py"],
    ["Usability", "Every screen usable at 360, 768 and 1440 px in light and dark themes without horizontal overflow or console errors.", "scripts/check_responsive.py (11 screens)"],
    ["Reliability", "Bad input is answered with a JSON error (401, 400, 404 or 422) and never changes stored data.", "tests/test_app.py::test_invalid_inputs"],
    ["Security", "Passwords are stored as pbkdf2_sha256 hashes; session tokens are random (32 bytes, URL-safe) and sent as an HttpOnly, SameSite=Lax cookie; database access goes through the ORM with bound parameters; inputs are validated by Pydantic.", "app/security.py, app/schemas.py"],
    ["Portability", "Runs on Windows with Python 3.11 and Node.js 20 or newer; one script (`run.bat`) starts the back end and the front end.", "run.bat, HOW_TO_RUN.md"],
    ["Maintainability", f"Ranking, models, routes, ORM and front end are separate modules; behaviour is covered by {F.TESTS['pytest']['passed']} automated tests and a {F.TESTS['smoke']['checks']}-check smoke test.", "tests/, scripts/smoke_test.py"],
    ["Reproducibility", "The training pipeline uses a fixed seed (42) and re-running it reproduces the stored metrics exactly.", "scripts/train_pipeline.py, experiments/seed_study.json"],
    ["Privacy", "All data stay in one local SQLite file; no third-party service is called by the application.", "app/config.py"],
    ["Honesty of output", "The analytics screen names the data source (`synthetic-oulad-like-fallback-v1`) and the offline policy evaluation carries its effective sample size.", "artifacts/metrics/model_metrics.json"],
]


def blocks():
    cpu = _ENV["cpu"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical feasibility"),
        P("The project needs a web service, a small database, a text-similarity step, three standard classifiers and a browser interface. All of these exist as mature open-source libraries, and "
          "none needs a graphics card, so the technical question is whether they can be combined into one working system on ordinary hardware. The project answers it by doing so."),
        TAB("Technical building blocks and the evidence that each works", ["Need", "Chosen technology", "Evidence from this project"], [
            ["Web service and routes", f"FastAPI {_PK['fastapi']}, Uvicorn {_PK['uvicorn']}, Pydantic {_PK['pydantic']} {c('fastapi')}", "18 routes answer correctly in the test suite and the smoke test"],
            ["Persistence", f"SQLAlchemy {_PK['sqlalchemy']} over SQLite {c('sqlalchemy')}", "six tables created and used by all routes"],
            ["Text similarity", f"scikit-learn {_PK['scikit-learn']} TF-IDF and cosine similarity {c('sklearn', 'tfidf')}", f"ranking of 24 courses in {_ms('GET /api/recommendations?top_n=8')} ms on average"],
            ["Success and action models", f"scikit-learn logistic regression and random forest, XGBoost {_PK['xgboost']} {c('xgboost', 'breiman')}", f"one full training run takes about {F.SEEDS['runs'][0]['seconds']:.1f} s on the test machine"],
            ["Front end", "React 19 and Vite with a proxy to the API", f"{F.TESTS['responsive']['screens_private'] + F.TESTS['responsive']['screens_public']} screens pass the responsive check"],
            ["Security helpers", f"passlib {_PK['passlib']} (pbkdf2_sha256), Python `secrets`", "login, logout and rejection of bad tokens tested"],
        ], widths=[1.5, 2.6, 2.2], size=9.5),
        P(f"The risk that matters is not the software but the data. A recommendation engine needs learner histories, and none were available. The project therefore generates a synthetic data set and says so everywhere. "
          "This makes the pipeline technically feasible and demonstrable but leaves open whether the same models would work on real learners."),
        H2("3.2 Economic feasibility"),
        P("The cost of the system is almost entirely the authors' time. Every component is open-source under a permissive licence (MIT, BSD, Apache-2.0 or the Python licence), no paid API or cloud service is used, "
          "and all data stay on the local machine."),
        TAB("Cost items", ["Item", "Cost basis", "Remark"], [
            ["Software licences", "None", "All libraries are open-source"],
            ["Data", "None", "Synthetic data generated locally; the real OULAD data (CC BY 4.0) were not used"],
            ["Hardware", "Existing desktop", f"{cpu}, {_ENV['ram_gb']} GB RAM, no GPU used"],
            ["Cloud and API fees", "None", "Nothing is hosted; the application runs locally"],
            ["Effort", "Student time", "Four students and one guide; no payroll figure is recorded"],
            ["Maintenance", "Not budgeted", "Library versions are pinned in `requirements.txt` to keep the build repeatable"],
        ], widths=[1.6, 1.6, 3.1], size=10),
        P("No rupee or dollar figure is given for effort because none was recorded. If the system were hosted, the first costs would be a small server and a managed database; they are not estimated here."),
        H2("3.3 Operational feasibility"),
        P("The users are learners, who need no training beyond a sign-up form and a short profile form; and a developer, who runs two commands. The interface was checked at three widths and two themes, "
          "and every recommendation explains itself, which lowers the effort needed to trust it. Starting the system takes one script, and the first run trains the models (the project README budgets one to three minutes; a measured training run takes seconds)."),
        P("Operational weak points are stated plainly. Recommendations are recomputed on each request with no cache, SQLite allows one writer at a time, tokens are not expired in the database, and the models were trained on synthetic data and "
          "would need retraining on real logs before any real use."),
        H2("3.4 Schedule feasibility"),
        P("The calendar dates of the project are not recorded in the project files, so the plan is given as ordered phases rather than dates. Each phase produced a measurable output that later phases used."),
        TAB("Project phases and outputs", ["Phase", "Work", "Output"], [
            ["1", "Study the base paper, set objectives and problem statement", "Batch documents 2 to 6"],
            ["2", "Write the catalogue and the synthetic data generator", "`data/catalog/courses.json`, `scripts/train_pipeline.py`"],
            ["3", "Train and compare the success models; fit the T-learner; run offline policy evaluation and the fairness audit", "`models/*.joblib`, `artifacts/metrics/model_metrics.json`"],
            ["4", "Build the ranker, the database layer and the JSON routes", "`app/recommender.py`, `app/api_routes.py`, `app/models.py`"],
            ["5", "Build the server-rendered interface, then the React interface", "`app/templates/`, `frontend/`"],
            ["6", "Test and measure", f"{F.TESTS['pytest']['passed']} tests, {F.TESTS['smoke']['checks']} smoke checks, responsive check, latency and persona experiments"],
            ["7", "Write the documents and presentations", "Batch documents 7 to 19"],
        ], widths=[0.6, 3.6, 2.1], size=10, align=["c", "l", "l"]),
        H2("3.5 Legal and ethical considerations"),
        B("**Data licence.** The OULAD data, which the base paper uses, are released under CC BY 4.0 and require attribution; the synthetic data used here carry no third-party licence.",
          "**Personal data.** The system stores a name, an e-mail address, a password hash and profile fields. Age band and gender are collected only for the fairness audit, which is reporting only and never used to rank.",
          "**Fairness.** The audit shows that the 55-and-over group has a lower F1 (0.305) than the 0-to-35 group (0.415). This is reported openly and no mitigation was attempted.",
          "**Claims.** Estimated benefits are not proven causal effects, and the offline policy values are not live results; the interface and documents say so."),
        H2("3.6 Advantages and constraints"),
        TAB("Advantages and constraints", ["Advantages", "Constraints"], [
            ["Works from the first profile (no history needed)", "Trained on synthetic data; no external validity"],
            ["Explains every recommendation with parts and reasons", "No collaborative filtering across learners"],
            ["Adapts at once to learner events without retraining", "Action advice can change sign after a few events"],
            ["Reports its own weaknesses (effective sample size, fairness gaps)", "Offline policy evidence is weak (effective sample size 9.1)"],
            ["Runs on one ordinary desktop with open-source software", "Single-node SQLite, no cache, demonstration-grade tokens"],
        ], widths=[3.1, 3.1], size=10),

        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing system and its limitations"),
        P("A learner today meets one of three situations. On a course platform they search a catalogue by keyword and category and sort by rating or popularity. On a platform with a recommendation feature "
          "they receive a list tuned mostly to engagement. In a research setting, such as the base paper, a pipeline predicts risk and evaluates policies offline but never reaches a learner."),
        B("**Keyword search and popularity lists** treat every learner alike: a beginner and an advanced learner see the same ranking.",
          "**Engagement-tuned lists** reward clicks, not learning outcome, and give a new learner little because no history exists.",
          "**Single-course suggestions** ignore the order in which courses should be taken.",
          "**Research pipelines** are not interactive and give no explanation that a learner can read.",
          "**Closed platforms** do not let a student inspect how scores are made."),
        H2("4.2 Proposed system and its advantages"),
        P("LearnPathIQ is a locally deployed web application. A learner registers, fills a profile and immediately receives a ranked list of the 24 courses. Each card shows a match percentage, an estimated chance of success, "
          "a suggested next action and the reasons. Events the learner logs change the next ranking, and a staged learning path, an insights page and a model-analytics area complete the product."),
        B("**Cold-start ready:** the first ranking uses only the profile text, skill level, topics, goals and the catalogue.",
          "**Explainable:** the eight score parts and up to three reasons are returned with every card.",
          "**Adaptive:** the behavioural boost, the engagement score and the success estimate change with each event.",
          "**Transparent about evidence:** the analytics screen shows the data source, the model comparison, the confusion matrices, the policy-evaluation estimates with their effective sample size and the fairness audit.",
          "**Inspectable:** the code, the data generator and the experiments are small enough for a student to read and rerun."),
        H2("4.3 Functional requirements"),
        P("Each requirement is tied to the route or module that implements it. Priorities follow the MoSCoW scheme (Must, Should, Could)."),
        TAB("Functional requirements", ["ID", "Requirement", "Implemented by", "Priority"], FUNCTIONAL, widths=[0.5, 3.3, 1.8, 0.7], size=9, align=["c", "l", "l", "c"]),
        H2("4.4 Non-functional requirements"),
        TAB("Non-functional requirements", ["Quality", "Requirement", "Verified by"], NONFUNCTIONAL, widths=[1.1, 3.6, 1.6], size=9),
        H2("4.5 Hardware requirements"),
        TAB("Hardware requirements", ["Item", "Minimum (documented in the project)", "Machine used for all measurements"], [
            ["Processor", "A recent 64-bit CPU; no GPU needed", f"{_ENV['cpu']}, {_ENV['cores']} cores / {_ENV['logical_processors']} threads"],
            ["Memory", "4 GB (8 GB recommended)", f"{_ENV['ram_gb']} GB"],
            ["Disk", "About 500 MB free for the Python environment and data", "Local SSD"],
            ["Graphics", "None", f"{_ENV['gpu']}"],
            ["Network", "Not needed after installation; localhost only", "Loopback (127.0.0.1)"],
        ], widths=[1.2, 2.6, 2.5], size=10),
        H2("4.6 Software requirements"),
        TAB("Software requirements", ["Component", "Version used", "Purpose"], [
            ["Operating system", "Windows 11 Pro, version " + _ENV["os"].split("-")[2], "Development and measurement"],
            ["Python", _ENV["python"], "Back end and training"],
            ["FastAPI / Uvicorn", f"{_PK['fastapi']} / {_PK['uvicorn']}", "Web service"],
            ["SQLAlchemy / Pydantic", f"{_PK['sqlalchemy']} / {_PK['pydantic']}", "ORM and validation"],
            ["pandas / NumPy", f"{_PK['pandas']} / {_PK['numpy']}", "Data generation and features"],
            ["scikit-learn / XGBoost / joblib", f"{_PK['scikit-learn']} / {_PK['xgboost']} / {_PK['joblib']}", "Models and storage of fitted models"],
            ["matplotlib", _PK["matplotlib"], "Training plots"],
            ["passlib", _PK["passlib"], "Password hashing (pbkdf2_sha256)"],
            ["pytest", _PK["pytest"], "Automated tests"],
            ["Node.js / npm", f"{_ENV['node']} / {_ENV['npm']}", "Front-end build and dev server"],
            ["React / Vite / React Router / Recharts", f"{_ENV['frontend_dependencies']['react']} / {_ENV['frontend_dependencies']['vite']} / {_ENV['frontend_dependencies']['react-router-dom']} / {_ENV['frontend_dependencies']['recharts']}", "Interface and charts"],
            ["Browser", "Chrome (driven by Playwright for the checks)", "Use and automated checks"],
        ], widths=[2.1, 2.1, 2.1], size=9.5),
        H2("4.7 User roles"),
        TAB("User roles", ["Role", "Can do", "Cannot do"], [
            ["Visitor (not signed in)", "View the landing page, browse and filter the catalogue, open a course, view model analytics, register, sign in", "See recommendations, path, insights or any personal data"],
            ["Learner (signed in)", "Edit own profile, receive and refresh recommendations, record events, follow the path, view own activity and history and insights", "See another learner's data"],
            ["Developer / administrator", "Retrain the models, rerun experiments and tests, change the catalogue file (outside the interface)", "Not available through the web interface: there is no admin screen"],
        ], widths=[1.5, 3.0, 1.8], size=10),
        H2("4.8 Data requirements"),
        TAB("Data used by the system", ["Data", "Fields", "Source"], [
            ["Learner account", "name, e-mail (unique), password hash, creation time", "Registration form"],
            ["Learner profile (1 : 1)", "education, skill level, interests, preferred topics, learning style, goals, course preferences, weekly hours, age band, gender", "Profile form"],
            ["Course", "id, title, category, topic, skill level, description, duration, difficulty, prerequisites, outcomes, tags, resource type, rating", "`data/catalog/courses.json` (24 courses, 9 categories)"],
            ["Interaction event", "user, course, event type (9 kinds), value, time", "Learner actions in the interface"],
            ["Recommendation log", "user, course, score, explanation, time", "Written on every ranking"],
            ["Learner state (for the models)", "cum_clicks, recent_clicks, quiz_count, forum_count, completions, engagement, weekly_hours, skill_code", "Derived from events and profile; in training from the synthetic generator"],
            ["Training data", f"{F.PROFILE['rows']:,} learner-weeks (2,200 learners x 12 weeks), success rate {F.pct(F.PROFILE['success_rate'])}", "`synthetic-oulad-like-fallback-v1`, seed 42"],
        ], widths=[1.5, 3.1, 1.7], size=9.5),
        H2("4.9 Use cases"),
        FIG(F.diag("08_use_case_diagram.png"), "Use-case diagram of LearnPathIQ", 4.6),
        TAB("Main use cases", ["ID", "Use case", "Actor", "Main flow"], [
            ["UC1", "Register and sign in", "Visitor", "Enter name, e-mail and password; the account, an empty profile and a token are created and a cookie is set"],
            ["UC2", "Fill the profile", "Learner", "Enter education, skill level, interests, topics, goals and weekly hours; save"],
            ["UC3", "Browse the catalogue", "Visitor, learner", "Search by text; filter by category and level; open a course"],
            ["UC4", "View recommendations", "Learner", "The ranked list appears with match, success estimate, suggested action and reasons"],
            ["UC5", "Give feedback", "Learner", "Press start, quiz, complete, save or dismiss; the event is stored and the next ranking changes"],
            ["UC6", "Follow the learning path", "Learner", "Read the staged path and the next best action"],
            ["UC7", "Read insights", "Learner", "See engagement, success estimate, action benefits, strengths and areas to attend to"],
            ["UC8", "Inspect model analytics", "Visitor, learner", "Compare models, read the confusion matrices, offline policy estimates and fairness audit"],
            ["UC9", "Retrain the models", "Developer", "Run the training script; reload the models by `POST /api/recommendations/refresh` or restart"],
        ], widths=[0.5, 1.5, 1.1, 3.2], size=9.5, align=["c", "l", "l", "l"]),
        H2("4.10 Traceability of requirements to tests"),
        TAB("Requirement coverage by the tests", ["Requirement", "Automated test or check"], [
            ["FR1, FR2", "`test_auth_profile_recs_interactions` (register and token); `test_invalid_inputs` (bad e-mail and password mismatch give 422); smoke test (register, duplicate e-mail, session restore, logout, 401 after logout, bad password, login)"],
            ["FR3, FR4", "`test_auth_profile_recs_interactions` (profile update, catalogue list, course detail); `test_invalid_inputs` (unknown course gives 404)"],
            ["FR5, FR6, FR8", "`test_auth_profile_recs_interactions` (ranking, interaction, refresh); persona and feedback-loop experiments"],
            ["FR7", "`test_invalid_inputs` (unknown event type gives 400); smoke test"],
            ["FR9 to FR13", "`test_auth_profile_recs_interactions` (learning path, insights, activity, history, metrics, fairness); `test_health`; `test_artifacts_load`"],
            ["FR14, FR15", f"Smoke test through the front-end proxy ({F.TESTS['smoke']['checks']} checks); responsive check on 11 screens at 3 widths in 2 themes"],
        ], widths=[1.4, 4.9], size=9.5),
    ]
