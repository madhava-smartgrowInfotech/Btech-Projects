"""
Single source of truth for the documentation build of QuantPulse (CSE-C-C4).

Batch details come from 1.C4_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
experiments/**/metrics.json (written by scripts/run_experiments.py, mil_study.py, measure_api.py) or from artifacts/metrics.json
(the numbers the shipped app displays). docs/REPORT_FACTS.md is the human-readable copy; docs/NARRATIVE.md fixes the story every document tells.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C4
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "QuantPulse"
TITLE = "Stock Market Prediction Using Multi-Source Multiple Instance Learning"
FULL_TITLE = TITLE
SUBTITLE = "Short-term stock trend forecasting with LSTM, attention, news sentiment and simulated federated learning"
TAGLINE = "QuantPulse: ten tickers, five classical baselines, four deep-model tiers, a FinBERT sentiment channel, a simulated FedAvg stage and a six-screen React website"
BATCH_NO = "C4"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
COLLEGE_SHORT = "[COLLEGE NAME]"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Pottepaka Lingaswamy", "23K91A05J7"),
    ("Maduna Naveen Kumar", "23K91A05D7"),
    ("Meedigeri Keerthi", "24K95A0517"),
    ("Mareddy Sai Karthik", "23K91A05E8"),
]
STUDENTS_UPPER = [(n.upper(), r) for n, r in STUDENTS]
GUIDE = "K Anusha"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("Y. Nejatbakhsh and M. Aliasgari, \"Enhancing stock market prediction with hybrid deep learning: Integrating LSTM, transformer attention, "
              "federated learning, and sentiment analysis,\" IEEE Access, vol. 14, pp. 3926-3942, 2026, doi: 10.1109/ACCESS.2025.3649668.")
BASE_SHORT = "Nejatbakhsh and Aliasgari (IEEE Access, 2026)"
API_PORT, WEB_PORT = 8404, 5404
TICKERS = ["TSLA", "AAPL", "AMZN", "MSFT", "GOOGL", "NVDA", "META", "FDX", "IBM", "ORCL"]


def _load(*p):
    path = os.path.join(EXP, *p, "metrics.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


SUM = _load("shipped_summary")        # shipped artifacts/metrics.json aggregated
FWD = _load("forward_test_shipped")   # shipped forecasts vs the closes that followed
RR = _load("rerun")                   # five-seed re-run on the 501 training rows
MIL = _load("mil_study")              # multiple-instance-learning study on real headlines
API = _load("api_latency")
SHIP = json.load(open(os.path.join(CODE, "artifacts", "metrics.json"), encoding="utf-8"))

# measured by the test runs (docs/metrics/*.txt, REPORT_FACTS section 6) - updated by hand after the final run
PYTEST_TOTAL, PYTEST_PASSED = 56, 56
SMOKE_TOTAL, SMOKE_PASSED = 26, 26

TIER_LABEL = {"lstm": "LSTM", "lstm_attention": "LSTM + attention", "lstm_attention_sentiment": "LSTM + attention + sentiment",
              "attention_shuffled_sentiment": "Placebo (shuffled sentiment)", "hybrid_federated": "Hybrid (FedAvg)"}
BASE_LABEL = {"arima": "ARIMA(5,1,0)", "sarimax": "SARIMAX", "prophet": "Prophet", "random_forest": "Random Forest", "svr": "SVR"}

BASE_PAPER_RESULTS = {  # as printed in the base paper (text of Sections III-IV); the paper's tables are images and are not quoted
    "r2_avg": 0.91, "r2_min_company": 0.84, "tsla_mse": 0.039, "tsla_mae": 0.179, "tsla_r2": 0.888, "lstm_trend_acc": 65.36,
    "trend_best": "Airbnb 94 %, Google 86 %", "trend_worst": "Tesla 34.9 %, IBM 18 %", "prophet_5d_r2": -0.7126,
    "window": "one month (30 days of NewsAPI headlines) for the hybrid; three months for the 5-day LSTM trend accuracy", "split": "70/15/15 hybrid, 80/20 baselines",
}


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def mstd(pair, d=2):
    return f"{pair[0]:.{d}f} ± {pair[1]:.{d}f}"


def shot(name):
    return os.path.join(SHOTS, name)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)
