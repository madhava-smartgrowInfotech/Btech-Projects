"""Unit tests for the src/ pipeline (small synthetic frames, no network, no files)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (  # noqa: E402
    baseline_models,
    demand_forecasting,
    domain_adaptation,
    evaluation,
    feature_engineering,
    preprocessing,
    xgboost_model,
)


def make_tx(n_days=40, articles=(1, 2, 3), seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for d in pd.date_range("2020-01-01", periods=n_days):
        for a in articles:
            for _ in range(int(rng.integers(1, 6))):
                rows.append({"t_dat": d.strftime("%Y-%m-%d"), "customer_id": f"c{rng.integers(0, 50)}", "article_id": a,
                             "price": 0.03 + 0.01 * a, "sales_channel_id": int(rng.integers(1, 3))})
    return pd.DataFrame(rows)


def make_art(articles=(1, 2, 3)):
    return pd.DataFrame({"article_id": list(articles), "prod_name": [f"p{a}" for a in articles],
                         "product_type_name": ["Trousers", "Dress", "Trousers"][: len(articles)],
                         "department_name": ["Denim", "Dresses", "Denim"][: len(articles)]})


# ---- preprocessing -----------------------------------------------------------------------------
def test_clean_transactions_drops_bad_rows():
    tx = pd.DataFrame({"t_dat": ["2020-01-02", "2020-01-01", "bad", "2020-01-01", "2020-01-03"],
                       "customer_id": ["a", "a", "b", "a", None], "article_id": [1, 1, 1, 1, 1],
                       "price": [0.1, 0.1, 0.1, 0.1, 0.1]})
    out = preprocessing.clean_transactions(tx)
    assert len(out) == 2  # bad date, null customer and the exact duplicate removed
    assert out["t_dat"].is_monotonic_increasing


def test_clean_transactions_removes_non_positive_price():
    tx = pd.DataFrame({"t_dat": ["2020-01-01"] * 3, "customer_id": ["a", "b", "c"], "article_id": [1, 1, 1], "price": [0.1, 0.0, -2]})
    assert len(preprocessing.clean_transactions(tx)) == 1


def test_clean_articles_fills_unknown_and_dedupes():
    art = pd.DataFrame({"article_id": [1, 1, 2], "prod_name": ["a", "a", None], "detail_desc": [None, None, "x"]})
    out = preprocessing.clean_articles(art)
    assert len(out) == 2 and (out["prod_name"] == "Unknown").sum() == 1


def test_merge_keeps_all_transactions_even_without_article():
    tx = make_tx(3, articles=(1, 2, 99))
    merged = preprocessing.merge_datasets(preprocessing.clean_transactions(tx), make_art((1, 2)))
    assert len(merged) == len(preprocessing.clean_transactions(tx))
    assert (merged.loc[merged.article_id == 99, "product_type_name"] == "Unknown").all()


def test_quality_report_counts():
    tx = make_tx(5)
    clean = preprocessing.clean_transactions(tx)
    merged = preprocessing.merge_datasets(clean, make_art())
    rep = preprocessing.data_quality_report(tx, clean, merged)
    assert rep["num_products"] == 3 and rep["rows_removed"] == len(tx) - len(clean)


# ---- aggregation + features --------------------------------------------------------------------
def build(n_days=60):
    clean = preprocessing.clean_transactions(make_tx(n_days))
    merged = preprocessing.merge_datasets(clean, preprocessing.clean_articles(make_art()))
    daily = demand_forecasting.aggregate_daily_demand(merged)
    return clean, daily


def test_daily_demand_equals_row_count():
    clean, daily = build(10)
    one = clean[(clean.article_id == 1) & (clean.t_dat == clean.t_dat.min())]
    got = daily[(daily.article_id == 1) & (daily.t_dat == clean.t_dat.min())]["demand"].iloc[0]
    assert got == len(one)


def test_fill_missing_dates_adds_zero_days():
    daily = pd.DataFrame({"t_dat": pd.to_datetime(["2020-01-01", "2020-01-04"] * 3), "article_id": [1] * 2 + [2] * 2 + [3] * 2,
                          "demand": [3, 5] * 3, "price": 0.1, "sales_channel_id": 1})
    out = demand_forecasting.fill_missing_dates_per_article(daily, min_transactions_per_article=2)
    a1 = out[out.article_id == 1].sort_values("t_dat")
    assert len(a1) == 4 and a1["demand"].tolist() == [3, 0, 0, 5]


def test_lag_features_use_only_the_past():
    _, daily = build(60)
    filled = demand_forecasting.fill_missing_dates_per_article(daily)
    ft, _ = feature_engineering.build_feature_table(filled)
    g = ft[ft.article_id == 1].sort_values("t_dat").reset_index(drop=True)
    assert g.loc[10, "lag_1"] == g.loc[9, "demand"]
    assert g.loc[20, "lag_7"] == g.loc[13, "demand"]
    # rolling mean of day 20 is built from days 14..19 (shifted), never day 20 itself
    assert g.loc[20, "rolling_mean_7"] == pytest.approx(g.loc[13:19, "demand"].mean())


def test_time_features_cyclical_and_weekend():
    df = pd.DataFrame({"t_dat": pd.to_datetime(["2020-01-04", "2020-01-06"])})
    out = feature_engineering.add_time_features(df)
    assert out["is_weekend"].tolist() == [1, 0]
    assert np.allclose(out["month_sin"] ** 2 + out["month_cos"] ** 2, 1)


def test_encode_categoricals_returns_mapping():
    df = pd.DataFrame({"c": ["b", "a", "b"]})
    out, mp = feature_engineering.encode_categoricals(df, ["c"])
    assert out["c"].tolist() == [1, 0, 1] and mp["c"] == {0: "a", 1: "b"}


def test_feature_columns_exclude_ids_and_target():
    _, daily = build(60)
    ft, _ = feature_engineering.build_feature_table(demand_forecasting.fill_missing_dates_per_article(daily))
    cols = feature_engineering.get_feature_columns(ft)
    assert not {"t_dat", "article_id", "demand"} & set(cols) and "lag_28" in cols


# ---- split + baseline --------------------------------------------------------------------------
def test_chronological_split_has_no_overlap():
    _, daily = build(60)
    tr, te = baseline_models.chronological_split(daily, train_fraction=0.8)
    assert tr["t_dat"].max() < te["t_dat"].min() and len(tr) + len(te) == len(daily)


def test_moving_average_falls_back_for_unseen_article():
    tr = pd.DataFrame({"t_dat": pd.to_datetime(["2020-01-01"] * 2), "article_id": [1, 2], "demand": [4.0, 8.0]})
    te = pd.DataFrame({"article_id": [1, 99]})
    pred = baseline_models.moving_average_forecast(tr, te)
    assert pred[0] == 4.0 and pred[1] == 6.0  # unseen article -> global mean


# ---- evaluation --------------------------------------------------------------------------------
def test_safe_mape_excludes_zero_actuals():
    mape, excl = evaluation.safe_mape([0, 10, 20], [5, 11, 18])
    assert excl == 1 and mape == pytest.approx(10.0)


def test_evaluate_model_perfect_prediction():
    m = evaluation.evaluate_model([1, 2, 3, 4], [1, 2, 3, 4])
    assert m["RMSE"] == 0 and m["MAE"] == 0 and m["R2"] == 1


def test_improvement_percentage_sign_and_zero_guard():
    assert evaluation.improvement_percentage(10, 8) == pytest.approx(20)
    assert evaluation.improvement_percentage(10, 12) == pytest.approx(-20)
    assert np.isnan(evaluation.improvement_percentage(0, 1))


def test_before_after_report_has_four_metrics():
    b = {"RMSE": 2, "MAE": 1, "MAPE (%)": 50, "R2": 0.5}
    a = {"RMSE": 1, "MAE": 0.5, "MAPE (%)": 25, "R2": 0.75}
    rep = evaluation.before_after_adaptation_report(b, a)
    assert rep["Metric"].tolist() == ["RMSE", "MAE", "MAPE (%)", "R2"]
    assert rep["Improvement (%)"].tolist() == pytest.approx([50, 50, 50, 50])


# ---- xgboost + domain adaptation ---------------------------------------------------------------
def toy_domains(n=400, seed=1):
    rng = np.random.default_rng(seed)
    src = pd.DataFrame({"x1": rng.normal(0, 1, n), "x2": rng.normal(0, 1, n)})
    tgt = pd.DataFrame({"x1": rng.normal(1.5, 1, n), "x2": rng.normal(0, 1, n)})
    return src, tgt


def test_xgboost_trains_and_accepts_sample_weight():
    src, _ = toy_domains()
    y = 2 * src["x1"] + 1
    m = xgboost_model.train_xgboost(src, y, params={"n_estimators": 30, "max_depth": 3})
    m2 = xgboost_model.train_xgboost(src, y, params={"n_estimators": 30, "max_depth": 3}, sample_weight=np.ones(len(src)))
    assert np.corrcoef(m.predict(src), y)[0, 1] > 0.95 and len(m2.predict(src)) == len(src)


def test_domain_classifier_detects_shift():
    src, tgt = toy_domains()
    _, acc = domain_adaptation.train_domain_classifier(src, tgt)
    assert acc > 0.7


def test_domain_classifier_near_chance_without_shift():
    rng = np.random.default_rng(3)
    a = pd.DataFrame({"x": rng.normal(size=500)})
    b = pd.DataFrame({"x": rng.normal(size=500)})
    _, acc = domain_adaptation.train_domain_classifier(a, b)
    assert acc < 0.62


def test_instance_weights_positive_clipped_and_favour_target_like_rows():
    src, tgt = toy_domains()
    clf, _ = domain_adaptation.train_domain_classifier(src, tgt)
    w = domain_adaptation.compute_instance_weights(clf, src, clip_max=5.0)
    assert (w >= 0).all() and w.max() <= 5.0
    hi, lo = w[src["x1"].values > 1], w[src["x1"].values < -1]
    assert hi.mean() > lo.mean()


def test_split_domains_and_shift_summary_ranks_shifted_feature_first():
    src, tgt = toy_domains()
    df = pd.concat([src.assign(d=0), tgt.assign(d=1)])
    s, t = domain_adaptation.split_domains(df, "d", 0, 1)
    assert len(s) == len(t) == 400
    summ = domain_adaptation.domain_shift_summary(s.drop(columns="d"), t.drop(columns="d"))
    assert summ.iloc[0]["feature"] == "x1"
