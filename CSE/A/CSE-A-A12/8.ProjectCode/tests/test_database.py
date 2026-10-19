"""Unit tests for the SQLite persistence layer."""

from database import db


def _add(name="a.jpg", pred="Normal", conf=0.9):
    return db.insert_prediction(name, f"uploads/{name}", f"heatmaps/{name}", pred, conf, 0.9, 0.05, 0.05)


def test_init_is_idempotent(sandbox):
    db.init_db()
    db.init_db()
    assert db.get_all_predictions() == []


def test_insert_returns_incrementing_ids(sandbox):
    assert _add("a.jpg") == 1
    assert _add("b.jpg") == 2


def test_get_prediction_round_trip(sandbox):
    pid = _add("scan.jpg", "Viral Pneumonia", 0.77)
    row = db.get_prediction(pid)
    assert row["filename"] == "scan.jpg"
    assert row["prediction"] == "Viral Pneumonia"
    assert abs(row["confidence"] - 0.77) < 1e-9
    assert row["created_at"]


def test_unknown_id_returns_none(sandbox):
    assert db.get_prediction(999) is None


def test_history_is_newest_first(sandbox):
    for n in ("1.jpg", "2.jpg", "3.jpg"):
        _add(n)
    assert [r["filename"] for r in db.get_all_predictions()] == ["3.jpg", "2.jpg", "1.jpg"]


def test_history_limit(sandbox):
    for i in range(5):
        _add(f"{i}.jpg")
    assert len(db.get_all_predictions(limit=2)) == 2


def test_schema_has_expected_columns(sandbox):
    conn = db.get_connection()
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(predictions)")]
    conn.close()
    assert cols == ["id", "filename", "original_path", "heatmap_path", "prediction", "confidence",
                    "prob_normal", "prob_bacterial", "prob_viral", "created_at"]
