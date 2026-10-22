"""Chapter 7: System testing. Counts are read from experiments/test_run.json (written by scripts/collect_env.py)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import c
from . import facts as F


def _t():
    return F.TESTS or {}


def _latency_rows():
    lat = (F.API_LAT or {}).get("endpoints", {})
    rows = []
    for k, v in lat.items():
        rows.append([f"`{k}`", v["n"], f"{v['mean_ms']:.1f}", f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"])
    return rows


def _persona_rows():
    rows = []
    for p in (F.REC or {}).get("per_persona", []):
        rows.append([p["persona"], p["skill"], ", ".join(p["relevant_categories"]), ", ".join(p["top3_hybrid"]), f"{p['hybrid (shipped)']['p@3']:.2f}"])
    return rows


def blocks():
    t = _t()
    py = t.get("pytest", {})
    sm = t.get("smoke", {})
    rs = t.get("responsive", {})
    rec = (F.REC or {}).get("summary", {})
    fb = F.FB or {}
    tr = fb.get("tracked", {})
    lat = (F.API_LAT or {}).get("endpoints", {})
    rec8 = lat.get("GET /api/recommendations?top_n=8", {})
    n_tests = py.get("passed", 0)
    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Testing strategy"),
        P("Testing follows the layers of the system. A small pytest suite drives the FastAPI application in-process and checks the main flow and the input validation; a smoke test "
          "walks the same flow through the running React development server (so it also proves that the proxy reaches every route the interface uses); a browser check loads every "
          "screen at three widths in two themes; and two experiments written for this documentation check that the recommendation engine behaves sensibly on hand-written "
          "learners and that feedback changes the ranking. Each layer was run on the final code and its results are in the tables below."),
        TAB("Test layers and results of the final run", ["Layer", "Tool", "What it checks", "Result"], [
            ["Unit and API", "pytest (FastAPI TestClient)", "Health, home page, register / profile / catalogue / recommendations / interactions / refresh and six read routes, input validation, artefacts present",
             f"{py.get('passed', 0)} of {py.get('collected', 0)} passed in {py.get('seconds', 0):.1f} s"],
            ["System smoke", "`scripts/smoke_test.py` (requests)", "Running servers through the Vite proxy: register, profile, catalogue, ranking, feedback loop, path, insights, metrics, logout, login",
             f"{sm.get('passed', 0)} of {sm.get('checks', 0)} checks passed"],
            ["User interface", "`scripts/check_responsive.py` (Playwright, Chrome)", "Horizontal overflow, console errors, failed requests, drawer and keyboard behaviour at 360, 768 and 1440 px, light and dark",
             "passed" if rs.get("passed") else "failed"],
            ["Recommendation behaviour", "`scripts/run_experiments.py`", "Ten personas against popularity and content-only baselines; a feedback-loop probe", "reported in Section 7.5"],
            ["Latency", "`scripts/measure_api.py`", "Response time of every route on loopback", "reported in Section 7.7"],
        ], widths=[1.1, 1.5, 2.6, 1.1], size=9, align=["l", "l", "l", "c"]),
        H2("7.2 Automated tests (pytest)"),
        P(f"`tests/test_app.py` contains {py.get('collected', 0)} tests and all {n_tests} passed in the final run ({py.get('seconds', 0):.1f} s). They use FastAPI's `TestClient`, a real registered "
          "account and the real trained model bundle, against the project's own SQLite file; each registering test creates a new e-mail address, so tests do not depend on each other."),
        TAB("The automated tests", ["Test", "What it checks"], [
            ["`test_health`", "`GET /api/health` returns 200 and `ok` is true"],
            ["`test_homepage`", "`GET /` returns 200 and the page contains \"LearnPathIQ\""],
            ["`test_auth_profile_recs_interactions`", "Register returns a token; `PUT /api/profile` is accepted; the catalogue has more than five courses; one course detail loads; "
                                                      "`GET /api/recommendations?top_n=5` returns a non-empty list; a quiz interaction is accepted; refresh succeeds; learning-path, insights, activity, history, metrics and fairness each return 200 (or 503 if artefacts were missing)"],
            ["`test_invalid_inputs`", "A malformed registration (bad e-mail, one-letter name, short and mismatching passwords) gives 422; an unknown `event_type` gives 400; an unknown course id gives 404"],
            ["`test_artifacts_load`", "`artifacts/metrics/model_metrics.json` exists"],
        ], widths=[2.2, 4.1], size=9.5),
        P("The suite is deliberately small: it asserts status codes and shapes, not the numeric content of a ranking, and it has no separate unit tests for the individual scoring "
          "functions. Code coverage was not measured. The numeric behaviour of the ranker is covered instead by the persona experiment and the feedback-loop probe of Section 7.5."),
        H2("7.3 System smoke test"),
        P(f"`scripts/smoke_test.py` creates a throw-away account and runs {sm.get('checks', 0)} checks through the React server's proxy (port 5407) and the API (port 8407); all "
          f"{sm.get('passed', 0)} passed. The checks fall into nine groups:"),
        TAB("Smoke-test checks", ["Group", "Checks", "Examples"], [
            ["Servers reachable", "3", "the React app is served; the backend health route; the proxy reaches the API and reports `models_ready`"],
            ["Account and session", "3", "register; duplicate e-mail rejected; the cookie restores the user"],
            ["Profile", "2", "save a profile; read it back"],
            ["Catalogue", "3", "at least 20 courses; filter by category; search for \"python\""],
            ["Ranking and feedback loop", "8", "six ranked courses with explanations; open, start, quiz and complete accepted; a bad event type gives 400; **the score of the interacted course changes**; refresh works"],
            ["Course detail", "2", "match score and explanation for a known course; 404 for an unknown one"],
            ["Activity, history, path, insights", "5", "activity log has at least four events; recommendation history; one to six path steps with a next action; the five action benefits; the success estimate differs from the 0.55 fallback"],
            ["Model transparency", "3", "three models with 2 x 2 confusion matrices; fairness audit present; the ROC plot is served as an image"],
            ["Logout and login", "4", "logout; protected call is 401 afterwards; wrong password is 401; correct password logs in"],
        ], widths=[1.9, 0.7, 3.7], size=9.5, align=["l", "c", "l"]),
        H2("7.4 User-interface and responsive check"),
        P(f"`scripts/check_responsive.py` opens Chrome through Playwright with reduced motion on and visits, for each of three viewports (360 x 740, 768 x 1024 and 1440 x 900 pixels) and each "
          "of the two colour schemes, the five public pages (landing, sign in, register, catalogue, model analytics), registers a new learner through the real form, and visits the six "
          "signed-in pages (dashboard, recommendations, path, insights, activity, profile) and one course-detail page. It fails on any horizontal overflow greater than one pixel, any "
          "console error, any page error and any HTTP status of 400 or more. Below 1024 pixels it also opens the navigation drawer and checks that the Escape key closes it, and at "
          "1440 pixels it checks that the first keyboard stop on the sign-in page is the skip link and that the focused element has a visible outline. "
          f"The run took {rs.get('seconds', 0)} s and ended with: *{(rs.get('tail') or [''])[0]}*"),
        FIG(F.shot_view("20_dashboard_dark.png"), "The dashboard in the dark theme at 1440 x 900 pixels, one of the screens covered by the check", F.shot_w(F.shot_view("20_dashboard_dark.png"), 5.6)),
        P("The check is automated and covers layout, errors and basic keyboard behaviour in one browser (Chrome). It is not an accessibility audit: contrast ratios, screen-reader "
          "behaviour and other browsers were not tested."),
        H2("7.5 Recommendation behaviour"),
        H3("Persona check against two baselines"),
        P("Ten learner personas were written by the authors, each with the course categories that would count as relevant for that learner; the categories were fixed before any "
          "ranking was run. For each persona the 24 courses were ranked three ways: by rating only (popularity), by the TF-IDF content score only, and by the shipped hybrid "
          "score. Precision at 1, 3 and 5 and the mean reciprocal rank (MRR) of the first relevant course were computed. This is a **sanity check on a 24-course catalogue**, not a user study, and "
          "not a measurement of precision and recall against real learner feedback."),
        TAB("Persona check (10 personas, 24 courses)", ["Ranker", "P@1", "P@3", "P@5", "MRR"],
            [[k, f"{v['p@1']:.2f}", f"{v['p@3']:.3f}", f"{v['p@5']:.2f}", f"{v['mrr']:.3f}"] for k, v in rec.items()], widths=[2.6, 0.9, 0.9, 0.9, 0.9], size=10, align=["l", "c", "c", "c", "c"]),
        P("The hybrid ranker is far better than the popularity baseline, but it is **not better than the content-only baseline** on these personas (P@3 0.733 against 0.800, P@5 0.54 against 0.56). "
          "What the extra terms add is behaviour that the content score cannot provide: an adjustment from the learner's own events, a skill-level fit and cold-start-safe defaults. "
          "The drop-one-term ablation is reported in Chapter 8."),
        TAB("The ten personas and the hybrid's top three", ["Persona", "Level", "Relevant categories", "Hybrid top 3", "P@3"], _persona_rows(),
            widths=[1.5, 0.9, 1.6, 1.7, 0.5], size=8.5, align=["l", "l", "l", "l", "c"]),
        H3("Feedback-loop probe"),
        P("To check that feedback changes the ranking in the right direction, a learner with the profile \"python, data science, machine learning\" (Beginner) was ranked, then received six "
          "events (start, quiz, quiz and complete on ML101, a view of DS101 and a dismissal of DA101) and was ranked again."),
        TAB("Effect of six events on the ranking", ["Quantity", "Before", "After"], [
            ["Top three", ", ".join(fb.get("top3_before", [])), ", ".join(fb.get("top3_after", []))],
            ["ML101 score and rank", f"{tr.get('ML101', {}).get('score_before')} (rank {tr.get('ML101', {}).get('rank_before')})", f"{tr.get('ML101', {}).get('score_after')} (rank {tr.get('ML101', {}).get('rank_after')})"],
            ["DS101 score and rank", f"{tr.get('DS101', {}).get('score_before')} (rank {tr.get('DS101', {}).get('rank_before')})", f"{tr.get('DS101', {}).get('score_after')} (rank {tr.get('DS101', {}).get('rank_after')})"],
            ["DA101 (dismissed) score and rank", f"{tr.get('DA101', {}).get('score_before')} (rank {tr.get('DA101', {}).get('rank_before')})", f"{tr.get('DA101', {}).get('score_after')} (rank {tr.get('DA101', {}).get('rank_after')})"],
            ["Estimated success", f"{fb.get('p_success_before')}", f"{fb.get('p_success_after')}"],
            ["Engagement", f"{fb.get('engagement_before', {}).get('label')} ({fb.get('engagement_before', {}).get('score')})", f"{fb.get('engagement_after', {}).get('label')} ({fb.get('engagement_after', {}).get('score')})"],
            ["Suggested action", str(fb.get("best_action_before")), str(fb.get("best_action_after"))],
        ], widths=[2.2, 2.0, 2.1], size=9.5),
        P("The course the learner worked on rose in score and the dismissed course fell one place, as intended. The probe also exposed two weaknesses that Chapter 8 discusses: the estimated "
          "benefit of every action changed sign after only six events, so the suggested action flipped from a quiz to a homepage visit, and the suggested action is the same on every card because it "
          "depends on the learner state only."),
        H2("7.6 Input validation and security checks"),
        TAB("Validation and access-control cases that were run", ["Case", "Expected", "Covered by"], [
            ["Malformed registration (bad e-mail, one-letter name, short and mismatching passwords)", "422", "`test_invalid_inputs`"],
            ["Registration with an e-mail that already exists", "400", "smoke test"],
            ["Unknown interaction event type", "400", "`test_invalid_inputs`, smoke test"],
            ["Unknown course id", "404", "`test_invalid_inputs`, smoke test"],
            ["Protected route after logout", "401", "smoke test"],
            ["Wrong password at login", "401", "smoke test"],
            ["Training artefacts present", "metrics file exists", "`test_artifacts_load`, smoke test"],
        ], widths=[3.5, 1.2, 1.6], size=9.5),
        P("Password hashing, token handling and the cookie attributes were reviewed in the code (Chapter 6) but have **no dedicated automated test**, and no penetration test, "
          "fuzzing or dependency audit was run."),
        H2("7.7 Performance"),
        P("`scripts/measure_api.py` registers one throw-away account on the running backend and times each route over the loopback address 127.0.0.1 (using the address avoids a "
          "2-second IPv6 fallback seen with the name localhost on this machine). Read routes were called 30 times in sequence after three warm-up calls to the recommendations route; the first registration includes "
          "the first password hash and database write."),
        TAB("API latency in milliseconds (loopback, development machine)", ["Route", "n", "Mean", "Median", "p95", "Max"], _latency_rows(),
            widths=[2.7, 0.4, 0.7, 0.8, 0.7, 0.7], size=8.5, align=["l", "c", "c", "c", "c", "c"]),
        FIG(F.fig("fig_latency.png"), "Mean and 95th-percentile latency of the API routes", 5.6),
        P(f"Recommendations for eight courses take about {rec8.get('mean_ms', 0):.0f} ms on average (p95 {rec8.get('p95_ms', 0):.0f} ms), although the TF-IDF matrix is fitted and all 24 courses are "
          "scored on every call without any cache. The figures come from one machine (a 12th-generation Core i5, no GPU), one client and a catalogue of 24 courses; they say nothing about "
          "many simultaneous users or a larger catalogue."),
        H2("7.8 A defect found during testing"),
        P("While the frontend was being verified the success estimate was always exactly 55 % and every action benefit was zero. The cause was that the stored model files had been "
          "saved with a different scikit-learn version than the pinned 1.5.2; predicting failed, and the application's catch-all handlers returned the fallback values "
          "silently. Re-running `scripts/train_pipeline.py` unchanged under the pinned versions restored the model (logistic regression, test AUC 0.6028 as before), and the smoke test gained a check "
          "that the success estimate differs from 0.55. The episode shows the cost of the design choice to fail soft."),
        H2("7.9 Traceability to the objectives"),
        TAB("Objectives and the evidence collected", ["Objective", "Evidence", "Status"], [
            ["1. Learner profiles", "`PUT/GET /api/profile` in the pytest and smoke tests; profile screens in the responsive check", "Met"],
            ["2. Course catalogue", "24 seeded courses; catalogue search and filter in the smoke test", "Met (small, hand-written catalogue)"],
            ["3. Collaborative filtering", "No cross-learner model exists; only a per-learner behavioural boost", "Not implemented"],
            ["4. Content-based filtering", "TF-IDF scoring; persona check P@3 0.800 for the content-only ranking", "Met"],
            ["5. Hybrid recommendation and learning path", "Eight-term score; feedback-loop probe; path steps in the smoke test", "Met (path is ordered by level and score, no prerequisite graph)"],
            ["6. Evaluation with precision, recall and feedback", "Model AUC and F1 on a synthetic test split; persona P@k and MRR; no real learner feedback", "Partly met"],
        ], widths=[1.8, 3.2, 1.3], size=9),
        H2("7.10 What was not tested"),
        B("**Load and concurrency:** latency was measured with sequential requests from one client; no load test was run.",
          "**Real data:** every model result comes from the synthetic generator; the real OULAD data were never used.",
          "**Users:** no user study, no real-feedback precision or recall, no A/B test.",
          "**Security:** no penetration test, no fuzzing, no dependency audit and no automated test of hashing or cookie flags.",
          "**Browsers and assistive technology:** Chrome only; no screen-reader or contrast audit.",
          "**Deployment:** the Dockerfile and compose file were not run; only the local launcher was used.",
          "**Coverage:** line coverage of the Python code was not measured."),
    ]
    return out
