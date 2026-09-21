"""
Authentication: signup, login, and Streamlit session-state helpers.

Design notes:
- Passwords are always hashed with bcrypt (utils.security) before storage.
- Login accepts either username or email in the same field.
- All lookups are done through SQLAlchemy's ORM (parameterized queries),
  which protects against basic SQL injection by construction.
"""
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import or_

from database.database import get_session
from database.models import User
from utils.security import hash_password, verify_password
from utils.validators import is_valid_email, is_valid_username, password_strength_errors


@dataclass
class AuthResult:
    success: bool
    message: str
    user_id: int | None = None


def signup(name: str, email: str, username: str, password: str, confirm_password: str) -> AuthResult:
    name = (name or "").strip()
    email = (email or "").strip().lower()
    username = (username or "").strip()

    if not name:
        return AuthResult(False, "Full name is required.")
    if not is_valid_email(email):
        return AuthResult(False, "Please enter a valid email address.")
    if not is_valid_username(username):
        return AuthResult(False, "Username must be 3-30 characters: letters, numbers, underscore only.")
    if password != confirm_password:
        return AuthResult(False, "Passwords do not match.")
    pw_errors = password_strength_errors(password)
    if pw_errors:
        return AuthResult(False, " ".join(pw_errors))

    with get_session() as session:
        existing = session.query(User).filter(
            or_(User.email == email, User.username == username)
        ).first()
        if existing:
            field = "email" if existing.email == email else "username"
            return AuthResult(False, f"An account with this {field} already exists.")

        user = User(
            name=name,
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        session.add(user)
        session.flush()  # populate user.id before session closes/commits
        user_id = user.id

    return AuthResult(True, "Account created successfully. Please log in.", user_id=user_id)


def login(identifier: str, password: str) -> AuthResult:
    identifier = (identifier or "").strip().lower()
    if not identifier or not password:
        return AuthResult(False, "Please enter your username/email and password.")

    with get_session() as session:
        user = session.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()
        if not user or not verify_password(password, user.password_hash):
            return AuthResult(False, "Invalid username/email or password.")
        return AuthResult(True, "Login successful.", user_id=user.id)


def get_current_user(session, user_id: int) -> User | None:
    """Fetch the full User row for the given id within an existing session."""
    return session.query(User).filter(User.id == user_id).first()
