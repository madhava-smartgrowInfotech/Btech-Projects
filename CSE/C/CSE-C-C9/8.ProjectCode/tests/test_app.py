import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app

VALID = {
    "age": "39", "workclass": "State-gov", "education": "Bachelors",
    "marital-status": "Never-married", "occupation": "Adm-clerical",
    "relationship": "Not-in-family", "race": "White", "sex": "Male",
    "native-country": "United-States", "capital-gain": "2174",
    "capital-loss": "0", "hours-per-week": "40",
}


def _client():
    return create_app().test_client()


def test_health():
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json["status"] in ("ok", "degraded")


def test_pages_load():
    c = _client()
    for url in ["/", "/assess", "/explain", "/forecast", "/whatif", "/performance", "/about"]:
        assert c.get(url).status_code == 200, url


def test_valid_prediction_not_hardcoded():
    c = _client()
    r1 = c.post("/assess", data=VALID)
    assert r1.status_code == 200
    assert b"Financial-strength score" in r1.data
    other = dict(VALID, **{"age": "60", "education": "Doctorate",
                           "capital-gain": "50000", "hours-per-week": "60"})
    r2 = c.post("/assess", data=other)
    assert r2.status_code == 200
    # Different inputs must not produce byte-identical pages (no hardcoded output)
    assert r1.data != r2.data


def test_invalid_input_rejected():
    c = _client()
    assert c.post("/assess", data={}).status_code == 400
    bad = dict(VALID, age="-5")
    assert c.post("/assess", data=bad).status_code == 400
    bad2 = dict(VALID, **{"workclass": "Hacker"})
    assert c.post("/assess", data=bad2).status_code == 400


def test_api_predict_and_forecast():
    c = _client()
    payload = {"age": 39, "workclass": "State-gov", "education": "Bachelors",
               "marital-status": "Never-married", "occupation": "Adm-clerical",
               "relationship": "Not-in-family", "race": "White", "sex": "Male",
               "native-country": "United-States", "capital-gain": 2174,
               "capital-loss": 0, "hours-per-week": 40}
    r = c.post("/api/predict", json=payload)
    assert r.status_code == 200
    assert r.json["ok"] is True
    assert 0 <= r.json["result"]["proba"] <= 1
    assert r.json["result"]["shap"]["available"] is True
    f = c.get("/api/forecast")
    assert f.status_code == 200
    assert f.json["available"] is True
    assert len(f.json["forecast"]) == 12


def test_whatif_changes_score():
    c = _client()
    r = c.post("/whatif", data={**VALID, "scenario_capital_gain": "80000",
                                "scenario_hours": "50",
                                "scenario_education": "",
                                "scenario_capital_loss": ""})
    assert r.status_code == 200
    assert b"Comparison" in r.data


def test_artifacts_present_and_real():
    import json
    comp = json.loads((ROOT / "artifacts" / "model_comparison.json").read_text())
    assert len(comp["models"]) == 4
    assert comp["best_model"] in comp["models"]
    shap_g = json.loads((ROOT / "artifacts" / "shap_global.json").read_text())
    assert len(shap_g["features"]) > 5
    fc = json.loads((ROOT / "artifacts" / "forecast.json").read_text())
    assert len(fc["forecast"]) == 12 and len(fc["history"]) > 100
