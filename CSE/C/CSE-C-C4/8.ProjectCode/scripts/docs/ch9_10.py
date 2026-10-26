"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared helper block lists used by documents 9, 10, 12 and 15.

Every number is read from scripts/docs/facts.py (experiments/*.json and artifacts/metrics.json) when the blocks are built.
"""
import os

import numpy as np

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


# ---------------------------------------------------------------------------- measured numbers used in several places
T = F.TICKERS
NS = len(F.RR["seeds"])


def _sw(tier, key):
    """Mean over the ten tickers per seed -> (mean, std over seeds)."""
    per = [np.mean([F.RR["tickers"][t]["models"][tier][s][key] for t in T]) for s in range(NS)]
    return float(np.mean(per)), float(np.std(per))


def _pers():
    return float(np.mean([F.RR["tickers"][t]["persistence"]["mae"] for t in T]))


def _above(thr=50.0):
    return sum(1 for t in T if F.RR["tickers"][t]["test_close_above_train_max_pct"] > thr)


def _m(k, key="accuracy"):
    return F.MIL["models"][k]["summary"][key]["mean"]


def _mil_best_gap():
    """largest accuracy gain of any MIL variant over the matched price-only LSTM, in points, and its interval."""
    k = max(("lstm_mil_mean", "lstm_mil_max", "lstm_mil_attention"), key=lambda n: F.MIL["paired_vs_lstm_price"][n]["acc_diff"])
    v = F.MIL["paired_vs_lstm_price"][k]
    return k, v["acc_diff"] * 100, v["ci95"][0] * 100, v["ci95"][1] * 100


def _attn():
    """Gated-attention examples from the MIL study: (n examples, mean top weight / uniform weight, the example used in the text)."""
    ex = F.MIL["attention_examples"]
    ratio = float(np.mean([e["top"][0]["weight"] / e["uniform_weight"] for e in ex]))
    pick = next((e for e in ex if e["ticker"] == "MSFT" and e["date"] == "2023-10-27"), ex[0])
    return len(ex), ratio, pick


def _seed_std(tier):
    return _sw(tier, "mae_true")[1]


def _down5():
    return sum(1 for t in T if F.SUM["trend"][t] == "down")


# ---------------------------------------------------------------------------- novelty / contributions
def novelty_blocks():
    return [
        H2("What the base paper contributes"),
        P(f"The base paper [{R['base']}] combines four ideas for short-term forecasting of ten technology and logistics stocks: an LSTM over a 20-day OHLCV window, multi-head attention on top of the LSTM, a sentiment channel built from FinBERT-tone scores of NewsAPI headlines, "
          f"and a simulated federated-averaging stage in which each company is a client. It reports an average R2 of {F.BASE_PAPER_RESULTS['r2_avg']} over the ten companies, TSLA MSE {F.BASE_PAPER_RESULTS['tsla_mse']}, MAE {F.BASE_PAPER_RESULTS['tsla_mae']} and R2 {F.BASE_PAPER_RESULTS['tsla_r2']}, "
          f"and a baseline-LSTM trend accuracy of {F.BASE_PAPER_RESULTS['lstm_trend_acc']} % over 100 runs per company. Its hybrid experiments use a one-month window because the NewsAPI free tier returns about 30 days of headlines, and federated learning is only simulated; the paper says both limits itself."),
        H2("What QuantPulse shares with it"),
        B("The same four components in the same order: LSTM, LSTM plus 4-head attention, plus a sentiment channel, plus FedAvg, each tier added to the previous one (an ablation).",
          "The same five classical baselines (ARIMA, SARIMAX, Prophet, Random Forest, SVR), the same 20-day window, the same 5-day and 30-day horizons, and a one-LSTM-layer-with-64-units design with batch normalisation and dropout.",
          "FinBERT-tone [" + str(R['finbert_tone']) + "] scoring of headlines, and the ten-company universe (Airbnb is replaced by Meta because Airbnb's history is short)."),
        H2("What is different in this project"),
        B(f"**Data scale.** Two years of daily prices (501 training rows per ticker, 97 test windows) instead of a one-month window, so the test period contains regime changes that a 30-day window cannot show.",
          f"**Scoring against real closes.** The product's own test scoring clips targets to the training range. The re-run scores the same predictions against the real closes ('true-target' scoring) and adds a persistence baseline (yesterday's close). On that scale the best deep tier has a mean absolute error of ${_sw('lstm_attention', 'mae_true')[0]:.2f}, against ${_pers():.2f} for persistence.",
          f"**A forward test.** The stored forecasts, made from the 2026-09-08 close, were compared with the 30 trading days that actually followed: the 5-day forecasts averaged {F.FWD['short']['mean_pred_change_pct']:+.1f} % against an actual {F.FWD['short']['mean_actual_change_pct']:+.1f} %, and the trend flag was right for {F.FWD['short']['trend_hits']} of 10 tickers.",
          f"**A placebo and five seeds.** A sentiment channel shuffled in time and five training seeds show that the sentiment tier's behaviour is an artefact of its zero-filled channel, not a finding about news.",
          f"**An offline multiple-instance-learning study on real headlines.** The batch title asks for MIL, which the base paper does not use. A separate script bags {F.MIL['instances']['n_headline_rows_used']:,} real FNSPID headlines per ticker and trading day, trains mean, max and gated-attention MIL pooling next to a price-only LSTM, and reports accuracy, precision, recall and F1 on {F.MIL['n_test_pooled']:,} test samples [{R['ilse']}], [{R['fnspid']}].",
          "**A reproducible experiment suite and tests.** `scripts/run_experiments.py`, `scripts/mil_study.py`, 56 pytest tests and a 26-check smoke test regenerate every number in the documents."),
        H2("What is not new"),
        P(f"The model architectures, the FedAvg rule [{R['fedavg']}], the baselines and the FinBERT scorer are the base paper's or are published components used unchanged. The application shell (FastAPI, React, a forecast screen with confidence bands) is engineering rather than research. "
          f"The MIL formulation follows Dietterich et al. [{R['dietterich']}] and the attention pooling follows Ilse et al. [{R['ilse']}]; applying MIL to daily news bags for stock direction was proposed earlier by Zhang et al. [{R['zhang']}] and Deng and Yiu [{R['deng']}], so this project's contribution there is a small, honest replication on a new dataset, not a new method."),
        P(f"In the study's own diagnostics the gated-attention weights stay close to uniform (on average the top weight is {_attn()[1]:.2f} times 1/n over {_attn()[0]} inspected test days), so the model did not learn to prefer particular headlines; the study therefore reports a negative result, not a new method."),
        P("The comparison with the base paper is indicative only. The paper's window, scaling units and split differ from ours, so its R2 of 0.91 and its 65.36 % trend accuracy are not reproduced and not contradicted by a like-for-like run."),
    ]


def contribution_blocks():
    k, d, lo, hi = _mil_best_gap()
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N("**A working forecasting product, QuantPulse**: a FastAPI service with seven JSON endpoints, a six-screen React website, ten tickers, five classical baselines, four deep-model tiers and 5- and 30-day forecasts with confidence bands, started by one `run.bat`.",
          f"**An implementation of the base paper's ablation** (LSTM, attention, sentiment, simulated FedAvg) that can be re-run end to end with `python -m backend.train`, with its results shown on a model-comparison screen.",
          f"**An evaluation that goes beyond the base paper**: five seeds, a persistence baseline, true-target scoring and a forward test. It shows that no deep tier beats 'tomorrow equals today' (mean MAE ${_pers():.2f} for persistence against ${_sw('lstm_attention', 'mae_true')[0]:.2f} for the best tier) and that the stored 5-day forecasts were wrong in direction for {10 - F.FWD['short']['trend_hits']} of 10 tickers.",
          f"**Four defects documented with evidence**: clipped test targets that inflate directional accuracy (shipped {_sw('lstm_attention', 'directional_accuracy')[0] * 100:.1f} % against {_sw('lstm_attention', 'da_true')[0] * 100:.1f} % on real closes), a sentiment channel that is zero throughout training, FedAvg across differently scaled clients, and artefacts older than the data.",
          f"**An offline multiple-instance-learning study on real headlines** (seven tickers, 2022-2023, {F.MIL['n_test_pooled']:,} test samples, five seeds). The best MIL variant gained {d:+.1f} accuracy points over the matched price-only LSTM with a 95 % interval of [{lo:+.1f}, {hi:+.1f}], and no model beat the always-up rate of {F.MIL['always_up_accuracy_test'] * 100:.1f} %: no evidence that news bags improve next-day direction at this sample size.",
          "**A tested, documented artefact**: 56 unit and API tests, a 26-check smoke test, 12 design diagrams, 17 real screenshots and scripts that regenerate every figure from JSON."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        H2("In scope"),
        B("**Short-term forecasting of closing prices** for a configurable universe, default ten tickers (TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM, ORCL): 5-day and 30-day horizons with a 95 % band and an up/down trend flag.",
          "**A comparison of nine models** on a chronological 80/20 split: ARIMA, SARIMAX, Prophet, Random Forest and SVR as baselines, and LSTM, LSTM plus attention, plus sentiment, and a simulated-federated hybrid as deep tiers.",
          "**Headline sentiment**: NewsAPI headlines scored by FinBERT-tone when a key is set; otherwise a labelled synthetic-headline fallback with the same schema.",
          "**A website and API**: dashboard, forecast, model comparison, news sentiment and method screens over seven endpoints, in light and dark themes.",
          "**Evaluation work added for the documents**: five-seed re-run, persistence baseline, forward test, API latency, tests, and an offline MIL study on real headlines."),
        H2("Out of scope"),
        B("Multiple instance learning inside the application, and any social-media text source: neither exists in QuantPulse.",
          "Precision, recall and F1 in the application: it forecasts price levels, not a direction classifier (the offline study reports them).",
          "Trading, order placement, portfolio construction, transaction costs and back-tested strategies; QuantPulse is a research and education tool, not financial advice.",
          "Intraday data, options, other asset classes, macro-economic indicators and technical indicators beyond the five OHLCV columns.",
          "User accounts, a database, role management, multi-tenant operation and cloud deployment (there is no login and no database).",
          "A real federated deployment: all ten clients run in one process and exchange weights in memory."),
        H2("Boundaries of the product"),
        TAB("Dimensions of the delivered system", ["Dimension", "Delivered"],
            [["Universe", "10 tickers (override with QP_TICKERS); 501 daily rows each (2024-09-09 to 2026-09-08 for the shipped artefacts)"],
             ["Models", "5 baselines, LSTM(64), LSTM(64) + 4-head attention, sentiment variant, FedAvg hybrid (10 clients x 2 rounds x 3 epochs)"],
             ["Window and split", "20 trading days; chronological 80/20; Min-Max scaling fitted on the first 80 % of rows"],
             ["Horizons", "5 and 30 trading days, recursive; band = 1.96 x residual std x sqrt(h)"],
             ["Interface", "React 19 + Vite, 6 routes; FastAPI, 7 JSON endpoints; ports 5404 and 8404"],
             ["Sentiment", "FinBERT-tone (yiyanghkust/finbert-tone) on NewsAPI headlines, or synthetic template headlines"],
             ["Hardware used", "Intel Core i5-12500, 15.7 GB RAM, no GPU; one full re-run of five seeds took " + f"{F.RR['seconds'] / 60:.0f} minutes"]],
            widths=[1.6, 4.6], align=["l", "l"], size=10),
    ]


def assumption_blocks():
    return [
        P("The results depend on the following assumptions, all of which are choices of the project or of the base paper rather than findings."),
        B("**Data.** Daily Yahoo Finance bars are taken as correct; the unadjusted Close is used as the target; the last two years are enough history; the same 20-day window suits every ticker.",
          "**Split.** A chronological 80/20 split with Min-Max scalers fitted on the first 80 % of rows is a fair test; the deep tiers hold out the last 15 % of the training windows for validation and early stopping (patience 7).",
          "**Sentiment.** A headline's FinBERT tone (positive +1, negative -1, neutral 0, times its probability) averaged over a day represents the market mood; the daily value is carried forward over days without headlines and is zero before the first headline.",
          "**Federation.** Each ticker is one client; clients start from one global model, train for three epochs, and their weights are averaged in proportion to sample count; two rounds are enough.",
          "**Forecast.** For multi-day horizons the predicted close is fed back as the next day's Open, High, Low and Close; volume and sentiment are held at their last values; the band grows with the square root of the horizon.",
          "**Evaluation.** Directional accuracy compares the sign of the predicted close minus yesterday's actual close with the sign of the real change; the re-run adds true-target scoring, persistence and five seeds (42-46).",
          "**MIL study.** A headline belongs to the bag of the first trading day whose close is not earlier than its time stamp (day-level stamps go to that calendar day); the label is whether the next close is higher; the instance vector is three FinBERT-tone probabilities plus 64 PCA components of the [CLS] vector fitted on training headlines only.",
          "**Operation.** One user, one machine, internet access for Yahoo Finance, and no authentication."),
    ]


def limitation_blocks():
    p_ = _pers()
    return [
        P("The limitations below are properties of the delivered system and of the evidence, ordered by how much they affect the conclusions."),
        TAB("Limitations of QuantPulse and their effect", ["Limitation", "Evidence", "Effect on the conclusions"],
            [["No multiple-instance learning, social media or P/R/F1 in the product", "Sentiment is one daily mean per ticker; the attention layer runs over the price window", "Objectives 3 and 5 are met only by the offline study"],
             ["Sentiment is synthetic in the shipped run", f"News source 'synthetic-fallback' for all ten tickers; {F.RR['tickers']['TSLA']['n_headlines']} template headlines for TSLA, generated for the last 90 days only", "The sentiment tier says nothing about real news"],
             ["Sentiment channel is zero throughout training", "0 non-zero rows in the training part of every ticker; 83-90 in the test part", f"Sentiment tier MAE ${_sw('lstm_attention_sentiment', 'mae_true')[0]:.2f} ± {_sw('lstm_attention_sentiment', 'mae_true')[1]:.2f} against ${_sw('lstm_attention', 'mae_true')[0]:.2f} without it"],
             ["Test targets are clipped to the training range", f"{_above()} of 10 tickers have more than half of their test closes above the training maximum", f"Shipped direction {_sw('lstm_attention', 'directional_accuracy')[0] * 100:.1f} % against true {_sw('lstm_attention', 'da_true')[0] * 100:.1f} %; MAE understated"],
             ["Deep tiers do not beat persistence", f"Persistence MAE ${p_:.2f}; best tier ${_sw('lstm_attention', 'mae_true')[0]:.2f}; R2 {_sw('lstm_attention', 'r2_true')[0]:.1f} on real closes", "The product forecasts are not useful as price levels"],
             ["Stored forecasts missed the realised moves", f"5-day mean forecast {F.FWD['short']['mean_pred_change_pct']:+.1f} % vs actual {F.FWD['short']['mean_actual_change_pct']:+.1f} %; trend right for {F.FWD['short']['trend_hits']} of 10", f"{_down5()} of 10 tickers were flagged 'down'"],
             ["FedAvg across differently scaled clients", f"Hybrid MAE ${_sw('hybrid_federated', 'mae_true')[0]:.2f} ± {_sw('hybrid_federated', 'mae_true')[1]:.2f} on real closes", "Federation did not help; the base paper's gain is not reproduced"],
             ["Artefacts older than the data", "Trained on data to 2026-09-08; CSVs overwritten by every live pull", "The Forecast screen shows a banner; retrain to refresh"],
             ["Small, short data", "501 rows per ticker; 97 test windows", "Single-split results are noisy; seed std up to " + f"${max(_sw(t, 'mae_true')[1] for t in ('lstm_attention_sentiment', 'hybrid_federated')):.1f}"],
             ["Mixed baseline protocols", "ARIMA/SARIMAX/Prophet forecast 101 days without refitting; RF/SVR use actual lags", "Baseline table is not like-for-like (as in the base paper)"],
             ["MIL study is small", f"7 tickers, 2022-2023, {F.MIL['n_test_pooled']:,} test samples; stamps day-level", "Differences under about 3 accuracy points are noise"],
             ["CPU only, one machine", "i5-12500, no GPU", "No large-scale or hyper-parameter search"],
             ["No authentication, no database", "No login route; state is JSON/CSV/Keras files", "Not a production service"]],
            widths=[1.7, 2.6, 2.3], align=["l", "l", "l"], size=9),
        P("Further defects of the shipped code, kept unchanged in this project: multi-step forecasts roll the Close forward and overwrite Open, High and Low with it; the synthetic fallback seeds with Python's `hash(ticker)`, so its headlines change between processes; "
          "the API never loads the saved `.keras` models and serves stored JSON; the stored 5-day forecast comes from the federated model while the 30-day forecast comes from the local attention-plus-sentiment model."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and nothing in the documents should be read as a result for them:"),
        B("Real NewsAPI headlines inside the product (no key was available), and any social-media text (no data source was available).",
          "Multiple instance learning, precision, recall and F1 inside the application; they exist only in the offline study.",
          "Trading performance, transaction costs, risk-adjusted returns or any back-tested strategy.",
          "A genuine federated deployment: communication cost, privacy guarantees and client drop-out were not studied because the federation is simulated in one process.",
          "Behaviour under concurrent users, long-running stability and memory footprint; GPU timing; energy use.",
          "A clean-machine `run.bat` install and the Docker image (Docker was not used).",
          "Security of the API (no authentication exists) and browser compatibility beyond Chromium and Chrome.",
          f"News effects at scale: the MIL study covers seven tickers, two years of dense headlines and {F.MIL['n_test_pooled']:,} test samples; GOOGL, META and IBM had no usable headlines."),
    ]


# ---------------------------------------------------------------------------- design walk-throughs and decisions
def walkthrough_blocks():
    return [
        H2("Windows and scalers (`models_dl.py`)"),
        CODE(src("backend/app/models_dl.py", 21, 44), 8),
        P("Each sample is the previous 20 rows of OHLCV (plus the sentiment column when present); the target is the next Close, column 3. The split is chronological. Scalers are fitted per column on the first 80 % of rows and the output is clipped to [0, 1]. "
          "That clip is why the product's test scoring is wrong for rising tickers: a test close above the training maximum becomes exactly 1.0 before the error is computed."),
        H2("The attention tier (`models_dl.py`)"),
        CODE(src("backend/app/models_dl.py", 59, 73), 8),
        P("An LSTM(64) returns the whole sequence; 4-head self-attention with key size 16 mixes the 20 time steps; a residual connection and layer normalisation follow, then global average pooling, Dense(32) with ReLU, dropout 0.2 and a linear output. "
          "The attention is over days of the price window, not over news instances, which is the difference from a multiple-instance model."),
        H2("Federated averaging (`federated.py`)"),
        CODE(src("backend/app/federated.py", 16, 23) + "\n...\n" + src("backend/app/federated.py", 30, 43), 8),
        P("`fedavg` averages each weight tensor in proportion to the client's sample count. In each of two rounds every ticker copies the global weights, trains three epochs and returns its weights. The clients use different price scales, and the global model is later scored with each ticker's own scaler, which is one reason the hybrid tier is the worst of the four."),
        H2("Recursive forecast (`forecast.py`)"),
        CODE(src("backend/app/forecast.py", 6, 21), 8),
        P("Each step predicts the next scaled close, writes it into Close, Open, High and Low of a new row and slides the window; volume and sentiment keep their last values. The band is 1.96 times the standard deviation of the one-step test residuals times the square root of the step, floored at 0.01. "
          "Because errors feed back and the band assumes independent steps, the band is far narrower than the actual 5-day miss in the forward test."),
        H2("Sentiment alignment (`sentiment.py`)"),
        CODE(src("backend/app/sentiment.py", 139, 147), 8),
        P("Daily headline scores are matched to trading dates, forward-filled over days without headlines and set to zero before the first headline; the synthetic fallback only generates headlines for the last 90 trading dates, so every earlier row is zero."),
        H2("Forecast endpoint (`main.py`)"),
        CODE(src("backend/app/main.py", 95, 104), 8),
        P("The endpoint validates the ticker with a 1-6 letter regular expression (400), looks the ticker up in the stored metrics (404), and returns the stored 5- or 30-row forecast; an invalid horizon is rejected by FastAPI (422). No model is loaded at request time, which is why it answers in about "
          f"{F.API['endpoints']['forecast_short']['median_ms']:.0f} ms."),
    ]


def decision_blocks():
    return [
        P("The table lists the main implementation decisions with the reason for each and the consequence that was observed."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "Consequence observed"],
            [["Follow the base paper's four-tier ablation", "The batch names the paper as base; the ablation makes each idea's effect visible", "Attention helped the LSTM; sentiment and FedAvg did not (re-run, five seeds)"],
             ["Chronological 80/20 split, 20-day window", "No look-ahead; same as the paper's baselines", "97 test windows per ticker: small and noisy"],
             ["Min-Max scaling fitted on the training rows, clipped to [0, 1]", "Keeps inputs bounded for the LSTM", "Test prices above the training maximum are clipped, which hides errors and inflates direction accuracy"],
             ["Sentiment from synthetic template headlines when no key is set", "NewsAPI needs a key and returns only about a month of history", "A labelled fallback keeps the pipeline running but the channel is zero during training"],
             ["FinBERT-tone for scoring, lexicon as fallback", "Domain-specific model, inference only; offline fallback", "Scorer is reported in the metadata (finbert in this run)"],
             ["Simulated FedAvg in one process", "Shows the protocol without a network; mirrors the paper", "Clients with different scales; federation scored worst"],
             ["Recursive multi-step forecast with a sqrt(h) band", "One model serves 5 and 30 days", "Predicted close overwrites OHLC; the band is too narrow"],
             ["Serve stored JSON instead of loading models", "Fast, no TensorFlow at serving time", f"Forecast latency about {F.API['endpoints']['forecast_short']['median_ms']:.0f} ms; forecasts go stale until retrained"],
             ["Re-download prices on every /api/history call", "Always show the latest closes next to the stored forecast", f"History costs about {F.API['endpoints']['history_120d']['median_ms']:.0f} ms and rewrites the CSVs"],
             ["FastAPI + React with a Vite proxy", "Simple, typed JSON, one-command start (`run.bat`)", "26 smoke checks and 56 tests cover it"],
             ["Lazy-loaded screens, Recharts charts", "Small first load; charts for bands and bars", "Sentiment screen waits for FinBERT on the first call"],
             ["No login, no database", "A single-user research tool", "Not suitable for production"],
             ["Pinned snapshot for experiments", "The app overwrites its own CSVs", "Experiments are repeatable; rows to 2026-09-08 match the stored last closes"],
             ["Offline MIL study instead of changing the product", "Keep the shipped artefacts unchanged and comparable", "Objectives 3, 5 and 6 are answered with real headlines, outside the application"],
             ["Measure on 127.0.0.1", "`localhost` adds about 2 s per call on this machine", "Latency figures reflect the application, not the resolver"]],
            widths=[1.8, 2.5, 2.3], align=["l", "l", "l"], size=9),
    ]


# ---------------------------------------------------------------------------- chapter 9
def _objective_rows():
    k, d, lo, hi = _mil_best_gap()
    return [
        ["1. Collect prices, financial news and social-media text", "Partly", "Prices yes (Yahoo Finance, 10 tickers). News only as NewsAPI headlines when a key is set; the shipped run used a synthetic fallback. No social-media source."],
        ["2. Align the data into daily instances per trading day", "Partly", "Daily alignment yes, but headlines are reduced to one mean score per day; the offline study builds true bags of headlines."],
        ["3. Represent each day as a bag (MIL)", "Offline only", f"Not in the product. The offline study bags {F.MIL['instances']['n_headline_rows_used']:,} real headlines and trains mean, max and gated-attention pooling."],
        ["4. Hybrid of sequence learning on prices and attention over news", "Partly", "LSTM + attention over the 20-day price window + a daily sentiment channel (product); attention over news instances only in the offline study."],
        ["5. Predict direction; accuracy, precision, recall, F1", "Offline only", "The product reports MAE/R2 and a direction figure; precision, recall and F1 are computed only in the offline study."],
        ["6. Compare multi-source against a price-only baseline", "Done, no gain", f"Offline: best MIL variant {d:+.1f} points [{lo:+.1f}, {hi:+.1f}] over the price-only LSTM; the product's own ablation is not valid because its sentiment is synthetic and zero in training."],
    ]


def _chapter9_core():
    k, d, lo, hi = _mil_best_gap()
    fs, fl = F.FWD["short"], F.FWD["long"]
    return [
        H2("9.1 Summary of the work"),
        P(f"The project set out to predict stock direction from prices, news and social media with multiple instance learning. It delivered QuantPulse, a working forecasting product that implements the base paper's hybrid pipeline [{R['base']}]: ten tickers, five classical baselines, four deep-model tiers (LSTM, attention, sentiment, simulated FedAvg), "
          "5- and 30-day forecasts with bands, a FastAPI backend and a six-screen React website, with 56 passing tests and 26 passing smoke checks. In the documentation phase the product was evaluated far more strictly than the base paper evaluates its own: five seeds, a persistence baseline, scoring against real closes, and a forward test against the closes that followed the stored forecasts. "
          f"Because the title asks for multiple instance learning and the product has none, an offline MIL study was added on {F.MIL['instances']['n_headline_rows_used']:,} real FNSPID headlines."),
        P("The work therefore has two layers. The first is the product layer: what a user sees and can run, which behaves as the base paper's design says it should and is robust against bad input (invalid symbols return 400, unknown ones 404, missing artefacts 503). "
          "The second is the evidence layer: what the numbers say about the forecasts, which is mostly negative. Keeping the two apart is the main discipline of this report, and the same split is used in every chapter: Chapter 6 and Chapter 5 describe what was built, Chapter 7 and Chapter 8 describe what was measured."),
        H2("9.2 Objectives achieved and not achieved"),
        TAB("Batch objectives against the outcome", ["Objective", "Status", "Evidence"], _objective_rows(), widths=[2.0, 0.9, 3.7], align=["l", "c", "l"], size=9.5),
        P("Two of the six objectives are met only partly by the product and two only by work done outside it; none is claimed beyond what the table says."),
        P("The statuses are deliberately strict. 'Partly' means that the product contains a simpler version of the step; 'Offline only' means that the step exists as a script that is not part of the application; 'Done, no gain' means the comparison was made and showed no improvement."),
        H2("9.3 Key findings"),
        N(f"**No deep tier beats persistence.** Against the real closes the best tier (LSTM plus attention) has a mean absolute error of ${_sw('lstm_attention', 'mae_true')[0]:.2f} ± {_sw('lstm_attention', 'mae_true')[1]:.2f} over five seeds, and persistence ${_pers():.2f}; R2 is {_sw('lstm_attention', 'r2_true')[0]:.1f}. Random Forest is the best of the shipped models on {F.SUM['best_mae_wins'].get('random_forest', 0)} of 10 tickers.",
          f"**The shipped scoring is optimistic.** Test targets are clipped to the training range, which affects {_above()} of 10 tickers strongly; directional accuracy reads {_sw('lstm_attention', 'directional_accuracy')[0] * 100:.1f} % in the product and {_sw('lstm_attention', 'da_true')[0] * 100:.1f} % against real closes.",
          f"**The stored forecasts failed a forward test.** From 2026-09-08 the 5-day forecasts averaged {fs['mean_pred_change_pct']:+.1f} % while prices moved {fs['mean_actual_change_pct']:+.1f} %; the 5-day MAE was ${fs['mean_mae']:.2f} against ${fs['mean_persistence_mae']:.2f} for no change, and the trend flag was right for {fs['trend_hits']} of 10 (30-day: {fl['trend_hits']} of 10).",
          f"**Sentiment and federation did not help.** The sentiment channel is zero during training, so the tier is unstable (MAE ${_sw('lstm_attention_sentiment', 'mae_true')[0]:.2f} ± {_sw('lstm_attention_sentiment', 'mae_true')[1]:.2f}); a time-shuffled placebo scores ${_sw('attention_shuffled_sentiment', 'mae_true')[0]:.2f}, the same as no sentiment; FedAvg scores ${_sw('hybrid_federated', 'mae_true')[0]:.2f} ± {_sw('hybrid_federated', 'mae_true')[1]:.2f}.",
          f"**Real news bags gave no measurable gain in the offline study.** On {F.MIL['n_test_pooled']:,} pooled test samples the always-up rate is {F.MIL['always_up_accuracy_test'] * 100:.1f} %; the matched price-only LSTM reaches {_m('lstm_price') * 100:.1f} %, the gated-attention MIL model {_m('lstm_mil_attention') * 100:.1f} % (F1 {_m('lstm_mil_attention', 'f1'):.2f}), and a placebo with other days' bags {_m('placebo_mil_attention_shuffled_bags') * 100:.1f} %. The largest paired gain over price-only is {d:+.1f} points with a 95 % interval [{lo:+.1f}, {hi:+.1f}].",
          f"**The attention weights did not single out headlines.** In the {_attn()[0]} test days inspected the highest weight was on average {_attn()[1]:.2f} times the uniform weight 1/n; for example on {_attn()[2]['ticker']} {_attn()[2]['date']} ({_attn()[2]['n_headlines']} headlines) the top three weights were "
          + "/".join(f"{t['weight']:.3f}" for t in _attn()[2]['top']) + f" against a uniform {_attn()[2]['uniform_weight']:.3f}, and the predicted probability was {_attn()[2]['p_up']:.2f}, so gated attention behaved almost like mean pooling.",
          f"**The base paper's R2 of {F.BASE_PAPER_RESULTS['r2_avg']} was not reproduced.** Shipped R2 averages {F.SUM['models']['hybrid_federated']['r2']['mean']:.1f} for the hybrid; datasets and protocols differ (30-day window and scaled units in the paper, two years and dollars here), so this is not a refutation."),
        P(f"Reading the MIL table needs care. Accuracy alone is dominated by the class balance: the test samples are {F.MIL['up_share_test'] * 100:.1f} % up days, and the price-only LSTM trained on all history since 2016 reaches {_m('lstm_price_full_history') * 100:.1f} % accuracy only because it predicts 'up' for {F.MIL['models']['lstm_price_full_history']['summary']['pred_up_share']['mean'] * 100:.0f} % of days (recall {_m('lstm_price_full_history', 'recall'):.2f}, ROC-AUC {_m('lstm_price_full_history', 'auc'):.2f}, i.e. no ranking skill). "
          f"The matched-window models lean the other way and call fewer days up, which lowers recall and F1. ROC-AUC, which does not depend on a threshold, sits between {min(F.MIL['models'][k]['summary']['auc']['mean'] for k in ('lstm_price', 'lstm_flat_sentiment', 'lstm_mil_mean', 'lstm_mil_max', 'lstm_mil_attention')):.3f} and {max(F.MIL['models'][k]['summary']['auc']['mean'] for k in ('lstm_price', 'lstm_flat_sentiment', 'lstm_mil_mean', 'lstm_mil_max', 'lstm_mil_attention')):.3f} for every price or price-plus-news model, which is within chance for a sample of this size. "
          f"Restricting the score to days that have at least one headline ({F.MIL['bags']['share_days_with_news_test'] * 100:.0f} % of test days) changes nothing: the MIL attention model scores {F.MIL['models_news_days']['lstm_mil_attention']['accuracy']['mean'] * 100:.1f} % on those days. The news-only MIL model, which has no price input, reaches {_m('mil_attention_news_only') * 100:.1f} % accuracy but with ROC-AUC {_m('mil_attention_news_only', 'auc'):.2f}: it, too, mostly predicts the majority class."),
        TAB("Headline measurements behind the findings", ["Measurement", "Value", "Source"],
            [["Persistence MAE (yesterday's close), 10-ticker mean", f"${_pers():.2f}", "5-seed re-run, true closes"],
             ["LSTM + attention MAE / R2 on real closes", f"${_sw('lstm_attention', 'mae_true')[0]:.2f} / {_sw('lstm_attention', 'r2_true')[0]:.1f}", "5-seed re-run"],
             ["LSTM MAE / sentiment tier MAE / FedAvg hybrid MAE", f"${_sw('lstm', 'mae_true')[0]:.2f} / ${_sw('lstm_attention_sentiment', 'mae_true')[0]:.2f} / ${_sw('hybrid_federated', 'mae_true')[0]:.2f}", "5-seed re-run"],
             ["Shipped direction vs true direction (LSTM + attention)", f"{_sw('lstm_attention', 'directional_accuracy')[0] * 100:.1f} % vs {_sw('lstm_attention', 'da_true')[0] * 100:.1f} %", "5-seed re-run"],
             ["Stored 5-day forecast: mean change vs actual", f"{fs['mean_pred_change_pct']:+.1f} % vs {fs['mean_actual_change_pct']:+.1f} %", "Forward test, 10 tickers"],
             ["Stored 30-day forecast: mean change vs actual", f"{fl['mean_pred_change_pct']:+.1f} % vs {fl['mean_actual_change_pct']:+.1f} %", "Forward test, 10 tickers"],
             ["MIL study: always-up / price-only LSTM / MIL attention accuracy", f"{F.MIL['always_up_accuracy_test'] * 100:.1f} % / {_m('lstm_price') * 100:.1f} % / {_m('lstm_mil_attention') * 100:.1f} %", f"{F.MIL['n_test_pooled']:,} test samples"],
             ["Warm API latency, stored forecast / history / sentiment (median)", f"{F.API['endpoints']['forecast_short']['median_ms']:.0f} ms / {F.API['endpoints']['history_120d']['median_ms']:.0f} ms / {F.API['endpoints']['sentiment']['median_ms'] / 1000:.1f} s", "measure_api.py"],
             ["Automated checks", "56 pytest + 26 smoke, all passing", "docs/metrics"]],
            widths=[3.3, 1.7, 1.6], align=["l", "c", "l"], size=9.5),
        H2("9.4 Lessons learned"),
        B("**Add the naive baseline first.** Every deep tier looks reasonable on a chart because a price series is smooth; only the comparison with 'tomorrow equals today' shows that none of them forecasts anything useful at the level of dollars.",
          "**Check what the evaluation function does to the data.** One `np.clip` in the scaler step changed both the error and the direction figures for most tickers; the same predictions score 68 % or 53 % depending on whether the target is clipped.",
          "**An ablation needs a working channel.** A sentiment input that is zero during training cannot be shown to help or hurt; the placebo made that visible.",
          "**Test the way the product will be used.** The stored forecasts look plausible on the screen until the realised closes are drawn next to them, as the Forecast screen now does.",
          "**State what is synthetic and what is missing.** The shipped sentiment is template text, the product has no MIL and no social media; the documents say so rather than let the title imply otherwise."),
        H2("9.5 Practical applications"),
        P("QuantPulse is a research and education tool. It is useful for teaching the pipeline from price download to forecast screen, for demonstrating how an ablation is built, and as a test bed for evaluation mistakes (clipping, empty channels, missing baselines) that the documents expose. "
          "It is not suitable for trading decisions, and every screen states that forecasts are statistical estimates, not financial advice."),
        P("A reader should take three things from the findings. First, the numbers that the application displays are not the numbers that a careful evaluation produces, and the difference is large enough to change the story. Second, the multi-source idea in the title is untested by the product and, in the offline study, unsupported at the sample size available. "
          "Third, none of this makes the engineering worthless: a clean, tested pipeline with honest diagnostics is exactly what is needed before a better model is attempted."),
        H2("9.6 Known limitations"),
        P(f"The sentiment source is synthetic in the shipped run, the product has no multiple instance learning, social-media text or precision/recall/F1, the data are short (501 rows, 97 test windows per ticker), the federation is simulated, and the multiple-instance study covers seven tickers over two years. "
          "Chapter 8 and the Scope and Limitations document list each limit with its evidence."),
    ]


def _strip(blocks, drop_prefix=None):
    """Chapter blocks without their chapter numbers on H2 headings (for the shared chapter-document text)."""
    out = []
    for b in blocks:
        if b[0] == "h2":
            if drop_prefix and b[1].startswith(drop_prefix):
                continue
            out.append(("h2", b[1].split(" ", 1)[1]))
        else:
            out.append(b)
    return out


def conclusion_blocks():
    return _strip(_chapter9_core(), "9.5")


def chapter9_blocks():
    core = _chapter9_core()
    i = next(n for n, b in enumerate(core) if b[0] == "tab" and b[1].startswith("Headline"))
    figs = [FIG(F.fig("f02_true_mae_vs_persistence.png"), "True-target MAE of LSTM + attention (five seeds) against persistence for each ticker.", 5.6),
            FIG(F.fig("f05_forecast_vs_actual_change.png"), "Stored 5-day forecast change against the realised change for each ticker (forward test from 2026-09-08).", 5.6),
            FIG(F.fig("f08_mil_accuracy.png"), "Offline MIL study: accuracy of each model against the always-up rate on the pooled test quarters.", 5.6),
            FIG(F.fig("f10_mil_paired_ci.png"), "Offline MIL study: accuracy difference to the price-only LSTM with 95 % bootstrap intervals.", 5.6)]
    return [H1("9. CONCLUSION")] + core[:i] + figs + core[i:]


# ---------------------------------------------------------------------------- chapter 10
def _chapter10_core():
    return [
        H2("10.1 Improvements to the existing system"),
        N("**Score against the real closes.** Remove the clip from test targets, or fit scalers on a range that includes the test period's growth, and report persistence next to every model; this alone changes the direction figures from "
          f"{_sw('lstm_attention', 'directional_accuracy')[0] * 100:.0f} % to about {_sw('lstm_attention', 'da_true')[0] * 100:.0f} %.",
          "**Predict returns, not levels.** A target of next-day log return (or direction) is stationary, does not need level scaling and cannot be clipped away; levels follow by compounding.",
          "**Fill the sentiment channel for the whole history.** Fetch archived headlines (the FNSPID news used in the offline study, or a paid archive) so the channel is non-zero in training, and drop the synthetic fallback from the ablation.",
          "**Walk-forward validation.** Replace the single 80/20 split by rolling or expanding windows with many test periods, and report mean and spread, as the offline study already does for direction.",
          "**Refresh and retrain.** Write the training date into the artefact, retrain on a schedule, and have the Forecast screen compare the stored forecast with the realised closes automatically (the screen already shows a banner and the miss columns).",
          "**Honest uncertainty.** Use residuals from walk-forward folds to build prediction intervals, or conformal intervals, instead of a sqrt(h) band built from one-step residuals."),
        P("These six changes are small relative to the model work and each addresses a measured defect. Together they would turn the product's evaluation from a demonstration of the base paper's recipe into a test of whether that recipe has any predictive value on current data."),
        H2("10.2 Additional features"),
        B("**A multiple-instance model in the product.** Promote `scripts/mil_study.py` into `backend/app/`: embed each day's headlines, pool them with gated attention, and show which headlines received the most weight on the Sentiment screen.",
          "**A direction classifier with precision, recall and F1.** Add a classification head and report a confusion matrix per ticker, with a probability threshold the user can move.",
          "**A social-media source.** Add a licensed or public discussion feed as a second bag per day, so that the multi-source claim is true; keep it optional behind a key.",
          "**A baseline panel.** Show persistence and drift on every forecast chart so a user can see at a glance whether a model adds anything.",
          "**More inputs.** Technical indicators (moving averages, as in the base paper), volume features, sector indices and macro-economic series."),
        P("Each feature should be added behind a flag and scored with the same five-seed, true-target, persistence-relative protocol used in this report, so that a new component is kept only if it beats the baseline by clearly more than the seed-to-seed spread. "
          f"Across the five seeds the standard deviation of the true-target MAE was about ${_seed_std('lstm'):.1f} for the LSTM and ${_seed_std('lstm_attention'):.1f} for LSTM plus attention, but ${_seed_std('lstm_attention_sentiment'):.1f} for the sentiment tier and ${_seed_std('hybrid_federated'):.1f} for the federated tier, "
          "so a difference of a few dollars between two single runs of the unstable tiers means nothing."),
        H3("10.2.1 How much data the next study needs"),
        P(f"The standard error of an accuracy figure measured on n samples near 50 % is about sqrt(0.25 / n). With the {F.MIL['n_test_pooled']:,} test samples of the offline study it is {100 * (0.25 / F.MIL['n_test_pooled']) ** 0.5:.1f} accuracy points, so a 95 % interval is about +-{196 * (0.25 / F.MIL['n_test_pooled']) ** 0.5:.1f} points wide, which is the reason the observed gaps of one to two points cannot be told from zero. "
          f"To detect a real gain of one point the standard error must fall to about 0.5 points, which needs on the order of {int(0.25 / 0.005 ** 2):,} independent test samples; that means more tickers (several hundred rather than seven) and several years of dense headlines, not just more seeds, because seeds repeat the same test days."),
        H2("10.3 Scalability and deployment"),
        P("The API is stateless apart from its JSON files, so it scales horizontally behind a reverse proxy once a database or object store replaces the files. Stored forecasts already answer in about "
          f"{F.API['endpoints']['forecast_short']['median_ms']:.0f} ms; the two slow routes are the history download ({F.API['endpoints']['history_120d']['median_ms']:.0f} ms median, it calls Yahoo Finance on every request) and the sentiment route (about {F.API['endpoints']['sentiment']['median_ms'] / 1000:.1f} s median, FinBERT inference). "
          "Both should move to a scheduled job and a cache. A real deployment also needs authentication, rate limits, a database for prices, headlines and forecasts, a model registry, monitoring of forecast error against realised prices, and a container image (the Dockerfile exists but was not exercised here)."),
        P("The offline MIL script is a reasonable starting point for the product version: it already builds bags with a no-look-ahead time rule, embeds headlines with FinBERT-tone, pools them with mean, max or gated attention, and reports accuracy, precision, recall and F1 with paired bootstrap intervals. "
          "What it lacks is a serving path (embedding a day's headlines on request), an instance-relevance filter and a store for the headline archive."),
        H2("10.4 Further research"),
        B("**Real federated learning.** Run clients in separate processes or machines, normalise scales across clients, and measure communication cost, drop-out and what federation does to accuracy, since the simulated version made the forecasts worse.",
          "**Longer news history and more tickers.** The offline study covers seven tickers in 2022-2023; repeating it with a denser archive and many more tickers would give the statistical power that 1,309 test samples lack.",
          "**Better MIL formulations.** Instance-level relevance to the ticker (many headlines mention several companies), transformer instance encoders, and bag-level losses that cope with empty bags.",
          "**Explanation and trust.** Attention weights over headlines, calibration of direction probabilities and a comparison with a purely statistical benchmark for every claim.",
          f"**Market microstructure and regime effects.** Test whether any news effect appears at an intraday horizon, where daily stamps and close-to-close labels hide it; the base paper itself lists larger-scale sentiment datasets and real-world federation as future work [{R['base']}]."),
        H2("10.5 A suggested order of work"),
        TAB("Roadmap", ["Step", "Change", "Why first", "Effort"],
            [["1", "Persistence baseline and true-target scoring in `backend/train.py` and the Models screen", "Removes the main overstatement; a few lines of code", "Small"],
             ["2", "Train on returns or direction; walk-forward folds", "Makes the evaluation honest and the target stationary", "Medium"],
             ["3", "Archived headlines for the full history; drop the synthetic fallback from the ablation", "Gives the sentiment tier a chance to learn", "Medium"],
             ["4", "Promote the MIL model into the backend with a classifier head and a P/R/F1 panel", "Meets objectives 3 and 5 inside the product", "Medium"],
             ["5", "Social-media feed as a second bag", "Meets the multi-source claim", "Medium to large"],
             ["6", "Scheduled retraining, forecast-vs-actual tracking, database, authentication", "Production readiness", "Large"],
             ["7", "Real federated clients", "Tests whether federation helps at all", "Large"]],
            widths=[0.5, 3.0, 2.3, 0.8], align=["c", "l", "l", "c"], size=9.5),
        P("Steps 1 to 3 are cheap and decide whether the later steps are worth taking: if returns remain unpredictable once the evaluation is honest, the MIL and federation work should be judged as research questions, not as product features."),
        P("A final research question concerns the evaluation itself. A daily direction label is noisy: a one-cent move counts as 'up'. Labels that ignore moves smaller than a cost-aware threshold, or that use the sign of an excess return over a market index, would remove most of the coin-flip component and make any real signal easier to detect. "
          "The offline study's pooled up-day share of 53.6 % shows how close to a coin flip the plain label is."),
        P("None of these steps should be taken without first adding the persistence baseline and true-target scoring; both are cheap and would have prevented the main overstatements found here."),
    ]


def future_blocks():
    return _strip(_chapter10_core())


def chapter10_blocks():
    return [H1("10. FUTURE SCOPE")] + _chapter10_core()
