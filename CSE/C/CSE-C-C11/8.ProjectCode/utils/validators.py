"""Input validation helpers shared across the app."""
from __future__ import annotations

import re
from datetime import date

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def is_valid_username(username: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_]{3,30}$", username or ""))


def password_strength_errors(password: str) -> list[str]:
    """Return a list of human-readable problems with the password. Empty list = OK."""
    errors = []
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if password and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if password and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if password and not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one digit.")
    if password and not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=]", password):
        errors.append("Password must contain at least one special character.")
    return errors


def is_valid_amount(amount) -> bool:
    try:
        return float(amount) > 0
    except (TypeError, ValueError):
        return False


def is_valid_date(value) -> bool:
    if isinstance(value, date):
        return True
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def sanitize_text(value: str, max_len: int = 255) -> str:
    """Strip whitespace and cap length. SQL injection itself is prevented by
    SQLAlchemy's parameterized queries, but we still cap/trim free-text input."""
    if value is None:
        return ""
    return str(value).strip()[:max_len]
