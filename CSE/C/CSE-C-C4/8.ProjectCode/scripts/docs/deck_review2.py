"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers (prepare, set_title, wipe, agenda, title_slide, thank_you) are defined here so the deck does not depend on
the Review 1 module. All numbers come from facts.py (experiments/**/metrics.json, artifacts/metrics.json); nothing is typed in by hand.
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os
import time

import numpy as np
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "stock market prediction, LSTM, attention, FinBERT sentiment, federated averaging, multiple instance learning"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=3):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 30)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag, wait=900):
    """Copy of a diagram or chart with its white margins removed (written to the temp folder, source untouched). Waits for a figure still being produced."""
    import tempfile

    from PIL import Image, ImageChops

    t0 = time.time()
    while not os.path.exists(path):
        if time.time() - t0 > wait:
            raise FileNotFoundError(path)
        time.sleep(10)
    time.sleep(1)
    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"qp_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    """Real screenshot in a w x h area with a one-line caption under it."""
    K.picture(slide, F.shot(name), x, y, w, h - 0.34, border=True)
    K.text(slide, x, y + h - 0.3, w, 0.3, caption, size=11, color=K.TXT, align="c", italic=True)


def seedwise(tier, key):
    """Ten-ticker mean per seed -> mean over seeds."""
    T = list(F.RR["tickers"])
    n = len(F.RR["seeds"])
    return float(np.mean([np.mean([F.RR["tickers"][t]["models"][tier][s][key] for t in T]) for s in range(n)]))


def lat(name):
    return F.API["endpoints"][name]["median_ms"]


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    T = F.TICKERS
    sm, fw, mil = F.SUM, F.FWD, F.MIL
    pers = float(np.mean([F.RR["tickers"][t]["persistence"]["mae"] for t in T]))
    best_true = seedwise("lstm_attention", "mae_true")
    da_true, da_ship = seedwise("lstm_attention", "da_true"), seedwise("lstm_attention", "directional_accuracy")
    mm = mil["models"]
    acc = {k: v["summary"]["accuracy"]["mean"] for k, v in mm.items()}
    up_rate = mil["always_up_accuracy_test"]
    n_hl = sm["sentiment_meta"]
    hl_lo, hl_hi = min(v["n_headlines"] for v in n_hl.values()), max(v["n_headlines"] for v in n_hl.values())
    n_test_windows = F.SHIP["TSLA"]["deep"]["lstm"]["n_test"]
    n_rows = F.SHIP["TSLA"]["n_rows"]
    wins_rf = sm["best_mae_wins"].get("random_forest", 0)
    pd_ = mil["paired_vs_lstm_price"]["lstm_mil_attention"]
    inst = mil["instances"]

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: LSTM, attention, news sentiment and simulated federated learning for short-term stock forecasting",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how QuantPulse is designed and built, what is implemented, the first measured results and the open items. QuantPulse implements the hybrid forecasting pipeline of the base paper; "
                "multiple instance learning was studied in a separate offline experiment. Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and datasets"), ("03", "Preprocessing and models"), ("04", "Training and decision logic"),
               ("05", "Data flow, entities and UML"), ("06", "Technology stack"), ("07", "Progress and preliminary results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")], [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Share prices move with company results, news and mood, so a price-only history misses information; labelling each news item is impractical, so the batch asks for a bag-of-news (multiple instance) view of each trading day.", K.ORANGE, "!"),
        ("Proposed system", "QuantPulse forecasts 5- and 30-day closes for ten tickers with five classical baselines and four deep-model tiers (LSTM, attention, FinBERT sentiment, simulated FedAvg), shows them on six screens, and an offline study tests the multiple-instance idea on real headlines.", K.BLUE, "i"),
        ("Base paper link [1]", "Nejatbakhsh and Aliasgari (IEEE Access, 2026) combine LSTM, transformer attention, FinBERT-tone sentiment and simulated federated learning on ten tech stocks. QuantPulse follows that design; the product does not contain MIL or social-media text.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.5, t, b_, col, gl, body_size=17)
    notes[3] = ("Recap of Review 1: the base paper is the hybrid price-level forecaster; the batch title and objectives ask for multiple instance learning over daily news bags and for accuracy, precision, recall and F1. "
                "We say plainly that the product follows the base paper and that the MIL formulation was run offline.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.2, 5.7)
    K.text(s, 8.0, 1.45, 4.75, 5.4, [
        ("**Four tiers, no database**", {"space_after": 8}),
        (f"Website: React 19 + Vite on port {F.WEB_PORT}, six screens (landing, dashboard, forecast, model comparison, news sentiment, method).", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}, seven JSON endpoints plus the built site; 400, 404, 422 and 503 errors carry a message.", {"bullet": True}),
        ("Pipeline: data_loader, sentiment, baselines, models_dl, federated, forecast in backend/app; backend/train.py writes the artefacts.", {"bullet": True}),
        ("State: JSON, CSV and Keras files only. No login, no database.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = ("The API serves the stored artefacts/metrics.json and forecasts.json; it does not load the saved Keras models at run time. Only the history and sentiment endpoints do live work "
                "(a Yahoo Finance download and FinBERT scoring).")

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: load, align, model, evaluate")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.4, 5.0)
    for i, (t, b_) in enumerate([("Load and align", "Two years of daily prices per ticker; headlines scored by FinBERT-tone and averaged to one number per trading day."),
                                 ("Model tiers", "Five baselines, LSTM, LSTM + attention, + sentiment, and a FedAvg hybrid over ten clients."),
                                 ("Evaluate and serve", "MAE, MSE, RMSE, R2 and direction on an 80/20 chronological split; stored forecasts shown on the website. Offline: MIL on real headlines.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.3, y, 4.43, 1.65)
        K.text(s, 8.45, y + 0.07, 4.15, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.45, y + 0.42, 4.15, 1.2, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.4, 0.45, "High-level workflow of backend/train.py and the serving layer.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "One command (python -m backend.train) runs the whole ablation per ticker and then the federated stage, then writes the artefacts the API serves."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Data: prices, fallback headlines and real news")
    wipe(s)
    for i, (v, l, c) in enumerate([("10", "tickers: TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM, ORCL", K.ORANGE), (f"{n_rows}", f"daily rows per ticker, 2024-09-09 to 2026-09-08; {n_test_windows} test windows", K.BLUE),
                                   (f"{hl_lo}-{hl_hi}", "synthetic template headlines per ticker (no NewsAPI key)", K.GREEN), (f"{inst['n_headline_rows_used'] / 1000:.1f}k", f"real FNSPID headlines, {len(mil['tickers'])} tickers (offline MIL study)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=11)
    rows = [["", "Shipped product", "Offline MIL study"],
            ["Prices", "Yahoo Finance daily OHLCV through yfinance, last two years, chronological 80/20 split", "Yahoo Finance 2016-2023, seven tickers, same OHLCV features"],
            ["News", "NewsAPI when a key is set; otherwise 11 template headlines, last 90 trading days only", "FNSPID news (Dong et al., KDD 2024), mostly day-level stamps; dense only from 2022"],
            ["Social media", "none - no data source was available", "none"],
            ["Label", "next close (regression); trend flag = day-5 forecast vs last close", "next-day close above today's (bag-level label)"],
            ["Split", "80/20 chronological; scalers fitted on the first 80 % of rows", f"three expanding folds tested on Q2, Q3, Q4 2023: {mil['n_test_pooled']:,} test samples"]]
    K.table(s, 0.6, 2.95, [1.5, 5.4, 5.23], rows, font_size=12.5, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 6.75, 12.13, 0.35, "The application re-downloads prices on every history call, so the experiments use a pinned snapshot of the same window.", size=12, color=K.TXT, italic=True)
    notes[6] = ("Prices are real. The headlines inside the product are synthetic unless a NewsAPI key is set, and NewsAPI only returns about a month, which is also why the base paper's sentiment runs cover 30 days. "
                "The offline study uses real headlines from the public FNSPID dataset.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Daily OHLCV", K.NAVY), ("20-day sliding window", K.PURPLE), ("Min-Max to [0,1]", K.PURPLE),
                                       ("Sentiment channel added", K.GREEN), ("Chronological 80/20 split", K.GREEN), ("Next-day close target", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("20 x 5-6", "window length x features (Open, High, Low, Close, Volume + sentiment)", K.BLUE),
                                   ("0 - 1", "scaled range; test values outside the training range are clipped", K.GREEN)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=12)
    K.text(s, 0.6, 4.35, 12.13, 2.6, [
        ("Scalers are fitted on the first 80 % of rows, then applied to all rows and clipped; where prices rise above the training maximum the target is flat at 1.0.", {"bullet": True}),
        ("Sentiment: headline scores (FinBERT-tone, positive minus negative, -1 to 1) are averaged per trading day, forward-filled, and zero before the first headline.", {"bullet": True}),
        ("Offline MIL study: a headline joins the bag of the first trading day whose close is not earlier than its time stamp; instances are 3 FinBERT probabilities + 64 PCA components.", {"bullet": True}),
        ("Known limit: the product's sentiment channel is exactly zero for every training row (headlines exist for the last 90 days only).", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "make_windows, fit_scalers and apply_scalers in models_dl.py. The clipping and the empty sentiment channel were found while re-running the pipeline and are reported as limitations."

    # ---- 8 model
    s = S[7]
    set_title(s, "Models: LSTM, attention, sentiment and FedAvg")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**LSTM tier**: LSTM(64), batch norm, dropout 0.2, one dense output.", {"bullet": True, "space_after": 8}),
        ("**Attention tier**: LSTM(64, sequences), 4-head self-attention, residual, layer norm, average pooling, dense 32.", {"bullet": True, "space_after": 8}),
        ("**Sentiment and FedAvg**: one extra input channel; ten clients average weights, 2 rounds x 3 epochs.", {"bullet": True, "space_after": 8}),
        ("**Offline MIL model**: gated attention pools a day's headlines into one vector joined to an LSTM over prices.", {"bullet": True}),
    ], size=14, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "Architecture of the model tiers as implemented in models_dl.py and federated.py.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "The attention in the product runs over the 20 price steps, not over news instances. The MIL model in the offline study attends over headlines."

    # ---- 9 training configuration
    s = S[8]
    set_title(s, "Training and evaluation configuration")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Deep tiers", "Adam, learning rate 1e-3, MSE loss, batch 32, up to 50 epochs, validation split 0.15, early stopping (patience 7, best weights), seed 42"],
            ["Federated stage", "ten ticker clients, 2 rounds x 3 local epochs, weights averaged in proportion to training samples"],
            ["Baselines", "ARIMA(5,1,0), SARIMAX(1,1,1)x(1,1,1,5), Prophet, Random Forest (200 trees, lag 20), SVR (rbf, C = 10)"],
            ["Re-run for this report", f"{len(F.RR['seeds'])} seeds on the same 501 training rows; persistence baseline; true-target scoring; {F.RR['seconds'] / 60:.0f} min on a shared CPU"],
            ["Offline MIL study", "AdamW 2e-3, batch 128, up to 60 epochs, patience 7, hidden size 32, 5 seeds x 3 expanding folds, threshold 0.5"],
            ["Machine", "Core i5-12500, 15.7 GB RAM, no GPU; Python 3.11.9, TensorFlow 2.16.2, PyTorch 2.5.1 (CPU)"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=14, row_h=0.72, first_bold=True)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Hyper-parameters are those in config.py, models_dl.py and federated.py; no tuning was done for this report.", size=12, color=K.TXT, italic=True)
    notes[9] = "The first three rows are the shipped configuration. The last rows describe the added experiments, which reuse the shipped modules unchanged."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: forecast, band and aggregation")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_forecast.png"), "10"), 0.6, 1.3, 5.9, 5.65)
    rows = [["Step", "Rule"],
            ["Multi-step forecast", "feed each predicted close back into the 20-day window"],
            ["Rolled-forward bar", "Open, High, Low set to the prediction; volume and sentiment kept"],
            ["Confidence band", "prediction +/- 1.96 x residual std x sqrt(h); lower floor 0.01"],
            ["Trend flag", "up if the day-5 forecast is at or above the last close"],
            ["FedAvg", "w = sum over clients of (n_i / n) x w_i"],
            ["MIL pooling (offline)", "z = sum of a_i h_i, a_i = softmax of a gated score"]]
    K.table(s, 6.8, 1.4, [2.0, 3.95], rows, font_size=12.5, row_h=0.55, first_bold=True)
    K.text(s, 6.8, 5.4, 5.95, 1.5, [
        ("The 5-day forecast stored for each ticker comes from the federated global model; the 30-day forecast comes from the local attention + sentiment model.", {"bullet": True}),
    ], size=13, color=K.INK)
    notes[10] = "This mirrors forecast.py (recursive_forecast) and federated.py (fedavg). Because one-step residuals set the band, it widens only with the square root of the horizon and does not reflect model bias."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 7.0, 5.65)
    rows = [["Module", "Role"], ["data_loader.py", "yfinance, CSV, synthetic fallback"], ["sentiment.py", "NewsAPI, FinBERT-tone, daily score"], ["baselines.py", "ARIMA, SARIMAX, Prophet, RF, SVR"],
            ["models_dl.py", "windows, scalers, LSTM tiers"], ["federated.py", "FedAvg simulation"], ["forecast.py", "5- and 30-day forecasts"], ["main.py", "7 endpoints, SPA serving"],
            ["frontend/src", "6 React screens"], ["tests/, scripts/", f"{F.PYTEST_TOTAL} tests, smoke, experiments"]]
    K.table(s, 7.9, 1.4, [2.1, 2.73], rows, font_size=12, row_h=0.5, first_bold=True)
    K.text(s, 7.9, 6.5, 4.83, 0.5, "Level-1 data-flow diagram of the platform.", size=11.5, color=K.TXT, italic=True)
    notes[11] = "Level 1: load data, align sentiment, train baselines and deep tiers, aggregate federated weights, write artefacts, serve them, draw screens."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Entities and UML (no database)")
    wipe(s)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 0.6, 1.3, 6.0, 4.95)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 6.75, 1.3, 6.0, 5.2)
    K.text(s, 0.6, 6.35, 6.0, 0.7, "QuantPulse keeps no database; the ER diagram is logical (prices, headlines, daily sentiment, model tiers, metrics, forecasts, artefact files).", size=11.5, color=K.TXT, italic=True)
    K.text(s, 6.75, 6.55, 6.0, 0.5, "The backend is mostly functions grouped in modules; the diagram shows modules and the API app.", size=11.5, color=K.TXT, italic=True)
    notes[12] = "Honest point: there is no persistence layer and no user model. Everything is regenerated by python -m backend.train."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    rows = [["Layer", "Technology"],
            ["Language and API", "Python 3.11.9, FastAPI 0.141.1, Uvicorn 0.52.4; CORS limited to localhost origins"],
            ["Deep learning", "TensorFlow 2.16.2 with Keras 3.15.1 (LSTM, MultiHeadAttention, manual FedAvg)"],
            ["Classical models", "scikit-learn 1.9.0 (Random Forest, SVR), statsmodels 0.15.0 (ARIMA, SARIMAX), Prophet 1.4.0"],
            ["Language model", "transformers 4.47.1 with PyTorch 2.5.1 (CPU): FinBERT-tone for inference; offline MIL models in PyTorch"],
            ["Data", "yfinance 1.7.0, pandas 3.0.5, NumPy 1.26.4; NewsAPI (optional key); FNSPID headlines for the offline study"],
            ["Front end", "React 19, Vite 8, Recharts 3, Framer Motion, React Router 7"],
            ["Testing and run", f"pytest, FastAPI TestClient, smoke script, Playwright captures; run.bat or Docker; ports {F.API_PORT} and {F.WEB_PORT}"]]
    K.table(s, 0.6, 1.45, [2.6, 9.53], rows, font_size=14, row_h=0.65, first_bold=True)
    notes[13] = "Versions are those installed on the measurement PC. TensorFlow has to be imported before scikit-learn on this machine, so the tests and experiment scripts import it first."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Data loader, five baselines, LSTM and attention tiers, sentiment channel, FedAvg", "Done", "python -m backend.train writes metrics, forecasts and models for 10 tickers"],
            ["FinBERT-tone scoring and daily alignment", "Done", f"headlines are synthetic templates by default ({hl_lo}-{hl_hi} per ticker)"],
            ["API (7 endpoints) and React website (6 screens)", "Done", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} smoke checks; {F.PYTEST_PASSED}/{F.PYTEST_TOTAL} pytest tests"],
            ["Multiple instance learning on real headlines", "Offline only", f"scripts/mil_study.py; best MIL variant {max(mm[k]['summary']['accuracy']['mean'] for k in ('lstm_mil_mean', 'lstm_mil_max', 'lstm_mil_attention', 'mil_attention_news_only')) * 100:.1f} % vs always-up {up_rate * 100:.1f} %"],
            ["Precision, recall and F1 in the product", "Not done", "product reports MAE, RMSE, R2 and direction only"],
            ["Social-media text source", "Not done", "no data source available"],
            ["Real federated deployment, database, accounts", "Not done", "FedAvg is simulated in one process; no persistence or login"]]
    K.table(s, 0.6, 1.4, [5.4, 1.4, 5.33], rows, font_size=12.5, row_h=0.64)
    notes[14] = "State of the code base. The last four rows are the honest gaps against the batch objectives."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"${pers:.2f}", f"mean error of 'tomorrow = today' (persistence) on the test windows", K.ORANGE),
                                   (f"${best_true:.2f}", "best deep tier (LSTM + attention) scored against real closes", K.BLUE),
                                   (f"{da_true * 100:.0f}% vs {da_ship * 100:.0f}%", "direction accuracy: real closes vs as reported by the app", K.GREEN),
                                   (f"{up_rate * 100:.1f}%", f"always-up accuracy; MIL attention model {mm['lstm_mil_attention']['summary']['accuracy']['mean'] * 100:.1f}%", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.35, 2.85, 1.2, v, l, c, vsize=24, lsize=11)
    K.picture(s, trim(F.fig("f02_true_mae_vs_persistence.png"), "f02"), 0.6, 2.7, 6.0, 3.25)
    K.picture(s, trim(F.fig("f03_clipping_and_direction.png"), "f03"), 6.75, 2.7, 6.0, 3.25)
    K.text(s, 0.6, 6.05, 12.13, 1.0, [
        (f"Shipped artefacts: Random Forest has the lowest error on {wins_rf} of 10 tickers; sentiment and FedAvg raise the deep-tier error. Forward test from 2026-09-08: 5-day forecast MAE ${fw['short']['mean_mae']:.2f} vs ${fw['short']['mean_persistence_mae']:.2f} for no change, "
         f"trend right for {fw['short']['trend_hits']} of 10; mean forecast {fw['short']['mean_pred_change_pct']:+.1f}% vs actual {fw['short']['mean_actual_change_pct']:+.1f}%. The base paper's R2 of 0.91 was not reproduced (different data and protocol).", {}),
    ], size=12.5, color=K.TXT)
    notes[15] = (f"Persistence beats every deep tier on real closes. The app scores test targets clipped to the training range, which inflates direction from {da_true * 100:.0f} to {da_ship * 100:.0f} percent. "
                 f"The MIL study on real headlines found no gain over a price-only LSTM: attention MIL minus price-only is {pd_['acc_diff'] * 100:+.1f} points with a 95 percent interval of {pd_['ci95'][0] * 100:+.1f} to {pd_['ci95'][1] * 100:+.1f}.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    cw, ch = 3.95, 2.62
    grid = [("03_dashboard.png", "Dashboard: ten tickers, last close, trend, 5-day outlook"), ("16_forecast_top.png", "Forecast: NVDA 5-day outlook and notice about stale artefacts"),
            ("14_forecast_table.png", "Forecast table with actual close and forecast miss"), ("06_models_comparison.png", "Model comparison: ablation charts for NVDA"),
            ("12_models_table.png", "Deep-tier metrics table"), ("08_sentiment.png", "News sentiment: source and FinBERT scorer")]
    for i, (n_, cap) in enumerate(grid):
        r, c = divmod(i, 3)
        shot_box(s, n_, 0.6 + c * (cw + 0.19), 1.3 + r * (ch + 0.14), cw, ch, cap)
    K.text(s, 0.6, 6.72, 12.13, 0.3, "Real captures of the running application at 1440 x 900 with the shipped artefacts and live Yahoo Finance prices.", size=11, color=K.TXT, italic=True)
    notes[16] = "Real screenshots from the running website. The forecast table shows the stored forecast next to the closes that actually followed, so the miss is visible to the user."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", "pytest tests passed (pipeline and API)", K.GREEN), (f"{F.SMOKE_PASSED} / {F.SMOKE_TOTAL}", "smoke-test checks passed against the live API", K.BLUE),
                                   (f"{lat('forecast_short'):.0f} ms", "median time of a stored 5-day forecast call (127.0.0.1)", K.ORANGE),
                                   (f"{lat('sentiment') / 1000:.1f} s", "median time of a sentiment call (FinBERT scoring)", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            [f"Direction reported by the app {da_ship * 100:.0f}% vs {da_true * 100:.0f}% against real closes (targets clipped to the training range)", "Both reported; true-target scoring added in the re-run"],
            ["Sentiment channel is zero for every training row (headlines only for the last 90 days)", "Stated as a limitation; placebo run shows no sentiment effect can be measured"],
            [f"Stored 5-day forecasts averaged {fw['short']['mean_pred_change_pct']:+.1f}% while prices moved {fw['short']['mean_actual_change_pct']:+.1f}%", "Forward test added; banner on the Forecast screen explains stale artefacts"],
            [f"History call takes {lat('history_120d'):.0f} ms median because it re-downloads prices", "Documented; caching listed as future work"]]
    K.table(s, 0.6, 2.95, [6.4, 5.73], rows, font_size=13, row_h=0.78)
    notes[17] = "Tests run offline with stubs for network and FinBERT; the smoke script drives the live server. Every observation came from running the code and is recorded rather than hidden."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "Corrective action"],
            ["Free news APIs return about a month of headlines, so real news cannot cover the training window", "Labelled synthetic fallback in the product; offline MIL study on the public FNSPID dataset instead"],
            ["Multiple instance learning and F1 are in the objectives but not in the base paper's pipeline", "Added scripts/mil_study.py with bags, gated attention, accuracy, precision, recall, F1 and a placebo"],
            [f"Deep tiers do not beat 'tomorrow = today' (${pers:.2f} vs ${best_true:.2f})", "Persistence baseline and true-target scoring reported next to the shipped numbers"],
            ["Short, clipped test period: 97 windows per ticker, prices above the training range", "Scaler clipping documented; forward test on the 30 days that followed the training end"],
            ["CPU-only machine shared with other jobs; TensorFlow and scikit-learn DLL order", "Experiments run sequentially with TensorFlow imported first; timings reported as indicative"]]
    K.table(s, 0.6, 1.5, [5.9, 6.23], rows, font_size=14, row_h=0.88)
    notes[18] = "Each challenge was met by a concrete design choice or by measuring it and saying so in the report."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Fix the evaluation", "Score against real closes, add the persistence baseline and walk-forward validation, and fill the sentiment channel for the whole history.", K.BLUE, "1"),
        ("Bring MIL into the product", "Add the bag-of-headlines model with a classification head that reports accuracy, precision, recall and F1.", K.GREEN, "2"),
        ("Real news and social media", "Use an archived news source for the full window and add a social-media text source.", K.ORANGE, "3"),
        ("Make it deployable", "Cache prices, retrain on a schedule, add a database and accounts, and try federated learning across real clients.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.09, 1.6, 2.85, 3.9, t, b_, col, gl, body_size=16)
    K.box(s, 0.6, 5.75, 12.13, 0.95, fill=K.FHEAD, line=None)
    K.text(s, 0.85, 5.9, 11.6, 0.7, "Priority: items 1 and 2 close the largest honest gaps - a trustworthy evaluation and the missing multiple-instance component.", size=16, color=K.INK, anchor="m")
    notes[19] = "Plan to the final review. The first two items address the biggest gaps against the objectives."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = ("Likely questions: why the deep models do not beat persistence; why the sentiment tier is worse; where multiple instance learning is; "
                 "what the offline study found; how the numbers compare with the base paper.")

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


def render(path, outdir):
    """Export every slide to PNG with PowerPoint COM (absolute path; serialised with the other builders)."""
    import win32com.client

    from .comlock import com_lock

    os.makedirs(outdir, exist_ok=True)
    with com_lock():
        app = win32com.client.DispatchEx("PowerPoint.Application")
        try:
            pres = app.Presentations.Open(os.path.abspath(path), True, False, False)
            pres.SaveAs(os.path.abspath(outdir), 18)
            pres.Close()
        finally:
            app.Quit()


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
