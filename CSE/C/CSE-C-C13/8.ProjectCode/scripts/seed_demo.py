"""Seed local demo accounts (clearly fictional) for trying CipherVault.

Usage:
    python scripts/seed_demo.py --url http://localhost:8413

Creates owner@example.com / editor@example.com / viewer@example.com with
passwords shown below. Keys are real RSA-2048 pairs generated locally; the
private keys are protected with the demo passwords exactly like the app does.
"""

import argparse
import base64
import sys

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import json

try:
    import httpx
except ImportError:
    print("httpx is required: pip install httpx")
    sys.exit(1)

DEMOS = [
    ("Olivia Owner", "owner@example.com", "Demo-Owner-123"),
    ("Eddie Editor", "editor@example.com", "Demo-Editor-123"),
    ("Vera Viewer", "viewer@example.com", "Demo-Viewer-123"),
]


def make_bundle(password: str):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_bytes(serialization.Encoding.DER,
                                        serialization.PublicFormat.SubjectPublicKeyInfo)
    priv = key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=120000)
    kek = kdf.derive(password.encode())
    iv = os.urandom(12)
    ct = AESGCM(kek).encrypt(iv, priv, None)
    bundle = json.dumps({"salt": base64.b64encode(salt).decode(), "iv": base64.b64encode(iv).decode(),
                         "data": base64.b64encode(ct).decode(), "iterations": 120000})
    return base64.b64encode(pub).decode(), bundle, base64.b64encode(salt).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8413")
    args = ap.parse_args()
    for name, email, pw in DEMOS:
        pub, bundle, salt = make_bundle(pw)
        r = httpx.post(f"{args.url}/api/auth/register",
                       json={"name": name, "email": email, "password": pw, "public_key": pub,
                             "encrypted_private_key": bundle, "private_key_salt": salt}, timeout=30)
        if r.status_code == 201:
            print(f"created {email} / password: {pw}")
        elif r.status_code == 400:
            print(f"exists  {email} / password: {pw}")
        else:
            print(f"FAILED {email}: {r.status_code} {r.text}")


if __name__ == "__main__":
    main()
