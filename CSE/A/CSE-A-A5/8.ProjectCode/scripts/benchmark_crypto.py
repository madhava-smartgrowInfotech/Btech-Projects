"""Measure the SecureChannel (ECDH P-256 + HKDF-SHA256 + AES-256-GCM) and a classical RSA-OAEP + AES-GCM hybrid.

Everything uses the `cryptography` package on this machine; nothing is estimated.
Output: experiments/crypto/metrics.json

    python scripts/benchmark_crypto.py
"""
import base64
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import padding, rsa  # noqa: E402
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402

from cipherguard.crypto.secure_channel import KeyPair, SecureChannel  # noqa: E402

SIZES = {"1 KB": 1024, "10 KB": 10 * 1024, "100 KB": 100 * 1024, "1 MB": 1024 * 1024, "5 MB": 5 * 1024 * 1024}


def reps_for(n):
    return 300 if n <= 100 * 1024 else 40 if n <= 1024 * 1024 else 15


def timeit(fn, reps):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    return {"median_ms": statistics.median(ts), "p95_ms": ts[int(0.95 * (len(ts) - 1))], "reps": reps}


def secure_channel_costs(cloud):
    out = {}
    for label, n in SIZES.items():
        pt = os.urandom(n)
        enc = SecureChannel.encrypt_with_ephemeral(pt, cloud.public_key)

        def dec():
            eph = KeyPair.load_public_from_bytes(base64.b64decode(enc["ephemeral_public"]))
            key = SecureChannel.derive_session_key(cloud.private_key, eph)
            SecureChannel.decrypt(base64.b64decode(enc["ciphertext"]), base64.b64decode(enc["nonce"]), base64.b64decode(enc["tag"]), key)

        r = reps_for(n)
        e = timeit(lambda: SecureChannel.encrypt_with_ephemeral(pt, cloud.public_key), r)
        d = timeit(dec, r)
        out[label] = {"bytes": n, "encrypt": e, "decrypt": d,
                      "encrypt_throughput_mb_s": n / 1048576 / (e["median_ms"] / 1000)}
    return out


def aes_only_costs():
    key = AESGCM.generate_key(256)
    out = {}
    for label, n in SIZES.items():
        pt, nonce = os.urandom(n), os.urandom(12)
        a = AESGCM(key)
        ct = a.encrypt(nonce, pt, None)
        r = reps_for(n)
        e = timeit(lambda: a.encrypt(nonce, pt, None), r)
        d = timeit(lambda: a.decrypt(nonce, ct, None), r)
        out[label] = {"encrypt": e, "decrypt": d, "throughput_mb_s": n / 1048576 / (e["median_ms"] / 1000)}
    return out


def rsa_hybrid_costs(bits):
    t0 = time.perf_counter()
    priv = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    keygen_ms = (time.perf_counter() - t0) * 1000
    pub = priv.public_key()
    oaep = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    out = {"keygen_ms_one_time": keygen_ms, "sizes": {}}
    for label, n in SIZES.items():
        pt = os.urandom(n)

        def enc():
            k = AESGCM.generate_key(256)
            nonce = os.urandom(12)
            return pub.encrypt(k, oaep), nonce, AESGCM(k).encrypt(nonce, pt, None)

        wrapped, nonce, ct = enc()

        def dec():
            k = priv.decrypt(wrapped, oaep)
            AESGCM(k).decrypt(nonce, ct, None)

        r = reps_for(n)
        out["sizes"][label] = {"encrypt": timeit(enc, r), "decrypt": timeit(dec, r), "wrapped_key_bytes": len(wrapped)}
    return out


def key_setup_costs(cloud):
    ephemeral = timeit(lambda: KeyPair.generate(), 300)
    other = KeyPair.generate()
    exchange = timeit(lambda: SecureChannel.derive_session_key(other.private_key, cloud.public_key), 300)
    return {"ecdh_p256_keygen": ephemeral, "ecdh_exchange_plus_hkdf": exchange}


