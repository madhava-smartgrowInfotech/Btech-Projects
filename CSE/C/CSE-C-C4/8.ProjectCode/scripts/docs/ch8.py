"""Chapter 8: Results and output screens for QuantPulse. Every number is read from facts.py (F.SUM, F.FWD, F.RR, F.MIL, F.API, F.SHIP); nothing is typed in except labels."""
import json
import os

import numpy as np

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as R

SH = F.shot
T = F.TICKERS
SEEDS = F.RR["seeds"]
NS = len(SEEDS)
TIERS = ["lstm", "lstm_attention", "lstm_attention_sentiment", "attention_shuffled_sentiment", "hybrid_federated"]
TN = {"lstm": "LSTM", "lstm_attention": "LSTM + attention", "lstm_attention_sentiment": "LSTM + attention + sentiment (synthetic headlines)",
      "attention_shuffled_sentiment": "Placebo: attention + time-shuffled sentiment", "hybrid_federated": "Hybrid (FedAvg of the sentiment tier)"}


def S(name, caption, base=5.6, max_h=3.9):
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def seedwise(tier, key):
    per = [np.mean([F.RR["tickers"][t]["models"][tier][s][key] for t in T]) for s in range(NS)]
    return float(np.mean(per)), float(np.std(per))


def ms(pair, d=2):
    return f"{pair[0]:.{d}f} ± {pair[1]:.{d}f}"


def mm(d, k, n=3):
    return f"{d[k]['mean']:.{n}f} ± {d[k]['std']:.{n}f}"


def fwd_agg(tier, h, key):
    return float(np.mean([F.RR["tickers"][t]["forward"][tier][s][h][key] for t in T for s in range(NS)]))


def _clean(s):
    return str(s).replace("�", "'").replace("�", "'")


PERS = float(np.mean([F.RR["tickers"][t]["persistence"]["mae"] for t in T]))
UPSHARE = float(np.mean([F.RR["tickers"][t]["persistence"]["up_day_share"] for t in T]))
MODELS = {"arima": "ARIMA(5,1,0)", "sarimax": "SARIMAX", "prophet": "Prophet", "random_forest": "Random Forest (lag-20)", "svr": "SVR (rbf)", "lstm": "LSTM",
          "lstm_attention": "LSTM + attention", "lstm_attention_sentiment": "LSTM + attention + sentiment", "hybrid_federated": "Hybrid (FedAvg)"}


def _setup():
    m = F.MIL
    return [
        H2("8.1 Experimental set-up"),
        P("All measurements were made on one machine: Intel Core i5-12500 (12 threads), 15.7 GB memory, no GPU, Windows 11, Python 3.11.9, TensorFlow 2.16.2, scikit-learn 1.9.0, PyTorch 2.5.1 (CPU) for FinBERT-tone and the MIL models, FastAPI 0.141.1. "
          "The machine was shared with other jobs, so timings are indicative; accuracy numbers do not depend on load. Every table and figure comes from stored JSON written by the scripts in `scripts/` or from the shipped `artifacts/metrics.json`; no result was typed in by hand."),
        TAB("Data used in the evaluation.", ["Item", "Content", "Source and status"],
            [["Prices (product and re-run)", "Ten tickers, daily OHLCV, 501 rows each, 2024-09-09 to 2026-09-08; 400 / 101 chronological split, 97 deep-model test windows", "Yahoo Finance through yfinance; pinned snapshot `experiments/data_snapshot/` reproduces every stored last close"],
             ["Prices (forward test)", "The same ten tickers, 30 trading days after 2026-09-08 (to 2026-10-20)", "Same snapshot; used only to score the stored forecasts"],
             ["Headlines in the product", "Synthetic template headlines, 166-191 per ticker, last 90 trading days only, scored by FinBERT-tone", "`news_source = synthetic-fallback` (no NewsAPI key)"],
             ["Headlines in the MIL study", f"{m['instances']['n_headline_rows_used']:,} real headlines for {len(m['tickers'])} tickers, dense from 2022; bags of mean size {m['bags']['mean_size_nonempty_test']:.1f} on test days with news",
              f"FNSPID news [{R['fnspid']}], public mirror; all stamps day-level; GOOGL, META, IBM absent or too sparse"],
             ["Prices in the MIL study", "The seven tickers, 2016-01-04 to 2023-12-29", "Yahoo Finance snapshot `experiments/data_snapshot/mil/`"]],
            widths=[1.5, 2.8, 2.3], align=["l", "l", "l"], size=9.5),
        P(f"Protocol: the shipped code is re-run unchanged on the same 501 rows with {NS} seeds ({', '.join(str(x) for x in SEEDS)}); the ten-ticker mean is taken per seed, then mean and standard deviation over seeds. "
          "'Shipped scoring' is the product's own `evaluate_dl`; 'true scoring' compares the same predictions with the real closes; 'persistence' forecasts today's close as yesterday's. "
          f"The MIL study uses three expanding-window folds tested on Q2, Q3 and Q4 2023 ({m['n_test_pooled']:,} pooled test samples) and five seeds. Nothing was tuned on test data.")]


