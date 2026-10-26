"""Chapter 5: System Design for QuantPulse.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
The diagram explanations come from diagram_index.DIAGRAMS so that the chapter, the Block Diagrams document and the decks never disagree.
"""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_IDX = {d[0]: d for d in DIAGRAMS}


def dg(key, width=5.4, extra=None, para=False):
    """Figure for one diagram, optionally with the long index paragraph (which also appears in the Block Diagrams document) and extra paragraphs."""
    _, _title, fname, caption, text = _IDX[key]
    out = [FIG(F.diag(fname), caption, width)]
    if para:
        out.append(P(text))
    for e in extra or []:
        out.append(P(e))
    return out


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    rr = F.RR
    out = [
        H1("5. SYSTEM DESIGN"),
        P("This chapter describes how QuantPulse is built: the architecture and workflow, the data flow, the module, sequence and use-case design, the data design, the three core algorithms, "
          "the module and API design and the user interface. Every diagram was drawn from the code in `backend/` and `frontend/src/` and is reproduced with an explanation; the full set is also collected in the Block Diagrams document. "
          "Two facts about the design are stated at the outset because they shape everything below. QuantPulse has **no database and no authentication**: all state is files, and the website is open. "
          "And it has **no multiple-instance-learning component**: news enters the model as one averaged sentiment number per trading day, so the design follows the base paper "
          f"[{R['base']}] rather than the multiple-instance formulation that the project title and objectives describe. The offline study that addresses that formulation is a separate script, described in Chapter 6."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **reproduce the base paper's pipeline as a usable product**: ARIMA, SARIMAX, Prophet, Random Forest and SVR baselines, an LSTM, a multi-head-attention LSTM, a sentiment channel from FinBERT-tone headlines and a simulated federated-averaging stage, "
          f"all on ten technology and logistics tickers [{R['base']}]. Second, **fast screens**: training takes minutes on a CPU, so it is run offline once and the web tier serves stored JSON, which is why most endpoints answer in about ten milliseconds (Chapter 7). "
          "Third, **say where the data came from**: every ticker carries a mode label (live, csv or synthetic), the sentiment source is shown on its own screen, and the Forecast screen warns when the stored forecast starts before the newest price. "
          "Fourth, **run on a laptop without a GPU**, which fixed the choice of CPU TensorFlow, PyTorch for FinBERT inference only, and small networks. Fifth, **keep it replaceable**: every hyper-parameter is in `config.py`, and the ticker universe is an environment variable."),
    ] + dg("arch", 5.4, para=True, extra=[
        f"Ports are fixed by the batch: the API listens on 127.0.0.1:{a} and the website on {w}. Cross-origin calls from the localhost origins on ports 5173, 5404, 8000 and 8404 (and from 127.0.0.1 on 5173 and 5404) are allowed, so the Vite development server, the prebuilt site and the Docker image all work. "
        "The pipeline modules contain no web code, and `main.py` contains no model code: it never loads the saved Keras files, it only reads `artifacts/metrics.json` and `forecasts.json`. "
        "The Keras models and scalers are written by training so that a forecast could be regenerated, but nothing in the running application uses them."]) + [

        H2("5.2 High-Level Workflow"),
    ] + dg("flow", 5.4, para=True, extra=[
        "The workflow has two time scales. The training pipeline is a command-line program, `python -m backend.train`, which takes five to ten minutes on a CPU and writes everything the website shows. "
        "The serving path is a few lines of FastAPI. The only operations that leave the machine at run time are the history call, which re-downloads prices from Yahoo Finance, and the first sentiment call, which loads the FinBERT-tone model from the Hugging Face cache."]) + [

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
    ] + dg("dfd0", 4.6, [
        "At level 0 the product is one process with three kinds of neighbour: the trader or analyst (browser), the evaluator or developer (scripts and tests) and three external services (Yahoo Finance, NewsAPI and the Hugging Face hub for FinBERT-tone)."]) + [
        H3("5.3.2 Level 1: seven processes"),
    ] + dg("dfd1", 5.0, para=True, extra=[
        "Processes 1.0 to 6.0 are one offline script (acquire prices, score sentiment, fit baselines, train deep tiers, average federatedly, forecast and write artefacts); process 7.0 is the FastAPI application. "
        "The three stores are files: D1 `data/<T>.csv`, D2 `data/news_cache/` (only with a NewsAPI key) and D3 `artifacts/`."]) + [
        H3("5.3.3 Level 2: training one deep tier"),
    ] + dg("dfd2", 5.0, [
        "Level 2 expands the training of one deep tier into seven steps. Step 4.2 carries the design's most consequential choice: the scalers are fitted on the first 80 % of the rows but applied to every row and clipped to [0, 1], so a test price above the training maximum is flattened to 1.0 (Chapter 8 shows this matters)."]) + [

        H2("5.4 Module, Sequence and Use-Case Design"),
        H3("5.4.1 Module (class) diagram"),
    ] + dg("uml", 5.0, para=True, extra=[
        "The backend is deliberately a set of function modules, each small and testable on its own (the tests in `tests/` call the functions directly); the only true classes are the front end's `ApiError` and the FastAPI application object."]) + [
        TAB("Backend modules and their roles.",
            ["Module", "File", "Role", "Main functions"],
            [["Configuration", "backend/app/config.py", "Tickers, window, split, batch, epochs, units, heads, horizons, paths, NewsAPI key", "`get_tickers`"],
             ["Price source", "backend/app/data_loader.py", "Live Yahoo download, bundled CSV, labelled synthetic series", "`load_ticker`, `load_universe`, `_synthetic_series`"],
             ["Sentiment", "backend/app/sentiment.py", "NewsAPI fetch and cache, FinBERT-tone or lexicon scoring, synthetic headlines, daily alignment", "`get_daily_sentiment`, `score_headlines`, `recent_headlines`"],
             ["Baselines", "backend/app/baselines.py", "ARIMA, SARIMAX, Prophet, Random Forest, SVR with one metric helper", "`run_all`, `_metrics`"],
             ["Deep models", "backend/app/models_dl.py", "Windows, scalers, two Keras architectures, training, evaluation", "`make_windows`, `build_lstm`, `build_attention_lstm`, `evaluate_dl`"],
             ["Federated", "backend/app/federated.py", "Manual FedAvg over per-ticker clients", "`fedavg`, `run_federated`"],
             ["Forecast", "backend/app/forecast.py", "Recursive multi-step forecast with confidence band", "`recursive_forecast`"],
             ["API", "backend/app/main.py", "Seven JSON routes, static site, validation", "`_check_ticker`, `forecast`, `history`"],
             ["Training script", "backend/train.py", "Runs the whole pipeline and writes artefacts and plots", "`train_ticker`, `main`"]],
            widths=[1.0, 1.6, 2.2, 1.7], align=["l", "l", "l", "l"], size=9.0),
        H3("5.4.2 Sequence diagram"),
    ] + dg("seq", 4.6, para=True, extra=[
        "Opening the Forecast screen triggers `/api/tickers`, then `/api/forecast` and `/api/history` together; the history call goes live to Yahoo Finance and rewrites the price CSV, so it is the slowest of the three."]) + [
        H3("5.4.3 Use-case diagram"),
    ] + dg("uc", 4.4, [
        "There is one human role, the trader or analyst, who needs no login, and one technical role, the evaluator or developer; no administrator exists because there is no authentication."]) + [

        H2("5.5 Data Design"),
    ] + dg("er", 4.6, [
        "There is no database, so the entities are rows inside CSV and JSON files and the diagram is logical. The shape of `artifacts/metrics.json` is the de facto schema of the product; the table lists the parts of one ticker's record."]) + [
        TAB("Contents of one ticker's record in artifacts/metrics.json.",
            ["Field", "Content", "Written by"],
            [["`mode`, `n_rows`", "Price source (live, csv, synthetic) and number of daily rows used (501 for every ticker in the shipped run)", "`train_ticker`"],
             ["`baselines`", "ARIMA, SARIMAX, Prophet, Random Forest, SVR: MAE, MSE, RMSE, R2, directional accuracy, n_test (101)", "`baselines.run_all`"],
             ["`sentiment`", "Source (newsapi or synthetic-fallback), scorer (finbert, lexicon), headline count (166 to 191), note", "`get_daily_sentiment`"],
             ["`deep`", "Four tiers with the same metric set and n_test = 97", "`train_ticker`, `main`"],
             ["`histories`", "Training and validation loss per epoch for three local tiers", "`train_model`"],
             ["`forecast_short`, `forecast_long`", "5 and 30 rows: day, predicted close, lower, upper", "`recursive_forecast`"],
             ["`last_close`, `trend`", "Last training close and up/down flag (day-5 forecast against last close)", "`main`"],
             ["`headlines`", "Eight headlines with their scores for the sentiment screen", "`recent_headlines`"],
             ["`federated_rounds`", "Mean local loss for round 1 and 2 (same for every ticker)", "`run_federated`"]],
            widths=[1.5, 3.9, 1.2], align=["l", "l", "l"], size=9.0),
        P("Price files are CSV with a date index and the columns Open, High, Low, Close, Adj Close and Volume (a synthetic file starts with `# synthetic: true`); the Keras files and scalers in `artifacts/serving/` are saved per ticker. The API loads each JSON file once and keeps it in memory until restart."),

        H2("5.6 Core Algorithm Design"),
        P("Three algorithms carry the product and each has a flowchart; they are derived formally in Chapter 6."),
        H3("5.6.1 Recursive forecast"),
    ] + dg("flow_core", 4.4, [
        "Each step feeds the prediction back as the next Close (and Open, High, Low) with volume and sentiment held constant, so after day one the forecast is driven by the model's own outputs; the band widens with the square root of the horizon."]) + [
        H3("5.6.2 Sentiment path"),
    ] + dg("flow_sent", 4.6, [
        f"No key was configured in the shipped run, so every ticker used the synthetic path: 166 to 191 headlines per ticker from eleven fixed templates, which say nothing about real news. The screen labels this; the base paper's own NewsAPI limit of one month [{R['base']}] is why live responses are cached per day."]) + [
        H3("5.6.3 Network architecture"),
    ] + dg("model", 5.2) + [

        H2("5.7 Module Design of the Website"),
        P("The website is a single-page React 19 application (Vite 8, React Router 7, Recharts 3, Framer Motion) on the \"Soft Pastel Calm\" kit, with six lazily loaded screens; each asks the API through one hook and renders loading, error, empty and data states."),
        TAB("Website modules.",
            ["Module", "File(s)", "Role"],
            [["Router and shell", "`App.jsx`, `components/ui/Layout.jsx`", "Routes `/` (landing) and `/app/*`; sidebar, top bar with the API status pill, theme toggle"],
             ["Landing", "`pages/Landing.jsx`", "Hero with a live price chart of the first ticker, feature sections, call to action"],
             ["Dashboard", "`pages/Dashboard.jsx`", "Four KPI cards, ten ticker cards with sparklines, sortable universe table"],
             ["Forecast", "`pages/Forecast.jsx`", "Ticker tabs, horizon and history selectors, KPIs, chart with band, forecast table with actual closes, stale-model banner"],
             ["Model comparison", "`pages/Models.jsx`", "KPIs, ablation chart, all-model MAE chart, deep and baseline tables, loss curves, federated rounds"],
             ["News sentiment", "`pages/Sentiment.jsx`", "Source, headline count, 30-day mean, daily chart, searchable headline list with tone filter"],
             ["Method and data", "`pages/About.jsx`", "Pipeline timeline, installation facts from the API, data table per ticker"],
             ["API client", "`lib/api.js`", "`fetch` wrapper with a 30 s timeout (240 s for sentiment), abort support and `ApiError`"],
             ["Hooks and helpers", "`lib/hooks.js`, `market.js`, `format.js`, `palette.js`, `theme.jsx`", "`useAsync`, `useRefresh`, model labels, `buildSeries` (aligns forecast and history), number and date formats, light and dark tokens"],
             ["UI kit and charts", "`components/ui/*`, `components/charts/index.jsx`", "Buttons, cards, tables, tabs, toasts, skeletons; area, bar, line, grouped-bar and forecast charts with accessible labels"]],
            widths=[1.3, 2.2, 3.1], align=["l", "l", "l"], size=9.0),
        P("The most delicate front-end logic is `buildSeries`: the stored forecast starts from the last training close, which can be older than the live history, so the function anchors the forecast on the history row with that close, lays it on the following business days and adds the actual close and percentage miss for every forecast day that has already happened. If no row matches it shows the stale warning."),

        H2("5.8 API Design"),
        P("The API is read-only JSON: seven routes under `/api`, with the same process serving the built website. Request and response shapes are in Chapter 6."),
        TAB("API routes.",
            ["Route", "Purpose", "Errors"],
            [["`GET /api/health`", "Readiness, tickers, whether artefacts exist, news source", "none"],
             ["`GET /api/tickers`", "Universe with last close, trend and data mode", "none"],
             ["`GET /api/metrics`", "All records", "503 when not trained"],
             ["`GET /api/metrics/{ticker}`", "One record", "400 invalid symbol, 404 unknown"],
             ["`GET /api/forecast/{ticker}?horizon=`", "5 or 30 forecast rows", "400, 404, 422 bad horizon"],
             ["`GET /api/sentiment/{ticker}`", "Meta, 30 daily scores, headlines", "400"],
             ["`GET /api/history/{ticker}?days=`", "OHLCV rows and forecast overlay", "400, 422 days outside 20 to 500"]],
            widths=[2.4, 2.7, 1.5], align=["l", "l", "l"], size=9.0),

        H2("5.9 User Interface Design"),
        P("Four rules guide the interface. **Calm and legible**: warm off-white surfaces, pastel tones by category (lavender deep models, blue baselines, mint positive, rose negative) and tabular figures. **Honest states**: skeletons, error states with retry, empty states and an \"API online, models ready\" pill. "
          "**Accessible**: charts carry an `aria-label`, tabs and segmented controls use tab and radio roles, and motion respects reduced-motion. **Two themes** share the same tokens; the choice is stored in the browser."),
        PAIR([(F.shot("01_landing_light.png"), "Landing page in the light theme."), (F.shot("02_landing_dark.png"), "Landing page in the dark theme.")], 3.0),
        TAB("Screens and their data sources.",
            ["Screen", "Route", "API calls", "What the user can do"],
            [["Landing", "/", "tickers, metrics, history (first ticker, 250 days)", "Read the pitch, open the app"],
             ["Dashboard", "/app", "tickers, metrics", "Scan ten tickers, sort the table, open a forecast"],
             ["Forecast", "/app/forecast", "tickers, then forecast and history together", "Pick ticker, 5- or 30-day horizon, 60 to 250 days of history; read the table with actual closes"],
             ["Model comparison", "/app/models", "tickers, metrics/{t}", "Compare nine models, see loss curves and federated rounds"],
             ["News sentiment", "/app/sentiment", "tickers, sentiment/{t}", "See source and daily mood, search and filter headlines"],
             ["Method and data", "/app/about", "health, metrics", "Read the pipeline and per-ticker data modes"]],
            widths=[1.2, 1.1, 2.0, 2.3], align=["l", "l", "l", "l"], size=9.0),

        H2("5.10 Design Trade-offs and Known Weaknesses"),
        B("**Precomputed artefacts keep the site fast but go stale:** the shipped ones end at 2026-09-08; the Forecast screen says so, only retraining fixes it.",
          "**The history route downloads on every call:** the chart stays current at about 140 ms per call (Chapter 7) and depends on Yahoo Finance being reachable.",
          "**Function modules share a few module-level caches** (the FinBERT pipeline, two JSON caches) that would need a lock under heavy concurrency.",
          "**No authentication and no database:** the API is read-only with no personal data and files suffice for ten tickers; watch-lists or forecast history would need both.",
          "**Simulated federated learning:** the clients share one process and one scaling convention; a real deployment would need transport, secure aggregation and per-client scaling."),
    ]
    return out
