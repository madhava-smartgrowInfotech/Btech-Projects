"""
ResQAI - account login for the React console.

Adds four endpoints next to the existing API (nothing existing is changed):
  POST /api/auth/register  {name, email, password}  -> {token, user}
  POST /api/auth/login     {email, password}        -> {token, user}
  GET  /api/auth/me        (Bearer token)           -> {user}
  GET  /api/auth/status                             -> {auth_required}

Accounts live in data/users.json (password hashes only). Tokens are signed, expire after 12 hours and are sent as
`Authorization: Bearer <token>`. The existing endpoints stay open by default so the original Flask page keeps working;
set REQUIRE_AUTH=1 to make every /api/* route except /api/health and /api/auth/* demand a valid token.
"""

import json
import os
import re
import secrets
import threading
import time

from flask import Blueprint, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SECRET_FILE = os.path.join(DATA_DIR, ".secret")

TOKEN_MAX_AGE = 12 * 60 * 60  # seconds
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 5 * 60

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
_lock = threading.Lock()
_failed = {}  # email -> [timestamps of recent failed logins]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _secret_key():
    """SECRET_KEY env var, else a random key generated once and kept in data/.secret."""
    env = os.environ.get("SECRET_KEY")
    if env:
        return env
    if not os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "w") as f:
            f.write(secrets.token_hex(32))
    with open(SECRET_FILE) as f:
        return f.read().strip()


_serializer = URLSafeTimedSerializer(_secret_key(), salt="resqai-auth")


def auth_required():
    return os.environ.get("REQUIRE_AUTH", "0").lower() in ("1", "true", "yes")


def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(users):
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    os.replace(tmp, USERS_FILE)


def _public(user):
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def _error(message, status, field=None):
    body = {"error": message}
    if field:
        body["field"] = field
    return jsonify(body), status


def _issue_token(user):
    return _serializer.dumps({"uid": user["id"]})


def user_from_request():
    """Return the user for the request's Bearer token, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        data = _serializer.loads(header[7:], max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return next((u for u in _load_users().values() if u["id"] == data.get("uid")), None)


@bp.route("/status", methods=["GET"])
def status():
    return jsonify({"auth_required": auth_required()})


@bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not 2 <= len(name) <= 60:
        return _error("Enter your name (2 to 60 characters).", 400, "name")
    if not EMAIL_RE.match(email) or len(email) > 120:
        return _error("Enter a valid email address.", 400, "email")
    if len(password) < 8:
        return _error("Use at least 8 characters for the password.", 400, "password")
    if len(password) > 128:
        return _error("The password is too long (128 characters at most).", 400, "password")

    with _lock:
        users = _load_users()
        if email in users:
            return _error("An account with this email already exists. Sign in instead.", 409, "email")
        user = {
            "id": secrets.token_hex(8),
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        users[email] = user
        _save_users(users)
    return jsonify({"token": _issue_token(user), "user": _public(user)}), 201


@bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    now = time.time()
    recent = [t for t in _failed.get(email, []) if now - t < LOCKOUT_SECONDS]
    if len(recent) >= MAX_FAILED_LOGINS:
        wait = int(LOCKOUT_SECONDS - (now - recent[0])) + 1
        return _error(f"Too many failed attempts. Try again in {wait} seconds.", 429)

    user = _load_users().get(email)
    if not user or not check_password_hash(user["password_hash"], password):
        _failed[email] = recent + [now]
        return _error("Incorrect email or password.", 401)

    _failed.pop(email, None)
    return jsonify({"token": _issue_token(user), "user": _public(user)})


@bp.route("/me", methods=["GET"])
def me():
    user = user_from_request()
    if not user:
        return _error("Your session has expired. Sign in again.", 401)
    return jsonify({"user": _public(user)})


def init_app(app):
    """Register the blueprint and (only when REQUIRE_AUTH=1) guard the rest of the API."""
    os.makedirs(DATA_DIR, exist_ok=True)
    app.register_blueprint(bp)

    @app.before_request
    def _guard():
        if not auth_required() or request.method == "OPTIONS":
            return None
        path = request.path
        if not path.startswith("/api/") or path == "/api/health" or path.startswith("/api/auth/"):
            return None
        if user_from_request() is None:
            return _error("Sign in to use this endpoint.", 401)
        return None
