"""Chapter 7: System testing. Counts come from artifacts/measured.json; edge-case tables come from
artifacts/edge_cases.json (written by scripts/edge_cases.py against the running API)."""

import json
import os

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F


def _edge():
    p = os.path.join(F.ART, "edge_cases.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"cases": [], "health_after": {}}


def _rows(cases, group):
    out = []
    for c in cases:
        if c["group"] == group:
            res = c["message"] or c["outcome"] or "-"
            out.append([c["id"], c["case"], str(c["status"]), res if len(res) <= 120 else res[:117] + "..."])
    return out


def blocks():
    meas = F.MEAS or {}
    py = meas.get("pytest", {})
    sm = meas.get("smoke_test", {})
    lat = meas.get("api_latency_ms_127_0_0_1", {})
    env = meas.get("environment", {})
    E = _edge()
    cases = E["cases"]
    n_cases = len([c for c in cases if c["id"].startswith("E")])
    n_get = len([c for c in cases if c["id"].startswith("G")])
    rejected = len([c for c in cases if c["id"].startswith("E") and c["status"] == 400])
    accepted = len([c for c in cases if c["id"].startswith("E") and c["status"] == 200])
    health = E.get("health_after", {}).get("body", {})
    pr = lat.get("POST /api/predict", {})
    wi = lat.get("POST /api/whatif", {})
    px = lat.get("POST /api/predict via port 5409 proxy", {})
    pm = F.RM["predict_profile_ms"]
    RM_MED, RM_P95, RM_N = pm["median"], pm["p95"], pm["n"]

    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Testing strategy"),
        P("FinSight AI is a small system whose value rests on three properties: the model returns different, plausible answers for different people; invalid input is refused before it reaches the model; "
          "and the explanations and forecast shown on screen are the ones the code produced. The testing strategy follows from this. Small deterministic pieces (feature engineering, the preprocessing pipeline) "
          "are covered by unit tests; the Flask application is exercised through its test client with the real trained model; the running stack is checked end to end by a smoke test that talks to the live servers; "
          "and hostile or malformed inputs are probed against the live API by a dedicated script written for this chapter."),
        P(f"All results in this chapter were produced on 2026-10-22 on the development machine ({env.get('cpu', '')}, {env.get('ram_gb', '')} GB RAM, {env.get('os', '')}), using Python {env.get('python', '')}, "
          f"scikit-learn {env.get('scikit-learn', '')}, XGBoost {env.get('xgboost', '')} and Flask {env.get('flask', '')}. The persisted model files were written by an older scikit-learn and XGBoost, which emit "
          "version warnings when loaded; the model nevertheless reproduces the stored metrics exactly (Section 8.2), so the warnings were treated as cosmetic and noted here for completeness."),
        TAB("Test layers used", ["Layer", "Tool", "What it checks", "Result"], [
            ["Unit", "pytest", "Derived-feature arithmetic, missing-value handling by the preprocessing pipeline", f"{py.get('files', {}).get('tests/test_features.py', 0)} tests passed"],
            ["Integration and functional", "pytest + Flask test client", "All pages, validation, prediction through the real model, JSON API, what-if, artifact files", f"{py.get('files', {}).get('tests/test_app.py', 0)} tests passed"],
            ["System smoke", "scripts/smoke_test.py (requests)", "The running API on port 8409 and the Vite proxy on port 5409: every JSON route, artifact images, predictions, validation, what-if, SPA deep links", f"{sm.get('passed', 0)}/{sm.get('total', 0)} checks passed"],
            ["Edge and security probe", "scripts/edge_cases.py (requests)", f"{n_cases} malformed, boundary and hostile requests to /api/predict and /api/whatif and {n_get} path probes", "Section 7.5 and 7.6"],
            ["Performance", "Python timing loops", "Median and 95th-percentile response time of five routes, 40 calls each", "Section 7.7"],
        ], widths=[1.2, 1.5, 2.8, 1.0], size=9.5, align=["l", "l", "l", "c"]),
        P(f"The automated suite contains **{py.get('passed', 0)} pytest tests**; all {py.get('passed', 0)} passed in {py.get('seconds', 0)} seconds, with {py.get('failed', 0)} failures."),

        H2("7.2 Unit testing"),
        P("Unit tests live in `tests/test_features.py` and target `scripts/feature_engineering.py`, the module that turns a raw record into the 26-column frame the model expects. Because the same functions run at "
          "training time and at prediction time, a mistake here would silently corrupt every prediction, so the arithmetic is pinned down with exact expectations."),
        TAB("Unit tests", ["Test", "Input", "What it asserts"], [
            ["`test_derived_features_computable`", "One complete record: age 40, Private, Bachelors, married, Exec-managerial, gains 5,000, 45 hours, United-States",
             "net-capital equals 5,000; region is 'North America'; education-tier is 'Tertiary'; age-band is '36-50'; employment-stability is 'Stable-private'"],
            ["`test_missing_values_handled_by_pipeline`", "Two records, the first with age missing and '?' in workclass, marital status, occupation and country",
             "`clean_frame` and `add_derived_features` run, the scaled preprocessor fits and transforms, the output has two rows and contains no missing value"],
        ], widths=[2.1, 2.2, 2.2], size=9.5, align=["l", "l", "l"]),
        P("The second test matters because the real Adult data use the character '?' for missing values (2,799 workclass, 2,809 occupation and 857 country entries in the raw file) and a user may also leave a "
          "field empty; the test confirms that the imputation steps inside the Pipeline absorb both without error."),

        H2("7.3 Integration testing"),
        P("`tests/test_app.py` builds the real Flask application with `create_app()`, so the trained model, the SHAP explainer and the forecast artifact are loaded exactly as in production. It contains seven tests."),
        TAB("Integration and functional tests", ["Test", "What it asserts"], [
            ["`test_health`", "GET /health returns 200 and a status of 'ok' or 'degraded'"],
            ["`test_pages_load`", "The seven server-rendered pages (/, /assess, /explain, /forecast, /whatif, /performance, /about) all return 200"],
            ["`test_valid_prediction_not_hardcoded`", "A valid assessment returns the 'Financial-strength score' page; a second, very different profile (age 60, Doctorate, gains 50,000, 60 hours) produces a different page, proving the output is not fixed text"],
            ["`test_invalid_input_rejected`", "An empty form, a negative age and an unknown workclass each return 400"],
            ["`test_api_predict_and_forecast`", "POST /api/predict returns ok with a probability between 0 and 1 and live SHAP available; GET /api/forecast reports available data with 12 forecast points"],
            ["`test_whatif_changes_score`", "A what-if post with scenario gains 80,000 and hours 50 returns 200 and the 'Comparison' section"],
            ["`test_artifacts_present_and_real`", "Four models in the comparison file with a valid best model; more than five SHAP features; 12 forecast points over more than 100 history points"],
        ], widths=[2.4, 4.1], size=9.5, align=["l", "l"]),
        P("The smoke test adds the layer the unit tests cannot reach: the processes that actually run. It is described in the next section."),

        H2("7.4 Functional testing"),
        P(f"`scripts/smoke_test.py` runs {sm.get('total', 0)} checks against the live servers. The same 16 API checks are run twice, once directly against Flask on port 8409 and once through the Vite proxy on port 5409 "
          "(the path the browser uses), and three more checks confirm that the single-page application is served at /, /app and the deep link /app/forecast."),
        TAB("Smoke-test checks (run against both ports)", ["Group", "Checks", "What is verified"], [
            ["Service health", "1", "/health reports a loaded model"],
            ["Read-only JSON routes", "5", "/api/options lists 16 education levels and numeric limits; /api/dashboard has ROC-AUC and five top SHAP drivers; /api/explain; /api/performance has four models; /api/forecast has 12 points"],
            ["Artifact images", "4", "confusion_matrix.png, roc_curve.png, shap_bar.png and shap_beeswarm.png are served as image/png"],
            ["Prediction", "3", "A valid profile returns a probability and live SHAP; a very different profile gives a different probability; age -5 returns 400 with messages"],
            ["What-if", "3", "Gains 80,000 and hours 50 produce a comparison with two changed fields; a request with no change returns 400; hours 500 returns 400"],
            ["Single-page app (port 5409 only)", "3", "/, /app and /app/forecast each return the application shell"],
        ], widths=[1.8, 0.7, 4.0], size=9.5, align=["l", "c", "l"]),
        P(f"All {sm.get('passed', 0)} of {sm.get('total', 0)} checks passed. Functional behaviour of the interface was additionally exercised by the browser walk-through in `scripts/capture_screens.py`, which logs in with the "
          "sample account, fills the assessment form, analyses a profile, runs a what-if comparison and visits every screen, producing the screenshots of Chapter 8; "
          "a further script, `scripts/capture_extra_screens.py`, produced the validation-error, Established-profile and Developing-profile captures. These walks confirm that the screens render with real model output "
          "but they are not assertion-based tests."),

        H2("7.5 Security testing"),
        P("FinSight AI stores no personal data and has no real authentication, so its security surface is small: a JSON API that accepts user input, a route that serves four image files, and, on the original Flask pages only, a session cookie that carries the what-if "
          "baseline. This section records what was actually tested."),
        P(f"**Input handling.** The validation module checks every field against an allow-list or a numeric range before any model code runs. {n_cases} requests were sent to the live API; "
          f"{rejected} were refused with HTTP 400 and {accepted} were accepted, each accepted case being a valid or boundary input or an ignored extra field. After the whole probe the service still answered "
          f"/health with status '{health.get('status', '')}' and the model loaded, so none of the inputs crashed or degraded it."),
        TAB("Hostile and malformed input (POST /api/predict)", ["ID", "Case", "HTTP", "Response"], _rows(cases, "Hostile input") + _rows(cases, "Allowed values"),
            widths=[0.5, 2.5, 0.5, 3.0], size=9, align=["c", "l", "c", "l"]),
        P("Script text and SQL-style text in a categorical field are rejected because they are not in the allowed set, so they are never echoed into a page or passed to any query (there is no database to query). "
          "An unknown extra field (`is_admin`) is silently ignored: the validator copies only the twelve known keys, so the request cannot smuggle extra attributes into the model frame. "
          "A 10,000-character string is rejected by the same allow-list check."),
        TAB("File-access probes (GET)", ["ID", "Case", "HTTP", "Content type"], _rows(cases, "Path probes"), widths=[0.5, 3.1, 0.6, 2.3], size=9, align=["c", "l", "c", "l"]),
        P("The artifact route serves only the four image names on its allow-list. Requests for a JSON artifact, the model pickle (directly and with an encoded `..` traversal) and `.env` all return 404; "
          "only the allowed image returns 200."),
        P("**What this does not establish.** This is a black-box probe of one input route and one file route, not a penetration test. Authentication was not tested because the sample login is a browser-only demo gate "
          "(`demo@finsight.ai` / `finsight123`, stored in client code) and gives no protection to the API, which is open on the local machine. The Flask secret key defaults to a development value when "
          "`FINSIGHT_SECRET_KEY` is not set, so session cookies are not trustworthy in a shared deployment. Cross-site scripting through the React interface was not tested in a browser; the "
          "interface renders only server-validated values and React escapes text by default, but that is a property of the framework and was not verified here. These are listed again as limitations in Chapter 8."),

        H2("7.6 Validation and edge cases"),
        P("The edge-case script `scripts/edge_cases.py` sends each case below to the running API and records the real status and message; the tables are generated from `artifacts/edge_cases.json`, so they cannot drift from what the "
          "server did. The first table covers missing and malformed requests."),
        TAB("Missing and malformed requests (POST /api/predict)", ["ID", "Case", "HTTP", "Response"], _rows(cases, "Required fields"),
            widths=[0.5, 2.3, 0.5, 3.2], size=9, align=["c", "l", "c", "l"]),
        P("An empty body, a plain-text body and truncated JSON all return the same list of 'is required' messages. This is safe but slightly misleading: the route reads the body with `get_json(silent=True)` and treats anything "
          "that is not valid JSON as an empty object, so the caller is told every field is missing instead of being told the body was not JSON. It is recorded as a minor usability finding, not fixed, because it affects "
          "no valid client."),
        TAB("Numeric boundaries and ranges (POST /api/predict)", ["ID", "Case", "HTTP", "Response"], _rows(cases, "Numeric range"),
            widths=[0.5, 2.5, 0.5, 3.0], size=9, align=["c", "l", "c", "l"]),
        P("Every value one step outside its range is refused with a message naming the field and the permitted range, and every value on the boundary is accepted: ages 16 and 100, and investment gains of exactly 1,000,000. "
          "The boundary results are worth reading as predictions: a 16-year-old and a 100-year-old with the same other attributes score as Emerging with a very low strength score, while gains of 1,000,000 push the score to the "
          "Established band. Because the training data contain very few such rows, these boundary predictions are extrapolations; they show that the system does not crash at the limits, not that its scores there are reliable."),
        TAB("What-if scenarios (POST /api/whatif)", ["ID", "Case", "HTTP", "Response"], _rows(cases, "Scenario"),
            widths=[0.5, 2.5, 0.5, 3.0], size=9, align=["c", "l", "c", "l"]),
        P("A what-if request with no scenario field returns 400 and a clear message, and every out-of-range scenario value is refused. Two outcomes deserve comment. A scenario that sets hours to the baseline value (40) "
          "is accepted and returns a change of 0.00 percentage points: the rule is 'at least one scenario field must be filled in', not 'at least one must differ'. And the extreme scenario of gains 1,000,000 changes the score by "
          "close to 100 points, the same extrapolation effect discussed above."),

        H2("7.7 Performance testing"),
        P(f"Response times were measured on the development machine against 127.0.0.1 (using the loopback address avoids a two-second IPv6 fallback delay seen on this machine with the name 'localhost'). Each route was called 40 times "
          f"in sequence by one client, so these are single-user latencies and not capacity figures."),
        TAB("API response time (milliseconds, 40 calls each)", ["Route", "Median", "95th percentile"],
            [[k, f"{v['median']:.1f}", f"{v['p95']:.1f}"] for k, v in lat.items() if isinstance(v, dict)], widths=[3.6, 1.2, 1.7], size=10, align=["l", "c", "c"]),
        FIG(F.fig("api_latency.png"), "Median and 95th-percentile response time of the API routes", 5.4),
        P(f"A prediction, which includes feature engineering, XGBoost inference and a live SHAP explanation, takes a median of {pr.get('median', 0):.1f} ms and 95 percent of calls finish within {pr.get('p95', 0):.1f} ms. "
          f"A what-if request runs the prediction twice and takes {wi.get('median', 0):.1f} ms at the median, about double, as expected. Read-only routes that return a stored JSON artifact take under 10 ms at the median. "
          f"Going through the Vite proxy adds little ({px.get('median', 0):.1f} ms median for a prediction). In-process, `predict_profile` alone has a median of {RM_MED} ms and a 95th percentile of {RM_P95} ms ({RM_N} calls), so most of the "
          "HTTP time is the model and SHAP, not the web layer."),
        P("All of these are comfortably interactive for a single user. They say nothing about behaviour under concurrent load, which was not measured."),

        H2("7.8 User acceptance"),
        P("No formal user-acceptance test with outside participants was carried out. What exists is the project team's own acceptance walk-through: the team logged in with the sample account, entered several profiles of different kinds "
          "(Section 8.4), compared a baseline and a scenario, read the explanations, and checked the forecast and performance screens against the files in `artifacts/`. The criteria applied were those of the objectives in "
          "Chapter 1: the screen shows a profile, a risk band, the reasons, a forecast and the model's measured performance, in plain language, with a disclaimer on every analysis. All of these were satisfied, "
          "but a walk-through by the people who built the system is evidence that the features work, not evidence that outsiders find them clear."),
        P("Two usability observations came out of the walk-through and are reported as they are. The validation banner for a rejected assessment says 'Please fix the highlighted fields and try again' and marks the field in red "
          "(see the validation-error screen in Chapter 8), which is adequate for a single bad field. And the extreme what-if scores in the 90s show how easily a non-expert could over-read a scenario; the interface labels every such result as a model "
          "simulation, not a causal prediction, and that label is the only protection."),

        H2("7.9 Limits of the testing done"),
        P("The testing above supports the claim that the system works as designed on the machine it was built on. It does not support stronger claims, and the following were not done:"),
        B("**No load or concurrency test.** All timings are single-user. Flask is run with its development server, which is not designed for concurrent production traffic.",
          "**No penetration test or dependency audit.** The probe in Section 7.5 is a black-box check of two routes. Authentication, session handling under attack and cross-site scripting were not tested.",
          "**No formal user-acceptance study.** There were no outside participants and no questionnaire.",
          "**No browser or device matrix.** The only browser captures are the 1440 x 900 screenshots taken with Chrome through Playwright. Behaviour at phone or tablet widths, in other browsers and with assistive technology was not tested.",
          "**No front-end unit tests.** The React code has no component tests; it is checked only through the browser walk-throughs and the smoke test of what the server returns.",
          "**No model-regression test against new data.** The tests check that the model returns plausible, input-dependent output and that the stored artifacts are internally consistent; they do not check predictive accuracy, which is evaluated separately in Chapter 8 on a held-out split.",
          "**No test of the training script's failure paths** (for example a failed download, which falls back to synthetic data), and no test run on any other operating system."),
        P("These gaps are acceptable for a final-year prototype whose purpose is to demonstrate an explainable pipeline, and they are the first items to address before any wider use."),
    ]
    return out
