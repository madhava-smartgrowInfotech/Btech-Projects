"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB
from .ch9_10 import between, fn


def _intro():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` as they stood when the results were measured; docstrings are removed to save space (the full files are in the repository). "
          "The lag features and importance weights are also explained in Chapter 6 and the walk-throughs of the design document."),
    ]


def _common():
    return _intro() + [
        H2("A.1 Cleaning and merging (`preprocessing.py`)"),
        P("Dates are parsed, rows without identifiers or with a non-positive price are dropped, exact duplicates are removed and the table is sorted by date. The left joins keep every transaction even when an article record is missing."),
        CODE(fn("src/preprocessing.py", "clean_transactions") + "\n\n" + fn("src/preprocessing.py", "merge_datasets"), 7.6),
        H2("A.2 Daily demand and zero-filling (`demand_forecasting.py`)"),
        P("A transaction row is one unit, so demand is a row count per article per day. Lag features need a continuous series, so missing days between an article's first and last sale are filled with zero."),
        CODE(fn("src/demand_forecasting.py", "aggregate_daily_demand") + "\n\n" + fn("src/demand_forecasting.py", "fill_missing_dates_per_article"), 7.6),
        H2("A.3 Calendar features, encoding and feature list (`feature_engineering.py`)"),
        CODE(fn("src/feature_engineering.py", "add_time_features") + "\n\n" + fn("src/feature_engineering.py", "encode_categoricals") + "\n\n" + fn("src/feature_engineering.py", "get_feature_columns"), 7.6),
        H2("A.4 Chronological split and moving-average baseline (`baseline_models.py`)"),
        CODE(fn("src/baseline_models.py", "chronological_split") + "\n\n" + fn("src/baseline_models.py", "moving_average_forecast"), 7.6),
        H2("A.5 XGBoost training and time-aware tuning (`xgboost_model.py`)"),
        CODE(between("src/xgboost_model.py", "DEFAULT_PARAMS = dict(", "n_jobs=-1,") + "\n)\n\n" + fn("src/xgboost_model.py", "train_xgboost") + "\n\n" + fn("src/xgboost_model.py", "tune_xgboost"), 7.6),
        H2("A.6 Domain adaptation (`domain_adaptation.py`)"),
        CODE(fn("src/domain_adaptation.py", "train_domain_classifier") + "\n\n" + fn("src/domain_adaptation.py", "compute_instance_weights") + "\n\n"
             + fn("src/domain_adaptation.py", "domain_shift_summary") + "\n\n" + fn("src/domain_adaptation.py", "train_adapted_model"), 7.6),
        H2("A.7 Metrics (`evaluation.py`)"),
        CODE(fn("src/evaluation.py", "safe_mape") + "\n\n" + fn("src/evaluation.py", "evaluate_model") + "\n\n" + fn("src/evaluation.py", "improvement_percentage"), 7.6),
        H2("A.8 The domain-adaptation route (`backend/main.py`)"),
        CODE(fn("backend/main.py", "run_domain"), 7.4),
        H2("A.9 The recursive forecast route (`backend/main.py`)"),
        CODE(fn("backend/main.py", "forecast"), 7.4),
        H2("A.10 Gating helper and shared state (`backend/main.py`, `backend/state.py`)"),
        CODE(fn("backend/main.py", "need") + "\n\n" + between("backend/state.py", "LOCK = threading.RLock()", "S[\"results\"] = {}"), 7.6),
        H2("A.11 One domain pair with its controls (`scripts/run_experiments.py`)"),
        P("The offline harness repeats the route's procedure and adds the controls that decided the conclusions: shuffled weights, mean-1 weights, a target-only model, a pooled model and the time-clean source."),
        CODE(fn("scripts/run_experiments.py", "domain_run"), 7.4),
    ]


def _report():
    return _intro() + [
        H2("A.1 Cleaning (`preprocessing.py`)"),
        CODE(fn("src/preprocessing.py", "clean_transactions"), 7.0),
        H2("A.2 Importance weights and weighted training (`domain_adaptation.py`)"),
        CODE(fn("src/domain_adaptation.py", "compute_instance_weights") + "\n\n" + fn("src/domain_adaptation.py", "train_adapted_model"), 7.0),
        H2("A.3 The domain-adaptation route (`backend/main.py`)"),
        CODE(fn("backend/main.py", "run_domain"), 6.8),
        H2("A.4 One domain pair with its controls (`scripts/run_experiments.py`)"),
        CODE(fn("scripts/run_experiments.py", "domain_run"), 6.8),
        H2("A.5 Safe MAPE (`evaluation.py`)"),
        CODE(fn("src/evaluation.py", "safe_mape"), 7.0),
    ]


def code_blocks():
    return _report() if F.REPORT else _common()


# ------------------------------------------------------------------------------ Appendix B
def guide_blocks():
    out = [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Requirements", ["Item", "Needed"],
            [["Operating system", "Windows 10/11 (run.bat); the Python and Node commands also work on Linux and macOS"],
             ["Python", "3.10 or newer on PATH (measured with 3.11.9)"],
             ["Node.js and npm", "Node 18 or newer (the interface uses Vite 8 and React 19)"],
             ["Python packages", "streamlit, pandas, numpy, scikit-learn, xgboost, lightgbm, plotly, joblib, python-dateutil, google-generativeai, fastapi, uvicorn, python-multipart, requests (`requirements.txt`)"],
             ["Extra for tests and screenshots", "`pip install pytest httpx playwright` (and `playwright install chromium` or an installed Chrome)"],
             ["Data", "H&M-style `transactions_train.csv` and `articles.csv` (customers optional); `scripts/make_sample_data.py` makes a synthetic set"],
             ["Memory", "15.7 GB was available; the 684,392-row subset needs well under 2 GB"]],
            widths=[1.7, 4.9], align=["l", "l"], size=10),
        H2("B.2 Installation and start with run.bat"),
        N("Copy or clone the project so that `8.ProjectCode` is on a local disk.",
          "Open the folder and double-click `run.bat` (or run it from a command prompt). On the first run it creates `.venv`, installs `requirements.txt` (several minutes) and runs `npm install` in `frontend`.",
          "It starts the FastAPI backend on port 8317 and the Vite frontend on port 5317 and opens `http://localhost:5317` in the browser. The two console windows must stay open.",
          "`run.bat test` starts the backend, creates the synthetic sample if it is missing and runs the 26-check smoke test.",
          "During the documentation run the servers were started manually with the commands in B.3; a fresh-machine installation through `run.bat` was not repeated."),
        H2("B.3 Manual start"),
        CODE("# backend (from 8.ProjectCode)\npython -m uvicorn backend.main:app --host 127.0.0.1 --port 8317\n\n# frontend (from 8.ProjectCode/frontend)\nnpm install\nnpm run dev\n\n# original Streamlit app (optional, from 8.ProjectCode)\nstreamlit run app.py", 8.5),
        H2("B.4 Configuration (`.env`)"),
        TAB("Settings read from .env", ["Key", "Meaning"],
            [["BACKEND_PORT / FRONTEND_PORT", "Ports for the API (default 8317) and the interface (default 5317); `run.bat` and `vite.config.js` read them"],
             ["GEMINI_API_KEY", "Optional. Without it AI Insights shows a notice and every other page works. The key is never committed (`.env` is git-ignored)"],
             ["GEMINI_MODEL", "Model name for AI Insights (default gemini-flash-latest)"],
             ["DATABASE_URL, JWT_SECRET, GEMINI_EMBED_MODEL", "Present in the shared template but not read by this product"]],
            widths=[2.4, 4.2], align=["l", "l"], size=10),
        H2("B.5 Using the console"),
        TAB("Pages and what to do on them", ["Page", "What to do", "Output"],
            [["Overview", "Read the progress checklist and open the next step", "Progress and next-step banner"],
             ["Data upload", "Choose transactions and articles (customers optional), set the row limit (0 = no limit), press Load and process data", "Data-quality report: rows read and removed, customers, products, date range"],
             ["Data exploration", "Inspect daily, weekly and monthly demand, top products, department, colour and channel mix, price histogram", "Charts"],
             ["Demand analysis", "Read the aggregated daily-demand table", "First 200 rows and the no-leakage note"],
             ["Feature engineering", "Press Build feature table", "Row and column counts, the 31 model inputs, a 50-row preview"],
             ["Model training", "Set the training fraction, run the moving average, train XGBoost (optionally tuned), or load the saved model", "Test metrics, comparison table and bar charts, best parameters"],
             ["Domain adaptation", "Pick the domain column, source and target values and run", "Classifier accuracy, shift table, histogram and box plot, before-and-after cards and report"],
             ["Model evaluation", "Compare models, read the domain report and the top-20 feature importance", "Tables and charts"],
             ["Demand forecast", "Pick an article and a 7, 14 or 30-day horizon", "History-and-forecast chart and table"],
             ["AI insights", "Ask a question or summarise the forecast (needs a key)", "Plain-language answer or an error banner"]],
            widths=[1.4, 3.0, 2.2], align=["l", "l", "l"], size=9.5),
        P("Use 0 for the row limit when the file is sorted by date: the default of 200,000 reads only the first rows and therefore only the first weeks of data. Pages stay locked, with a plain-language message, until the step before them has run."),
        H2("B.6 API quick reference"),
        CODE("curl http://127.0.0.1:8317/api/health\n"
             "curl -F transactions=@transactions_train.csv -F articles=@articles.csv -F sample_rows=0 http://127.0.0.1:8317/api/data/upload\n"
             "curl -X POST http://127.0.0.1:8317/api/features/build\n"
             "curl -X POST -H \"Content-Type: application/json\" -d '{\"train_fraction\":0.8,\"tune\":false}' http://127.0.0.1:8317/api/training/xgboost\n"
             "curl -X POST -H \"Content-Type: application/json\" -d '{\"domain_col\":\"sales_channel_id\",\"source\":2,\"target\":1}' http://127.0.0.1:8317/api/domain/run\n"
             "curl -X POST -H \"Content-Type: application/json\" -d '{\"article_id\":108775015,\"horizon\":7}' http://127.0.0.1:8317/api/forecast", 7.8),
        H2("B.7 Tests, experiments and screenshots"),
        CODE("python -m pytest tests -q                      # 39 tests\n"
             "python scripts/smoke_test.py --base http://127.0.0.1:8317\n"
             "python scripts/make_real_subset.py --raw <folder with articles.parquet and tx0.parquet> --top 300\n"
             "python scripts/run_experiments.py               # writes experiments/**/metrics.json\n"
             "python scripts/measure_api.py                   # stage times and latencies\n"
             "python scripts/capture_screens.py --rows 0 --tune\n"
             "python scripts/make_report_facts.py             # docs/REPORT_FACTS.md", 8.5),
        H2("B.8 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and fix"],
            [["Port 8317 or 5317 already in use", "Another copy is running; stop it or change the ports in `.env`"],
             ["Upload returns 400 with 'missing required column'", "The transactions file needs t_dat, customer_id, article_id, price; articles need article_id and prod_name"],
             ["A page shows a 409 message", "An earlier step has not run (upload, then features, then training); follow the message"],
             ["Only a few weeks of data after upload", "The row limit cut the file; set it to 0"],
             ["Domain run says source and target must differ", "Choose two different values"],
             ["Department pairs give R2 near 0 after adaptation", "Weights are near 1e-5 and XGBoost predicts a constant; see Chapter 8 (rescale the weights to mean 1)"],
             ["ConvergenceWarning from logistic regression", "Expected on unscaled features; the run still completes"],
             ["AI Insights shows 502 or 503", "The Gemini service was busy or unreachable (it was, during the screenshot run); retry later. Other pages are unaffected"],
             ["LightGBM crashes with an access violation", "Import `lightgbm` before pandas and XGBoost (as `scripts/run_experiments.py` does)"],
             ["API calls take about 2 seconds each from Python", "Use `127.0.0.1` instead of `localhost` (IPv6 fallback on this machine)"]],
            widths=[2.3, 4.3], align=["l", "l"], size=9.5),
    ]
    return _guide_trim(out) if F.REPORT else out


