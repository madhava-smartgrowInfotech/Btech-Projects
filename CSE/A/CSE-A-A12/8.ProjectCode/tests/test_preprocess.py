"""Unit tests for model/preprocess.py (resize, CLAHE, blur, normalise)."""

import cv2
import numpy as np
import pytest

from model.preprocess import IMG_SIZE, apply_clahe, load_and_preprocess_image, preprocess_for_display

from .conftest import SAMPLE_FILES


def test_output_shape_dtype_and_range():
    img = load_and_preprocess_image(SAMPLE_FILES["normal"])
    assert img.shape == (224, 224, 3)
    assert img.dtype == np.float32
    assert 0.0 <= img.min() and img.max() <= 1.0


def test_three_channels_are_identical():
    img = load_and_preprocess_image(SAMPLE_FILES["bacterial"])
    assert np.array_equal(img[..., 0], img[..., 1])
    assert np.array_equal(img[..., 1], img[..., 2])


def test_accepts_raw_bytes(sample_bytes):
    from_bytes = load_and_preprocess_image(sample_bytes("viral"))
    from_path = load_and_preprocess_image(SAMPLE_FILES["viral"])
    assert np.allclose(from_bytes, from_path)


def test_clahe_changes_the_image():
    plain = load_and_preprocess_image(SAMPLE_FILES["normal"], apply_enhancement=False)
    enhanced = load_and_preprocess_image(SAMPLE_FILES["normal"], apply_enhancement=True)
    assert not np.allclose(plain, enhanced)


def test_clahe_raises_local_contrast():
    rng = np.random.default_rng(0)
    dull = (120 + rng.normal(0, 3, (128, 128))).clip(0, 255).astype(np.uint8)  # low-contrast texture
    assert apply_clahe(dull).std() > 2 * dull.std()


def test_missing_file_raises_value_error(tmp_path):
    with pytest.raises(ValueError):
        load_and_preprocess_image(str(tmp_path / "nope.jpg"))


def test_garbage_bytes_raise_value_error():
    with pytest.raises(ValueError):
        load_and_preprocess_image(b"this is not an image")


def test_display_image_is_uint8_rgb():
    disp = preprocess_for_display(SAMPLE_FILES["normal"])
    assert disp.shape == (224, 224, 3) and disp.dtype == np.uint8


def test_size_constant_matches_model_input():
    from model.model_builder import INPUT_SHAPE

    assert tuple(IMG_SIZE) == tuple(INPUT_SHAPE[:2])


def test_small_image_is_upscaled(tmp_path):
    p = tmp_path / "tiny.png"
    cv2.imwrite(str(p), np.random.randint(0, 255, (32, 40), dtype=np.uint8))
    assert load_and_preprocess_image(str(p)).shape == (224, 224, 3)
