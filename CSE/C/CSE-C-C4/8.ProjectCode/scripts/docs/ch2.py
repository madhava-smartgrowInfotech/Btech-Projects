"""Chapter 2: Literature survey (QuantPulse, CSE-C-C4)."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    bp = F.BASE_PAPER_RESULTS
    base = R["base"]

    def c(*keys):
        return ", ".join(f"[{R[k]}]" for k in keys)

    out = [
        H1("2. LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four purposes: to understand the base paper in depth, to place it among earlier work on price forecasting, text-based sentiment and multiple-instance learning, to identify the datasets "
          "and algorithms worth reusing, and to find the gap this project addresses. The base paper, the two companion papers archived with this batch (Zhang et al. [" + str(R["zhang"]) + "] and Liao et al. [" + str(R["liao"]) + "]) "
          "were read in full from their PDFs. The arXiv abstract of Deng and Yiu [" + str(R["deng"]) + "] was read. The batch literature survey lists four further papers, [" + str(R["s_hybrid"]) + "] to [" + str(R["s_text"]) + "]; "
          "their bibliographic records were checked, but no abstract or full text could be read, so they appear below by title only and nothing is claimed for their results. Items quoted from the base paper's own "
          "related-work section are marked as reported there."),
        H2("2.2 Base Paper Analysis"),
        P(f"**Title.** {lit.BASE_PAPER_TITLE}. **Authors and venue.** {lit.BASE_PAPER_VENUE} (pp. 3926-3942, doi 10.1109/ACCESS.2025.3649668) [{base}]."),
        H3("2.2.1 Aim and approach"),
        P("The paper benchmarks traditional forecasters (ARIMA, SARIMAX, Prophet, random forest, support vector regression, exponential smoothing) against an LSTM on ten technology and logistics "
          "companies, then enlarges the LSTM in three steps: a multi-head Transformer-style attention layer for long-range dependence, a FinBERT-tone sentiment channel computed from financial headlines, "
          "and a simulated federated-learning stage in which each company is a client and the global model is formed by weighted averaging (FedAvg [" + str(R["fedavg"]) + "]). The argument is that price "
          "history alone cannot show news-driven shocks, that attention helps select informative time steps, and that federated training preserves the privacy of institutional data."),
        H3("2.2.2 Data and preprocessing"),
        P("Daily open, high, low, close, adjusted close and volume were downloaded from Yahoo Finance [" + str(R["yahoo"]) + "] for Tesla, Apple, Airbnb, Amazon, FedEx, IBM, Microsoft, Nvidia, Oracle and Google. "
          "Two windows were used: the full history up to 4 January 2024 for 30-day forecasts, and a six-month window from 6 July 2023 to 4 January 2024 (127 trading days) for short-term work. "
          "Because the news service returned only thirty days of headlines, the hybrid model was trained on a one-month window. Features were scaled to [0, 1] with Min-Max scaling and turned into supervised "
          "samples with a sliding window of previous trading days; baselines used an 80/20 chronological split and the hybrid a 70/15/15 split. Headline scores from FinBERT-tone were aligned to trading days and "
          "concatenated with the price features."),
        H3("2.2.3 Models"),
        P("The baseline LSTM has one LSTM layer of 64 units, batch normalisation and a single linear output neuron that predicts the next close. The enhanced model passes the sequence through an LSTM, a dropout "
          "layer and a multi-head attention layer, pools the result by global average pooling, applies dense layers and concatenates the sentiment features; the federated stage averages the clients' weights "
          "in proportion to their sample counts, wt+1 = sum_i (n_i / n) w_i, once per communication round. The paper reports that LeakyReLU worked better than sigmoid, tanh or ReLU in its trials."),
        H3("2.2.4 Reported results"),
        P(f"The hybrid model is reported to reach an average R2 of {bp['r2_avg']} over the ten companies, with every company above {bp['r2_min_company']}; for Tesla the paper gives MSE {bp['tsla_mse']}, "
          f"MAE {bp['tsla_mae']} and R2 {bp['tsla_r2']} in scaled units. The baseline LSTM's average 5-day trend accuracy is {bp['lstm_trend_acc']} % over 100 runs per company, with large spread ({bp['trend_best']} at the "
          f"top and {bp['trend_worst']} at the bottom). Prophet scored a 5-day R2 of {bp['prophet_5d_r2']}, worse than a mean predictor. In the ablation, adding attention is said to reduce the MSE by nearly 20 % "
          "against the baseline, and each further component (sentiment, federated averaging) to improve it again; the ablation table itself is an image in the paper and its figures are not quoted here."),
        H3("2.2.5 Strengths and limits stated by the paper"),
        P("The strengths are the breadth of the comparison, the modular design and the explicit directional metric. The authors themselves list four limitations: the unpredictability of markets in stress periods, "
          "sentiment restricted to a thirty-day window by the news API, federated learning that is only simulated, and results that vary between companies. The reported metrics are on very short test spans "
          "(the last part of a one-month window for the hybrid model), which is why the paper's R2 values cannot be compared directly with any longer test set."),
        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Statistical and machine-learning forecasters"),
        P(f"ARIMA and SARIMAX {c('box')} model a series by its own lags and seasonality; Prophet {c('prophet')} fits an additive trend and seasonality decomposition; random forests {c('rf')} and support vector regression {c('svr')} "
          "learn non-linear maps from lagged prices. They are cheap and a necessary baseline, but the base paper itself notes that they are ill-suited to abrupt moves. A central caution from the literature on "
          f"market efficiency {c('emh')} is that a one-step forecast that repeats the last price is hard to beat, so any new model should be compared with a no-change forecast, which the text of the base paper does not report and this project does."),
        H3("2.3.2 Deep sequence models"),
        P(f"LSTM networks {c('lstm')} became the standard deep baseline for price sequences; Fischer and Krauss {c('fischer')} applied them to market prediction at scale, and the surveys {c('sezer', 'lim')} "
          f"review dozens of variants. Attention {c('transformer')} lets a model weight time steps, and the base paper stacks it on an LSTM. The surveys also point to the main hazard: results depend strongly on the "
          "split, the window length and the scaling, and it is easy to evaluate a model on a test range the scaler has not seen."),
        H3("2.3.3 Text and sentiment"),
        P(f"Tetlock {c('tetlock')} linked the tone of a newspaper column to market returns and Bollen et al. {c('bollen')} used Twitter mood to predict an index. FinBERT {c('finbert', 'finbert_tone')} is a BERT model "
          "further trained on financial text; the fine-tuned tone version used here outputs the probability that a sentence is positive, neutral or negative. The usual way to feed it to a price model, followed by the base paper, "
          "is to average a day's headline scores into one number per day."),
        H3("2.3.4 Multiple-instance learning and news fusion"),
        P(f"Multiple-instance learning was introduced by Dietterich et al. {c('dietterich')} for problems in which labels attach to bags of instances; Ilse et al. {c('ilse')} added a learned attention weight over "
          f"the instances. Zhang et al. {c('zhang')} applied it to the stock market with three sources: index-level price data, news events and Xueqiu social-media sentiment. On the Shanghai Composite Index for 2015 and 2016, using "
          "38,727 and 39,465 news articles and about 6.2 million posts, their multi-source MIL model is reported to improve F1 by 6.9 % and 9.2 % over their nMIL baseline for the two years. "
          f"Deng and Yiu {c('deng')} treat each trading day as a bag of news instances with a bag-level label for S&P 500 direction. Liao et al. {c('liao')} pool the daily news with self-attention for six Taiwan Stock Exchange "
          "stocks plus a US set and report that pooling lowers the mean absolute error on normalised prices from 0.1913 to 0.1777, a 7.11 % reduction."),
        P(f"The remaining batch survey items {c('s_hybrid', 's_llm', 's_multimodal', 's_text')} concern hybrid models with news and social-media sentiment, a language-model approach to news and price data, multimodal "
          "fusion for the Chinese market and text mining of news with investor sentiment. They indicate the direction of recent work, but they could not be read beyond their titles and are not used for any comparison."),
        H3("2.3.5 Federated learning"),
        P(f"Federated averaging {c('fedavg')} trains a shared model across clients without moving the clients' data, and Yang et al. {c('fedml')} survey the concept. In the base paper each company is one client in a "
          "single-process simulation. That demonstrates the algorithm but not communication cost, client drift or privacy guarantees."),
        TAB("Literature summary", ["Work", "Year", "Approach", "Finding / limitation"], lit.LIT_TABLE, widths=[1.5, 0.5, 2.2, 2.3], align=["l", "c", "l", "l"], size=9),
        H2("2.4 Datasets and Algorithms Used in the Surveyed Work"),
        P(f"Prices come from Yahoo Finance {c('yahoo')} in the base paper and in this project; the FNSPID dataset {c('fnspid')} supplies more than a decade of headlines tagged with ticker symbols and is the real-news "
          f"source for the offline study in this project. Headlines are scored with FinBERT-tone {c('hf_finbert_tone')}. The algorithms reused are the LSTM, multi-head attention, FedAvg, gradient-based optimisers "
          f"{c('adam', 'adamw')}, the five classical baselines, and, for the offline study, mean, max and gated-attention pooling in the multiple-instance setting {c('ilse')}. Implementation uses TensorFlow {c('tf')}, "
          f"PyTorch {c('pytorch')} and scikit-learn {c('sklearn')}."),
        H2("2.5 Strengths and Limitations of Existing Approaches"),
        TAB("Strengths and limitations of the main approaches", ["Approach", "Strength", "Limitation"],
            [["Classical statistical / ML [" + str(R["box"]) + "], [" + str(R["rf"]) + "]", "Cheap, fast, interpretable baselines", "Weak on abrupt moves; level forecasts rarely beat no-change"],
             ["LSTM [" + str(R["lstm"]) + "]", "Captures non-linear sequence dependence", "Sensitive to window, scaling and split; many seeds needed"],
             ["LSTM + attention + sentiment [" + str(base) + "]", "Combines price and news tone; modular", "Daily average of headlines; sentiment window of 30 days; short test span"],
             ["Simulated FedAvg [" + str(R["fedavg"]) + "]", "Shows decentralised training in principle", "One process; no communication cost or privacy analysis"],
             ["Multi-source MIL [" + str(R["zhang"]) + "]", "Bag formulation avoids article-level labels", "Event extraction; one Chinese index; not an LSTM price branch"],
             ["Attentive news pooling [" + str(R["liao"]) + "]", "Weights relevant articles; one model for many stocks", "Price regression on normalised prices; small stock set"]],
            widths=[1.9, 2.2, 2.4], align=["l", "l", "l"], size=9.5),
        H2("2.6 Research Gap"),
        P("Reading the literature against the batch objectives yields the following gaps, which define what this project attempts."),
        N(*lit.GAPS),
        P("QuantPulse covers the first part of that gap by implementing the base paper's pipeline as a product and testing it on two years of data. The multiple-instance formulation is not part of the product; "
          "it is examined in an offline study on real headlines, whose design and outcome are reported in Chapters 6 and 8."),
    ]
    return out