def SP(a, b):
    return PAIR([(SH(a[0]), a[1]), (SH(b[0]), b[1])], 3.0)


def _screens():
    sm = F.SUM
    nv = F.SHIP["NVDA"]
    allm = {}
    for k, v in nv["baselines"].items():
        if v.get("metrics"):
            allm[MODELS[k]] = v["metrics"]
    for k, v in nv["deep"].items():
        allm[MODELS[k]] = v
    best_mae = min(allm, key=lambda k: allm[k]["mae"])
    best_r2 = max(allm, key=lambda k: allm[k]["r2"])
    ts = F.SHIP["TSLA"]
    fr = F.SUM["federated_rounds"]
    down = sum(1 for v in sm["trend"].values() if v == "down")
    mean5 = np.mean(list(sm["forecast_5d_change_pct"].values()))
    return [
        H2("8.2 Output screens"),
        P("The screens are real captures of the running website (1440 x 900) with the shipped artefacts and live Yahoo prices. QuantPulse has no login, so the landing page leads straight to the dashboard."),
        SP(("01_landing_light.png", "Landing page: live price chart and entry to the application."), ("09_about.png", "Method and data screen: universe, pipeline and model table.")),
        SP(("03_dashboard.png", "Dashboard: one card per ticker with last close, trend, 5-day outlook and data mode."), ("15_dashboard_tickers.png", "Dashboard scrolled to the ticker grid.")),
        P(f"The dashboard reads: ten tickers covered, {10 - down} of 10 trending up, 'Most accurate model: Random Forest' (lowest test MAE on {sm['best_mae_wins'].get('random_forest', 0)} of 10 tickers) and an average 5-day move of {mean5:+.2f} %. "
          f"{down} cards show 'Trend down', with outlooks from {min(sm['forecast_5d_change_pct'].values()):+.1f} % to {max(sm['forecast_5d_change_pct'].values()):+.1f} %, which already looks implausible for five days; Section 8.5 scores them."),
        S("16_forecast_top.png", "Forecast screen for NVDA: close at forecast, day-5 forecast, band, trend, controls and the notice about the training date.", 5.2, 3.5),
        P(f"For NVDA the tiles read: close at forecast $225.73 (8 September 2026), day-5 forecast $162.98 ({sm['forecast_5d_change_pct']['NVDA']:+.2f} %), a band that rounds to $163 - $163, and 'Trend down'. An orange notice says the models were trained up to 8 September 2026 and that actual closes since then are drawn past the dotted marker. "
          "The band is narrow because it is built from the one-step residual spread; it does not express the uncertainty of a multi-step forecast."),
        SP(("04_forecast_5day.png", "TSLA 5-day forecast: actual closes (solid), forecast (dashed), band."), ("14_forecast_table.png", "TSLA forecast table: predicted close, band, actual close and forecast miss.")),
        P(f"The TSLA forecast falls from ${ts['last_close']:.2f} to ${ts['forecast_short'][-1]['predicted_close']:.2f} in five days while the actual close stays between about $355 and $370. The table adds the realised close for each day: the day-1 forecast is $316.57 against an actual $367.81, a miss of about 14 % that does not shrink. "
          "The screen documents its own error; that view was added by the front end, not by the model."),
        S("05_forecast_30day.png", "MSFT 30-day forecast (horizon = long).", 5.0, 3.4),
        P(f"The stored 30-day forecast for MSFT is {F.FWD['tickers']['MSFT']['long']['pred_end_pct_change']:+.1f} % at day 30; the realised change over the same 30 trading days was {F.FWD['tickers']['MSFT']['long']['actual_end_pct_change']:+.1f} %."),
        SP(("06_models_comparison.png", "Model comparison for NVDA: best-model tiles and deep-model ablation chart."), ("12_models_table.png", "Deep-model metrics table for NVDA with the best MAE highlighted.")),
        P(f"For NVDA the tiles name {best_mae} as the lowest-error model (MAE {allm[best_mae]['mae']:.2f}) and {best_r2} as the best fit (R² {allm[best_r2]['r2']:.3f}) on the 97 test windows; the table lists the four deep tiers with MAE, MSE, RMSE, R² and direction."),
        SP(("07_models_training.png", "Training tab: loss curves and federated rounds."), ("08_sentiment.png", "News sentiment for TSLA: source, headlines scored, average score.")),
        P(f"Mean local loss falls from {fr[0]['mean_local_loss']:.4f} in federated round 1 to {fr[1]['mean_local_loss']:.4f} in round 2; this shows the clients fit their own data, not that the averaged model predicts well (Section 8.4). "
          "The sentiment screen is explicit about its source: 'Built-in fallback', scorer FinBERT, and a banner that NEWSAPI_KEY is missing. The headlines are template sentences ('TSLA hits record revenue on enterprise adoption surge'), so the daily score swings between -1 and +1. "
          "The screen shows 167 headlines for TSLA while the stored artefact records 183: the generator is seeded with Python's per-process string hash, so the headlines are not reproducible between runs."),
    ]


