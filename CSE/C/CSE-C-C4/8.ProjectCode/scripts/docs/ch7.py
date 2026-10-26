"""Chapter 7: System Testing for QuantPulse. Counts come from the recorded test runs (docs/metrics/*.txt, docs/REPORT_FACTS.md section 6); timings from F.API."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB

# pytest test cases collected per file (pytest --collect-only: parametrised cases counted separately); they add up to F.PYTEST_TOTAL
N_PIPELINE, N_API = 29, 27
assert N_PIPELINE + N_API == F.PYTEST_TOTAL

_NAMES = {"health": "GET /api/health", "tickers": "GET /api/tickers", "metrics_all": "GET /api/metrics (all ten tickers)", "metrics_one": "GET /api/metrics/TSLA",
          "forecast_short": "GET /api/forecast/TSLA?horizon=short", "forecast_long": "GET /api/forecast/TSLA?horizon=long", "history_120d": "GET /api/history/TSLA?days=120 (live Yahoo download)",
          "sentiment": "GET /api/sentiment/TSLA (FinBERT scoring)", "error_invalid_ticker": "GET /api/forecast/T5LA (400)", "error_unknown_ticker": "GET /api/forecast/ZZZZ (404)",
          "frontend_index": "GET / (built React page)"}


def _lat_rows():
    rows = []
    for k, e in F.API["endpoints"].items():
        rows.append([_NAMES.get(k, k), str(e["status"]), f"{e['bytes']:,}", f"{e['first_ms']:.1f}", f"{e['median_ms']:.1f}", f"{e['p95_ms']:.1f}", str(e["n"])])
    return rows


def blocks():
    ep = F.API["endpoints"]
    b = [H1("7. SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("QuantPulse was delivered with one end-to-end smoke script (`scripts/smoke_test.py`) and a screenshot script. The documentation run added an automated pytest suite and the measurement scripts. "
            "The pipeline modules in `backend/app/` are mostly plain functions (loader, windowing, scalers, metrics, FedAvg, recursive forecast, sentiment scoring), so they are tested at unit level with exact or tolerance assertions on small constructed inputs. "
            "The FastAPI application is tested through its test client against the shipped artefacts, with the network replaced by a stub, and through the smoke script against the running servers. "
            "The predictive quality of the models is a different question from software correctness: it is not something a unit test can settle, so it is measured by the multi-seed re-run, the forward test and the multiple-instance-learning study of Chapter 8."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_pipeline.py (loader, windows, scalers, metrics, FedAvg, forecast, baselines, sentiment)", f"{N_PIPELINE} cases", "All passed"],
               ["API / component", "pytest with FastAPI TestClient: tests/test_api.py (every endpoint, validation, error codes, artefact completeness)", f"{N_API} cases", "All passed"],
               ["Integration", f"scripts/smoke_test.py against the running API (127.0.0.1:{F.API_PORT}) and website (localhost:{F.WEB_PORT})", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Functional / screens", "scripts/capture_screens.py (Playwright, Chrome, 1440 x 900) over every route with real data", "16 captures", "Rendered with real data"],
               ["Performance", "scripts/measure_api.py (127.0.0.1)", "11 endpoint groups", "Section 7.7"],
               ["Model validation", "scripts/run_experiments.py (5 seeds, forward test), scripts/mil_study.py", "10 tickers; 7 tickers x 3 folds", "Chapter 8"]],
              widths=[1.3, 3.2, 1.2, 1.0], align=["l", "l", "l", "l"], size=9.5),
          P("All tests ran on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM shared with other programs, Windows 11, Python 3.11.9, TensorFlow 2.16.2, scikit-learn 1.9.0, FastAPI 0.141.1. "
            "The full pytest run finished in about 14 s. Timings in Section 7.7 are indicative because the machine was shared.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The pytest suite has **{F.PYTEST_TOTAL} test cases in two files, and all {F.PYTEST_PASSED} passed**. `tests/conftest.py` imports TensorFlow before anything else, because on the test machine TensorFlow's DLLs fail to initialise if scikit-learn or SciPy are loaded first."),
          TAB("Unit tests of the pipeline modules, grouped (tests/test_pipeline.py).",
              ["Group", "What is asserted"],
              [["Data loader (invalid symbols, synthetic series, CSV and synthetic fallbacks, universe, ticker list)",
                "Seven invalid symbols (empty, blank, digits, over six letters, `None`) raise `ValueError`; the synthetic series is a valid OHLCV frame (High above Open/Close, Low below), identical for the same seed; with yfinance unavailable the loader reads a bundled CSV (`mode = csv`) or writes a labelled synthetic file (`# synthetic: true`, `mode = synthetic`); `QP_TICKERS` is parsed and defaults to ten tickers"],
               ["Windows, scalers and split (make_windows, scale_split, fit_scalers, prepare_features)",
                "A 60-row array gives 40 windows of 20 x 5 whose target is the next Close; scalers fit on training rows map the training range to [0, 1] and clip a rising future to exactly 1.0 (this is the behaviour that Chapter 8 shows to distort the evaluation); the split is chronological 80/20; the sentiment column is appended as feature six"],
               ["Metrics (evaluate_dl, baseline metrics, lag features)",
                "A perfect prediction gives MAE 0, R² 1 and directional accuracy 1; a constant prediction above every price scores the up-day share; baseline `_metrics`, the 80/20 `_split` and the lag-20 design matrix have the expected shapes and values; RF, SVR and ARIMA run on a random walk and return finite metrics"],
               ["Models and FedAvg (build_lstm, build_attention_lstm, train_model, fedavg, run_federated)",
                "Both Keras models output (n, 1) and train for two epochs; FedAvg weights the clients by sample count (1 : 3 gives 0.75 of the second client); two federated rounds over two clients return a global model and finite per-round losses"],
               ["Forecast (recursive_forecast)",
                "30 steps with day numbers 1-30; the band widens monotonically with the horizon, always brackets the prediction, and the lower bound is floored at 0.01 under huge uncertainty"],
               ["Sentiment (lexicon, scorer fallback, daily alignment, headline schema)",
                "The lexicon gives positive, negative and zero scores in [-1, 1]; with FinBERT unavailable the scorer falls back to the lexicon; without a news key the module reports `synthetic-fallback` with the key hint, the first rows of the daily series are 0 and only the last 90 trading days carry values; `recent_headlines` returns `headline` and `sentiment_score` only"]],
              widths=[2.6, 3.9], align=["l", "l"], size=9),
          P(f"The {N_API} API cases drive the real FastAPI application through `TestClient` on the shipped `artifacts/`, with `data_loader.load_ticker` and the sentiment function replaced by offline stubs so that no network call is made. "
            "They check the health payload (ten tickers, `trained = true`, news source), the ticker list (trend, last close, mode), the full and per-ticker metric payloads (four deep tiers, five baselines, two federated rounds, the six metric fields), "
            "the 5- and 30-day forecast shapes and the default horizon, the 422 for an unknown horizon, the 400 for twelve invalid symbols across four routes, the 404 for an unknown ticker, the sentiment and history payloads (history overlay starts after the last bar), "
            "the 422 for history lengths 5 and 501, the 503 when artefacts are missing, and that every ticker has a `.keras` model, a scaler file and a 5- and 30-row forecast on disk.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration testing"),
          P(f"`scripts/smoke_test.py` drives the running API and website over HTTP with no mocks; it finished with **{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks passed and none failed** (log `docs/metrics/smoke_run.txt`). "
            "The checks cover readiness (health OK and trained, ticker list equal to the health list), the metric payload for all ten tickers with four deep tiers and five baselines, short and long forecasts with bands that bracket the prediction, "
            "the history route (requested number of days, OHLCV fields, overlay dates equal to the front end's business-day calendar), the sentiment payload with scores inside [-1, 1], the error codes (400, 404, 422 twice, unknown `/api` path stays 404), "
            "and the website (app shell served, `/api` proxied to the backend by Vite, the API serving the built site and the client routes by SPA fallback). "
            "The smoke script exercises the live Yahoo download and the FinBERT load, so it also shows that those two external dependencies worked on the test day.")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing of the screens"),
          P("`scripts/capture_screens.py` walks every screen of the website in a real Chrome browser, with the shipped artefacts and live Yahoo prices on screen, and saves 1440 x 900 captures. "
            "The captures are the evidence used in Chapter 8: dashboard, forecast (5- and 30-day, table, dark theme), model comparison (ablation charts, metrics table, training curves), news sentiment and the method page. "
            "The React components have no unit tests or automated accessibility audit; the screen walk shows that the screens render and respond with real data, nothing more.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("QuantPulse has **no authentication, no accounts and no database**; it is a single-user research tool served on localhost. Security testing is therefore limited to input validation and the cross-origin policy. "
            "The tests confirm that ticker symbols must match one to six letters (twelve invalid symbols over four routes return 400 with a message), that the horizon and history-length parameters are validated by FastAPI (422), "
            "that unknown tickers answer 404 with a message and not a stack trace, and that the CORS policy allows only the localhost origins of the website and the API (5173, 5404, 8000, 8404)."),
          P("**Not tested:** any authorisation (none exists, so every route is public), rate limiting (none), transport security (plain HTTP), dependency vulnerabilities, the NewsAPI key handling beyond reading it from the environment, and any penetration test. "
            "The application stores no personal data, which bounds the risk but is not a defence; a deployment beyond localhost would need authentication and TLS first.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          H3("7.6.1 Validity of the evaluation"),
          P("The most important validation result of this project is not a passed test but a failed assumption. Checking the evaluation code with a constructed example (`test_scalers_are_fit_on_train_rows_only_and_clip_test_values`) shows that scalers fitted on the first 80 % of rows map a later, higher price to exactly 1.0. "
            "The deep-tier metrics are then computed against these clipped targets. Chapter 8 measures the consequence on the real data: for tickers whose test prices rise above the training maximum, the target is flat and the directional accuracy is inflated. "
            "A second check, that the sentiment channel is non-zero in the training part, fails for all ten tickers: the synthetic headline generator covers only the last 90 trading days, so no training row carries a value. "
            "Neither finding made a unit test fail, because the unit tests assert the code does what it was written to do; both were found by looking at the data, and both are recorded as limitations."),
          H3("7.6.2 Validation of the forecasts"),
          P("A forecast that cannot be checked is not testable, so the stored forecasts were scored against the closes that followed. The shipped forecasts start at the 2026-09-08 close (verified: the snapshot close on that date equals each ticker's stored `last_close`), "
            f"and thirty trading days of real closes follow. The result (Chapter 8, forward test) is a 5-day mean absolute error of ${F.FWD['short']['mean_mae']:.2f} against ${F.FWD['short']['mean_persistence_mae']:.2f} for 'no change', and a correct trend call for {F.FWD['short']['trend_hits']} of 10 tickers. "
            "The Forecast screen itself shows this comparison (actual close, forecast miss) and carries a banner that the models were trained up to 8 September 2026."),
          H3("7.6.3 Edge cases exercised"),
          TAB("Edge cases and their handling.",
              ["Case", "Handling", "Tested by"],
              [["Empty, blank, numeric, over-long or `None` symbol", "`ValueError` in the loader; 400 'Invalid ticker' from the API", "Unit and API tests (twelve API cases)"],
               ["Unknown but valid symbol (ZZZZ)", "404 with a message to train the pipeline or listing the configured tickers", "API test"],
               ["Horizon other than short or long; history length 5 or 501", "422 from FastAPI validation", "API tests"],
               ["Model artefacts missing", "503 from `/api/metrics` and `trained = false` in health", "API test (artefacts stubbed away)"],
               ["No NewsAPI key", "Labelled synthetic headlines; meta carries the key hint; first rows zero", "Unit test; screen walk"],
               ["Yahoo unreachable", "Bundled CSV (`mode = csv`), else labelled synthetic series (`mode = synthetic`)", "Unit tests with the network stubbed"],
               ["FinBERT cannot load", "Lexicon scorer, reported as `scorer: lexicon`", "Unit test"],
               ["Forecast with huge residual spread", "Lower band floored at 0.01 so prices never go negative", "Unit test"],
               ["Synthetic CSV read back on a second call", "The comment header makes the file unreadable, so a new series is generated; because Python's `hash(ticker)` seeds the generator, it differs between processes", "Checked by hand while writing the loader tests (second call reports `synthetic` again); not asserted"]],
              widths=[2.3, 2.7, 1.9], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P("`scripts/measure_api.py` calls each endpoint repeatedly against `http://127.0.0.1:8404` (the numeric address, because `localhost` adds about two seconds per call on this machine through an IPv6 fallback) and records the first call, the median and the 95th percentile."),
          TAB("API response times (milliseconds, 127.0.0.1, one uvicorn worker).",
              ["Endpoint", "Status", "Bytes", "First", "Median", "p95", "Calls"], _lat_rows(), widths=[2.6, 0.5, 0.7, 0.6, 0.6, 0.6, 0.5], align=["l", "c", "r", "r", "r", "r", "r"], size=9),
          FIG(F.fig("f11_api_latency.png"), "Median and 95th-percentile response time of each endpoint (log scale).", 5.4),
          P(f"The routes that serve stored results (health, tickers, metrics, forecasts, errors, the built page) answer in a median of about {min(e['median_ms'] for e in ep.values()):.0f} to {max(ep[k]['median_ms'] for k in ('metrics_all', 'metrics_one', 'forecast_short', 'forecast_long')):.0f} ms; "
            f"the 95th percentile of about 16 ms across them is the resolution of the Windows timer, not a real tail. Two routes are different in kind. `/api/history` re-downloads the prices from Yahoo Finance on every request and rewrites a CSV, which costs a median of {ep['history_120d']['median_ms']:.0f} ms "
            f"({ep['history_120d']['first_ms']:.0f} ms on the first call). `/api/sentiment` scores the headlines with FinBERT on the CPU on every request: median {ep['sentiment']['median_ms'] / 1000:.1f} s and {ep['sentiment']['first_ms'] / 1000:.1f} s for the first call, which is why the website shows a patient progress state and allows a 240-second timeout. "
            "Neither is cached, so both would be the first things to fix before real use (Chapter 10)."),
          P("The training pipeline (`python -m backend.train`) is not a latency problem but a set-up cost: the README quotes 5 to 10 minutes on a CPU for ten tickers; the five-seed re-run of the same pipeline took "
            f"{F.RR['seconds'] / 60:.0f} minutes while the machine was also running other jobs. No load test with many simultaneous users was run; the API holds its caches in module globals and has no state that concurrent readers would corrupt, but that was not tested.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance"),
          P("**No formal user-acceptance test was carried out.** There was no panel of traders or analysts, no questionnaire and no usability metric. What exists is a repeatable walkthrough: open the dashboard, pick a ticker, read the 5-day outlook, compare it with the actual closes on the same chart, "
            "switch to 30 days, open the model comparison and read the ablation, open the sentiment screen and read its source banner. Each step was executed by the screen-capture script with real data, so it is known to work, "
            "but whether a trader would find the forecasts useful is answered by Chapter 8, not by acceptance testing, and the answer is that they would not have been: the stored forecasts missed the realised moves.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Findings from testing"),
          P("Writing the tests and running the experiments produced findings that are recorded rather than hidden. They change how the product should be described rather than how it passes its tests."),
          B("**The evaluation clips its targets** (Section 7.6.1): directional accuracy of 67 to 68 % in the shipped table is 53 % on the real closes.",
            "**The sentiment tier is trained on an all-zero channel**, so the ablation cannot show an effect of sentiment.",
            "**The stored forecasts were wrong in direction for six of ten tickers** over five trading days (Chapter 8).",
            "**Reads overwrite data:** every `/api/history` call rewrites `data/<T>.csv`, so the experiments use a pinned snapshot; the API also never loads the saved `.keras` models, it serves stored JSON.",
            "**No multiple-instance component and no precision, recall or F1 in the product**; they exist only in the offline study.")]

    # ------------------------------------------------------------------ 7.10
    b += [H2("7.10 Limits of the testing done"),
          B(f"**The unit tests assert intended behaviour.** {F.PYTEST_TOTAL} passing pytest cases and {F.SMOKE_TOTAL} passing smoke checks show the software does what it was written to do; they say nothing about whether the forecasts are good.",
            "**The React components are untested** apart from the screen walk; no accessibility or cross-browser audit beyond Chrome/Chromium.",
            "**External services were live** during the smoke run (Yahoo Finance, Hugging Face); the unit and API tests use stubs.",
            "**Statistical power is small**: ten tickers, 97 test windows each, five seeds; the forward test covers one 30-day period after one training date.",
            "**No concurrency, endurance, Docker, clean-machine (`run.bat`) or security audit** was run.")]
    return b
