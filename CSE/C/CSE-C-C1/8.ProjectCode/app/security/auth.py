from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(hash_: str, password: str) -> bool:
    try:
        ph.verify(hash_, password)
        # check rehash
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False