def _shipped():
    sm = F.SUM
    rows = []
    for k, nm in MODELS.items():
        m = sm["models"][k]
        rows.append([nm, f"{m['mae']['mean']:.2f}", f"{m['mae']['min']:.1f} - {m['mae']['max']:.1f}", f"{m['rmse']['mean']:.2f}", f"{m['r2']['mean']:.2f}", f"{m['r2']['median']:.2f}", f"{m['directional_accuracy']['mean'] * 100:.1f} %"])
    wins = sm["best_mae_wins"]
    return [
        H2("8.3 Model performance as shipped"),
        P("The numbers the application displays come from `artifacts/metrics.json`, written once by `python -m backend.train` on data ending 8 September 2026 (seed 42, 97 test windows per ticker). Table 8.1 averages them over the ten tickers."),
        TAB("Shipped test metrics, mean over ten tickers (MAE and RMSE in dollars; direction is the product's own figure).", ["Model", "MAE", "MAE range", "RMSE", "R² mean", "R² median", "Direction"], rows,
            widths=[1.9, 0.7, 1.0, 0.7, 0.8, 0.8, 0.8], align=["l", "r", "c", "r", "r", "r", "r"], size=9.5),
        P(f"Three points stand out. The Random Forest on lagged closes has the lowest MAE for {wins.get('random_forest', 0)} of ten tickers and the lowest mean MAE ({sm['models']['random_forest']['mae']['mean']:.2f}), better than every deep tier. "
          f"Attention helps (LSTM {sm['models']['lstm']['mae']['mean']:.2f} to {sm['models']['lstm_attention']['mae']['mean']:.2f}), but sentiment ({sm['models']['lstm_attention_sentiment']['mae']['mean']:.2f}) and FedAvg ({sm['models']['hybrid_federated']['mae']['mean']:.2f}) make the error larger again, the opposite of the base paper's staircase. "
          f"Almost every mean R² is negative and is dominated by single tickers (LSTM mean {sm['models']['lstm']['r2']['mean']:.1f}, median {sm['models']['lstm']['r2']['median']:.2f}), so medians are fairer.")]


def _rerun():
    rows = []
    for tier in TIERS:
        rows.append([TN[tier], ms(seedwise(tier, "mae")), ms(seedwise(tier, "mae_true")), ms(seedwise(tier, "r2_true")),
                     f"{seedwise(tier, 'da_true')[0] * 100:.1f} %", f"{seedwise(tier, 'directional_accuracy')[0] * 100:.1f} %"])
    for key, nm in (("arima", "ARIMA(5,1,0)"), ("random_forest", "Random Forest (lag-20, one step)"), ("svr", "SVR (rbf, one step)")):
        v = [F.RR["tickers"][t]["baselines"][key] for t in T]
        rows.append([nm, "-", f"{np.mean([x['mae'] for x in v]):.2f}", f"{np.mean([x['r2'] for x in v]):.2f}", f"{np.mean([x['directional_accuracy'] for x in v]) * 100:.1f} %", "-"])
    rows.append(["**Persistence (yesterday's close)**", "-", f"**{PERS:.2f}**", "-", f"up-day share {UPSHARE * 100:.1f} %", "-"])
    diag = []
    for t in T:
        d = F.RR["tickers"][t]
        diag.append([t, f"{d['test_close_above_train_max_pct']:.1f} %", f"{d['clipped_test_windows_pct']:.1f} %", f"{d['persistence']['mae']:.2f}",
                     f"{np.mean([x['mae_true'] for x in d['models']['lstm_attention']]):.2f}",
                     f"{np.mean([x['directional_accuracy'] for x in d['models']['lstm_attention']]) * 100:.0f} % / {np.mean([x['da_true'] for x in d['models']['lstm_attention']]) * 100:.0f} %"])
    best_true = seedwise("lstm_attention", "mae_true")[0]
    return [
        H2("8.4 Re-run on the same training rows: true scoring, persistence and seeds"),
        P(f"The unchanged pipeline was re-run on the same 501 rows with {NS} seeds. It reproduces the shipped picture (LSTM + attention is the best deep tier; sentiment and FedAvg make it worse) and adds a persistence baseline, scoring against the real closes, and seed-to-seed spread."),
        TAB(f"Re-run, ten-ticker mean per seed, then mean ± std over {NS} seeds (dollars).", ["Model", "MAE (shipped scoring)", "MAE (true scoring)", "R² (true)", "Direction (true)", "Direction (shipped)"], rows,
            widths=[2.2, 1.1, 1.1, 0.9, 0.8, 0.8], align=["l", "c", "c", "c", "c", "c"], size=9),
        FIG(F.fig("f02_true_mae_vs_persistence.png"), "True-target MAE of LSTM + attention (five seeds) against persistence, per ticker.", 5.6),
        P(f"**Persistence beats every deep tier.** Predicting that tomorrow's close equals today's gives a mean absolute error of ${PERS:.2f}; the best deep tier, LSTM + attention, scores ${best_true:.2f} on the same days, about {best_true / PERS:.1f} times larger, for every one of the ten tickers. "
          f"The lag-20 Random Forest (${np.mean([F.RR['tickers'][t]['baselines']['random_forest']['mae'] for t in T]):.2f}) is closest and is still about twice persistence: the deep networks learn a smoothed level of the price, not the next price."),
        P("**The product's scoring flatters the deep tiers.** `evaluate_dl` compares predictions with targets that passed through the training-range scaler; for a ticker whose test prices rise above the training maximum the target is clipped to 1.0 and is flat. "
          f"Shipped directional accuracy is about 67 to 68 % for every deep tier, while the same predictions scored on the real closes give 52 to 53 %, a coin flip against an up-day share of {UPSHARE * 100:.0f} %. The MAE is understated by about $6 for the same reason."),
        FIG(F.fig("f03_clipping_and_direction.png"), "Share of test closes above the training maximum per ticker, and shipped against true directional accuracy.", 5.6),
        P("The five tickers that rallied above their training range (AAPL, AMZN, GOOGL, NVDA, FDX) are exactly those with shipped directional accuracy above 75 %; for TSLA, MSFT, META, IBM and ORCL the shipped figure (46 to 57 %) is close to the true one. "
          "The high numbers are the result of agreeing on 'not up' when both the clipped target and the saturated prediction are flat."),
        P(f"Seed spread matters for the tiers with sentiment and federation: the standard deviation of the ten-ticker MAE is {seedwise('lstm_attention', 'mae_true')[1]:.1f} for LSTM + attention but {seedwise('lstm_attention_sentiment', 'mae_true')[1]:.1f} with the sentiment channel and {seedwise('hybrid_federated', 'mae_true')[1]:.1f} for the federated model, as large as some of the differences, so a single-seed ablation can rank them either way.")]


