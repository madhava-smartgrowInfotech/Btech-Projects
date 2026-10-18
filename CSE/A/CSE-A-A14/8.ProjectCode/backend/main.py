"""FastAPI layer for the Churn Intelligence React frontend.

Every route is a thin wrapper over the existing functions in src/ (the Streamlit app keeps
working untouched). Run:  python -m uvicorn backend.main:app --port 8314
"""
import io
import os
import threading
from contextlib import asynccontextmanager
from typing import Optional

os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 1))  # silence joblib core-count warning

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import config  # noqa: E402
from .auth import check_credentials, make_token, require_user  # noqa: E402
from .helpers import SafeJSON, downsample  # noqa: E402
from .state import STATE  # noqa: E402

# --- existing project modules (src/ is on sys.path via backend.state) ---
from data_loader import (  # noqa: E402
    coerce_numeric_looking_columns, detect_id_column, detect_target_column, load_csv,
    normalize_target, profile_dataset, validate_dataset_for_training,
)
from eda import compute_kpis  # noqa: E402
from evaluation import results_to_table  # noqa: E402
from explainability import (  # noqa: E402
    SHAP_AVAILABLE, clean_feature_label, get_shap_explainer, global_importance, local_explanation,
)
from persistence import save_artifacts  # noqa: E402
from prediction import build_batch_predictions, score_customers, validate_columns_for_prediction  # noqa: E402
from preprocessing import (  # noqa: E402
    build_preprocessor, class_distribution, clean_missing_and_duplicates, get_feature_names,
    train_test_split_data,
)
from retention_engine import generate_recommendations, recommendations_dataframe  # noqa: E402
from risk_segmentation import build_risk_table, risk_distribution_summary  # noqa: E402
from sample_data import generate_sample_churn_data  # noqa: E402
from train_models import MODEL_REGISTRY, OPTIONAL_MODELS, REQUIRED_MODELS, select_best_model, train_selected_models  # noqa: E402
from utils import RISK_ORDER, assign_risk_category, make_tenure_group  # noqa: E402


@asynccontextmanager
async def lifespan(_: FastAPI):
    STATE.restore_from_disk()
    yield


