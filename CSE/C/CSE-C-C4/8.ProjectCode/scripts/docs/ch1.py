"""Chapter 1: Introduction (QuantPulse, CSE-C-C4)."""

import numpy as np

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (kept for the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def K():
    """Derived headline numbers shared by the front-matter and chapter modules (all read from the measured JSON files)."""
    T = F.TICKERS
    S = len(F.RR["seeds"])

    def seedwise(tier, key):
        per = [np.mean([F.RR["tickers"][t]["models"][tier][s][key] for t in T]) for s in range(S)]
        return float(np.mean(per)), float(np.std(per))

    m = F.MIL["models"]
    k = {
        "persist": float(np.mean([F.RR["tickers"][t]["persistence"]["mae"] for t in T])),
        "attn_true_mae": seedwise("lstm_attention", "mae_true"), "attn_true_da": seedwise("lstm_attention", "da_true")[0],
        "attn_ship_da": F.SUM["models"]["lstm_attention"]["directional_accuracy"]["mean"],
        "attn_ship_mae": F.SUM["models"]["lstm_attention"]["mae"]["mean"], "rf_ship_mae": F.SUM["models"]["random_forest"]["mae"]["mean"],
        "hyb_ship_mae": F.SUM["models"]["hybrid_federated"]["mae"]["mean"], "hyb_ship_r2": F.SUM["models"]["hybrid_federated"]["r2"]["mean"],
        "hyb_true_mae": seedwise("hybrid_federated", "mae_true"), "sent_true_mae": seedwise("lstm_attention_sentiment", "mae_true"),
        "lstm_true_mae": seedwise("lstm", "mae_true"),
        "f5_pred": F.FWD["short"]["mean_pred_change_pct"], "f5_act": F.FWD["short"]["mean_actual_change_pct"], "f5_hits": F.FWD["short"]["trend_hits"],
        "f5_mae": F.FWD["short"]["mean_mae"], "f5_pers": F.FWD["short"]["mean_persistence_mae"],
        "f30_pred": F.FWD["long"]["mean_pred_change_pct"], "f30_act": F.FWD["long"]["mean_actual_change_pct"], "f30_hits": F.FWD["long"]["trend_hits"],
        "f30_mae": F.FWD["long"]["mean_mae"], "f30_pers": F.FWD["long"]["mean_persistence_mae"],
        "n_down": sum(1 for v in F.SUM["trend"].values() if v == "down"),
        "ship_f5_mean": float(np.mean(list(F.SUM["forecast_5d_change_pct"].values()))),
        "mil_n": F.MIL["n_test_pooled"], "always_up": F.MIL["always_up_accuracy_test"],
        "mil_tickers": len(F.MIL["tickers"]),
    }
    for key in ("lstm_price", "lstm_price_full_history", "lstm_flat_sentiment", "lstm_mil_mean", "lstm_mil_max", "lstm_mil_attention", "mil_attention_news_only", "placebo_mil_attention_shuffled_bags"):
        k["acc_" + key] = m[key]["summary"]["accuracy"]["mean"]
        k["f1_" + key] = m[key]["summary"]["f1"]["mean"]
    accs = [m[x]["summary"]["accuracy"]["mean"] for x in ("lstm_price", "lstm_flat_sentiment", "lstm_mil_mean", "lstm_mil_max", "lstm_mil_attention", "placebo_mil_attention_shuffled_bags")]
    k["acc_lo"], k["acc_hi"] = min(accs), max(accs)
    return k


def blocks():
    k = K()
    base = R["base"]
    out = [
        H1("1. INTRODUCTION"),
        H2("1.1 Domain Overview"),
        P("Stock-market prediction is the task of estimating how the price of a listed share will move. Prices are set continuously by buyers and sellers who react to company results, "
          "macro-economic data, market mood and news, so the series is noisy, non-stationary and, according to the efficient-market hypothesis [" + str(R["emh"]) + "], hard to forecast from "
          "its own past alone. Even so, short-horizon forecasts are wanted by retail investors, portfolio managers and risk teams, and the field has moved from statistical models such as ARIMA "
          "[" + str(R["box"]) + "] and additive decomposition [" + str(R["prophet"]) + "], through machine-learning regressors such as random forests [" + str(R["rf"]) + "] and support vector "
          "regression [" + str(R["svr"]) + "], to recurrent networks [" + str(R["lstm"]) + "], [" + str(R["fischer"]) + "] and attention-based sequence models [" + str(R["transformer"]) + "]. "
          "Systematic reviews [" + str(R["sezer"]) + "], [" + str(R["lim"]) + "] show that deep learning dominates recent work while also warning that reported gains depend heavily on the evaluation protocol."),
        P("A second thread of research adds text. Media tone has been linked to returns [" + str(R["tetlock"]) + "], social-media mood has been used to predict an index [" + str(R["bollen"]) + "], and "
          "domain-specific language models such as FinBERT [" + str(R["finbert"]) + "], [" + str(R["finbert_tone"]) + "] turn a headline into a positive, neutral or negative score. This project "
          "belongs to the intersection of the two threads: prices are a numeric sequence, headlines are text, and the question is whether combining them gives a better short-term forecast than prices alone."),
        H2("1.2 Background and Motivation"),
        P("The batch title, *Stock Market Prediction Using Multi-Source Multiple Instance Learning*, is taken from the work of Zhang et al. [" + str(R["zhang"]) + "], who combined price data, "
          "news events and social-media sentiment for a Chinese index and treated the day's news as a set of instances whose individual labels are unknown. Multiple Instance Learning (MIL) "
          "[" + str(R["dietterich"]) + "] is the natural formulation for news: on a given day a company may appear in dozens of articles, only a few of which matter, and nobody labels each article as "
          "bullish or bearish. The learner receives a *bag* of articles with a single outcome label (the price moved up or down) and must work out which instances carried the signal. "
          "Attention-based pooling [" + str(R["ilse"]) + "] lets a network learn that weighting, and it also shows which headlines the model relied on."),
        P("The base paper named for this batch, " + lit.BASE_PAPER_VENUE + " [" + str(base) + "], is a more recent and more practical design: an LSTM over twenty-day price windows, a multi-head attention layer, "
          "a FinBERT-tone sentiment channel, and a simulated federated-averaging stage over ten stocks, reported to reach an average R2 of 0.91. QuantPulse, the product built for this batch, "
          "implements that pipeline as a working website, and the project then asks what the title asks: does a multi-source, multiple-instance treatment of daily news add anything? "
          "The motivation is therefore twofold: to turn a research pipeline into something a trader or analyst can open in a browser, and to test its claims on data the base paper did not use."),
        H2("1.3 Problem Statement"),
        P("Price-only models miss the news and sentiment that move markets; labelling each news article individually is impractical and noisy; financial data is volatile and non-stationary, so models "
          "degrade quickly; and a prediction that is not explained is not actionable for an investor. The problem is to build a system that forecasts short-term stock movement from historical prices together "
          "with financial news, that is evaluated honestly against simple baselines, and that presents its forecasts, errors and caveats clearly to a user."),
        H2("1.4 Need for the Project"),
        P("Three needs motivate the work. First, a research result is of little use until it can be run and inspected: the base paper reports its figures but offers no application, so QuantPulse provides one, with "
          "ten tickers, five classical baselines, four deep-model tiers and 5- and 30-day forecasts with confidence bands. Second, the base paper's sentiment experiments rest on thirty days of headlines, because the news "
          "service it uses returns about a month of history [" + str(base) + "]; the need is to see what happens when the sentiment channel is exercised properly. Third, forecasts are easy to publish and hard to check: "
          "a forecasting tool should be tested against the prices that actually followed and against a no-change forecast, and this project does both."),
        H2("1.5 Objectives"),
        P("The six objectives set in the batch document are:"),
        N(*lit.OBJECTIVES),
        P("Section 1.9 and Chapter 8 state, objective by objective, what was achieved. In short, the product covers prices, a daily sentiment channel, a hybrid LSTM-attention model and a four-tier ablation, "
          "while the multiple-instance formulation, the social-media source and the precision, recall and F1 evaluation are *not* part of the product and were examined in a separate offline study."),
        H2("1.6 Scope of the Work"),
        P("**In scope:** daily Yahoo Finance prices for ten technology-heavy tickers (TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM, ORCL); five classical baselines (ARIMA, SARIMAX, Prophet, random forest, SVR); "
          "an LSTM, an LSTM with four-head attention, the same with a daily FinBERT-tone sentiment channel, and a hybrid trained by simulated federated averaging; 5- and 30-day forecasts with a confidence band; "
          "a FastAPI service with seven JSON endpoints; a six-screen React website; unit, API and smoke tests; and an offline multiple-instance study on real headlines."),
        P("**Out of scope:** trading, order execution or portfolio advice (QuantPulse is a research and education tool, not financial advice); intraday data; social-media text, for which no data source was available; "
          "authentication; a database; real federated deployment across institutions; and any claim of profitability."),
        H2("1.7 Contributions"),
        N("A working end-to-end implementation of the base paper's hybrid pipeline for ten tickers, with a FastAPI service and a six-screen React website that shows forecasts, bands, model comparison and sentiment.",
          "A pinned-data, five-seed re-run of the shipped pipeline with a persistence baseline, showing that no deep tier beats \"tomorrow equals today\" on real closes (persistence MAE "
          f"${k['persist']:.2f} against ${k['attn_true_mae'][0]:.2f} for the best deep tier).",
          "A forward test of the shipped forecasts against the closes that followed: the stored 5-day forecasts averaged " + f"{k['f5_pred']:+.1f} % against a realised {k['f5_act']:+.1f} %, and the trend flag was right for {k['f5_hits']} of 10 tickers.",
          "Identification of three evaluation defects in the shipped pipeline (clipped test targets, an empty training sentiment channel, differently scaled federated clients), documented rather than hidden.",
          "An offline multiple-instance-learning study on real FNSPID headlines, with mean, max and gated-attention pooling, a flat-sentiment baseline, a shuffled-bag placebo and precision, recall and F1 reported over five seeds."),
        P("**The findings in brief.** On the ten tickers the stored deep-model scores look respectable when read from the application: the best deep tier shows a directional accuracy of "
          f"{k['attn_ship_da'] * 100:.0f} %. In a five-seed re-run of the same pipeline scored against the real closes, it falls to {k['attn_true_da'] * 100:.0f} %, because the application clips the test targets to the training price range. "
          f"The mean absolute error of the best deep tier is ${k['attn_true_mae'][0]:.2f} per share, against ${k['persist']:.2f} for repeating yesterday's close. In the forward test the 5-day forecasts "
          f"missed by ${k['f5_mae']:.2f} on average, against ${k['f5_pers']:.2f} for a no-change forecast, and {k['n_down']} of 10 tickers were flagged as falling although the realised mean change was {k['f5_act']:+.1f} %. "
          "These are results of the shipped pipeline as the base paper describes it, measured on two years of data rather than one month, and they do not reproduce the paper's R2 of 0.91."),
        P(f"For the multiple-instance question, {k['mil_n']:,} test days across {k['mil_tickers']} tickers were used. Accuracy ranged from {k['acc_lo'] * 100:.1f} % to {k['acc_hi'] * 100:.1f} % for the price-only LSTM, the flat-sentiment model, "
          f"the three pooling variants and the shuffled-bag placebo, while predicting \"up\" every day scores {k['always_up'] * 100:.1f} %. No evidence was found that a bag of real headlines improves next-day direction at this sample size. "
          "The result is reported as it came out; it is a statement about this data and this sample, not about whether news matters."),
        H2("1.8 Limitations and Assumptions"),
        P("The limitations that matter most are listed here and developed in Chapters 7 to 9. Multiple Instance Learning is not implemented in the product. The sentiment channel of the product is built from "
          "template headlines generated by a fallback, because no NewsAPI key was configured, and these headlines exist only for the last 90 trading days of each series. Forecast quality was measured and is poor. "
          "The MIL study uses seven tickers, two years of dense news and 1,309 test samples, so differences smaller than about three accuracy points cannot be told from noise. Federated learning is simulated in "
          "one process, as in the base paper."),
        P("The assumptions are that Yahoo Finance daily bars are accurate and complete, that trading days are the unit of prediction, that a chronological 80/20 split reflects deployment, that headlines with a "
          "day-level time stamp were available before the next day's close, and that the machine used for all measurements (Intel Core i5-12500, 15.7 GB of memory, no graphics card, Windows 11) is representative of an ordinary workstation."),
        H2("1.9 Status of the Objectives"),
        TAB("Status of the six batch objectives", ["No.", "Objective", "Status in this project"],
            [["1", "Collect prices, news and social-media text", "Partly: prices yes; news only as NewsAPI headlines when a key is set, otherwise synthetic template headlines; no social-media source"],
             ["2", "Align into daily instances per trading day", "Partly: daily alignment yes, but headlines are averaged into one number per day in the product; bags exist only in the offline study"],
             ["3", "Represent each day as a bag (MIL)", "Not in the product. Done offline: mean, max and gated-attention MIL on real headlines (Chapter 8)"],
             ["4", "Hybrid sequence model with attention", "Yes: LSTM + four-head attention + sentiment channel + simulated FedAvg (attention is over the price window, not over news)"],
             ["5", "Directional prediction with accuracy, precision, recall, F1", "Product: price level and an up/down flag only. Precision, recall and F1 reported in the offline study"],
             ["6", "Multi-source versus price-only baseline", "Product ablation exists but its sentiment is synthetic; the valid comparison is the offline study, which found no gain"]],
            widths=[0.4, 2.2, 3.9], align=["c", "l", "l"], size=10),
        H2("1.10 Organisation of the Report"),
        P("Chapter 2 surveys the literature and analyses the base paper. Chapter 3 assesses feasibility and Chapter 4 sets out the requirements and the existing and proposed systems. Chapter 5 presents the design, "
          "with architecture, data-flow, UML, entity and interface designs. Chapter 6 describes the methodology and the software implementation, including the mathematical formulation. Chapter 7 reports system testing. "
          "Chapter 8 gives the results and output screens, including the re-run, the forward test and the multiple-instance study, and compares them with the base paper. Chapter 9 concludes and Chapter 10 outlines future scope. "
          "The report ends with the references and three appendices: important code, installation and user guide, and additional screens."),
    ]
    return out
