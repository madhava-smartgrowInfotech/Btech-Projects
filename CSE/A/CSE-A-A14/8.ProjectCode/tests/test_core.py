"""Unit tests for the src/ core (the part both the Streamlit and React interfaces share).

    .venv\\Scripts\\python -m pytest tests -q
"""
import numpy as np
import pandas as pd
import pytest

from data_loader import (
    coerce_numeric_looking_columns, detect_id_column, detect_target_column, normalize_target,
    profile_dataset, validate_dataset_for_training,
)
from explainability import clean_feature_label, local_explanation
from persistence import load_artifacts, save_artifacts
from prediction import build_batch_predictions, score_customers, validate_columns_for_prediction
from preprocessing import (
    apply_smote, build_preprocessor, class_distribution, clean_missing_and_duplicates, get_feature_names,
    train_test_split_data,
)
from retention_engine import generate_recommendations
from risk_segmentation import build_risk_table, risk_distribution_summary
from sample_data import generate_sample_churn_data
from train_models import MODEL_REGISTRY, REQUIRED_MODELS, select_best_model, train_selected_models
from utils import assign_risk_category, make_tenure_group

NUM = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges"]
BANDS = {"low": 30, "medium": 60, "high": 80}


@pytest.fixture(scope="module")
def df():
    return generate_sample_churn_data()


@pytest.fixture(scope="module")
def fitted(df):
    cat = [c for c in df.columns if c not in NUM + ["customerID", "Churn"]]
    feats = NUM + cat
    y = normalize_target(df, "Churn")
    X_tr, X_te, y_tr, y_te = train_test_split_data(df[feats], y)
    pre = build_preprocessor(NUM, cat)
    A, B = pre.fit_transform(X_tr), pre.transform(X_te)
    models, results = train_selected_models(A, y_tr.values, B, y_te.values, REQUIRED_MODELS, "class_weight")
    return dict(feats=feats, cat=cat, pre=pre, A=A, B=B, y_tr=y_tr, y_te=y_te, models=models, results=results)


# ------------------------------------------------------------------ sample data
def test_sample_shape_and_schema(df):
    assert df.shape == (1000, 21)
    assert df["customerID"].is_unique and not df.isna().any().any()


def test_sample_is_reproducible_and_churn_rate_sane(df):
    assert generate_sample_churn_data().equals(df)
    assert 0.2 < (df["Churn"] == "Yes").mean() < 0.33


# ------------------------------------------------------------------ data loading
def test_detects_target_and_id(df):
    assert detect_target_column(df) == "Churn"
    assert detect_id_column(df) == "customerID"


# Regression tests for the pandas >= 3 string dtype (data_loader once tested `dtype == object`).
@pytest.mark.parametrize("values", [
    ["Yes", "No", "Yes"], [1, 0, 1], [True, False, True],
    ["Churned", "Retained", "Churned"],
])
def test_normalize_target_variants(values):
    out = normalize_target(pd.DataFrame({"Churn": values}), "Churn")
    assert out.tolist() == [1, 0, 1]


def test_totalcharges_blank_strings_are_coerced():
    d = pd.DataFrame({"TotalCharges": ["10.5", " ", "30", "40", "50", "60", "70", "80", "90", "100"]})
    out = coerce_numeric_looking_columns(d)
    assert pd.api.types.is_numeric_dtype(out["TotalCharges"]) and out["TotalCharges"].isna().sum() == 1


def test_profile_flags_duplicates_and_missing(df):
    d = pd.concat([df, df.iloc[[0]]]).copy()
    d.iloc[1, d.columns.get_loc("tenure")] = np.nan
    p = profile_dataset(d)
    assert p.n_duplicates == 1 and any("missing" in w for w in p.warnings)


def test_validation_messages(df):
    assert validate_dataset_for_training(df, "Churn") == []
    assert validate_dataset_for_training(df.iloc[0:0], "Churn")
    assert "not found" in validate_dataset_for_training(df, "Nope")[0]
    assert validate_dataset_for_training(df.head(10), "Churn")
    one = df.copy()
    one["Churn"] = "No"
    assert "only one class" in validate_dataset_for_training(one, "Churn")[0]