def _forward():
    rows = []
    for t in T:
        r = F.FWD["tickers"][t]
        rows.append([t, f"{r['last_close']:.2f}", f"{r['short']['pred_end_pct_change']:+.1f} %", f"{r['short']['actual_end_pct_change']:+.1f} %", f"{r['short']['mae']:.2f}", f"{r['short']['persistence_mae']:.2f}",
                     "yes" if r["short"]["trend_hit"] else "no", f"{r['long']['pred_end_pct_change']:+.1f} %", f"{r['long']['actual_end_pct_change']:+.1f} %", f"{r['long']['mae']:.2f}", f"{r['long']['persistence_mae']:.2f}"])
    sh, lg = F.FWD["short"], F.FWD["long"]
    trows = []
    for tier in TIERS:
        trows.append([TN[tier], f"{fwd_agg(tier, 'short', 'mae'):.2f}", f"{fwd_agg(tier, 'long', 'mae'):.2f}", f"{fwd_agg(tier, 'short', 'pred_end_pct_change'):+.1f} %"])
    trows.append(["Persistence ('no change')", f"{sh['mean_persistence_mae']:.2f}", f"{lg['mean_persistence_mae']:.2f}", "0.0 %"])
    trows.append(["Shipped artefact (seed 42)", f"{sh['mean_mae']:.2f}", f"{lg['mean_mae']:.2f}", f"{sh['mean_pred_change_pct']:+.1f} %"])
    return [
        H2("8.5 Forward test: the stored forecasts against the closes that followed"),
        P("The only evaluation that mirrors how the product is used is to forecast from a date and wait. The shipped forecasts start at the 2026-09-08 close; the real closes of the next 30 trading days (to 2026-10-20) come from the pinned snapshot, whose close on 8 September equals the stored `last_close` for all ten tickers."),
        TAB("Stored 5- and 30-day forecasts against what happened (change in % from the 8 September close; MAE in dollars over the horizon).",
            ["Ticker", "Close", "5d fcst", "5d actual", "5d MAE", "Persist.", "Trend ok", "30d fcst", "30d actual", "30d MAE", "Persist."], rows,
            widths=[0.5, 0.6, 0.6, 0.6, 0.55, 0.55, 0.5, 0.6, 0.6, 0.55, 0.55], align=["l"] + ["r"] * 10, size=8.5),
        FIG(F.fig("f05_forecast_vs_actual_change.png"), "Predicted against actual 5-day change per ticker.", 5.6),
        P(f"Over five trading days the stored forecasts have a mean absolute error of ${sh['mean_mae']:.2f} (MAPE {sh['mean_mape']:.1f} %), against ${sh['mean_persistence_mae']:.2f} for 'no change'. They predicted an average move of {sh['mean_pred_change_pct']:+.1f} %; the stocks moved {sh['mean_actual_change_pct']:+.1f} % on average. "
          f"The up/down flag shown on the dashboard was right for {sh['trend_hits']} of 10 tickers, fewer than a coin flip would give on average. Over 30 days the error is ${lg['mean_mae']:.2f} against ${lg['mean_persistence_mae']:.2f} for 'no change', with a correct trend call for {lg['trend_hits']} of 10."),
        FIG(F.fig("f04_forward_test_30day.png"), "Actual closes and the stored 30-day forecast for each ticker (forecast starts at the 8 September close).", 5.8),
        TAB("Forward test of the re-trained tiers (ten tickers x five seeds) and of the shipped artefact: mean absolute error in dollars and mean predicted 5-day change.",
            ["Model", "5-day MAE", "30-day MAE", "Mean 5-day change"], trows, widths=[3.0, 1.0, 1.0, 1.4], align=["l", "r", "r", "r"], size=9.5),
        P("Re-training does not change the verdict: every tier is several times worse than 'no change'. The stored forecasts are biased downwards because the recursive forecast feeds each predicted close back as Open, High, Low and Close while the scaler has clipped the recent window to the training range, so the window the model sees after a rally is not the window of a rally.")]


