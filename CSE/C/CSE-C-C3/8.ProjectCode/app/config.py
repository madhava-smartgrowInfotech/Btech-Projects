"""ParkSure application configuration (single source of truth)."""
from __future__ import annotations
import os

APP_NAME = "ParkSure"
APP_VERSION = "1.0.0"

# Server
HOST = "127.0.0.1"
PORT = int(os.getenv("PARKSURE_PORT", "8000"))
DATABASE_URL = os.getenv("PARKSURE_DB", "sqlite:///./parksure.db")

# Auth
JWT_SECRET = os.getenv("PARKSURE_JWT_SECRET", "parksure-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 12
BCRYPT_ROUNDS = 12

# Smart Availability Engine (buffer policy)
BUFFER_INIT = int(os.getenv("PARKSURE_BUFFER_INIT", "1"))
BUFFER_MAX = int(os.getenv("PARKSURE_BUFFER_MAX", "5"))
BUFFER_RESET_HOURS = int(os.getenv("PARKSURE_BUFFER_RESET_HOURS", "24"))

# Driver Trust Score policy
TRUST_START = 3.0
TRUST_MIN = 0.0
TRUST_MAX = 5.0
BENEFIT_STREAK_FOR_REWARD = int(os.getenv("PARKSURE_B", "3"))   # B consecutive Benefits -> +1
WARNINGS_FOR_PENALTY = int(os.getenv("PARKSURE_W", "2"))        # W warnings -> -1
TRUST_SUSPEND_THRESHOLD = float(os.getenv("PARKSURE_TRUST_THRESHOLD", "1.5"))
RECENT_VIOLATION_DAYS = int(os.getenv("PARKSURE_VIOLATION_DAYS", "14"))
SUSPEND_COOLDOWN_HOURS = int(os.getenv("PARKSURE_COOLDOWN_HOURS", "24"))

# Pricing: fee multiplier by trust score (rounded score -> multiplier).
# Lower trust pays more; high trust earns a small discount.
FEE_MULTIPLIER = {0: 1.75, 1: 1.50, 2: 1.25, 3: 1.00, 4: 0.95, 5: 0.90}

# Stripe (test mode). When keys are absent the app uses an internal
# demo checkout so the product remains fully usable offline.
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
APP_BASE_URL = os.getenv("PARKSURE_BASE_URL", f"http://localhost:{PORT}")
