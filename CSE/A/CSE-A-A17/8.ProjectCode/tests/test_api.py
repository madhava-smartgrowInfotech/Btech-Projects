"""API tests: the whole pipeline through FastAPI's TestClient on a small synthetic H&M-shaped dataset."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from backend import main as api_main  # noqa: E402
from backend.state import S, reset_downstream  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    # keep the user's saved models untouched
    tmp = tmp_path_factory.mktemp("models")
    api_main.MODEL_DIR = tmp
    api_main.BASELINE_MODEL_PATH = tmp / "b.joblib"
    api_main.ADAPTED_MODEL_PATH = tmp / "a.joblib"
    api_main.FEATURE_INFO_PATH = tmp / "f.joblib"
    for k in list(S):
        S[k] = None
    S["results"] = {}
    return TestClient(api_main.app)


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode()


@pytest.fixture(scope="module")
def files():
    rng = np.random.default_rng(5)
    arts = [101, 102, 103, 104]
    rows = []
    for d in pd.date_range("2020-01-01", periods=70):
        for a in arts:
            for _ in range(int(rng.integers(2, 9))):
                rows.append({"t_dat": d.strftime("%Y-%m-%d"), "customer_id": f"c{rng.integers(0, 80)}", "article_id": a,
                             "price": round(0.03 + 0.005 * (a - 100) + rng.normal(0, 0.002), 5), "sales_channel_id": int(rng.integers(1, 3))})
    tx = pd.DataFrame(rows)
    art = pd.DataFrame({"article_id": arts, "prod_name": [f"p{a}" for a in arts],
                        "product_type_name": ["Trousers", "Dress", "Trousers", "Dress"],
                        "product_group_name": ["Lower", "Full", "Lower", "Full"],
                        "department_name": ["Denim", "Dresses", "Denim", "Dresses"]})
    return tx, art


def upload(client, files, **kw):
    tx, art = files
    return client.post("/api/data/upload",
                       files={"transactions": ("t.csv", csv_bytes(tx)), "articles": ("a.csv", csv_bytes(art))},
                       data={"sample_rows": 0}, **kw)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_state_before_upload_is_empty(client):
    st = client.get("/api/state").json()
    assert st["data_loaded"] is False and st["features_ready"] is False


def test_downstream_routes_are_gated_before_upload(client):
    assert client.get("/api/explore").status_code == 409
    assert client.post("/api/features/build").status_code == 409
    assert client.post("/api/training/baseline", json={"train_fraction": 0.8}).status_code == 409


def test_upload_rejects_wrong_columns(client):
    r = client.post("/api/data/upload", files={"transactions": ("t.csv", b"a,b\n1,2\n"), "articles": ("a.csv", b"article_id,prod_name\n1,x\n")},
                    data={"sample_rows": 0})
    assert r.status_code == 400 and "missing required column" in r.json()["detail"]


def test_upload_rejects_empty_file(client):
    r = client.post("/api/data/upload", files={"transactions": ("t.csv", b""), "articles": ("a.csv", b"article_id,prod_name\n1,x\n")},
                    data={"sample_rows": 0})
    assert r.status_code == 400


def test_upload_ok_and_report(client, files):
    r = upload(client, files)
    assert r.status_code == 200
    rep = r.json()
    assert rep["num_products"] == 4 and rep["num_transactions"] > 0
    assert client.get("/api/data/report").json()["num_transactions"] == rep["num_transactions"]


def test_explore_and_demand_table(client):
    ex = client.get("/api/explore").json()
    assert len(ex["daily"]) == 70 and len(ex["top_products"]) == 4 and len(ex["price_hist"]) == 50
    t = client.get("/api/demand/table", params={"limit": 20}).json()
    assert len(t["rows"]) == 20 and t["total"] > 20


def test_training_gated_until_features(client):
    assert client.post("/api/training/xgboost", json={"train_fraction": 0.8}).status_code == 409


def test_build_features(client):
    r = client.post("/api/features/build")
    assert r.status_code == 200
    js = r.json()
    assert "lag_7" in js["feature_columns"] and len(js["head"]) == 50


def test_train_fraction_validated(client):
    assert client.post("/api/training/baseline", json={"train_fraction": 0.2}).status_code == 422
    assert client.get("/api/training/split", params={"train_fraction": 0.99}).status_code == 400


def test_baseline_and_xgboost_training(client):
    b = client.post("/api/training/baseline", json={"train_fraction": 0.8}).json()
    assert b["metrics"]["RMSE"] > 0
    x = client.post("/api/training/xgboost", json={"train_fraction": 0.8, "tune": False}).json()
    assert x["metrics"]["RMSE"] > 0 and len(x["comparison"]) == 2
    assert client.get("/api/state").json()["saved_model_exists"] is True
    assert client.post("/api/training/load").json() == {"loaded": True}


def test_domain_options_and_validation(client):
    opts = client.get("/api/domain/options").json()["options"]
    chan = next(o for o in opts if o["column"] == "sales_channel_id")
    a, b = chan["values"][0]["value"], chan["values"][1]["value"]
    assert client.post("/api/domain/run", json={"domain_col": "sales_channel_id", "source": a, "target": a}).status_code == 400
    assert client.post("/api/domain/run", json={"domain_col": "price", "source": 1, "target": 2}).status_code == 400
    r = client.post("/api/domain/run", json={"domain_col": "sales_channel_id", "source": a, "target": b})
    assert r.status_code == 200
    js = r.json()
    assert 0 <= js["classifier_accuracy"] <= 1 and len(js["report"]) == 4 and js["weights"]["max"] <= 20.0


def test_evaluation_after_runs(client):
    ev = client.get("/api/evaluation").json()
    assert len(ev["comparison"]) == 2 and ev["domain"] is not None and len(ev["importance"]) > 0


def test_forecast_horizons(client):
    arts = client.get("/api/forecast/articles").json()["articles"]
    assert len(arts) == 4
    for h in (7, 14, 30):
        r = client.post("/api/forecast", json={"article_id": arts[0]["id"], "horizon": h})
        assert r.status_code == 200 and len(r.json()["forecast"]) == h
        assert min(p["predicted_demand"] for p in r.json()["forecast"]) >= 0


def test_forecast_rejects_bad_horizon_and_unknown_article(client):
    arts = client.get("/api/forecast/articles").json()["articles"]
    assert client.post("/api/forecast", json={"article_id": arts[0]["id"], "horizon": 5}).status_code == 400
    assert client.post("/api/forecast", json={"article_id": 1, "horizon": 7}).status_code == 400


def test_new_upload_resets_downstream(client, files):
    assert upload(client, files).status_code == 200
    st = client.get("/api/state").json()
    assert st["features_ready"] is False and st["domain_done"] is False


def test_ai_not_configured_is_a_clear_error(client, monkeypatch):
    monkeypatch.setattr(api_main.gemini_api, "configured", lambda: False)
    assert client.get("/api/ai/status").json()["configured"] is False
    r = client.post("/api/ai/explain", json={"question": "why?"})
    assert r.status_code == 503