app = FastAPI(title="Churn Intelligence API", version="1.0.0", lifespan=lifespan, default_response_class=SafeJSON)
app.add_middleware(
    CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return SafeJSON({"detail": f"Unexpected server error: {exc}"}, status_code=500,
                    headers={"Access-Control-Allow-Origin": "*"})


public = APIRouter(prefix="/api")
private = APIRouter(prefix="/api", dependencies=[Depends(require_user)])


def ok(payload, status: int = 200):
    return SafeJSON(payload, status_code=status)


# ----------------------------------------------------------------------------- guards
def need_data():
    if STATE.working_df is None or STATE.target_col is None:
        raise HTTPException(409, "No prepared dataset yet. Load a dataset on the Data page and click “Prepare data”.")
    return STATE.working_df


def need_model():
    df = need_data()
    if not STATE.has_model:
        raise HTTPException(409, "No active model yet. Train and save a model on the Training page first.")
    missing = [c for c in STATE.model_features if c not in df.columns]
    if missing:
        raise HTTPException(409, f"The loaded dataset lacks columns the active model needs: {', '.join(missing)}.")
    return df


def feature_names() -> list:
    return STATE.model_feature_names or get_feature_names(STATE.preprocessor)


def dense(x):
    return x.toarray() if hasattr(x, "toarray") else np.asarray(x)


def ensure_explainer():
    """Rebuild the SHAP explainer lazily (e.g. after a restart) when SHAP is installed."""
    if STATE.explainer is not None or not SHAP_AVAILABLE or not STATE.has_model:
        return STATE.explainer
    try:
        bg = None
        if STATE.working_df is not None:
            sample = STATE.working_df[STATE.model_features].head(200)
            bg = dense(STATE.preprocessor.transform(sample))
        STATE.explainer = get_shap_explainer(STATE.model, bg, STATE.model_name)
    except Exception:
        STATE.explainer = None
    return STATE.explainer


def risk_table(display_cols: list | None = None) -> pd.DataFrame:
    df = need_model()
    cols = [c for c in (display_cols or []) if c in df.columns]
    table = build_risk_table(df, STATE.model_features, STATE.preprocessor, STATE.model, STATE.id_col,
                             STATE.risk_thresholds, display_cols=cols)
    table["risk_category"] = table["risk_category"].astype(str)
    return table


def find_row(cid: str):
    df = need_data()
    if STATE.id_col and STATE.id_col in df.columns:
        match = df[df[STATE.id_col].astype(str) == cid]
        if match.empty:
            raise HTTPException(404, f"Customer “{cid}” was not found in the loaded dataset.")
        return cid, match.iloc[0]
    try:
        idx = int(cid)
        return f"Row {idx}", df.iloc[idx]
    except (ValueError, IndexError):
        raise HTTPException(404, f"Row “{cid}” was not found in the loaded dataset.")


def explain_row(row):
    x_raw = pd.DataFrame([row[STATE.model_features]])
    proba = float(score_customers(x_raw, STATE.preprocessor, STATE.model)[0])
    x_dense = dense(STATE.preprocessor.transform(x_raw))[0]
    top_pos, top_neg, method = local_explanation(ensure_explainer(), STATE.model, x_dense, feature_names(), top_n=5)

    def pack(items):
        return [{"feature": f, "label": clean_feature_label(f), "value": float(v)} for f, v in items]

    return proba, pack(top_pos), pack(top_neg), method


def churn_by_category(df: pd.DataFrame, col: str, y: pd.Series) -> list:
    tmp = pd.DataFrame({"k": df[col].values, "y": y.values})
    g = tmp.groupby("k", dropna=True)["y"].agg(["mean", "count"]).reset_index()
    rows = [{"name": str(r["k"]), "rate": round(float(r["mean"]) * 100, 1), "count": int(r["count"])} for _, r in g.iterrows()]
    return sorted(rows, key=lambda r: -r["rate"])


def churn_by_tenure(df: pd.DataFrame, y: pd.Series) -> list:
    tmp = pd.DataFrame({"g": make_tenure_group(df["tenure"]).values, "y": y.values})
    g = tmp.groupby("g", observed=True)["y"].agg(["mean", "count"]).reset_index()
    return [{"name": str(r["g"]), "rate": round(float(r["mean"]) * 100, 1), "count": int(r["count"])} for _, r in g.iterrows()]


_importance_lock = threading.Lock()


def importance_payload(top: int = 15) -> dict:
    """Global importance (built-in / permutation / SHAP), cached per active model."""
    need_model()
    key = (id(STATE.model), STATE.X_test_t is not None)
    cached = STATE.importance_cache.get(key)
    if cached:
        return cached
    with _importance_lock:  # a warm-up thread and a request must not compute it twice
        return _compute_importance(key, top)


def _compute_importance(key, top: int) -> dict:
    cached = STATE.importance_cache.get(key)
    if cached:
        return cached
    if STATE.X_test_t is not None:
        X, y, basis = STATE.X_test_t, np.asarray(STATE.y_test), "held-out test split"
    else:
        df = STATE.working_df
        X = dense(STATE.preprocessor.transform(df[STATE.model_features]))
        y = normalize_target(df, STATE.target_col).values
        basis = "full dataset (model restored from disk)"
    X = dense(X)
    gi = global_importance(STATE.model, X, y, feature_names(), STATE.model_name, ensure_explainer())
    labels = {"model_importance": "Built-in importance", "permutation_importance": "Permutation importance",
              "shap_importance": "SHAP importance"}
    out = {
        "basis": basis, "shap_available": SHAP_AVAILABLE, "model_name": STATE.model_name,
        "methods": [
            {"key": k, "label": labels[k], "rows": [
                {"feature": r.feature, "label": clean_feature_label(r.feature), "importance": float(r.importance)}
                for r in gi[k].head(top).itertuples()]}
            for k in ("shap_importance", "permutation_importance", "model_importance") if k in gi
        ],
    }
    STATE.importance_cache[key] = out
    return out


def read_upload(file: UploadFile) -> pd.DataFrame:
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(422, "Please upload a .csv file.")
    try:
        raw = file.file.read()
        if not raw.strip():
            raise ValueError("the file is empty")
        return coerce_numeric_looking_columns(load_csv(io.BytesIO(raw)))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(422, f"Could not read the uploaded file: {e}")


def active_model_info() -> dict | None:
    if not STATE.has_model:
        return None
    meta = STATE.metadata or {}
    return {
        "name": STATE.model_name, "saved_at": meta.get("saved_at"), "metrics": meta.get("metrics", {}),
        "feature_cols": STATE.model_features, "training_dataset_size": meta.get("training_dataset_size"),
        "imbalance_strategy": meta.get("imbalance_strategy"),
    }


# ============================================================================ public
@public.get("/health")
def health():
    return ok({"status": "ok", "shap_available": SHAP_AVAILABLE, "model_loaded": STATE.has_model,
               "dataset_loaded": STATE.working_df is not None})


class LoginBody(BaseModel):
    email: str
    password: str


@public.post("/auth/login")
def login(body: LoginBody):
    if not check_credentials(body.email, body.password):
        raise HTTPException(401, "That email or password is not right. Use the demo account shown on the sign-in page.")
    return ok({"token": make_token(body.email.strip().lower()), "user": {"email": body.email.strip().lower(), "name": "Demo Analyst"}})


@private.get("/auth/me")
def me(user: dict = Depends(require_user)):
    return ok({"email": user["sub"], "name": "Demo Analyst"})


# ============================================================================ state
@private.get("/state")
def get_state():
    STATE.restore_from_disk()
    raw, work = STATE.raw_df, STATE.working_df
    return ok({
        "dataset": {
            "name": STATE.dataset_name, "loaded": raw is not None, "prepared": work is not None,
            "rows": None if raw is None else len(raw), "prepared_rows": None if work is None else len(work),
            "columns": None if raw is None else len(raw.columns),
        },
        "target_col": STATE.target_col, "id_col": STATE.id_col,
        "feature_count": len(STATE.feature_cols),
        "trained_models": list((STATE.trial or {}).get("results", {}).keys()),
        "model": active_model_info(), "thresholds": STATE.risk_thresholds,
        "shap_available": SHAP_AVAILABLE, "required_models": REQUIRED_MODELS, "optional_models": OPTIONAL_MODELS,
    })


# ============================================================================ data
def apply_dataset(df: pd.DataFrame, name: str) -> dict:
    df = coerce_numeric_looking_columns(df)
    prof = profile_dataset(df)
    with STATE.lock:
        STATE.raw_df, STATE.working_df, STATE.dataset_name = df, None, name
        STATE.target_col, STATE.id_col = prof.target_col, prof.id_col
        STATE.numeric_cols, STATE.categorical_cols = prof.numeric_cols, prof.categorical_cols
        STATE.feature_cols = prof.numeric_cols + prof.categorical_cols
        STATE.trial, STATE.prepare_report = None, None
        STATE.importance_cache.clear()
    return {"name": name, "rows": len(df), "columns": len(df.columns), "target_col": prof.target_col, "id_col": prof.id_col}


@private.post("/data/sample")
def load_sample():
    return ok(apply_dataset(generate_sample_churn_data(), "Sample telecom dataset (1,000 synthetic customers)"))


@private.post("/data/upload")
def upload(file: UploadFile = File(...)):
    df = read_upload(file)
    if len(df.columns) < 2:
        raise HTTPException(422, "The file needs at least two columns (features plus a churn column).")
    return ok(apply_dataset(df, file.filename))


def need_raw():
    if STATE.raw_df is None:
        raise HTTPException(409, "No dataset loaded yet. Upload a CSV or use the sample dataset.")
    return STATE.raw_df


@private.get("/data/preview")
def preview(rows: int = 15):
    df = need_raw()
    return ok({"columns": list(df.columns), "rows": df.head(max(1, min(rows, 100))).to_dict(orient="records")})


@private.get("/data/config")
def get_config():
    df = need_raw()
    return ok({
        "columns": list(df.columns), "target_col": STATE.target_col, "id_col": STATE.id_col,
        "numeric_cols": STATE.numeric_cols, "categorical_cols": STATE.categorical_cols,
        "detected_target": detect_target_column(df), "detected_id": detect_id_column(df),
    })


class ConfigBody(BaseModel):
    target_col: Optional[str] = None
    id_col: Optional[str] = None
    numeric_cols: list[str] = Field(default_factory=list)
    categorical_cols: list[str] = Field(default_factory=list)


@private.put("/data/config")
def put_config(body: ConfigBody):
    df = need_raw()
    cols = set(df.columns)
    for c in [body.target_col, body.id_col, *body.numeric_cols, *body.categorical_cols]:
        if c and c not in cols:
            raise HTTPException(422, f"Column “{c}” is not in the dataset.")
    if body.target_col and body.target_col == body.id_col:
        raise HTTPException(422, "The target and ID columns must be different.")
    bad = {body.target_col, body.id_col} & set(body.numeric_cols + body.categorical_cols)
    bad.discard(None)
    if bad:
        raise HTTPException(422, f"Feature columns cannot include the target or ID column ({', '.join(sorted(bad))}).")
    if set(body.numeric_cols) & set(body.categorical_cols):
        raise HTTPException(422, "A column cannot be both numeric and categorical.")
    with STATE.lock:
        STATE.target_col, STATE.id_col = body.target_col, body.id_col
        STATE.numeric_cols, STATE.categorical_cols = body.numeric_cols, body.categorical_cols
        STATE.feature_cols = body.numeric_cols + body.categorical_cols
        STATE.working_df, STATE.trial = None, None  # configuration changed: prepare again
    return get_config()


@private.get("/data/quality")
def quality():
    df = need_raw()
    prof = profile_dataset(df, target_col=STATE.target_col, id_col=STATE.id_col)
    errors = validate_dataset_for_training(df, STATE.target_col) if STATE.target_col else ["Select a churn / target column."]
    missing = [] if prof.missing_summary is None else [{"column": k, "count": int(v)} for k, v in prof.missing_summary.items()]
    return ok({
        "rows": prof.n_rows, "columns": prof.n_cols, "duplicates": prof.n_duplicates, "missing": missing,
        "warnings": prof.warnings, "errors": errors, "ready": not errors and bool(STATE.feature_cols),
        "feature_count": len(STATE.feature_cols),
    })


@private.post("/data/prepare")
def prepare():
    df = need_raw()
    if not STATE.target_col:
        raise HTTPException(422, "Select a churn / target column before preparing the data.")
    errors = validate_dataset_for_training(df, STATE.target_col)
    if errors:
        raise HTTPException(422, " ".join(errors))
    if not STATE.feature_cols:
        raise HTTPException(422, "No feature columns selected.")
    cleaned, report = clean_missing_and_duplicates(df, drop_duplicates=True)
    with STATE.lock:
        STATE.working_df, STATE.prepare_report, STATE.trial = cleaned, report, None
        STATE.importance_cache.clear()
    return ok(report)


# ============================================================================ EDA & dashboard
EDA_FILTERS = ["Contract", "InternetService", "PaymentMethod", "SeniorCitizen", "Partner", "Dependents",
               "TechSupport", "OnlineSecurity", "PaperlessBilling", "MultipleLines"]
EDA_TABS = ["Contract", "InternetService", "PaymentMethod", "SeniorCitizen", "TechSupport", "OnlineSecurity",
            "Partner", "Dependents"]
KPI_LABELS = {
    "total_customers": "Total customers", "churned_customers": "Churned", "retained_customers": "Retained",
    "churn_rate_pct": "Churn rate (%)", "avg_tenure": "Avg. tenure (months)",
    "avg_monthly_charges": "Avg. monthly charges", "avg_total_charges": "Avg. total charges",
}


def split(y: pd.Series) -> list:
    n1 = int(y.sum())
    return [{"name": "Retained", "value": len(y) - n1}, {"name": "Churned", "value": n1}]


@private.get("/eda")
def eda(filters: str = "{}", numeric: Optional[str] = None):
    import json
    df = need_data()
    try:
        wanted = json.loads(filters or "{}")
    except ValueError:
        raise HTTPException(422, "filters must be a JSON object such as {\"Contract\": [\"Two year\"]}.")
    options = {c: sorted(df[c].dropna().unique().tolist(), key=str) for c in EDA_FILTERS if c in df.columns}
    f = df
    for col, vals in wanted.items():
        if col in df.columns and vals:
            f = f[f[col].astype(str).isin([str(v) for v in vals])]
    base = {"filter_options": options, "total_rows": len(df), "filtered_rows": len(f)}
    if f.empty:
        return ok({**base, "empty": True})
    y = normalize_target(f, STATE.target_col)
    kpis = compute_kpis(f, STATE.target_col, y)
    numeric_ok = [c for c in STATE.numeric_cols if c in f.columns and f[c].nunique() > 2]
    chosen = numeric if numeric in numeric_ok else (numeric_ok[0] if numeric_ok else None)
    hist = None
    if chosen:
        vals = pd.to_numeric(f[chosen], errors="coerce")
        edges = np.histogram_bin_edges(vals.dropna(), bins=24)
        r, _ = np.histogram(vals[y.values == 0].dropna(), bins=edges)
        c, _ = np.histogram(vals[y.values == 1].dropna(), bins=edges)
        hist = [{"x": round(float((edges[i] + edges[i + 1]) / 2), 2), "lo": float(edges[i]), "hi": float(edges[i + 1]),
                 "retained": int(r[i]), "churned": int(c[i])} for i in range(len(r))]
    corr_cols = [c for c in STATE.numeric_cols if c in f.columns]
    corr = None
    if len(corr_cols) >= 2:
        m = f[corr_cols].apply(pd.to_numeric, errors="coerce").corr()
        corr = {"columns": corr_cols, "matrix": m.values.round(3).tolist()}
    return ok({
        **base, "empty": False,
        "kpis": [{"key": k, "label": KPI_LABELS.get(k, k), "value": v} for k, v in kpis.items()],
        "distribution": split(y),
        "by_category": {c: churn_by_category(f, c, y) for c in EDA_TABS if c in f.columns},
        "by_tenure": churn_by_tenure(f, y) if "tenure" in f.columns else None,
        "numeric_options": numeric_ok, "numeric": chosen, "histogram": hist, "correlation": corr,
    })


@private.get("/dashboard")
def dashboard():
    df = STATE.working_df
    if df is None or STATE.target_col is None:
        return ok({"stage": "no_data", "model": active_model_info()})
    y = normalize_target(df, STATE.target_col)
    kpis = compute_kpis(df, STATE.target_col, y)
    out = {
        "stage": "ready" if STATE.has_model else "no_model", "kpis": kpis, "distribution": split(y),
        "by_contract": churn_by_category(df, "Contract", y) if "Contract" in df.columns else None,
        "by_tenure": churn_by_tenure(df, y) if "tenure" in df.columns else None,
        "model": active_model_info(), "dataset": STATE.dataset_name,
    }
    if STATE.has_model:
        table = risk_table(["Contract", "tenure", "MonthlyCharges"])
        summary = risk_distribution_summary(table.assign(risk_category=pd.Categorical(table["risk_category"], RISK_ORDER)))
        out["risk"] = summary
        out["at_risk"] = table.head(20).to_dict(orient="records")
        try:
            imp = importance_payload(10)
            out["drivers"] = {"basis": imp["basis"], "label": imp["methods"][0]["label"] if imp["methods"] else None,
                              "rows": imp["methods"][0]["rows"] if imp["methods"] else []}
        except HTTPException:
            out["drivers"] = None
    return ok(out)


# ============================================================================ training
class TrainBody(BaseModel):
    test_size: float = 0.2
    imbalance_strategy: str = "class_weight"
    models: list[str] = Field(default_factory=lambda: list(REQUIRED_MODELS))
    selection_metric: str = "f1_score"


@private.post("/models/train")
def train(body: TrainBody):
    df = need_data()
    if not STATE.feature_cols:
        raise HTTPException(409, "No feature columns configured. Review the Data page.")
    if not 0.1 <= body.test_size <= 0.4:
        raise HTTPException(422, "Test size must be between 0.1 and 0.4.")
    if body.imbalance_strategy not in ("class_weight", "smote", "none"):
        raise HTTPException(422, "Imbalance strategy must be class_weight, smote or none.")
    if body.selection_metric not in ("f1_score", "roc_auc", "recall", "precision", "accuracy"):
        raise HTTPException(422, "Unknown selection metric.")
    names = [m for m in body.models if m in MODEL_REGISTRY]
    if not names:
        raise HTTPException(422, "Pick at least one model to train.")
    with STATE.lock:
        y_full = normalize_target(df, STATE.target_col)
        X_train, X_test, y_train, y_test = train_test_split_data(df[STATE.feature_cols], y_full, test_size=body.test_size)
        pre = build_preprocessor(STATE.numeric_cols, STATE.categorical_cols)
        X_train_t = pre.fit_transform(X_train)
        X_test_t = pre.transform(X_test)
        strategy, note = body.imbalance_strategy, None
        if strategy == "smote":
            try:
                import imblearn  # noqa: F401
            except Exception:
                strategy, note = "class_weight", "imbalanced-learn is not installed, so class_weight was used instead of SMOTE."
        models, results = train_selected_models(X_train_t, y_train.values, X_test_t, y_test.values, names,
                                                imbalance_strategy=strategy)
        STATE.trial = {
            "preprocessor": pre, "models": models, "results": results, "X_train_t": X_train_t, "X_test_t": X_test_t,
            "y_test": y_test.values, "feature_names": get_feature_names(pre), "strategy": strategy,
            "numeric_cols": list(STATE.numeric_cols), "categorical_cols": list(STATE.categorical_cols),
            "feature_cols": list(STATE.feature_cols), "target_col": STATE.target_col, "id_col": STATE.id_col,
            "metric": body.selection_metric, "test_size": body.test_size, "dataset_size": len(df),
        }
    return trial_payload(note)


def trial_payload(note: str | None = None) -> dict:
    t = STATE.trial
    if not t:
        raise HTTPException(409, "No models trained in this session yet.")
    table = results_to_table(t["results"])
    rows = [{"model": r["Model"], "accuracy": r["Accuracy"], "precision": r["Precision"], "recall": r["Recall"],
             "f1_score": r["F1-Score"], "roc_auc": r["ROC-AUC"]} for _, r in table.iterrows()]
    return ok({
        "rows": rows, "recommended": select_best_model(t["results"], metric=t["metric"]), "metric": t["metric"],
        "strategy": t["strategy"], "note": note, "test_size": t["test_size"], "active": STATE.model_name,
    })


@private.get("/models/results")
def model_results():
    return trial_payload()


class SaveBody(BaseModel):
    name: str


@private.post("/models/save")
def save_model(body: SaveBody):
    t = STATE.trial
    if not t or body.name not in t["models"]:
        raise HTTPException(409, "Train that model first, then save it.")
    with STATE.lock:
        model, name = t["models"][body.name], body.name
        metadata = {
            "model_name": name, "target_col": t["target_col"], "id_col": t["id_col"],
            "numeric_cols": t["numeric_cols"], "categorical_cols": t["categorical_cols"],
            "feature_cols": t["feature_cols"], "feature_names": t["feature_names"],
            "metrics": {k: float(v) for k, v in t["results"][name].items()
                        if k in ("accuracy", "precision", "recall", "f1_score", "roc_auc")},
            "training_dataset_size": t["dataset_size"], "imbalance_strategy": t["strategy"],
        }
        saved = save_artifacts(model, t["preprocessor"], metadata)
        STATE.model, STATE.preprocessor, STATE.model_name, STATE.metadata = model, t["preprocessor"], name, saved
        STATE.X_test_t, STATE.y_test = t["X_test_t"], t["y_test"]
        STATE.explainer = get_shap_explainer(model, t["X_train_t"], name)
        STATE.importance_cache.clear()
    threading.Thread(target=_warm_importance, daemon=True).start()
    return ok({"model": active_model_info()})


def _warm_importance():
    """Pre-compute global importance right after saving so the first dashboard load is instant."""
    try:
        importance_payload(15)
    except Exception:
        pass


@private.get("/evaluation")
def evaluation():
    t = STATE.trial
    if not t:
        raise HTTPException(409, "No trained models in this session yet. Train models on the Training page.")
    models = []
    for name, m in t["results"].items():
        fpr, tpr = downsample(*m["roc_curve"])
        prec, rec = m["pr_curve"]
        rec_d, prec_d = downsample(rec, prec)
        models.append({
            "name": name, "active": name == STATE.model_name,
            "metrics": {k: m[k] for k in ("accuracy", "precision", "recall", "f1_score", "roc_auc")},
            "confusion": np.asarray(m["confusion_matrix"]).tolist(),
            "roc": [{"x": a, "y": b} for a, b in zip(fpr, tpr)],
            "pr": [{"x": a, "y": b} for a, b in zip(rec_d, prec_d)],
        })
    return ok({"models": models, "active": STATE.model_name})


# ============================================================================ risk
class ThresholdBody(BaseModel):
    low: int
    medium: int
    high: int


@private.get("/risk/thresholds")
def get_thresholds():
    return ok(STATE.risk_thresholds)


@private.put("/risk/thresholds")
def put_thresholds(body: ThresholdBody):
    if not (5 <= body.low <= 50):
        raise HTTPException(422, "The Low / Medium boundary must be between 5% and 50%.")
    if not (body.low + 5 <= body.medium <= 85):
        raise HTTPException(422, "The Medium / High boundary must be at least 5 points above Low and at most 85%.")
    if not (body.medium + 5 <= body.high <= 95):
        raise HTTPException(422, "The High / Critical boundary must be at least 5 points above Medium and at most 95%.")
    STATE.risk_thresholds = {"low": body.low, "medium": body.medium, "high": body.high}
    return ok(STATE.risk_thresholds)


@private.get("/risk")
def risk_view(risk: str = "", search: str = "", limit: int = 2000):
    table = risk_table(["Contract", "tenure", "MonthlyCharges", "InternetService", "PaymentMethod"])
    summary = risk_distribution_summary(table.assign(risk_category=pd.Categorical(table["risk_category"], RISK_ORDER)))
    view = table
    wanted = [r for r in risk.split(",") if r in RISK_ORDER]
    if wanted:
        view = view[view["risk_category"].isin(wanted)]
    if search:
        view = view[view["customerID"].astype(str).str.contains(search, case=False, na=False, regex=False)]
    return ok({
        "summary": summary, "thresholds": STATE.risk_thresholds, "total": len(table), "matched": len(view),
        "rows": view.head(max(1, min(limit, 20000))).to_dict(orient="records"),
    })


# ============================================================================ customers
@private.get("/customers")
def customers(search: str = "", limit: int = 100):
    table = risk_table()
    if search:
        table = table[table["customerID"].astype(str).str.contains(search, case=False, na=False, regex=False)]
    rows = table.head(max(1, min(limit, 500)))
    return ok({"matched": len(table), "has_id": bool(STATE.id_col and STATE.id_col in STATE.working_df.columns),
               "rows": [{"id": str(r.customerID), "probability": r.churn_probability, "risk": r.risk_category}
                        for r in rows.itertuples()]})


PROFILE_GROUPS = {
    "Customer information": ["gender", "SeniorCitizen", "Partner", "Dependents"],
    "Service information": ["PhoneService", "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
                            "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"],
    "Billing information": ["Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges"],
}


@private.get("/customers/{cid}")
def customer(cid: str):
    df = need_model()
    label, row = find_row(cid)
    proba, drivers, protective, method = explain_row(row)
    risk_band = assign_risk_category(proba, STATE.risk_thresholds)
    groups = []
    for name, cols in PROFILE_GROUPS.items():
        items = [{"label": c, "value": row[c]} for c in cols if c in df.columns]
        if items:
            groups.append({"name": name, "items": items})
    recs = generate_recommendations(row, proba, risk_band)
    return ok({
        "id": label, "probability": proba, "risk": risk_band,
        "tenure": row["tenure"] if "tenure" in df.columns else None,
        "actual_churn": None if STATE.target_col not in df.columns else bool(normalize_target(df.loc[[row.name]], STATE.target_col).iloc[0]),
        "groups": groups, "drivers": drivers, "protective": protective, "method": method,
        "recommendations": [{"reason": r, "suggestion": s} for r, s in recs],
    })


@private.get("/xai/global")
def xai_global():
    return ok(importance_payload(15))


@private.get("/xai/local/{cid}")
def xai_local(cid: str):
    need_model()
    label, row = find_row(cid)
    proba, drivers, protective, method = explain_row(row)
    return ok({"id": label, "probability": proba, "risk": assign_risk_category(proba, STATE.risk_thresholds),
               "drivers": drivers, "protective": protective, "method": method, "shap_available": SHAP_AVAILABLE})


# ============================================================================ what-if
@private.get("/whatif/schema")
def whatif_schema(customer_id: Optional[str] = None):
    df = need_model()
    num, cat = [c for c in STATE.model_features if c in (STATE.metadata or {}).get("numeric_cols", [])], \
               [c for c in STATE.model_features if c in (STATE.metadata or {}).get("categorical_cols", [])]
    fields = []
    for c in num + cat:
        if c in num:
            s = pd.to_numeric(df[c], errors="coerce").dropna()
            lo, hi = float(s.min()), float(s.max())
            if lo == hi:
                hi = lo + 1
            step = 1.0 if df[c].dtype.kind in "iu" else (round((hi - lo) / 100, 2) or 0.1)
            fields.append({"name": c, "type": "numeric", "min": lo, "max": hi, "step": step})
        else:
            fields.append({"name": c, "type": "categorical", "options": sorted(df[c].dropna().unique().astype(str).tolist())})
    out = {"fields": fields}
    if customer_id is not None:
        label, row = find_row(customer_id)
        out["customer"] = label
        out["current"] = {f["name"]: row[f["name"]] for f in fields}
    return ok(out)


class WhatIfBody(BaseModel):
    customer_id: str
    changes: dict = Field(default_factory=dict)


@private.post("/whatif")
def whatif(body: WhatIfBody):
    need_model()
    label, row = find_row(body.customer_id)
    feats = STATE.model_features
    original = float(score_customers(pd.DataFrame([row[feats]]), STATE.preprocessor, STATE.model)[0])
    scenario_row = row.copy()
    for feat, val in body.changes.items():
        if feat not in feats:
            raise HTTPException(422, f"“{feat}” is not a feature of the active model.")
        scenario_row[feat] = val
    try:
        scenario = float(score_customers(pd.DataFrame([scenario_row[feats]]), STATE.preprocessor, STATE.model)[0])
    except Exception as e:
        raise HTTPException(422, f"The model could not score that scenario: {e}")
    diff = scenario - original
    return ok({
        "id": label, "original": original, "scenario": scenario, "change": round(diff, 2),
        "original_risk": assign_risk_category(original, STATE.risk_thresholds),
        "scenario_risk": assign_risk_category(scenario, STATE.risk_thresholds),
        "verdict": "none" if abs(diff) < 0.5 else ("lower" if diff < 0 else "higher"),
    })


# ============================================================================ retention
@private.get("/retention")
def retention(risk: str = "High Risk,Critical Risk", limit: int = 50):
    limit = max(5, min(limit, 500))
    table = risk_table(["Contract", "tenure", "MonthlyCharges", "InternetService", "PaymentMethod", "TechSupport"])
    wanted = [r for r in risk.split(",") if r in RISK_ORDER]
    subset = table[table["risk_category"].isin(wanted)].head(limit)
    if subset.empty:
        return ok({"customers": 0, "suggestions": 0, "rows": [], "available": len(table)})
    subset = subset.assign(risk_category=pd.Categorical(subset["risk_category"], RISK_ORDER))
    rec = recommendations_dataframe(subset, STATE.working_df, STATE.id_col)
    rec["risk_category"] = rec["risk_category"].astype(str)
    return ok({"customers": int(subset["customerID"].nunique()), "suggestions": len(rec),
               "rows": rec.to_dict(orient="records"), "available": len(table)})


# ============================================================================ batch
@private.get("/batch/template")
def batch_template():
    df = need_model()
    cols = ([STATE.id_col] if STATE.id_col and STATE.id_col in df.columns else []) + STATE.model_features
    csv = df[cols].head(25).to_csv(index=False)
    return Response(csv, media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="sample_batch.csv"'})


@private.post("/batch/predict")
def batch_predict(file: UploadFile = File(...), include_drivers: bool = Form(True)):
    need_model()
    new_df = read_upload(file)
    problems = validate_columns_for_prediction(new_df, STATE.model_features)
    if problems:
        raise HTTPException(422, " ".join(problems))
    missing_values = int(new_df[STATE.model_features].isna().sum().sum())
    lookup = None
    if include_drivers:
        def lookup(row):
            _, pos, _, _ = explain_row(row)
            return [p["label"] for p in pos[:3]]
    try:
        res = build_batch_predictions(new_df, STATE.model_features, STATE.preprocessor, STATE.model,
                                      STATE.id_col if STATE.id_col in new_df.columns else None,
                                      STATE.risk_thresholds, top_driver_lookup=lookup)
    except Exception as e:
        raise HTTPException(422, f"Prediction failed: {e}")
    counts = res["risk_category"].value_counts().reindex(RISK_ORDER, fill_value=0).to_dict()
    return ok({
        "filename": file.filename, "total": len(res), "missing_values": missing_values, "counts": counts,
        "avg_probability": round(float(res["churn_probability"].mean()), 2),
        "predicted_churn": int((res["predicted_churn"] == "Yes").sum()), "drivers_included": include_drivers,
        "rows": res.to_dict(orient="records"),
    })


# ============================================================================ monitoring
@private.get("/monitoring")
def monitoring():
    STATE.restore_from_disk()
    info = active_model_info()
    if not info:
        raise HTTPException(409, "No active saved model. Train and save a model on the Training page.")
    meta = STATE.metadata or {}
    return ok({**info, "feature_count": len(meta.get("feature_names") or []), "target_col": meta.get("target_col"),
               "has_reference": STATE.working_df is not None})


@private.post("/monitoring/drift")
def drift(file: UploadFile = File(...)):
    meta = STATE.metadata
    if not meta:
        raise HTTPException(409, "No active saved model. Train and save a model first.")
    new_df = read_upload(file)
    expected = meta.get("feature_cols", [])
    missing_cols = [c for c in expected if c not in new_df.columns]
    present = [c for c in expected if c in new_df.columns]
    numeric = [c for c in meta.get("numeric_cols", []) if c in present]
    categorical = [c for c in meta.get("categorical_cols", []) if c in present]
    missing_pct = float(new_df[present].isna().mean().mean() * 100) if present else 0.0
    ref = STATE.working_df
    unexpected, means = [], []
    if ref is not None:
        for c in categorical:
            if c in ref.columns:
                new_vals = set(new_df[c].dropna().unique()) - set(ref[c].dropna().unique())
                if new_vals:
                    unexpected.append({"column": c, "values": sorted(map(str, new_vals))})
        for c in numeric:
            if c in ref.columns:
                means.append({"feature": c,
                              "training_mean": round(float(pd.to_numeric(ref[c], errors="coerce").mean()), 2),
                              "new_mean": round(float(pd.to_numeric(new_df[c], errors="coerce").mean()), 2)})
    churn_rate, imbalance = None, False
    target = meta.get("target_col")
    if target and target in new_df.columns:
        y_new = normalize_target(new_df, target)
        churn_rate = round(float(y_new.mean() * 100), 1)
        imbalance = bool(y_new.value_counts().min() < 5)
    return ok({
        "filename": file.filename, "rows": len(new_df), "missing_columns": missing_cols,
        "missing_pct": round(missing_pct, 1), "high_missing": missing_pct > 10, "has_reference": ref is not None,
        "unexpected_categories": unexpected, "mean_comparison": means, "new_churn_rate": churn_rate,
        "imbalance_warning": imbalance,
    })


app.include_router(public)
app.include_router(private)
