"""Chapter 6: Methodology and Software Implementation for QuantPulse.

methodology_blocks() is also rendered (renumbered) by document 9, application_blocks() by document 12; blocks() is the report chapter.
Hyper-parameters are exactly those of backend/app/config.py, models_dl.py, federated.py and forecast.py; study numbers come from facts.py.
"""

import numpy as np

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_IDX = {d[0]: d for d in DIAGRAMS}


def c(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def _fig(key, width):
    d = _IDX[key]
    return FIG(F.diag(d[2]), d[3], width)


def _api_example():
    import json

    t = F.SHIP["TSLA"]
    body = json.dumps({"ticker": "TSLA", "horizon": "short", "last_close": t["last_close"], "trend": t["trend"], "forecast": t["forecast_short"][:2] + ["..."]})
    return ("GET /api/forecast/TSLA?horizon=short\n" + body + "\n\n"
            "GET /api/forecast/T5LA                -> 400 {\"detail\": \"Invalid ticker 'T5LA'. Use 1-6 letters, e.g. TSLA.\"}\n"
            "GET /api/forecast/ZZZZ                -> 404 {\"detail\": \"No forecast for 'ZZZZ'. Train the pipeline first.\"}\n"
            "GET /api/forecast/TSLA?horizon=weekly -> 422 (query validation)")


def methodology_blocks():
    mil = F.MIL
    rr = F.RR
    epochs = {k: np.mean([m["epochs"] for t in F.TICKERS for m in rr["tickers"][t]["models"][k]]) for k in ("lstm", "lstm_attention", "lstm_attention_sentiment")}
    per_run = rr["seconds"] / (len(rr["seeds"]) * len(F.TICKERS))
    nh = [F.SHIP[t]["sentiment"]["n_headlines"] for t in F.TICKERS]
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall Methodology"),
          P("QuantPulse is built as one pipeline with two phases. The **offline phase** (`python -m backend.train`) loads daily prices for ten tickers, scores five classical baselines, builds a daily sentiment series from headlines, "
            "trains three deep-model tiers on 20-day windows, averages the sentiment-tier network across the ten tickers with federated averaging, writes the 5- and 30-day recursive forecasts and stores every metric in JSON. "
            "The **online phase** is a FastAPI service and a React website that read those files and, for the price chart and the sentiment screen, fetch fresh prices and score headlines on demand. "
            f"The design is that of the base paper {c('base')}; the intent of the project title, a multiple-instance treatment of daily news, is addressed by a separate offline study (Section 6.7) and is not part of the application. The method has eight steps:"),
          N("**Acquire prices** from Yahoo Finance, with a bundled CSV and a labelled synthetic series as fall-backs.",
            "**Build sentiment:** NewsAPI headlines if a key is set, otherwise template headlines for the last 90 trading days, scored by FinBERT-tone and averaged per day.",
            "**Score the classical baselines** on an 80/20 chronological split.",
            "**Window and scale:** 20-day windows, Min-Max scaled to [0, 1] with scalers fitted on the first 80 % of the rows.",
            "**Train three deep tiers** (LSTM, attention, attention with sentiment): Adam, batch 32, up to 50 epochs, early stopping.",
            "**Average federatedly:** ten clients, two rounds of three local epochs, weights averaged by client size.",
            "**Forecast** 5 and 30 days recursively with a 95 % band and an up or down flag.",
            "**Serve and display** through seven JSON routes and six screens.")]
    b.append(_fig("flow", 5.4))

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          P(f"**Prices.** The ten tickers are TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM and ORCL, the base paper's universe with Airbnb replaced by Meta [{R['base']}]. The loader asks `yfinance` for two years of daily bars [{R['yahoo']}]; "
            "the shipped artefacts were trained on **501 rows per ticker, 2024-09-09 to 2026-09-08**, all with mode `live`. If the download fails the loader reuses `data/<T>.csv`, and if that is missing it generates a geometric-Brownian-motion series with regime shifts and volatility clustering, saved with a `# synthetic: true` header. "
            "Every record carries its mode so that a synthetic series can never be mistaken for a real one. The application overwrites the CSV on each live pull, so the documentation experiments use a pinned snapshot, `experiments/data_snapshot/`, whose rows up to 2026-09-08 reproduce the stored last closes."),
          P(f"**News in the product.** No `NEWSAPI_KEY` was set, so all ten tickers used the built-in fallback: {min(nh)} to {max(nh)} headlines per ticker (about 1 to 3 per day for the last 90 trading days) generated from eleven fixed templates, 45 % positive, 25 % neutral and 30 % negative in expectation, and then scored by FinBERT-tone [{R['finbert_tone']}]. "
            "These headlines carry no information about the real market. The free NewsAPI tier returns only about a month of history [" + str(R['newsapi']) + "], which is why the base paper's sentiment experiments are limited to 30 days."),
          P(f"**Real news for the offline study.** The multiple-instance study uses the news portion of FNSPID [{R['fnspid']}], read from a public mirror: {mil['instances']['n_headline_rows_used']:,} headline rows for seven tickers (AAPL, AMZN, FDX, MSFT, NVDA, ORCL, TSLA), "
            f"of which {mil['instances']['per_year'].get('2022', 0) + mil['instances']['per_year'].get('2023', 0):,} fall in 2022 and 2023; GOOGL and META have no headlines in this portion and IBM has seven. All rows carry day-level time stamps. "
            "Each article is tagged with every company it mentions, so a bag holds headlines only loosely about the ticker, the situation multiple-instance learning is meant for. Prices for this study are Yahoo Finance 2016 to 2023."),
          TAB("Datasets used and their roles.",
              ["Data", "Source", "Size", "Role"],
              [["Daily prices (product)", "Yahoo Finance via yfinance", "10 tickers x 501 rows", "Training and serving"],
               ["Price snapshot", "Same, pinned 2024-09-09 to 2026-10-23", "10 x 534 rows", "Re-runs, forward test"],
               ["Synthetic headlines", "Eleven templates (sentiment.py)", f"{min(nh)} to {max(nh)} per ticker", "Sentiment channel of the product"],
               ["Real headlines", f"FNSPID news {c('fnspid')}", f"{mil['instances']['n_headline_rows_used']:,} rows, 7 tickers", "Offline multiple-instance study"],
               ["Prices for the study", "Yahoo Finance 2016 to 2023", "7 tickers, about 2,000 days each", "Labels and price features"]],
              widths=[1.5, 2.2, 1.7, 1.4], align=["l", "l", "l", "l"], size=9.0)]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing"),
          P("Preprocessing is deliberately small and is the same for every deep tier. The feature matrix has the columns Open, High, Low, Close and Volume, plus the daily sentiment score for the third tier. "
            "Each column is scaled separately with `MinMaxScaler`, fitted on the **first 80 % of the rows** (400 of 501) and applied to all rows, with the result clipped to [0, 1]. Sliding windows of 20 trading days are cut from the scaled matrix; the target of a window is the Close of the day after it. "
            "The 481 windows are split chronologically 80/20 into 384 training and 97 test windows, and the training windows are further divided by Keras with a 15 % validation split taken from their end (326 / 58). The test period is therefore the last 97 trading days of the two-year series."),
          P("Three properties of this preprocessing matter for the results. First, the scaler never sees the test period, which avoids leakage, but the clip means that any test price above the training maximum becomes exactly 1.0; "
            "in the pinned data this affects 56 to 82 % of the test closes of AAPL, AMZN, GOOGL, NVDA and FDX. Second, the target is the next close itself rather than its change, so a model that merely repeats the last input already scores well on level errors. "
            "Third, **sentiment alignment** averages the headline scores per calendar date, places them on the trading dates, forward-fills the gaps and sets days before the first headline to zero; because the generator writes headlines only for the last 90 trading days, the channel is exactly zero for every training window and non-zero only in the test part."),
          P("Baselines are preprocessed differently, as in the base paper: ARIMA, SARIMAX and Prophet fit the close series on the first 80 % and forecast the whole remaining span without refitting; Random Forest and SVR use the previous 20 closes and predict one step ahead from actual lagged values. Headline scores are signed probabilities: +p, -p or 0 for positive, negative or neutral.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Algorithm Choice and Justification"),
          P("Each model in the pipeline answers a specific question, and the table records why it was chosen and what the measurements of Chapter 8 showed about it."),
          TAB("Algorithms, the reason for each and what was observed.",
              ["Algorithm", "Role", "Reason for choosing it", "What the measurements show"],
              [[f"ARIMA(5,1,0), SARIMAX {c('box')}", "Statistical baseline", "Standard linear time-series models, in the base paper", f"Mean MAE ${F.SUM['models']['arima']['mae']['mean']:.2f} and ${F.SUM['models']['sarimax']['mae']['mean']:.2f}; multi-step forecast without refit"],
               [f"Prophet {c('prophet')}", "Decomposable baseline", "Trend and seasonality model in the base paper", f"Worst model: mean MAE ${F.SUM['models']['prophet']['mae']['mean']:.2f}"],
               [f"Random Forest, SVR {c('rf', 'svr')}", "Machine-learning baselines", "Non-linear regressors on lagged closes", f"Random Forest lowest MAE on 6 of 10 tickers (mean ${F.SUM['models']['random_forest']['mae']['mean']:.2f})"],
               [f"LSTM {c('lstm')}", "Sequence model", "Captures temporal dependence in the price window", f"Mean MAE ${F.SUM['models']['lstm']['mae']['mean']:.2f} (shipped scoring)"],
               [f"Multi-head attention {c('transformer')}", "Weights the time steps of the window", "Base paper adds it to the LSTM to model long-range dependence", f"Best deep tier, mean MAE ${F.SUM['models']['lstm_attention']['mae']['mean']:.2f}"],
               [f"FinBERT-tone {c('finbert_tone', 'finbert')}", "Headline sentiment", "Pretrained on financial text, inference only, no labels needed", "Works as a scorer; the channel it feeds is synthetic and empty during training"],
               [f"FedAvg {c('fedavg')}", "Simulated decentralised training", "Base paper's privacy argument; one client per ticker", f"Worse than local tiers (mean MAE ${F.SUM['models']['hybrid_federated']['mae']['mean']:.2f})"],
               [f"Gated-attention MIL {c('ilse', 'dietterich')}", "Bag-level news model (offline study)", "Only the day's outcome labels a bag of headlines, as the title requires", "No gain over price-only on 1,309 test samples"]],
              widths=[1.4, 1.2, 2.0, 2.0], align=["l", "l", "l", "l"], size=8.5),
          P("The **LSTM with attention** was kept because it is the base paper's architecture and the tier comparison is the paper's ablation, not because it is expected to beat a persistence forecast. **FinBERT-tone in inference mode** was chosen because no labelled headlines exist for the ten tickers; the cost is a download of several hundred megabytes on first use.")]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Mathematical Formulation"),
          H3("6.5.1 Windows and scaling"),
          P("Let x_t be the vector of the five price columns (and the sentiment score) on trading day t. Each column j is scaled with the minimum and maximum of its first 80 % of rows, and the input window and target are"),
          EQ("x̃_t,j = clip((x_t,j − min_j) / (max_j − min_j), 0, 1),   X_t = [x̃_(t−20), …, x̃_(t−1)],   y_t = x̃_t,Close"),
          H3("6.5.2 LSTM cell"),
          P(f"The recurrent layer is the standard LSTM {c('lstm')} with 64 units. With σ the logistic function and ⊙ the element-wise product, at each step"),
          EQ("f_t = σ(W_f[h_(t−1), x_t] + b_f),   i_t = σ(W_i[h_(t−1), x_t] + b_i),   o_t = σ(W_o[h_(t−1), x_t] + b_o)"),
          EQ("C̃_t = tanh(W_C[h_(t−1), x_t] + b_C),   C_t = f_t ⊙ C_(t−1) + i_t ⊙ C̃_t,   h_t = o_t ⊙ tanh(C_t)"),
          H3("6.5.3 Multi-head attention"),
          P(f"The attention tier keeps the whole LSTM sequence H = [h_1, …, h_20] and applies four-head self-attention {c('transformer')} with key size 16, adds the result back (residual connection), normalises and averages over time:"),
          EQ("Attention(Q, K, V) = softmax(Q Kᵀ / √d_k) V,   Z = LayerNorm(H + MultiHead(H, H, H)),   z̄ = (1/20) Σ_t Z_t"),
          P("The vector z̄ passes through a 32-unit ReLU layer, dropout 0.2 and one linear output."),
          H3("6.5.4 Daily sentiment"),
          P("For ticker k and date d, let S_(k,d) be the set of headlines. FinBERT-tone returns a label and a probability p for each headline, and the headline score is s = +p for positive, −p for negative and 0 for neutral. The daily value is the mean, forward-filled and clipped:"),
          EQ("σ_(k,d) = clip( mean_(h ∈ S_(k,d)) s_h , −1, 1 ),   σ_(k,d) = σ_(k,d−1) if S_(k,d) = ∅,   σ = 0 before the first headline"),
          H3("6.5.5 Federated averaging"),
          P(f"Each ticker i is a client with n_i training windows. In every round each client copies the global weights, trains for three local epochs and returns its weights; the server forms the weighted mean {c('fedavg')}:"),
          EQ("w^(r+1) = Σ_(i=1..10) (n_i / n) w_i^(r),   n = Σ_i n_i"),
          P("Because every ticker has 384 training windows the weights are equal and the average is a plain mean. The global model is then scored on each ticker's test windows using that ticker's own scalers."),
          H3("6.5.6 Evaluation metrics and forecast band"),
          P("For test targets y_i with predictions ŷ_i (inverse-scaled to dollars) and n test windows:"),
          EQ("MAE = (1/n) Σ |y_i − ŷ_i|,   MSE = (1/n) Σ (y_i − ŷ_i)²,   RMSE = √MSE,   R² = 1 − Σ (y_i − ŷ_i)² / Σ (y_i − ȳ)²"),
          EQ("DA = (1/(n−1)) Σ_i 1[ sign(y_i − y_(i−1)) = sign(ŷ_i − y_(i−1)) ]"),
          P("The directional accuracy compares the sign of the actual move with the sign of the predicted level against the previous actual. For the multi-step forecast the recursion feeds each prediction back as the next input and the band widens with the square root of the horizon h, using σ_res, the standard deviation of the test residuals:"),
          EQ("ŷ_(T+h) = f(window with ŷ_(T+h−1) appended),   band_h = ŷ_(T+h) ± 1.96 σ_res √h,   trend = up if ŷ_(T+5) ≥ y_T"),
          P("Two further quantities are used in Chapter 8 and are not computed by the application. The **persistence baseline** forecasts ŷ_t = y_(t−1). The **true-target scoring** computes the same metrics against the real closes instead of the clipped scaled targets."),
          H3("6.5.7 Multiple-instance formulation (offline study)"),
          P(f"In multiple-instance learning {c('dietterich')} the label belongs to a bag, not to its members. Here the bag B_(k,d) = {{x_1, …, x_n}} is the set of headlines of ticker k published before the close of day d, each instance x_i is represented by FinBERT-tone probabilities and a 64-component projection of its [CLS] vector, "
            f"and the bag label is y = 1 if the close of day d+1 is above the close of day d. With an instance encoder h_i = ReLU(W_e x_i) the gated attention pooling of Ilse et al. {c('ilse')} is"),
          EQ("a_i = softmax_i( wᵀ ( tanh(V h_i) ⊙ sigmoid(U h_i) ) ),   z = Σ_i a_i h_i,   p(y = up) = sigmoid( f([LSTM(price window), z]) )"),
          P("Mean pooling (a_i = 1/n) and max pooling are the simpler alternatives; an empty bag is replaced by a learned vector. The attention weights say which headlines the model relied on, which is the explainability the problem statement asks for.")]

    # ------------------------------------------------------------------ 6.6
    b += [H2("6.6 Model Architecture and Training"),
          _fig("model", 5.4),
          TAB("Hyper-parameters (config.py, models_dl.py, federated.py, forecast.py).",
              ["Setting", "Value"],
              [["Window / split / batch / maximum epochs", "20 trading days / 80 % chronological / 32 / 50"],
               ["LSTM tier", "LSTM(64), BatchNorm, Dropout 0.2, Dense(1): 18,241 parameters (18,113 trainable)"],
               ["Attention tier", "LSTM(64, sequences), MultiHeadAttention(4 heads, key size 16), residual, LayerNorm, global average pooling, Dense(32, ReLU), Dropout 0.2, Dense(1): 36,801 parameters (37,057 with the sentiment column)"],
               ["Optimiser and loss", f"Adam, learning rate 1e-3 {c('adam')}; mean squared error"],
               ["Early stopping", "Monitor validation loss, patience 7, restore best weights; validation split 15 %"],
               ["Federated stage", "10 clients, 2 rounds, 3 local epochs per round, weighted average of weights"],
               ["Seeds", "TensorFlow and NumPy seed 42 in the product; seeds 42 to 46 in the documentation re-run"],
               ["Forecast horizons / band", "5 and 30 trading days / 1.96 σ_res √h"],
               ["Classical baselines", "ARIMA(5,1,0); SARIMAX(1,1,1)(1,1,1,5); Prophet with daily and weekly seasonality; Random Forest 200 trees on 20 lags; SVR RBF C = 10, ε = 0.5"]],
              widths=[2.0, 4.6], align=["l", "l"], size=9.0),
          P(f"Training is cheap. In the five-seed re-run the three local tiers stopped after about {epochs['lstm']:.0f} (LSTM), {epochs['lstm_attention']:.0f} (attention) and {epochs['lstm_attention_sentiment']:.0f} (attention and sentiment) epochs on average, "
            f"and one ticker and one seed (four local networks plus that ticker's share of the federated stage) took about {per_run:.0f} seconds on the six-core CPU used here, which was shared with other jobs. The shipped run saved one loss curve per local tier, and the federated stage logs the mean local loss of each round "
            f"({F.SUM['federated_rounds'][0]['mean_local_loss']:.4f} in round 1 and {F.SUM['federated_rounds'][1]['mean_local_loss']:.4f} in round 2).")]

    # ------------------------------------------------------------------ 6.7
    cfg = mil["folds"]
    b += [H2("6.7 Multiple-Instance Learning Study (Offline)"),
          P("The batch objectives ask for news treated as bags, directional prediction scored with accuracy, precision, recall and F1, and a comparison with a price-only baseline. The application does none of these, so the study was run as a separate script, `scripts/mil_study.py`, using real headlines. Its design is summarised below; its results are in Chapter 8."),
          TAB("Design of the study.",
              ["Item", "Choice"],
              [["Bag and instance", "All headlines of one ticker published before a day's close; instance = 3 FinBERT-tone probabilities + 64 PCA components of the [CLS] vector (PCA fitted on training headlines only)"],
               ["Label", "1 if the next trading day's close is above today's close; bag-level only"],
               ["Tickers and period", "AAPL, AMZN, FDX, MSFT, NVDA, ORCL, TSLA; news era 2022 to 2023"],
               ["Folds", "Three expanding windows tested on Q2, Q3 and Q4 2023; validation = the two months before each test quarter; test predictions pooled (" + f"{mil['n_test_pooled']:,}" + " samples)"],
               ["Price branch", "LSTM(32) over 20 days of return, high-low range and log volume ratio (z-scored)"],
               ["Bag models", "Flat mean sentiment; MIL mean, max and gated-attention pooling (hidden size 32, attention size 16, at most 24 instances per bag); news-only attention; placebo with bags of other days"],
               ["Training", f"AdamW, learning rate 2e-3, weight decay 1e-3 {c('adamw')}; batch 128; at most 60 epochs; early stopping patience 7; five seeds"],
               ["Metrics", "Accuracy, precision, recall, F1 (up = positive), ROC-AUC; paired bootstrap against the price-only LSTM"],
               ["Leakage controls", "A headline is placed in the bag of the first trading day whose close is not earlier than its time stamp; scaling and PCA fitted on training data; the placebo gives each day the bag of another day of the same ticker"]],
              widths=[1.6, 5.0], align=["l", "l"], size=9.0)]

    # ------------------------------------------------------------------ 6.8
    b += [H2("6.8 Evaluation Protocol"),
          P("Five measurements are used in Chapter 8: the **shipped metrics** of `artifacts/metrics.json`; a **five-seed re-run** of the shipped pipeline on the same 501 rows; **true-target scoring** and the **persistence baseline**, which expose what the shipped scoring hides; the **forward test** of the stored forecasts (from the 2026-09-08 close) against the closes of the following 30 trading days, the only genuinely out-of-sample check; and the **multiple-instance study** of Section 6.7. Timings come from `scripts/measure_api.py` on 127.0.0.1.")]
    return b


