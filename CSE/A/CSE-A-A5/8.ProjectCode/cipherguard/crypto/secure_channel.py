"""
CipherGuard Shield - SecureChannel subsystem
Authenticated encryption: AES-256-GCM + ECDH P-256 + HKDF-SHA256.

- ECDH on NIST P-256 (SECP256R1) via cryptography library
- HKDF-SHA256 to derive 256-bit AES session key
- AES-256-GCM with 12-byte nonce, 16-byte tag
- Full round-trip: encrypt produces (ciphertext, nonce, tag), decrypt verifies tag.
"""
import os
import base64
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


@dataclass
class KeyPair:
    """ECDH P-256 key pair."""
    private_key: ec.EllipticCurvePrivateKey
    public_key: ec.EllipticCurvePublicKey

    @classmethod
    def generate(cls) -> "KeyPair":
        private = ec.generate_private_key(ec.SECP256R1(), default_backend())
        return cls(private_key=private, public_key=private.public_key())

    def public_bytes_raw(self) -> bytes:
        """Return uncompressed point bytes for transport (for demo)."""
        from cryptography.hazmat.primitives import serialization
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

    @staticmethod
    def load_public_from_bytes(data: bytes) -> ec.EllipticCurvePublicKey:
        from cryptography.hazmat.primitives import serialization
        return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), data)


def _derive_aes_key(shared_secret: bytes, info: bytes = b"cipherguard-shield-v1") -> bytes:
    """HKDF-SHA256: derive 32-byte AES-256 key."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info,
    )
    return hkdf.derive(shared_secret)


class SecureChannel:
    """
    SecureChannel: ECDH P-256 key exchange + AES-256-GCM authenticated encryption.

    Usage:
        alice = KeyPair.generate()
        bob = KeyPair.generate()
        # Each side derives same session key:
        alice_key = SecureChannel.derive_session_key(alice.private_key, bob.public_key)
        bob_key   = SecureChannel.derive_session_key(bob.private_key, alice.public_key)
        assert alice_key == bob_key
    """

    @staticmethod
    def derive_session_key(
        private_key: ec.EllipticCurvePrivateKey,
        peer_public_key: ec.EllipticCurvePublicKey,
        info: bytes = b"cipherguard-shield-v1"
    ) -> bytes:
        shared = private_key.exchange(ec.ECDH(), peer_public_key)
        return _derive_aes_key(shared, info=info)

    @staticmethod
    def encrypt(plaintext: bytes, session_key: bytes) -> dict:
        """
        AES-256-GCM encrypt.
        Returns dict with base64-encoded ciphertext, nonce, tag is inside ciphertext.
        We split for UI clarity: AESGCM returns ciphertext+tag combined; we separate last 16 bytes as tag.
        """
        if len(session_key) != 32:
            raise ValueError("session_key must be 32 bytes for AES-256")
        nonce = os.urandom(12)  # 96-bit nonce per NIST
        aesgcm = AESGCM(session_key)
        ct_with_tag = aesgcm.encrypt(nonce, plaintext, None)
        # AESGCM appends 16-byte tag
        ciphertext = ct_with_tag[:-16]
        tag = ct_with_tag[-16:]
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "ciphertext_raw": ciphertext,
            "nonce_raw": nonce,
            "tag_raw": tag,
        }

    @staticmethod
    def decrypt(ciphertext: bytes, nonce: bytes, tag: bytes, session_key: bytes) -> bytes:
        """
        AES-256-GCM decrypt with tag verification. Raises exception on auth failure.
        """
        if len(session_key) != 32:
            raise ValueError("session_key must be 32 bytes for AES-256")
        if len(nonce) != 12:
            raise ValueError("nonce must be 12 bytes")
        if len(tag) != 16:
            raise ValueError("tag must be 16 bytes")
        aesgcm = AESGCM(session_key)
        ct_with_tag = ciphertext + tag
        return aesgcm.decrypt(nonce, ct_with_tag, None)

    @staticmethod
    def encrypt_b64(plaintext: bytes, session_key: bytes) -> dict:
        """Convenience: returns base64 strings only."""
        r = SecureChannel.encrypt(plaintext, session_key)
        return {"ciphertext": r["ciphertext"], "nonce": r["nonce"], "tag": r["tag"]}

    @staticmethod
    def decrypt_b64(ciphertext_b64: str, nonce_b64: str, tag_b64: str, session_key: bytes) -> bytes:
        ct = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        tag = base64.b64decode(tag_b64)
        return SecureChannel.decrypt(ct, nonce, tag, session_key)

    @staticmethod
    def encrypt_with_ephemeral(plaintext: bytes, recipient_public_key: ec.EllipticCurvePublicKey) -> dict:
        """
        One-shot: generate ephemeral keypair, ECDH, encrypt. Returns ephemeral public + encrypted payload.
        Useful for 'transmission to cloud' demo where cloud has long-term key.
        """
        ephemeral = KeyPair.generate()
        session_key = SecureChannel.derive_session_key(ephemeral.private_key, recipient_public_key)
        enc = SecureChannel.encrypt(plaintext, session_key)
        return {
            "ephemeral_public": base64.b64encode(ephemeral.public_bytes_raw()).decode(),
            "ciphertext": enc["ciphertext"],
            "nonce": enc["nonce"],
            "tag": enc["tag"],
            "_ephemeral_private": ephemeral.private_key,  # internal, not serialized
            "_session_key": session_key,
        }


# Module-level cloud keypair (mock cloud endpoint key). Generated at import, persisted per process.
_cloud_keypair: KeyPair | None = None

def get_cloud_keypair() -> KeyPair:
    global _cloud_keypair
    if _cloud_keypair is None:
        _cloud_keypair = KeyPair.generate()
    return _cloud_keypair

def get_cloud_public_key() -> ec.EllipticCurvePublicKey:
    return get_cloud_keypair().public_key
