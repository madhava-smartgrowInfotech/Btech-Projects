"""Unit tests for the SecureChannel (ECDH P-256 + HKDF-SHA256 + AES-256-GCM)."""
import base64
import os
import sys
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cipherguard.crypto.secure_channel import KeyPair, SecureChannel  # noqa: E402


@pytest.fixture(scope="module")
def cloud():
    return KeyPair.generate()


def _open(cloud, enc):
    eph = KeyPair.load_public_from_bytes(base64.b64decode(enc["ephemeral_public"]))
    key = SecureChannel.derive_session_key(cloud.private_key, eph)
    return key, base64.b64decode(enc["ciphertext"]), base64.b64decode(enc["nonce"]), base64.b64decode(enc["tag"])


def test_both_sides_derive_the_same_key():
    a, b = KeyPair.generate(), KeyPair.generate()
    ka = SecureChannel.derive_session_key(a.private_key, b.public_key)
    kb = SecureChannel.derive_session_key(b.private_key, a.public_key)
    assert ka == kb and len(ka) == 32


def test_round_trip(cloud):
    msg = b"quarterly payroll export"
    enc = SecureChannel.encrypt_with_ephemeral(msg, cloud.public_key)
    key, ct, nonce, tag = _open(cloud, enc)
    assert SecureChannel.decrypt(ct, nonce, tag, key) == msg
    assert ct != msg


def test_sizes_of_nonce_tag_and_point(cloud):
    enc = SecureChannel.encrypt_with_ephemeral(b"x" * 100, cloud.public_key)
    assert len(base64.b64decode(enc["nonce"])) == 12
    assert len(base64.b64decode(enc["tag"])) == 16
    assert len(base64.b64decode(enc["ephemeral_public"])) == 65
    assert len(base64.b64decode(enc["ciphertext"])) == 100  # GCM keeps the length


def test_same_plaintext_gives_different_ciphertext(cloud):
    a = SecureChannel.encrypt_with_ephemeral(b"same", cloud.public_key)
    b = SecureChannel.encrypt_with_ephemeral(b"same", cloud.public_key)
    assert a["ciphertext"] != b["ciphertext"] and a["nonce"] != b["nonce"] and a["ephemeral_public"] != b["ephemeral_public"]


@pytest.mark.parametrize("field", ["ciphertext", "tag", "nonce"])
def test_any_flipped_bit_is_rejected(cloud, field):
    enc = SecureChannel.encrypt_with_ephemeral(b"integrity matters", cloud.public_key)
    key, ct, nonce, tag = _open(cloud, enc)
    parts = {"ciphertext": ct, "tag": tag, "nonce": nonce}
    parts[field] = bytes([parts[field][0] ^ 0x01]) + parts[field][1:]
    with pytest.raises(InvalidTag):
        SecureChannel.decrypt(parts["ciphertext"], parts["nonce"], parts["tag"], key)


def test_wrong_key_is_rejected(cloud):
    enc = SecureChannel.encrypt_with_ephemeral(b"secret", cloud.public_key)
    _, ct, nonce, tag = _open(cloud, enc)
    with pytest.raises(InvalidTag):
        SecureChannel.decrypt(ct, nonce, tag, os.urandom(32))


def test_bad_parameter_lengths_are_refused(cloud):
    key = os.urandom(32)
    with pytest.raises(ValueError):
        SecureChannel.encrypt(b"x", b"short")
    with pytest.raises(ValueError):
        SecureChannel.decrypt(b"x", b"\0" * 11, b"\0" * 16, key)
    with pytest.raises(ValueError):
        SecureChannel.decrypt(b"x", b"\0" * 12, b"\0" * 15, key)


def test_empty_and_large_payloads(cloud):
    for n in (0, 1, 5 * 1024 * 1024):
        msg = os.urandom(n)
        key, ct, nonce, tag = _open(cloud, SecureChannel.encrypt_with_ephemeral(msg, cloud.public_key))
        assert SecureChannel.decrypt(ct, nonce, tag, key) == msg