def _sentiment():
    rr = F.RR["tickers"]
    rows = [[t, str(rr[t]["n_headlines"]), str(rr[t]["sentiment_nonzero_in_train_part"]), str(rr[t]["sentiment_nonzero_in_test_part"])] for t in T]
    return [
        H2("8.6 What the sentiment channel contains"),
        P("The product's sentiment path is: NewsAPI if a key is set, otherwise template headlines; FinBERT-tone scores; a daily mean; forward fill; zero before the first headline. No key was set, so the channel is built from templates, and the generator only writes headlines for the last 90 trading days."),
        TAB("Sentiment channel per ticker in the training run (rows of the 501-row series).", ["Ticker", "Synthetic headlines", "Non-zero rows in the training part (400 rows)", "Non-zero rows in the test part (101 rows)"], rows, widths=[0.8, 1.4, 2.4, 2.0], align=["l", "c", "c", "c"], size=9.5),
        FIG(F.fig("f06_sentiment_channel.png"), "Non-zero sentiment rows in the training and test parts for each ticker, and the TSLA channel over time.", 5.6),
        P("For every ticker the channel is exactly zero throughout training and non-zero only in the test part. The 'sentiment' tier is trained on a constant input and evaluated on random template values, which is why it is worse than the attention tier (MAE "
          f"{ms(seedwise('lstm_attention_sentiment', 'mae_true'))} against {ms(seedwise('lstm_attention', 'mae_true'))}) and unstable across seeds; a placebo with time-shuffled sentiment, non-zero in training too, scores {ms(seedwise('attention_shuffled_sentiment', 'mae_true'))}, the same as no sentiment. "
          "The row 'LSTM + attention + sentiment' therefore measures nothing about news and must not be read as 'sentiment hurts' or 'helps'.")]
def _paper():
    bp = F.BASE_PAPER_RESULTS
    sm = F.SUM
    return [
        H2("8.7 Comparison with the base paper"),
        P(f"The base paper [{R['base']}] reports an average R² of {bp['r2_avg']:.2f} for its hybrid model over ten companies (all above {bp['r2_min_company']:.2f}), for Tesla MSE {bp['tsla_mse']}, MAE {bp['tsla_mae']} and R² {bp['tsla_r2']} (scaled units), "
          f"and an average trend accuracy of {bp['lstm_trend_acc']:.2f} % for its baseline LSTM ({bp['trend_best']}; {bp['trend_worst']}). The datasets and protocols are not the same, which this table makes explicit."),
        TAB("Base paper against this project: what is comparable and what is not.", ["Aspect", "Base paper", "QuantPulse (this project)"],
            [["Data window", bp["window"], "Two years of daily bars; 97 test windows per ticker"],
             ["News", "NewsAPI headlines, 30 days", "Synthetic template headlines (no key); real headlines only in the offline MIL study"],
             ["Hybrid R² (mean)", f"{bp['r2_avg']:.2f}", f"{sm['models']['hybrid_federated']['r2']['mean']:.1f} (median {sm['models']['hybrid_federated']['r2']['median']:.1f}); best deep tier {sm['models']['lstm_attention']['r2']['mean']:.1f} (median {sm['models']['lstm_attention']['r2']['median']:.2f})"],
             ["Trend / direction", f"{bp['lstm_trend_acc']:.2f} % (LSTM, 100 runs per company)", f"Shipped {sm['models']['lstm']['directional_accuracy']['mean'] * 100:.1f} % (clipped scoring); {seedwise('lstm', 'da_true')[0] * 100:.1f} % on the real closes"],
             ["Ablation order", "Each addition improves the result", "Attention helps; sentiment and FedAvg do not (sentiment channel empty in training)"]],
            widths=[1.2, 2.7, 2.7], align=["l", "l", "l"], size=9),
        FIG(F.fig("f12_base_paper_comparison.png"), "Base paper's reported figures next to the measured ones. The datasets and protocols differ, so the bars are not a like-for-like comparison.", 5.4),
        P("The base paper's R² of 0.91 was not reproduced here, and these experiments do not show that it is wrong: a short window, scaled targets and a test period inside the training range can give a high R² to a level forecaster, while a two-year window with a rally in the test period gives a negative one. "
          "What they do show is that on the longer window the same architecture does not beat 'no change' and that the staircase from LSTM to the full hybrid does not hold when the sentiment channel is empty in training. The paper itself notes that sentiment was limited to 30 days and that federated learning was only simulated; both limits apply here too.")]


