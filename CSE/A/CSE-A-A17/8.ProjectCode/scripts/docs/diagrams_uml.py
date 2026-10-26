"""UML class diagram (06): application, request models, state and src/ modules; no empty compartments."""

import os

from matplotlib.patches import Rectangle

from . import facts as F
from .dgm_lib import GREY, INK, NAVY, ORANGE, PURPLE, TEAL, BLUE, WHITE, arrow, canvas, save as _save

W, HIN = 11.0, 8.7
LH = 2.3          # line height in drawing units
FS = 8.0


def save(fig, path):
    for t in fig.findobj(__import__("matplotlib.text", fromlist=["Text"]).Text):
        if t.get_text() and t.get_fontsize() < FS:
            t.set_fontsize(FS)
    _save(fig, path)


def cls(ax, x, y, w, name, stereo, attrs, methods, hdr=NAVY):
    """Class box, top-left (x, y). Returns (x, y_bottom, w, h)."""
    head = 5.0
    ha = (len(attrs) * LH + 1.0) if attrs else 0
    hm = (len(methods) * LH + 1.0) if methods else 0
    h = head + ha + hm
    ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
    ax.add_patch(Rectangle((x, y - head), w, head, fc=hdr, ec=NAVY, lw=1.3, zorder=3))
    ax.text(x + w / 2, y - 1.45, f"<<{stereo}>>", ha="center", va="center", color=WHITE, fontsize=FS, style="italic", zorder=4)
    ax.text(x + w / 2, y - 3.6, name, ha="center", va="center", color=WHITE, fontsize=FS + 1.2, fontweight="bold", zorder=4)
    yy = y - head
    for i, a in enumerate(attrs):
        ax.text(x + 0.8, yy - 0.5 - LH / 2 - i * LH, a, ha="left", va="center", fontsize=FS, color=INK, family="DejaVu Sans Mono", zorder=4)
    yy -= ha
    if attrs and methods:
        ax.plot([x, x + w], [yy, yy], color=NAVY, lw=1.0, zorder=3)
    for i, m in enumerate(methods):
        ax.text(x + 0.8, yy - 0.5 - LH / 2 - i * LH, m, ha="left", va="center", fontsize=FS, color=INK, family="DejaVu Sans Mono", zorder=4)
    return (x, y - h, w, h)


def d_uml():
    fig, ax = canvas(W, HIN, 100)
    H_ = 100 * HIN / W
    top = H_ - 5.0
    # column 1: application and state
    app = cls(ax, 0.8, top, 26, "FastAPI app", "backend/main.py", ["title: TrendCast API 1.0.0", "CORS: localhost:5317"],
              ["upload_data()", "explore()  demand_table()", "build_features()", "train_baseline()", "train_xgb()", "run_domain()", "get_evaluation()", "forecast()", "ai_explain()"])
    st = cls(ax, 0.8, app[1] - 6, 26, "State  S", "backend/state.py", ["dict, 17 keys:", "merged, daily_demand,", "feature_table, results,", "baseline_model,", "adapted_model, domain_run", "LOCK = RLock()"],
             ["reset_downstream()", "clean(obj)", "env(key)"], hdr=ORANGE)
    # column 2: request models and gemini_api
    y = top
    for name, attrs in (("TrainRequest", ["train_fraction: 0.5-0.95", "tune: bool"]), ("DomainRequest", ["domain_col: str", "source: float", "target: float"]),
                        ("ForecastRequest", ["article_id: int", "horizon: 7 | 14 | 30"]), ("AskRequest", ["question: str"])):
        b = cls(ax, 30, y, 21, name, "pydantic", attrs, [], hdr=BLUE)
        y = b[1] - 2.0
    cls(ax, 30, y - 1.0, 21, "gemini_api", "optional", ["uses gemini_helper", "key from state.env()"], ["configured()", "ask(question, ctx)"], hdr=PURPLE)
    # column 3: data modules
    y = top
    for name, meth in (("preprocessing", ["clean_transactions()", "clean_articles()", "clean_customers()", "merge_datasets()", "data_quality_report()"]),
                       ("demand_forecasting", ["aggregate_daily_demand()", "fill_missing_dates()"]),
                       ("feature_engineering", ["add_time_features()", "add_lag_rolling()", "encode_categoricals()", "build_feature_table()", "get_feature_columns()"])):
        b = cls(ax, 54, y, 19, name, "module", [], meth)
        y = b[1] - 2.5
    # column 4: model modules
    y = top
    tops = {}
    for name, meth, hdr, gap in (("baseline_models", ["chronological_split()", "moving_average_forecast()", "train_random_forest()"], NAVY, 2.5),
                                 ("xgboost_model", ["train_xgboost()", "tune_xgboost()", "get_feature_importance()"], NAVY, 7.0),
                                 ("domain_adaptation", ["split_domains()", "train_domain_classifier()", "compute_instance_weights()", "domain_shift_summary()", "train_adapted_model()"], TEAL, 2.5),
                                 ("evaluation", ["safe_mape()", "evaluate_model()", "compare_models()", "before_after_adaptation_report()"], NAVY, 2.5)):
        b = cls(ax, 76, y, 23.8, name, "module", [], meth, hdr=hdr)
        tops[name] = (y, b)
        y = b[1] - gap
    # relationships
    arrow(ax, (27.1, top - 2.5), (29.8, top - 2.5), color=BLUE, lw=1.2)
    arrow(ax, (13.8, app[1] - 0.1), (13.8, app[1] - 5.9), color=ORANGE, lw=1.3)
    ax.text(15.2, app[1] - 3.0, "reads / writes", fontsize=FS, color=ORANGE, ha="left", va="center", zorder=6)
    # bus above the boxes: app -> data modules and model modules
    by = H_ - 1.6
    ax.plot([13.8, 13.8, 87.9], [top + 0.05, by, by], color=GREY, lw=1.3, ls="--", zorder=3)
    ax.plot([63.5, 63.5], [by, top + 0.1], color=GREY, lw=1.3, ls="--", zorder=3)
    arrow(ax, (63.5, by), (63.5, top + 0.1), color=GREY, ls="--", lw=1.3)
    arrow(ax, (87.9, by), (87.9, top + 0.1), color=GREY, ls="--", lw=1.3)
    ax.text(40, by + 0.1, "calls the src/ modules", fontsize=FS, color=GREY, ha="center", va="bottom", zorder=6)
    # domain_adaptation -> xgboost_model (sample_weight)
    xb = tops["xgboost_model"][1]
    da_top = tops["domain_adaptation"][0]
    arrow(ax, (82, da_top), (82, xb[1] - 0.1), color=TEAL, lw=1.5)
    ax.text(83.2, (da_top + xb[1]) / 2, "sample_weight", fontsize=FS, color=TEAL, ha="left", va="center", zorder=6)
    ax.set_ylim(0, H_)
    save(fig, os.path.join(F.DIAG, "06_uml_class.png"))


DRAWERS = {"uml": d_uml}
