"""Chapter 7: System testing."""

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, P, TAB

GROUP_TEXT = {
    "functional": ("Functional", "Every route, all four diseases, both classes: health, disease list, report, datasets, form metadata, sample rows with the requested label, and a prediction from every sample"),
    "consistency": ("Consistency", "The API's class equals a direct `model.predict` on 40 sampled rows (5 per disease and class); the same input twice gives an identical response"),
    "validation": ("Validation", "Missing field, empty body, text, `nan`, `inf`, `null` and empty string for a field (422); numeric string accepted; unknown field ignored; unknown disease (404); malformed JSON (422); wrong method (405); unknown route (404)"),
    "sanity": ("Sanity", "A clinically extreme low-risk diabetes input is predicted Low Risk and an extreme high-risk input is predicted High Risk"),
}


def _groups():
    out = {}
    for c in F.API["checks"]:
        if c["group"] == "observation":
            continue
        g = out.setdefault(c["group"], [0, 0])
        g[1] += 1
        g[0] += int(c["passed"])
    return out


def blocks():
    A = F.API
    lat = A["latency"]
    groups = _groups()
    obs = [c for c in A["checks"] if c["group"] == "observation"]
    conc = lat["POST /api/predict/diabetes (4 concurrent clients)"]
    X = F.X
    infer_hi = max(v["predict_ms_per_row"] for d in F.DISEASES for v in X[d]["timing"].values())
    infer_lo = min(v["predict_ms_per_row"] for d in F.DISEASES for v in X[d]["timing"].values())
    match = sum(int(v) for d in F.DISEASES for v in X[d]["report_match"].values())
    return [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Test Strategy"),
        P("The system is small, stateless and has one job: turn a vector of numbers into a class and a confidence. Testing therefore concentrates on four questions: do the saved models reproduce the numbers the application reports, "
          "does the API return the right answer for valid input, does it refuse invalid input with a useful message, and does the interface show the result correctly. "
          "There is **no pytest or unit-test suite** in this project; the tests below are executable scripts that run against the real models and the running service. Their output was kept in `docs/experiments/` so that the figures in this chapter can be re-checked."),
        TAB("Test layers actually run", ["Layer", "What it covers", "Tool", "Result"],
            [["Model reproduction", "Re-training the 16 models with the same split and settings gives the scores in `training_report.json`; the shipped pickles give the reported accuracy", "`scripts/run_experiments.py`", f"{match} of 16 model-and-disease cells match to 4 decimals; all 4 shipped pickles match"],
             ["API smoke test", "Every route, two samples per disease, an invalid input and an unknown disease", "`scripts/smoke_test.py` (standard library)", f"{F.SMOKE_CHECKS} checks passed, 0 failed"],
             ["API functional, consistency and validation tests", "Section 7.4", "`scripts/api_tests.py`", f"{A['passed']} of {A['total']} checks passed"],
             ["Performance", "Latency of five request types and four concurrent clients", "`scripts/api_tests.py`", "Section 7.6"],
             ["Interface", "Screens captured from the running application with real data, including an empty-form error, an out-of-range warning and a phone layout", "Playwright with Chrome, `capture_screens.py`, `capture_extra.py`", "20 screenshots; Section 7.7"]],
            widths=[1.2, 2.3, 1.4, 1.1], size=8.5),
        H2("7.2 Unit-Level Checks"),
        P("Because the code is a handful of short functions around scikit-learn objects, the unit-level evidence is indirect. Two checks stand in for unit tests. "
          f"First, the **reproduction check** retrains every model and compares accuracy and F1 with the stored report; all {match} cells agree, which shows that `train_models.py`, the saved report and the saved pickles are consistent with one another and that the results are repeatable. "
          "Second, the **consistency check** compares what the API returns with what `model.predict` returns when called directly on the same scaled vector. A function-level test of `_options` (the generator of drop-down choices), "
          "`_fields` (the field metadata) and `_summary` was not written; their output is exercised by the functional checks and appears on screen in every form."),
        H2("7.3 Integration Testing"),
        P("The integration points are file loading, the Flask-to-FastAPI import, and the browser-to-API call. The smoke test starts from the running service and walks through the whole path: health, the list of diseases, the training report, the dataset facts, and for each disease the form metadata, "
          "a negative and a positive sample row, and a prediction from that row. It asserts that the sample has the label that was requested, that the form has as many fields as the model has features, "
          "that a prediction contains one of the two result strings and a confidence between 0 and 100, that a text value is rejected with 422 and a message containing \"valid number\", and that an unknown disease gives 404. "
          "The browser-to-API call is exercised by the screen captures (Section 7.7): the React application fetched its data from the real API on port 8303 in every screenshot."),
        H2("7.4 Functional, Consistency and Validation Tests"),
        P(f"`scripts/api_tests.py` runs against the live service on `127.0.0.1:8303` and records every check in `docs/experiments/api_tests.json`. All {A['passed']} of {A['total']} checks passed. The table groups them."),
        TAB("Checks of scripts/api_tests.py", ["Group", "Checks", "Passed", "What is checked"],
            [[GROUP_TEXT[g][0], str(groups[g][1]), str(groups[g][0]), GROUP_TEXT[g][1]] for g in ("functional", "consistency", "validation", "sanity") if g in groups]
            + [["**Total**", f"**{A['total']}**", f"**{A['passed']}**", ""]],
            widths=[1.1, 0.7, 0.7, 3.5], align=["l", "c", "c", "l"], size=9),
        P("The functional group includes, for each disease, one prediction from a real positive sample and one from a real negative sample. The test checks that the call succeeds and that the confidence lies between 50% and 100%; "
          "it does **not** assert that the predicted class equals the row's label, because the models are not perfect. That is visible in the interface: for example screenshot 20 (Chapter 8) shows a heart-disease row labelled negative that the model classifies as high risk with 99.53% confidence, "
          "which is one of the 34 false positives of the heart-disease model on its test set."),
        P("Four more observations were recorded rather than counted as pass or fail, because they describe behaviour the specification does not forbid but a clinician would want to know about:"),
        TAB("Recorded observations", ["Observation", "Result"],
            [[o["name"], o["detail"]] for o in obs] + [["Out-of-range value in the browser", "Screenshot 18: a glucose of 900 shows a warning that the value is outside the training range (60 to 229.7) and the estimate may be less reliable; the form still submits"],
                                                       ["Impossible values", "The API does not check physiological ranges; the models return a class and a confidence for absurd inputs"]],
            widths=[3.0, 3.0], size=9),
        H2("7.5 Security Testing"),
        P("There is no authentication to test, no stored data to leak and no query language to inject into: every value is converted with `float()` and used only as a number. Within that narrow scope the following was checked:"),
        B("Malformed JSON, a missing body, text, `null`, `nan` and `inf` are rejected with 422 and never reach the model (validation group).",
          "A wrong HTTP method on the prediction route returns 405 and an unknown route returns 404.",
          "An unknown extra field in the body is ignored and does not change the result.",
          "The CORS list (two localhost origins) was reviewed in the code; no request from a different origin was sent to confirm the browser's refusal."),
        P("**Not tested:** authentication, authorisation, HTTPS, denial of service, rate limiting, dependency vulnerabilities, the Flask debug server and the safety of unpickling model files. No penetration test was performed."),
        H2("7.6 Performance Testing"),
        P("Latency was measured by `scripts/api_tests.py` over `127.0.0.1` with one client: 10 warm-up calls and then 200 timed calls per request type. The numbers include the HTTP client, the FastAPI routing, JSON conversion and, for the prediction requests, scaling and model inference."),
        TAB("API latency on the project machine (milliseconds)", ["Request", "Calls", "Median", "95th percentile", "Maximum", "Mean"],
            [[k.replace(" (4 concurrent clients)", ", 4 concurrent clients"), str(v["n"]), f"{v['p50_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}", f"{v['mean_ms']:.1f}"] for k, v in lat.items()],
            widths=[2.6, 0.6, 0.7, 0.8, 0.7, 0.6], align=["l", "c", "c", "c", "c", "c"], size=9),
        FIG(F.fig("api_latency.png"), "Median and 95th-percentile latency of the API (200 calls per request type, single client)", 5.0),
        P(f"A prediction takes a median of {lat['POST /api/predict/diabetes']['p50_ms']:.1f} ms for diabetes and {lat['POST /api/predict/heart']['p50_ms']:.1f} ms for heart disease, and with four concurrent clients the service handled {conc['throughput_rps']:.0f} requests per second. "
          f"Model inference itself is a small part of this: in-process prediction costs between {infer_lo:.4f} and {infer_hi:.3f} ms per row, and fitting any single model takes well under a second. "
          "Two cautions apply. The machine was under heavy memory pressure from other programs while the numbers were taken, and Windows timers have a resolution of about 15.6 ms, so single-call timings are quantised; the figures are upper bounds and are suitable only to say that a prediction needs well under 25 ms at the 95th percentile. "
          "Only localhost was used, so network latency is not included. No test with many users was run."),
        H2("7.7 Interface Testing and Acceptance"),
        P("The screens were captured by driving the real application with Playwright and Chrome at 1440 x 900: the landing page in both themes, the overview, the four prediction forms with a positive and with a negative real sample, "
          "the model-comparison page, the dataset page, the about page, the not-found page, an empty form submitted (screenshot 17), an out-of-range value (18), a phone-sized form of 390 x 844 pixels (19) and a false-positive case (20). "
          "`capture_screens.py`, written for the interface build, is designed to fail on any console error, page error, failed request or HTTP status of 400 or more; it was not re-run for this report. "
          "`capture_extra.py`, run for the documentation, completed all its captures against the same API, which shows that the pages render with data and respond to clicks. "
          "For those extra captures the interface was served from its production build (`frontend/dist`) by a static server, because the machine did not have enough free memory for the Vite development server; the code and data are the same."),
        P("**User acceptance.** No formal acceptance test with clinicians or other users was carried out. The walk-through captured in the screenshots is a developer's check, not an evaluation by the intended users, "
          "and it says nothing about whether a health worker would understand or trust the result card."),
        H2("7.8 Findings from Testing"),
        TAB("What the testing and the measurements revealed", ["Finding", "Evidence", "Consequence"],
            [["Impossible clinical values are accepted", "Glucose 100,000 mg/dL and age -5 are accepted and classified High Risk (observations in Section 7.4)", "Add range checks in the API; at present only the browser warns"],
             ["The diabetes model chosen on one split is not the best in repeated tests", "Logistic Regression wins F1 on 10 of 10 random splits; SVM was shipped on the seed-42 split (Chapter 8)", "Select models by cross-validation, not on the reported test set"],
             ["Real-looking rows can be misclassified with high confidence", "Screenshot 20; heart model has 34 false positives among 108 negative test rows", "The confidence is not a calibrated probability and should not be read as one"],
             ["The training script never computed ROC-AUC", "Objective 4 asks for it; it was measured afterwards in `run_experiments.py`", "Add ROC-AUC to `train_models.py` and to the report"],
             ["The shipped models transfer only partly to real data", "Supplementary real-data check (Chapter 8): the liver model scores below the majority-class baseline", "The application must not be used for real decisions"]],
            widths=[2.0, 2.4, 1.6], size=8.5),
        H2("7.9 What Was Not Tested"),
        B("There is no automated unit-test suite, no code-coverage measurement and no test of the React components.",
          "No test with real clinical data inside the application; the real-data check is an offline experiment.",
          "No load, stress or soak test beyond four concurrent clients on one machine.",
          "No security or penetration test, and no accessibility audit; only Chrome was used.",
          "No test on a clean machine other than the project machine, and no test of the installation steps by a second person.",
          "No user study."),
        H2("7.10 Conclusion on Testing"),
        P(f"The evidence shows that the models and the API are consistent with each other and repeatable, that all {A['total']} API checks and all {F.SMOKE_CHECKS} smoke checks pass, that invalid input is refused with clear messages, and that every screen renders with real data. "
          "It does not show that the predictions are clinically valid; that is a question about the data and the models, answered in Chapter 8, and the answer there is that the application is a demonstration."),
    ]
