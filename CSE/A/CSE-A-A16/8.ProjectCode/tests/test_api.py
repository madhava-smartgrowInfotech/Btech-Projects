"""Integration tests of the FastAPI layer (in-process, no network). Collection writes go to a temp folder."""

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import main
from sign_language_app import config


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return tmp_path


def jpeg(img=None):
    img = np.zeros((540, 960, 3), np.uint8) if img is None else img
    return cv2.imencode(".jpg", img)[1].tobytes()


def files(data):
    return {"frame": ("f.jpg", data, "image/jpeg")}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_config_describes_pipeline(client):
    j = client.get("/api/config").json()
    assert len(j["classes"]) == 29 and j["img_size"] == 64
    assert j["roi"] == {"x1": 620, "y1": 90, "x2": 920, "y2": 390}
    assert j["thresholds"]["stable_frames"] == config.STABLE_FRAMES_TO_COMMIT


def test_about(client):
    j = client.get("/api/about").json()
    assert len(j["pipeline"]) == 8 and j["base_paper"]["DOI"]


def test_dataset_counts(client, tmp_data):
    j = client.get("/api/dataset").json()
    assert j["total"] == 0 and j["ready_to_train"] is False


def test_unknown_class_is_404(client):
    assert client.get("/api/dataset/Z9/images").status_code == 404
    assert client.post("/api/collect/Z9", files=files(jpeg())).status_code == 404


@pytest.mark.parametrize("name", ["..%2F..%2Fsecret.png", "a.txt", "x y.exe"])
def test_image_endpoint_rejects_bad_names(client, tmp_data, name):
    assert client.get(f"/api/dataset/A/images/{name}").status_code in (400, 404)


def test_collect_saves_png_and_counts(client, tmp_data):
    r = client.post("/api/collect/A", files=files(jpeg()))
    assert r.status_code == 200 and r.json()["count"] == 1
    saved = list((tmp_data / "A").glob("*.png"))
    assert len(saved) == 1
    assert cv2.imread(str(saved[0])).shape[:2] == (200, 200)
    assert client.get("/api/dataset").json()["counts"]["A"] == 1
    listing = client.get("/api/dataset/A/images").json()
    assert listing["total"] == 1
    assert client.get(listing["images"][0]["url"]).status_code == 200


def test_preview_returns_mask_data_url(client):
    r = client.post("/api/preview", files=files(jpeg()))
    assert r.status_code == 200 and r.json()["mask"].startswith("data:image/png;base64,")


def test_empty_and_garbage_frames_are_400(client):
    assert client.post("/api/preview", files=files(b"")).status_code == 400
    assert client.post("/api/preview", files=files(b"not an image")).status_code == 400


def test_non_16x9_frame_is_resized_not_rejected(client):
    small = np.zeros((120, 200, 3), np.uint8)
    assert client.post("/api/preview", files=files(jpeg(small))).status_code == 200


def test_missing_frame_field_is_422(client):
    assert client.post("/api/preview").status_code == 422


def test_recognize_unknown_session_is_404_or_409(client):
    r = client.post("/api/recognize/frame", files=files(jpeg()), data={"session_id": "nope"})
    assert r.status_code in (404, 409)


@pytest.mark.parametrize("body", [
    {"epochs": 0}, {"epochs": 501}, {"batch_size": 0}, {"batch_size": 2000},
    {"learning_rate": 0}, {"learning_rate": 2},
])
def test_train_start_validates_hyperparameters(client, body):
    assert client.post("/api/train/start", json=body).status_code == 400


def test_train_start_needs_two_classes(client, tmp_data):
    assert client.post("/api/train/start", json={}).status_code == 409


def test_train_status_idle(client):
    assert client.get("/api/train/status").json()["state"] in ("idle", "done", "error")


@pytest.mark.parametrize("text, code", [("", 400), ("   ", 400), ("x" * 2001, 400)])
def test_speak_validation(client, text, code):
    assert client.post("/api/tts/speak", json={"text": text}).status_code == code


def test_model_info_shape(client):
    j = client.get("/api/model").json()
    assert "trained" in j
    if j["trained"]:
        assert len(j["labels"]) == 29 and 0 < j["test_accuracy"] <= 1


@pytest.mark.skipif(not config.MODEL_PATH.exists(), reason="no trained model in models/")
def test_recognize_flow_with_trained_model(client):
    assert client.post("/api/recognize/reload").json()["model_loaded"] is True
    sid = client.post("/api/recognize/session").json()["session_id"]
    r = client.post("/api/recognize/frame", files=files(jpeg()), data={"session_id": sid})
    j = r.json()
    assert r.status_code == 200
    assert j["label"] in config.CLASSES and 0 <= j["confidence"] <= 1
    assert j["mask"].startswith("data:image/png")