def _guide_trim(out):
    """Compact variant for the full report: requirements as one sentence, short page table, no API quick reference, short troubleshooting."""
    res, skip = [], False
    for b in out:
        if b[0] == "h2":
            skip = b[1].startswith(("B.1", "B.6", "B.7"))
            if b[1].startswith("B.1"):
                res.append(("h2", "B.1 Requirements"))
                res.append(("p", "Python 3.10 or newer (3.11.9 was used), Node.js 18 or newer, the packages in `requirements.txt`, and for tests and screenshots `pip install pytest httpx playwright`. "
                                 "Data: H&M-style `transactions_train.csv` and `articles.csv` (customers optional); `scripts/make_sample_data.py` makes a synthetic set."))
            if b[1].startswith("B.7"):
                res.append(("h2", "B.7 Tests and experiments"))
                res.append(("code", "python -m pytest tests -q\npython scripts/smoke_test.py --base http://127.0.0.1:8317\npython scripts/run_experiments.py\npython scripts/capture_screens.py --rows 0 --tune", 8.0))
        if skip:
            continue
        if b[0] == "tab" and b[1].startswith("Pages and what to do"):
            b = ("tab", b[1], ["Page", "What to do"], [[r[0], r[1]] for r in b[3] if r[0] not in ("Overview", "Demand analysis")], [1.5, 5.1], ["l", "l"], 9.0)
        if b[0] == "tab" and b[1].startswith("Common problems"):
            keep = ("Upload returns 400", "A page shows a 409", "Only a few weeks", "Department pairs", "AI Insights shows", "LightGBM crashes")
            b = ("tab", b[1], b[2], [r for r in b[3] if r[0].startswith(keep)]) + tuple(b[4:])
        if b[0] == "tab" and b[1].startswith("Settings read from .env"):
            b = ("tab", b[1], b[2], b[3][:3]) + tuple(b[4:])
        if b[0] == "p" and b[1].startswith("Use 0 for the row limit"):
            b = ("p", "Use 0 for the row limit: the default of 200,000 reads only the first rows of a date-sorted file. Pages stay locked, with a message, until the step before them has run.")
        res.append(b)
    return res


