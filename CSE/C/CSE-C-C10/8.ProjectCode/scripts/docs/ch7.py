"""Chapter 7: System Testing."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def latency_rows():
    names = [("health", "GET /api/health"), ("model_metrics", "GET /api/model-metrics"), ("insights", "GET /api/insights"),
             ("predict_k10", "POST /predict, k = 10"), ("predict_k50", "POST /predict, k = 50")]
    rows = []
    for key, label in names:
        r = F.LAT[key]
        rows.append([label, str(r["n"]), f"{r['median_ms']:.1f}", f"{r['mean_ms']:.1f}", f"{r['p95_ms']:.1f}", f"{r['max_ms']:.1f}"])
    return rows


def edge_rows():
    rows = []
    for i, c in enumerate(F.EDGE["cases"], 1):
        rows.append([str(i), c["case"], c["route"], str(c["expected"]), str(c["got"]), "pass" if c["pass"] else "FAIL"])
    return rows


def blocks():
    L = F.LAT
    k10, k50 = L["predict_k10"], L["predict_k50"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    b += [H2("7.1 Testing strategy"),
          P("Testing covers four layers. The functions of the machine-learning layer (dataset loading, preprocessing, embeddings and fusion, balanced retrieval) and the prediction service are tested "
            "in the project's own `pytest` suite. The API as a whole is exercised in-process with the FastAPI test client by the smoke test, which calls every JSON endpoint and the four original pages. "
            "A third script drives deliberately awkward requests (out-of-range values, oversized text, wrong types, tampered tokens) through the same client. Finally, the React screens were used in a real browser "
            "while the documentation screenshots were captured, and latency was measured against a running server."),
          P("All tests check behaviour, not predictive quality. Predictive quality is measured on held-out data with the protocol of Chapter 6 and reported in Chapter 8; a passing test here says nothing about whether a verdict is right. "
            f"The repository had seven `pytest` tests and a 15-check smoke test before this documentation run; `scripts/edge_tests.py` (29 cases) was added, bringing the total to {F.N_TESTS} automated checks, all of which pass."),
          TAB("Test layers and results", ["Layer", "What it covers", "Script", "Result"],
              [["Unit and component", "Dataset, preprocessing, embeddings and fusion, balanced retrieval, prediction and API, original pages", "`pytest tests` (`tests/test_app.py`)", f"{F.N_UNIT} of {F.N_UNIT} passed"],
               ["Integration", "Every JSON endpoint, demo sign-in, validation error, the four original pages", "`scripts/smoke_test.py`", f"{F.N_SMOKE} of {F.N_SMOKE} passed"],
               ["Validation, edge and security", "Range limits, wrong types, oversized text, unknown categories, form route, token handling", "`scripts/edge_tests.py`", f"{F.N_EDGE} of {F.N_EDGE} passed"],
               ["Browser checks", "Responsive widths, light and dark theme, reduced motion, keyboard use, error states", "`scripts/ui_checks.py`", "Passed when the frontend was built; not re-run here"],
               ["Functional walk-through", "All React screens used with a real submission (Section 7.4)", "`scripts/capture_screens.py`", "All 9 screens captured"],
               ["Performance", "Latency of the endpoints against a running server", "`scripts/measure_latency.py`", "Section 7.6"]],
              widths=[1.3, 2.5, 1.7, 1.0], align=["l", "l", "l", "c"], size=9.5)]

    b += [H2("7.2 Unit and component testing"),
          P(f"`tests/test_app.py` contains {F.N_UNIT} tests. They run against the shipped artefacts and small synthetic inputs, so the whole group finishes in 16 to 26 seconds, most of which is loading the embedding model."),
          TAB("The seven pytest tests", ["Test", "What it asserts"],
              [["`test_health`", "`GET /api/health` returns 200 and status `ok`"],
               ["`test_dataset`", "The dataset loader returns more than 200 rows and a `status` column"],
               ["`test_preprocessing`", "`prepare_frame` creates a binary `label`; the fitted preprocessor returns one row per input; a missing funding value is imputed and no NaN remains"],
               ["`test_embeddings_and_fusion`", "Embeddings are 384-dimensional; fusing a 10-column structured block with them gives 394 columns"],
               ["`test_retrieval_balanced`", "`retrieve_similar` with k = 10 returns 10 rows, both classes present, similarity not above 1"],
               ["`test_predict_and_api`", "`POST /predict` returns 200, an outcome of SUCCESS or FAILURE and exactly k = 10 similar startups each with a similarity; invalid input (negative funding, k = 999) is rejected with 400 or 422"],
               ["`test_pages`", "`/`, `/predict`, `/performance` and `/insights` return 200"]],
              widths=[2.0, 4.5], align=["l", "l"], size=9.5)]

    b += [H2("7.3 Integration testing of the API"),
          P(f"`scripts/smoke_test.py` uses the test client, so no port is needed. Its {F.N_SMOKE} checks are listed below; all pass."),
          TAB("Smoke-test checks", ["#", "Check", "Expected"],
              [["1", "`GET /api/health`", "200 and status ok"],
               ["2", "`GET /api/config`", "ks equal to 10, 20, 30, 50; industry list contains Software"],
               ["3", "`GET /api/model-metrics`", "Four models and a best model among them"],
               ["4", "`GET /api/insights`", "Total above 200; success plus failure equals total"],
               ["5", "`GET /api/feature-importance?top=5`", "Five features in descending order of value"],
               ["6", "Login with a wrong password", "401"],
               ["7", "Login with the demo account", "A token is returned"],
               ["8", "`GET /api/auth/me` with the token", "200 and the demo e-mail"],
               ["9", "`GET /api/auth/me` without a token", "401"],
               ["10", "`POST /predict` with a valid payload and k = 20", "200; SUCCESS or FAILURE; 20 similar startups; probabilities sum to 1"],
               ["11", "`POST /predict` with funding -5 and k = 999", "422"],
               ["12-15", "Original pages `/dashboard`, `/predict`, `/performance`, `/insights`", "200 each"]],
              widths=[0.6, 3.2, 2.7], align=["c", "l", "l"], size=9.5),
          P("Check 10 runs the whole inference path: preprocessing, text embedding, fusion, the classifier, balanced retrieval and the explanation builder.")]

    b += [H2("7.4 Functional testing"),
          P("The functional walk-through follows the main use cases of Chapter 5 (sign in, view the dashboard, predict, inspect the evidence, read the performance and insight screens). The interface was driven in Google Chrome by a Playwright script (`scripts/capture_screens.py`) against the running application at 1440 pixels wide in the dark theme; "
            "the screenshots in Chapter 8 are the record of that run. One real submission was used throughout: a software startup in California with USD 2.5 million raised over two rounds, six relationships, three milestones, "
            "venture-capital backing and a round A, and the description \"A subscription analytics platform for small retailers using demand forecasting, with 40 paying stores and growing monthly revenue.\""),
          TAB("Functional scenarios", ["Use case", "Scenario", "Observed result"],
              [["Sign in", "Open the sign-in screen, use the demo-account button, press Sign in", "Dashboard opens with the confirmation \"Signed in as Demo Analyst\""],
               ["View dashboard", "Open the dashboard", "1,400 historical startups (595 successful, 805 failed, 42.5 %), the selected model Logistic Regression with balanced accuracy 0.749 ± 0.025, a data note that the synthetic fallback is in use"],
               ["Predict an outcome", "Fill the form with the submission above, k = 50, press Predict startup success", "SUCCESS, confidence 83.3 %, Lower risk; 25 SUCCESS and 25 FAILURE comparable startups, top similarity 0.580"],
               ["Predict an outcome", "Press Predict with the description empty", "The form shows \"Describe the startup in a few sentences\" and sends nothing (checked in `ui_checks.py`)"],
               ["Inspect evidence", "Scroll the result: explanation bullets, evidence split, comparable-case table", "Five feature contributions with sign, two retrieval statistics, a sortable table of 50 cases over 5 pages"],
               ["Model performance", "Open Model performance", "Comparison table of four models, bar charts, precision-recall scatter, confusion matrix 122.2 / 38.8 / 31.0 / 88.0, retrieval-size and representation studies, top-15 coefficients"],
               ["Startup insights", "Open Startup insights", "Industry success rates, median funding by outcome ($993K vs $592K), correlations, state table"]],
              widths=[1.4, 2.6, 2.5], align=["l", "l", "l"], size=9.5),
          P("The walk-through found no crash. It made visible that the screens describe the synthetic-trained model (Section 7.9, finding 1) and that the displayed confidence is not a calibrated probability (Chapter 8).")]

    b += [H2("7.5 Security, validation and edge-case testing"),
          P(f"`scripts/edge_tests.py` sends {F.N_EDGE} requests with the FastAPI test client and compares the status code with the intended one; all {F.N_EDGE} match. "
            "The cases fall into five groups: payload ranges and types for `POST /predict`, unusual but legal inputs, the form route, the read-only routes and token handling."),
          TAB("The 29 edge, validation and security cases", ["#", "Case", "Route", "Expected", "Got", "Result"], edge_rows(),
              widths=[0.35, 2.6, 1.5, 0.65, 0.5, 0.65], align=["c", "l", "l", "c", "c", "c"], size=8.5),
          P("The Pydantic model rejects values outside the ranges of Chapter 6 (funding up to 1e10, rounds up to 20, relationships up to 200, description up to 2,000 characters, k in 10, 20, 30, 50) with HTTP 422 before any model is called. "
            "Unknown industries and states are accepted because the one-hot encoder ignores unseen categories; an empty description falls back to a text built from the industry name; an empty body runs on the defaults. "
            "The original form route is stricter on the description (an empty one gives 400, as does the React form before it sends anything) and silently replaces an invalid k by the default."),
          P("The demo token is an HMAC-SHA256 signature over the e-mail and an expiry time. A first version of the tampered-token check appended a character after the base64 padding and the token was still accepted, "
            "because the decoder ignores characters after the padding; that was a flaw of the test, not of the signature, and the check was corrected to change one character of the signature, after which the token is rejected (401)."),
          P("These checks cover input validation, range limits and token handling. They do not amount to a security audit: the demo sign-in protects only the React screens, `POST /predict` and the JSON read endpoints are open on localhost, "
            "the model files are loaded with `joblib` (so they must come from a trusted source), no penetration test was run and no rate limiting exists.")]

    b += [H2("7.6 Performance testing"),
          P(f"`scripts/measure_latency.py` calls a running uvicorn server (127.0.0.1, port 8410, model already loaded). It addresses 127.0.0.1 rather than `localhost`, because name resolution adds about two seconds per call on the test machine. "
            f"Hardware: {F.HARDWARE}. The PC was otherwise idle."),
          TAB("Endpoint latency in milliseconds", ["Endpoint", "Requests", "Median", "Mean", "p95", "Max"], latency_rows(), widths=[2.2, 0.8, 0.8, 0.8, 0.8, 0.8], align=["l"] + ["c"] * 5, size=9.5),
          P(f"The read-only endpoints answer in 3 to 15 ms at the median. A prediction costs {k10['median_ms']:.0f} ms at the median for k = 10 and {k50['median_ms']:.0f} ms for k = 50, because every request embeds the description "
            f"with MiniLM on the CPU and compares the fused vector with all 1,400 training vectors. The tail is heavier: p95 is {k10['p95_ms']:.0f} ms and {k50['p95_ms']:.0f} ms and the slowest request took {k50['max_ms']:.0f} ms, "
            f"so a user will occasionally wait about half a second. The first request after the server starts is much slower: the first call of `edge_tests.py` took 11.3 s because the embedding model and the artefacts are loaded on demand."),
          FIG(F.fig("f12_latency.png"), "Median and 95th-percentile latency of the endpoints (milliseconds).", 4.6),
          P("Not measured: concurrent requests, memory use, a larger training set (the retrieval cost grows linearly with the number of stored vectors), start-up time of the whole application, any GPU run. "
            "Training cost is small: the whole real-data study of Chapter 8 (five models, imbalance, threshold, size and transfer studies) ran in "
            f"{F.R['runtime_seconds']:.0f} s and the extra studies in {F.X['runtime_seconds']:.0f} s on this CPU.")]

    b += [H2("7.7 User interface testing"),
          P("The React interface was built with Vite and its nine captured states (landing in two themes, sign-in, dashboard, empty and filled form, result, performance, insights) were produced by scripted browser sessions without a crash. "
            "`scripts/ui_checks.py` checks 360, 768 and 1440 pixel widths, the light and dark themes, reduced-motion preference, keyboard navigation and error states; it passed when the frontend was built and was not re-run for this documentation. "
            "For this run only 1440 x 900 was captured."),
          P("Only Chrome was used. There are no automated component tests for the React code, and no accessibility audit was made.")]

    b += [H2("7.8 User acceptance testing"),
          P("No user acceptance test was performed. The project team used the application while building it, but no group of founders, investors or students tried it and no questionnaire was used, "
            "so nothing is claimed about whether users find the estimates useful or understandable. The functional walk-through of Section 7.4 stands in for it as a check that the intended tasks can be completed; it measures neither usability nor trust.")]

    b += [H2("7.9 Defects and limitations found by testing"),
          P("Testing with real data and with awkward requests exposed the behaviours below. They are reported as findings; no product code was changed for this documentation."),
          TAB("Findings", ["#", "Finding", "Evidence", "Consequence"],
              [["1", "The shipped model was trained on synthetic data", "Dashboard data note; `models/metadata.json` has `synthetic_fallback` true; 1,400 generated rows", "Every score the screens show (0.749 balanced accuracy) is a pipeline check, not real-world evidence"],
               ["2", "The synthetic description text leaks the label", "Text-only model scores 0.599 balanced accuracy on templates that differ by class", "The fused 0.749 must not be read as proof that text helps in reality"],
               ["3", "Displayed confidence is not calibrated", "On the real table, Logistic Regression with balanced class weights predicts about 0.25 in a bin where 0.44 of the startups succeed (Chapter 8)", "\"Confidence 83.3 %\" is the model's score, not a frequency"],
               ["4", "Open endpoints", "`POST /predict` and the JSON reads need no token", "Acceptable for a local demonstration; not for a shared deployment"],
               ["5", "JSON and form routes differ", "JSON rejects k = 7 (422); the form silently uses the default; JSON accepts an empty description, the form refuses it", "Same input can give different outcomes on the two routes"],
               ["6", "Slow first request and a heavy latency tail", "11.3 s first call; p95 about 0.6 s", "Warm the model at start-up before a demonstration"],
               ["8", "The explanation ranks features by coefficient size", "`predictor.py` orders by |coefficient| and labels the sign from coefficient x scaled value; an absent flag (value 0) is listed as \"supports FAILURE\" (has_roundC in the sample result)", "The driver list describes the model, not the specific start-up; a contribution-based ranking would fix it"],
               ["7", "ROC-AUC of the shipped fused model was not recorded", "`evaluation_results.json` holds accuracy, balanced accuracy, precision, recall, F1 only", "ROC-AUC is reported from the real-data study instead (Chapter 8)"]],
              widths=[0.35, 1.7, 2.6, 1.85], align=["c", "l", "l", "l"], size=9)]

    b += [H2("7.10 Limits of the testing done"),
          B("The tests establish that the code behaves as specified for the inputs tried; they do not establish that the estimates are correct. Correctness on real startups is measured in Chapter 8 and is moderate.",
            "There is no load, stress or concurrency test and no multi-user test; latency figures are for one client on one idle machine and vary between runs.",
            "No cross-browser, mobile, accessibility, security-audit or user-acceptance testing was carried out (Sections 7.5, 7.7 and 7.8).",
            f"The {F.N_TESTS} automated checks run against the shipped synthetic-trained model; none re-runs the real-data experiments, which are scripts whose output files are inspected by hand.",
            "Tests were run on one machine with one set of package versions; the earlier failure to load model files saved with newer library versions (recorded in the README) is the kind of fault they would only find on a differing installation.")]
    return b
