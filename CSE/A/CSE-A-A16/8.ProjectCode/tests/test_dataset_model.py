"""Unit tests for dataset loading / splitting and the CNN architecture."""

import cv2
import numpy as np
import pytest

from sign_language_app import config, dataset
from sign_language_app.model import build_cnn


def write_class(folder, name, n, kind):
    d = folder / name
    d.mkdir(parents=True)
    rng = np.random.default_rng(abs(hash(name)) % 1000)
    for i in range(n):
        img = np.zeros((200, 200, 3), np.uint8)
        c = int(rng.integers(80, 120))
        if kind == "disc":
            cv2.circle(img, (c + 20, c + 20), 50, (230, 230, 230), -1)
        else:
            cv2.rectangle(img, (c - 40, c - 40), (c + 40, c + 40), (230, 230, 230), -1)
        cv2.imwrite(str(d / f"{name}_{i}.png"), img)


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "LABELS_PATH", tmp_path / "labels.json")
    return tmp_path


def test_class_counts_cover_all_29_classes(data_dir):
    counts = dataset.class_counts()
    assert list(counts) == config.CLASSES and len(counts) == 29
    assert sum(counts.values()) == 0


def test_class_counts_and_available_classes(data_dir):
    write_class(data_dir, "A", 5, "disc")
    write_class(data_dir, "B", 3, "square")
    assert dataset.class_counts()["A"] == 5 and dataset.class_counts()["B"] == 3
    assert dataset.available_classes() == ["A", "B"]


def test_load_dataset_without_data_raises(data_dir):
    with pytest.raises(RuntimeError):
        dataset.load_dataset()


def test_load_dataset_split_is_70_15_15_and_stratified(data_dir):
    write_class(data_dir, "A", 40, "disc")
    write_class(data_dir, "B", 40, "square")
    ds = dataset.load_dataset()
    assert ds.labels == ["A", "B"]
    assert len(ds.x_train) + len(ds.x_val) + len(ds.x_test) == 80
    assert len(ds.x_train) == 56 and len(ds.x_val) == 12 and len(ds.x_test) == 12
    assert ds.x_train.shape[1:] == (64, 64, 1)
    for y in (ds.y_train, ds.y_val, ds.y_test):
        counts = y.sum(axis=0)
        assert counts[0] == counts[1]


def test_split_is_reproducible(data_dir):
    write_class(data_dir, "A", 20, "disc")
    write_class(data_dir, "B", 20, "square")
    a, b = dataset.load_dataset(), dataset.load_dataset()
    assert np.array_equal(a.x_test, b.x_test)


def test_labels_roundtrip(data_dir):
    dataset.save_labels(["A", "B"])
    assert dataset.load_labels() == ["A", "B"]


def test_cnn_output_shape_and_softmax():
    model = build_cnn(num_classes=29)
    out = model.predict(np.zeros((2, 64, 64, 1), np.float32), verbose=0)
    assert out.shape == (2, 29)
    assert np.allclose(out.sum(axis=1), 1.0, atol=1e-4)


def test_cnn_has_three_conv_blocks():
    model = build_cnn(num_classes=29)
    kinds = [type(layer).__name__ for layer in model.layers]
    assert kinds.count("Conv2D") == 3 and kinds.count("MaxPooling2D") == 3
    assert kinds[-1] == "Dense" and model.output_shape == (None, 29)