# ------------------------------------------------------------------------------ Appendix C
def screens_blocks():
    SH = F.shot
    out = [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below are captures that are not shown in Chapter 8: the public landing page in both colour themes, the overview and about pages, the empty feature page, the domain-adaptation form and the evaluation page in the dark theme. "
          "All were taken from the running application at 1440 x 900 with the real H&M subset loaded."),
        PAIR([(SH("01_landing-light.png"), "Additional screen: landing page, light theme, with the model, split, lag, rolling, weight and MAPE summary card."),
              (SH("03_landing-dark.png"), "Additional screen: landing page, dark theme.")], 2.95),
        P("The landing page is public and needs no data. Its right-hand card restates how the model is built: XGBoost with squared-error loss, a split by date (first 80 percent for training), lags of 1, 7, 14 and 28 days, rolling windows of 7, 14 and 28 days, "
          "domain weights p/(1-p) clipped at 20 and a safe MAPE that excludes zero-demand rows. The strip below the headline repeats the same settings. Both themes use the same tokens; the toggle is in the top bar."),
        PAIR([(SH("02_landing-light-features.png"), "Additional screen: landing page capability cards, light theme."),
              (SH("04_landing-dark-features.png"), "Additional screen: landing page capability cards, dark theme.")], 2.95),
        P("The four cards summarise what the product promises: the user's own data and not a demo, no data leakage, domain adaptation and honest metrics. The last promise is the one Chapter 8 holds the product to: improvements are reported as measured, including negative ones."),
        PAIR([(SH("22_overview.png"), "Additional screen: Overview page after the whole pipeline has run, with the progress checklist and the step cards."),
              (SH("23_about.png"), "Additional screen: About page with the goal, the techniques used and the data tables.")], 2.95),
        P("The overview page tells the user which step is next and shows five checkboxes (upload, features, train, adapt, forecast); each step card opens its page and shows a Done badge. "
          "The about page lists the goal, the techniques (XGBoost, chronological splitting, leakage-free lag and rolling features, logistic-regression instance weighting and safe MAPE) and the columns the three uploaded tables need."),
        PAIR([(SH("10_features-empty.png"), "Additional screen: Feature engineering page before the feature table is built."),
              (SH("14_domain-form.png"), "Additional screen: Domain adaptation form with the domain column, source and target values.")], 2.95),
        P("Before the feature table exists, the feature page shows an explanatory empty state and one button instead of an error. The domain form offers the three domain columns (sales channel, product group and department) and the values found in the data; "
          "the default is channel 1 as source and channel 2 as target, the pair that Chapter 8 reports for the app run."),
        FIG(SH("24_evaluation-dark.png"), "Additional screen: Model evaluation page in the dark theme, with the comparison table and the RMSE chart.", F.shot_w(SH("24_evaluation-dark.png"), 5.0, 4.4)),
        P("The dark theme redraws every table and chart with the same data. The comparison table in this capture shows the moving average and the tuned XGBoost that was the last model trained during the screenshot run (RMSE 10.341, R2 0.421), "
          "not the default model whose five-seed mean is 11.089."),
    ]
    if os.path.exists(SH("21b_insights-answer.png")):
        out += [FIG(SH("21b_insights-answer.png"), "Additional screen: AI Insights page with a Gemini answer.", F.shot_w(SH("21b_insights-answer.png"), 5.0, 4.4))]
    return _screens_trim(out) if F.REPORT else out