# ------------------------------------------------------------------ preprocessing
def test_duplicates_removed(df):
    out, rep = clean_missing_and_duplicates(pd.concat([df, df.head(5)]))
    assert rep["duplicates_removed"] == 5 and len(out) == 1000


def test_encoded_width_and_names(fitted):
    assert fitted["A"].shape[1] == 45 == len(get_feature_names(fitted["pre"]))


def test_split_is_stratified_80_20(df):
    y = normalize_target(df, "Churn")
    X_tr, X_te, y_tr, y_te = train_test_split_data(df, y)
    assert (len(X_tr), len(X_te)) == (800, 200)
    assert abs(y_tr.mean() - y_te.mean()) < 0.01


def test_unseen_category_is_ignored_not_fatal(fitted, df):
    row = df[fitted["feats"]].head(1).copy()
    row["Contract"] = "Brand new plan"
    assert fitted["pre"].transform(row).shape == (1, 45)


def test_smote_balances_the_training_split(fitted):
    X, y = apply_smote(fitted["A"], fitted["y_tr"].values)
    assert abs(int(y.sum()) - (len(y) - int(y.sum()))) <= 1 and len(y) > len(fitted["y_tr"])


def test_class_distribution(df):
    d = class_distribution(normalize_target(df, "Churn"))
    assert d["counts"][0] + d["counts"][1] == 1000 and d["imbalance_ratio"] > 1


# ------------------------------------------------------------------ training and evaluation
def test_registry_has_required_models():
    assert set(REQUIRED_MODELS) <= set(MODEL_REGISTRY)


def test_three_models_trained_with_valid_metrics(fitted):
    assert set(fitted["results"]) == set(REQUIRED_MODELS)
    for r in fitted["results"].values():
        for k in ("accuracy", "precision", "recall", "f1_score", "roc_auc"):
            assert 0.0 <= r[k] <= 1.0


def test_confusion_matrix_sums_to_test_size(fitted):
    for r in fitted["results"].values():
        assert np.asarray(r["confusion_matrix"]).sum() == 200


def test_best_model_follows_requested_metric(fitted):
    res = fitted["results"]
    assert select_best_model(res, "roc_auc") == max(res, key=lambda k: res[k]["roc_auc"])
    assert select_best_model({}, "f1_score") is None


def test_class_weights_raise_recall_over_no_handling(fitted):
    _, none = train_selected_models(fitted["A"], fitted["y_tr"].values, fitted["B"], fitted["y_te"].values,
                                    ["Logistic Regression"], "none")
    assert fitted["results"]["Logistic Regression"]["recall"] > none["Logistic Regression"]["recall"]


# ------------------------------------------------------------------ scoring, risk, batch
def test_scores_are_percentages(fitted, df):
    p = score_customers(df[fitted["feats"]], fitted["pre"], fitted["models"]["Logistic Regression"])
    assert len(p) == 1000 and p.min() >= 0 and p.max() <= 100


@pytest.mark.parametrize("p,band", [(0, "Low Risk"), (29.99, "Low Risk"), (30, "Medium Risk"), (59.9, "Medium Risk"),
                                    (60, "High Risk"), (79.9, "High Risk"), (80, "Critical Risk"), (100, "Critical Risk")])
def test_default_risk_band_boundaries(p, band):
    assert assign_risk_category(p) == band


def test_custom_thresholds_move_the_bands():
    assert assign_risk_category(50, {"low": 20, "medium": 40, "high": 60}) == "High Risk"


def test_tenure_groups():
    g = make_tenure_group(pd.Series([0, 12, 13, 24, 25, 48, 49, 72])).astype(str).tolist()
    assert g == ["0-12 months", "0-12 months", "13-24 months", "13-24 months",
                 "25-48 months", "25-48 months", "49+ months", "49+ months"]


def test_risk_table_sorted_and_summary_adds_up(fitted, df):
    t = build_risk_table(df, fitted["feats"], fitted["pre"], fitted["models"]["Random Forest"], "customerID", BANDS)
    assert t["churn_probability"].is_monotonic_decreasing
    s = risk_distribution_summary(t)
    assert sum(s["counts"].values()) == s["total"] == 1000


