"""Chapter 7: System Testing."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB

A = F.A


def latency_rows():
    rows = []
    for r, name in zip(F.LAT, ("LIAR2 model (12.6 MB)", "Demo model (0.85 MB)")):
        c, s = r["predict_client_ms"], r["predict_server_ms"]
        rows.append([name, f"{r['startup_s']:.1f}", f"{s['mean']:.1f}", f"{s['p50']:.1f}", f"{s['p95']:.1f}", f"{c['mean']:.1f}", f"{c['p50']:.1f}", f"{c['p95']:.1f}", f"{c['max']:.1f}"])
    return rows


def batch_rows():
    rows = []
    for r, name in zip(F.LAT, ("LIAR2 model", "Demo model")):
        bt = r["batch"]
        rows.append([name] + [f"{bt[k]['server_s']:.2f}" for k in ("100", "1000", "2296")] + [f"{bt['2296']['server_s'] / 2296 * 1000:.2f}"])
    return rows


def blocks():
    n_lib, n_api, n_smoke = F.N_UNIT_LIB, F.N_UNIT_API, F.N_SMOKE
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    b += [H2("7.1 Testing strategy"),
          P("Testing covers four layers. The small functions of the library (cleaning, features, label mapping, the Firefly decoder and fitness, the pipeline and its save/load round trip) are tested in isolation. "
            "The API is tested end to end against a real server started on a spare port with a copy of the model, so that the Retrain endpoint can never overwrite the shipped model. Edge cases and invalid "
            "inputs are driven through the same server. Finally the interface is built (type-check and production bundle) and every screen was exercised in a browser while the documentation screenshots were captured. "
            "All automated tests are in `scripts/` and re-run with one command each. They test behaviour, not predictive quality: predictive quality is measured on held-out data and reported in Chapter 8. "
            f"Before this documentation work the repository had one automated test script (`smoke_test.py`); `unit_edge_tests.py` was added, bringing the total to {F.N_TESTS} automated checks, all of which pass."),
          TAB("Test layers and results", ["Layer", "What it covers", "Script", "Result"],
              [["Unit: library", "Text cleaning, stylometric features, label mapping, demo corpus, CSV loading, Firefly, pipeline", "`scripts/unit_edge_tests.py` (in-process)", f"{n_lib} of {n_lib} passed"],
               ["Integration: API", "All eight endpoints, validation errors, batch run, a real retraining job", "`scripts/smoke_test.py` (own server, port 8496)", f"{n_smoke} of {n_smoke} passed"],
               ["Edge cases and validation", "Boundaries of the 5-word rule, malformed and oversized uploads, parameter ranges, hostile or unusual text", "`scripts/unit_edge_tests.py` (own server, port 8497)", f"{n_api} of {n_api} passed"],
               ["Build", "TypeScript type-check and Vite production build of the interface", "`npm run build`", "Passes (6.7 s)"],
               ["Functional walk-through", "All six screens used with real data (Section 7.4)", "`scripts/capture_docs_screens.py`", "All screens completed; 17 screenshots"],
               ["Performance", "Latency, batch throughput, training cost", "`scripts/measure_api.py`, `scripts/run_experiments.py`", "Section 7.6"]],
              widths=[1.3, 2.4, 1.9, 0.9], align=["l", "l", "l", "c"], size=9.5)]

    b += [H2("7.2 Unit testing of the library"),
          P(f"The in-process part of `unit_edge_tests.py` contains {n_lib} checks. They use small synthetic inputs, a 90-point toy dataset for the optimiser and the 120-document demo corpus for the pipeline, so the whole group "
            "runs in under a minute."),
          TAB("Unit checks by area", ["Area", "Checks", "Examples of what is asserted"],
              [["Text cleaning (`clean_text`)", "5", "Lower-casing and URL removal; stop words and short tokens dropped; `None` and numbers give an empty string; `@user #tag` removed; digit-only text gives nothing"],
               ["Stylometric features", "4", "25 columns per text; all values finite even for an empty text; the exclamation count of \"SHOCKING news!!! click now?\" is 3; the more-than-two-exclamations flag is set"],
               ["Class labels", "1", "`LABELS` is exactly REAL, PARTIALLY TRUE, FAKE"],
               ["Label conversion (`_canon_label`)", "3", "LIAR word labels map to 0 / 0 / 1 / 2 / 2 / 2; 0, 1, 2 and the project's names map to themselves; unknown labels go to FAKE"],
               ["Demo corpus", "2", "60 documents, 20 per class, for `n_per_class=20`; two calls with the same seed return the same corpus"],
               ["CSV loading (`load_csv`)", "6", "Title and text are joined; labels converted; the LIAR `statement` layout; a file without a label column raises `ValueError`; a missing path and a folder without CSV files raise"],
               ["Firefly optimiser", "6", "Decoding never gives an empty mask; log C and log gamma are clipped to 3 and -4; fitness is 0 for fewer than two components; `optimize` returns a mask and positive C and gamma; one history entry per generation; the informative column is kept"],
               ["Pipeline", "7", "Fit reports statistics; PCA stays between 10 and 300 components; at least one component selected; one id and three probabilities per text; probabilities sum to 1; an empty string is accepted; save and load give identical predictions"]],
              widths=[1.7, 0.7, 4.1], align=["l", "c", "l"], size=9.5),
          P("The Firefly tests assert properties that hold for every run (shapes, ranges, history length) and one that follows from a constructed dataset, not exact parameter values.")]

    b += [H2("7.3 Integration testing of the API"),
          P(f"`scripts/smoke_test.py` starts its own server on port 8496 with a copy of the model, waits for the health check and then calls every endpoint. Its {n_smoke} checks are:"),
          TAB("Smoke-test checks", ["#", "Check", "Expected"],
              [["1", "Health", "200 and `model_loaded` true"], ["2", "Model statistics", "Three labels; accuracy present; raw test predictions absent"], ["3", "Samples", "All three classes represented"],
               ["4", "Predict, sourced-style text", "REAL with a confidence in (0, 1] and probabilities summing to 1"], ["5", "Predict, clickbait text", "FAKE and the cue word \"shocking\" found"],
               ["6", "Predict, too short", "422 with a message naming the minimum"], ["7", "Batch preview", "Column `text` guessed; 3 rows"], ["8", "Batch run", "3 rows scored; distribution sums to 3; results CSV has the added columns"],
               ["9", "Batch, unknown column", "400"], ["10", "Batch, non-CSV file", "400"], ["11", "Retrain, fireflies out of range", "422"], ["12", "Retrain accepted", "202 and a job id"],
               ["13", "Second retrain while one runs", "409"], ["14", "Retrain finishes", "status done, accuracy above 0"], ["15", "Predict after retraining", "200 on the new model"], ["16", "Unknown job id", "404"]],
              widths=[0.4, 2.8, 3.3], align=["c", "l", "l"], size=9.5),
          P("Check 14 runs a complete retraining job (4 fireflies, 3 generations, 2,000 TF-IDF features), exercising the background thread, the atomic file replacement and the in-memory swap on a copy of the model.")]

    b += [H2("7.4 Functional testing"),
          P("The functional walk-through follows the use cases of Chapter 5 with real data. The screenshots in Chapter 8 are the record of this run: the interface was driven in Google Chrome by a Playwright script "
            "against the backend serving the LIAR2 model, at 1440 x 900 pixels in the dark theme."),
          TAB("Functional scenarios", ["Use case", "Scenario", "Observed result"],
              [["UC1 Check one article", "Real LIAR2 test statement (a FAKE one about a shirt photo) typed into Detect", "Verdict FAKE, confidence 83.8 %, class-probability bars, \"None found\" for both cue boxes (26 ms)"],
               ["UC1", "A REAL statement about poverty among the elderly", "Verdict REAL, confidence 54.1 %"],
               ["UC1", "A PARTIALLY TRUE statement about unemployment", "Verdict PARTIALLY TRUE shown with confidence 47.2 % while the FAKE bar is the tallest: the verdict/probability mismatch of Section 6.6.3"],
               ["UC1", "A FAKE statement about the Declaration of Independence", "Verdict REAL, confidence 53.4 %: a wrong answer, kept as the failure example"],
               ["UC3 and UC4 Batch check", "120 real test statements (40 per class) uploaded as CSV, text column `statement`", "Preview of the file, then 120 rows scored in 1.51 s as shown by the browser: 44 REAL, 24 PARTIALLY TRUE, 52 FAKE; results table and CSV download offered"],
               ["UC5 Model analytics", "Open the screen with the LIAR2 model loaded", "Accuracy 48.67 %, macro-F1 0.4134, features 4025 to 154, train time about 442 s, confusion matrix, Firefly curve, classification report, baseline-versus-proposed table"],
               ["UC7 About", "Open the screen", "Pipeline, classes and the loaded model's figures read live from the API"],
               ["UC6 Retrain", "Upload a 600-row labelled CSV (200 per class), 4 fireflies, 3 generations, confirm", "Progress card while running, then \"Retrained successfully\": 600 documents, PCA 300, 147 components kept, accuracy 42.50 %, macro-F1 0.4113"]],
              widths=[1.3, 2.6, 2.6], align=["l", "l", "l"], size=9.5),
          P("The walk-through found no crash. It made visible two behaviours recorded in Section 7.9: verdicts that contradict the probability bars, and fixed text that still describes the demo model.")]

    b += [H2("7.5 Security, validation and edge-case testing"),
          P(f"The second half of `unit_edge_tests.py` sends {n_api} deliberately awkward requests to a live server. Every one passes: the server answers with the intended status code and stays up for the next request."),
          TAB("API edge-case checks", ["Area", "Checks", "Cases"],
              [["Health and model info", "3", "Model path reported; unknown route gives 404; model info hides the raw test predictions"],
               ["Predict: boundaries", "4", "4 words gives 422; exactly 5 words gives 200; title and text together count towards the 5; whitespace only gives 422"],
               ["Predict: malformed input", "2", "Empty JSON body gives 422; a number instead of text gives 422"],
               ["Predict: unusual text", "4", "A 5,600-word article; HTML with a script tag; Devanagari text; digits only. Each returns a verdict instead of failing"],
               ["Predict: output contract", "2", "Probabilities cover exactly the three labels; latency is reported"],
               ["Batch preview", "5", "Empty file and header-only file give 400; garbage bytes do not crash the server; unknown columns fall back to the first; only 10 rows previewed"],
               ["Batch run", "5", "Blank lines are skipped by the CSV reader; an empty cell is kept and scored; 20,001 rows give 413; a 26 MB file gives 413; a missing file gives 422"],
               ["Retrain", "7", "Fireflies 21, generations 2, TF-IDF 999 and 8,001 give 422; fewer than 30 rows, a file without labels and a non-CSV upload give 400"],
               ["Samples", "1", "Six examples, two per class"]],
              widths=[1.7, 0.7, 4.1], align=["l", "c", "l"], size=9.5),
          P("These checks cover input validation, size limits, hostile content and parameter bounds. They do not amount to a security audit: there is no authentication to test, no penetration test was run and "
            "the pickle-loading risk of Section 6.9 is accepted rather than tested.")]

    b += [H2("7.6 Performance testing"),
          H3("7.6.1 Latency and throughput of the API"),
          P(f"`scripts/measure_api.py` starts a backend for each model, measures the time to the first successful health check, then makes 300 sequential `POST /api/predict` calls (after 10 warm-up calls) with real LIAR2 "
            "test statements, and then three batch runs. It addresses 127.0.0.1 rather than `localhost`, because name resolution adds about two seconds per call on the test machine. The PC was idle. "
            f"Hardware: {F.HARDWARE}."),
          TAB("Single-article latency (milliseconds, 300 requests)", ["Model", "Start-up (s)", "Server mean", "Server p50", "Server p95", "Client mean", "Client p50", "Client p95", "Client max"],
              latency_rows(), widths=[1.4, 0.7, 0.65, 0.6, 0.6, 0.65, 0.6, 0.6, 0.6], align=["l"] + ["c"] * 8, size=9),
          P(f"The server needs about {F.LAT[0]['predict_server_ms']['mean']:.1f} ms per article with the LIAR2 model and the browser sees about {F.LAT[0]['predict_client_ms']['p50']:.1f} ms at the median; the larger "
            f"model costs about {F.LAT[0]['predict_server_ms']['mean'] - F.LAT[1]['predict_server_ms']['mean']:.1f} ms more because its SVM has more support vectors. The slowest request took {F.LAT[0]['predict_client_ms']['max']:.0f} ms, which is still "
            "well under the 0.1 s that users perceive as instant."),
          TAB("Batch throughput (server time in seconds)", ["Model", "100 rows", "1,000 rows", "2,296 rows", "ms per row (2,296)"], batch_rows(), widths=[1.6, 1.0, 1.0, 1.0, 1.4], align=["l", "c", "c", "c", "c"], size=10),
          P("A whole test split of 2,296 statements is scored in about a second, so the batch screen is not limited by model speed; the 20,000-row cap is a safety limit, not a performance limit."),
          H3("7.6.2 Training cost"),
          P(f"Training is where the pipeline is expensive. A run of 10 fireflies and 12 generations with 3,000 statements took {A['train_time_s']['mean']:.0f} ± {A['train_time_s']['std']:.0f} s on this CPU, "
            f"of which one default SVM fit is {A['baseline_time_s']['mean']:.1f} s and the rest is the Firefly search ({A['n_firefly_evals']['mean']:.0f} cross-validated fits). Equal-budget random search needed "
            f"{A['random_search_time_s']['mean']:.0f} s. A linear SVM on all {F.NTRAIN_FULL:,} training statements trained in {A['ref_full_LinearSVC_time']['mean']:.2f} s and logistic regression in "
            f"{A['ref_full_LogisticRegression_time']['mean']:.2f} s. The retraining job started from the Retrain screen with 600 rows, 4 fireflies and 3 generations took 137 s in the final capture run."),
          FIG(F.fig("f07_training_time.png"), "Training time of the pipeline stages and comparison models (log scale).", 4.2),
          P("Not measured: memory use, concurrent requests, cold-cache start-up, any GPU run.")]

    b += [H2("7.7 User interface testing"),
          P("`npm run build` runs the TypeScript compiler over the whole interface and then bundles it; it passes with no type errors. The six screens were opened in Chrome with the LIAR2 model loaded and each "
            "completed its task (Section 7.4). The interface code splits every screen into its own chunk, loads charts only where used, and includes a light and a dark theme (both landing captures exist). "
            "Responsive layouts for narrow screens exist in the code (a navigation drawer below 1,024 px and a bottom bar), but they were not tested during this documentation run: only 1440 x 900 was captured."),
          P("Only Chrome was used. No automated component tests exist for the React code, the browser walk-through was a scripted capture rather than an assertion-based suite, and no accessibility audit was made.")]

    b += [H2("7.8 User acceptance testing"),
          P("No user acceptance test was performed. The project team used the application while it was built, but no group of readers, journalists or fact-checkers tried it and no questionnaire was used, "
            "so nothing is claimed about whether users find the verdicts useful or understandable. The functional walk-through of Section 7.4 stands in for it as a check that the intended tasks can be completed; "
            "it measures neither usability nor trust.")]

    b += [H2("7.9 Defects and limitations found by testing"),
          P("Testing with real data, unlike the shipped demo model, exposed behaviour that the earlier demonstrations could not show. These are reported as findings; no product code was changed."),
          TAB("Findings", ["#", "Finding", "Evidence", "Consequence"],
              [["1", "The verdict and the displayed probabilities disagree", f"On {F.LV['disagree_n']:,} of {F.NTEST:,} test statements ({F.pct(F.LV['disagree_rate'])}) the verdict is not the top-probability class; PARTIALLY TRUE is never the top class", "The confidence shown can belong to another class than the verdict (see Chapter 8)"],
               ["2", "`load_csv` misreads a label column holding only true / false", "pandas parses the column as booleans, so true becomes 1 (PARTIALLY TRUE) and false becomes 0 (REAL)", "ISOT-style files must be given REAL / FAKE words or 0 / 2 codes"],
               ["3", "`load_csv` reads the numbers 0, 1, 2 as the project's classes", "Numeric LIAR2 ids 3, 4, 5 would all become FAKE", "Six-way ids must be mapped first, as the experiment script does"],
               ["4", "Blank lines in a batch CSV are dropped silently", "A 4-line file with two blank lines scores 2 rows", "Row numbers in the results refer to the rows that were read"],
               ["5", "Fixed interface text assumes the demo model", "The landing page and Analytics note describe a \"demo corpus\" even when the LIAR2 model is loaded", "A reader could misread the real-data scores as template scores"],
               ["6", "One sensational-lexicon entry cannot match", "\"you wont believe\" has three words but tokens are matched one at a time", "Negligible effect on the 25 features"]],
              widths=[0.35, 1.8, 2.5, 1.85], align=["c", "l", "l", "l"], size=9)]

    b += [H2("7.10 Limits of the testing done"),
          B("The tests establish that the code behaves as specified for the inputs tried; they do not establish that verdicts are correct. Correctness on real statements is measured in Chapter 8 and is modest.",
            "There is no load or concurrency test; latency figures are for one client on one idle machine and vary a little between runs.",
            "No cross-browser, mobile, accessibility, security-audit or user-acceptance testing was carried out (Sections 7.7 and 7.8).",
            f"The {F.N_TESTS} automated checks run against the shipped demo model or a model trained inside the test; the interface checks run against the LIAR2 model. No test compares the two models' behaviour.")]
    return b
