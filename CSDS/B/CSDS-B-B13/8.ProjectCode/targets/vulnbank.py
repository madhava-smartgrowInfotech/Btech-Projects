"""VulnBank - a second, partially-hardened practice target.

Unlike DemoPay this service fixes most misconfigurations (CORS, security
headers, verbose errors, JWT signature verification) but still ships a few real
flaws, including one BOLA that a generic integer-enumeration scanner will miss
(the id is an unguessable reference). This gives the validation step a realistic
detection rate below 100%.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

JWT_SECRET = secrets.token_urlsafe(48)  # strong, per-process secret
JWT_ALG = "HS256"

app = FastAPI(
    title="VulnBank API",
    version="1.0.0",
    description="Partially hardened sample banking API for security testing.",
    servers=[{"url": f"http://localhost:{os.getenv('VULNBANK_PORT', '12131')}"}],
)

USERS = {
    "carol": {"id": 1, "username": "carol", "password": "password123", "role": "user"},
    "dave": {"id": 2, "username": "dave", "password": "password123", "role": "user"},
}
LOANS = {
    2001: {"id": 2001, "owner_id": 1, "amount": 12000, "ssn": "222-33-4444", "card_number": "4444555566667777"},
    2002: {"id": 2002, "owner_id": 2, "amount": 3000, "ssn": "555-66-7777", "card_number": "4444555566668888"},
}
# Statements keyed by an unguessable reference (integer enumeration will miss these).
STATEMENTS = {
    "st_" + secrets.token_hex(8): {"owner_id": 1, "balance": 12000},
    "st_" + secrets.token_hex(8): {"owner_id": 2, "balance": 3000},
}


def make_token(user: dict) -> str:
    payload = {"sub": user["username"], "user_id": user["id"], "role": user["role"],
               "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def read_token(authorization: str) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])  # signature verified
    except jwt.PyJWTError:
        return None


@app.middleware("http")
async def secure_headers(request: Request, call_next):
    response = await call_next(request)
    # Hardened: specific origin, real security headers.
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5213"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=63072000"
    return response


@app.get("/")
def root():
    return {"service": "VulnBank", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/login")
def login(body: dict):
    # Still missing rate limiting (planted weakness).
    user = USERS.get(body.get("username") or "")
    if not user or user["password"] != body.get("password"):
        return JSONResponse(status_code=401, content={"error": "invalid credentials"})
    return {"token": make_token(user), "user_id": user["id"]}


@app.get("/loans/{loan_id}")
def get_loan(loan_id: int, authorization: str = Header(default="")):
    claims = read_token(authorization)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    loan = LOANS.get(loan_id)
    if not loan:
        return JSONResponse(status_code=404, content={"error": "not found"})
    # BOLA + excessive data (planted): any user reads any loan incl SSN/card.
    return loan


@app.get("/statements/{ref}")
def get_statement(ref: str, authorization: str = Header(default="")):
    claims = read_token(authorization)
    if not claims:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    st = STATEMENTS.get(ref)
    if not st:
        return JSONResponse(status_code=404, content={"error": "not found"})
    # BOLA on an unguessable reference (hard for a generic scanner to enumerate).
    return st


if __name__ == "__main__":
    port = int(os.getenv("VULNBANK_PORT", "12131"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
