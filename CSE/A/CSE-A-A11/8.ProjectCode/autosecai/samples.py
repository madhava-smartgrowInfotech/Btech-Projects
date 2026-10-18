"""Built-in demo material: a vulnerable pull request diff, a before/after pair and a small demo repository."""

DEMO_DIFF = '''diff --git a/app/users.py b/app/users.py
index 3f2a1b4..9c8d7e2 100644
--- a/app/users.py
+++ b/app/users.py
@@ -1,12 +1,52 @@
 import sqlite3
-from flask import Flask, request, jsonify
+import os
+import hashlib
+import pickle
+import subprocess
+import yaml
+import requests
+import random
+from flask import Flask, request, jsonify, render_template_string

 app = Flask(__name__)
+DB_PASSWORD = "Sup3rS3cret!2024"
+API_KEY = "AKIAIOSFODNN7EXAMPLE"


 def get_db():
     return sqlite3.connect("app.db")
+

+@app.route("/user")
+def find_user():
+    name = request.args.get("name")
+    cur = get_db().cursor()
+    cur.execute(f"SELECT id, email FROM users WHERE name = '{name}'")
+    return jsonify(cur.fetchall())
+
+
+@app.route("/login", methods=["POST"])
+def login():
+    user = request.form["user"]
+    pwd = request.form["password"]
+    digest = hashlib.md5(pwd.encode()).hexdigest()
+    query = "SELECT * FROM users WHERE name = '" + user + "' AND pw = '" + digest + "'"
+    row = get_db().execute(query).fetchone()
+    token = str(random.randint(100000, 999999))
+    return jsonify(ok=bool(row), token=token)
+
+
+@app.route("/ping")
+def ping():
+    host = request.args.get("host", "127.0.0.1")
+    os.system(f"ping -c 1 {host}")
+    return "done"
+
+
+@app.route("/hello")
+def hello():
+    name = request.args.get("name", "")
+    return f"<h1>Hello {name}</h1>"
+
+
+@app.route("/download")
+def download():
+    fname = request.args.get("file")
+    with open(os.path.join("/srv/uploads", fname)) as fh:
+        return fh.read()
+
+
+@app.route("/import", methods=["POST"])
+def import_data():
+    blob = request.data
+    obj = pickle.loads(blob)
+    cfg = yaml.load(request.form["config"])
+    calc = eval(request.args.get("expr"))
+    return jsonify(obj=str(obj), cfg=cfg, calc=calc)
+
+
+@app.route("/fetch")
+def fetch():
+    url = request.args.get("url")
+    return requests.get(url, verify=False).text
+
+
+if __name__ == "__main__":
+    app.run(debug=True)
'''

BEFORE = '''import sqlite3


def get_user(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users WHERE name = ?", (name,))
    return cur.fetchall()
'''

AFTER = '''import sqlite3
import subprocess
import yaml
import hashlib


def get_user(conn, name):
    cur = conn.cursor()
    cur.execute(f"SELECT id, email FROM users WHERE name = '{name}'")
    return cur.fetchall()


def load_settings(path):
    with open(path) as fh:
        return yaml.load(fh)


def checksum(password):
    return hashlib.md5(password.encode()).hexdigest()


def process(order, mode, region, tier, coupon, gift, express, notes):
    total = 0
    if order:
        for item in order:
            if item and mode:
                if region == "EU":
                    if tier == "gold" and coupon:
                        if gift or express:
                            total += item * 2 if not notes else item
                        else:
                            total += item
                    else:
                        total += item + 1
                elif region == "US":
                    total += item
    try:
        return total
    except:
        pass
'''

DEMO_REPO = {
    "app/__init__.py": "",
    "app/main.py": '''"""Application entry point: creates the Flask app and registers routes."""
from flask import Flask
from app.auth import auth_bp
from app.routes import api_bp
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(api_bp, url_prefix="/api")


@app.route("/")
def index():
    """Render the landing page."""
    from flask import render_template
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
''',
    "app/config.py": '''import os


class Config:
    """Application configuration read from environment variables."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    JWT_EXPIRY_MINUTES = 30
''',
    "app/auth.py": '''"""Authentication: login, logout, password hashing, JWT token creation and session checks."""
import hashlib
import hmac
import time
import jwt
from flask import Blueprint, request, session, jsonify
from app.db import get_user_by_name
from app.config import Config

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str, salt: bytes) -> str:
    """Derive a password hash with PBKDF2."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000).hex()


def create_token(user_id: int) -> str:
    """Create a signed JWT access token for the user."""
    payload = {"sub": user_id, "exp": time.time() + Config.JWT_EXPIRY_MINUTES * 60}
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user with username and password and return a token."""
    user = get_user_by_name(request.form["username"])
    if not user:
        return jsonify(error="invalid"), 401
    candidate = hash_password(request.form["password"], user["salt"])
    if not hmac.compare_digest(candidate, user["pw_hash"]):
        return jsonify(error="invalid"), 401
    session["uid"] = user["id"]
    return jsonify(token=create_token(user["id"]))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Clear the session."""
    session.clear()
    return jsonify(ok=True)


def login_required(view):
    """Decorator that rejects unauthenticated requests."""
    def wrapper(*a, **kw):
        if "uid" not in session:
            return jsonify(error="auth required"), 401
        return view(*a, **kw)
    return wrapper
''',
    "app/db.py": '''"""Database access layer (SQLite)."""
import sqlite3


def get_connection():
    """Open a database connection."""
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_user_by_name(name):
    """Fetch a user row by username using a parameterised query."""
    with get_connection() as c:
        return c.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()


def list_orders(user_id):
    """Return all orders that belong to the user."""
    with get_connection() as c:
        return c.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)).fetchall()
''',
    "app/routes.py": '''"""REST API routes for orders and profile."""
from flask import Blueprint, jsonify, request
from app.auth import login_required
from app.db import list_orders

api_bp = Blueprint("api", __name__)


@api_bp.route("/orders")
@login_required
def orders():
    """List the current user's orders."""
    from flask import session
    return jsonify(list_orders(session["uid"]))


@api_bp.route("/profile", methods=["GET", "PUT"])
@login_required
def profile():
    """Read or update the current user's profile."""
    if request.method == "PUT":
        return jsonify(ok=True)
    return jsonify(name="demo")
''',
    "templates/index.html": '<html><body><h1>Shop</h1><nav><a href="/auth/login">Login</a></nav>'
                            '<div id="orders"></div><script src="/static/app.js"></script></body></html>',
    "templates/login.html": '<form method="post" action="/auth/login"><input name="username"><input name="password" type="password">'
                            '<button>Sign in</button></form>',
    "static/app.js": "async function loadOrders(){const r=await fetch('/api/orders');"
                     "document.getElementById('orders').innerText=JSON.stringify(await r.json());}\nloadOrders();\n",
    "tests/test_auth.py": '''from app.auth import hash_password


def test_hash_is_stable():
    assert hash_password("a", b"s") == hash_password("a", b"s")
''',
}
