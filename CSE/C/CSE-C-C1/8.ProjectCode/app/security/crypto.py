import base64
import hashlib
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

from app.config import ELECTION_KEY

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def canonical_serialize(obj: dict) -> bytes:
    import json
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

def encrypt_ballot(plaintext: str) -> str:
    aesgcm = AESGCM(ELECTION_KEY)
    nonce = secrets.token_bytes(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    combined = nonce + ct
    return base64.b64encode(combined).decode()

def decrypt_ballot(token: str) -> str:
    aesgcm = AESGCM(ELECTION_KEY)
    raw = base64.b64decode(token.encode())
    nonce = raw[:12]
    ct = raw[12:]
    pt = aesgcm.decrypt(nonce, ct, None)
    return pt.decode()

def generate_ballot_id() -> str:
    return "blt_" + secrets.token_hex(16)

def generate_nonce() -> str:
    return secrets.token_hex(16)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# Ed25519 helpers
def generate_ed25519_keypair():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return priv_bytes.hex(), pub_bytes.hex()

def sign_message(private_hex: str, message: bytes) -> str:
    priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_hex))
    sig = priv.sign(message)
    return sig.hex()

def verify_signature(public_hex: str, message: bytes, sig_hex: str) -> bool:
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        pub.verify(bytes.fromhex(sig_hex), message)
        return True
    except Exception:
        return False

def hash_aadhaar(aadhaar: str) -> str:
    # salted/peppered hash simulation - use SECRET_KEY as pepper
    from app.config import SECRET_KEY
    pepper = SECRET_KEY
    salt = "aegisballot-aadhaar-salt-v1"
    return hashlib.sha256(f"{salt}{pepper}{aadhaar}".encode()).hexdigest()

def mask_aadhaar(aadhaar: str) -> str:
    return "XXXX-XXXX-" + aadhaar[-4:]
