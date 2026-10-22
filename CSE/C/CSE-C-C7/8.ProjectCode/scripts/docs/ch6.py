"""Chapter 6: Methodology and software implementation."""

from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import c
from . import facts as F


def _m():
    return F.METRICS or {}


def _pct(x):
    return f"{x * 100:.1f}"


def _model_rows():
    m = _m().get("models", {})
    rows = []
    for k in ("logistic_regression", "random_forest", "xgboost"):
        if k in m:
            v = m[k]
            rows.append([F.MODEL_LABEL[k] + (" (selected)" if k == _m().get("selected_model") else ""), f"{v['val_auc']:.4f}", f"{v['roc_auc']:.4f}",
                         f"{v['accuracy']:.4f}", f"{v['f1']:.4f}", f"{v['brier']:.4f}"])
    return rows


def methodology_blocks():
    P_ = (_m().get("policy_evaluation") or {})
    prof = F.PROFILE or {}
    run_s = ((F.SEEDS or {}).get("runs") or [{}])[0].get("seconds", 6.0)
    corr = prof.get("corr_with_success", {})
    ac = prof.get("action_counts", {})
    return [
        H2("6.1 Overall methodology"),
        P("The method has two phases that meet in one module. In the **offline phase** the script `scripts/train_pipeline.py` generates a synthetic, OULAD-like table "
          "of learner behaviour, splits it by learner, fits three classifiers that predict whether a learner-week ends in success, fits a pair of logistic regressions "
          "per learning action to estimate its benefit, runs an offline policy evaluation and a fairness audit, and saves everything the application needs "
          f"as joblib and JSON files. In the **online phase** every request for recommendations runs `rank_courses()` in `app/recommender.py`, which combines a "
          "content-based score, simple rules, the learner's recent behaviour and the two model outputs into one ranked list with an explanation per course. "
          "The structure follows the base paper " + c("base") + ", which couples a success predictor, an uplift estimate of the benefit of each learning action "
          "and offline policy evaluation, but it replaces the paper's OULAD data with a synthetic generator and does not implement its reinforcement-learning agent "
          "(Section 6.5 and Chapter 10)."),
        FIG(F.diag("10_core_algorithm_flowchart.png"), "The online ranking procedure (flowchart repeated from Chapter 5)", 4.4),
        H2("6.2 Data"),
        P("**The training data are synthetic.** `acquire_data()` first sends one short request to the Open University Learning Analytics Dataset page "
          f"{c('oulad')} but never reads a file from it; whatever the response, it then generates a table with the same kind of columns, tagged "
          "`synthetic-oulad-like-fallback-v1`. The real OULAD was not downloaded and no number in this report comes from it. The generator is seeded (seed 42), so a re-run "
          "reproduces the shipped files exactly."),
        P(f"The table has {prof.get('learners', 2200):,} learners observed for {prof.get('weeks', 12)} weeks, that is {prof.get('rows', 26400):,} learner-week rows. "
          "For each learner the generator draws an age band (0-35, 35-55 or 55 and over, with probabilities 0.6, 0.3 and 0.1), a gender, an education level, a skill code "
          "(0, 1 or 2) and a latent *ability* that rises with skill and postgraduate education and falls slightly for the oldest band. Each week it draws the number of "
          "clicks from ability plus noise, whether the learner took a quiz or posted in the forum, homepage visits, content clicks and an assessment score "
          "(60 + 10 x ability + noise, clipped to 0-100); a completion flag is set in week 12 for learners with ability above 0.5."),
        P("The label is generated, not observed: a learner-week is a success when the hidden assessment score is at least 50 **and** a uniform random draw falls below "
          "0.55 + 0.2 x (score - 50) / 50. The label is therefore noisy by construction, and the assessment score is not one of the eight features the deployed model sees. "
          "The learning action of a week is the first of quiz, content, forum, homepage or continue-course that applies to that week's behaviour (a quiz if one was taken, "
          "otherwise content if content clicks exceed four, and so on), so actions are assigned by a rule on behaviour and not at random."),
        TAB("The synthetic data set", ["Item", "Value"], [
            ["Source tag", "`synthetic-oulad-like-fallback-v1` (real OULAD not used)"],
            ["Learners x weeks", f"{prof.get('learners', 2200):,} x {prof.get('weeks', 12)} = {prof.get('rows', 26400):,} rows"],
            ["Success rate", _pct(prof.get("success_rate", 0.4397)) + " %"],
            ["Logged actions", ", ".join(f"{k} {v:,}" for k, v in ac.items())],
            ["Features given to the models", "cum_clicks, recent_clicks, quiz_count, forum_count, completions, engagement, weekly_hours, skill_code"],
            ["Hidden columns", "assessment score (drives the label), age band, gender, education, homepage hits, content clicks"],
        ], widths=[1.8, 4.5], size=10),
        FIG(F.fig("fig_data_profile.png"), "Logged action counts and label balance of the synthetic data", 5.6),
        P("Correlation of each feature with the label is weak (largest: recent_clicks 0.183 and engagement 0.182, forum_count 0.002), which sets the ceiling for any "
          "model trained on these features; Chapter 8 shows that adding the hidden assessment score lifts the test AUC from 0.60 to 0.80, so the weak signal is a property of the generated data and not "
          "of the models."),
        FIG(F.fig("fig_feature_signal.png"), "Correlation of each feature with success (left) and the logistic-regression coefficients (right)", 6.0),
        H2("6.3 Learner-level split and success models"),
        P("The rows are split by learner, not by row, so no learner appears on both sides: the learner ids are shuffled with seed 42 and cut 80 / 10 / 10, giving "
          f"{_m().get('train_samples', 21120):,} training rows (1,760 learners), {_m().get('val_samples', 2640):,} validation rows (220 learners) and {_m().get('test_samples', 2640):,} "
          "test rows (220 learners). A `StandardScaler` is fitted on the training rows only. Three classifiers from scikit-learn " + c("sklearn") + " and XGBoost " + c("xgboost") + " are trained:"),
        B("**Logistic regression** (`max_iter=1000`), the interpretable baseline;",
          "**Random forest** " + c("breiman") + " with 200 trees;",
          "**XGBoost** with 300 trees, maximum depth 5, learning rate 0.05, subsample and column sampling 0.9."),
        P("The model with the highest **validation** AUC is selected and saved; the test split is used only for the reported metrics, at a decision threshold of 0.5. "
          "On the shipped run logistic regression wins (validation AUC 0.6035), and Chapter 8 shows that it is selected in four of six data-generation seeds (seed 42 included). "
          "The saved file is called `xgb_model.joblib` for historical reasons; it holds whichever model was selected, which is logistic regression in the shipped build."),
        TAB("Success models on the held-out test split (seed 42)", ["Model", "Val. AUC", "Test AUC", "Accuracy", "F1", "Brier"], _model_rows(),
            widths=[2.0, 0.9, 0.9, 0.9, 0.8, 0.8], size=10, align=["l", "c", "c", "c", "c", "c"]),
        P(f"One seed run (data generation, three models, uplift models) takes about {run_s:.1f} s on the development machine; the launcher prints \"1 to 3 minutes\" for the first "
          "run, which includes installing and the slower policy-evaluation loop."),
        H2("6.4 Estimated benefit of a learning action (T-learner)"),
        P("For each of the five actions (quiz, content, forum, homepage, continue-course) the script fits a **T-learner** " + c("kunzel") + ": one logistic regression on the "
          "learner-weeks where that action was taken (the treated arm) and one on all the other weeks (the control arm). For a learner state *x* the **estimated benefit** is the "
          "difference of the two predicted success probabilities. This is the one-versus-rest form of the uplift idea described in the base paper " + c("uplift", "base") + ". An action is fitted only when "
          "both arms have more than 200 rows and both outcomes; otherwise its benefit is reported as 0."),
        EQ("benefit(a | x) = P(success | x, treated by a) - P(success | x, not treated by a)       [two logistic regressions per action]"),
        P("At run time `uplift_scores()` evaluates the ten models on the learner's current state; the action with the largest benefit becomes the *suggested action* of every "
          "card, and its benefit is shown as the estimated benefit. Because the actions were assigned by a rule on behaviour in a synthetic log, these numbers are "
          "**associations learned from that log, not proven causal effects**, and the interface says so (\"based on observed learning patterns, not proven causal effects\"). "
          "Two further consequences are measured in Chapter 8: the benefits can change sign after a handful of events, and because the benefit depends only on the learner state the same "
          "suggested action appears on every card of one learner's list. If the bundle cannot be loaded, a state-based heuristic supplies the five numbers instead."),
        H2("6.5 Offline policy evaluation and what is not implemented"),
        P("Following the evaluation practice of the base paper, the script estimates the value of the policy \"give each learner-week the action with the largest estimated benefit\" "
          "from the logged test rows. A multinomial logistic regression on the learner state estimates the logging policy's propensity of the logged action; propensities are "
          "clipped to [0.02, 0.98], and the importance weight is 1 when the target action equals the logged one (otherwise 0), divided by the propensity and capped at 10. "
          "Three estimators are reported " + c("dudik") + ":"),
        EQ("IPS = mean(w r)        SNIPS = IPS / mean(w)        DR = mean( q(x) + w (r - q(x)) )        ESS = (sum w)^2 / sum(w^2)"),
        P("Here r is the observed success, q(x) the selected model's predicted success and ESS the effective sample size. The shipped run gives "
          f"IPS {P_.get('ips', 0):.4f}, SNIPS {P_.get('snips', 0):.4f} and DR {P_.get('doubly_robust', 0):.4f} with an effective sample size of {P_.get('effective_sample_size', 0):.1f} out of "
          f"{P_.get('test_samples', 0):,} rows. An effective sample size of about nine means a handful of rows carry all the weight, so these values are **not evidence that the policy "
          "improves outcomes**; they are reported as a transparency feature of the application, and the stored note calls them an observational offline estimate, not a live experiment."),
        P("**Not implemented:** the base paper's Actor-Critic reinforcement-learning agent, its causal regularisation, a collaborative-filtering model over many learners' course "
          "histories (the behavioural term of Section 6.8 is per learner) and any use of the real OULAD data. The project takes from the base paper only the success "
          "predictor, the uplift-style action estimate, offline policy evaluation and a fairness audit."),
        H2("6.6 Fairness audit"),
        P("The script groups the test rows by age band and by gender and reports, for each group, the number of rows, the observed success rate, the mean predicted success and "
          "the F1 score of the selected model. The audit is reporting only: no mitigation is applied, and the API note describes it as \"transparent reporting, not a claim of perfect fairness\". "
          "The result (Chapter 8) shows the lowest F1 for the 55-and-over band, which has only 204 test rows."),
        H2("6.7 Content-based scoring"),
        P("The text of a course is its title, description, topic, category, tags and skill level; the text of a learner is the interests, preferred topics, goals, course "
          "preferences, education and skill level from the profile. For every request a `TfidfVectorizer` (English stop words, at most 2,000 terms) is fitted on these "
          f"25 short documents (the profile plus the 24 courses) {c('tfidf')} and the content score of a course is the cosine similarity between its vector and the learner's."),
        EQ("content(c) = cos( tfidf(profile), tfidf(course c) )"),
        P("Fitting on 25 documents each time keeps the code simple and needs no stored index, at the price that the term weights change slightly with the catalogue, and that "
          "the catalogue is small enough that a whole recommendations request takes about 33 ms (Chapter 7)."),
        H2("6.8 Hybrid ranking, behaviour and explanations"),
        P("The final score of a course is a weighted sum of eight terms, clipped to [0, 1]. The weights are fixed constants in the code and were not fitted on data; Chapter 8 reports a "
          "drop-one-term ablation of them."),
        EQ("score(c) = 0.30 content + 0.15 skill + 0.15 topic + 0.12 success + 0.10 (0.5 + behaviour) + 0.08 goal + 0.05 rating + 0.05 engagement"),
        TAB("The eight terms of the hybrid score", ["Term", "Weight", "Definition in the code"], [
            ["content", "0.30", "TF-IDF cosine similarity between profile text and course text"],
            ["skill", "0.15", "Skill compatibility: level difference 0, 1 or 2 between learner (Beginner 0, Intermediate 1, Advanced 2; All levels counts as 1) and course gives 1.0, 0.6 or 0.3"],
            ["topic", "0.15", "Share of the learner's interest, topic and goal words (longer than two letters) found in the course's topic, category, tags and title; 0.5 if the learner has none"],
            ["success", "0.12", "Predicted success probability of the selected model for the learner state (same value for every course); 0.55 if the model is unavailable"],
            ["behaviour", "0.10", "0.5 plus the behavioural boost of this course, from the learner's events on it, clipped to [-0.3, 0.35]"],
            ["goal", "0.08", "0.7 if any comma-separated goal appears in the course title, description or tags, else 0.4"],
            ["rating", "0.05", "(rating - 3.5) / 1.5, clipped to [0, 1]"],
            ["engagement", "0.05", "Engagement score of the learner (same value for every course)"],
        ], widths=[0.9, 0.7, 4.7], size=9.5, align=["l", "c", "l"]),
        FIG(F.fig("fig_score_weights.png"), "Weights of the eight terms in the hybrid score", 4.6),
        P("Two of the eight terms (success and engagement, together 0.17 of the weight) are identical for every course of one learner, so they shift all scores together and cannot change the "
          "order; the order is decided by the other six terms. This is stated here because the \"success estimate\" shown beside each card is a property of the learner, not of the course."),
        H3("Behavioural boost and engagement"),
        TAB("Event weights of the behavioural boost", ["Event", "view", "open", "start", "content", "quiz", "forum", "save", "complete", "dismiss"],
            [["Weight", "0.05", "0.06", "0.12", "0.10", "0.14", "0.10", "0.08", "0.20", "-0.25"]], size=9.5, align=["l"] + ["c"] * 9),
        P("The boost of a course is the sum of the weights of the learner's events on that course, each multiplied by the event value (1.0 by default), clipped to [-0.3, 0.35]; an event type "
          "not in the table counts 0.03. The **engagement score** is computed from the last 200 events:"),
        EQ("engagement = min(1, 0.25 + 0.04 x (view, open, start, content, quiz and forum events) + 0.03 x quizzes + 0.08 x completions)"),
        P("With no events the score is 0.25 (label \"Getting started\"); below 0.4 the label is \"Getting started\", below 0.7 \"Steady learner\" and otherwise \"Highly engaged\"; a learner who "
          "dismissed a course among the last five events and has a score under 0.45 is labelled \"Needs a nudge\"."),
        H3("Learner state for the models"),
        P("The success and uplift models expect the eight training features, which `learner_state_vector()` builds from the profile and the logged events: cum_clicks is the number of events, recent_clicks "
          "that number capped at 20, quiz_count, forum_count and completions are the counts of those events, engagement is the score above, weekly_hours comes from the profile and "
          "skill_code is 0, 1 or 2. These definitions differ from the synthetic training weeks (where cum_clicks accumulates clicks), so the models are applied to a **proxy** of the "
          "state they were trained on; this is a limitation of the application, not something the offline metrics measure."),
        H3("Explanations and the learning path"),
        P("Each card carries up to three reasons chosen by rules: a content or topic reason (\"Matches your interests (tag, tag)\", \"Aligned with your topic preferences in ...\" or "
          "\"Broadens your ... knowledge\"), a skill reason (\"Fits your current skill level\", \"Stretches you slightly beyond your level\" or \"A comfortable refresher\"), "
          "\"You have engaged with similar material before\" when the boost exceeds 0.05, and \"High estimated completion likelihood\" when the predicted success exceeds 0.6. The **learning path** "
          "takes the top 12 courses, orders them by skill level (Beginner and All levels first, then Intermediate, then Advanced) and then by score, and keeps six; it uses no prerequisite graph."),
    ]