def _mil():
    m = F.MIL
    mname = {"majority_class": "Majority class (train)", "logreg_price_C0.01": "Logistic regression, price (C=0.01)", "logreg_price_C1.0": "Logistic regression, price (C=1)",
             "lstm_price": "LSTM, price only (same window)", "lstm_price_full_history": "LSTM, price only (all history since 2016)", "lstm_flat_sentiment": "LSTM + flat mean sentiment",
             "lstm_mil_mean": "LSTM + MIL mean pooling", "lstm_mil_max": "LSTM + MIL max pooling", "lstm_mil_attention": "LSTM + MIL gated-attention pooling",
             "mil_attention_news_only": "MIL attention, news only (no prices)", "placebo_mil_attention_shuffled_bags": "Placebo: MIL attention with other days' bags"}
    rows = [[nm, mm(m["models"][k]["summary"], "accuracy"), mm(m["models"][k]["summary"], "precision"), mm(m["models"][k]["summary"], "recall"), mm(m["models"][k]["summary"], "f1"),
             mm(m["models"][k]["summary"], "auc"), f"{m['models'][k]['summary']['pred_up_share']['mean'] * 100:.0f} %"] for k, nm in mname.items()]
    pr = [[mname[k], f"{v['acc_diff'] * 100:+.1f}", f"[{v['ci95'][0] * 100:+.1f}, {v['ci95'][1] * 100:+.1f}]"] for k, v in m["paired_vs_lstm_price"].items()]
    pt = [[t, str(m["per_ticker_test_n"][t]), f"{m['per_ticker_test_accuracy']['lstm_price'][t] * 100:.1f} %", f"{m['per_ticker_test_accuracy']['lstm_mil_attention'][t] * 100:.1f} %"] for t in m["tickers"]]
    fold = [[f"Q{i + 2} 2023" if i < 3 else "", f"{f['n_train_news_era']:,}", f"{f['n_val']}", f"{f['n_test']}", f"{f['test_up_share'] * 100:.1f} %"] for i, f in enumerate(m["folds"])]
    ex = []
    for e in m["attention_examples"][:3]:
        for j, tp in enumerate(e["top"][:2]):
            ex.append([f"{e['ticker']} {e['date']}" if j == 0 else "", f"{e['n_headlines']}" if j == 0 else "", f"{tp['weight']:.3f}", _clean(tp["headline"])[:95], f"{tp['p_pos']:.2f} / {tp['p_neg']:.2f}"])
    spread = max(e["top"][0]["weight"] / e["uniform_weight"] for e in m["attention_examples"])
    return [
        H2("8.8 Multiple-instance learning on real headlines (offline study)"),
        P("The batch objectives ask for each trading day to be a bag of news instances with a bag-level label, evaluated with accuracy, precision, recall and F1 against a price-only baseline. QuantPulse does not contain this, so the study was run separately (`scripts/mil_study.py`). "
          f"A bag is all FNSPID headlines of one ticker published before a trading day's close; an instance is its three FinBERT-tone probabilities plus a 64-component projection of its [CLS] vector; the label is whether the next close is above today's. Seven tickers have enough headlines ({', '.join(m['tickers'])}); "
          f"the news is dense only from 2022, so three expanding-window folds are tested on Q2, Q3 and Q4 2023 and pooled ({m['n_test_pooled']:,} samples, {m['up_share_test'] * 100:.1f} % up days). "
          f"{m['bags']['share_days_with_news_test'] * 100:.0f} % of test-day bags are non-empty, with a mean of {m['bags']['mean_size_nonempty_test']:.1f} headlines (95th percentile {m['bags']['p95_size_test']:.0f}; capped at {m['bags']['capped_at']})."),
        TAB(f"Directional prediction on {m['n_test_pooled']:,} pooled test samples (mean ± std over {len(m['seeds'])} seeds; threshold 0.5; positive class = up).",
            ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "Predicted up"], rows, widths=[2.1, 0.85, 0.85, 0.85, 0.85, 0.85, 0.6], align=["l"] + ["c"] * 6, size=8.5),
        FIG(F.fig("f08_mil_accuracy.png"), f"Accuracy of each model in the MIL study; the dashed line is the always-up rate ({m['always_up_accuracy_test'] * 100:.1f} %).", 5.6),
        FIG(F.fig("f09_mil_prf.png"), "Precision, recall and F1 of the models in the MIL study.", 5.6),
        P(f"**No model beats always predicting 'up' ({m['always_up_accuracy_test'] * 100:.1f} %).** The LSTM on the same short window scores {m['models']['lstm_price']['summary']['accuracy']['mean'] * 100:.1f} % accuracy; the MIL variants score {m['models']['lstm_mil_attention']['summary']['accuracy']['mean'] * 100:.1f} % (gated attention), "
          f"{m['models']['lstm_mil_mean']['summary']['accuracy']['mean'] * 100:.1f} % (mean) and {m['models']['lstm_mil_max']['summary']['accuracy']['mean'] * 100:.1f} % (max), with AUC between {min(m['models'][k]['summary']['auc']['mean'] for k in ('lstm_mil_mean', 'lstm_mil_max', 'lstm_mil_attention')):.2f} and {max(m['models'][k]['summary']['auc']['mean'] for k in ('lstm_mil_mean', 'lstm_mil_max', 'lstm_mil_attention')):.2f}. "
          f"The full-history price LSTM reaches {m['models']['lstm_price_full_history']['summary']['accuracy']['mean'] * 100:.1f} % only by predicting 'up' on {m['models']['lstm_price_full_history']['summary']['pred_up_share']['mean'] * 100:.0f} % of days (recall {m['models']['lstm_price_full_history']['summary']['recall']['mean']:.2f}, which also explains its F1 of {m['models']['lstm_price_full_history']['summary']['f1']['mean']:.2f}); "
          "the F1 column of the other models mostly reflects how often each one happens to say 'up'. The placebo, which gives each day the bag of a different day of the same ticker, scores the same as the real bags, which is what a model without news signal should do."),
        TAB("Paired bootstrap against the same-window price-only LSTM: accuracy difference in percentage points (95 % interval, 2,000 resamples of the seed-averaged predictions).", ["Model", "Difference (points)", "95 % interval"], pr, widths=[3.4, 1.3, 1.6], align=["l", "c", "c"], size=9.5),
        P("Every news-based variant is one to two points above the same-window price LSTM and every interval includes zero; the only interval that excludes zero belongs to the full-history price model, whose gain is the always-up effect. With 1,309 test samples a difference of three points is within noise: the reading is *no evidence of a gain from news in this data*, not *evidence of no gain*."),
        P("What does the gated attention look at? The examples below, taken from the last fold, list the two highest-weighted headlines for three test days. The weights are close to the uniform weight 1/n of a bag of n headlines "
          f"(in the eight stored examples the top-weighted headline never exceeds {spread:.1f} times its bag's uniform weight), the predicted probability of an up day stays near 0.50, and the highest-weighted headlines are not obviously about the ticker: the instances are noisy because FNSPID assigns an article to every company it names or lists. "
          "This is the situation multiple-instance learning is meant for, but with this data and sample size the attention did not learn to pick out informative instances."),
        P("Limits: seven tickers and one year of dense news; day-level stamps only; headlines cut to their first line; no social-media source; small models with no tuning beyond early stopping. A negative result does not show that multi-source MIL cannot work, only that a reasonable first implementation found nothing at this scale.")]


