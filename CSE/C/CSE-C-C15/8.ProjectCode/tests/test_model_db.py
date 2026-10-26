import json
import os
import sqlite3
import time

import pytest

from ml import model_loader
from security import detector
from tests.conftest import attack_features, benign_features

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_model_artifacts_exist_and_match_schema():
    assert model_loader.is_trained()
    model_loader.load_model()
    assert model_loader.get_metadata()["is_synthetic"] is True


def test_prediction_shape_and_confidence_range():
    r = model_loader.predict_traffic(attack_features())
    assert set(r) == {"prediction", "label", "confidence"} and r["prediction"] in ("Attack", "Benign")
    assert 0.5 <= r["confidence"] <= 1.0


def test_volumetric_flood_window_is_attack():
    assert detector.detect(attack_features())["prediction"] == "Attack"


def test_prediction_rejects_bad_feature_dict():
    with pytest.raises(ValueError):
        model_loader.predict_traffic({"received_packets": 1})


def test_detector_reports_untrained_state(monkeypatch):
    monkeypatch.setattr(model_loader, "is_trained", lambda: False)
    with pytest.raises(FileNotFoundError, match="not trained"):
        detector.detect(benign_features())


def test_shipped_metrics_file_is_consistent():
    m = json.load(open(os.path.join(ROOT, "results", "metrics.json")))
    cm = json.load(open(os.path.join(ROOT, "results", "confusion_matrix.json")))["matrix"]
    assert m["test_samples"] == sum(map(sum, cm)) == 4800
    assert m["accuracy"] == pytest.approx((cm[0][0] + cm[1][1]) / 4800)
    assert m["precision"] == pytest.approx(cm[1][1] / (cm[1][1] + cm[0][1]))
    assert m["recall"] == pytest.approx(cm[1][1] / (cm[1][1] + cm[1][0]))


# ---- database ------------------------------------------------------------------------------------------------------
def _rec(**kw):
    base = {"timestamp": time.time(), "interface": "sim", "source": "simulation", "prediction": "Attack",
            "confidence": 0.9, "severity": "High", "packet_rate": 1000.0, "byte_rate": 5e5, "source_count": 10,
            "destination_count": 3, "distributed_risk": 0.5, "mitigation_status": "quarantine", "detail": {"k": [1, 2]}}
    base.update(kw)
    return base


def test_detection_round_trip_and_ordering(db):
    a = db.add_detection(_rec())
    b = db.add_detection(_rec(prediction="Benign", severity="Low"))
    rows = db.get_detections(10)
    assert [r["id"] for r in rows] == [b, a] and json.loads(rows[1]["detail_json"]) == {"k": [1, 2]}


def test_counts_by_prediction_and_severity(db):
    for p, s in [("Attack", "High"), ("Attack", "Critical"), ("Benign", "Low")]:
        db.add_detection(_rec(prediction=p, severity=s))
    assert db.count_by_prediction() == {"Attack": 2, "Benign": 1}
    assert db.count_by_severity() == {"High": 1, "Critical": 1, "Low": 1}


def test_limit_is_applied(db):
    for _ in range(5):
        db.add_detection(_rec())
    assert len(db.get_detections(3)) == 3


def test_mitigation_history_and_recovery(db):
    db.add_mitigation("1.2.3.4", "why", 40, "active")
    db.mark_mitigation_recovered("1.2.3.4", "why")
    assert db.get_mitigations()[0]["status"] == "recovered"


def test_health_history_is_chronological(db):
    for i in range(3):
        db.add_health({"timestamp": i, "cpu_percent": i, "memory_percent": 1, "bytes_sent": 1, "bytes_recv": 1,
                       "packets_sent": 1, "packets_recv": 1})
    assert [h["cpu_percent"] for h in db.get_health_history(10)] == [0, 1, 2]


def test_settings_default_and_overwrite(db):
    assert db.get_setting("window", "10") == "10"
    db.set_setting("window", "20")
    db.set_setting("window", "30")
    assert db.get_setting("window") == "30"


def test_schema_has_four_tables(db):
    with sqlite3.connect(db.path) as c:
        names = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    assert names == {"detections", "mitigations", "health_samples", "settings"}
