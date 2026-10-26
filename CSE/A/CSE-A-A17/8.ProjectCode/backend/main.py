"""
main.py
--------
Thin FastAPI layer over the existing `src/` pipeline. Every route calls the same
functions the Streamlit app (app.py) calls; no pipeline logic is rewritten here.

Run:  uvicorn backend.main:app --port 8317     (run.bat does this)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import logging

logging.getLogger('streamlit').setLevel(logging.ERROR)  # src/ imports streamlit; its no-runtime warnings are noise here

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src import (
    baseline_models,
    data_loader,
    demand_forecasting,
    domain_adaptation,
    evaluation,
    feature_engineering,
    preprocessing,
    xgboost_model,
)

from . import gemini_api
from .state import (
    ADAPTED_MODEL_PATH,
    BASELINE_MODEL_PATH,
    FEATURE_INFO_PATH,
    LOCK,
    MODEL_DIR,
    S,
    clean,
    env,
    reset_downstream,
)

app = FastAPI(title="TrendCast API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5317", "http://127.0.0.1:5317"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOMAIN_COLUMNS = ["sales_channel_id", "product_group_name", "department_name"]
COLUMN_LABELS = {
    "sales_channel_id": "Sales channel",
    "product_group_name": "Product group",
    "department_name": "Department",
}


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def need(key: str, message: str):
    """Return S[key] or raise a 409 with a plain-language 'do this first' message."""
    value = S.get(key)
    if value is None or (isinstance(value, pd.DataFrame) and value.empty):
        raise HTTPException(status_code=409, detail=message)
    return value


def ensure_daily() -> pd.DataFrame:
    merged = need("merged", "Upload and process your data first (Data Upload).")
    if S["daily_demand"] is None:
        S["daily_demand"] = demand_forecasting.aggregate_daily_demand(merged)
    return S["daily_demand"]


def feature_cols_of(ft: pd.DataFrame) -> list[str]:
    return feature_engineering.get_feature_columns(ft)


def feature_payload() -> dict:
    ft = need("feature_table", "Build the feature table first (Feature Engineering).")
    head = ft.head(50).copy()
    return clean({
        "rows": int(ft.shape[0]),
        "columns": int(ft.shape[1]),
        "feature_columns": feature_cols_of(ft),
        "head_columns": list(head.columns),
        "head": head,
    })


def comparison_rows() -> list[dict]:
    if not S["results"]:
        return []
    return clean(evaluation.compare_models(S["results"]))


def top_importance(top_n: int) -> list[dict]:
    model, ft = S["baseline_model"], S["feature_table"]
    if model is None or ft is None:
        return []
    pairs = xgboost_model.get_feature_importance(model, feature_cols_of(ft), top_n=top_n)
    return [{"feature": f, "importance": float(i)} for f, i in pairs]


def split_for(fraction: float):
    ft = need("feature_table", "Build the feature table first (Feature Engineering).")
    train_df, test_df = baseline_models.chronological_split(ft, train_fraction=fraction)
    if train_df.empty or test_df.empty:
        raise HTTPException(status_code=400, detail="That split leaves the train or test set empty. Choose a different training fraction.")
    S["train_df"], S["test_df"] = train_df, test_df
    return ft, train_df, test_df, baseline_models.split_summary(train_df, test_df)


# ----------------------------------------------------------------------
# health + state
# ----------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/state")
def state():
    return {
        "data_loaded": S["merged"] is not None,
        "daily_ready": S["daily_demand"] is not None,
        "features_ready": S["feature_table"] is not None,
        "baseline_ran": "Moving Average" in S["results"],
        "xgboost_trained": S["baseline_model"] is not None,
        "domain_done": S["domain_eval"] is not None,
        "forecast_done": S["last_forecast"] is not None,
        "saved_model_exists": BASELINE_MODEL_PATH.exists(),
        "gemini_configured": gemini_api.configured(),
    }


# ----------------------------------------------------------------------
# 1. data upload
# ----------------------------------------------------------------------
def _read_csv(upload: UploadFile, label: str, nrows: int | None = None) -> pd.DataFrame:
    try:
        return pd.read_csv(upload.file, nrows=nrows)
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail=f"The {label} file is empty.")
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"The {label} file could not be read as a CSV ({exc}).")


@app.post("/api/data/upload")
def upload_data(
    transactions: UploadFile = File(...),
    articles: UploadFile = File(...),
    customers: UploadFile | None = File(None),
    sample_rows: int = Form(200_000),
):
    nrows = None if sample_rows <= 0 else int(sample_rows)
    with LOCK:
        try:
            txn_raw = _read_csv(transactions, "transactions", nrows)
            data_loader.validate_columns(txn_raw, data_loader.REQUIRED_TRANSACTION_COLUMNS, "transaction dataset")
            art_raw = _read_csv(articles, "articles")
            data_loader.validate_columns(art_raw, data_loader.REQUIRED_ARTICLE_COLUMNS, "article dataset")
            if customers is not None and customers.filename:
                cust_raw = _read_csv(customers, "customers")
                data_loader.validate_columns(cust_raw, data_loader.REQUIRED_CUSTOMER_COLUMNS, "customer dataset")
            else:
                cust_raw = pd.DataFrame()
        except data_loader.DataValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        cleaned_txn = preprocessing.clean_transactions(txn_raw)
        if cleaned_txn.empty:
            raise HTTPException(status_code=400, detail="No usable transaction rows remain after cleaning. Check the date and price columns.")
        cleaned_art = preprocessing.clean_articles(art_raw)
        cleaned_cust = preprocessing.clean_customers(cust_raw)
        merged = preprocessing.merge_datasets(cleaned_txn, cleaned_art, cleaned_cust)

        reset_downstream()
        S["transactions_raw"], S["articles_raw"], S["customers_raw"], S["merged"] = cleaned_txn, cleaned_art, cleaned_cust, merged
        report = preprocessing.data_quality_report(txn_raw, cleaned_txn, merged)
        report["raw_rows"] = int(len(txn_raw))
        report["articles"] = int(len(cleaned_art))
        report["customers_file"] = bool(not cleaned_cust.empty)
        S["quality_report"] = clean(report)
    return S["quality_report"]


@app.get("/api/data/report")
def data_report():
    need("merged", "Upload and process your data first (Data Upload).")
    return S["quality_report"]


# ----------------------------------------------------------------------
# 2. exploration + demand table
# ----------------------------------------------------------------------
@app.get("/api/explore")
def explore():
    with LOCK:
        daily = ensure_daily()

        trend = daily.groupby("t_dat")["demand"].sum().reset_index()
        trend["t_dat"] = trend["t_dat"].dt.date.astype(str)

        d = daily.copy()
        d["month"] = d["t_dat"].dt.to_period("M").astype(str)
        monthly = d.groupby("month")["demand"].sum().reset_index()
        d["week"] = d["t_dat"].dt.to_period("W").astype(str)
        weekly = d.groupby("week")["demand"].sum().reset_index()

        top = daily.groupby("article_id")["demand"].sum().sort_values(ascending=False).head(10)

        def by_cat(col: str, top_n: int = 15):
            if col not in daily.columns:
                return None
            g = daily.groupby(col)["demand"].sum().sort_values(ascending=False).head(top_n)
            return [{"label": str(k), "demand": int(v)} for k, v in g.items()]

        counts, edges = np.histogram(daily["price"].dropna(), bins=50)
        price_hist = [
            {"label": f"{edges[i]:.3f}", "from": float(edges[i]), "to": float(edges[i + 1]), "count": int(counts[i])}
            for i in range(len(counts))
        ]

        return clean({
            "daily": trend.rename(columns={"t_dat": "date"}),
            "monthly": monthly,
            "weekly": weekly,
            "top_products": [{"article_id": str(k), "demand": int(v)} for k, v in top.items()],
            "department": by_cat("department_name"),
            "colour": by_cat("colour_group_name"),
            "channel": by_cat("sales_channel_id"),
            "price_hist": price_hist,
            "total_units": int(daily["demand"].sum()),
            "rows": int(len(daily)),
        })


@app.get("/api/demand/table")
def demand_table(limit: int = 200):
    with LOCK:
        daily = ensure_daily()
        limit = max(1, min(limit, 2000))
        head = daily.head(limit)
        return clean({"total": int(len(daily)), "columns": list(head.columns), "rows": head})


# ----------------------------------------------------------------------
# 3. feature engineering
# ----------------------------------------------------------------------
@app.post("/api/features/build")
def build_features():
    with LOCK:
        daily = ensure_daily()
        filled = demand_forecasting.fill_missing_dates_per_article(daily)
        ft, mappings = feature_engineering.build_feature_table(filled)
        S["feature_table"], S["feature_mappings"] = ft, mappings
        S["train_df"] = S["test_df"] = None
        S["baseline_model"] = S["source_model"] = S["adapted_model"] = S["domain_eval"] = S["domain_run"] = S["last_forecast"] = None
        S["results"] = {}
        return feature_payload()


@app.get("/api/features")
def get_features():
    return feature_payload()


# ----------------------------------------------------------------------
# 4. model training
# ----------------------------------------------------------------------
class TrainRequest(BaseModel):
    train_fraction: float = Field(0.8, ge=0.5, le=0.95)
    tune: bool = False


@app.get("/api/training/split")
def training_split(train_fraction: float = 0.8):
    if not 0.5 <= train_fraction <= 0.95:
        raise HTTPException(status_code=400, detail="Training fraction must be between 0.5 and 0.95.")
    with LOCK:
        _, _, _, summary = split_for(train_fraction)
        return clean(summary)


@app.post("/api/training/baseline")
def train_baseline(req: TrainRequest):
    with LOCK:
        _, train_df, test_df, summary = split_for(req.train_fraction)
        preds = baseline_models.moving_average_forecast(train_df, test_df)
        metrics = evaluation.evaluate_model(test_df["demand"], preds)
        S["results"]["Moving Average"] = metrics
        return clean({"metrics": metrics, "split": summary, "comparison": comparison_rows()})


@app.post("/api/training/xgboost")
def train_xgb(req: TrainRequest):
    with LOCK:
        ft, train_df, test_df, summary = split_for(req.train_fraction)
        cols = feature_cols_of(ft)
        X_train, y_train = train_df[cols], train_df["demand"]
        X_test, y_test = test_df[cols], test_df["demand"]
        best_params = None
        if req.tune:
            model, best_params = xgboost_model.tune_xgboost(X_train, y_train, n_iter=10, cv_splits=3)
        else:
            model = xgboost_model.train_xgboost(X_train, y_train)
        metrics = evaluation.evaluate_model(y_test, model.predict(X_test))

        S["baseline_model"] = model
        S["results"]["XGBoost"] = metrics
        MODEL_DIR.mkdir(exist_ok=True)
        joblib.dump(model, BASELINE_MODEL_PATH)
        joblib.dump({"feature_cols": cols}, FEATURE_INFO_PATH)
        return clean({
            "metrics": metrics,
            "best_params": best_params,
            "tuned": req.tune,
            "split": summary,
            "comparison": comparison_rows(),
        })


@app.post("/api/training/load")
def load_saved_model():
    with LOCK:
        try:
            S["baseline_model"] = joblib.load(BASELINE_MODEL_PATH)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="No saved model found yet. Train one first.")
        return {"loaded": True}


@app.get("/api/training/results")
def training_results():
    return {"comparison": comparison_rows()}


# ----------------------------------------------------------------------
# 5. domain adaptation
# ----------------------------------------------------------------------
def _domain_values(ft: pd.DataFrame, col: str) -> list[dict]:
    mapping = (S["feature_mappings"] or {}).get(col)
    out = []
    for v in sorted(ft[col].dropna().unique().tolist()):
        if mapping is not None:
            label = mapping.get(int(v), str(v))
        elif col == "sales_channel_id":
            label = f"Channel {int(v)}"
        else:
            label = str(v)
        out.append({"value": v, "label": str(label)})
    return out


@app.get("/api/domain/options")
def domain_options():
    ft = need("feature_table", "Build the feature table first (Feature Engineering).")
    options = []
    for col in DOMAIN_COLUMNS:
        if col in ft.columns:
            options.append({"column": col, "label": COLUMN_LABELS[col], "values": _domain_values(ft, col)})
    return clean({"options": options})


class DomainRequest(BaseModel):
    domain_col: str
    source: float
    target: float


def _hist(source: pd.Series, target: pd.Series, bins: int = 30) -> list[dict]:
    both = pd.concat([source, target])
    edges = np.histogram_bin_edges(both.dropna(), bins=bins)
    s_counts, _ = np.histogram(source.dropna(), bins=edges)
    t_counts, _ = np.histogram(target.dropna(), bins=edges)
    return [
        {"label": f"{edges[i]:.2f}", "from": float(edges[i]), "to": float(edges[i + 1]),
         "source": int(s_counts[i]), "target": int(t_counts[i])}
        for i in range(len(s_counts))
    ]


def _box(series: pd.Series) -> dict:
    s = series.dropna()
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75]).tolist()
    iqr = q3 - q1
    lo = float(s[s >= q1 - 1.5 * iqr].min())
    hi = float(s[s <= q3 + 1.5 * iqr].max())
    return {"min": lo, "q1": q1, "median": med, "q3": q3, "max": hi, "mean": float(s.mean()), "n": int(len(s))}


@app.post("/api/domain/run")
def run_domain(req: DomainRequest):
    with LOCK:
        ft = need("feature_table", "Build the feature table first (Feature Engineering).")
        if req.domain_col not in DOMAIN_COLUMNS or req.domain_col not in ft.columns:
            raise HTTPException(status_code=400, detail="Choose one of the offered domain columns.")
        if req.source == req.target:
            raise HTTPException(status_code=400, detail="Source and target values must be different.")

        # The domain column is excluded from the features so the classifier cannot read the label off a feature.
        cols = [c for c in feature_cols_of(ft) if c != req.domain_col]
        source_df, target_df = domain_adaptation.split_domains(ft, req.domain_col, req.source, req.target)
        if source_df.empty or target_df.empty:
            raise HTTPException(status_code=400, detail="One of the domains has no data. Choose different values.")

        source_X, source_y = source_df[cols], source_df["demand"]
        target_train, target_test = baseline_models.chronological_split(target_df, train_fraction=0.5)
        if target_test.empty or target_train.empty:
            raise HTTPException(status_code=400, detail="The target domain has too few dates to hold out a test half. Choose a larger target domain.")
        target_test_X, target_test_y = target_test[cols], target_test["demand"]

        source_model = xgboost_model.train_xgboost(source_X, source_y)
        metrics_before = evaluation.evaluate_model(target_test_y, source_model.predict(target_test_X))

        classifier, acc = domain_adaptation.train_domain_classifier(source_X, target_df[cols])
        shift = domain_adaptation.domain_shift_summary(source_X, target_df[cols])
        top_feature = shift.iloc[0]["feature"]

        weights = domain_adaptation.compute_instance_weights(classifier, source_X)
        adapted = domain_adaptation.train_adapted_model(source_X, source_y, weights)
        metrics_after = evaluation.evaluate_model(target_test_y, adapted.predict(target_test_X))

        S["source_model"], S["adapted_model"] = source_model, adapted
        S["domain_eval"] = (metrics_before, metrics_after)
        MODEL_DIR.mkdir(exist_ok=True)
        joblib.dump(adapted, ADAPTED_MODEL_PATH)

        report = evaluation.before_after_adaptation_report(metrics_before, metrics_after)
        mapping_labels = {o["value"]: o["label"] for o in _domain_values(ft, req.domain_col)}
        result = clean({
            "domain_col": req.domain_col,
            "source_label": mapping_labels.get(req.source, str(req.source)),
            "target_label": mapping_labels.get(req.target, str(req.target)),
            "source_rows": int(len(source_df)),
            "target_rows": int(len(target_df)),
            "target_test_rows": int(len(target_test)),
            "classifier_accuracy": acc,
            "shift": shift.head(15),
            "top_shift_feature": top_feature,
            "histogram": _hist(source_X[top_feature], target_df[top_feature]),
            "box": {"source": _box(source_X[top_feature]), "target": _box(target_df[top_feature])},
            "weights": {"mean": float(np.mean(weights)), "max": float(np.max(weights)), "min": float(np.min(weights))},
            "before": metrics_before,
            "after": metrics_after,
            "report": report,
        })
        S["domain_run"] = result
        return result


@app.get("/api/domain/last")
def domain_last():
    """The most recent domain-adaptation run, so the screen survives a page reload."""
    return {"run": S["domain_run"]}


# ----------------------------------------------------------------------
# 6. evaluation
# ----------------------------------------------------------------------
@app.get("/api/evaluation")
def get_evaluation():
    domain = None
    if S["domain_eval"] is not None:
        before, after = S["domain_eval"]
        domain = {"report": clean(evaluation.before_after_adaptation_report(before, after)),
                  "meta": {k: (S["domain_run"] or {}).get(k) for k in ("domain_col", "source_label", "target_label")}}
    return clean({
        "comparison": comparison_rows(),
        "domain": domain,
        "importance": top_importance(20),
        "has_results": bool(S["results"]),
    })


# ----------------------------------------------------------------------
# 7. demand forecast
# ----------------------------------------------------------------------
@app.get("/api/forecast/articles")
def forecast_articles():
    ft = need("feature_table", "Build the feature table first (Feature Engineering).")
    if S["baseline_model"] is None:
        raise HTTPException(status_code=409, detail="Train the XGBoost model first (Model Training).")
    daily = S["daily_demand"]
    ids = sorted(ft["article_id"].unique().tolist())
    totals = ft.groupby("article_id")["demand"].sum()
    label = {}
    if daily is not None and "product_type_name" in daily.columns:
        label = daily.groupby("article_id")["product_type_name"].first().to_dict()
    return clean({
        "articles": [{"id": int(i), "label": str(label.get(i, "")), "units": int(totals.get(i, 0))} for i in ids]
    })


class ForecastRequest(BaseModel):
    article_id: int
    horizon: int = Field(7)


@app.post("/api/forecast")
def forecast(req: ForecastRequest):
    if req.horizon not in (7, 14, 30):
        raise HTTPException(status_code=400, detail="Horizon must be 7, 14 or 30 days.")
    with LOCK:
        ft = need("feature_table", "Build the feature table first (Feature Engineering).")
        model = need("baseline_model", "Train the XGBoost model first (Model Training).")
        cols = feature_cols_of(ft)

        article_history = ft[ft["article_id"] == req.article_id].sort_values("t_dat")
        if len(article_history) < 5:
            raise HTTPException(status_code=400, detail="Not enough historical data to create lag features for this product.")

        last_row = article_history.iloc[-1].copy()
        last_date = last_row["t_dat"]
        recent_demand = article_history["demand"].tolist()

        rows = []
        for step in range(1, req.horizon + 1):
            future_date = last_date + pd.Timedelta(days=step)
            row = last_row.copy()
            row["t_dat"] = future_date

            row["year"] = future_date.year
            row["month"] = future_date.month
            row["day"] = future_date.day
            row["day_of_week"] = future_date.dayofweek
            row["is_weekend"] = int(future_date.dayofweek >= 5)
            row["month_sin"] = np.sin(2 * np.pi * future_date.month / 12)
            row["month_cos"] = np.cos(2 * np.pi * future_date.month / 12)
            row["dow_sin"] = np.sin(2 * np.pi * future_date.dayofweek / 7)
            row["dow_cos"] = np.cos(2 * np.pi * future_date.dayofweek / 7)

            for lag in [1, 7, 14, 28]:
                row[f"lag_{lag}"] = recent_demand[-lag] if len(recent_demand) >= lag else 0
            for window in [7, 14, 28]:
                row[f"rolling_mean_{window}"] = np.mean(recent_demand[-window:])
            for window in [7, 28]:
                row[f"rolling_std_{window}"] = np.std(recent_demand[-window:]) if len(recent_demand) > 1 else 0

            pred = max(0, float(model.predict(pd.DataFrame([row[cols]]))[0]))
            rows.append({"t_dat": future_date, "predicted_demand": pred})
            recent_demand.append(pred)

        forecast_df = pd.DataFrame(rows)
        S["last_forecast"] = forecast_df
        history = article_history.tail(60)[["t_dat", "demand"]]
        return clean({
            "article_id": req.article_id,
            "horizon": req.horizon,
            "history": history,
            "forecast": forecast_df,
            "total": float(forecast_df["predicted_demand"].sum()),
            "history_days": int(len(article_history)),
        })


# ----------------------------------------------------------------------
# 8. AI insights (optional)
# ----------------------------------------------------------------------
@app.get("/api/ai/status")
def ai_status():
    return {"configured": gemini_api.configured(), "model": gemini_api.model_name()}


class AskRequest(BaseModel):
    question: str = ""


def _domain_summary() -> dict | None:
    run = S["domain_run"]
    if not run:
        return None
    return {k: run.get(k) for k in ("domain_col", "source_label", "target_label", "classifier_accuracy", "top_shift_feature", "before", "after")}


def _ai_call(question: str, **context):
    try:
        return {"answer": gemini_api.ask(question, gemini_api.build_context(**context))}
    except RuntimeError as exc:
        status = 503 if not gemini_api.configured() else 502
        raise HTTPException(status_code=status, detail=str(exc))
    except Exception as exc:  # network failure etc. The rest of the app does not depend on this
        raise HTTPException(status_code=502, detail=f"AI Insights is temporarily unavailable ({exc}). Every other page still works.")


@app.post("/api/ai/explain")
def ai_explain(req: AskRequest):
    importance = [(i["feature"], i["importance"]) for i in top_importance(10)]
    return _ai_call(
        req.question.strip() or "Summarize the model results.",
        metrics=S["results"] or None,
        feature_importance=importance or None,
        domain_shift=_domain_summary(),
    )


@app.post("/api/ai/forecast-summary")
def ai_forecast_summary():
    fdf = need("last_forecast", "Generate a forecast first (Demand Forecast).")
    start_val, end_val = fdf["predicted_demand"].iloc[0], fdf["predicted_demand"].iloc[-1]
    trend = "increase" if end_val > start_val else ("decrease" if end_val < start_val else "stay stable")
    importance = [(i["feature"], i["importance"]) for i in top_importance(10)]
    return _ai_call(
        "Summarize this demand forecast in 2-3 short sentences for a project demo.",
        feature_importance=importance or None,
        forecast_summary={
            "horizon_days": len(fdf),
            "start_predicted_demand": round(float(start_val), 2),
            "end_predicted_demand": round(float(end_val), 2),
            "trend": trend,
        },
    )