def application_blocks():
    a, w = F.API_PORT, F.WEB_PORT
    b = []
    b += [H2("6.9 Application Architecture"),
          P(f"The application is one Python process plus a static website. `main.py` creates the FastAPI object with a CORS middleware, defines seven routes and, when `frontend/dist` exists, serves `/assets` and a catch-all that returns `index.html` for client-side routes. "
            f"Nothing is loaded at start-up: the first request reads `artifacts/metrics.json` (and later `forecasts.json`) into a module-level cache. In development Vite serves the website on port {w} and proxies `/api` to 127.0.0.1:{a}; otherwise the API serves the built website itself."),
          _fig("seq", 4.8),
          P("The `/api/history` route calls `load_ticker`, which tries a live download, then the CSV, then the synthetic generator, so a chart can always be drawn; the route then places the stored forecast on the next business days after the last bar. "
            "The `/api/sentiment` route calls `get_daily_sentiment` for the ticker's dates, which loads FinBERT-tone on first use into a module-level singleton and is the slowest call of the system."),
          P("The training script is the other half of the application. `train_ticker` runs the baselines, builds the sentiment series and calls an inner `run_tier` three times (LSTM, attention, attention with sentiment); each call builds the features, fits the scalers, makes the windows, trains with early stopping and scores the test windows. "
            "The recursive forecasts come from the third tier. After the ten tickers, `main` runs two federated rounds over the third tier, scores the global model on every ticker, **replaces each ticker's 5-day forecast and trend with the global model's**, saves the Keras files and scalers, draws four plots for TSLA and writes `metrics.json` and `forecasts.json`; the stored 30-day forecast therefore still comes from the local attention and sentiment model."),
          H2("6.10 API Design"),
          TAB("Routes, parameters and responses.",
              ["Route", "Parameters", "Success response", "Errors"],
              [["GET /api/health", "none", "`{status, product, tickers[], trained, news_source}`", "none"],
               ["GET /api/tickers", "none", "`{tickers:[{ticker, last_close, trend, mode}]}`", "none"],
               ["GET /api/metrics", "none", "`{<TICKER>: record}` for ten tickers (about 76 KB)", "503 not trained"],
               ["GET /api/metrics/{ticker}", "symbol of 1 to 6 letters", "`{ticker, ...record}`", "400 invalid, 404 unknown"],
               ["GET /api/forecast/{ticker}", "`horizon` = short or long (default short)", "`{ticker, horizon, last_close, trend, forecast:[{day, predicted_close, lower, upper}]}`", "400, 404, 422"],
               ["GET /api/sentiment/{ticker}", "symbol", "`{ticker, meta, daily:[{date, score}] (30), headlines:[{headline, sentiment_score}]}`", "400"],
               ["GET /api/history/{ticker}", "`days` 20 to 500 (default 120)", "`{ticker, mode, history:[{date, open, high, low, close, volume}], forecast_overlay:[{date, predicted_close, lower, upper}]}`", "400, 422"]],
              widths=[1.5, 1.4, 2.7, 1.0], align=["l", "l", "l", "l"], size=8.5),
          CODE(_api_example(), 8.0),
          P("The record returned for a ticker has the fields listed in Section 5.5. Every route is a plain `GET` with no body; the API is read-only and idempotent, which makes it safe to cache and to test. Interactive documentation is available from FastAPI at `/docs`."),
          H2("6.11 Front-End Implementation"),
          P("Each page calls `useAsync` with a function that receives an abort signal (so changing the ticker cancels the request) and renders a skeleton while loading, an `ErrorState` with a retry button on failure and an `EmptyState` when there are no rows. "
            "The API client sets a 30-second timeout (240 seconds for sentiment, because the first call loads FinBERT) and turns every failure into an `ApiError`. Charts are Recharts components with an `aria-label`, and animation is off when the user prefers reduced motion. "
            "`buildSeries` in `lib/market.js` anchors the stored forecast on the history row with the training last close and annotates every forecast day that already has an actual close."),
          H2("6.12 Security and Error Handling"),
          B("**Input validation.** A ticker must match `^[A-Za-z]{1,6}$` before any file or network access; `horizon` must be `short` or `long` and `days` between 20 and 500, enforced by FastAPI query validation (HTTP 422).",
            "**Errors.** Invalid symbol 400 with a message, unknown ticker 404 listing the configured tickers, missing artefacts 503 with the command to run; unknown `/api/...` paths return 404 instead of the single-page fallback.",
            "**Network failure.** A failed Yahoo download falls back to the CSV and then to a labelled synthetic series; a missing FinBERT model to a word-list scorer (`scorer: lexicon`); a failed NewsAPI call to the synthetic headlines.",
            "**No authentication, no personal data.** The API is read-only and binds to 127.0.0.1; CORS is limited to localhost origins. A public deployment would need rate limiting and a reverse proxy. The optional `NEWSAPI_KEY` is read from the environment or `.env` (ignored by Git) and never sent to the browser.",
            "**Honesty features.** The mode of every price series, the news source and the stale-forecast banner are displayed; the README states that forecasts are not financial advice."),
          H2("6.13 Installation and Execution"),
          P(f"The one-click path is `run.bat`. In six steps it finds Python 3.11, creates or repairs `.venv`, installs `backend/requirements.txt` once, trains the models only if `artifacts/metrics.json` is missing (five to ten minutes on a CPU), installs the website packages, and opens the API on port {a}, the website on port {w} and the browser; ports come from `.env`."),
          N("Install Python 3.11 and Node.js 20 or newer; optionally put a `NEWSAPI_KEY` in `.env`.",
            "Run `run.bat`, or manually: `py -3.11 -m venv .venv`, activate it, `python -m pip install -r backend\\requirements.txt`, `python -m backend.train`, `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8404`.",
            "For live reload: `cd frontend`, `npm install`, `npm run dev` (port 5404, proxying `/api`).",
            "Without Node.js the API serves the prebuilt `frontend/dist` at http://localhost:8404.",
            "With Docker: `docker compose up --build`; the image serves the prebuilt site and API on port 8000 (the Docker route was not exercised in this work).",
            "Check the stack with `python scripts/smoke_test.py` (26 checks) and the unit tests with `pytest tests` (56 tests)."),
          P("Retraining with `python -m backend.train` rewrites `artifacts/` and is the only way to move the forecast origin to the latest price. The documentation experiments are separate scripts (`run_experiments.py`, `mil_study.py` with `extract_news.py` and `mil_features.py`, `measure_api.py`, `fetch_snapshot.py`).")]
    return b


def blocks():
    return [
        H1("6. METHODOLOGY AND SOFTWARE IMPLEMENTATION"),
        P("This chapter explains how QuantPulse works from data to screen: the methodology, the datasets, the preprocessing, the choice of algorithms and their mathematics, the model architecture and training, "
          "the offline multiple-instance study, the application and its API, the error handling and the way to install and run it. All hyper-parameters quoted are those in the code, and every statement about data says whether the data are real or synthetic."),
    ] + methodology_blocks() + application_blocks()
