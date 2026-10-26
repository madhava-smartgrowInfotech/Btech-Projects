"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for QuantPulse."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .ch1 import K
from .refs import CITE as R


def ep(name, key="median_ms"):
    return F.API["endpoints"][name][key]


def blocks():
    return chapter3() + chapter4()


def epochs(tier):
    import numpy as np

    return float(np.mean([x["epochs"] for t in F.TICKERS for x in F.RR["tickers"][t]["models"][tier]]))


# =====================================================================================================================
def chapter3():
    k = K()
    secs = F.RR["seconds"]
    return [
        H1("3. FEASIBILITY STUDY"),
        H2("3.1 Introduction"),
        P("This chapter asks whether QuantPulse can be built, run and maintained with the resources at hand. The question is answered partly by argument and partly by measurement: the system was built and "
          "run on a single office desktop with no graphics card, and the figures below were taken on that machine."),
        H2("3.2 Technical Feasibility"),
        P("**Hardware.** Every measurement in this report was taken on an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, integrated graphics and Windows 11. No CUDA device was used, "
          "so the training pipeline (ten tickers, three deep tiers and a federated stage) runs on the CPU. Smaller machines were not tested; the machine was shared with other jobs during several runs, "
          "so timings are indicative."),
        P("**Software.** All components are mature open-source packages: Python 3.11, TensorFlow and Keras for the LSTM and attention models, scikit-learn, statsmodels and Prophet for the baselines, "
          "transformers with PyTorch for FinBERT-tone inference, yfinance for prices, FastAPI with uvicorn for the service, and React with Vite and Recharts for the website. They install from public package indexes, "
          "and `run.bat` creates the environment, trains the models if the artefacts are missing, and starts both servers."),
        P("**Data.** Daily prices are free through Yahoo Finance [" + str(R["yahoo"]) + "]. News is the weak point: the news service used by the base paper [" + str(R["newsapi"]) + "] returns about a month of "
          "history on its free tier and needs a key. Without a key QuantPulse falls back to labelled synthetic headlines. A public alternative with real headlines exists (FNSPID [" + str(R["fnspid"]) + "]); "
          "it was used for the offline study but not inside the product."),
        P("**Model size and training effort.** The models are small by current standards. Each ticker supplies 501 rows, which become 481 windows of twenty days, of which 384 are used for training (about 330 after the validation hold-out), and the networks have one "
          "64-unit LSTM layer with, in the attention tiers, a four-head attention layer. Early stopping with a patience of seven epochs ended training after "
          f"{epochs('lstm'):.0f} epochs on average for the plain LSTM and {epochs('lstm_attention'):.0f} for the attention tier in the five-seed re-run, and in the five-seed re-run the four single-ticker tiers of one ticker trained in about a minute or less on the shared CPU machine. "
          "This is the main reason the technical side of the project is feasible without a graphics card; it is also a warning, because a few hundred windows are a small sample for a deep network."),
        P("**Evidence from measurement.** The technical risks were tested directly:"),
        TAB("Technical risks and the measurements that addressed them", ["Risk", "Measurement", "Verdict"],
            [["Training too slow without a GPU", f"A full five-seed re-run of ten tickers, four deep tiers and the federated stage took {secs / 60:.0f} minutes on the shared CPU machine; the README quotes 5-10 minutes for one training run", "Feasible"],
             ["API too slow for a live website", f"Stored-result endpoints answer in about {ep('forecast_short'):.0f} ms (median), the 76 KB all-metrics payload in {ep('metrics_all'):.0f} ms", "Feasible"],
             ["Live price download inside a request", f"`/api/history` re-downloads from Yahoo Finance on every call: median {ep('history_120d'):.0f} ms, first call {ep('history_120d', 'first_ms'):.0f} ms", "Feasible but wasteful"],
             ["Sentiment scoring on demand", f"`/api/sentiment` scores headlines with FinBERT on each call: median {ep('sentiment') / 1000:.1f} s, first call {ep('sentiment', 'first_ms') / 1000:.1f} s", "Slow; the UI shows a loading state"],
             ["Forecast accuracy good enough to use", f"Mean 5-day MAE ${k['f5_mae']:.2f} against ${k['f5_pers']:.2f} for a no-change forecast; trend flag right for {k['f5_hits']} of 10 tickers", "Not feasible as shipped"],
             ["Real news available for training", "None in the product (synthetic fallback); 46,532 real FNSPID headline rows were obtained for the offline study", "Partly feasible"]],
            widths=[1.8, 3.4, 1.3], align=["l", "l", "l"], size=9.5),
        P("**Environment risks that did occur.** TensorFlow fails to initialise its libraries on this Windows machine if scikit-learn or SciPy are imported before it, so the tests and experiment scripts import "
          "TensorFlow first. Newer NumPy releases are incompatible with this TensorFlow version, which pins NumPy 1.26 and in turn limits the parquet library that could be used for the news data. "
          "Both were solved by import order and version pins; neither affects a user who runs the application through `run.bat`."),
        H2("3.3 Economic Feasibility"),
        P("The software is free of licence cost, the price source is free, and the whole project ran on one existing workstation. The only optional paid item is a news API key for live headlines; the "
          "free tier is enough for a demonstration but covers a single month. Hosting needs one process and no database or GPU. "
          "The recurring cost of a production deployment would be dominated by a licensed news and price feed, which the project does not include. Development effort was student time."),
        TAB("Cost view of the project", ["Item", "Cost", "Comment"],
            [["Python, TensorFlow, PyTorch, scikit-learn, FastAPI, React", "Free (open source)", "Installed from public package indexes"],
             ["Daily prices", "Free", "Yahoo Finance through yfinance; terms of use apply and the data are for research and education"],
             ["Live news headlines", "Free tier or paid key", "NewsAPI free tier covers about a month; not set in this project"],
             ["Historic headlines for the offline study", "Free", "FNSPID subset read from a public mirror; licence listed as 'other' on the mirror card, used for research only"],
             ["Compute", "Existing workstation", "No GPU or cloud instance was rented"]],
            widths=[2.2, 1.3, 3.0], align=["l", "l", "l"], size=9.5),
        H2("3.4 Operational Feasibility"),
        P("The intended users are a trader or analyst who wants to read forecasts and an evaluator or developer who wants to retrain and inspect the models. The first group needs only a browser: the website has six screens "
          "with ticker tabs, a horizon switch and tables that can be sorted. The second group needs Python 3.11 and Node.js 20 and runs `python -m backend.train` or `run.bat`. "
          f"The service has no authentication and no database, which makes it easy to run and unsuitable for exposure to the internet as it stands. {F.PYTEST_PASSED} automated tests and {F.SMOKE_PASSED} smoke checks pass, "
          "which makes day-to-day maintenance practical."),
        H2("3.5 Schedule Feasibility"),
        P("The work was organised in the phases below. The batch calendar was not recorded in the project files, so no dates or durations are claimed; the table shows the order of the phases and their status."),
        TAB("Project phases and status", ["Phase", "Content", "Status"],
            [["1", "Literature survey, base-paper reading, objectives", "Done"], ["2", "Data loader, ten-ticker universe, five classical baselines", "Done"],
             ["3", "LSTM, attention tier, sentiment module, federated averaging, training pipeline", "Done"], ["4", "FastAPI service with seven endpoints", "Done"],
             ["5", "React website, six screens, light and dark themes", "Done"], ["6", "Automated tests, smoke test, screenshots", "Done"],
             ["7", "Evaluation: five-seed re-run, forward test, multiple-instance study on real news", "Done in the documentation run"], ["8", "Documentation: decks, chapters, report, paper", "Done"]],
            widths=[0.6, 4.4, 1.5], align=["c", "l", "l"], size=10),
        H2("3.6 Risk Analysis"),
        P("Beyond the technical risks above, the project carries risks that are about the data and the interpretation of results rather than the software. They are listed with the mitigation actually used."),
        TAB("Project risks and mitigations", ["Risk", "Effect", "Mitigation used"],
            [["Live price download fails or changes the data window", "Artefacts older than the CSVs; inconsistent charts", "Bundled CSV fallback; a banner on the forecast screen; a pinned snapshot for the experiments"],
             ["No news key", "Sentiment channel is synthetic", "Source shown on screen (built-in fallback); documented as a limitation; real headlines used only offline"],
             ["Short, trending series", "Test prices above the training range; clipped scaling", "Identified and reported; true-target scoring added in the re-run"],
             ["Over-reading a small test set", "Spurious gains reported as findings", "Five seeds, bootstrap intervals, placebo and always-up baselines in the offline study"],
             ["Misuse as financial advice", "Losses to users", "Disclaimer on the site and in the report: research and education only"]],
            widths=[2.0, 2.0, 2.5], align=["l", "l", "l"], size=9.5),
        H2("3.7 Advantages and Constraints"),
        P("The advantages are that the whole pipeline is reproducible on modest hardware, uses only open components, and is fast to serve because it stores its results. The constraints are the news data (a month of live "
          "headlines, synthetic fallback otherwise), the short two-year price history, the absence of a social-media source, the CPU-only training, and the fact that the forecasts themselves are not accurate "
          "enough to act on. These constraints are carried into the limitations in Chapters 7 to 9."),
    ]


