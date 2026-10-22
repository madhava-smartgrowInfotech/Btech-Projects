"""Real tests for preprocessing, ensemble gating, fusion and Flask routes."""
import io
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app import config  # noqa: E402
from app import ensemble as ens  # noqa: E402
from app import preprocessing as pre  # noqa: E402


def _png_bytes(color=(10, 120, 200), size=(64, 64)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def test_preprocessing_valid_image():
    raw = _png_bytes()
    img = pre.decode_image(raw)
    assert img.size == (64, 64)
    assert img.mode == "RGB"
    assert pre.allowed_extension("photo.JPG")


def test_preprocessing_rejects_unsupported_and_corrupt():
    assert not pre.allowed_extension("notes.txt")
    assert not pre.allowed_extension("noext")

    class FakeUpload:
        filename = "evil.txt"
        def read(self):
            return b"hello"

    with pytest.raises(pre.PreprocessingError):
        pre.validate_upload(FakeUpload())
    with pytest.raises(pre.PreprocessingError):
        pre.decode_image(b"this is not an image at all")


def test_weight_normalization():
    w = ens.normalize_weights({"a1": 0.35, "a2": 0.15, "b": 0.25, "c": 0.25})
    assert abs(sum(w.values()) - 1.0) < 1e-9
    w2 = ens.normalize_weights({"a1": 7, "b": 3})
    assert w2["a1"] == pytest.approx(0.7)


def test_logit_fusion_uses_weights():
    logits = {"a1": [2.0, 0.0], "b": [2.0, 0.0]}
    fused = ens.fuse_logits(logits, {"a1": 0.5, "b": 0.5})
    assert fused[0] == pytest.approx(2.0)
    assert fused[1] == pytest.approx(0.0)
    # Unequal weights shift the result toward a1
    fused2 = ens.fuse_logits({"a1": [4.0, 0.0], "b": [0.0, 0.0]}, {"a1": 0.75, "b": 0.25})
    assert fused2[0] == pytest.approx(3.0)


def test_gate1_excludes_confident_outlier():
    logits = {
        "a1": [3.0, 0.0], "a2": [2.5, 0.0],
        "b": [0.0, 5.0],  # strongly disagrees with all three others
        "c": [2.0, 0.0],
    }
    w = {"a1": 0.35, "a2": 0.15, "b": 0.25, "c": 0.25}
    active, excluded, _reason = ens.apply_gate1(logits, w)
    assert excluded == "b"
    assert "b" not in active


def test_gate1_keeps_agreeing_b():
    logits = {
        "a1": [0.0, 3.0], "a2": [0.0, 2.5],
        "b": [0.0, 3.2], "c": [0.0, 2.0],
    }
    w = {"a1": 0.35, "a2": 0.15, "b": 0.25, "c": 0.25}
    active, excluded, _ = ens.apply_gate1(logits, w)
    assert excluded is None
    assert set(active) == {"a1", "a2", "b", "c"}


def test_gate2_corrects_toward_bc_consensus():
    fused = [4.0, 0.0]  # points REAL
    logits = {"b": [0.0, 4.0], "c": [0.0, 3.5], "a1": [4.0, 0.0], "a2": [4.0, 0.0]}
    adj, applied, _ = ens.apply_gate2(fused, logits)
    assert applied is True
    assert adj[1] > fused[1]


def test_gate2_no_correction_without_consensus():
    fused = [4.0, 0.0]
    logits = {"b": [0.0, 4.0], "c": [4.0, 0.0], "a1": [4.0, 0.0]}
    adj, applied, _ = ens.apply_gate2(fused, logits)
    assert applied is False
    assert adj == fused


def test_prediction_response_structure_with_fixture_models():
    """Train-free check: build tiny real checkpoints, run the Flask stack end to end."""
    import torch
    from app import models as app_models

    tmp_models = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_models")
    os.makedirs(tmp_models, exist_ok=True)
    # Save randomly-initialized (untrained) branch weights as fixtures — real
    # forward passes, no hardcoded predictions.
    fixtures = {}
    for branch, builder in app_models.BUILDERS.items():
        m = builder()
        p = os.path.join(tmp_models, f"{branch}.pt")
        torch.save({k: v.cpu() for k, v in m.state_dict().items()}, p)
        fixtures[branch] = p
    old = dict(config.MODEL_FILES)
    config.MODEL_FILES.update({"a1": fixtures["a1"], "a2": fixtures["a2"],
                               "b": fixtures["b"], "c": fixtures["c"]})
    try:
        from app import inference
        inference._BRANCH_MODELS.clear()
        inference._LOADED = False
        img = Image.new("RGB", (96, 96), (90, 140, 60))
        pred = inference.predict_image(img)
        assert pred["predicted_label"] in ("REAL", "AI_GENERATED")
        assert 0.0 <= pred["prob_real"] <= 1.0
        assert abs(pred["prob_real"] + pred["prob_fake"] - 1.0) < 1e-5
        assert set(pred["branch_labels"]) == {"a1", "a2", "b", "c"}
    finally:
        config.MODEL_FILES.update(old)
        from app import inference as _inf
        _inf._BRANCH_MODELS.clear()
        _inf._LOADED = False


def test_health_endpoint():
    from app import create_app
    app = create_app()
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code in (200, 503)
    assert "status" in resp.get_json()


def test_predict_route_rejects_bad_file():
    from app import create_app
    app = create_app()
    client = app.test_client()
    data = {"image": (io.BytesIO(b"not an image"), "bad.txt")}
    resp = client.post("/predict", data=data, content_type="multipart/form-data")
    assert resp.status_code in (400, 503)