def _screens_trim(out):
    """Compact variant for the full report: three screenshot pairs and one single screen, each explained in a sentence or two."""
    res, drop_next = [], False
    for b in out:
        if b[0] == "pair" and "02_landing-light-features" in b[1][0][0]:
            drop_next = True       # capability-card pair and its paragraph
            continue
        if drop_next and b[0] == "p":
            drop_next = False
            continue
        if b[0] == "p" and b[1].startswith("The landing page is public"):
            b = ("p", "The landing page is public and needs no data; its card restates how the model is built (XGBoost, split by date, lags 1/7/14/28, rolling windows, weights p/(1-p) clipped at 20, safe MAPE).")
        if b[0] == "p" and b[1].startswith("The overview page"):
            b = ("p", "The overview page shows the progress checklist and the next step; the about page lists the goal, the techniques and the columns each uploaded table needs.")
        if b[0] == "p" and b[1].startswith("Before the feature table exists"):
            b = ("p", "Before the feature table exists the page shows an empty state and one button; the domain form offers the three domain columns, with channel 1 as source and channel 2 as target by default.")
        if b[0] == "p" and b[1].startswith("The dark theme redraws"):
            b = ("p", "The comparison table shows the tuned XGBoost that was the last model trained during the screenshot run (RMSE 10.341, R2 0.421), not the default model whose five-seed mean is 11.089.")
        if b[0] == "p" and b[1].startswith("The screens below are captures"):
            b = ("p", "The screens below were not shown in Chapter 8; all were captured at 1440 x 900 with the real H&M subset loaded.")
        res.append(b)
    return res
