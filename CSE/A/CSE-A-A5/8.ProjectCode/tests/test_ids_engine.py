"""ThreatSense Engine tests against the shipped model artifacts."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cipherguard.ids.features import FEATURE_NAMES  # noqa: E402
from cipherguard.ids.inference import ThreatSenseEngine  # noqa: E402

ATTACK = {"proto": "tcp", "service": "ftp", "state": "RST", "dur": 3.5, "sbytes": 85000, "dbytes": 1200, "rate": 95000,
          "spkts": 35, "dpkts": 4, "ct_srv_src": 12, "ct_dst_ltm": 15}
NORMAL = {"proto": "tcp", "service": "http", "state": "CON", "dur": 0.3, "sbytes": 900, "dbytes": 700, "rate": 12000,
          "spkts": 7, "dpkts": 5, "ct_srv_src": 1, "ct_dst_ltm": 1}


def _full(partial):
    base = {f: 0 for f in FEATURE_NAMES}
    base.update({"proto": "tcp", "service": "http", "state": "CON"})
    base.update(partial)
    return base


@pytest.fixture(scope="module")
def engine():
    e = ThreatSenseEngine(models_dir=ROOT / "models")
    e.load()
    return e


def test_engine_loads_all_artifacts(engine):
    assert engine.loaded and engine.cnn_backend == "torch" and engine.input_dim == 70


def test_attack_and_normal_presets(engine):
    a, n = engine.score_single(_full(ATTACK)), engine.score_single(_full(NORMAL))
    assert a["label"] == "attack" and a["severity"] in ("medium", "high", "critical")
    assert n["label"] == "normal" and n["severity"] == "low"


def test_scores_are_probabilities(engine):
    r = engine.score_single(_full(ATTACK))
    for k in ("confidence", "xgb_score", "cnn_score"):
        assert 0.0 <= r[k] <= 1.0


def test_batch_matches_single(engine):
    df = pd.DataFrame([_full(ATTACK), _full(NORMAL)])
    res = engine.predict_proba(df)
    assert res["labels"] == ["attack", "normal"]
    assert res["ensemble_proba"][0] == pytest.approx(engine.score_single(_full(ATTACK))["confidence"], abs=1e-6)


def test_unseen_category_does_not_crash(engine):
    r = engine.score_single(_full({"proto": "never-seen-proto", "service": "x", "state": "zzz"}))
    assert r["label"] in ("attack", "normal")


def test_shipped_metrics_file_is_consistent():
    m = json.loads((ROOT / "reports" / "metrics.json").read_text())
    tn, fp = m["confusion_matrix"][0]
    fn, tp = m["confusion_matrix"][1]
    assert tn + fp + fn + tp == m["splits"]["test"]
    assert m["accuracy"] == pytest.approx((tn + tp) / (tn + fp + fn + tp))
