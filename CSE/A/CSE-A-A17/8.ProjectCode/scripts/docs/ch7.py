"""Chapter 7: System Testing for TrendCast. Numbers come from facts.py (experiments/**/metrics.json) and the recorded test runs (docs/REPORT_FACTS.md section 13)."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def _stage_rows():
    names = {
        "upload+clean+merge (684k rows)": "Upload, clean and merge (684,392 rows)",
        "explore (aggregate daily)": "Daily-demand aggregation (first call of the Explore page)",
        "build features": "Build the feature table (31,094 rows)",
        "moving-average baseline": "Moving-average baseline",
        "train XGBoost (default)": "Train XGBoost, default parameters",
        "train XGBoost (tuned)": "Train XGBoost with tuning (10 iterations x 3 time-ordered folds)",
        "domain adaptation run": "Domain adaptation run (classifier, shift table, two models)",
        "train XGBoost (default, again)": "Train XGBoost, default parameters (second run)",
    }
    return [[names.get(k, k), f"{v:.2f}"] for k, v in F.API["stages_seconds"].items()]


def _lat_rows():
    rows = []
    for k, v in F.API["latency_ms"].items():
        rows.append([k.replace("POST /api/forecast", "POST /api/forecast"), str(v["n"]), f"{v['median']:.1f}", f"{v['p95']:.1f}", f"{v['max']:.1f}"])
    return rows


def blocks():
    b = [H1("CHAPTER 7: SYSTEM TESTING")]
    fig12 = F.fig("f12_api_latency.png")

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("TrendCast was delivered as a working Streamlit application plus a FastAPI layer and a React console, with one end-to-end smoke script and a screenshot script. "
            "The documentation run added an automated pytest suite and the measurement scripts of Chapter 8. The pipeline in `src/` is deterministic once the data and the XGBoost seed are fixed, "
            "so it is tested at unit level with exact assertions: what cleaning removes, how a daily demand row is counted, that a lag feature for day *t* equals the demand of day *t* minus *k*, that a chronological split never overlaps, "
            "and how the domain weights behave. The API is tested through FastAPI's test client on a small synthetic dataset, and through a smoke script against a running server. "
            "The screens are tested by driving every route of the console with the real H&M subset in a headless browser."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_pipeline.py (cleaning, aggregation, features, split, metrics, XGBoost, domain adaptation)", f"{F.PYTEST_UNIT} tests", "All passed"],
               ["API / component", "pytest with FastAPI TestClient: tests/test_api.py (gating, validation, whole pipeline)", f"{F.PYTEST_API} tests", "All passed"],
               ["Integration (live server)", f"scripts/smoke_test.py against a running backend (127.0.0.1, port {F.API_PORT} code path)", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Functional / screens", "Playwright walk of the console with the real subset (scripts/capture_screens.py)", "25 screenshots", "Rendered with real data; 3 problems, all from the Gemini call"],
               ["Performance", "scripts/measure_api.py against the live API", "8 stages, 6 endpoints x 20 calls", "Section 7.7"],
               ["Model validation", "scripts/run_experiments.py (6 experiment groups)", "5 seeds; 6 domain pairs", "Chapter 8"]],
              widths=[1.3, 3.2, 1.2, 1.0], align=["l", "l", "l", "l"], size=9.5),
          P(f"All tests ran on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM shared with other programs, Windows 11, Python 3.11.9, scikit-learn 1.5.0, XGBoost 2.0.3, pandas 2.2.1 and FastAPI 0.143.3. "
            f"The complete pytest suite of {F.PYTEST_TOTAL} tests finished in under 10 seconds. Timings in Section 7.7 were taken while other jobs were running on the same machine and are indicative."),
          ]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The unit file `tests/test_pipeline.py` has **{F.PYTEST_UNIT} tests, and all of them passed**. They use small synthetic frames built inside the tests (three articles over 40 to 60 days, a toy two-feature source and target), so they need no files or network. "
            "A synthetic frame is the right tool here because each assertion is about one rule, and the frame is constructed so that the right answer is known in advance."),
          TAB("Unit tests of the pipeline, grouped by module (tests/test_pipeline.py).",
              ["Module (tests)", "What is asserted"],
              [["preprocessing (5): drops bad rows, non-positive price, fills Unknown and dedupes, merge keeps rows, quality report",
                "Rows with an unparseable date, a missing customer or an exact duplicate are removed (5 rows become 2); prices of 0 or below are removed; missing article text becomes `Unknown` and duplicate article ids collapse; "
                "a left join never loses a transaction even when the article is missing from the catalogue; the quality report counts products and removed rows correctly"],
               ["demand_forecasting (2): daily demand equals the row count, missing dates filled",
                "The demand of an article on a day equals the number of its transaction rows that day; a gap between two sale days is filled with zero demand rows (3, 0, 0, 5)"],
               ["feature_engineering (4): lags use only the past, cyclical time features, categorical encoding, feature columns",
                "`lag_1` of day 10 equals the demand of day 9 and `lag_7` of day 20 equals that of day 13; the 7-day rolling mean of day 20 is the mean of days 13 to 19 and never includes day 20; "
                "weekend flags and sin/cos pairs are right (sin squared plus cos squared is 1); label codes are returned with a mapping; identifiers, date and the target are excluded from the model inputs"],
               ["baseline_models (2): chronological split, moving-average fallback",
                "The latest training date is before the earliest test date and no row is lost; an article unseen in training is forecast with the global mean"],
               ["evaluation (4): safe MAPE, perfect prediction, improvement sign, before-and-after report",
                "Zero-actual rows are excluded from MAPE and counted; a perfect prediction gives RMSE 0 and R2 1; improvement is positive when the error falls, negative when it rises, and undefined for a zero baseline; the report has the four metrics in order"],
               ["xgboost_model (1): training and sample weights",
                "XGBoost fits a linear target (correlation above 0.95) and accepts a `sample_weight` vector"],
               ["domain_adaptation (4): classifier detects shift, near chance without shift, weights, shift summary",
                "On two clearly shifted toy domains the classifier is above 70 % accurate; on identical domains it stays below 62 %; weights are non-negative, never above the clip value, and higher for target-like source rows; "
                "the shift table puts the shifted feature first"]],
              widths=[2.4, 4.0], align=["l", "l"], size=9.5),
          P("Two of these tests protect the properties the project's honesty rests on. The lag test fails if anyone removes the one-day shift in `add_lag_rolling_features`, which would let a row see its own target. "
            "The split test fails if the chronological split is replaced by a random one. Neither can be checked by looking at accuracy, because leakage makes accuracy go up.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration and API testing"),
          P(f"The file `tests/test_api.py` has **{F.PYTEST_API} tests, and all of them passed**. A module-scoped test client is created once and the tests run in file order, because the pipeline state is a single shared dictionary: "
            "each test relies on the one before it, which is how a user moves through the console. The fixture redirects the model files to a temporary folder so the tests never overwrite the user's saved models. "
            "The data are a synthetic H&M-shaped set of four articles over 70 days and two sales channels."),
          *([] if F.REPORT else [TAB("API tests in execution order (tests/test_api.py).",
              ["No.", "Test", "What it checks"],
              [["1", "health", "GET /api/health returns status ok"],
               ["2", "state before upload", "No pipeline flag is set on a fresh process"],
               ["3", "downstream routes gated", "Explore, build features and baseline training answer 409 before any upload"],
               ["4", "upload rejects wrong columns", "A transactions file without the required columns gets 400 with a message naming the missing column"],
               ["5", "upload rejects empty file", "An empty transactions file gets 400"],
               ["6", "upload ok and report", "Valid upload returns 200, 4 products and a transaction count; the report route repeats it"],
               ["7", "explore and demand table", "70 daily points, 4 top products, a 50-bin price histogram; the table returns the requested 20 rows"],
               ["8", "training gated until features", "XGBoost training answers 409 before the feature table exists"],
               ["9", "build features", "`lag_7` is among the model inputs and the preview has 50 rows"],
               ["10", "train fraction validated", "A training fraction of 0.2 gets 422; 0.99 on the split route gets 400"],
               ["11", "baseline and XGBoost training", "Both give positive RMSE, the comparison has two models, the model file is saved and can be loaded"],
               ["12", "domain options and validation", "Same source and target gets 400; a non-offered column gets 400; a valid run returns an accuracy in [0, 1], four report rows and a maximum weight of at most 20"],
               ["13", "evaluation after runs", "Comparison table, domain report and importance list are present"],
               ["14", "forecast horizons", "7, 14 and 30 days return that many rows, none negative"],
               ["15", "forecast rejects bad input", "Horizon 5 gets 400; an unknown article gets 400"],
               ["16", "new upload resets downstream", "A second upload clears features and the domain result"],
               ["17", "AI not configured", "With the key switched off the status says not configured and the explain route answers 503 with a clear message"]],
              widths=[0.4, 2.0, 4.0], align=["c", "l", "l"], size=9.5)]),
          *([P("The 17 tests run in this order: health; fresh state; gating before upload; wrong columns rejected (400); empty file rejected (400); valid upload and report; exploration and demand table; training gated until features; feature build; training fraction validated (422 and 400); baseline and XGBoost training with model save and load; domain options and validation (same domain 400, unknown column 400, valid run with accuracy in [0, 1], four report rows and maximum weight at most 20); evaluation; forecast horizons 7, 14, 30 with no negative value; bad horizon and unknown article rejected (400); a new upload clears the downstream state; and AI not configured gives 503 with a clear message.")] if F.REPORT else [])]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing"),
          P(f"`scripts/smoke_test.py` walks the product through a running backend, from the first request to the AI route, and prints one line per check. The recorded run on the synthetic sample (70,974 rows, 90 articles) gave **{F.SMOKE_PASSED} passes out of {F.SMOKE_TOTAL}**. "
            "The checks are: health; exploration gated before upload; a wrong file rejected with a column message; upload and quality report; the report route; exploration series and the demand table; training gated before features; building features (21,562 rows by 36 columns) and the 50-row preview; "
            "the split summary; the moving-average baseline (RMSE 2.581 on that sample); XGBoost training (RMSE 2.096); model persistence and loading; domain options; same-domain rejection; a domain run (classifier accuracy 58.75 %) with its histogram and box data; the evaluation page; "
            "the article list; forecasts of 7, 14 and 30 days; rejection of a 5-day horizon; and the AI route."),
          P("The smoke test ran on the synthetic sample because the real subset has no customers file; the real subset was exercised by the browser walk (Section 7.8) and the timing script (Section 7.7). "
            "The AI check passes with either a live Gemini answer or a clear error; during the recorded run Gemini did not answer and the route returned a 502 with *AI Insights is temporarily unavailable*, so it proves the failure is handled, not that Gemini text is useful.") if F.REPORT else
          P("The smoke test was run on the synthetic sample, not on the real subset, because the real subset has no customers file and the script uploads one; the real subset was exercised by the browser walk (Section 7.8) and by the timing script (Section 7.7). "
            "The AI check is written to pass either with a live Gemini answer or with a clear error: during the recorded run the Gemini service did not answer and the route returned a 502 with the message *AI Insights is temporarily unavailable*, which is the designed behaviour and is what the check accepts. "
            "It therefore proves that the failure is handled, not that Gemini text is useful.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("TrendCast is a single-user analysis tool, and its security posture is correspondingly small. This section states what exists and what does not, because neither has been penetration-tested."),
          TAB("Security-relevant behaviour of the product.", ["Area", "What exists", "What does not exist"],
              [["Access control", "CORS allows only http://localhost:5317 and http://127.0.0.1:5317", "No login, roles or tokens: anyone who can reach port 8317 can upload data, train models and read results. The `JWT_SECRET` line in `.env.example` belongs to the shared batch template and is unused"],
               ["Input validation", "Required columns are checked (400 with a column message); empty and unparseable CSV files are rejected; request bodies are typed with pydantic (training fraction 0.5-0.95, horizon 7/14/30, known domain columns); an article with fewer than five history rows is refused", "No file-size limit on the API (the UI offers a row cap, default 200,000); no content-type or virus scanning; no rate limiting"],
               ["Secrets", "The Gemini key is read from `.env`, which is git-ignored; the browser only learns whether a key is configured, never its value", "The `.env` file is a plain-text file on disk; no secret manager"],
               ["Data sent out", "AI Insights sends only an aggregated summary (metrics, top features, domain-shift statistics, forecast totals), never raw rows", "The summary is still sent to an external service when the key is set; no per-user consent screen"],
               ["Model files", "Models are saved with joblib to `models/` and loaded back from there", "joblib uses pickle: loading a model file that someone else could write is unsafe; the folder must be trusted. No signature on model files"],
               ["Concurrency", "One re-entrant lock serialises every route that touches the state", "A single process-wide state means two users would overwrite each other's data"]],
              widths=[1.1, 2.9, 2.5], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          P("The cases below were exercised by the unit, API or smoke tests unless a note says otherwise. They matter because retail files are rarely clean."),
          TAB("Edge cases, expected behaviour and observed result.", ["Case", "Expected behaviour", "Observed"],
              [["Wrong or incomplete transactions file", "400 with the names of the missing columns", "Passed (API test 4, smoke check 3)"],
               ["Empty file", "400, no crash", "Passed (API test 5)"],
               ["Calling a later step first", "409 with a plain-language instruction", "Passed (API tests 3 and 8; smoke checks 2 and 9)"],
               ["Rows with bad dates, null ids, prices of 0 or below, exact duplicates", "Dropped and counted in the quality report", "Passed (unit tests); on the real subset 79,214 of 684,392 rows (11.6 %) were removed, almost all exact duplicates"],
               ["Product missing from the article catalogue", "Row kept, attributes `Unknown`", "Passed (unit test)"],
               ["Day with no sales", "Zero-demand row created between an article's first and last sale; MAPE excludes it and counts it", "Passed; real test window has 345 excluded zero-demand rows"],
               ["Training fraction outside 0.5-0.95", "Rejected", "Passed (422 on training, 400 on the split route)"],
               ["Same source and target domain", "400", "Passed"],
               ["Target domain too small to hold out a test half", "400 with a message", "Implemented in the route; not triggered by the test data"],
               ["Forecast horizon other than 7, 14, 30", "400", "Passed"],
               ["Article with fewer than five days of history", "400, not enough history for lag features", "Passed (unknown article id)"],
               ["New upload after a trained pipeline", "Everything downstream is cleared", "Passed (API test 16)"],
               ["Gemini not configured or unreachable", "Clear message, rest of the app works", "Passed; on the real run Gemini answered 503 and then timed out"]],
              widths=[2.0, 2.4, 2.1], align=["l", "l", "l"], size=9.5),
          P("Two edge cases revealed real defects rather than passes, and both are reported in Chapter 8. First, perfectly separable domains give importance weights near 10^-5 and XGBoost then predicts a constant: the case is valid input and the product accepts it silently. "
            "Second, a source file with repeated identical rows is silently reduced by `drop_duplicates`, which on H&M data removes real repeat purchases. Neither was caught by a test because both are statistical, not functional, failures; they were found by the experiments.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P("`scripts/measure_api.py` runs the whole pipeline through the live API on the real subset (684,392 transaction rows, 300 articles, 31,094 feature rows) and then calls the light routes 20 times each. "
            "Calls were made to 127.0.0.1 because on this machine the name `localhost` adds about two seconds per request through an IPv6 fallback and would make every latency four times too high."),
          TAB("Stage times of the pipeline on the real subset (one run, seconds).", ["Stage", "Seconds"], _stage_rows(), widths=[5.0, 1.2], align=["l", "c"], size=10),
          TAB("Latency of repeated calls (20 each, milliseconds).", ["Endpoint", "Calls", "Median", "95th percentile", "Maximum"], _lat_rows(),
              widths=[2.6, 0.7, 0.9, 1.2, 0.9], align=["l", "c", "c", "c", "c"], size=10)]
    if os.path.exists(fig12) and not F.REPORT:
        b.append(FIG(fig12, "Stage times and endpoint latencies measured through the live API on the real subset.", 5.8))
    b += [P(f"Everything a user waits for is a few seconds, except tuning, which takes about {F.API['stages_seconds']['train XGBoost (tuned)']:.0f} seconds because it fits 30 models. A 30-day forecast takes a median of {F.API['latency_ms']['POST /api/forecast (30 d)']['median']:.0f} ms because the recursive loop calls "
             "the model once per day. The experiment script measured a prediction cost of about 2.3 microseconds per row for the default model and a fit time of about 1.9 seconds, so the web layer, not the model, dominates the small latencies. "
             "These numbers say nothing about larger inputs: the full H&M table has 31,788,324 rows (per its dataset card), and the per-article loops in `fill_missing_dates_per_article` and the group-wise rolling transforms would not scale to it without a rewrite.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance and the browser walk-through"),
          P("**No user study was run.** No planner, student or teacher other than the project team used the application under observation, so there are no task times, error counts or satisfaction scores, and none is claimed. "
            "What was done instead is a scripted walk of the console that a user would follow."),
          P("`scripts/capture_screens.py` opens the console in headless Chrome at 1440 by 900, uploads the real subset files with the row limit set to 0 (no cap), loads and cleans them, opens every page, builds the features, runs the baseline, trains XGBoost with and without tuning, runs domain adaptation on the default pair, opens the evaluation and forecast pages, "
            "asks the AI Insights page a question and visits the overview and about pages, saving 25 screenshots. While walking, it listens for console errors, page errors and failed requests. It reported **three problems, all caused by the Gemini call**: an HTTP 502 response from `/api/ai/explain`, "
            "the matching browser console line (*Failed to load resource: 502*) and the script's own note that no answer appeared within 90 seconds. A later script retried the question eight times with a 90-second wait each and Gemini never answered, so the AI Insights screenshot shows the error banner (*Gemini returned 503: This model is currently experiencing high demand*). "
            "No other console error, page error or failed request was seen on any page, in light or dark mode."),
          P("The walk found two things that were fixed in the script rather than in the product: after the first file is chosen, its drop zone is replaced by a *Remove* button, so the next file input is always the first one left (the first script run chose the wrong input); "
            "and the upload page must be given a row limit of 0 for a file that has already been reduced to the subset, because the default of 200,000 would keep only the first thirty days.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          B("**Test data are synthetic.** The 39 tests and the smoke test use generated data; the real H&M subset is used by the experiments, the timing run and the browser walk, but there are no assertions on the real data's values.",
            "**No load or concurrency test.** The application keeps one shared state by design; two simultaneous users were never tried and would interfere.",
            "**One browser.** The walk used headless Chrome only, at one viewport for the screenshots; responsive layouts and other browsers were not checked.",
            "**Statistical failures are not covered by pytest.** The tests check rules, not forecast quality; the model-quality defects found in Chapter 8 (collapsing weights, time overlap, frozen calendar features in the recursive loop) have no regression test yet.",
            "**No full-size run.** The product was never run on all 31.8 million H&M rows; the 200,000-row default cap of the upload page is itself a limit.",
            "**No accessibility, security or usability audit** beyond the notes in Section 7.5.",
            "**The Gemini path is untested against a live answer.** Only the failure branch was observed.",
            "**Timings are from a shared machine** and should be read as orders of magnitude."),
          P(f"In short: the pipeline rules and the API contract are well covered ({F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks, all passing), the screens render real data without browser errors, and the quality of the forecasts is established by experiments, not by tests.")]
    return b