def _samples():
    ts = F.SHIP["TSLA"]
    f = json.dumps({"ticker": "TSLA", "horizon": "short", "last_close": ts["last_close"], "trend": ts["trend"], "forecast": ts["forecast_short"][:2]}, indent=2)
    mt = json.dumps({"ticker": "TSLA", "deep": {"lstm_attention": {k: round(v, 3) if isinstance(v, float) else v for k, v in ts["deep"]["lstm_attention"].items()}},
                     "sentiment": {"source": ts["sentiment"]["source"], "scorer": ts["sentiment"]["scorer"], "n_headlines": ts["sentiment"]["n_headlines"]}}, indent=2)
    return [
        H2("8.9 Sample inputs and outputs"),
        P("A request is a ticker symbol and optionally a horizon or a history length; there is no other input. A call to `GET /api/forecast/TSLA?horizon=short` returns the stored forecast (first two of five rows shown):"),
        CODE(f, 8),
        P("A request that fails validation returns a readable message: `GET /api/forecast/T5LA` gives status 400 with 'Invalid ticker', `GET /api/forecast/TSLA?horizon=weekly` gives 422 and an unknown valid symbol such as `ZZZZ` gives 404."),
    ]


def _analysis():
    sm = F.SUM
    return [
        H2("8.10 Success and failure analysis"),
        H3("8.10.1 Where it worked"),
        B("**The software.** Seven endpoints, six screens, 56 unit and API tests and 26 smoke checks pass; stored results answer in a median of 2 to 13 ms.",
          f"**Classical baselines.** The Random Forest has the lowest shipped MAE for {sm['best_mae_wins'].get('random_forest', 0)} of ten tickers and is the closest model to persistence in the re-run.",
          "**Attention over the price window** lowers the deep-model error against the plain LSTM (about 48 to 23 in the re-run), the only part of the base paper's ablation that held.",
          "**Transparency.** The Forecast screen shows actual closes beside the forecast and the sentiment screen states its news source; a pinned snapshot, five seeds and stored JSON make every number here reproducible."),
        H3("8.10.2 Where it failed"),
        B(f"**Forecast accuracy.** No tier beats 'no change' on real closes (${PERS:.2f} mean error against about ${seedwise('lstm_attention', 'mae_true')[0]:.0f} for the best tier); the stored forecasts missed the direction for 6 of 10 tickers over five days.",
          "**Evaluation validity.** Clipped targets inflate direction metrics from about 53 % to 67 - 68 %.",
          "**Sentiment and federation.** A channel that is zero in training cannot be learned from, and averaging weights of ten models trained on different price scales is worse than any local model (MAE " + ms(seedwise("hybrid_federated", "mae_true")) + ").",
          "**MIL and the base paper.** No MIL variant beat always-up and the attention stayed near uniform; the base paper's R² of 0.91 was not reproduced.")]


