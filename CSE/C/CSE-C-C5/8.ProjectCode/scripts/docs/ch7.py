"""Chapter 7: System Testing."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def _d(i):
    """Detail string recorded by scripts/edge_tests.py for check number i."""
    return F.TEST_CHECKS[i]["detail"]


def _ok(i):
    return "Pass" if F.TEST_CHECKS[i]["passed"] else "FAIL"


def _grp(g):
    a, b = F.TEST_SUMMARY["by_group"][g]
    return f"{a} of {b}"


def perf_rows():
    return [F.perf_row(lbl, key) for lbl, key in (
        ("GET /api/health", "GET /api/health"), ("GET /api/metrics", "GET /api/metrics"), ("GET /api/stats", "GET /api/stats"),
        ("POST /api/predict", "POST /api/predict"), ("POST /api/recruiter/shortlist", "POST /api/recruiter/shortlist"),
        ("POST /api/recommend", "POST /api/recommend"))]


def blocks():
    S = F.TEST_SUMMARY
    L = F.LAT_PREDICT
    rc = F.REC["recommend_latency_s"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]
    b += [H2("7.1 Testing strategy"),
          P("Testing covers five layers: small functions of the core (`src/`) are tested directly; every API endpoint is called over HTTP against the running FastAPI server; the main user-facing behaviours are "
            "checked as functional cases; invalid and hostile inputs are sent to the API; and response times are measured. All checks are scripts in the repository and can be re-run with one command "
            "(`scripts/edge_tests.py` and `scripts/smoke_test.py`, with the backend running on port 8405). Before this documentation work the project contained only the smoke test; the 46 checks of "
            "`edge_tests.py` were written for it. They test behaviour, not prediction quality: prediction quality is measured separately on held-out data (Chapter 8)."),
          P("A guiding choice was to *record* what the system does, and not only to assert what we hoped it would do. Where the behaviour is a limitation rather than a requirement (for example an unknown branch name "
            "being accepted), the check is recorded as an observation and is listed in Section 7.9 and in the limitations of Chapter 9."),
          TAB("Test layers and results", ["Layer", "What it covers", "How", "Result"],
              [["Unit", "Tier tolerance, feature matrix, company table, determinism, monotonic behaviour, recommender filters", "`scripts/edge_tests.py`, direct import of `src/`", _grp("unit") + " pass"],
               ["Integration", "Every GET endpoint, the three plot images, counts of companies and students", "Live HTTP calls to 127.0.0.1:8405", _grp("integration") + " pass"],
               ["Functional", "Prediction of a strong and a weak profile, recommendation, location preference, recruiter shortlist", "Live HTTP calls", _grp("functional") + " pass"],
               ["Validation and edge cases", "Out-of-range and wrongly typed fields, missing fields, boundary profiles, unknown values, empty shortlists", "Live HTTP calls", _grp("validation") + " pass"],
               ["Security", "Injection-style strings, path traversal, CORS, oversized input, undefined routes", "Live HTTP calls", _grp("security") + " pass"],
               ["End-to-end smoke test", "Every endpoint the React front end calls, with success and failure cases", "`scripts/smoke_test.py`", f"{F.SMOKE_TOTAL} of {F.SMOKE_TOTAL} checks pass"],
               ["Performance", "Response times of six endpoints; latency of the model call (Section 7.8)", "`scripts/edge_tests.py`", "Measured"]],
              widths=[1.2, 2.6, 1.7, 1.1], align=["l", "l", "l", "c"], size=9),
          P(f"In total **{S['passed']} of {S['total']} checks pass and {S['failed']} fail** in `edge_tests.py`, and **{F.SMOKE_TOTAL} of {F.SMOKE_TOTAL}** smoke-test checks pass. No failure was found, so no defect list is given; "
            "the observed limitations are collected instead in Section 7.9.")]

    b += [H2("7.2 Unit testing"),
          P("The unit checks import the real modules and use the real trained models; no mocks are used, because the behaviour under test (probability from a pickled model) cannot be separated from the model. "
            "They verify the contracts that the rest of the system relies on: the feature matrix has a fixed shape, predictions are deterministic and bounded, and the probability moves in the direction the domain expects."),
          TAB("Unit test cases (scripts/edge_tests.py)", ["ID", "Test", "Input", "Expected result", "Observed", "Result"],
              [["U1", "Tier tolerance", "`delta_max_cgpa(1), (2), (3)`", "0.6, 1.0, 1.5", "0.6, 1.0, 1.5", _ok(0)],
               ["U2", "Feature matrix", "`build_features` on 25 rows with the saved encoders", "Shape (25, 24), no NaN", _d(1), _ok(1)],
               ["U3", "Company table", "`companies.csv`", "30 rows; tiers {1, 2, 3}", "30 rows; tiers {1, 2, 3}", _ok(2)],
               ["U4", "Determinism", "`predict_for` twice, same profile, Infosys SDE", "Equal values in [0, 1]", f"both {_d(3)}", _ok(3)],
               ["U5", "Effect of CGPA", "CGPA 6.0 then 9.0, same profile otherwise, Infosys", "Probability rises", _d(4), _ok(4)],
               ["U6", "Effect of backlogs", "0 then 4 backlogs, Infosys", "Probability falls", _d(5), _ok(5)],
               ["U7", "Weak profile at a dream company", "CGPA 7.0, aptitude 60, technical 60, Google", "Probability below 0.5", _d(6), _ok(6)],
               ["U8", "Recommender output size and order", "`recommend(..., top_k=5)`, CGPA 7.2, 3 backlogs, target Google", "At most 5 items, sorted by score", f"{_d(7)} items, sorted", _ok(7)],
               ["U9", "Tier-1 exclusion", "Same call with 3 backlogs", "No Tier-1 company in the list", _d(8), _ok(8)],
               ["U10", "CGPA feasibility filter", "Same call, CGPA 7.2", "Every pick within the tier tolerance of its cutoff", "All picks within tolerance", _ok(9)]],
              widths=[0.4, 1.2, 1.8, 1.3, 1.1, 0.5], align=["c", "l", "l", "l", "l", "c"], size=8),
          P("U5 and U6 show a small effect because the test profile is strong and Infosys has a low cutoff, so the probability is near its ceiling; the direction is what is asserted.")]

    b += [H2("7.3 Integration testing"),
          P("Integration checks call the running FastAPI application over HTTP on 127.0.0.1 (the default host name `localhost` adds about two seconds per call on this machine because of an IPv6 fall-back, so it "
            "was not used for timing). They verify that the API, the core modules, the data files and the model files work together."),
          TAB("Integration test cases", ["ID", "Test", "Input", "Expected result", "Result"],
              [["I1", "Health", "GET /api/health", "200; `models_ready` is true", _ok(10)],
               ["I2", "Meta", "GET /api/meta", "30 company names and 6 branches", _ok(11)],
               ["I3", "Companies", "GET /api/companies", "30 rows with cutoffs, package, location", _ok(12)],
               ["I4", "Metrics", "GET /api/metrics", "9 models with 5 metrics each, 9-fold CV and Brier score", _ok(13)],
               ["I5", "Statistics", "GET /api/stats", "3,000 students, placed rate, per-branch rates", _ok(14)],
               ["I6", "Probability histogram", "GET /api/plots/prob_hist", "200 and a PNG signature", _ok(15)],
               ["I7", "PCA plot", "GET /api/plots/pca", "200 and a PNG signature", _ok(16)],
               ["I8", "SHAP plot", "GET /api/plots/shap", "200 and a PNG signature", _ok(17)]],
              widths=[0.4, 1.4, 1.9, 2.3, 0.6], align=["c", "l", "l", "l", "c"], size=8.5)]

    b += [H2("7.4 Functional testing"),
          P("Functional checks follow what a user does: ask whether a student is ready, ask for alternatives, and shortlist candidates. The expected results come from the domain (a strong student at a Tier-3 company "
            "should be ready; a weak student at a Tier-1 company should not) and from the documented rules of `src/recommend.py`."),
          TAB("Functional test cases", ["ID", "Test", "Input", "Expected result", "Observed", "Result"],
              [["F1", "Strong profile", "CGPA 8.4, aptitude 82, technical 84, 1 internship; Infosys, SDE", "PLACEMENT READY", f"probability {_d(18)}", _ok(18)],
               ["F2", "Weak profile", "CGPA 6.2, aptitude 50, technical 45, no internship; Google", "NEEDS IMPROVEMENT with at least 3 tips", f"probability {_d(19)}", _ok(19)],
               ["F3", "Recommendation", "CGPA 7.2, aptitude 65, technical 65; target Google SDE; location Hyderabad", "5 hybrid options and a company-only list", _d(20), _ok(20)],
               ["F4", "Role-only list at an infeasible target", "Same request", "Observed behaviour, not a requirement", _d(21) + " (Google fails the CGPA filter)", _ok(21)],
               ["F5", "Location preference", "Same request, location Hyderabad", "At least one Hyderabad option in the top 5", "At least one Hyderabad option", _ok(22)],
               ["F6", "Recruiter shortlist", "CGPA >= 8.5, aptitude >= 70, CSE", "At most 50 rows, all CSE, sorted by CGPA", f"{_d(23)} matches in total", _ok(23)]],
              widths=[0.4, 1.0, 1.8, 1.4, 1.2, 0.5], align=["c", "l", "l", "l", "l", "c"], size=8),
          P("F4: when the target company is out of reach the role-only strategy returns nothing, because the filter removes the company before roles are tried; the hybrid and company-only lists still work.")]

    b += [H2("7.5 Validation and edge cases"),
          P("The API validates every field with Pydantic ranges (CGPA 0 to 10, scores 0 to 100, counts 0 to 20). Boundary values are accepted and values outside the range are refused with HTTP 422; an unknown company is refused with 404."),
          TAB("Validation and edge-case test cases", ["ID", "Test", "Input", "Expected result", "Observed", "Result"],
              [["V1", "CGPA above range", "`cgpa` = 14", "422", _d(24), _ok(24)],
               ["V2", "Negative score", "`aptitude` = -5", "422", _d(25), _ok(25)],
               ["V3", "Wrong type", "`cgpa` = \"abc\"", "422", _d(26), _ok(26)],
               ["V4", "Missing field", "no `target_company`", "422", _d(27), _ok(27)],
               ["V5", "Unknown company", "`Nope Inc`", "404", _d(28), _ok(28)],
               ["V6", "Count above range", "`backlogs` = 99", "422", _d(29), _ok(29)],
               ["V7", "All-zero profile", "every score and count 0; Infosys", "Accepted; probability below 0.5", f"accepted; {_d(30)}", _ok(30)],
               ["V8", "All-maximum profile", "CGPA 10, all scores 100, 20 projects, 20 internships; Google", "Accepted; probability above 0.5", f"accepted; {_d(31)}", _ok(31)],
               ["V9", "Unknown branch", "`branch` = ROBOTICS", "Observation only", _d(32), _ok(32)],
               ["V10", "Unknown role", "`target_role` = Astronaut", "Observation only", _d(33), _ok(33)],
               ["V11", "Impossible shortlist filter", "CGPA >= 10, aptitude >= 100", "200 and an empty list", "200, empty list", _ok(34)],
               ["V12", "Unknown shortlist branch", "branch XYZ", "0 matches", "0 matches", _ok(35)],
               ["V13", "Shortlist CGPA above range", "`min_cgpa` = 11", "422", "422", _ok(36)]],
              widths=[0.4, 1.2, 1.7, 1.3, 1.3, 0.5], align=["c", "l", "l", "l", "l", "c"], size=8),
          P("V9 and V10 are the weaknesses of the validation layer: branch and role are free strings, and an unseen value is accepted and given frequency 0 (limitation L8). V8 shows that even a perfect profile reaches only about 0.80 at Google because the Tier-1 penalty is built into the data.")]

    b += [H2("7.6 Security testing"),
          P("The application has no login, no database and no file upload, so the attack surface is small: the JSON body of three POST endpoints, the `name` path parameter of the plot endpoint and the browser origin. "
            "The checks send hostile values to these and confirm that nothing is executed, echoed or read from the disk."),
          TAB("Security test cases", ["ID", "Test", "Input", "Expected result", "Result"],
              [["S1", "SQL-injection-style value", "company = `'; DROP TABLE students;--`", "404; nothing executed (there is no database)", _ok(37)],
               ["S2", "Script tag", "company = `<script>alert(1)</script>`", "404; not returned as HTML", _ok(38)],
               ["S3", "Path traversal", "GET /api/plots/..%2Fapp.py", "404", _ok(39)],
               ["S4", "Dotted traversal", "GET /api/plots/../../app.py", "404", _ok(40)],
               ["S5", "CORS, own origin", "Origin: http://localhost:5405", "Origin echoed in the response", _ok(41)],
               ["S6", "CORS, foreign origin", "Origin: http://evil.example", "No allow-origin header", _ok(42)],
               ["S7", "Oversized value", "100,000-character company name", "404, no crash", _ok(43)],
               ["S8", "Undefined route", "GET /api/admin", "404", _ok(44)],
               ["S9", "Authentication and rate limiting", "Observation", "None exists (documented limitation)", "Observed"]],
              widths=[0.4, 1.4, 2.3, 1.9, 0.6], align=["c", "l", "l", "l", "c"], size=8.5),
          P("The plot endpoint is safe because it looks the name up in a fixed dictionary of three entries and never builds a path from user input. S9 is not a pass: every endpoint is public and unlimited, which is acceptable "
            "for a single-user demonstration on one PC but not for a deployment (Chapter 10).")]

    b += [H2("7.7 End-to-end smoke test"),
          P(f"`scripts/smoke_test.py` was written with the React front end and exercises every endpoint the front end calls, including the error cases. Run against the live server it printed {F.SMOKE_TOTAL} PASS lines and `ALL PASSED`."),
          P("The 15 checks are: health (models ready); meta (at least 30 companies, CSE present); companies (same count, cutoffs present); metrics (hybrid result and cross-validation present); stats (3,000 rows, six branches); "
            "the three plots (each a PNG) and an unknown plot name (404); predict (probability in [0, 1], tips present), an unknown company (404) and CGPA 14 (422); recommend (5 hybrid items and all summary fields); "
            "and the shortlist (CSE and CGPA >= 8.5) with an impossible filter (empty list).")]

    b += [H2("7.8 Performance testing"),
          P("Response times were measured sequentially (one request at a time) on the development PC "
            f"({F.ENV['cpu']}, {F.ENV['ram']} RAM, no GPU) over 127.0.0.1. The first call of each endpoint was not discarded, so the maximum includes warm-up."),
          TAB("Response time of the API (milliseconds)", ["Endpoint", "n", "Mean", "Median", "95th pct", "Max"], perf_rows(),
              widths=[2.6, 0.5, 0.8, 0.8, 0.9, 0.8], align=["l", "c", "c", "c", "c", "c"], size=10),
          P(f"The metadata and statistics endpoints answer in 3 to 30 ms and the prediction endpoint in a median of {F.PERF['POST /api/predict']['p50_ms']:.0f} ms. In process, `predict_for` takes a mean of {L['mean']:.1f} ms (p50 {L['p50']:.1f}, p95 {L['p95']:.1f}, n = {L['n']}); "
            "almost all of it is the loading of four pickle files, since the function reloads the artefacts on every call."),
          P(f"**Recommendation is slow.** `POST /api/recommend` took a mean of {F.PERF['POST /api/recommend']['mean_ms'] / 1000:.1f} s (median {F.PERF['POST /api/recommend']['p50_ms'] / 1000:.1f} s) over 8 calls. In process, over 60 students the mean was {rc['mean']:.2f} s "
            f"(median {rc['p50']:.2f}, 95th percentile {rc['p95']:.2f}, maximum {rc['max']:.2f}). The reason is structural: for each feasible company the recommender evaluates up to four roles, and each evaluation calls `predict_for`, "
            "which loads the pickles again. A request therefore performs from a few dozen to over a hundred model loads. The user interface shows a progress state during the wait, and the result is correct, but the "
            "delay is noticeable. Caching the loaded artefacts once per process would remove most of it; this was not done because the task was to document and measure the system, not to change its code."),
          P("Only sequential calls were measured; the numbers say nothing about throughput under load.")]

    b += [H2("7.9 Behaviours observed rather than asserted"),
          P("Observed rather than asserted: unknown branch and role values are accepted (V9, V10); the role-only list can be empty (F4); the recommender favours Tier-3 companies for weak profiles (in the screenshot request all five picks are ValueLabs or Infosys, because the score is the probability and package and fit are not part of it); there is no authentication or rate limiting (S9); and a strong profile at a Tier-3 company is insensitive to CGPA and backlogs (U5, U6).")]

    b += [H2("7.10 User acceptance: a walkthrough against the objectives"),
          P("No user study was carried out: no placement officer, recruiter or student outside the project team used the system, and no acceptance figure (such as a satisfaction score) is claimed. What was done is a "
            "walkthrough by the team in which each batch objective was checked against a working screen. The captures in Chapter 8 are the evidence."),
          TAB("Acceptance walkthrough against the batch objectives", ["Objective (batch document 6)", "Screen or feature used", "Outcome of the walkthrough"],
              [["1. Collect records", "`data/placement_dataset.csv` (generated)", "Partly: 3,000 synthetic records; no real data"],
               ["2. Clean, encode, address imbalance", "`src/preprocess.py`", "Encoding done; classes 59.7 / 40.3, no resampling applied"],
               ["3. Train and compare classifiers", "Officer dashboard, model table", "Met: 6 baselines, calibrated XGBoost, 2 hybrids"],
               ["4. Recommend companies", "Recommendations screen", "Met: 5 hybrid picks, base probability, average gain, match rate"],
               ["5. Identify skill gaps", "Eligibility screen: cutoff panel and tips", "Met as rules on cutoffs; SHAP ranking is global, not per student"],
               ["6. Dashboards and evaluation", "Officer dashboard, Recruiter screen", "Met: accuracy, precision, recall, F1, AUC, Brier; shortlist of 1,394 matches at CGPA 7.5, aptitude 65"]],
              widths=[2.0, 2.2, 2.4], align=["l", "l", "l"], size=9)]

    b += [H2("7.11 The limits of the testing done"),
          B("**No test on real data.** All prediction tests use a model trained on synthetic data; they show that the software behaves consistently, not that it predicts real placements.",
            "**No automated browser test suite.** The ten screens were captured by a script and inspected by eye; interaction (keyboard shortcuts, the command palette, the theme toggle, the responsive drawer) was exercised during capture but is not asserted by tests.",
            "**No concurrency or load test**, and no test on other machines, browsers or operating systems.",
            "**No test of the original Flask application** beyond its use of the same `src/` functions; the FastAPI layer is the tested interface.",
            "**Models and data are fixed.** The tests do not retrain; retraining reproduces the saved metrics to within 0.011 (Chapter 8), but that is a measurement, not a test.",
            "**The checks were written by the same team that wrote the code**, with expectations taken from the domain and the code's own rules, so they can share its blind spots.")]
    return b
