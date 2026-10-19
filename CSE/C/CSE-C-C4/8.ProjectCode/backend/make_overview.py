"""Generates QuantPulse_Product_Overview.pdf from real training artifacts.

Usage: python -m backend.make_overview   (from QuantPulse/ dir)
Reads artifacts/metrics.json - all tables contain measured values.
"""
from __future__ import annotations
import os, json
from fpdf import FPDF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "artifacts")
OUT = os.path.join(ROOT, "QuantPulse_Product_Overview.pdf")


class Doc(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "QuantPulse  -  Product Overview", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"QuantPulse Product Overview  |  page {self.page_no()}/{{nb}}", align="C")

    def h1(self, t):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(15, 23, 42)
        self.multi_cell(0, 10, t, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def h2(self, t):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 41, 59)
        self.ln(3)
        self.multi_cell(0, 8, t, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, t):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, t, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def bullets(self, items):
        self.set_font("Helvetica", "", 10.5)
        for it in items:
            self.multi_cell(0, 6, "-  " + it, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)


def table(pdf: Doc, headers, rows, widths=None):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    w = widths or [pdf.w - 20 - sum([30] * (len(headers) - 1))] + [30] * (len(headers) - 1)
    for i, h in enumerate(headers):
        pdf.cell(w[i], 8, h, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(20, 20, 20)
    fill = False
    for r in rows:
        if fill:
            pdf.set_fill_color(241, 245, 249)
        for i, c in enumerate(r):
            pdf.cell(w[i], 7, str(c), border=1, fill=fill, align="C")
        pdf.ln()
        fill = not fill
    pdf.ln(2)


def main():
    m = json.load(open(os.path.join(ART, "metrics.json")))
    tickers = sorted(m.keys())
    pdf = Doc()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, 20)

    # cover
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 34)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 14, "QuantPulse", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "AI-Powered Short-Term Stock Trend Forecasting", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, "Product overview: features, technology, architecture, operating guide, "
                         "and measured forecasting results across a 10-ticker universe.", align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"Coverage: {', '.join(tickers)}   |   Generated from live training artifacts", align="C")

    # 1 overview
    pdf.add_page()
    pdf.h1("1. Product overview")
    pdf.body("QuantPulse is a forecasting platform for retail and professional traders. It combines "
             "market price history (OHLCV) with financial-news sentiment to produce 5-day short-term "
             "closing-price forecasts with 95% confidence bands, 30-day longer-horizon projections, "
             "per-ticker directional trend signals (UP/DOWN), and a model-comparison dashboard that "
             "benchmarks the hybrid deep model against five classical baselines.")
    pdf.bullets([
        "5-day forecasts with confidence bands + 30-day horizon per ticker.",
        "Directional trend accuracy (up/down) evaluated on a held-out test period.",
        "Sentiment overlay: FinBERT-tone news tone aligned to trading days.",
        "Ablation dashboard: LSTM vs LSTM+Attention vs +Sentiment vs Full Hybrid with federated averaging.",
        "FastAPI backend + React/Tailwind dashboard; one-click run.bat and Docker support.",
    ])

    # 2 features
    pdf.h2("2. Key features")
    pdf.bullets([
        "Configurable ticker universe (default: TSLA, AAPL, AMZN, MSFT, GOOGL, NVDA, META, FDX, IBM, ORCL).",
        "Live OHLCV ingestion via Yahoo Finance with bundled-CSV and labeled-synthetic fallbacks.",
        "NewsAPI ingestion with local caching; FinBERT-tone sentiment scoring (inference only).",
        "Simulated federated training (per-ticker clients + FedAvg) runnable on a laptop CPU.",
        "Input validation and graceful errors across all API endpoints.",
    ])

    # 3 stack
    pdf.h2("3. Technology stack")
    table(pdf, ["Layer", "Technology"],
          [["Backend API", "Python 3.11, FastAPI, Uvicorn (127.0.0.1:8000)"],
           ["Deep models", "TensorFlow/Keras: LSTM-64 + 4-head attention"],
           ["Baselines", "statsmodels (ARIMA/SARIMAX), Prophet, scikit-learn (RF/SVR)"],
           ["Sentiment", "NewsAPI + FinBERT-tone (transformers, PyTorch CPU)"],
           ["Frontend", "React 18, Vite, Tailwind CSS, Recharts"],
           ["Packaging", "run.bat, Dockerfile, docker-compose.yml"]],
          widths=[55, 125])

    # 4 architecture
    pdf.h2("4. Architecture summary")
    pdf.body("OHLCV (20-day Min-Max windows) and daily FinBERT sentiment form the model input. "
             "Five classical baselines are scored on an 80/20 chronological split. The deep track "
             "trains LSTM, LSTM+Attention, and LSTM+Attention+Sentiment tiers per ticker; a "
             "federated stage then averages per-ticker client weights with FedAvg (2 rounds, "
             "in-process simulation). Recursive multi-step decoding produces the 5- and 30-day "
             "forecasts; residual-based bands give the 95% intervals. The FastAPI layer serves "
             "forecasts, metrics, sentiment, and history; the React SPA renders charts, the "
             "comparison dashboard, and the sentiment panel.")

    # 5 run
    pdf.h2("5. How to run")
    pdf.bullets([
        "Automatic: double-click run.bat, then open http://localhost:8000.",
        "Docker: docker compose up --build, then open http://localhost:8000.",
        "Manual: create venv (3.11), pip install -r backend/requirements.txt, "
        "python -m backend.train, then uvicorn backend.app.main:app --host 127.0.0.1 --port 8000.",
        "Full instructions and troubleshooting: HOW_TO_RUN.md.",
    ])

    # 6 results
    pdf.add_page()
    pdf.h1("6. Results and metrics (measured)")
    modes = sorted({v.get("mode", "?") for v in m.values()})
    pdf.body(f"All values below were produced by executing backend/train.py (80/20 chronological "
             f"split; deep tiers evaluated on windowed test sets). Data mode(s) in this build: "
             f"{', '.join(modes)}. Sentiment scorer: {m[tickers[0]]['sentiment'].get('scorer')}; "
             f"news source: {m[tickers[0]]['sentiment'].get('source')}.")
    pdf.h2("6.1 Ablation - deep model tiers (MAE / directional accuracy)")
    rows = []
    for t in tickers:
        d = m[t]["deep"]
        r = [t]
        for k in ("lstm", "lstm_attention", "lstm_attention_sentiment", "hybrid_federated"):
            v = d.get(k, {})
            r.append(f"{v.get('mae', float('nan')):.2f}/{v.get('directional_accuracy', float('nan')) * 100:.1f}%" if "mae" in v else "-")
        rows.append(r)
    table(pdf, ["Ticker", "LSTM", "+Attn", "+Sent", "Hybrid(Fed)"], rows, widths=[24] + [39] * 4)

    pdf.h2("6.2 Classical baselines (MAE / directional accuracy)")
    rows = []
    for t in tickers:
        b = m[t]["baselines"]
        r = [t]
        for k in ("arima", "sarimax", "prophet", "random_forest", "svr"):
            v = (b.get(k) or {}).get("metrics")
            r.append(f"{v['mae']:.2f}/{v['directional_accuracy'] * 100:.1f}%" if v else "-")
        rows.append(r)
    table(pdf, ["Ticker", "ARIMA", "SARIMAX", "Prophet", "RF", "SVR"], rows, widths=[24] + [31] * 5)

    pdf.h2("6.3 Tesla deep dive")
    t = m["TSLA"]
    pdf.body(f"Last close ${t['last_close']:.2f}; 5-day outlook: {t['trend'].upper()}. "
             f"Hybrid test MAE {t['deep']['hybrid_federated']['mae']:.2f}, "
             f"R2 {t['deep']['hybrid_federated']['r2']:.3f}, directional accuracy "
             f"{t['deep']['hybrid_federated']['directional_accuracy'] * 100:.1f}%. "
             f"Training/validation loss curves and predicted-vs-actual charts are stored in "
             f"artifacts/plots/ and embedded in the dashboard screenshots.")
    for img, cap in [("TSLA_predicted_vs_actual.png", "Tesla predicted vs actual (test period)"),
                     ("TSLA_lstm_attention_sentiment_loss.png", "Tesla LSTM+Attention+Sentiment loss curves")]:
        p = os.path.join(ART, "plots", img)
        if os.path.exists(p):
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, cap, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.image(p, w=170)
    pdf.output(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
