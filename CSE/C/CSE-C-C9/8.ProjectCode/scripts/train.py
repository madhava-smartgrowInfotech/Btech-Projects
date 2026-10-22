"""FinSight AI — reproducible training pipeline.

Steps: load dataset -> validate schema -> clean -> engineer features ->
stratified split -> train 4 candidate models -> 5-fold stratified CV ->
evaluate -> select best by ROC-AUC -> SHAP artifacts -> plots ->
persist model + preprocessor -> metrics + validation + stats reports.

Dataset: UCI Adult / Census Income.
"""
import io
import json
import urllib.request
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from feature_engineering import (
    COLUMN_NAMES, TARGET_COL, POSITIVE_LABEL, RANDOM_STATE,
    clean_frame, add_derived_features, build_preprocessor,
    get_output_feature_names, human_label,
)
from models import get_candidate_models
from forecast import build_index_series, fit_forecast

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
ARTIFACTS_DIR = ROOT / "artifacts"

ADULT_TRAIN_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
ADULT_TEST_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.test"

SYNTHETIC_FALLBACK_ROWS = 8000


def download_adult() -> pd.DataFrame:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    train_path = DATA_RAW / "adult.data"
    test_path = DATA_RAW / "adult.test"
    for url, path in [(ADULT_TRAIN_URL, train_path), (ADULT_TEST_URL, test_path)]:
        if not path.exists() or path.stat().st_size < 1000:
            print(f"Downloading {url} ...")
            req = urllib.request.Request(url, headers={"User-Agent": "FinSightAI/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                path.write_bytes(r.read())
            print(f"Saved {path} ({path.stat().st_size} bytes)")
    train = pd.read_csv(train_path, header=None, names=COLUMN_NAMES, skipinitialspace=True)
    test = pd.read_csv(test_path, header=None, names=COLUMN_NAMES, skipinitialspace=True,
                       skiprows=1)
    df = pd.concat([train, test], ignore_index=True)
    return df


def synthetic_fallback() -> pd.DataFrame:
    """Realistic synthetic data with the documented Adult-compatible schema.

    Used only when the public dataset cannot be downloaded. Labelled
    synthetic in data/README.md and training_summary.json.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n = SYNTHETIC_FALLBACK_ROWS
    workclasses = ["Private", "Self-emp-not-inc", "Local-gov", "State-gov", "Federal-gov"]
    educations = ["HS-grad", "Some-college", "Bachelors", "Masters", "Doctorate",
                  "Assoc-voc", "11th", "9th"]
    edu_num_map = {"9th": 7, "11th": 9, "HS-grad": 9, "Assoc-voc": 11,
                   "Some-college": 10, "Bachelors": 13, "Masters": 14, "Doctorate": 16}
    maritals = ["Married-civ-spouse", "Never-married", "Divorced", "Separated", "Widowed"]
    occs = ["Tech-support", "Craft-repair", "Other-service", "Sales", "Exec-managerial",
            "Prof-specialty", "Handlers-cleaners", "Machine-op-inspct", "Adm-clerical"]
    rels = ["Wife", "Own-child", "Husband", "Not-in-family", "Other-relative", "Unmarried"]
    edu = rng.choice(educations, n)
    age = rng.integers(17, 90, n)
    hours = rng.integers(1, 80, n)
    gain = np.where(rng.random(n) < 0.12, rng.integers(1000, 40000, n), 0)
    loss = np.where(rng.random(n) < 0.08, rng.integers(500, 5000, n), 0)
    edu_num = np.array([edu_num_map[e] for e in edu])
    score = (0.05 * age + 0.35 * edu_num + 0.02 * hours
             + 0.00008 * gain - 0.0002 * loss + rng.normal(0, 2.2, n))
    income = np.where(score > np.quantile(score, 0.76), ">50K", "<=50K")
    return pd.DataFrame({
        "age": age, "workclass": rng.choice(workclasses, n),
        "fnlwgt": rng.integers(50000, 400000, n), "education": edu,
        "education-num": edu_num, "marital-status": rng.choice(maritals, n),
        "occupation": rng.choice(occs, n), "relationship": rng.choice(rels, n),
        "race": rng.choice(["White", "Black", "Asian-Pac-Islander", "Other"], n, p=[.7, .12, .08, .1]),
        "sex": rng.choice(["Male", "Female"], n, p=[.6, .4]),
        "capital-gain": gain, "capital-loss": loss, "hours-per-week": hours,
        "native-country": rng.choice(["United-States", "Mexico", "India", "Philippines", "Germany"], n, p=[.85, .05, .04, .03, .03]),
        "income": income,
    })


def evaluate_binary(y_true, y_pred, y_proba):
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_proba)), 4),
    }


def save_confusion_matrix(y_true, y_pred, path):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_title("Confusion Matrix — FinSight AI")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["≤50K", ">50K"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["≤50K", ">50K"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def save_roc_curves(curves: dict, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, (fpr, tpr, auc) in curves.items():
        ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", label="Chance")
    ax.set_title("ROC Curves — model comparison")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    data_source = "UCI Adult / Census Income (public)"
    source_url = "https://archive.ics.uci.edu/dataset/20/census+income"
    try:
        df_raw = download_adult()
        if len(df_raw) < 1000:
            raise ValueError("Downloaded dataset unexpectedly small")
    except Exception as e:
        print(f"Public dataset download failed ({e}); using synthetic fallback.")
        df_raw = synthetic_fallback()
        data_source = "Synthetic fallback (Adult-compatible schema; labelled synthetic)"
        source_url = "synthetic (see data/README.md)"

    # Schema validation
    missing = [c for c in COLUMN_NAMES if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Invalid dataset schema, missing columns: {missing}")
    if df_raw.empty:
        raise ValueError("Dataset is empty")

    df = clean_frame(df_raw)
    df = df.dropna(subset=[TARGET_COL])
    df = add_derived_features(df)
    y = (df[TARGET_COL] == POSITIVE_LABEL).astype(int)
    X = df.drop(columns=[TARGET_COL])

    (DATA_PROCESSED / "features_preview.csv").write_text(
        pd.concat([X.head(200), y.head(200).rename("target")], axis=1).to_csv(index=False))

    # Cross-sectional: one row per person -> stratified split + stratified K-fold.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    candidates = get_candidate_models()
    results = {}
    roc_curves = {}
    cv_summary = {}
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    for name, clf in candidates.items():
        scale = (name == "logistic_regression")
        pipe = Pipeline([
            ("preprocess", build_preprocessor(scale_numeric=scale)),
            ("model", clf),
        ])
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=skf, scoring="roc_auc", n_jobs=-1)
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)
        m = evaluate_binary(y_test, pred, proba)
        m["cv_roc_auc_mean"] = round(float(cv_scores.mean()), 4)
        m["cv_roc_auc_std"] = round(float(cv_scores.std()), 4)
        results[name] = m
        fpr, tpr, _ = roc_curve(y_test, proba)
        roc_curves[name] = (fpr, tpr, m["roc_auc"])
        cv_summary[name] = [round(float(s), 4) for s in cv_scores]
        joblib.dump(pipe, MODELS_DIR / f"{name}.pkl")
        print(f"{name}: {m}")

    best_name = max(results, key=lambda k: results[k]["roc_auc"])
    print(f"Best model: {best_name}")

    best_pipe = joblib.load(MODELS_DIR / f"{best_name}.pkl")
    proba_best = best_pipe.predict_proba(X_test)[:, 1]
    pred_best = (proba_best >= 0.5).astype(int)
    save_confusion_matrix(y_test, pred_best, ARTIFACTS_DIR / "confusion_matrix.png")
    save_roc_curves(roc_curves, ARTIFACTS_DIR / "roc_curve.png")

    joblib.dump(best_pipe, MODELS_DIR / "best_model.pkl")
    (MODELS_DIR / "best_model_name.txt").write_text(best_name)

    # ---- SHAP global artifacts (TreeExplainer for tree models) ----
    shap_payload = {"model": best_name, "features": [], "note": ""}
    try:
        import shap
        preprocess = best_pipe.named_steps["preprocess"]
        Xt_train = preprocess.transform(X_train)
        feat_names = get_output_feature_names(preprocess)
        rng = np.random.default_rng(RANDOM_STATE)
        idx = rng.choice(len(Xt_train), size=min(2000, len(Xt_train)), replace=False)
        sample = Xt_train[idx]
        # subsample for SHAP computation speed
        bg = sample[: min(200, len(sample))]
        model_step = best_pipe.named_steps["model"]
        is_tree = type(model_step).__name__ in (
            "XGBClassifier", "RandomForestClassifier", "GradientBoostingClassifier")
        if is_tree:
            explainer = shap.TreeExplainer(model_step, feature_perturbation="tree_path_dependent")
            sv = explainer.shap_values(sample[:500])
            if isinstance(sv, list):
                sv = sv[1] if len(sv) == 2 else sv[0]
            sv = np.asarray(sv)
        else:
            explainer = shap.LinearExplainer(model_step, bg)
            sv = np.asarray(explainer.shap_values(sample[:500]))
        mean_abs = np.abs(sv).mean(axis=0)
        order = np.argsort(mean_abs)[::-1][:15]
        shap_payload["features"] = [
            {"feature": feat_names[i] if i < len(feat_names) else f"f{i}",
             "label": human_label(feat_names[i] if i < len(feat_names) else f"f{i}"),
             "mean_abs_shap": round(float(mean_abs[i]), 5)}
            for i in order
        ]
        # Bar chart
        top = shap_payload["features"][::-1]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh([f["label"] for f in top], [f["mean_abs_shap"] for f in top])
        ax.set_title(f"Global feature importance (mean |SHAP|) — {best_name}")
        ax.set_xlabel("Mean |SHAP value|")
        fig.tight_layout()
        fig.savefig(ARTIFACTS_DIR / "shap_bar.png", dpi=120)
        plt.close(fig)
        # Beeswarm / summary
        try:
            shap.summary_plot(sv, sample[:500], feature_names=feat_names,
                              show=False, max_display=15)
            import matplotlib.pyplot as _plt
            fig = _plt.gcf()
            fig.tight_layout()
            fig.savefig(ARTIFACTS_DIR / "shap_beeswarm.png", dpi=120, bbox_inches="tight")
            _plt.close("all")
        except Exception as e:
            shap_payload["note"] = f"beeswarm skipped: {e}"
        # background sample for live local explanations
        np.save(MODELS_DIR / "shap_background.npy", bg)
        joblib.dump(feat_names, MODELS_DIR / "feature_names.pkl")
    except Exception as e:
        shap_payload["note"] = f"SHAP generation failed: {e}"
        print(shap_payload["note"])

    (ARTIFACTS_DIR / "shap_global.json").write_text(json.dumps(shap_payload, indent=2))

    # ---- Forecasting artifacts ----
    index_df = build_index_series()
    forecast_payload = fit_forecast(index_df)
    (ARTIFACTS_DIR / "forecast.json").write_text(json.dumps(forecast_payload, indent=2))

    # ---- Metrics / comparison / validation / stats ----
    comparison = {
        "models": results,
        "best_model": best_name,
        "primary_metric": "roc_auc",
        "target": f"income {POSITIVE_LABEL} vs <=50K (adapted as financial-profile signal)",
    }
    (ARTIFACTS_DIR / "model_comparison.json").write_text(json.dumps(comparison, indent=2))
    (ARTIFACTS_DIR / "metrics.json").write_text(json.dumps({
        "best_model": best_name, **results[best_name]}, indent=2))

    validation_report = {
        "protocol": "Stratified 80/20 train-test split + 5-fold stratified cross-validation "
                    "(n_splits=5, random_state=42).",
        "why": "The dataset is cross-sectional with one row per person; no repeated "
               "individuals exist, so entity-aware GroupKFold is unnecessary and "
               "stratified KFold preserves class ratios. Preprocessing is inside each "
               "pipeline to prevent leakage. Temporal validation is not applicable "
               "because the classification data has no genuine time dimension; "
               "forecasting is validated separately on its own time series.",
        "cv_roc_auc": cv_summary,
        "test_size": len(y_test),
        "train_size": len(y_train),
        "class_balance_test": {
            "<=50K": int((y_test == 0).sum()), ">50K": int((y_test == 1).sum())},
    }
    (ARTIFACTS_DIR / "validation_report.json").write_text(json.dumps(validation_report, indent=2))

    # Lightweight statistical validation (no fake panel regression).
    try:
        import statsmodels.api as sm
        num_cols = ["age", "education-num", "hours-per-week", "net-capital"]
        stats_df = pd.DataFrame({c: pd.to_numeric(X_train[c], errors="coerce") for c in num_cols})
        stats_df = stats_df.fillna(stats_df.median())
        corr = stats_df.join(y_train.rename("target")).corr(numeric_only=True)["target"].drop("target")
        Xc = sm.add_constant(stats_df)
        logit = sm.Logit(y_train.values, Xc.values).fit(disp=0)
        stats_report = {
            "correlations_with_target": {k: round(float(v), 4) for k, v in corr.items()},
            "logit_coefficients": {k: round(float(v), 5) for k, v in
                                   zip(["const"] + num_cols, logit.params)},
            "logit_pvalues": {k: round(float(v), 5) for k, v in
                              zip(["const"] + num_cols, logit.pvalues)},
            "note": "Complementary associational evidence only; not proof of causation.",
        }
    except Exception as e:
        stats_report = {"note": f"statistical analysis unavailable: {e}"}
    (ARTIFACTS_DIR / "stats_report.json").write_text(json.dumps(stats_report, indent=2))

    summary = {
        "product": "FinSight AI",
        "dataset": data_source,
        "source_url": source_url,
        "rows": int(len(df)),
        "features_used": sorted(set(list(X.columns))),
        "target": "income (>50K vs <=50K) adapted as financial-profile signal",
        "best_model": best_name,
        "metrics": results[best_name],
        "all_metrics": results,
        "random_state": RANDOM_STATE,
    }
    (ARTIFACTS_DIR / "training_summary.json").write_text(json.dumps(summary, indent=2))
    print("Training complete. Best:", best_name, results[best_name])


if __name__ == "__main__":
    main()
