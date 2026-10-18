"""Unit tests for the image preprocessing pipeline."""

import numpy as np
import pytest

from sign_language_app import config
from sign_language_app.preprocessing import (
    crop_roi,
    get_roi_box,
    normalize_for_model,
    preprocess_roi,
    reduce_noise,
    segment_hand,
    segment_threshold,
)


def hand_like_roi(size=300, bright_hand=True):
    img = np.full((size, size, 3), 30 if bright_hand else 220, np.uint8)
    img[80:230, 100:200] = 235 if bright_hand else 25
    return img


def test_roi_box_default_frame():
    assert get_roi_box(960, 540) == (620, 90, 920, 390)


def test_roi_box_stays_inside_small_frame():
    x1, y1, x2, y2 = get_roi_box(200, 150)
    assert 0 <= x1 < x2 <= 200 and 0 <= y1 < y2 <= 150


def test_crop_roi_shape_and_independent_copy():
    frame = np.zeros((540, 960, 3), np.uint8)
    roi = crop_roi(frame, get_roi_box(960, 540))
    assert roi.shape == (300, 300, 3)
    roi[:] = 255
    assert frame.max() == 0


def test_reduce_noise_keeps_shape_and_smooths():
    rng = np.random.default_rng(0)
    gray = rng.integers(0, 255, (64, 64), dtype=np.uint8)
    out = reduce_noise(gray)
    assert out.shape == gray.shape
    assert out.std() < gray.std()


@pytest.mark.parametrize("bright_hand", [True, False])
def test_segmentation_marks_hand_as_foreground(bright_hand):
    mask = segment_hand(hand_like_roi(bright_hand=bright_hand))
    assert set(np.unique(mask)) <= {0, 255}
    assert mask.mean() < 127, "foreground (hand) must be the minority white region"
    assert mask[150, 150] == 255, "centre of the hand must be white"
    assert mask[5, 5] == 0, "corner background must be black"


def test_segment_threshold_on_flat_image_does_not_crash():
    mask = segment_threshold(np.full((300, 300), 128, np.uint8))
    assert mask.shape == (300, 300)


def test_normalize_for_model_range_and_shape():
    mask = np.random.default_rng(1).integers(0, 256, (300, 300), dtype=np.uint8)
    out = normalize_for_model(mask)
    assert out.shape == (config.IMG_SIZE, config.IMG_SIZE, 1)
    assert out.dtype == np.float32
    assert 0.0 <= out.min() and out.max() <= 1.0


def test_preprocess_roi_returns_model_input_and_mask():
    model_input, mask = preprocess_roi(hand_like_roi())
    assert model_input.shape == (64, 64, 1)
    assert mask.shape == (300, 300) and mask.dtype == np.uint8


def test_skin_mode_returns_mask():
    mask = segment_hand(hand_like_roi(), mode="skin")
    assert mask.shape == (300, 300)
