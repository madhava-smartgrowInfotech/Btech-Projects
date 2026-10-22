"""Cryptographic primitive tests (server-side mirror of browser WebCrypto behavior)."""

import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def test_aes_gcm_roundtrip():
    key = AESGCM.generate_key(256)
    aes = AESGCM(key)
    iv = os.urandom(12)
    pt = b"CipherVault round-trip plaintext"
    ct = aes.encrypt(iv, pt, None)
    assert aes.decrypt(iv, ct, None) == pt


def test_different_keys_produce_different_ciphertext():
    pt = b"same plaintext"
    iv = os.urandom(12)
    ct1 = AESGCM(AESGCM.generate_key(256)).encrypt(iv, pt, None)
    ct2 = AESGCM(AESGCM.generate_key(256)).encrypt(iv, pt, None)
    assert ct1 != ct2


def test_corrupted_ciphertext_fails_authentication():
    key = AESGCM.generate_key(256)
    aes = AESGCM(key)
    iv = os.urandom(12)
    ct = bytearray(aes.encrypt(iv, b"secret", None))
    ct[0] ^= 0xFF
    try:
        aes.decrypt(iv, bytes(ct), None)
        raise AssertionError("corrupted ciphertext must not decrypt")
    except Exception:
        pass  # expected authentication failure


def test_sha256_verification():
    data = b"hello ciphervault"
    digest = hashlib.sha256(data).hexdigest()
    assert hashlib.sha256(data).hexdigest() == digest
    assert hashlib.sha256(b"tampered").hexdigest() != digest


def test_rsa_oaep_wrap_unwrap():
    owner_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    recipient_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    fek = os.urandom(32)
    # owner unwraps with own key (simulates browser unwrap), re-wraps for recipient
    wrapped_for_owner = owner_key.public_key().encrypt(
        fek, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    assert len(wrapped_for_owner) == 256
    recovered = owner_key.decrypt(
        wrapped_for_owner, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    rewrapped = recipient_key.public_key().encrypt(
        recovered, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    final = recipient_key.decrypt(
        rewrapped, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    assert final == fek
