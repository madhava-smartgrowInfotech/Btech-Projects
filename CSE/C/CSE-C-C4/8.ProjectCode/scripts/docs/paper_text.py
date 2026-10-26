"""Text of 19.IEEE_Paper.docx (QuantPulse). Every number is read from facts.py (experiments/**/metrics.json) or from the base paper's text.

Citations are written {r:N} with the global reference numbers of refs.py; Paper.expand renumbers them in order of first appearance.
"""
import numpy as np

from . import facts as F
from . import paper_figs
from .paper import Paper
from .refs import CITE


def c(*keys):
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


def build(path):
    figs = paper_figs.make()
    P = Paper()
    RR, MIL, FWD, SUM, API = F.RR, F.MIL, F.FWD, F.SUM, F.API["endpoints"]
    T = list(RR["tickers"])
    S = len(RR["seeds"])
    bp = F.BASE_PAPER_RESULTS

    def tier(t, key):
        v = [np.mean([RR["tickers"][k]["models"][t][s][key] for k in T]) for s in range(S)]
        return float(np.mean(v)), float(np.std(v))

    def base(name, key):
        return float(np.mean([RR["tickers"][k]["baselines"][name][key] for k in T]))

    pers = float(np.mean([RR["tickers"][k]["persistence"]["mae"] for k in T]))
    m = MIL["models"]

    def ms(k, key):
        return m[k]["summary"][key]["mean"]

    best_true = tier("lstm_attention", "mae_true")
    da_ship = tier("lstm_attention", "directional_accuracy")[0] * 100
    da_true = tier("lstm_attention", "da_true")[0] * 100
    clip_n = sum(1 for k in T if RR["tickers"][k]["test_close_above_train_max_pct"] > 50)
    clip_max = max(RR["tickers"][k]["test_close_above_train_max_pct"] for k in T)
    n_test = MIL["n_test_pooled"]
    up = MIL["always_up_accuracy_test"] * 100
    pr = MIL["paired_vs_lstm_price"]
    fs, fl = FWD["short"], FWD["long"]
    shipped_mean5 = float(np.mean(list(SUM["forecast_5d_change_pct"].values())))
    down9 = sum(1 for v in SUM["trend"].values() if v == "down")
    pyr = MIL['instances']['per_year']
    share2223 = (pyr['2022'] + pyr['2023']) / sum(pyr.values()) * 100
    ex = max(MIL["attention_examples"], key=lambda e: e["n_headlines"]) if MIL["attention_examples"] else None

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"])
    P.title_block("QuantPulse: Stock Trend Forecasting with LSTM, Attention and News Sentiment, and a Multiple-Instance Study of Daily News", authors)
    P.begin_two_columns()

    P.abstract(
        "Predicting where a stock will close next is hard, and models that look at prices alone ignore the news. This paper presents QuantPulse, a working web platform that reproduces the pipeline of a 2026 hybrid forecasting paper "
        "(LSTM, multi-head attention, FinBERT-tone sentiment and simulated federated averaging) for ten stocks, and then evaluates it more strictly than the original. "
        f"Scored against real closes and a no-change baseline, no deep tier beat yesterday's close: the best tier's mean absolute error was ${best_true[0]:.1f} against ${pers:.1f}, "
        f"the stored 5-day forecasts averaged {shipped_mean5:+.1f} % against an actual {fs['mean_actual_change_pct']:+.1f} %, and the sentiment channel held only synthetic headlines. "
        "Because the project asks for multiple instance learning (MIL), we also ran an offline study in which a day's real headlines form a bag with only a bag-level label. "
        f"On {n_test:,} test days no MIL variant beat the always-up rate of {up:.1f} %, and all stayed within about two points of a price-only LSTM. We report the defects found and what was not measured.",
        ["federated learning", "financial news", "multiple instance learning", "sentiment analysis", "stock market prediction", "time-series forecasting"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para(f"Forecasting share prices matters to investors and risk managers, but the task is difficult because prices are noisy, non-stationary and, in the efficient-market view, close to unpredictable from their own past. "
           f"Classical models such as ARIMA {c('box')} and machine-learning regressors {c('rf', 'svr')} are the usual baselines, recurrent networks {c('lstm', 'fischer')} are the common deep alternative, "
           f"and recent studies add financial news {c('s_llm', 's_multimodal', 's_text')}. The cost of getting this wrong is quiet: a forecast that merely tracks yesterday's price can look accurate in R2 and still carry no information about tomorrow.")
    P.para(f"The base paper {c('base')} combines an LSTM, Transformer-style attention {c('transformer')}, FinBERT-tone sentiment {c('finbert_tone')} and simulated federated averaging {c('fedavg')} on ten technology stocks and reports an average R2 of {bp['r2_avg']}. "
           f"Our batch asks for a different formulation: each trading day as a bag of news instances, multiple instance learning (MIL) {c('dietterich', 'zhang')}, predicting direction with accuracy, precision, recall and F1 against a price-only baseline. "
           "QuantPulse implements the base paper's pipeline as a product but contains no MIL component and no social-media source; the gap is closed here by a separate offline study.")
    P.para("The contributions are: (1) QuantPulse, a tested end-to-end product (FastAPI, React, ten tickers, nine models, 5- and 30-day forecasts with bands); "
           "(2) an evaluation that scores every model on the real closes, against a persistence baseline, over five seeds and in a forward test on data that arrived after training; "
           "(3) a multiple-instance study on real FNSPID headlines with mean, max and gated-attention pooling and a shuffled-bag placebo; and (4) a list of defects and unmeasured items. "
           "Section II surveys the literature, Section III describes the method, Section IV gives the results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("Everything ran on one CPU-only desktop: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11, no GPU. "
           f"Re-running four deep tiers and the federated stage for ten tickers and five seeds took {RR['seconds'] / 60:.0f} minutes while other jobs shared the machine.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9, TensorFlow 2.16.2 and Keras 3.15 for the models, PyTorch 2.5.1 (CPU) and transformers 4.47 for FinBERT-tone inference and the MIL study, scikit-learn 1.9, statsmodels 0.15, Prophet 1.4 and yfinance 1.7 for data; "
           "FastAPI 0.141 for the service and React 19 with Vite 8 for the website; pytest for the 56 automated tests.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Nejatbakhsh and Aliasgari {c('base')} benchmark ARIMA, SARIMAX, Prophet, random forest and SVR against a 64-unit LSTM on ten stocks (Tesla, Apple, Airbnb, Amazon, FedEx, IBM, Microsoft, Nvidia, Oracle, Google), "
           f"then add multi-head attention, FinBERT-tone sentiment from NewsAPI headlines, and a simulated federated stage in which each company is a client trained locally and averaged with FedAvg. "
           f"They report a baseline LSTM trend accuracy of {bp['lstm_trend_acc']} % over 100 runs per company, an average R2 of {bp['r2_avg']} for the hybrid (every company above {bp['r2_min_company']}) and, for Tesla, R2 {bp['tsla_r2']}. "
           "The hybrid was trained on a one-month window because NewsAPI returned only 30 days of headlines, with a 70/15/15 split; the paper itself notes that federated learning was only simulated.")
    P.para(f"**News fusion and sentiment.** Studies that combine price series with sentiment from news include an LLM-based model {c('s_llm')}, multimodal feature fusion for Chinese stocks {c('s_multimodal')} and text mining with investor sentiment {c('s_text')}; "
           f"we cite them by title because their abstracts were not available to us. Liao et al. {c('liao')} fuse news into one model for several stocks with attentive pooling and report a 7.11 % lower mean absolute error (0.1913 to 0.1777) on six Taiwanese stocks, a price-regression result.")
    P.para(f"**Multiple instance learning.** MIL, introduced for drug-activity prediction {c('dietterich')}, labels a bag rather than its instances; attention pooling makes the instance weights learnable and inspectable {c('ilse')}. "
           f"Zhang et al. {c('zhang')} apply multi-source MIL (events, sentiment and index data) to the Shanghai index and report F1 gains of 6.9 % and 9.2 % over a non-MIL model in two years; "
           f"Deng and Yiu {c('deng')} treat each trading day as a bag of news. The FNSPID corpus {c('fnspid')} supplies timestamped headlines per ticker for this kind of study.")
    P.para("**Evaluation practice.** One-step forecasts of a price level are easy to score well on R2, because consecutive prices are strongly autocorrelated and a model that mostly repeats the last input already tracks the series; "
           "a no-change (persistence) forecast is therefore the minimal reference, and a chronological split the minimal protocol. The base paper uses chronological splits and several error metrics, but its text does not mention a no-change baseline, "
           "and its sentiment experiments cover a window too short to include a long training period. We add the baseline, longer histories and direction metrics.")
    P.table("Selected related work",
            ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [[f"Base paper {c('base')}", "LSTM + attention + FinBERT + FedAvg", "10 stocks; 30-day news", f"avg R2 {bp['r2_avg']}; LSTM trend {bp['lstm_trend_acc']} %", "30 days of news; FL simulated"],
             [f"Zhang et al. {c('zhang')}", "Multi-source MIL", "Shanghai index, 2015-16", "F1 +6.9 % / +9.2 % vs non-MIL", "One index"],
             [f"Deng, Yiu {c('deng')}", "Day = bag of news", "S&P 500 news", "better trend accuracy (abstract)", "News only"],
             [f"Liao et al. {c('liao')}", "Attentive news pooling", "6 TWSE stocks", "MAE -7.11 %", "Price regression"],
             [f"Fischer, Krauss {c('fischer')}", "LSTM, financial prediction", "see source", "not quoted", "Prices only"],
             [f"Survey items {c('s_llm', 's_multimodal', 's_text')}", "News / sentiment fusion", "not verified", "not quoted", "Abstracts unread"],
             ["This work", "Base pipeline + MIL study", "10 stocks, 2 y; real news 2022-23", "Section IV", "No MIL in product"]],
            [0.62, 0.7, 0.62, 0.7, 0.55], size=6.2)
    P.para("**Research gap.** The base paper averages a day's headlines into one number and tests sentiment over only 30 days; the MIL literature treats the day as a bag but reports price-level or index results with different protocols. "
           "Missing is a side-by-side test, on one data source and one split, of a price-only model, a flat-sentiment model and bag-level MIL models, scored with direction metrics and a no-change baseline.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Data and Preprocessing")
    P.para(f"Prices are daily OHLCV from Yahoo Finance {c('yahoo')} for TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM and ORCL (Airbnb of the base paper is replaced by META): 501 rows per ticker from 2024-09-09 to 2026-09-08. "
           "A 20-day window of Open, High, Low, Close and Volume, Min-Max scaled to [0,1] with scalers fitted on the first 80 % of rows, predicts the next close; the split is chronological 80/20, giving 97 test windows per ticker. "
           "Values outside the training range are clipped to [0,1]. Each headline is scored by FinBERT-tone as +p for a positive, -p for a negative and 0 for a neutral label (p is the class probability); the daily value is the mean score of the day's headlines in [-1, 1], forward-filled and set to zero before the first headline. "
           "No NewsAPI key was configured, so the product used its built-in synthetic headlines: eleven templates, 166-191 headlines per ticker, generated for the last 90 trading days only.")
    P.sub("B", "Models")
    P.para(f"Baselines are ARIMA(5,1,0), SARIMAX, Prophet {c('prophet')}, a 200-tree random forest and an RBF support vector regressor on the last 20 closes. The deep tiers are (i) an LSTM {c('lstm')} with 64 units, batch normalisation, dropout 0.2 and a linear output, "
           "(ii) the same LSTM returning sequences followed by 4-head self-attention")
    P.eq("Attn(Q, K, V) = softmax(Q Kᵀ / √d_k) V")
    P.para("with a residual connection, layer normalisation, average pooling and two dense layers, (iii) tier (ii) with the sentiment score as a sixth input channel, and (iv) a federated tier: each ticker is a client, "
           "ten local models start from one global model, train three epochs, and are averaged for two rounds, "
           f"{c('fedavg')}")
    P.eq("w = Σ_k (n_k / n) w_k")
    P.para("Training uses Adam, batch 32, at most 50 epochs, the last 15 % of the training windows as validation and early stopping with patience 7 on the validation loss. Multi-step forecasts feed each prediction back as the next day's Open, High, Low and Close, and the 95 % band is 1.96 σ √h with σ the residual standard deviation and h the horizon in days.")
    P.sub("C", "Evaluation Protocol")
    P.para("The application scores the deep tiers with MAE, MSE, R2 and a directional accuracy on the clipped, scaled targets. We add (a) scoring against the real closes, (b) a persistence baseline (yesterday's close), "
           f"(c) five seeds, (d) a placebo tier whose sentiment values are shuffled in time, and (e) a forward test: the stored 5- and 30-day forecasts, made from the 2026-09-08 close, are compared with the 30 closes that followed (2026-09-09 to 2026-10-20).")
    P.sub("D", "Multiple-Instance Study")
    P.para(f"For ticker T and trading day t the bag B = {{x_1, …, x_n}} holds the FNSPID headlines {c('fnspid')} of T that were public before day t's close; each instance is a FinBERT-tone vector h_i (three class probabilities and 64 principal components of the [CLS] state). "
           f"The label is y = 1 if the close of day t+1 exceeds that of day t; no headline is labelled. Gated attention pooling {c('ilse')} gives")
    P.eq("z = Σ_i a_i h_i,   a_i = softmax_i( wᵀ [ tanh(V h_i) ⊙ σ(U h_i) ] )")
    P.para("and the classifier outputs p = σ(f([LSTM(price window), z])); mean and max pooling replace the weights, and an empty bag uses a learned vector. "
           f"Seven tickers have at least 1,000 headlines (AAPL, AMZN, FDX, MSFT, NVDA, ORCL, TSLA; {MIL['instances']['n_headline_rows_used']:,} headline rows, {share2223:.0f} % of them dated 2022-2023), "
           f"so training uses 2022 and 2023 and three expanding-window folds are tested on the quarters Q2, Q3 and Q4 of 2023 ({n_test:,} pooled test days). "
           "The two months before each test quarter validate early stopping, and five seeds are run. The placebo gives each day the bag of another random day of the same ticker. "
           "The instance encoder is a 67-to-32 linear layer with ReLU and dropout 0.3, the attention uses 16 hidden units, the price branch is a 32-unit LSTM over a three-channel window (log return, high-low range, log volume ratio), "
           "and training uses AdamW (learning rate 0.002, weight decay 0.001), batch 128, at most 60 epochs and patience 7; bags are capped at 24 instances.")
    P.sub("E", "Architecture and Implementation")
    P.figure(figs["arch"], "QuantPulse architecture: browser, FastAPI service, pipeline modules and files. There is no database.", 3.3)
    P.figure(figs["flow"], "Main flow: (A) the product pipeline and (B) the offline multiple-instance study.", 3.3)
    P.para("The service exposes seven JSON endpoints (health, tickers, metrics, forecast, sentiment, history and the built site) with ticker validation and error codes 400, 404, 422 and 503; "
           "it reads stored JSON, while the history endpoint downloads prices from Yahoo Finance on every call and the sentiment endpoint loads FinBERT-tone on first use.")

    P.sub("F", "Testing and Reproducibility")
    P.para("The 56 pytest cases cover the data loader (invalid symbols, synthetic fallback), windowing and scalers (including clipping), the metric functions, FedAvg, the recursive forecast, the baselines, the sentiment scorer and every endpoint with its error codes, "
           "with network access stubbed; 26 smoke checks run against the live API and website. All experiments are scripts that write JSON files (run_experiments.py, mil_study.py, measure_api.py), prices are pinned in a snapshot "
           "because the application overwrites its own CSV files on every live pull, and the synthetic-headline generator is seeded through PYTHONHASHSEED so that runs repeat.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions")
    P.para(f"Deep-model numbers are means over ten tickers and five seeds (± standard deviation over seeds) on 97 chronological test windows per ticker; baselines are deterministic. "
           f"The MIL study uses {n_test:,} pooled test days; with that sample a gap below about three accuracy points lies within the bootstrap interval. The re-run reproduces the shipped artefacts' ranking of the tiers.")
    rows = [["Persistence (yesterday)", "-", f"{pers:.2f}", "-", "-"],
            ["Random forest", f"{SUM['models']['random_forest']['mae']['mean']:.2f}", f"{base('random_forest', 'mae'):.2f}", f"{base('random_forest', 'r2'):.2f}", f"{base('random_forest', 'directional_accuracy') * 100:.1f}"],
            ["ARIMA(5,1,0)", f"{SUM['models']['arima']['mae']['mean']:.2f}", f"{base('arima', 'mae'):.2f}", f"{base('arima', 'r2'):.2f}", f"{base('arima', 'directional_accuracy') * 100:.1f}"],
            ["SVR", f"{SUM['models']['svr']['mae']['mean']:.2f}", f"{base('svr', 'mae'):.2f}", f"{base('svr', 'r2'):.2f}", f"{base('svr', 'directional_accuracy') * 100:.1f}"]]
    for t, nm in (("lstm", "LSTM"), ("lstm_attention", "LSTM + attention"), ("lstm_attention_sentiment", "+ sentiment (synthetic)"), ("attention_shuffled_sentiment", "Placebo (shuffled sentiment)"), ("hybrid_federated", "Hybrid (FedAvg)")):
        a, b, r2, d = tier(t, "mae"), tier(t, "mae_true"), tier(t, "r2_true"), tier(t, "da_true")
        rows.append([nm, f"{a[0]:.1f}", f"{b[0]:.1f} ± {b[1]:.1f}", f"{r2[0]:.1f}", f"{d[0] * 100:.1f}"])
    P.table("Mean over ten tickers: error and direction on real closes", ["Model", "MAE as scored by app ($)", "MAE real closes ($)", "R2 real", "Direction real (%)"], rows,
            [1.15, 0.6, 0.7, 0.4, 0.55], size=6.4, align=["l", "c", "c", "c", "c"])
    P.sub("B", "Deep Tiers against Persistence")
    P.para(f"Table II shows that yesterday's close has a mean absolute error of ${pers:.2f}, while the best deep tier (LSTM + attention) has ${best_true[0]:.1f} ± {best_true[1]:.1f} on the real closes; "
           f"the random forest, the only baseline that uses actual lagged closes one step ahead, reaches ${base('random_forest', 'mae'):.1f}. R2 is negative for every deep tier (best {tier('lstm_attention', 'r2_true')[0]:.1f}). "
           f"Adding attention helps (LSTM ${tier('lstm', 'mae_true')[0]:.1f}), but adding sentiment ({tier('lstm_attention_sentiment', 'mae_true')[0]:.1f}) and federated averaging ({tier('hybrid_federated', 'mae_true')[0]:.1f}) makes it worse and much less stable across seeds, "
           "the opposite of the base paper's ablation. ARIMA, SARIMAX and Prophet forecast the whole test span without refitting, so their errors are not one-step errors.")
    ratios = {k: float(np.mean([x["mae_true"] for x in RR["tickers"][k]["models"]["lstm_attention"]])) / RR["tickers"][k]["persistence"]["mae"] for k in T}
    kb, kw = min(ratios, key=ratios.get), max(ratios, key=ratios.get)
    P.para(f"The gap is not confined to one stock. For LSTM + attention the ratio of its real-close error to the persistence error ranges from {ratios[kb]:.1f} ({kb}) to {ratios[kw]:.1f} ({kw}), so every ticker is worse than no change. "
           f"Seed variation is large for the tiers that use sentiment or federation (standard deviation {tier('lstm_attention_sentiment', 'mae_true')[1]:.1f} and {tier('hybrid_federated', 'mae_true')[1]:.1f} dollars against {tier('lstm_attention', 'mae_true')[1]:.1f} for attention alone), "
           "so a single-seed ablation, as in the shipped artefacts, can rank the tiers differently from run to run.")
    P.figure(figs["results"], "(a) Mean absolute error of each model on real closes; (b) next-day accuracy of the multiple-instance study against the always-up rate.", 3.3)
    P.sub("C", "Defects Behind the Reported Numbers")
    P.para(f"Two defects explain why the application's own numbers look better. First, test targets are clipped to the training range; in {clip_n} of ten tickers more than half of the test closes lie above the training maximum (up to {clip_max:.0f} %), so the target is flat and the directional accuracy "
           f"reads {da_ship:.0f} % for LSTM + attention, against {da_true:.0f} % on the real closes. Second, the sentiment channel is zero for every training row (synthetic headlines exist only for the last 90 days) and non-zero only in the test part: "
           "the sentiment tier trains without sentiment and is tested on random values. The shuffled-sentiment placebo, which is non-zero in training, scores like the no-sentiment tier, "
           "so the ablation cannot show a sentiment effect in either direction.")
    P.sub("D", "Forward Test of the Stored Forecasts")
    P.para(f"From the 2026-09-08 close the stored 5-day forecasts fall for {down9} of ten tickers (mean {shipped_mean5:+.1f} %), while the realised 5-day change averaged {fs['mean_actual_change_pct']:+.1f} %; "
           f"the trend flag was right for {fs['trend_hits']} of ten tickers, and the 5-day MAE was ${fs['mean_mae']:.1f} against ${fs['mean_persistence_mae']:.1f} for no change. "
           f"At 30 days the forecasts averaged {fl['mean_pred_change_pct']:+.1f} % against {fl['mean_actual_change_pct']:+.1f} % realised, the trend was right for {fl['trend_hits']} of ten and the MAE was ${fl['mean_mae']:.1f} against ${fl['mean_persistence_mae']:.1f}. "
           "Table III lists every ticker. The recursive forecast rolls the close forward and overwrites Open, High and Low with it, which turns small level errors into steady drift.")
    P.table("Stored forecasts from 2026-09-08 against the realised closes", ["Ticker", "5-day forecast (%)", "5-day actual (%)", "Trend right", "30-day forecast (%)", "30-day actual (%)"],
            [[k, f"{FWD['tickers'][k]['short']['pred_end_pct_change']:+.1f}", f"{FWD['tickers'][k]['short']['actual_end_pct_change']:+.1f}", "yes" if FWD['tickers'][k]['short']['trend_hit'] else "no",
              f"{FWD['tickers'][k]['long']['pred_end_pct_change']:+.1f}", f"{FWD['tickers'][k]['long']['actual_end_pct_change']:+.1f}"] for k in T],
            [0.5, 0.62, 0.62, 0.45, 0.62, 0.62], size=6.4, align=["l", "c", "c", "c", "c", "c"])
    P.table("Multiple-instance study on real headlines (mean of five seeds)", ["Model", "Acc.", "Prec.", "Rec.", "F1", "AUC"],
            [[nm] + [f"{ms(k, q):.3f}" for q in ("accuracy", "precision", "recall", "f1", "auc")] for k, nm in
             (("majority_class", "Majority class"), ("logreg_price_C1.0", "Logistic regression, price"), ("lstm_price", "LSTM, price (same window)"), ("lstm_price_full_history", "LSTM, price (since 2016)"),
              ("lstm_flat_sentiment", "LSTM + mean sentiment"), ("lstm_mil_mean", "LSTM + MIL mean"), ("lstm_mil_max", "LSTM + MIL max"), ("lstm_mil_attention", "LSTM + MIL attention"),
              ("mil_attention_news_only", "MIL attention, news only"), ("placebo_mil_attention_shuffled_bags", "Placebo (other days' bags)"))],
            [1.35, 0.4, 0.4, 0.4, 0.4, 0.4], size=6.4, align=["l", "c", "c", "c", "c", "c"])
    P.sub("E", "Multiple-Instance Results")
    P.para(f"Table IV shows no gain from news. Always predicting up is right on {up:.1f} % of the test days; no MIL variant exceeds it (gated attention {ms('lstm_mil_attention', 'accuracy') * 100:.1f} %, mean pooling {ms('lstm_mil_mean', 'accuracy') * 100:.1f} %, max pooling {ms('lstm_mil_max', 'accuracy') * 100:.1f} %). "
           f"Against the price-only LSTM trained on the same window ({ms('lstm_price', 'accuracy') * 100:.1f} %) the differences are {pr['lstm_mil_attention']['acc_diff'] * 100:+.1f} (attention), {pr['lstm_mil_mean']['acc_diff'] * 100:+.1f} (mean) and {pr['lstm_mil_max']['acc_diff'] * 100:+.1f} (max) points, "
           f"with bootstrap 95 % intervals such as [{pr['lstm_mil_attention']['ci95'][0] * 100:+.1f}, {pr['lstm_mil_attention']['ci95'][1] * 100:+.1f}] that include zero, and the shuffled-bag placebo scores {ms('placebo_mil_attention_shuffled_bags', 'accuracy') * 100:.1f} %, the same as the real bags. "
           f"The price-only LSTM trained on all history since 2016 reaches {ms('lstm_price_full_history', 'accuracy') * 100:.1f} % only because it predicts up on {m['lstm_price_full_history']['summary']['pred_up_share']['mean'] * 100:.0f} % of days (recall {ms('lstm_price_full_history', 'recall'):.2f}, AUC {ms('lstm_price_full_history', 'auc'):.2f}). "
           f"ROC-AUC stays between {min(ms(k, 'auc') for k in m if k not in ('majority_class',)):.2f} and {max(ms(k, 'auc') for k in m if k not in ('majority_class',)):.2f}, i.e. near chance. "
           "The conclusion is limited to this setting: seven tickers, one year of training, mostly day-level time stamps and headlines that often concern several companies.")
    if ex:
        P.para(f"The attention weights are inspectable: on {ex['ticker']} {ex['date']} the bag held {ex['n_headlines']} headlines, the top-weighted one received {ex['top'][0]['weight']:.2f} against a uniform {ex['uniform_weight']:.2f}, "
               "Table V lists its top-weighted headlines; the weights did not lead to better predictions.")
    P.para("Threats to validity: the test period (January to September 2026) is one market regime, the ten stocks are large technology-heavy names, ninety-seven windows per ticker give wide intervals on any direction metric, "
           "and the deep models were not tuned beyond the base paper's settings; a tuned model could do better, but tuning would not remove the clipping and sentiment defects.")
    pt = MIL["per_ticker_test_accuracy"]
    tl = sorted(T for T in pt["lstm_mil_attention"])
    rngm = (min(pt["lstm_mil_attention"].values()) * 100, max(pt["lstm_mil_attention"].values()) * 100)
    rngp = (min(pt["lstm_price"].values()) * 100, max(pt["lstm_price"].values()) * 100)
    P.para(f"Per ticker (about {int(np.mean(list(MIL['per_ticker_test_n'].values())))} test days each) the accuracy of gated-attention MIL ranges from {rngm[0]:.0f} % to {rngm[1]:.0f} % and that of the price-only LSTM from {rngp[0]:.0f} % to {rngp[1]:.0f} %; "
           "with such samples a single ticker's figure is mostly noise.")
    if ex:
        P.table("Gated-attention weights for one test bag", ["Headline (top 3 of the bag)", "Weight", "P(pos)", "P(neg)"],
                [[t["headline"][:78] + ("…" if len(t["headline"]) > 78 else ""), f"{t['weight']:.2f}", f"{t['p_pos']:.2f}", f"{t['p_neg']:.2f}"] for t in ex["top"]],
                [1.9, 0.4, 0.4, 0.4], size=6.2, align=["l", "c", "c", "c"])
    P.sub("F", "Comparison with the Base Paper")
    P.para(f"The base paper reports an average R2 of {bp['r2_avg']} and a baseline-LSTM trend accuracy of {bp['lstm_trend_acc']} %; this work measures R2 {tier('hybrid_federated', 'r2_true')[0]:.1f} for the hybrid on the real closes and a direction accuracy of {da_true:.0f} % for the best tier. "
           "The comparison is indicative only: the paper's hybrid used one month of data with scaled units and a 70/15/15 split, whereas this work uses two years, dollar errors and 97 test windows per ticker. "
           "We could not reproduce the paper's R2 and do not claim to refute it; its own limitations section names the 30-day news window and the simulated federation.")
    P.sub("G", "Output Screens, Failure Cases and Limits")
    P.figure(figs["forecast"], "QuantPulse forecast screen for TSLA: actual closes, dashed 5-day forecast and band, drawn on real data.", 3.4)
    P.figure(figs["models"], "QuantPulse model-comparison screen for NVDA: ablation of the deep tiers and every model by MAE.", 3.4)
    P.para(f"Measured on 127.0.0.1, stored-result endpoints answer in about {API['forecast_short']['median_ms']:.0f} ms (median), the history endpoint in {API['history_120d']['median_ms']:.0f} ms because it re-downloads prices, and the sentiment endpoint in {API['sentiment']['median_ms'] / 1000:.1f} s. "
           f"Failure cases are: the stored forecast's {fs['mean_pred_change_pct']:+.1f} % drift, the wrong trend flag for {10 - fs['trend_hits']} of ten tickers, an average direction near chance, the unstable sentiment and federated tiers, and the synthetic news. "
           "The Forecast screen shows the misses next to the forecast. Not measured: real NewsAPI headlines inside the product, any social-media source, trading costs and a true multi-party federation.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"QuantPulse meets its engineering objective: a tested product (56 unit and API tests, 26 smoke checks) that reproduces the base paper's pipeline for ten stocks. It does not meet the forecasting objective. "
           f"Scored on real closes, no deep tier beats yesterday's close, the forward test missed the realised moves, and the MIL study found no evidence that a day's headlines, pooled as a bag, help predict next-day direction beyond the {up:.1f} % always-up rate. "
           "The product has no MIL, no social-media source and no precision, recall or F1; those objectives were addressed only by the offline study.")
    P.para("The practical reading is that QuantPulse is a sound research and teaching tool for building and auditing such a pipeline, not a source of trading signals. "
           "Limits: ten stocks and 97 test windows each, synthetic sentiment, a short and partly day-level news history, a simulated federation and CPU-only training. "
           "Future work: score on real closes and add a persistence baseline in the product; fill the sentiment channel with real headlines over the full training period; move MIL and a classification head into the application; "
           "use walk-forward validation over several years; and add a social-media source and a real multi-party federated deployment.")

    P.references()
    P.save(path)
    return path
