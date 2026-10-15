"""Encrypted file store: every uploaded scan and derived image is kept Fernet-encrypted on disk."""
import uuid

from ..auth import fernet
from ..config import STORE_DIR


def save(data: bytes) -> str:
    key = uuid.uuid4().hex
    (STORE_DIR / f"{key}.enc").write_bytes(fernet.encrypt(data))
    return key


def load(key: str) -> bytes:
    path = STORE_DIR / f"{key}.enc"
    if not key.isalnum() or not path.exists():
        raise FileNotFoundError(key)
    return fernet.decrypt(path.read_bytes())
