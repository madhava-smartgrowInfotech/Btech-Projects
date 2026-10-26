import numpy as np
import pytest

from app.services import crypto, lsb


def test_capacity_formula(cover):
    h, w = cover.shape[:2]
    assert lsb.capacity_bytes(cover) == (h * w * 3 - 32) // 8


def test_round_trip_exact(cover):
    rng = np.random.default_rng(1)
    for n in (1, 17, 1000, lsb.capacity_bytes(cover)):          # includes the exact-fit case
        data = rng.integers(0, 256, n, dtype=np.uint8).tobytes()
        assert lsb.extract(lsb.embed(cover, data)) == data


def test_only_lsb_changes_and_by_at_most_one(cover):
    data = bytes(range(256)) * 20
    stego = lsb.embed(cover, data)
    diff = np.abs(cover.astype(int) - stego.astype(int))
    assert diff.max() <= 1
    assert np.array_equal(cover >> 1, stego >> 1)               # every higher bit plane is untouched


def test_values_after_payload_untouched(cover):
    data = b"A" * 100
    stego = lsb.embed(cover, data)
    used = 32 + len(data) * 8
    assert np.array_equal(cover.reshape(-1)[used:], stego.reshape(-1)[used:])


def test_oversize_rejected(cover):
    with pytest.raises(lsb.StegoError, match="holds only"):
        lsb.embed(cover, b"x" * (lsb.capacity_bytes(cover) + 1))


def test_clean_cover_has_no_decryptable_payload(cover):
    # a natural image may carry a plausible-looking length header; the bundle must still not parse
    priv, _ = crypto.generate_keypair(2048)
    with pytest.raises((lsb.StegoError, crypto.CryptoError)):
        crypto.decrypt_bundle(priv, lsb.extract(cover))


def test_png_encoding_is_lossless(cover):
    data = b"hidden" * 50
    stego = lsb.embed(cover, data)
    again = lsb.load_rgb(lsb.to_png_bytes(stego))
    assert np.array_equal(again, stego) and lsb.extract(again) == data


def test_alpha_channel_dropped(tmp_path):
    from PIL import Image
    rgba = np.random.default_rng(0).integers(0, 256, (40, 40, 4), dtype=np.uint8)
    p = tmp_path / "a.png"
    Image.fromarray(rgba, "RGBA").save(p)
    assert lsb.load_rgb(str(p)).shape == (40, 40, 3)


def test_non_image_rejected():
    with pytest.raises(lsb.StegoError):
        lsb.load_rgb(b"this is not an image")
