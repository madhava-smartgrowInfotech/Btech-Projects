import pytest

from app.services import crypto


def test_round_trip_and_header(keypair):
    priv, pub = keypair
    data = b"confidential " * 100
    bundle, info = crypto.encrypt_bundle(pub, "dir/memo.txt", data)
    assert bundle[:4] == crypto.MAGIC
    name, out, dec = crypto.decrypt_bundle(priv, bundle)
    assert out == data and name == "memo.txt"       # path stripped from the stored name
    assert dec["match"] and dec["embedded_sha256"] == info["input_sha256"]


def test_overhead_matches_layout(keypair):
    priv, pub = keypair
    bundle, info = crypto.encrypt_bundle(pub, "a.bin", b"x" * 10)
    wrapped = 2048 // 8
    # magic 4 + len 2 + wrapped key + nonce 12 + header_len 2 + header json + tag 16
    assert info["wrapped_key_bytes"] == wrapped
    assert len(bundle) > 4 + 2 + wrapped + 12 + 16 + 10


def test_fresh_session_key_and_nonce_per_message(keypair):
    _, pub = keypair
    a, _ = crypto.encrypt_bundle(pub, "a.bin", b"same data")
    b, _ = crypto.encrypt_bundle(pub, "a.bin", b"same data")
    assert a != b
    assert a[6 + 256:6 + 256 + 12] != b[6 + 256:6 + 256 + 12]     # nonces differ


def test_wrong_private_key_rejected(keypair):
    _, pub = keypair
    other_priv, _ = crypto.generate_keypair(2048)
    bundle, _ = crypto.encrypt_bundle(pub, "a.bin", b"secret")
    with pytest.raises(crypto.CryptoError, match="not the key"):
        crypto.decrypt_bundle(other_priv, bundle)


def test_key_size_mismatch_rejected(keypair):
    _, pub = keypair
    priv3072, _ = crypto.generate_keypair(3072)
    bundle, _ = crypto.encrypt_bundle(pub, "a.bin", b"secret")
    with pytest.raises(crypto.CryptoError, match="different key size"):
        crypto.decrypt_bundle(priv3072, bundle)


@pytest.mark.parametrize("offset_from_end", [1, 20, 40])
def test_tampered_ciphertext_fails_tag(keypair, offset_from_end):
    priv, pub = keypair
    bundle, _ = crypto.encrypt_bundle(pub, "a.bin", b"important payload " * 20)
    bad = bytearray(bundle)
    bad[-offset_from_end] ^= 0x01
    with pytest.raises(crypto.CryptoError, match="tag check failed"):
        crypto.decrypt_bundle(priv, bytes(bad))


def test_tampered_wrapped_key_rejected(keypair):
    priv, pub = keypair
    bundle, _ = crypto.encrypt_bundle(pub, "a.bin", b"payload")
    bad = bytearray(bundle)
    bad[10] ^= 0x80
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt_bundle(priv, bytes(bad))


def test_truncated_and_foreign_bundles(keypair):
    priv, pub = keypair
    bundle, _ = crypto.encrypt_bundle(pub, "a.bin", b"payload")
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt_bundle(priv, bundle[:-5])
    with pytest.raises(crypto.CryptoError, match="No CipherVeil bundle"):
        crypto.decrypt_bundle(priv, b"XXXX" + bundle[4:])
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt_bundle(priv, b"")


def test_key_size_policy():
    with pytest.raises(crypto.CryptoError):
        crypto.generate_keypair(1024)
    with pytest.raises(crypto.CryptoError):
        crypto.load_public("not a pem")


def test_fingerprint_stable_and_short(keypair):
    _, pub = keypair
    fp = crypto.fingerprint(pub)
    assert fp == crypto.fingerprint(pub) and len(fp.split(":")) == 12


def test_public_from_private_matches(keypair):
    priv, pub = keypair
    assert crypto.public_from_private(priv).strip() == pub.strip()
