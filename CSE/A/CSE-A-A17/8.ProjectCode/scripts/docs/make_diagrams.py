"""Draws the TrendCast design diagrams (matplotlib, 150 dpi) into docs/diagrams/.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; all twelve
    python -m scripts.docs.make_diagrams arch dfd1  # selected keys

01-06 are here; 07-12 are in diagrams_more.py. Every box mirrors a real module, route or file of the product
(backend/main.py, backend/state.py, backend/gemini_api.py, src/*.py, models/*.joblib).
"""

import os
import sys

from . import facts as F
from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, WHITE,
                      arrow, box, canvas, circle, diamond, ellipse, panel, save as _save, store, uml_class)

MIN_FS = 8.0


def save(fig, path):
    """Bump every text to at least MIN_FS points (readable when the page is scaled to half width), then save."""
    for t in fig.findobj(__import__("matplotlib.text", fromlist=["Text"]).Text):
        if t.get_text() and t.get_fontsize() < MIN_FS:
            t.set_fontsize(MIN_FS)
    _save(fig, path)


W, H = 11.0, 6.8


def out(name):
    os.makedirs(F.DIAG, exist_ok=True)
    return os.path.join(F.DIAG, name)


def txt(ax, x, y, s, fs=8.5, color=INK, ha="center", bold=False, style="normal"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color, fontweight="bold" if bold else "normal", style=style, zorder=6, linespacing=1.2)