def test_batch_prediction_columns_and_threshold(fitted, df):
    out = build_batch_predictions(df.head(40), fitted["feats"], fitted["pre"], fitted["models"]["Logistic Regression"],
                                  "customerID", BANDS)
    assert {"customerID", "churn_probability", "predicted_churn", "risk_category", "top_risk_factor_1"} <= set(out.columns)
    assert ((out["churn_probability"] >= 50) == (out["predicted_churn"] == "Yes")).all()


def test_batch_validation_names_missing_columns(df):
    problems = validate_columns_for_prediction(df.drop(columns=["Contract"]), ["Contract", "tenure"])
    assert problems and "Contract" in problems[0]


# ------------------------------------------------------------------ retention rules
def _row(**kw):
    base = dict(Contract="Two year", TechSupport="Yes", OnlineSecurity="Yes", PaymentMethod="Credit card (automatic)",
                MonthlyCharges=40.0, tenure=30, InternetService="DSL", StreamingTV="Yes", StreamingMovies="Yes",
                PaperlessBilling="No")
    base.update(kw)
    return pd.Series(base)


def test_month_to_month_high_risk_gets_contract_offer():
    recs = generate_recommendations(_row(Contract="Month-to-month"), 72, "High Risk")
    assert any("longer-term contract" in s for _, s in recs)


def test_new_customer_and_critical_rules_fire():
    recs = generate_recommendations(_row(tenure=3), 90, "Critical Risk")
    reasons = " ".join(r for r, _ in recs)
    assert "tenure <= 6" in reasons and "Critical band" in reasons


def test_low_risk_gets_no_urgent_action_and_never_empty():
    recs = generate_recommendations(_row(), 10, "Low Risk")
    assert len(recs) == 1 and "No urgent retention action" in recs[0][1]
    assert generate_recommendations(_row(), 45, "Medium Risk")


def test_rules_do_not_fire_below_high_risk_threshold():
    recs = generate_recommendations(_row(Contract="Month-to-month", TechSupport="No"), 40, "Medium Risk")
    assert all("longer-term" not in s for _, s in recs)


# ------------------------------------------------------------------ explainability and persistence
def test_local_explanation_fallback_without_shap(fitted):
    pos, neg, method = local_explanation(None, fitted["models"]["Logistic Regression"], fitted["B"][0],
                                         get_feature_names(fitted["pre"]), top_n=5)
    assert method == "approximate" and len(pos) <= 5 and all(v > 0 for _, v in pos) and all(v < 0 for _, v in neg)


def test_feature_label_cleanup():
    assert clean_feature_label("cat__Contract_Month-to-month") == "Contract: Month-to-month"
    assert clean_feature_label("num__tenure") == "tenure"


def test_save_and_load_artifacts_roundtrip(tmp_path, monkeypatch, fitted):
    import persistence
    monkeypatch.setattr(persistence, "MODELS_DIR", str(tmp_path))
    meta = save_artifacts(fitted["models"]["Logistic Regression"], fitted["pre"], {"model_name": "Logistic Regression"})
    model, pre, loaded = load_artifacts()
    assert loaded["model_name"] == "Logistic Regression" and "saved_at" in meta
    assert np.allclose(model.predict_proba(fitted["B"]), fitted["models"]["Logistic Regression"].predict_proba(fitted["B"]))


# ------------------------------------------------------------------ demo auth (backend)
def test_token_roundtrip_tamper_and_expiry(monkeypatch):
    pytest.importorskip("fastapi")
    from backend import auth
    token = auth.make_token("demo@churniq.com")
    assert auth.read_token(token)["sub"] == "demo@churniq.com"
    assert auth.read_token(token[:-2] + "xx") is None
    monkeypatch.setattr(auth.config, "TOKEN_TTL_SECONDS", -10)
    assert auth.read_token(auth.make_token("demo@churniq.com")) is None


def test_credentials_check():
    pytest.importorskip("fastapi")
    from backend import auth, config
    assert auth.check_credentials(config.DEMO_EMAIL.upper(), config.DEMO_PASSWORD)
    assert not auth.check_credentials(config.DEMO_EMAIL, "wrong")
