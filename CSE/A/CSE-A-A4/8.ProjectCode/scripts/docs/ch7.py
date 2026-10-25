"""Chapter 7: System Testing. Edge-probe results are read from experiments/edge_cases.json (written by a real probe run).

blocks() returns the full text; when facts.REPORT is True (the 17.Final Document build) it returns the compact variant.
"""

import json
import os

from . import facts as F
from .blocks import FIG, H1, H2, P, B, TAB
from .refs import cite as c


def pick(full, short):
    """Compact text for the full report (F.REPORT), full text for the chapter documents."""
    return short if F.REPORT else full


SMOKE_CHECKS = [
    ("health", "GET /api/health", "status ok and a non-zero row count"),
    ("dataset_info", "GET /api/dataset_info", "rows equal fraud plus legitimate; five sample rows"),
    ("dataset_stats", "GET /api/dataset_stats", "24 hourly buckets, merchant groups, amount buckets"),
    ("comparison", "GET /api/comparison", "one row per model with an F1-Score field"),
    ("train_status", "GET /api/train_status", "only the keys classical, sa, qa"),
    ("model_history", "GET /api/model_history", "per-epoch F1 present for every model"),
    ("feature_importance", "GET /api/feature_importance", "ranked importances and the selected columns"),
    ("qubo classical", "GET /api/qubo?mode=classical", "matrix returned with the stated display size"),
    ("qubo sa", "GET /api/qubo?mode=sa", "same check for the SAS model"),
    ("qubo qa", "GET /api/qubo?mode=qa", "same check for the QS model"),
    ("predict_single ensemble (fraud example)", "POST /api/predict_single", "probability in [0, 1] and a risk level"),
    ("predict_single ensemble (legit example)", "POST /api/predict_single", "legitimate example scores lower than the fraud example"),
    ("predict_single classical", "POST /api/predict_single (mode classical)", "a fraud_probability is returned"),
    ("predict_single sa", "POST /api/predict_single (mode sa)", "a fraud_probability is returned"),
    ("predict_single qa", "POST /api/predict_single (mode qa)", "a fraud_probability is returned"),
    ("predict_single unknown mode", "POST /api/predict_single (mode nope)", "HTTP 404 with an error message"),
    ("predict_batch", "POST /api/predict_batch (sample_batch.csv)", "20 rows, 10-row preview, metrics present"),
    ("predict_batch without file", "POST /api/predict_batch (no file)", "HTTP 400 with an error message"),
    ("export_predictions", "GET /api/export_predictions", "CSV containing a Fraud_Probability column"),
    ("sample_batch download", "GET /api/sample_batch", "CSV that starts with the Amount header"),
]

SMOKE_GROUPS = [
    ("Health and data", "health, dataset_info, dataset_stats", "status ok, consistent row counts, 24 hourly buckets"),
    ("Models and analytics", "comparison, train_status, model_history, feature_importance", "one row per model, F1 per epoch, ranked importances"),
    ("QUBO", "qubo classical, sa, qa", "matrix returned with the stated display size"),
    ("Single transaction", "predict_single x6 (fraud and legit examples, three models, unknown mode)", "probability in [0, 1] with a risk level; legit below fraud; unknown mode gives 404"),
    ("Bulk and export", "predict_batch, predict_batch without file, export_predictions, sample_batch", "20 rows, 10-row preview, metrics; missing file gives 400; CSV downloads"),
]


