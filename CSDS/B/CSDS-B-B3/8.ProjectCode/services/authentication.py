"""
KnowledgeX AI - Authentication Service
========================================
Handles password hashing, user registration, login and role-based access
control. Uses bcrypt via passlib. No plaintext passwords are ever stored.
"""
import re
import bcrypt

from database.models import User

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte input limit; truncate defensively (still >> min length).
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        pw_bytes = password.encode("utf-8")[:72]
        return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))
    except Exception:
        return False


def validate_registration(name: str, email: str, password: str) -> str:
    """Return an error message string, or empty string if valid."""
    if not name or len(name.strip()) < 2:
        return "Please enter a valid full name."
    if not email or not EMAIL_REGEX.match(email):
        return "Please enter a valid email address."
    if not password or len(password) < 6:
        return "Password must be at least 6 characters long."
    return ""


def register_user(session, name, email, password, role="student"):
    error = validate_registration(name, email, password)
    if error:
        return None, error

    existing = session.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        return None, "An account with this email already exists."

    user = User(
        name=name.strip(),
        email=email.lower().strip(),
        password_hash=hash_password(password),
        role=role,
        is_verified=(role != "mentor"),  # mentors need admin verification
    )
    session.add(user)
    session.flush()
    return user, ""


def authenticate_user(session, email: str, password: str):
    """Return (user, error_message)."""
    user = session.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        return None, "No account found with this email."
    if not user.is_active:
        return None, "This account has been deactivated. Contact admin."
    if not verify_password(password, user.password_hash):
        return None, "Incorrect password."
    return user, ""


def require_role(user, allowed_roles):
    """Role-based access control check."""
    if user is None:
        return False
    return user.role in allowed_roles