# ------------------------------------------------------------------------------------------------ 01 architecture
def d_arch():
    fig, ax = canvas(W, 7.4, 100)          # height = 67.3
    H_ = 100 * 7.4 / W
    # presentation tier
    panel(ax, 1, 54, 70, 12, "Presentation tier (browser)")
    box(ax, 17, 58.5, 28, 6.5, "React 19 console, 13 pages\nVite dev server, port 5317", fc=NAVY, fs=8.5, bold=True)
    box(ax, 52, 58.5, 29, 6.5, "Streamlit app.py (original UI)\n11 pages, same src/ package", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.5)
    box(ax, 88, 58.5, 20, 6.5, "Gemini REST API\n(optional, external)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8.5, ls="--")
    # proxy
    box(ax, 17, 49.5, 31, 4.4, "Vite proxy: /api  ->  127.0.0.1:8317", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8.5)
    arrow(ax, (17, 55.2), (17, 51.8), color=NAVY)
    # application tier
    panel(ax, 1, 28, 70, 18.5, "Application tier: FastAPI, port 8317, 22 routes (/api/...)")
    box(ax, 17, 38.2, 29, 9.5, "Routes\ndata/upload  explore  demand/table\nfeatures/build  training/*  domain/*\nevaluation  forecast  ai/*", fc=NAVY, fs=7.8)
    box(ax, 44, 38.2, 21, 9.5, "Shared state  S\nprocess-wide dict\n+ RLock (one user)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 62.5, 38.2, 15, 9.5, "pydantic\nTrainRequest\nDomainRequest\nForecastRequest\nAskRequest", fc=LIGHT, tc=INK, ec=GREY, fs=7.2)
    arrow(ax, (17, 47.3), (17, 43.2), color=NAVY)
    box(ax, 17, 30.9, 29, 3.4, "backend/gemini_api.py (requests)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=7.6)
    # pipeline tier
    panel(ax, 1, 12.5, 98, 13.5, "Pipeline tier: src/ package (pure Python, shared with the Streamlit UI)")
    mods = ["data_loader\n(validate)", "preprocessing\n(clean, merge)", "demand_\nforecasting", "feature_\nengineering", "baseline_\nmodels", "xgboost_\nmodel", "domain_\nadaptation", "evaluation\n(metrics)", "gemini_\nhelper"]
    for i, m in enumerate(mods):
        box(ax, 6.6 + i * 10.85, 17.3, 10.2, 7.2, m, fc=BLUE if i != 6 else TEAL, fs=7.6)
    arrow(ax, (44, 33.2), (44, 26.4), color=NAVY)
    txt(ax, 47.5, 29.8, "calls", 7.5, NAVY)
    arrow(ax, (17, 29.0), (17, 26.2), color=PURPLE, lw=1.1)
    # storage tier
    panel(ax, 1, 1, 98, 9.5, "Storage")
    box(ax, 14, 4.2, 25, 4.6, "In-memory pandas tables\n(raw, merged, daily, features)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.6)
    box(ax, 40, 4.2, 22, 4.6, "models/baseline_xgboost.joblib\nmodels/adapted_xgboost.joblib", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=7.2)
    box(ax, 62, 4.2, 18, 4.6, "models/feature_info.joblib\n(feature column list)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=7.2)
    box(ax, 85, 4.2, 24, 4.6, ".env: ports, Gemini key and model\n(git-ignored)", fc=LIGHT, tc=INK, ec=GREY, fs=7.4)
    arrow(ax, (14, 13.6), (14, 6.6), color=GREY, lw=1.1)
    arrow(ax, (45, 13.6), (40, 6.6), color=GREY, lw=1.1)
    # gemini link
    arrow(ax, (88, 55.2), (88, 31.5), color=PURPLE, ls="--", lw=1.2)
    ax.plot([88, 33], [31.5, 31.5], color=PURPLE, ls="--", lw=1.2, zorder=3)
    arrow(ax, (33, 31.5), (31.6, 30.9), color=PURPLE, lw=1.2)
    txt(ax, 92.5, 43, "aggregated\nsummary only\n(no raw rows)", 7.4, PURPLE)
    ax.set_ylim(0, H_)
    save(fig, out("01_system_architecture.png"))


# ------------------------------------------------------------------------------------------------ 02 workflow
def d_flow():
    fig, ax = canvas(W, 6.0, 100)          # height 54.5
    steps_top = ["1  Upload CSVs\ntransactions, articles,\ncustomers (optional)", "2  Validate and clean\ndates, null ids, price > 0,\nexact duplicates", "3  Merge\nleft join articles\n(+ customers)",
                 "4  Daily demand\nunits sold per\narticle per day", "5  Fill missing days\ndemand = 0 between first\nand last sale", "6  Features\ncalendar, lag, rolling,\nencoded attributes"]
    steps_bot = ["7  Chronological split\nfirst 80 % of dates train,\nlast 20 % test", "8  Train and compare\nmoving average, XGBoost\n(optional tuning)", "9  Domain adaptation\nsource model, classifier,\nweighted model",
                 "10  Evaluation\nRMSE MAE MAPE R2,\nfeature importance", "11  Forecast\nrecursive 7, 14 or\n30 days", "12  AI explanation\nGemini, aggregated\nnumbers only"]
    xs = [9.5 + i * 16.2 for i in range(6)]
    for i, s in enumerate(steps_top):
        box(ax, xs[i], 40, 14.5, 11, s, fc=NAVY, fs=7.8)
        if i:
            arrow(ax, (xs[i - 1] + 7.4, 40), (xs[i] - 7.4, 40), color=GREY)
    for i, s in enumerate(steps_bot):
        x = xs[5 - i]
        fc = PURPLE if i == 5 else (TEAL if i == 2 else BLUE)
        box(ax, x, 18, 14.5, 11, s, fc=fc, fs=7.8, ls="--" if i == 5 else "-")
        if i:
            arrow(ax, (xs[5 - i + 1] - 7.4, 18), (x + 7.4, 18), color=GREY)
    # connector 6 -> 7
    arrow(ax, (xs[5], 34.4), (xs[5], 23.7), color=GREY)
    # annotations
    txt(ax, 50, 52, "Every page is gated: a later step answers 409 with a plain-language message until the earlier step has produced its output.", 8.2, GREY, style="italic")
    box(ax, (xs[4] + xs[3]) / 2, 5.0, 34, 5.2, "models/baseline_xgboost.joblib" + chr(10) + "models/adapted_xgboost.joblib", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    arrow(ax, (xs[4], 7.7), (xs[4], 12.4), color=TEAL, lw=1.1)
    arrow(ax, (xs[3], 7.7), (xs[3], 12.4), color=TEAL, lw=1.1)
    box(ax, 27, 5.0, 36, 5.2, "No leakage: lags shifted by one day, split by" + chr(10) + "date, TimeSeriesSplit for tuning", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    save(fig, out("02_high_level_workflow.png"))


# ------------------------------------------------------------------------------------------------ 03 DFD 0
def d_dfd0():
    fig, ax = canvas(W, 4.9, 100)          # height 44.5
    circle(ax, 50, 21, 11.5, "TrendCast\n0", fc=NAVY, fs=11)
    box(ax, 12, 21, 18, 8, "Analyst", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=11, bold=True, r=0.6)
    box(ax, 50, 41, 26, 6.5, "Dataset provider\n(H&M competition files)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=9.5, r=0.6)
    box(ax, 88, 21, 20, 8, "Gemini service\n(optional)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=10, r=0.6, ls="--")
    arrow(ax, (21, 24.5), (39, 24.5), "files, row limit, training fraction,\ntuning flag, domain choice,\nforecast request", lo=(0, 5.2), fs=8, color=NAVY)
    arrow(ax, (39, 17.5), (21, 17.5), "quality report, charts, metrics,\nshift report, importance,\nforecast", lo=(0, -5.5), fs=8, color=TEAL)
    arrow(ax, (50, 37.7), (50, 32.6), "articles.csv, transactions_train.csv,\ncustomers.csv", lo=(14.5, 0), fs=8, color=NAVY)
    arrow(ax, (61.5, 24.5), (78, 24.5), "aggregated summary\n+ question", lo=(0, 4.2), fs=8, color=PURPLE)
    arrow(ax, (78, 17.5), (61.5, 17.5), "plain-language\nexplanation", lo=(0, -4.2), fs=8, color=PURPLE)
    save(fig, out("03_dfd_level0.png"))


# ------------------------------------------------------------------------------------------------ 06 UML
def d_uml():
    fig, ax = canvas(W, 7.2, 100)          # height 65.5
    H_ = 100 * 7.2 / W
    fs = 7.0
    # column 1: application + state
    a = uml_class(ax, 0.8, 64.5, 25, "FastAPI app", ["title = TrendCast API 1.0.0", "CORS: localhost:5317"],
                  ["upload_data()", "explore()  demand_table()", "build_features()", "train_baseline()  train_xgb()", "run_domain()  domain_last()", "get_evaluation()", "forecast()", "ai_explain()  ai_forecast_summary()"], fs=fs, stereotype="backend/main.py")
    s = uml_class(ax, 0.8, 29.0, 25, "State  S", ["dict: 17 keys", "merged, daily_demand,", "feature_table, results,", "baseline_model, adapted_model", "domain_run, last_forecast", "LOCK = RLock()"], ["reset_downstream()", "clean(obj)", "env(key)"], fs=fs, stereotype="backend/state.py", hdr=ORANGE)
    # column 2: request models + gemini_api
    y = 64.5
    for name, attrs in (("TrainRequest", ["train_fraction: float 0.5-0.95", "tune: bool"]), ("DomainRequest", ["domain_col: str", "source: float", "target: float"]),
                        ("ForecastRequest", ["article_id: int", "horizon: int  (7, 14, 30)"]), ("AskRequest", ["question: str"])):
        b = uml_class(ax, 29, y, 21, name, attrs, [], fs=fs, stereotype="pydantic", hdr=BLUE)
        y = b[1] - 1.8
    g = uml_class(ax, 29, y - 0.5, 21, "gemini_api", [], ["configured()", "ask(question, context)", "build_context()"], fs=fs, stereotype="optional", hdr=PURPLE)
    # column 3: data modules
    y = 64.5
    for name, meth in (("preprocessing", ["clean_transactions()", "clean_articles()", "clean_customers()", "merge_datasets()", "data_quality_report()"]),
                       ("demand_forecasting", ["aggregate_daily_demand()", "fill_missing_dates_per_article()"]),
                       ("feature_engineering", ["add_time_features()", "add_lag_rolling_features()", "encode_categoricals()", "build_feature_table()", "get_feature_columns()"])):
        b = uml_class(ax, 54, y, 22, name, [], meth, fs=fs, stereotype="module", hdr=NAVY)
        y = b[1] - 1.8
    # column 4: models
    y = 64.5
    for name, meth, hdr in (("baseline_models", ["chronological_split()", "split_summary()", "moving_average_forecast()", "train_random_forest()"], NAVY),
                            ("xgboost_model", ["train_xgboost(X, y, sample_weight)", "tune_xgboost()", "get_feature_importance()"], NAVY),
                            ("domain_adaptation", ["split_domains()", "train_domain_classifier()", "compute_instance_weights()", "domain_shift_summary()", "train_adapted_model()"], TEAL),
                            ("evaluation", ["safe_mape()  evaluate_model()", "compare_models()", "before_after_adaptation_report()"], NAVY)):
        b = uml_class(ax, 78.5, y, 21, name, [], meth, fs=fs, stereotype="module", hdr=hdr)
        y = b[1] - 1.2
    # relations
    arrow(ax, (25.8, 58), (53.8, 58), "", color=GREY, ls="--", lw=1.1)
    arrow(ax, (25.8, 55), (78.3, 55), "uses", color=GREY, ls="--", lw=1.1, lo=(-6, 1.1), fs=7.4)
    arrow(ax, (13, 36.2), (13, 30.1), "", color=ORANGE, lw=1.3)
    txt(ax, 17.5, 33.3, "reads / writes", 7.4, ORANGE)
    arrow(ax, (25.8, 60.5), (28.8, 60.5), "", color=BLUE, lw=1.1)
    arrow(ax, (25.8, 49), (28.8, 22.5), "", color=PURPLE, ls="--", lw=1.1)
    txt(ax, 38.5, 17.2, "uses src.gemini_helper\n+ state.env", 7.2, PURPLE)
    ax.plot([64, 64], [34.5, 34.5], color=GREY)
    arrow(ax, (78.4, 37.3), (78.4, 41.5), "", color=TEAL, lw=1.3)
    txt(ax, 70.5, 39.5, "sample_weight", 7.4, TEAL)
    ax.set_ylim(0, H_)
    save(fig, out("06_uml_class.png"))


DRAWERS = {"arch": d_arch, "flow": d_flow, "dfd0": d_dfd0, "uml": d_uml}


def main():
    from . import diagrams_more as M
    from . import diagrams_dfd as D
    from . import diagrams_uml as U
    from . import diagrams_dfd2 as D2
    all_ = dict(DRAWERS)
    all_.update(D.DRAWERS)
    all_.update(U.DRAWERS)
    all_.update(D2.DRAWERS)
    all_.update(M.DRAWERS)
    from . import diagrams_er as ER
    all_.update(ER.DRAWERS)
    from . import diagrams_flow as FL
    all_.update(FL.DRAWERS)
    keys = sys.argv[1:] or list(all_)
    for k in keys:
        all_[k]()


if __name__ == "__main__":
    main()
