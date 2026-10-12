"""Hybrid encryption: AES-256-GCM for the data, RSA-OAEP(SHA-256) for the session key.

Bundle layout (what gets hidden in the image):
    MAGIC(4) | wrapped_key_len(2) | wrapped_key | nonce(12) | ciphertext+tag
The plaintext inside the AES-GCM layer is: header_len(2) | header JSON | file bytes,
where the header carries the file name, size and SHA-256 of the original file.
"""
import hashlib
import json
import os
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"CVL1"
NONCE_LEN = 12
ALLOWED_BITS = (2048, 3072, 4096)
_OAEP = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


class CryptoError(ValueError):
    pass


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_keypair(bits: int = 3072) -> tuple[str, str]:
    if bits not in ALLOWED_BITS:
        raise CryptoError(f"Key size must be one of {ALLOWED_BITS}")
    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return private_pem, public_pem


def load_public(pem: str):
    try:
        key = serialization.load_pem_public_key(pem.encode())
    except Exception as exc:
        raise CryptoError("Not a valid PEM public key") from exc
    if not isinstance(key, rsa.RSAPublicKey):
        raise CryptoError("Only RSA public keys are supported")
    if key.key_size < 2048:
        raise CryptoError("RSA keys below 2048 bits are rejected")
    return key


def load_private(pem: str):
    try:
        key = serialization.load_pem_private_key(pem.encode(), password=None)
    except Exception as exc:
        raise CryptoError("Not a valid unencrypted PEM private key") from exc
    if not isinstance(key, rsa.RSAPrivateKey):
        raise CryptoError("Only RSA private keys are supported")
    if key.key_size < 2048:
        raise CryptoError("RSA keys below 2048 bits are rejected")
    return key


def public_from_private(private_pem: str) -> str:
    return load_private(private_pem).public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()


def key_bits(pem: str, private: bool = False) -> int:
    return (load_private(pem) if private else load_public(pem)).key_size


def fingerprint(public_pem: str) -> str:
    der = load_public(public_pem).public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    digest = hashlib.sha256(der).hexdigest()
    return ":".join(digest[i:i + 2] for i in range(0, 24, 2))


def encrypt_bundle(public_pem: str, filename: str, data: bytes) -> tuple[bytes, dict]:
    """Return (bundle, info). A fresh AES session key and nonce are used for every call."""
    pub = load_public(public_pem)
    header = json.dumps({"name": os.path.basename(filename) or "payload.bin", "size": len(data),
                         "sha256": sha256_hex(data)}).encode()
    plaintext = struct.pack(">H", len(header)) + header + data

    session_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(NONCE_LEN)
    ciphertext = AESGCM(session_key).encrypt(nonce, plaintext, MAGIC)
    wrapped = pub.encrypt(session_key, _OAEP)

    bundle = MAGIC + struct.pack(">H", len(wrapped)) + wrapped + nonce + ciphertext
    return bundle, {"input_sha256": sha256_hex(data), "wrapped_key_bytes": len(wrapped),
                    "bundle_bytes": len(bundle), "overhead_bytes": len(bundle) - len(data)}


def decrypt_bundle(private_pem: str, bundle: bytes) -> tuple[str, bytes, dict]:
    """Return (filename, data, info). Raises CryptoError when the key or the tag is wrong."""
    if len(bundle) < 6 + NONCE_LEN + 16 or bundle[:4] != MAGIC:
        raise CryptoError("No CipherVeil bundle found in this image")
    priv = load_private(private_pem)
    (wlen,) = struct.unpack(">H", bundle[4:6])
    if wlen != priv.key_size // 8:
        raise CryptoError("This bundle was wrapped for a different key size - wrong private key")
    wrapped = bundle[6:6 + wlen]
    nonce = bundle[6 + wlen:6 + wlen + NONCE_LEN]
    ciphertext = bundle[6 + wlen + NONCE_LEN:]
    try:
        session_key = priv.decrypt(wrapped, _OAEP)
    except Exception as exc:
        raise CryptoError("RSA unwrap failed - this is not the key the message was sent to") from exc
    try:
        plaintext = AESGCM(session_key).decrypt(nonce, ciphertext, MAGIC)
    except InvalidTag as exc:
        raise CryptoError("AES-GCM tag check failed - the data was modified") from exc

    (hlen,) = struct.unpack(">H", plaintext[:2])
    header = json.loads(plaintext[2:2 + hlen])
    data = plaintext[2 + hlen:]
    return header["name"], data, {"embedded_sha256": header["sha256"], "output_sha256": sha256_hex(data),
                                  "match": header["sha256"] == sha256_hex(data), "size": len(data)}