def application_blocks():
    pk = (F.ENV or {}).get("packages", {})
    fd = (F.ENV or {}).get("frontend_dependencies", {})
    rank_code = '''def rank_courses(profile, courses, db, user_id, bundle, top_n=8):
    sims = content_scores(profile, courses)
    eng = engagement_level(db, user_id)
    state = learner_state_vector(profile, eng)
    p_success, feat_imp = predict_success(bundle, state)
    upl = uplift_scores(bundle, state)
    ranked = []
    for i, c in enumerate(courses):
        cs = float(sims[i]) if len(sims) > i else 0.0
        sk = skill_compat(profile.get("skill_level", "Beginner"), c.get("skill_level", "Beginner"))
        ti = topic_interest_score(profile, c)
        beh = behavioral_boost(user_id, c.get("id", ""), db)
        ...
        score = 0.30*cs + 0.15*sk + 0.15*ti + 0.12*p_success + 0.10*(0.5+beh) + 0.08*goal + 0.05*rating_f + 0.05*eng["score"]
        score = round(float(max(0, min(1, score))), 4)
        ...
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_n], {"engagement": eng, "p_success": ..., "uplift": upl, ...}'''
    return [
        H2("6.9 Technology stack"),
        TAB("Backend and tooling (versions measured in the project environment)", ["Component", "Version", "Role"], [
            ["Python", (F.ENV or {}).get("python", ""), "Language of the backend and the training script"],
            ["FastAPI " + c("fastapi"), pk.get("fastapi", ""), "Web framework and OpenAPI generation"],
            ["Uvicorn", pk.get("uvicorn", ""), "ASGI server"],
            ["SQLAlchemy " + c("sqlalchemy"), pk.get("sqlalchemy", ""), "ORM over the SQLite file"],
            ["Pydantic", pk.get("pydantic", ""), "Request validation (including e-mail check)"],
            ["scikit-learn " + c("sklearn"), pk.get("scikit-learn", ""), "TF-IDF, logistic regression, random forest, metrics"],
            ["XGBoost " + c("xgboost"), pk.get("xgboost", ""), "Gradient-boosted trees (one of the three candidates)"],
            ["pandas / NumPy", f"{pk.get('pandas', '')} / {pk.get('numpy', '')}", "Data table and arrays"],
            ["joblib", pk.get("joblib", ""), "Saving and loading the models"],
            ["Matplotlib", pk.get("matplotlib", ""), "Training plots and the documentation figures"],
            ["Passlib", pk.get("passlib", ""), "PBKDF2-SHA256 password hashing"],
            ["pytest", pk.get("pytest", ""), "Automated tests"],
            ["Node.js / npm", f"{(F.ENV or {}).get('node', '')} / {(F.ENV or {}).get('npm', '')}", "Frontend build and development server"],
        ], widths=[1.9, 1.2, 3.2], size=9.5, align=["l", "c", "l"]),
        TAB("Frontend dependencies declared in `frontend/package.json`", ["Package", "Version", "Role"], [
            ["react, react-dom", fd.get("react", ""), "User interface"],
            ["react-router-dom", fd.get("react-router-dom", ""), "Routing with lazy-loaded pages"],
            ["recharts", fd.get("recharts", ""), "Bar charts of benefits, interactions and model metrics"],
            ["vite, @vitejs/plugin-react", f"{fd.get('vite', '')}, {fd.get('@vitejs/plugin-react', '')}", "Development server with proxy, production build"],
            ["framer-motion, gsap, lenis", f"{fd.get('framer-motion', '')}, {fd.get('gsap', '')}, {fd.get('lenis', '')}", "Page transitions and motion"],
            ["lucide-react", fd.get("lucide-react", ""), "Icons"],
            ["@fontsource/* (Archivo Black, IBM Plex Sans, IBM Plex Mono)", fd.get("@fontsource/archivo-black", ""), "Self-hosted fonts"],
        ], widths=[2.4, 1.3, 2.6], size=9.5, align=["l", "c", "l"]),
        P("`requirements.txt` pins every Python package, including Jinja2 3.1.4, python-multipart, email-validator, requests, Pillow and Playwright 1.49.1, so the environment can be rebuilt. "
          "The machine used is a 12th-generation Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory and no GPU, running Windows 11."),
        H2("6.10 Backend implementation"),
        P("`app/main.py` creates the FastAPI application, calls `init_db()`, fills the `courses` table from `data/catalog/courses.json` if it is empty, mounts `/static` "
          "and includes the router of `app/api_routes.py`. The routes are thin: each resolves the learner with `require_user()`, loads the profile and the 24 courses, calls into "
          "`app/recommender.py` and returns a dictionary. The model bundle is loaded lazily on first use by `bundle()` and cached in a module variable; `POST /api/recommendations/refresh` "
          "reloads it. `rank_courses()` is used by the recommendations route, by the learning-path route (top 12, then re-ordered) and by the course-detail route (top 50, to find the "
          "course's own score and reasons), and every recommendations call writes one `recommendation_logs` row per returned card."),
        CODE(rank_code, 8.5),
        P("The catalogue is small and hand-written (24 courses in nine categories, from Data Science with six courses to Design with one, rated 4.3 to 4.7 and lasting 4 to 30 hours), so "
          "everything is computed per request without a cache or an index; Chapter 7 gives the measured latency."),
        H2("6.11 Training script and saved artefacts"),
        P("`python scripts/train_pipeline.py` runs `acquire_data()`, `split_learners()` and `train_eval()` and writes: `data/processed/learner_states.csv` (the synthetic table); "
          "`models/scaler.joblib`, `models/xgb_model.joblib` (the selected model), `models/feature_cols.joblib`, `models/all_models.joblib` (all three models; it is large and git-ignored, and "
          "is never read at run time), `models/uplift.joblib` and `models/ope.joblib`; `artifacts/metrics/model_metrics.json` (metrics, confusion matrices, feature importance, policy "
          "evaluation, fairness); and three plots in `artifacts/plots/`, which are copied to `app/static/` so that the analytics page can show them. `run.bat` trains automatically when "
          "the metrics file is missing."),
        P("A defect found while preparing the frontend shows why the artefacts must match the pinned library versions: files saved with a newer scikit-learn could not be used under "
          "scikit-learn 1.5.2, and because `predict_success()` and `uplift_scores()` catch every exception, the application silently fell back to a constant 55 % success estimate "
          "and zero action benefits. Re-running the unchanged script under the pinned versions fixed it (selected model and test AUC were unchanged). The silent fallback is deliberate "
          "so the pages never crash, but it hides this kind of fault; the smoke test now checks that the success estimate differs from 0.55."),
        H2("6.12 Frontend implementation"),
        P("The React application (`frontend/src`) has `App.jsx` with three layouts: public pages (landing, sign in, register), adaptive pages that use the signed-in or the public shell "
          "(catalogue, course detail, model analytics) and the protected `/app` area guarded by `RequireAuth`, which redirects to the sign-in page. Pages are loaded with `React.lazy`, so the "
          "chart library stays in its own chunks. `lib/api.js` wraps `fetch` with `credentials: same-origin`, turns FastAPI's string or list `detail` into one readable message and fires an "
          "event on a 401 so the session can be cleared; `useApi` runs a loader on mount, ignores stale responses and exposes `{data, error, loading, reload}`; `lib/auth.jsx` keeps the "
          "user from `GET /api/me`; `lib/theme.jsx` stores the light or dark choice. Shared components (cards, stat tiles, charts, forms, tables, toasts, skeletons) live in `components/ui`, and the "
          "design tokens (colours, fonts, borders, shadows, spacing) in `styles/tokens.css`. The Vite server proxies `/api` and `/static` to port 8407, so the HttpOnly cookie is never exposed "
          "to scripts and no cross-origin configuration is needed."),
        H2("6.13 Security and error handling"),
        TAB("Controls", ["Threat or fault", "Control in the code"], [
            ["Password theft from the database", "Passwords are stored only as PBKDF2-SHA256 hashes (29,000 rounds, Passlib); the password is cut to 72 bytes before hashing"],
            ["Unauthenticated access", "Profile, recommendation, path, insight, activity and interaction routes depend on `require_user()` and answer 401"],
            ["Token guessing", "Tokens are `secrets.token_urlsafe(32)` values stored in `auth_tokens`; logout deletes the row"],
            ["Script access to the session", "Cookie `lpq_token` is `HttpOnly` and `SameSite=Lax` with a 72-hour lifetime"],
            ["Malformed input", "Pydantic: name 2-120 characters, e-mail format, password 6-100 characters; unknown event types answered with 400"],
            ["SQL injection", "All data access goes through the ORM with bound parameters"],
            ["Missing or unusable model", "The ranker falls back to a 0.55 success estimate and heuristic action scores; `GET /api/health` reports `models_ready`; `/api/metrics` answers 503"],
        ], widths=[1.9, 4.4], size=9.5),
        P("Known weaknesses: the tokens have no server-side expiry (the `token_expire_hours` and `secret_key` settings exist in `app/config.py` but no code uses them), a token is "
          "also accepted from a request header, each login adds a new token row, there is no rate limiting or password-reset flow, the transport is plain HTTP on localhost and the session is "
          "demonstration-grade. The application is intended for local use."),
        H2("6.14 Installation and execution"),
        P("`run.bat` reads the ports from `.env` (backend 8407, frontend 5407), creates a `.venv` if needed, installs `requirements.txt`, trains the models if the metrics file is missing, "
          "runs `npm install` in `frontend/` on first use, starts the API (`python -m uvicorn app.main:app`) and the Vite server in two windows and opens the browser; the original "
          "server-rendered interface stays available on port 8407. A `Dockerfile` and `docker-compose.yml` are present in the project folder but were not run for these documents. "
          "Appendix B gives the full guide."),
    ]


def blocks():
    return [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