def tamper_tests(cloud, trials=1000):
    msg = b"confidential record 0123456789" * 8
    results = {}

    def fresh():
        e = SecureChannel.encrypt_with_ephemeral(msg, cloud.public_key)
        return (base64.b64decode(e["ciphertext"]), base64.b64decode(e["nonce"]), base64.b64decode(e["tag"]),
                base64.b64decode(e["ephemeral_public"]))

    def try_decrypt(ct, nonce, tag, eph, key=None):
        try:
            if key is None:
                key = SecureChannel.derive_session_key(cloud.private_key, KeyPair.load_public_from_bytes(eph))
            SecureChannel.decrypt(ct, nonce, tag, key)
            return False  # accepted
        except Exception:
            return True  # rejected

    def flip(b):
        i = int.from_bytes(os.urandom(4), "big") % len(b)
        bit = 1 << (int.from_bytes(os.urandom(1), "big") % 8)
        return b[:i] + bytes([b[i] ^ bit]) + b[i + 1:]

    cases = {
        "untouched message accepted": lambda ct, n, t, e: not try_decrypt(ct, n, t, e),
        "ciphertext bit flipped": lambda ct, n, t, e: try_decrypt(flip(ct), n, t, e),
        "tag bit flipped": lambda ct, n, t, e: try_decrypt(ct, n, flip(t), e),
        "nonce bit flipped": lambda ct, n, t, e: try_decrypt(ct, flip(n), t, e),
        "ciphertext truncated by one byte": lambda ct, n, t, e: try_decrypt(ct[:-1], n, t, e),
        "decrypted with another party's key": lambda ct, n, t, e: try_decrypt(ct, n, t, e, key=SecureChannel.derive_session_key(KeyPair.generate().private_key, KeyPair.load_public_from_bytes(e))),
    }
    for name, fn in cases.items():
        ok = sum(1 for _ in range(trials) if fn(*fresh()))
        results[name] = {"trials": trials, "as_expected": ok}
    return results


def uniqueness(cloud, n=20000):
    nonces, cts = set(), set()
    pt = b"identical plaintext"
    for _ in range(n):
        e = SecureChannel.encrypt_with_ephemeral(pt, cloud.public_key)
        nonces.add(e["nonce"])
        cts.add(e["ciphertext"] + e["tag"])
    return {"encryptions": n, "distinct_nonces": len(nonces), "distinct_ciphertexts_for_identical_plaintext": len(cts)}


def overhead():
    rows = {}
    for label, n in SIZES.items():
        # ciphertext == plaintext length (GCM is a stream mode); nonce 12 + tag 16 + 65-byte uncompressed P-256 point
        rows[label] = {"plaintext_bytes": n, "fixed_overhead_bytes": 12 + 16 + 65, "overhead_percent": (12 + 16 + 65) / n * 100}
    return rows


def main():
    cloud = KeyPair.generate()
    print("secure channel ...", flush=True)
    sc = secure_channel_costs(cloud)
    print("aes only ...", flush=True)
    aes = aes_only_costs()
    print("rsa 2048 / 3072 ...", flush=True)
    r2048 = rsa_hybrid_costs(2048)
    r3072 = rsa_hybrid_costs(3072)
    print("key setup ...", flush=True)
    ks = key_setup_costs(cloud)
    print("tamper tests ...", flush=True)
    tamper = tamper_tests(cloud)
    print("uniqueness ...", flush=True)
    uq = uniqueness(cloud)
    import cryptography
    out = {"machine": {"python": platform.python_version(), "cryptography": cryptography.__version__, "platform": platform.platform(),
                       "processor": platform.processor()},
           "secure_channel_ecdh_aesgcm": sc, "aes256gcm_only": aes, "rsa2048_oaep_aesgcm": r2048, "rsa3072_oaep_aesgcm": r3072,
           "key_setup": ks, "tamper_tests": tamper, "uniqueness": uq, "wire_overhead": overhead()}
    dest = ROOT / "experiments" / "crypto"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "metrics.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("tamper_tests", "uniqueness")}, indent=1))
    for lbl in SIZES:
        print(lbl, "SC enc %.3f dec %.3f | RSA2048 enc %.3f dec %.3f" % (
            sc[lbl]["encrypt"]["median_ms"], sc[lbl]["decrypt"]["median_ms"],
            r2048["sizes"][lbl]["encrypt"]["median_ms"], r2048["sizes"][lbl]["decrypt"]["median_ms"]))


if __name__ == "__main__":
    main()