def _edges():
    p = os.path.join(F.EXP, "edge_cases.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def _find(rows, key):
    for r in rows:
        if key in r["probe"]:
            return r
    raise KeyError(key)


def blocks():
    R = F.REPORT
    L = F.LATENCY
    E = _edges()
    sv = F.SERVING
    single = L["predict_single_fraud_example"]
    batch = L["predict_batch_20_rows"]
    origin = _find(E, "Origin")["response"].split(": ", 1)[1] if E else "n/a"
    b = [H1("7. SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P(pick("SecurePay AI is a small application with one model class, one preprocessing module, a Flask API and a React interface, so the testing was organised in layers that follow the data: "
                 "checks of the numbers the models produce, checks that the API routes return what the interface expects, probes with unusual input, measurements of response time, and a visual walk-through of every screen. "
                 "Each layer was run against the real code and the real files in `models/` and `data/`; nothing was mocked.",
                 "Testing was organised in layers that follow the data: the numbers the models produce, the API routes, probes with unusual input, response time, and a walk-through of every screen. "
                 "Everything ran against the real code and the real files in `models/` and `data/`; nothing was mocked.")),
          P(f"The effort was uneven and the report says so. The one automated suite in the project is the API smoke test `scripts/smoke_test.py`, which passed {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks. "
            "There is no pytest suite, no coverage measurement and no continuous-integration job. "
            + pick("The sections below therefore describe what was run, what it showed and, in Section 7.9, what it cannot show.", "Section 7.9 states what the testing cannot show.")),
          TAB("Test layers, the evidence behind each and its status", ["Layer", "Evidence", "Status"],
              [["Unit-level", "metric assertions in `scripts/run_experiments.py`; documentation verifier", "partial, no unit-test suite"],
               ["Integration", "smoke test through the Vite proxy and Flask, models loaded from disk", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} passed"],
               ["Functional", "20 named API checks and a walk-through of the six screens", "passed"],
               ["Security", "code review plus probes of upload, CORS and error handling", "findings recorded, not fixed"],
               ["Validation and edge cases", f"{len(E)} real probes against the running API", "defects found"],
               ["Performance", "100 timed calls per route on this PC", "measured"],
               ["User acceptance", "no user study; screenshots only", "not performed"]],
              widths=[1.4, 3.3, 1.5], align=["l", "l", "l"], size=pick(10, 9.5)),
          P(pick("**Test environment and data.** All tests ran on one Windows 11 PC (12th-generation Intel Core i5-12500 CPU with 15.7 GB of memory, no GPU) with Python 3.11, Flask 3.1, scikit-learn 1.5, pandas 2.2 and NumPy 1.26. The data under test were the 39,000-row synthetic file, the 20-row sample file and two fresh synthetic sets produced with new random seeds (a 2,000-row balanced batch and a 39,000-row set with 1 % fraud) so that some tests used rows the models had never seen. "
                 "The machine was shared with other jobs, which caused several out-of-memory failures while the experiments ran; the experiment script was made resumable and retried, and every figure in this report comes from a completed run.",
                 "**Test environment and data.** One Windows 11 PC (Intel Core i5-12500, 15.7 GB, no GPU) with Python 3.11, Flask 3.1, scikit-learn 1.5, pandas 2.2 and NumPy 1.26. The data were the 39,000-row synthetic file, the 20-row sample file and two fresh synthetic sets with new seeds (a 2,000-row balanced batch and a 39,000-row set with 1 % fraud). "
                 "The machine was shared and caused out-of-memory failures; the experiment script was made resumable, and every figure in this report comes from a completed run."))]
    if not R:
        b += [TAB("Traceability: which test addresses which objective", ["Objective (batch file)", "Test or measurement", "Section"],
                  [["1. Dataset and imbalance", "dataset_info and dataset_stats checks; 1 % fraud variant", "7.4, 8.7"],
                   ["2. Preprocessing and split", "pipeline rebuilt and compared with the saved training history", "7.2, 7.3"],
                   ["3. SMOTE versus undersampling", "balancing experiment, five splits", "8.7"],
                   ["4. Three standard classifiers", "baseline training on the same split", "8.6"],
                   ["5. Precision, recall, F1, ROC-AUC", "metrics recomputed from confusion matrices", "7.2, 8.3"],
                   ["6. Deployed interface", "smoke test, edge probes, latency, screen walk-through", "7.4 to 7.8"]],
                  widths=[2.2, 3.2, 0.9], align=["l", "l", "c"], size=10)]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit-level checks"),
          P(pick("The project has no pytest suite and no unit tests were invented for this report. What stands in for them is narrower. ", "No pytest suite exists and no unit tests were invented for this report. ")
            + "The experiment script `scripts/run_experiments.py` loads the three saved models, rebuilds the 18-feature pipeline exactly as the backend does at start-up "
            f"and recomputes accuracy, precision, recall, F1 and ROC-AUC from the confusion matrix. Its saved-model results match the metrics in the training history files to the stated precision: for example the SAS model gives "
            f"{F.pct(F.SAVED['sa']['accuracy'])} accuracy and {F.pct(F.SAVED['sa']['f1'])} F1 on the {F.SPLIT['test'][0]:,}-row test split, equal to the final epoch of `history_sa.json`. "
            "The same script reconstructs the probability of three example transactions offline and compares it with the value the API returns; the two agree to full floating-point precision for the single-transaction route (Section 8.9)."),
          P(pick("The documentation verifier, `scripts/verify_docs.py`, checks that every document exists, that no template text is left, that the figures and screenshots it references exist and that the student details appear. "
                 "These checks protect the documents, not the product code. Individual functions such as `GRBMC.predict_proba`, `full_pipeline` and `evaluate` were therefore exercised only indirectly, through the routes and the experiment script that call them.",
                 "The documentation verifier protects the documents, not the product code, so functions such as `GRBMC.predict_proba`, `full_pipeline` and `evaluate` were exercised only indirectly, through the routes and the experiment script."))]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration testing"),
          P(f"Integration testing joined the layers in the order a request travels: browser, Vite development proxy on port {F.WEB_PORT}, Flask on port {F.API_PORT}, the in-memory store, the pickled pipeline and the three model files. "
            "The smoke test was run read-only against Flask directly, and the React screens were captured with `scripts/capture_screens.py` against the live backend. "
            + pick("The capture named `21_dashboard-offline.png` shows the interface reporting that the API is unavailable instead of failing silently, and `22_bulk-error.png` shows the Bulk page reporting a failed upload.",
                   "The offline and failed-upload captures (Appendix C) show the interface reporting errors instead of failing silently.")),
          P(pick("One integration detail is worth recording. The pickled `models/pipeline.pkl` was written by a newer pandas than the one installed on the test PC, so loading it raises a `TypeError` that the backend catches and ignores. "
                 "The backend then rebuilds the pipeline from an 8,000-row sample with `random_state = 42`, which is deterministic. Because the models were trained on that same sample, the rebuilt pipeline reproduces the saved training history exactly, and the integration still holds; "
                 "but the silent fallback means a stale or incompatible pickle would go unnoticed.",
                 "`models/pipeline.pkl` was written by a newer pandas than the one installed here, so loading raises a `TypeError` that the backend ignores; it rebuilds the pipeline from the 8,000-row sample with `random_state = 42`, which reproduces the saved training history exactly. The silent fallback would also hide a stale or incompatible pickle."))]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing")]
    if R:
        b += [P(f"The smoke test has {len(SMOKE_CHECKS)} checks, grouped below; all {F.SMOKE_PASSED} passed on 25 October 2026 against port {F.API_PORT}. It is read-only: its `--full` mode retrains and would overwrite `models/`, so it was not used."),
              TAB("Smoke-test checks by group (scripts/smoke_test.py)", ["Group", "Checks", "What is asserted"], [list(g) for g in SMOKE_GROUPS],
                  widths=[1.3, 2.5, 2.5], align=["l", "l", "l"], size=9),
              P("The screens were also checked by hand: the Verify form returns a verdict, risk meter and per-model probabilities; the Bulk page shows counts, a confusion matrix and a download link; the Analytics and Model-comparison tabs render from live data; the Model lab shows the training state (Section 8.1).")]
    else:
        b += [P(f"The table below lists the {len(SMOKE_CHECKS)} checks of the smoke test with what each asserts. All {F.SMOKE_PASSED} passed on 25 October 2026 against the backend on port {F.API_PORT}. "
                "The test is read-only: its optional `--full` mode regenerates the dataset and retrains, which would overwrite `models/`, so it was not used."),
              TAB("Smoke-test checks (scripts/smoke_test.py)", ["No.", "Check", "Route", "What is asserted"],
                  [[str(i), n, r, a] for i, (n, r, a) in enumerate(SMOKE_CHECKS, 1)], widths=[0.4, 2.0, 2.0, 2.0], align=["c", "l", "l", "l"], size=9.5),
              P("Functional behaviour that the smoke test does not cover was checked by hand on the screens: the Verify form accepts a transaction, shows the verdict, the risk meter, the per-model probabilities and the recommended action; the Bulk page accepts the sample file, shows counts, "
                "a confusion matrix and the download link; the four Analytics tabs and the four Model-comparison tabs render from live data; the Model lab shows the current training state of each model. Section 8.1 shows every one of these screens.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing")]
    if R:
        b += [P("SecurePay AI is a local prototype with no authentication, roles or encryption; the review was a code reading plus a few probes, and the findings are limitations, not fixed defects."),
              B("**No authentication.** Every route, including `/api/train` and `/api/generate_dataset`, which overwrite files in `models/` and `data/`, is open to anyone who can reach the port.",
                "**Development server exposed.** `app.run(host=\"0.0.0.0\", debug=True)` listens on all interfaces with the debugger and reloader on; during testing the reloader restarted the server when an unrelated package changed.",
                f"**Open CORS.** A request with `Origin: http://evil.example` was answered with `Access-Control-Allow-Origin: {origin}`.",
                "**Uploads and errors.** `pandas.read_csv` reads any posted file with no size or type check; routes return raw exception text; the scaling step uses a bare `except: pass`, the cause of the batch defect in Section 8.9.",
                "**Not tested:** injection, authentication bypass, denial of service, dependency vulnerabilities and transport security.")]
    else:
        b += [P("SecurePay AI is a prototype for a local machine and has no authentication, no roles and no encryption of its own. The security review was therefore a code reading plus a few probes, and the findings below are limitations, not fixed defects."),
              B("**No authentication or authorisation.** Every route, including `/api/train` and `/api/generate_dataset`, which overwrite files in `models/` and `data/`, can be called by anyone who can reach the port.",
                "**Development server exposed.** `backend/app.py` ends with `app.run(host=\"0.0.0.0\", port=..., debug=True)`, which listens on every network interface with the Werkzeug debugger and auto-reloader switched on. "
                "During testing the reloader restarted the server whenever an unrelated Python package on the same machine changed, which interrupted a probe run; this is harmless on a developer PC and unsafe on a shared network.",
                f"**Open CORS.** The probe with an `Origin: http://evil.example` header received `Access-Control-Allow-Origin: {origin}`, so any web page can call the API from a visitor's browser.",
                "**Upload handling.** `/api/predict_batch` reads whatever file is posted with `pandas.read_csv`. There is no size limit, no content-type check and no row limit, so a very large file can exhaust memory. Malformed files return HTTP 500 with the parser's message (Section 7.6).",
                "**Exception handling.** Routes wrap their body in `try/except Exception` and return the exception text, which leaks internal messages; the scaling step inside the prediction routes uses a bare `except: pass`, which is the cause of the batch-scaling defect in Section 8.9.",
                "**Not tested.** Injection, authentication bypass, denial of service, dependency vulnerabilities and transport security were not tested; there is nothing to test for authentication and the application is not meant to be exposed beyond localhost.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases")]
    if R:
        b += [P(f"{len(E)} probes were sent to the live API (served without the auto-reloader) and the real status and answer were recorded in `experiments/edge_cases.json`."),
              TAB("Edge-case probes and what the API returned (answers shortened)", ["No.", "Probe", "HTTP", "Observed response"],
                  [[str(i), r["probe"].replace("POST ", "").replace("GET ", ""), str(r["status"]), r["response"][:60]] for i, r in enumerate(E, 1)],
                  widths=[0.35, 2.7, 0.45, 2.8], align=["c", "l", "c", "l"], size=8),
              B("**Missing fields are filled silently** with the dataset mean or mode, so a client mistake never produces an error.",
                "**An amount of 1,000,000 returns NaN**, label LEGITIMATE and a LOW band with HTTP 200: the free-energy computation overflows and `NaN > 0.5` is false. No input-range check exists; a negative amount (-50) scores 0.379 for the same reason.",
                "**Inconsistent error codes.** Invalid JSON and a non-numeric amount return HTTP 500 where 400 is correct; an unknown model gives 404 and a missing file 400, as intended.",
                f"**Malformed uploads fail with HTTP 500**, and a CSV with only Amount and Time is accepted with every row flagged; the valid sample file returns 20 of 20 flagged, the scaling defect of Section 8.9 (it holds {sv['sample_batch_true_fraud']} fraud rows).")]
    else:
        b += [P(f"{len(E)} probes were sent to the live API with `urllib`, recording the real status code and answer. The table below gives the result. They were run against the application served without the auto-reloader (the same Flask app object), because the reloader had restarted the debug server during the first attempt. "
                "The full record is in `experiments/edge_cases.json`."),
              TAB("Edge-case probes and what the API actually returned", ["No.", "Probe", "HTTP", "Observed response"],
                  [[str(i), r["probe"].replace("POST ", "").replace("GET ", ""), str(r["status"]), r["response"][:110]] for i, r in enumerate(E, 1)],
                  widths=[0.4, 2.5, 0.5, 2.9], align=["c", "l", "c", "l"], size=9),
              P("The probes show five behaviours that matter."),
              B("**Graceful handling of missing fields.** An empty JSON object, or one that contains only an amount, is accepted: the route fills the other fields with the dataset mean or mode and returns a score. This is convenient for the form but means a client mistake never produces an error.",
                "**A numerical failure on extreme input.** An amount of 1,000,000 returns a fraud probability that is not a number (`NaN`), a label of LEGITIMATE and a LOW risk band, with HTTP 200. The free-energy computation overflows because the input is far outside the training range, and the comparison `NaN > 0.5` is false. "
                "A very large amount is exactly what a fraudster might try, so this is a real weakness; no input-range check exists.",
                "**Error codes are not consistent.** A body that is not valid JSON and a non-numeric amount both return HTTP 500 with the internal message, where HTTP 400 would be correct; an unknown model name returns 404 and a missing file returns 400, as intended.",
                "**Malformed uploads fail loudly but with HTTP 500.** An empty file and binary junk return the parser's error text; a file with only a header returns zero rows without an error.",
                f"**Silent defaults in batch mode.** A CSV with only Amount and Time is accepted and every row is flagged, because the missing columns are filled with zeros. The valid sample file returns 20 flagged rows of 20, which is the scaling defect described in Section 8.9 (the sample holds {sv['sample_batch_true_fraud']} fraud rows)."),
              P("A negative amount (-50) is accepted and scores 0.379, below the fraud threshold. The training data contains no negative amounts, so the model has nothing to say about them; a check at the API boundary would be the right remedy.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P(pick(f"Response time was measured with `scripts/measure_latency.py` against the Flask server on 127.0.0.1 after five warm-up calls. The address is given as an IP number because resolving `localhost` adds about two seconds per call on this PC. ",
                 "Response time was measured with `scripts/measure_latency.py` against Flask on 127.0.0.1 after five warm-up calls (`localhost` adds about two seconds per call on this PC). ")
            + f"A single-transaction check has a median of {single['median_ms']:.1f} ms and a 95th percentile of {single['p95_ms']:.1f} ms over {single['n']} calls; the 20-row batch route has a median of {batch['median_ms']:.1f} ms. "
            + pick("The three single-model modes cost the same as the ensemble within a millisecond, because all three models are only a few thousand weights and the cost is dominated by building the feature vector from the dataset defaults.",
                   "Single-model modes cost the same as the ensemble within a millisecond.")),
          FIG(F.fig("f12_latency.png"), "Median and 95th-percentile response time of each API route (127.0.0.1, Flask development server, this PC).", pick(5.2, 4.0)),
          P(pick("These timings describe one PC, one client and a single worker and say nothing about throughput under concurrent load. ", "These timings say nothing about concurrent load. ")
            + "Training time was measured separately: with the 8,000-row sample a 20-epoch run takes about "
            f"{F.SEEDS['classical']['elapsed_sec']['mean']:.0f} s for PCD, {F.SEEDS['sa']['elapsed_sec']['mean']:.0f} s for SAS and {F.SEEDS['qa']['elapsed_sec']['mean']:.0f} s for QS, and on the full 39,000-row file {F.FULL['classical']['elapsed_sec']:.0f} s, {F.FULL['sa']['elapsed_sec']:.0f} s and {F.FULL['qa']['elapsed_sec']:.0f} s. "
            f"The base paper reports minutes to hours for the same three procedures {c('base')}; the difference reflects the simplified, subsampled samplers used here, not a faster algorithm.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance"),
          P(pick("No user study was carried out. There was no panel of analysts or customers, no questionnaire and no timed task, so no statement about usability or acceptance by real users can be made. "
                 "What exists is a walk-through by the project team of the 22 screenshots in `docs/screenshots`, covering the landing page, six application screens in light and dark themes, three phone-width screens, an offline state and an error state. "
                 "That walk-through shows that each screen renders with real data and that the main task (check one transaction, screen a file, read the analytics) can be completed; it is evidence of completeness, not of acceptance.",
                 "No user study was carried out: no analysts, questionnaire or timed task, so nothing can be said about usability for real users. The team walked through the 22 screenshots (landing, six screens in two themes, phone layouts, offline and error states); "
                 "that shows each screen renders with real data and the main tasks can be completed, which is evidence of completeness, not of acceptance."))]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing")]
    if R:
        b += [B(f"The data are synthetic and come from one generator for training and testing, so no test shows behaviour on real card traffic or drifting fraud {c('dp18')}.",
                "There is no unit-test suite; only the 20 route checks would notice a broken internal function, and they assert that a response is well-formed, not that its probability is right (that was checked offline in Section 8.9).",
                "Probes were hand-picked; no fuzzing or load tests were run. Security testing was a code review and a few probes, so the application should not be exposed beyond localhost.",
                "No user study, accessibility audit or cross-browser test was done; screenshots used one browser engine.")]
    else:
        b += [B(f"The data are synthetic and come from the same generator for training and testing, so no test shows how the system behaves on real card traffic or on drifting fraud patterns {c('dp18')}.",
                "There is no automated unit-test suite, so a code change can break an internal function without any alarm; only the 20 route checks would notice.",
                "Probes were hand-picked; no fuzzing, property-based tests or load tests were run.",
                "The functional checks assert that a response exists and is well-formed, not that its probability is right. Correctness of the probabilities was checked separately by the offline recomputation in Section 8.9.",
                "Security testing was a code review and a few probes; the application should not be exposed beyond localhost in its present form.",
                "No user study, accessibility audit or cross-browser test was done; the screenshots were produced with one browser engine.")]
    return b
