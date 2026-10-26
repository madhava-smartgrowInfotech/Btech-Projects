"""Index of the QuantPulse design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs/make_diagrams.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document (11), the full report, the decks and the paper.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of QuantPulse: React website, FastAPI application with seven JSON endpoints, pipeline modules, and JSON / CSV / Keras files, with three external services.",
     "The browser tier is a React 19 and Vite single-page website on port 5404 with six screens; its api.js client calls the backend under /api and Vite proxies the calls in development. "
     "The FastAPI application on port 8404 offers seven JSON endpoints (health, tickers, metrics, per-ticker metrics, forecast, sentiment and history) and also serves the built website with an index.html fallback. "
     "Underneath, the pipeline modules config, data_loader, sentiment, baselines, models_dl, federated and forecast are imported by main.py and by the offline training script train.py. "
     "State lives only in files: artifacts/ (metrics, forecasts, Keras models, plots), data/ (price CSVs) and data/news_cache/. "
     "Yahoo Finance, the optional NewsAPI service and the Hugging Face hub (FinBERT-tone weights) are outside the system. "
     "QuantPulse has no database, no authentication and no multiple-instance-learning component."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "Offline training pipeline (python -m backend.train) in two stages, then serving of the JSON artefacts to the website.",
     "Stage 1 runs once per ticker for the ten tickers in turn. The prices are loaded from Yahoo Finance, the bundled CSV or a labelled synthetic series; five classical baselines are scored on an 80/20 chronological split; daily sentiment is built from headlines scored by FinBERT-tone; "
     "and three deep tiers (LSTM, LSTM with four-head attention, and the same network with a sentiment channel) are trained on 20-day windows scaled to [0, 1]. The recursive 5- and 30-day forecasts come from the third tier. "
     "Stage 2 starts after all tickers are done: the third-tier network is averaged across the ten tickers by FedAvg, scored on each ticker, and its 5-day forecast replaces the local one; the results are written to metrics.json, forecasts.json, the serving models and the plots. "
     "At run time the API reads only the JSON files, except that the history and sentiment endpoints go back to Yahoo Finance and FinBERT. News enters only as one daily sentiment number, so the workflow has no database, no login and no multiple-instance stage."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0): one process, the trader or analyst, the evaluator or developer, and three external data sources.",
     "At level 0 the whole product is a single process. The trader or analyst sends a ticker, a horizon and a history length from the browser and receives the last close, the trend, the 5- and 30-day forecasts with their bands, the model metrics, the sentiment series and the price history with the forecast overlay. "
     "The evaluator or developer supplies the training command, the tests and the .env settings and receives metrics.json, plots, test logs and screenshots. "
     "Yahoo Finance supplies daily OHLCV data for the ten tickers, NewsAPI supplies headlines when a key is configured, and the Hugging Face hub supplies the FinBERT-tone weights and tokenizer. "
     "The boundary contains no database, no login and no MIL component."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: seven processes (acquire prices, score sentiment, fit baselines, train deep tiers, federated averaging, forecast and write artefacts, serve) and three data stores.",
     "Process 1.0 downloads prices and writes them to the CSV files (D1); the close series goes to the baselines (3.0) and the OHLCV frame goes to the deep-tier training (4.0). Process 2.0 reads the trading dates, fetches or generates headlines (cached in D2), scores them with FinBERT-tone and hands a daily sentiment series to 4.0. "
     "Process 4.0 passes its trained models and client data to the federated averaging (5.0) and its metrics, loss histories and last 20-day windows to process 6.0. Process 6.0 combines baseline metrics, tier metrics and the global model, makes the recursive forecasts and writes the artefacts (D3). "
     "Process 7.0, the FastAPI application and website, reads D3 for the trader and goes to Yahoo Finance on every history request. Processes 1.0 to 6.0 run offline; only 7.0 faces the browser."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: process 4.0, training of one deep tier, expanded into seven sub-processes.",
     "Process 4.1 builds the feature matrix from the five OHLCV columns and, for the third tier only, the daily sentiment column. Process 4.2 fits one Min-Max scaler per column on the first 80 % of the rows and scales and clips every row to [0, 1]. "
     "Process 4.3 turns the matrix into 20-day windows whose target is the next day's close, and process 4.4 splits the windows 80/20 in time and builds the Keras model. Process 4.5 trains with Adam, batch size 32, at most 50 epochs, early stopping with patience 7 and a 15 % validation split. "
     "Process 4.6 inverse-scales the test predictions and computes MAE, MSE, RMSE, R2 and directional accuracy, and process 4.7 keeps the model, the loss history and the residual standard deviation for the forecast and the artefact files. "
     "The stage runs three times per ticker, once per tier."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: the backend is a set of function modules, so modules are drawn as boxes with their functions, together with the React API client, ApiError and the useAsync hook.",
     "QuantPulse is written mostly as modules of functions, so the diagram draws each module as a box listing its constants and functions. The entry script train.py imports every module under backend/app; main.py, the FastAPI application, imports config, data_loader and sentiment and reads the artefact JSON through a cached loader. "
     "config holds the ticker list and hyper-parameters, data_loader the three-step price source, sentiment the NewsAPI, FinBERT and synthetic-headline logic, baselines the five classical models, models_dl the windowing, scaling, the two Keras architectures, training and evaluation, "
     "federated the manual FedAvg loop and forecast the recursive forecast with its confidence band. On the browser side the api object wraps fetch with a timeout and raises ApiError; useAsync is the hook the screens use to call it. The only genuine classes are ApiError and the FastAPI application object."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_flow.png",
     "Sequence diagram: the user opens the Forecast screen; the page calls /api/tickers, then /api/forecast and /api/history in parallel; history goes live to Yahoo Finance.",
     "Opening /app/forecast makes the React page call GET /api/tickers; main.py loads artifacts/metrics.json once, caches it and returns each ticker's last close, trend and data mode. "
     "The page then starts two requests together. GET /api/forecast/TSLA?horizon=short looks up the stored five forecast rows. GET /api/history/TSLA?days=250 calls load_ticker, which downloads two years of daily prices from Yahoo Finance, rewrites data/TSLA.csv and returns the latest 250 rows together with the stored forecast placed on the next business days. "
     "The page draws the actual closes, the dashed forecast and the confidence band, and the table shows the actual close once it exists. No request carries credentials, and the history call costs one Yahoo Finance download every time."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with the trader or analyst, the evaluator or developer, and three external services.",
     "The trader or analyst uses the website without logging in: viewing the dashboard of ten tickers, opening the 5-day or 30-day forecast with its confidence band, comparing the models (ablation chart, baselines and loss curves), inspecting the news sentiment and headlines, reading the method and data screen and switching between light and dark themes. "
     "The evaluator or developer retrains the pipeline with python -m backend.train and runs the pytest and smoke tests, which import the same modules. Yahoo Finance supplies prices for the forecast and history use cases, NewsAPI supplies headlines when a key is set, and the Hugging Face hub supplies the FinBERT-tone weights for the sentiment use case. "
     "There is no administrator or account because the application has no authentication."),
    ("er", "Entity-relationship diagram (logical)", "09_er_diagram.png",
     "Logical entity-relationship diagram: QuantPulse has no database, so the entities are rows inside CSV and JSON files.",
     "A Ticker (symbol, data mode, row count, last close, trend) has many PriceBar rows (OHLCV and adjusted close) stored in data/<T>.csv, many Headline rows (from NewsAPI or the synthetic generator, each with a sentiment score) that are averaged per date into DailySentiment, "
     "many MetricRecord rows (one per model with MAE, MSE, RMSE, R2, directional accuracy and the number of test windows) and many ForecastRow rows (day, predicted close, lower and upper band) for the short and long horizons. "
     "A ModelTier (five classical baselines or four deep tiers) has many MetricRecord rows, and the two federated rounds with their mean local loss are copied into every ticker's record. The ArtifactFile entity lists the files that hold all of it. "
     "No foreign keys exist; the relations are shared ticker and date keys, and the diagram is logical for that reason."),
    ("flow_core", "Forecast flowchart", "10_flowchart_forecast.png",
     "Flowchart of recursive_forecast: predict, roll the window, repeat, inverse-scale, add the 1.96 x residual std x sqrt(h) band and set the trend.",
     "The function starts from the last 20 scaled rows. For each step it predicts the next scaled close, appends it, builds the next row by copying the last row and setting Close (and Open, High and Low) to the prediction while volume and sentiment are carried forward, and slides the window by one day. "
     "After 5 steps (short) or 30 steps (long) the scaled predictions are inverse-transformed to dollars. The band for horizon h is 1.96 times the residual standard deviation of the test errors times the square root of h, with the lower edge floored at 0.01. "
     "Each row holds the day, the predicted close and the two band edges, and the trend flag is up when the fifth-day prediction is at least the last close."),
    ("flow_sent", "Sentiment flowchart", "11_flowchart_sentiment.png",
     "Flowchart of get_daily_sentiment: live NewsAPI headlines or the labelled synthetic fallback, FinBERT-tone or lexicon scoring, and alignment to the trading dates.",
     "If a NEWSAPI_KEY is set and articles are returned (or found in the per-day cache), up to 50 titles of the last 30 days are scored; otherwise the generator writes one to three template headlines for each of the last 90 trading dates (45 % positive, 25 % neutral, 30 % negative) and the source is labelled synthetic-fallback. "
     "FinBERT-tone turns each headline into a signed probability (positive plus, negative minus, neutral zero); if the model cannot be loaded a word-list lexicon is used instead and the scorer is reported as lexicon. "
     "The scores are averaged per calendar date, aligned to the trading dates (days without a headline are empty), forward-filled, set to zero before the first headline and clipped to [-1, 1]. The result is the single extra column of the sentiment tier."),
    ("model", "Model architecture", "12_model_architecture.png",
     "Architecture of the two network families (LSTM, and LSTM with four-head attention) and of the simulated FedAvg stage.",
     "The baseline LSTM tier feeds a 20-day window of Open, High, Low, Close and Volume through LSTM(64), batch normalisation, dropout 0.2 and one dense output for the next close. "
     "The attention tier keeps the full LSTM sequence, applies four-head self-attention (key size 16), adds it back to the sequence, normalises, averages over time and passes the result through a 32-unit dense layer, dropout and the output; the sentiment variant has the same layers with a sixth input column. "
     "The federated stage treats each of the ten tickers as a client holding a copy of the attention and sentiment network: for two rounds every client trains three local epochs from the global weights and the server averages the weights in proportion to the number of training windows. "
     "All tiers use Adam with learning rate 1e-3, mean squared error, batch size 32, up to 50 epochs and early stopping."),
]
