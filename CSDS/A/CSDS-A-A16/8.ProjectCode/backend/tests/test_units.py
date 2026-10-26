import time

import numpy as np
import pytest
import torch
from jose import jwt

from app import security
from app.config import ALGORITHM, SECRET_KEY
from app.ml import taxonomy as T
from app.ml.classifier_model import EmotionCNN, IMG_SIZE
from app.ml.dataset import class_weights
from app.ml.face import detect_largest_face
from app.ml.gan_model import NOISE_DIM, ConditionalDiscriminator, ConditionalGenerator
from app.ml.inference import _preprocess


def test_taxonomy_counts_and_order():
    assert (T.NUM_BASIC, T.NUM_COMPOUND, T.NUM_LABELS) == (7, 11, 18)
    assert T.ALL_LABELS[:7] == T.BASIC_EMOTIONS
    assert len(set(T.ALL_LABELS)) == 18


def test_every_compound_has_two_distinct_basic_components():
    for c in T.COMPOUND_EMOTIONS:
        a, b = T.COMPOUND_COMPONENTS[c]
        assert a != b and a in T.BASIC_INDEX and b in T.BASIC_INDEX


def test_compound_pairs_are_unique():
    pairs = [frozenset(T.COMPOUND_COMPONENTS[c]) for c in T.COMPOUND_EMOTIONS]
    assert len(set(pairs)) == len(pairs)


def test_display_label():
    assert T.display_label("happily_surprised") == "Happily Surprised"


def test_password_hash_roundtrip():
    h = security.hash_password("secret1")
    assert h != "secret1" and security.verify_password("secret1", h)
    assert not security.verify_password("secret2", h)


def test_token_roundtrip_and_tamper():
    tok = security.create_access_token("user-1")
    assert security.decode_access_token(tok) == "user-1"
    assert security.decode_access_token(tok[:-3] + "abc") is None
    assert security.decode_access_token("not-a-token") is None


def test_expired_token_rejected():
    tok = jwt.encode({"sub": "u", "exp": int(time.time()) - 10}, SECRET_KEY, algorithm=ALGORITHM)
    assert security.decode_access_token(tok) is None


def test_token_signed_with_other_key_rejected():
    tok = jwt.encode({"sub": "u", "exp": int(time.time()) + 100}, "other-key", algorithm=ALGORITHM)
    assert security.decode_access_token(tok) is None


def test_class_weights_inverse_frequency():
    w = class_weights(np.array([0] * 90 + [1] * 10))
    assert w[1] > w[0]


def test_cnn_output_shapes():
    x = torch.zeros(2, 1, IMG_SIZE, IMG_SIZE)
    assert EmotionCNN(7)(x).shape == (2, 7)
    assert EmotionCNN(18)(x).shape == (2, 18)


def test_gan_shapes():
    g = ConditionalGenerator(7)
    img = g(torch.randn(3, NOISE_DIM), torch.zeros(3, 7))
    assert img.shape == (3, 1, 64, 64) and img.min() >= -1 and img.max() <= 1
    assert ConditionalDiscriminator(7)(img, torch.zeros(3, 7)).shape == (3, 1)


def test_preprocess_range_and_shape():
    t = _preprocess(np.full((120, 100), 255, np.uint8))
    assert t.shape == (1, 1, 64, 64) and float(t.max()) == pytest.approx(1.0)


def test_no_face_in_flat_image():
    assert detect_largest_face(np.full((200, 200, 3), 127, np.uint8)) is None


def test_synthesised_compound_labels_have_three_bits():
    from app.ml.synthesize_compound import synthesize
    g = ConditionalGenerator(7).eval()
    imgs, labels = synthesize(g, n_per_class=2)
    assert imgs.shape == (22, 64, 64) and imgs.dtype == np.uint8
    assert labels.shape == (22, 18) and (labels.sum(1) == 3).all()
    assert (labels[:, 7:].sum(1) == 1).all()
