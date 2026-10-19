"""Unit tests for the CNN builder and the Grad-CAM module."""

import numpy as np

from model.gradcam import make_gradcam_heatmap, overlay_heatmap
from model.model_builder import CLASS_NAMES, INPUT_SHAPE, build_custom_cnn, find_last_conv_layer
from model.preprocess import load_and_preprocess_image, preprocess_for_display

from .conftest import SAMPLE_FILES


def test_class_names_are_the_three_project_classes():
    assert CLASS_NAMES == ["Normal", "Bacterial Pneumonia", "Viral Pneumonia"]


def test_custom_cnn_output_is_a_probability_vector():
    m = build_custom_cnn()
    out = m.predict(np.zeros((2, *INPUT_SHAPE), dtype="float32"), verbose=0)
    assert out.shape == (2, 3)
    assert np.allclose(out.sum(axis=1), 1.0, atol=1e-4)


def test_two_class_variant_is_supported():
    m = build_custom_cnn(num_classes=2)
    assert m.output_shape == (None, 2)


def test_last_conv_layer_is_found():
    assert find_last_conv_layer(build_custom_cnn()) == "last_conv"


def test_loaded_model_matches_input_contract(flask_module):
    model = flask_module.get_model()
    assert tuple(model.input_shape[1:]) == INPUT_SHAPE
    assert model.output_shape[-1] == len(flask_module._class_names)


def test_gradcam_heatmap_is_normalised(flask_module):
    model = flask_module.get_model()
    batch = np.expand_dims(load_and_preprocess_image(SAMPLE_FILES["bacterial"]), 0)
    heat, idx = make_gradcam_heatmap(batch, model, flask_module._last_conv_layer)
    assert heat.ndim == 2
    assert 0.0 <= heat.min() and heat.max() <= 1.0 + 1e-6
    assert 0 <= idx < model.output_shape[-1]


def test_gradcam_respects_requested_class(flask_module):
    model = flask_module.get_model()
    batch = np.expand_dims(load_and_preprocess_image(SAMPLE_FILES["normal"]), 0)
    _, idx = make_gradcam_heatmap(batch, model, flask_module._last_conv_layer, pred_index=1)
    assert idx == 1


def test_overlay_keeps_size_and_dtype():
    base = preprocess_for_display(SAMPLE_FILES["normal"])
    heat = np.random.rand(14, 14).astype("float32")
    out = overlay_heatmap(base, heat, alpha=0.4)
    assert out.shape == base.shape and out.dtype == np.uint8


def test_overlay_with_zero_alpha_returns_the_original():
    base = preprocess_for_display(SAMPLE_FILES["normal"])
    out = overlay_heatmap(base, np.ones((7, 7), dtype="float32"), alpha=0.0)
    assert np.array_equal(out, base)
