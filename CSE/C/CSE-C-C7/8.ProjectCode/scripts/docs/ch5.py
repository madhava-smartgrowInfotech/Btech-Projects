"""Chapter 5: System design. The diagram explanations are shared with '11. BLOCK DIAGRAMS ALL.docx'."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import c
from . import facts as F

# (key, section title, file, caption, explanation)
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png", "System architecture of LearnPathIQ",
     "The system has four tiers. In the presentation tier the React 19 single-page application (Vite development server, port 5407) and the original "
     "server-rendered Jinja2 interface (port 8407) are the two ways a learner reaches the system; the React server proxies `/api` and `/static` to the backend "
     "so the session cookie stays same-origin. The application tier is the FastAPI service: `app/main.py` creates the application, seeds the course table, mounts "
     "the static folder and serves the Jinja pages, while `app/api_routes.py` holds the 18 JSON routes under `/api` and resolves the learner from the `lpq_token` "
     "cookie or the `X-Token` header; `security.py` and `schemas.py` supply password hashing, token generation and request validation. The recommendation tier "
     "is `app/recommender.py`: `rank_courses()` combines the TF-IDF, skill, topic, goal, rating and behaviour terms with the engagement score, the predicted "
     "success probability and the per-action uplift, and the model bundle is read once through `load_ml_bundle()`. The data tier holds the SQLite file "
     "`learnpathiq.db` (six tables), the 24-course catalogue in `data/catalog/courses.json` that seeds the course table at start-up, and the trained artefacts "
     "(`models/*.joblib`, `artifacts/metrics`, `artifacts/plots`), which the offline script `scripts/train_pipeline.py` writes. Dashed arrows are start-up or offline only."),
    ("flow", "High-level workflow", "02_high_level_workflow.png", "High-level workflow of one learner session",
     "A session has eight steps. The learner registers or signs in (the password is checked against its PBKDF2 hash and an HttpOnly cookie is set), "
     "builds a profile (education, skill level, interests, preferred topics, goals, weekly hours), and the system scores the catalogue against it. The learner "
     "state is then fed to the success model and the action-benefit models, the eight terms are combined into a ranked list with a short explanation per course, "
     "and the learner acts on it (view, start, quiz, complete, dismiss and so on), each action being written to the interactions table. Because the behaviour "
     "and engagement terms are recomputed from that table on every request, the next ranking changes at once without retraining; the dashboard, learning path, "
     "insights and model analytics screens present the result. Steps 6 and 7 form the feedback loop."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png", "Data flow diagram, level 0 (context diagram)",
     "The context diagram shows LearnPathIQ as a single process with one external entity, the learner. The learner sends credentials, profile data and "
     "interaction events; the system returns ranked courses, the learning path, insights and model metrics. Internally the process reads and writes the SQLite "
     "store (D1: users, profiles, interactions and the recommendation log), reads the course catalogue (D2) and reads the trained model bundle (D3)."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png", "Data flow diagram, level 1",
     "Level 1 has five processes. Authenticate (1.0) checks credentials against the users and tokens store (D0) and issues the token and cookie. Manage "
     "profile (2.0) accepts the profile and passes the learner state on to Rank courses (3.0), which reads the model bundle and catalogue (D3) and writes the "
     "ranked list to the recommendation log (D2). Record interaction (4.0) writes each event to the profiles and interactions store (D1), and the log from 3.0 "
     "feeds it. Insights, path and model analytics (5.0) reads the stored events and returns the learning path, the insights and the model metrics. Every process "
     "except 1.0 requires a valid session token and answers HTTP 401 otherwise (the public catalogue and model-analytics routes are the exceptions described in "
     "Section 5.7)."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png", "Data flow diagram, level 2: process 3.0 expanded",
     "Level 2 expands the ranking process into nine steps. The learner state is built from the profile and the stored interactions (3.1); the TF-IDF content "
     "similarity of the profile against each course text is computed (3.2); the skill-compatibility, topic-interest, goal and rating terms follow (3.3) together "
     "with the behavioural boost from earlier events (3.4); the success probability and the per-action uplift come from the model bundle (3.5). The eight terms "
     "are combined by a weighted sum (3.6), clipped to [0, 1] and sorted (3.7), up to three reasons are attached to each course (3.8) and the best action "
     "(the action with the largest estimated benefit) is attached to every card (3.9). The weights are 0.30, 0.15, 0.15, 0.12, 0.10, 0.08, 0.05 and 0.05."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png", "UML class diagram (ORM classes and the recommender module)",
     "The six database tables are mapped by SQLAlchemy classes: `User` has one `Profile` and many `AuthToken` and `Interaction` rows; `Course` and "
     "`RecommendationLog` are standalone (the log stores the user and course ids as plain columns). The `Recommender` module (`app/recommender.py`) is drawn as a "
     "class stereotyped as a module, listing its public functions and the weight vector; it reads `Interaction` rows, scores `Course` rows and calls the "
     "`ModelBundle` (the joblib artefact: scaler, selected model, feature list, one-vs-rest uplift models and the policy-evaluation configuration) through "
     "`predict_proba`. `ApiRouter` (`app/api_routes.py`) loads the bundle, writes the log rows and uses `Security` for hashing and tokens; "
     "`TrainPipeline` (`scripts/train_pipeline.py`) runs offline and writes the bundle. The code base is function-oriented, so modules stand in for classes "
     "except in the ORM layer."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png", "Sequence diagram: requesting recommendations and logging feedback",
     "The sequence follows one pass of the feedback loop. Opening the Recommendations page makes the React app call `GET /api/recommendations?top_n=8` with the "
     "session cookie. The API resolves the token to a user and loads the profile and the 24 courses from SQLite, then calls `rank_courses()`. The recommender reads "
     "the learner's recent interactions (engagement and boost), asks the model bundle for the success probability and the five action benefits, and returns the "
     "ranked list with reasons. The API stores one `recommendation_logs` row per card and returns the JSON; the page shows the cards. When the learner presses "
     "Start, Dismiss or Save, the page posts `{course_id, event_type}` to `/api/interactions`; the API validates the event type and inserts the row, and the next "
     "`GET /api/recommendations` returns a list ranked with the new behaviour boost. A missing token gives 401 and an unknown event type gives 400, and nothing is written."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png", "Use-case diagram",
     "The learner can register or sign in, fill the profile, browse and search the catalogue, view ranked recommendations and the reasons for each, log "
     "interactions (start, quiz, complete, dismiss and so on), follow the staged learning path, read insights and the suggested next action, review the activity "
     "log and recommendation history, and inspect the model analytics and fairness audit. The catalogue, the course detail and the analytics routes are public in the "
     "code; the profile, recommendation, path, insight, activity and interaction routes require a session. The developer or administrator is a second actor who "
     "retrains the models, refreshes the artefacts and runs the tests with scripts outside the web interface."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png", "Entity-relationship diagram of the SQLite database",
     "The database has six tables. `users` is the parent of `profiles` (one to one, because `profiles.user_id` is unique), `auth_tokens` (one to many) and "
     "`interactions` (one to many); these three links are declared foreign keys, and the ORM relationships cascade deletion from a user to its profile, "
     "interactions and tokens. `courses` is referenced by `interactions.course_id` and `recommendation_logs.course_id`, and `recommendation_logs.user_id` "
     "refers to a user, but these are plain columns without a declared foreign key, so no database constraint ties them to their parent. SQLite does not enforce "
     "declared foreign keys unless a pragma is switched on, and the code does not switch it on."),
    ("flowchart", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png", "Flowchart of the core algorithm: rank_courses()",
     "The flowchart gives the steps of `GET /api/recommendations` in order. A missing or invalid token ends the request with 401. Otherwise the profile, the 24 "
     "courses and the recent interactions are loaded; the engagement score and the eight-feature learner state are built; the success probability and the "
     "per-action uplift are computed; the TF-IDF cosine similarity is computed once for all courses; and for each course the skill, topic, goal, rating and behaviour "
     "terms are added to form the weighted score, which is clipped to [0, 1]. Up to three reasons and the best action are attached, the list is sorted and cut to "
     "the top N, and one `recommendation_logs` row is inserted per card before the JSON is returned. With no interests or goals the content term is weak "
     "(only the education and skill words feed it) but the other terms still rank the catalogue."),
]

SCHEMA = [
    ["users", "id (PK), name, email (unique), password_hash, created_at", "Learner account; the password is stored only as a PBKDF2-SHA256 hash"],
    ["profiles", "id (PK), user_id (FK, unique), education, skill_level, interests, preferred_topics, learning_style, goals, course_preferences, weekly_hours, age_band, gender, updated_at",
     "One profile per learner; interests and goals are comma-separated text"],
    ["courses", "id (PK, e.g. PY101), title, category, topic, skill_level, description, duration_hours, difficulty, prerequisites, outcomes, tags, resource_type, rating",
     "The 24 seeded courses"],
    ["interactions", "id (PK), user_id (FK), course_id, event_type, value, created_at",
     "Feedback events: view, open, start, content, quiz, forum, save, complete, dismiss"],
    ["recommendation_logs", "id (PK), user_id, course_id, score, explanation, created_at", "One row per recommended card, shown on the Activity page"],
    ["auth_tokens", "id (PK), user_id (FK), token (unique), created_at", "Opaque session tokens issued at register and login, deleted at logout"],
]

MODULES = [
    ["`app/main.py`", "Application entry", "creates the FastAPI app, `seed_courses()`, static mount, Jinja pages `/`, `/register`, `/login`, `/onboarding`, `/dashboard`, `/recommendations`, `/course/{id}`, `/path`, `/activity`, `/insights`, `/analytics`"],
    ["`app/api_routes.py`", "JSON API", "18 routes, `get_current_user`, `require_user`, `profile_dict`, `course_dict`, cached `bundle()`"],
    ["`app/recommender.py`", "Recommendation engine", "`content_scores`, `skill_compat`, `topic_interest_score`, `behavioral_boost`, `engagement_level`, `learner_state_vector`, `predict_success`, `uplift_scores`, `rank_courses`, `load_ml_bundle`"],
    ["`app/models.py`, `app/database.py`", "Persistence", "six SQLAlchemy classes, engine, `SessionLocal`, `get_db`, `init_db`"],
    ["`app/security.py`, `app/schemas.py`", "Security and validation", "`hash_password`, `verify_password`, `new_token`; `RegisterIn`, `LoginIn`, `ProfileIn`, `InteractionIn`"],
    ["`app/config.py`", "Settings", "database URL, secret key, model and artefact folders, read from `.env`"],
    ["`scripts/train_pipeline.py`", "Offline training", "`acquire_data`, `split_learners`, `train_eval` (models, uplift, policy evaluation, fairness audit, plots)"],
    ["`scripts/run_experiments.py` and others", "Evidence for the documents", "six-seed study, ceiling check, persona evaluation with ablation, feedback-loop probe; `measure_api.py`, `collect_env.py`"],
    ["`frontend/src/pages/*`", "React screens", "Landing, Login, Register, Catalog, CourseDetail, Analytics, Dashboard, Recommendations, LearningPath, Insights, Activity, Profile, NotFound"],
    ["`frontend/src/components`, `lib`, `styles`", "UI kit and client logic", "layout shells, cards, charts, forms, toasts; `api.js`, `auth.jsx`, `theme.jsx`, `useApi.js`; design tokens and global CSS"],
    ["`tests/test_app.py`, `scripts/*`", "Verification", "5 pytest tests, smoke test, responsive check, screenshot capture"],
]

ENDPOINTS = [
    ["POST", "/api/auth/register", "No", "Create account, empty profile and token; sets the cookie"],
    ["POST", "/api/auth/login", "No", "Verify the password hash; issue a token and cookie"],
    ["POST", "/api/auth/logout", "No", "Delete the token row and the cookie"],
    ["GET", "/api/me", "No", "Signed-in user or `null`"],
    ["GET / PUT", "/api/profile", "Yes", "Read or update the learner profile"],
    ["GET", "/api/courses?q=&category=&level=", "No", "Search and filter the catalogue"],
    ["GET", "/api/courses/{id}", "No", "Course detail; match score, success probability and suggested action when signed in; 404 if unknown"],
    ["GET", "/api/recommendations?top_n=", "Yes", "Ranked list with the eight term values, reasons, engagement and uplift"],
    ["POST", "/api/recommendations/refresh", "Yes", "Reload the model bundle and re-rank"],
    ["POST", "/api/interactions", "Yes", "Log an event; 400 for an unknown event type"],
    ["GET", "/api/activity?limit=", "Yes", "The learner's latest interaction events"],
    ["GET", "/api/history", "Yes", "The latest 40 recommendation-log rows"],
    ["GET", "/api/learning-path", "Yes", "Up to six staged steps and the next best action"],
    ["GET", "/api/insights", "Yes", "Engagement, success estimate, action benefits, strengths, attention points"],
    ["GET", "/api/metrics", "No", "Model comparison, confusion matrices, policy evaluation, fairness; 503 if not trained"],
    ["GET", "/api/fairness", "No", "The fairness audit with a note that it is an audit only"],
    ["GET", "/api/health", "No", "`ok`, `models_ready`, application name"],
    ["GET", "/static/{roc_curve, confusion_matrix, feature_importance}.png", "No", "The three training plots"],
]

SCREENS = [
    ["Landing `/`", "Public introduction with the value proposition, how it works and live catalogue figures"],
    ["Sign in `/login`, Register `/register`", "Forms with inline validation messages; a new account is taken to the profile form"],
    ["Course catalogue `/courses`", "Search and filter by category and level; public, and also available inside the signed-in shell"],
    ["Course detail `/courses/:id`", "Description, prerequisites, outcomes, tags, the \"why recommended\" panel, and buttons that log start, content, quiz, discussion and complete events"],
    ["Model analytics `/analytics`", "Four tabs: model comparison, diagnostics (confusion matrices, ROC curve, feature importance), offline policy evaluation and fairness audit"],
    ["Dashboard `/app`", "Engagement status, success estimate, next action, recent activity and top recommendations"],
    ["Recommendations `/app/recommendations`", "Ranked cards with match percentage, success estimate, suggested action and explanation; search, refresh, view, start, dismiss"],
    ["Learning path `/app/path`", "Up to six staged steps with the reason and action for each, and the next best action"],
    ["Insights `/app/insights`", "Engagement, success estimate, estimated benefit by action, strengths and attention points, interactions by type"],
    ["Activity `/app/activity`", "Interaction log and recommendation history"],
    ["Profile `/app/profile`", "The learner profile form, also shown first after registration"],
    ["Not found `*`", "A 404 page with a way back"],
]

TIERS = [
    ["Presentation", "React 19 SPA (port 5407); Jinja2 pages (port 8407)", "Collect input, show ranked courses, explanations and model transparency"],
    ["Application", "FastAPI routes, Pydantic validation, token authentication", "Validate requests, resolve the learner, orchestrate ranking, log feedback"],
    ["Recommendation", "TF-IDF, rule-based terms, logistic-regression success model, uplift models", "Score and rank the catalogue"],
    ["Data", "SQLite file, JSON catalogue, joblib artefacts", "Persist accounts, events and logs; hold the trained models"],
]


def diagram_blocks(heading_level=3):
    out = []
    for i, (key, title, file, caption, text) in enumerate(DIAGRAMS, 1):
        out.append(("h3" if heading_level == 3 else "h2", f"{title}"))
        out.append(FIG(F.diag(file), caption, 6.0))
        out.append(P(text))
    return out


def schema_blocks():
    return [
        TAB("Tables of the SQLite database", ["Table", "Columns", "Purpose"], SCHEMA, widths=[1.2, 3.3, 1.8], size=9.5),
        P("The tables are created by `init_db()` through `Base.metadata.create_all`, so a fresh checkout needs no migration, and the course table is filled from "
          "`data/catalog/courses.json` the first time the application starts with an empty table. All queries go through the SQLAlchemy ORM, which uses bound "
          "parameters, so file names, e-mail addresses and search text are never concatenated into SQL."),
    ]


def blocks():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Architecture"),
        P("The design follows two rules: keep each tier replaceable, and keep the recommendation logic in one module that the routes only call. The original "
          "Jinja2 interface and the React interface use the same FastAPI routes and the same database, so the two front ends always agree."),
        TAB("The four tiers", ["Tier", "Components", "Responsibility"], TIERS, widths=[1.2, 2.8, 2.3], size=10),
        FIG(F.diag("01_system_architecture.png"), "System architecture of LearnPathIQ", 6.0),
        P(DIAGRAMS[0][4]),
        H2("5.2 High-level workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of one learner session", 6.0),
        P(DIAGRAMS[1][4]),
        H2("5.3 Data flow diagrams"),
        H3("Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0 (context diagram)", 5.6),
        P(DIAGRAMS[2][4]),
        H3("Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1", 5.8),
        P(DIAGRAMS[3][4]),
        H3("Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: process 3.0 expanded", 5.8),
        P(DIAGRAMS[4][4]),
        H2("5.4 UML diagrams"),
        H3("Class diagram"),
        FIG(F.diag("06_uml_class_diagram.png"), "UML class diagram (ORM classes and the recommender module)", 6.0),
        P(DIAGRAMS[5][4]),
        H3("Sequence diagram"),
        FIG(F.diag("07_sequence_diagram.png"), "Sequence diagram: requesting recommendations and logging feedback", 5.8),
        P(DIAGRAMS[6][4]),
        H3("Use-case diagram"),
        FIG(F.diag("08_use_case_diagram.png"), "Use-case diagram", 5.4),
        P(DIAGRAMS[7][4]),
        H3("Core algorithm flowchart"),
        FIG(F.diag("10_core_algorithm_flowchart.png"), "Flowchart of the core algorithm: rank_courses()", 4.8),
        P(DIAGRAMS[9][4]),
        H2("5.5 Database design"),
        FIG(F.diag("09_er_diagram.png"), "Entity-relationship diagram of the SQLite database", 5.6),
        P(DIAGRAMS[8][4]),
        *schema_blocks(),
        H2("5.6 Module design"),
        TAB("Modules and responsibilities", ["Module", "Responsibility", "Key contents"], MODULES, widths=[1.7, 1.3, 3.3], size=9),
        P("The backend package `app/` is 649 lines of Python in total; "
          "`rank_courses()` is the only function the routes need for a ranking and every term it adds comes from a separate helper function."),
        H2("5.7 API design"),
        P("The API is JSON over HTTP. Errors use the standard FastAPI body `{\"detail\": \"message\"}`: 400 for a bad event type, a duplicate e-mail or mismatched "
          "passwords, 401 for a missing or invalid token or a wrong password, 404 for an unknown course, 422 for a request body that fails Pydantic validation "
          "(for example a malformed e-mail address or a name shorter than two characters) and 503 when the training artefacts are missing. The session is a random "
          "opaque token (`secrets.token_urlsafe(32)`) stored in `auth_tokens`; it is accepted from the HttpOnly cookie `lpq_token`, the `X-Token` header or a Bearer header. "
          "The catalogue, the course detail, the model metrics and the fairness audit are public by design, because they contain no learner data."),
        TAB("REST endpoints", ["Method", "Path", "Session", "Purpose"], ENDPOINTS, widths=[0.8, 2.3, 0.7, 2.5], size=9, align=["c", "l", "c", "l"]),
        P("The original Jinja2 pages are `/`, `/register`, `/login`, `/onboarding`, `/dashboard`, `/recommendations`, `/course/{id}`, `/path`, `/activity`, "
          "`/insights` and `/analytics`; each loads its data from the same JSON routes."),
        H2("5.8 User interface design"),
        P("The React interface uses a \"neo-brutalist grid\" visual language: a warm paper background, thick black outlines, hard offset shadows, a visible grid, "
          "a heavy display typeface for headings, a sans-serif body face and a monospace face for numbers (fonts from the Fontsource packages). Lime, coral, sky "
          "and amber accents carry meaning (for example, lime marks the best next action), and every status is also given as text so that meaning never depends on colour alone. "
          "There is a light and a dark theme with a toggle that remembers the choice. The signed-in shell has a sidebar that becomes a drawer on narrow screens, "
          "and the public shell has its own header; pages are loaded lazily and show skeleton placeholders while data arrive."),
        TAB("Screens", ["Screen", "Content"], SCREENS, widths=[2.0, 4.3], size=9.5),
        P("Accessibility was designed in rather than added later: a skip link is the first keyboard stop on every page, focus outlines are visible, the mobile "
          "drawer is a dialog that closes with the Escape key, and a reduced-motion setting collapses animation to fades. Chapter 7 reports the automated "
          "check of the layout at three widths in both themes."),
    ]