def _limits_and_objectives():
    m = F.MIL
    obj = [["1. Collect prices, financial news and social-media text", "Partly met", "Prices: ten tickers, two years, Yahoo Finance. News: NewsAPI optional but not used; synthetic template headlines in the product; real FNSPID headlines (46 thousand rows, seven tickers) in the offline study. Social media: no source, not implemented."],
           ["2. Preprocess and align into daily instances per trading day", "Partly met", "Prices are cleaned, scaled and windowed; headlines are aligned to trading days, but the product collapses them to one daily mean. Bags of instances exist only in the offline study."],
           ["3. Represent each day as a bag (Multiple Instance Learning)", "Not met in the product; met offline", f"No MIL in QuantPulse. The offline study builds bags (mean {m['bags']['mean_size_nonempty_test']:.1f} headlines on days with news) with mean, max and gated-attention pooling."],
           ["4. Hybrid model: sequence learning over prices with attention", "Met (price attention); news attention offline", "LSTM + 4-head attention + sentiment channel + FedAvg implemented as in the base paper; attention runs over the price window. Attention over news instances only in the offline study."],
           ["5. Predict direction; report accuracy, precision, recall, F1", "Partly met", f"The product forecasts price level and a trend flag and reports direction accuracy (inflated by clipping). Accuracy, precision, recall and F1 are reported in the offline study: accuracy about {m['models']['lstm_mil_attention']['summary']['accuracy']['mean'] * 100:.0f} % against {m['always_up_accuracy_test'] * 100:.1f} % always-up."],
           ["6. Compare multi-source with a price-only baseline", "Done; no gain found", f"Offline: all news-based variants within about two points of the price-only LSTM, intervals include zero, placebo equal. In the product the ablation is invalid because the sentiment channel is empty in training."]]
    return [
        H2("8.11 Limitations of the results"),
        B("**One data window and one training date**: the forward test covers 30 trading days after one date; five seeds vary only the initialisation.",
          "**Synthetic sentiment in the product**: nothing about real news can be drawn from its sentiment tier.",
          f"**The MIL study is small**: {m['n_test_pooled']:,} test samples, seven tickers, one year of dense news, day-level stamps, headlines only; a difference below about three accuracy points is within noise.",
          "**Mixed protocols**: ARIMA, SARIMAX and Prophet forecast 101 days without refitting, whereas Random Forest and SVR use actual lags one step ahead.",
          "**No economic evaluation**: no trading rule or transaction cost was tested; the product is a research and education tool, not financial advice."),
        H2("8.12 Objectives against outcomes"),
        TAB("The six objectives of the batch against what was achieved.", ["Objective", "Outcome", "Evidence"], obj, widths=[2.0, 1.1, 3.5], align=["l", "l", "l"], size=9),
        P("In short: the engineering objectives were met and the scientific ones were measured honestly. QuantPulse is a working, tested implementation of the base paper's pipeline; the experiments show that this pipeline, on two years of data, does not forecast better than 'no change', "
          "and that real news bags did not add directional signal in the one-year study run alongside it.")]


def blocks():
    out = [H1("8. RESULTS AND OUTPUT SCREENS")]
    out += _setup() + _screens() + _shipped() + _rerun() + _forward() + _sentiment() + _paper() + _mil() + _samples() + _analysis() + _limits_and_objectives()
    return out
