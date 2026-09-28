"""DemoPay - a deliberately vulnerable payment API used as a practice target.

WARNING: This service is insecure on purpose. Every endpoint below contains a
planted weakness so APISentry has something real to detect. Never expose it to a
public network - it binds to localhost only.

Planted weaknesses (see targets/demopay_vulns.json for the machine-readable list):
  * BOLA on /accounts/{account_id} and /transactions/{tx_id}
  * Broken authentication on /me (JWT signature is not verified)
  * Excessive data exposure on /accounts/{account_id} (returns card number, CVV, SSN)
  * Mass assignment on POST /accounts (accepts is_admin / role from the body)
  * Broken function-level authorization on /admin/users (no role check)
  * SQL injection on /accounts/search
  * Missing rate limiting on /login
  * Security misconfiguration: wildcard CORS, missing security headers, verbose errors
  * Weak JWT signing secret
"""
import os
import traceback
from datetime import datetime, timedelta, timezone

import jwt
import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

# Deliberately weak, guessable signing secret (planted weakness).
JWT_SECRET = "demopay-secret"
JWT_ALG = "HS256"

app = FastAPI(
    title="DemoPay API",
    version="1.0.0",
    description="Sample payment API for security testing (intentionally vulnerable).",
    servers=[{"url": f"http://localhost:{os.getenv('DEMOPAY_PORT', '12130')}"}],
)

# --- Seed data -------------------------------------------------------------
USERS = {
    "alice": {"id": 1, "username": "alice", "password": "password123", "role": "user"},
    "bob": {"id": 2, "username": "bob", "password": "password123", "role": "user"},
    "admin": {"id": 3, "username": "admin", "password": "admin123", "role": "admin"},
}

ACCOUNTS = {
    1001: {"id": 1001, "owner_id": 1, "owner": "alice", "balance": 5200.50,
           "card_number": "4111111111111111", "cvv": "312", "ssn": "111-22-3333"},
    1002: {"id": 1002, "owner_id": 2, "owner": "bob", "balance": 830.00,
           "card_number": "4222222222222222", "cvv": "744", "ssn": "444-55-6666"},
    1003: {"id": 1003, "owner_id": 3, "owner": "admin", "balance": 99000.00,
           "card_number": "4333333333333333", "cvv": "901", "ssn": "777-88-9999"},
}

TRANSACTIONS = {
    9001: {"id": 9001, "account_id": 1001, "amount": -200.0, "to": "merchant:coffee", "ref": "tx-9001"},
    9002: {"id": 9002, "account_id": 1002, "amount": -50.0, "to": "merchant:books", "ref": "tx-9002"},
    9003: {"id": 9003, "account_id": 1003, "amount": -5000.0, "to": "merchant:travel", "ref": "tx-9003"},
}

PROCESSED_PAYMENTS: set[str] = set()


def make_token(user: dict) -> str:
    payload = {
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def read_token(authorization: str, verify: bool = True) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        # When verify=False the signature is NOT checked (planted weakness).
        return jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALG],
            options={"verify_signature": verify},
        )
    except jwt.PyJWTError:
        return None


# --- Middleware: wildcard CORS + missing security headers (misconfig) -------
@app.middleware("http")
async def insecure_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:  # verbose error handler (planted weakness)
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "traceback": tb},
        )
    # Wildcard CORS together with credentials (planted weakness).
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    # Note: deliberately NOT setting X-Content-Type-Options, X-Frame-Options,
    # Strict-Transport-Security or Content-Security-Policy.
    return response


@app.get("/")
def root():
    return {"service": "DemoPay", "status": "ok",
            "note": "Intentionally vulnerable sample payment API."}


@app.get("/health")
def health():
    return {"status": "healthy"}


# --- Auth: no rate limiting on login (planted weakness) --------------------
@app.post("/login")
def login(body: dict):
    username = body.get("username")
    password = body.get("password")
    user = USERS.get(username or "")
    if not user or user["password"] != password:
        return JSONResponse(status_code=401, content={"error": "invalid credentials"})
    return {"token": make_token(user), "user_id": user["id"], "role": user["role"]}


# --- /me: signature not verified (broken authentication) -------------------
@app.get("/me")
def me(authorization: str = Header(default="")):
    claims = read_token(authorization, verify=False)  # <-- not verified
    if not claims:
        return JSONResponse(status_code=401, content={"error": "missing token"})
    return {"username": claims.get("sub"), "user_id": claims.get("user_id"),
            "role": claims.get("role")}


# --- Accounts --------------------------------------------------------------
@app.get("/accounts")
def list_accounts(authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    mine = [a for a in ACCOUNTS.values() if a["owner_id"] == claims.get("user_id")]
    return {"accounts": [{"id": a["id"], "balance": a["balance"]} for a in mine]}


@app.get("/accounts/search")
def search_accounts(name: str = "", authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    # Planted SQL injection: user input concatenated into a query string.
    query = f"SELECT * FROM accounts WHERE owner = '{name}'"
    if "'" in name or "--" in name or " OR " in name.upper():
        # Simulate a database driver leaking the raw query on malformed input.
        return JSONResponse(
            status_code=500,
            content={"error": "OperationalError: near syntax error in SQL",
                     "query": query},
        )
    results = [a for a in ACCOUNTS.values() if a["owner"] == name]
    return {"query": query, "results": results}


@app.get("/accounts/{account_id}")
def get_account(account_id: int, authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    account = ACCOUNTS.get(account_id)
    if not account:
        return JSONResponse(status_code=404, content={"error": "not found"})
    # BOLA: no check that the account belongs to the caller.
    # Excessive data exposure: returns card_number, cvv, ssn in full.
    return account


@app.post("/accounts")
def create_account(body: dict, authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    new_id = max(ACCOUNTS) + 1
    # Mass assignment: whatever the client sends is trusted, including is_admin,
    # role and balance, which should be server-controlled.
    account = {"id": new_id, "owner_id": claims.get("user_id"),
               "owner": claims.get("sub"), "balance": 0.0}
    account.update(body)  # <-- planted weakness
    ACCOUNTS[new_id] = account
    return account


# --- Transactions: BOLA ----------------------------------------------------
@app.get("/transactions/{tx_id}")
def get_transaction(tx_id: int, authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    tx = TRANSACTIONS.get(tx_id)
    if not tx:
        return JSONResponse(status_code=404, content={"error": "not found"})
    # BOLA: any authenticated user can read any transaction.
    return tx


# --- Payments: business-logic flaws (for AI-generated tests) ---------------
@app.post("/payments")
def make_payment(body: dict, authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    from_account = body.get("from_account")
    amount = body.get("amount")
    ref = body.get("ref", "")
    # No validation: negative amounts, other people's accounts and replayed
    # payment references are all accepted (planted business-logic weaknesses).
    replayed = ref in PROCESSED_PAYMENTS
    if ref:
        PROCESSED_PAYMENTS.add(ref)
    return {"status": "processed", "from_account": from_account, "amount": amount,
            "ref": ref, "replayed": replayed}


# --- Admin: broken function-level authorization ----------------------------
@app.get("/admin/users")
def admin_users(authorization: str = Header(default="")):
    claims = read_token(authorization, verify=True)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    # No role check: any authenticated user reaches this admin endpoint, which
    # also leaks password material.
    return {"users": [
        {"id": u["id"], "username": u["username"], "role": u["role"],
         "password": u["password"]}
        for u in USERS.values()
    ]}


if __name__ == "__main__":
    port = int(os.getenv("DEMOPAY_PORT", "12130"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
