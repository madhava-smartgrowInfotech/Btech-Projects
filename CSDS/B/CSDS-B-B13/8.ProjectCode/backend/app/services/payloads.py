"""Payload lists and fix recommendations, written and committed (no dataset)."""

SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "'; DROP TABLE users; --",
    "1' UNION SELECT null--",
    "admin'--",
]

# Common weak JWT signing secrets to attempt a signature crack against.
WEAK_JWT_SECRETS = [
    "secret", "password", "123456", "changeme", "jwt", "demopay-secret",
    "admin", "test", "key", "token", "supersecret", "qwerty",
]

# Security headers a hardened API is expected to send.
EXPECTED_SECURITY_HEADERS = [
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "Strict-Transport-Security",
]

# Sensitive field names that should not appear in normal API responses.
SENSITIVE_FIELDS = ["cvv", "ssn", "card_number", "full_card", "pin", "secret"]

RECOMMENDATIONS = {
    "bola": {
        "recommendation": "Enforce object-level authorization: verify the authenticated "
                          "user owns (or may access) the requested object before returning it.",
        "fix_snippet": "obj = db.get(Account, account_id)\n"
                       "if obj.owner_id != current_user.id:\n"
                       "    raise HTTPException(403, 'forbidden')\n"
                       "return obj",
    },
    "broken_auth": {
        "recommendation": "Always verify the JWT signature and expiry with the server secret. "
                          "Never decode tokens with signature verification disabled.",
        "fix_snippet": "claims = jwt.decode(token, SECRET, algorithms=['HS256'])  "
                       "# verify_signature stays on",
    },
    "excessive_data": {
        "recommendation": "Return only the fields the client needs. Use an explicit response "
                          "schema and never expose card numbers, CVV, SSN or secrets.",
        "fix_snippet": "class AccountOut(BaseModel):\n    id: int\n    balance: float\n"
                       "# card_number / cvv / ssn are intentionally omitted",
    },
    "mass_assignment": {
        "recommendation": "Bind request bodies to an explicit allow-list of writable fields. "
                          "Never trust client-supplied is_admin/role/balance.",
        "fix_snippet": "class AccountCreate(BaseModel):\n    label: str\n"
                       "# server sets owner_id, role and balance",
    },
    "function_auth": {
        "recommendation": "Check the caller's role/permission on privileged endpoints. "
                          "Deny by default and require an explicit admin role.",
        "fix_snippet": "if current_user.role != 'admin':\n    raise HTTPException(403)",
    },
    "injection": {
        "recommendation": "Use parameterised queries / an ORM. Never concatenate user input "
                          "into SQL, and do not leak raw queries or driver errors.",
        "fix_snippet": "db.execute(text('SELECT * FROM accounts WHERE owner = :o'), "
                       "{'o': name})",
    },
    "rate_limit": {
        "recommendation": "Apply rate limiting / lockout on authentication and expensive "
                          "endpoints to stop brute force and abuse.",
        "fix_snippet": "@limiter.limit('5/minute')\n@app.post('/login')\n"
                       "def login(...): ...",
    },
    "cors": {
        "recommendation": "Do not combine a wildcard Access-Control-Allow-Origin with "
                          "credentials. Allow-list specific trusted origins.",
        "fix_snippet": "CORSMiddleware(allow_origins=['https://app.example.com'], "
                       "allow_credentials=True)",
    },
    "security_headers": {
        "recommendation": "Send standard security headers: X-Content-Type-Options, "
                          "X-Frame-Options, Content-Security-Policy, HSTS.",
        "fix_snippet": "response.headers['X-Content-Type-Options'] = 'nosniff'",
    },
    "verbose_errors": {
        "recommendation": "Return generic error messages to clients and log details server "
                          "side. Never expose stack traces or raw SQL.",
        "fix_snippet": "except Exception:\n    log.exception('...')\n"
                       "    raise HTTPException(500, 'internal error')",
    },
    "weak_jwt": {
        "recommendation": "Sign tokens with a long, random, secret key (>=32 bytes) stored "
                          "outside source control. Rotate it periodically.",
        "fix_snippet": "JWT_SECRET = os.environ['JWT_SECRET']  # 32+ random bytes",
    },
}