# =====================================================================================================================
def chapter4():
    k = K()
    pt = lambda i: f"[{R[i]}]"
    reqs = [
        ["FR-1", "Load daily OHLCV for each ticker of the configured universe (default ten), preferring a live download, then a bundled CSV, then a labelled synthetic series", "`data_loader.py`; `mode` returned with every record"],
        ["FR-2", "Train and evaluate five baselines (ARIMA, SARIMAX, Prophet, random forest, SVR) on a chronological 80/20 split", "`baselines.py`"],
        ["FR-3", "Train an LSTM, an LSTM with four-head attention, the same with a sentiment channel, and a federated hybrid", "`models_dl.py`, `federated.py`"],
        ["FR-4", "Compute a daily sentiment score from news headlines with FinBERT-tone, using NewsAPI when a key is set and a labelled synthetic fallback otherwise", "`sentiment.py`"],
        ["FR-5", "Produce 5- and 30-day close forecasts with a confidence band and an up/down trend flag per ticker", "`forecast.py`, `/api/forecast`"],
        ["FR-6", "Report MAE, MSE, RMSE, R2 and directional accuracy for every model and ticker", "`metrics.json`, `/api/metrics`"],
        ["FR-7", "Serve price history with the forecast overlay", "`/api/history`"],
        ["FR-8", "Serve daily sentiment and recent headlines per ticker", "`/api/sentiment`"],
        ["FR-9", "Reject malformed tickers (400), unknown tickers (404), bad horizons or ranges (422) and missing artefacts (503) with a clear message", "`main.py`"],
        ["FR-10", "Provide six website screens: landing, dashboard, forecast, model comparison, news sentiment, method and data", "`frontend/src/pages`"],
        ["FR-11", "Allow retraining with one command and regeneration of all artefacts", "`python -m backend.train`"],
    ]
    nfr = [
        ["NFR-1", "Responsiveness", f"Stored-result endpoints under 50 ms median; measured {ep('forecast_short'):.0f}-{ep('metrics_all'):.0f} ms", "Met"],
        ["NFR-2", "Reproducibility", "Fixed seeds, pinned data snapshot for the experiments, chronological splits; synthetic headlines need PYTHONHASHSEED fixed", "Partly met"],
        ["NFR-3", "Honesty of display", "Data mode (live / csv / synthetic) and news source shown on screen; stale-artefact banner on the forecast screen", "Met"],
        ["NFR-4", "Portability", "Windows 10/11 with Python 3.11 and Node 20; Docker files provided but not exercised in this run", "Partly met"],
        ["NFR-5", "Testability", f"{F.PYTEST_PASSED} pytest tests and {F.SMOKE_PASSED} smoke checks pass", "Met"],
        ["NFR-6", "Security", "Input validation on ticker symbols and ranges; CORS limited to localhost; no authentication, no TLS in the demo", "Partly met"],
        ["NFR-7", "Accuracy", f"Forecast error below a no-change forecast: 5-day MAE ${k['f5_mae']:.2f} versus ${k['f5_pers']:.2f}", "Not met"],
    ]
    sw = [["Python", "3.11.9"], ["FastAPI / uvicorn", "0.141.1 / 0.52.4"], ["TensorFlow / Keras", "2.16.2 / 3.15.1"], ["scikit-learn", "1.9.0"], ["statsmodels / Prophet", "0.15.0 / 1.4.0"],
          ["transformers / PyTorch (CPU)", "4.47.1 / 2.5.1"], ["yfinance", "1.7.0"], ["pandas / NumPy", "3.0.5 / 1.26.4"], ["React / Vite / Recharts", "19 / 8 / 3"], ["Node.js", "20 or newer"]]
    return [
        H1("4. SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System and its Limitations"),
        P("In practice the existing approaches are of three kinds. Retail investors use charting platforms and statistical indicators that look only at prices. Researchers use statistical and machine-learning "
          f"forecasters such as ARIMA, Prophet, random forests and support vector regression {pt('box')}, {pt('prophet')}, {pt('rf')}, {pt('svr')} or LSTM networks {pt('lstm')}, usually as scripts or notebooks. "
          f"The base paper {pt('base')} adds attention, a FinBERT-tone sentiment channel and simulated federated learning, again without an application. Multi-source multiple-instance models {pt('zhang')}, {pt('deng')} "
          "treat news as bags but are research systems."),
        N(*lit.LIMITATIONS_OF_EXISTING),
        H2("4.2 Proposed System and its Advantages"),
        P("QuantPulse turns the base paper's pipeline into a usable system: one command trains ten tickers and writes artefacts; a FastAPI service serves metrics, forecasts, history and sentiment; and a six-screen "
          "website shows the forecast chart with its confidence band, the actual closes that followed, the comparison of nine models, and the sentiment channel with its source. Compared with the scripts it replaces it "
          "offers an inspectable interface, a stored set of results, explicit labelling of data and news sources, and automated tests. It also exposes its own errors: the forecast table shows the actual close and "
          "the forecast miss for every day since the forecast date."),
        P("The proposed system deliberately differs from the batch title in one respect that has to be stated clearly: **it does not implement Multiple Instance Learning**. Its attention layer operates over the "
          "twenty-day price window, its sentiment is one averaged score per day, and it has no social-media source. The multiple-instance formulation was therefore studied in a separate offline experiment on real "
          f"headlines, which found no evidence of a gain over a price-only LSTM (accuracy between {k['acc_lo'] * 100:.1f} % and {k['acc_hi'] * 100:.1f} % for all variants against {k['always_up'] * 100:.1f} % for always predicting up)."),
        P("In operation the system has five stages. Data loading obtains two years of daily bars per ticker and labels their origin. The baseline stage fits the classical models on the first 80 % of rows. The deep stage "
          "scales the features to the unit range with scalers fitted on the training part, cuts twenty-day windows, trains the three tiers with early stopping, and then trains the federated hybrid by averaging ten "
          "client models over two rounds of three local epochs. The forecast stage rolls the last window forward five and thirty steps and widens a confidence band with the square root of the horizon. The serving stage "
          "writes everything to JSON artefacts, which the API returns and the website draws. Separating training from serving is what makes the application fast, and it is also why it can show forecasts that are older "
          "than the latest price, a situation the forecast screen explains with a banner."),
        H2("4.3 Functional Requirements"),
        P("The functional requirements follow from the objectives and from the scope in Chapter 1. Each is traced to the module that implements it, so that the testing chapter can check them one by one."),
        TAB("Functional requirements", ["ID", "Requirement", "Where implemented"], reqs, widths=[0.6, 4.0, 1.9], align=["c", "l", "l"], size=9.5),
        H2("4.4 Non-Functional Requirements"),
        P("The non-functional requirements describe how well the functions must work. The status column is honest about the one that is not met: accuracy. A forecasting product that is not more accurate than a "
          "no-change forecast does not satisfy its main quality requirement, and the report does not hide this."),
        TAB("Non-functional requirements and their status", ["ID", "Quality", "Criterion and evidence", "Status"], nfr, widths=[0.7, 1.1, 3.9, 0.8], align=["c", "l", "l", "c"], size=9.5),
        H2("4.5 Hardware Requirements"),
        TAB("Hardware used and recommended", ["Item", "Used for all measurements", "Minimum suggested"],
            [["Processor", "Intel Core i5-12500, 6 cores / 12 threads", "4 cores"], ["Memory", "15.7 GB", "8 GB (FinBERT and TensorFlow load about 2-3 GB together)"],
             ["Graphics", "Integrated; not used", "None required"], ["Disk", "About 3 GB for environment and models", "5 GB free"],
             ["Network", "Needed for Yahoo Finance and the first FinBERT download", "Broadband"]], widths=[1.3, 2.9, 2.3], align=["l", "l", "l"], size=10),
        P("The \"minimum suggested\" column is an estimate, not a tested minimum; only the first column was measured."),
        H2("4.6 Software Requirements"),
        TAB("Software versions used", ["Component", "Version"], sw, widths=[3.5, 3.0], align=["l", "l"], size=10),
        P("The operating system was Windows 11. The browser used for screenshots and checks was Chromium / Chrome. A Python 3.11 virtual environment and Node.js are created or required by `run.bat`."),
        H2("4.7 User Roles"),
        TAB("User roles", ["Role", "Needs", "Interface"],
            [["Trader / analyst", "Read forecasts, bands and trend flags; compare models; see the news tone; check how earlier forecasts fared", "Website (six screens)"],
             ["Evaluator / developer", "Retrain, run tests, inspect artefacts, re-run experiments, call the API directly", "Command line, JSON API, `/docs`"]],
            widths=[1.5, 3.4, 1.6], align=["l", "l", "l"], size=10),
        P("There are no accounts and no login screen; any visitor to the running site sees everything. This is acceptable for a local demonstration but would have to change before any shared deployment, "
          "where at least authentication, request limits and transport security would be needed. The evaluator role is deliberately separate from the trader role because the experiments (the five-seed re-run, the forward test "
          "and the multiple-instance study) are run from the command line against pinned data and are not available from the website."),
        H2("4.8 Data Requirements"),
        TAB("Data used by the system", ["Data", "Source", "Granularity and size", "Use"],
            [["Prices (Open, High, Low, Close, Adj Close, Volume)", "Yahoo Finance via yfinance", "Daily; 501 rows per ticker for the shipped artefacts (2024-09-09 to 2026-09-08); ten tickers", "Training, evaluation, charts"],
             ["Headlines for the sentiment channel", "NewsAPI if a key is set, otherwise 11 built-in templates", "166-191 synthetic headlines per ticker for the last 90 trading days", "Daily FinBERT-tone mean as one extra input"],
             ["Pinned price snapshot for experiments", "Yahoo Finance", "534 rows per ticker (2024-09-09 to 2026-10-23)", "Re-run and forward test"],
             ["Real headlines for the offline study", "FNSPID news portion", "46,532 headline rows for seven tickers, dense from 2022", "Multiple-instance study"],
             ["Stored results", "`artifacts/` JSON, Keras and plots", "metrics.json (76 KB), forecasts.json, ten serving models", "Served by the API"]],
            widths=[1.7, 1.5, 2.2, 1.1], align=["l", "l", "l", "l"], size=9),
        H2("4.9 Interface Requirements"),
        TAB("API interface", ["Method and path", "Purpose", "Errors"],
            [["GET /api/health", "Status, tickers, news source", "-"], ["GET /api/tickers", "Universe with last close, trend and data mode", "-"],
             ["GET /api/metrics, /api/metrics/{ticker}", "Per-ticker baselines, deep tiers, histories, forecasts", "400, 404, 503"],
             ["GET /api/forecast/{ticker}?horizon=short|long", "5 or 30 forecast rows with bands", "400, 404, 422"],
             ["GET /api/sentiment/{ticker}", "Sentiment meta, 30 daily scores, headlines", "400"],
             ["GET /api/history/{ticker}?days=20..500", "OHLCV plus forecast overlay", "400, 422"]],
            widths=[2.6, 2.8, 1.1], align=["l", "l", "c"], size=9.5),
        P("The website talks to the service only through this JSON interface, from the same origin (the development server proxies `/api`). The interface has no write operations: users cannot change "
          "models, data or settings from the browser, which keeps the attack surface small."),
        H2("4.10 Use Cases"),
        TAB("Principal use cases", ["ID", "Use case", "Actor", "Outcome"],
            [["UC-1", "See the forecast universe", "Trader / analyst", "Dashboard shows last close, trend and 5-day outlook per ticker"],
             ["UC-2", "Inspect one forecast", "Trader / analyst", "Chart with confidence band, forecast table and, where available, the actual closes since the forecast date"],
             ["UC-3", "Compare models", "Trader / analyst", "Nine models ranked by MAE, R2 and direction; training curves and federated rounds"],
             ["UC-4", "Check news tone", "Trader / analyst", "Daily sentiment series, source label and headline list with tone"],
             ["UC-5", "Retrain and test", "Evaluator / developer", "New artefacts, test and smoke results, experiment JSON files"]],
            widths=[0.6, 1.8, 1.4, 2.7], align=["c", "l", "l", "l"], size=9.5),
        H2("4.11 Existing and Proposed Systems Compared"),
        TAB("Comparison of the existing practice and QuantPulse", ["Aspect", "Existing practice", "QuantPulse"],
            [["Access", "Scripts and notebooks", "Browser website and JSON API"], ["Models shown together", "One or two per study", "Five baselines and four deep tiers for ten tickers"],
             ["Data labelling", "Rarely stated", "Mode (live / csv / synthetic) and news source on screen"], ["Checking forecasts", "Offline, by the author", "Actual closes and forecast miss shown for each day since the forecast date"],
             ["News handling", "Daily average score, or bags in MIL research systems", "Daily average score in the product; bags only in the offline study"],
             ["Testing", "Seldom described", f"{F.PYTEST_PASSED} unit/API tests, {F.SMOKE_PASSED} smoke checks"]],
            widths=[1.4, 2.4, 2.7], align=["l", "l", "l"], size=9.5),
        H2("4.12 Constraints and Assumptions"),
        P("The system is constrained by the availability and quality of free data (Yahoo Finance prices, a month of live news or synthetic headlines), by CPU-only training, by a two-year price history that gives "
          "about 400 training rows per ticker, and by the absence of a social-media source. It assumes that daily bars are complete, that a chronological split approximates deployment, and that users understand the "
          "forecasts are statistical estimates for research and education and not financial advice."),
    ]
