"""The OWASP API Top 10 scan engine.

Each check is an async function that probes the live target and returns a list of
finding dicts. run_scan() orchestrates the checks, scores the result and persists
findings. Everything here talks to the real target over HTTP - no mocked data.
"""
import json
import re
from dataclasses import dataclass, field

import httpx
import jwt

from .authprofile import AuthContext, resolve_auth
from .owasp import compute_score, owasp_name
from .payloads import (
    EXPECTED_SECURITY_HEADERS, RECOMMENDATIONS, SENSITIVE_FIELDS,
    SQL_INJECTION_PAYLOADS, WEAK_JWT_SECRETS,
)

# Bounded id space probed for BOLA / object access (how real BOLA scanners work).
CANDIDATE_IDS = (
    list(range(1, 6))
    + list(range(100, 106))
    + list(range(1000, 1006))
    + list(range(2000, 2006))
    + list(range(9000, 9006))
)


@dataclass
class ScanContext:
    client: httpx.AsyncClient
    base_url: str
    endpoints: list
    auth: AuthContext
    candidate_ids: list = field(default_factory=list)


def _fill_path(path: str, value) -> str:
    """Substitute every {param} in a path with the given value."""
    return re.sub(r"\{[^}]+\}", str(value), path)


def _url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def build_curl(method: str, url: str, headers: dict | None = None,
               body: dict | None = None) -> str:
    parts = [f"curl -X {method} '{url}'"]
    for k, v in (headers or {}).items():
        parts.append(f"-H '{k}: {v}'")
    if body is not None:
        parts.append("-H 'Content-Type: application/json'")
        parts.append(f"-d '{json.dumps(body)}'")
    return " ".join(parts)


def _finding(check_id: str, title: str, severity: str, owasp_id: str,
             endpoint: str, description: str, evidence: dict, curl: str,
             vuln_key: str, source: str = "owasp") -> dict:
    base = check_id.split(":")[0]
    rec = RECOMMENDATIONS.get(base, {})
    return {
        "check_id": check_id,
        "title": title,
        "severity": severity,
        "owasp_id": owasp_id,
        "owasp_name": owasp_name(owasp_id),
        "endpoint": endpoint,
        "description": description,
        "evidence": evidence,
        "curl": curl,
        "recommendation": rec.get("recommendation", ""),
        "fix_snippet": rec.get("fix_snippet", ""),
        "vuln_key": vuln_key,
        "source": source,
    }


async def _get(ctx: ScanContext, path: str, which: str = "a", params=None):
    try:
        return await ctx.client.get(
            _url(ctx.base_url, path), headers=ctx.auth.headers(which),
            params=params, timeout=10,
        )
    except httpx.HTTPError:
        return None


def _as_json(resp):
    if resp is None:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Discovery: build the pool of valid ids for object-level checks.
# --------------------------------------------------------------------------
async def discover_ids(ctx: ScanContext) -> None:
    pool = set(CANDIDATE_IDS)
    for ep in ctx.endpoints:
        if ep["method"] == "GET" and not ep["id_params"]:
            for which in ("a", "b"):
                data = _as_json(await _get(ctx, ep["path"], which))
                for ident in _extract_ids(data):
                    pool.add(ident)
    ctx.candidate_ids = sorted(i for i in pool if isinstance(i, int))


def _extract_ids(data, depth=0):
    ids = []
    if depth > 4 or data is None:
        return ids
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ("id", "account_id", "tx_id", "loan_id") and isinstance(v, int):
                ids.append(v)
            else:
                ids.extend(_extract_ids(v, depth + 1))
    elif isinstance(data, list):
        for item in data:
            ids.extend(_extract_ids(item, depth + 1))
    return ids


# --------------------------------------------------------------------------
# API1 - Broken Object Level Authorization
# --------------------------------------------------------------------------
async def check_bola(ctx: ScanContext) -> list[dict]:
    findings = []
    for ep in ctx.endpoints:
        if ep["method"] != "GET" or not ep["id_params"]:
            continue
        flagged = False
        for ident in ctx.candidate_ids:
            path = _fill_path(ep["path"], ident)
            resp_a = await _get(ctx, path, "a")
            if resp_a is None or resp_a.status_code != 200:
                continue
            body_a = _as_json(resp_a)
            if not isinstance(body_a, (dict, list)) or not body_a:
                continue
            resp_b = await _get(ctx, path, "b")
            if resp_b is not None and resp_b.status_code == 200:
                body_b = _as_json(resp_b)
                # Two different users retrieving the same object => no ownership check.
                if body_b and body_b == body_a:
                    url = _url(ctx.base_url, path)
                    findings.append(_finding(
                        "bola", f"BOLA on {ep['path']}", "critical", "API1",
                        ep["path"],
                        "Two different authenticated users can retrieve the same object "
                        f"at id {ident}. The endpoint does not enforce object ownership.",
                        {"id_tested": ident, "user_a_status": 200, "user_b_status": 200,
                         "sample": body_a},
                        build_curl("GET", url, ctx.auth.headers("b")),
                        f"bola:{ep['path']}",
                    ))
                    flagged = True
                    break
        if flagged:
            continue
    return findings


# --------------------------------------------------------------------------
# API3 - Excessive Data Exposure
# --------------------------------------------------------------------------
async def check_excessive_data(ctx: ScanContext) -> list[dict]:
    findings = []
    for ep in ctx.endpoints:
        if ep["method"] != "GET":
            continue
        bodies = []
        if ep["id_params"]:
            for ident in ctx.candidate_ids:
                resp = await _get(ctx, _fill_path(ep["path"], ident), "a")
                if resp is not None and resp.status_code == 200:
                    bodies.append((ident, _as_json(resp)))
                    if len(bodies) >= 1:
                        break
        else:
            resp = await _get(ctx, ep["path"], "a")
            if resp is not None and resp.status_code == 200:
                bodies.append((None, _as_json(resp)))
        for ident, body in bodies:
            leaked = _sensitive_hits(body)
            if leaked:
                sample_path = _fill_path(ep["path"], ident) if ident else ep["path"]
                findings.append(_finding(
                    "excessive_data", f"Excessive data exposure on {ep['path']}",
                    "high", "API3", ep["path"],
                    "The response exposes sensitive fields that clients should never "
                    f"receive: {', '.join(sorted(leaked))}.",
                    {"leaked_fields": sorted(leaked), "sample": body},
                    build_curl("GET", _url(ctx.base_url, sample_path), ctx.auth.headers("a")),
                    f"excessive_data:{ep['path']}",
                ))
                break
    return findings


def _sensitive_hits(data, found=None):
    found = set() if found is None else found
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in SENSITIVE_FIELDS:
                found.add(k.lower())
            _sensitive_hits(v, found)
    elif isinstance(data, list):
        for item in data:
            _sensitive_hits(item, found)
    return found


# --------------------------------------------------------------------------
# API3 - Mass Assignment
# --------------------------------------------------------------------------
async def check_mass_assignment(ctx: ScanContext) -> list[dict]:
    findings = []
    injected = {"is_admin": True, "role": "admin", "balance": 999999}
    for ep in ctx.endpoints:
        if ep["method"] != "POST":
            continue
        if _is_login(ep["path"], ctx):
            continue
        body = {"name": "apisentry-test", "label": "apisentry-test", **injected}
        try:
            resp = await ctx.client.post(
                _url(ctx.base_url, _fill_path(ep["path"], 1)),
                headers=ctx.auth.headers("a"), json=body, timeout=10,
            )
        except httpx.HTTPError:
            continue
        data = _as_json(resp)
        if isinstance(data, dict) and resp.status_code < 400:
            echoed = [k for k, v in injected.items() if data.get(k) == v]
            if echoed:
                findings.append(_finding(
                    "mass_assignment", f"Mass assignment on {ep['path']}", "high",
                    "API3", ep["path"],
                    "Client-supplied privileged fields were accepted and reflected: "
                    f"{', '.join(echoed)}. These should be server-controlled.",
                    {"accepted_fields": echoed, "sample": data},
                    build_curl("POST", _url(ctx.base_url, ep["path"]),
                               ctx.auth.headers("a"), body),
                    f"mass_assignment:{ep['path']}",
                ))
    return findings


# --------------------------------------------------------------------------
# API5 - Broken Function Level Authorization
# --------------------------------------------------------------------------
async def check_function_auth(ctx: ScanContext) -> list[dict]:
    findings = []
    for ep in ctx.endpoints:
        if ep["method"] != "GET":
            continue
        is_admin_ep = "admin" in ep["path"].lower() or "admin" in [
            t.lower() for t in ep.get("tags", [])
        ]
        if not is_admin_ep or ep["id_params"]:
            continue
        # Call as the ordinary (non-admin) user A.
        resp = await _get(ctx, ep["path"], "a")
        if resp is not None and resp.status_code == 200:
            findings.append(_finding(
                "function_auth", f"Broken function-level authorization on {ep['path']}",
                "high", "API5", ep["path"],
                "An administrative endpoint is reachable by a normal, non-admin user. "
                "It returned 200 without a role check.",
                {"status": 200, "sample": _as_json(resp)},
                build_curl("GET", _url(ctx.base_url, ep["path"]), ctx.auth.headers("a")),
                f"function_auth:{ep['path']}",
            ))
    return findings


# --------------------------------------------------------------------------
# Injection (mapped to API8 in the 2023 list)
# --------------------------------------------------------------------------
SQL_ERROR_SIGNS = ["operationalerror", "syntax error", "sql", "select * from",
                   "sqlite", "psycopg", "you have an error in your sql"]


async def check_injection(ctx: ScanContext) -> list[dict]:
    findings = []
    for ep in ctx.endpoints:
        if ep["method"] != "GET" or not ep.get("query_params"):
            continue
        flagged = False
        for param in ep["query_params"]:
            for payload in SQL_INJECTION_PAYLOADS:
                resp = await _get(ctx, _fill_path(ep["path"], 1), "a",
                                  params={param: payload})
                if resp is None:
                    continue
                text = resp.text.lower()
                if resp.status_code >= 500 or any(s in text for s in SQL_ERROR_SIGNS):
                    findings.append(_finding(
                        "injection", f"SQL injection on {ep['path']}", "high", "API8",
                        ep["path"],
                        f"A SQL injection payload in '{param}' triggered a database error "
                        "or leaked query, indicating unsafe query construction.",
                        {"param": param, "payload": payload, "status": resp.status_code,
                         "response_excerpt": resp.text[:400]},
                        build_curl("GET",
                                   _url(ctx.base_url, _fill_path(ep["path"], 1))
                                   + f"?{param}={payload}", ctx.auth.headers("a")),
                        f"injection:{ep['path']}",
                    ))
                    flagged = True
                    break
            if flagged:
                break
    return findings


# --------------------------------------------------------------------------
# API4 - Unrestricted Resource Consumption (missing rate limiting on login)
# --------------------------------------------------------------------------
async def check_rate_limit(ctx: ScanContext) -> list[dict]:
    findings = []
    login = _login_endpoint(ctx)
    if not login:
        return findings
    url = _url(ctx.base_url, login)
    statuses = []
    for _ in range(12):
        try:
            resp = await ctx.client.post(
                url, json={"username": "apisentry", "password": "wrong-on-purpose"},
                timeout=10,
            )
            statuses.append(resp.status_code)
        except httpx.HTTPError:
            break
    if statuses and 429 not in statuses:
        findings.append(_finding(
            "rate_limit", f"Missing rate limiting on {login}", "high", "API4",
            login,
            f"Sent {len(statuses)} rapid authentication requests with no 429 / lockout "
            "response. This endpoint can be brute forced or abused.",
            {"requests_sent": len(statuses), "statuses": statuses},
            build_curl("POST", url, None, {"username": "x", "password": "y"}),
            f"rate_limit:{login}",
        ))
    return findings


# --------------------------------------------------------------------------
# API2 - Broken Authentication (forged / unverified token)
# --------------------------------------------------------------------------
async def check_broken_auth(ctx: ScanContext) -> list[dict]:
    findings = []
    forged = jwt.encode(
        {"sub": "attacker", "user_id": 1, "role": "admin"},
        "an-attacker-controlled-secret", algorithm="HS256",
    )
    for ep in ctx.endpoints:
        if ep["method"] != "GET" or ep["id_params"] or ep.get("query_params"):
            continue
        # Must be protected: no token => 401/403.
        try:
            no_tok = await ctx.client.get(_url(ctx.base_url, ep["path"]), timeout=10)
        except httpx.HTTPError:
            continue
        if no_tok.status_code not in (401, 403):
            continue
        # Now try the forged token.
        try:
            forged_resp = await ctx.client.get(
                _url(ctx.base_url, ep["path"]),
                headers={ctx.auth.header_name: f"{ctx.auth.scheme} {forged}"},
                timeout=10,
            )
        except httpx.HTTPError:
            continue
        if forged_resp.status_code == 200:
            findings.append(_finding(
                "broken_auth", f"Broken authentication on {ep['path']}", "critical",
                "API2", ep["path"],
                "A token signed with an attacker-controlled secret was accepted (200). "
                "The server is not verifying the JWT signature.",
                {"no_token_status": no_tok.status_code, "forged_token_status": 200,
                 "sample": _as_json(forged_resp)},
                build_curl("GET", _url(ctx.base_url, ep["path"]),
                           {ctx.auth.header_name: f"{ctx.auth.scheme} {forged}"}),
                f"broken_auth:{ep['path']}",
            ))
    return findings


# --------------------------------------------------------------------------
# API8 - Security Misconfiguration (CORS, headers, verbose errors) + weak JWT
# --------------------------------------------------------------------------
async def check_misconfig(ctx: ScanContext) -> list[dict]:
    findings = []
    probe_path = ctx.endpoints[0]["path"] if ctx.endpoints else "/"
    probe_path = _fill_path(probe_path, 1)

    # CORS
    try:
        cors_resp = await ctx.client.get(
            _url(ctx.base_url, "/"),
            headers={"Origin": "http://evil.example"}, timeout=10,
        )
        acao = cors_resp.headers.get("access-control-allow-origin", "")
        acac = cors_resp.headers.get("access-control-allow-credentials", "")
        if acao == "*" or acao == "http://evil.example":
            findings.append(_finding(
                "cors", "Insecure CORS configuration", "medium", "API8", "/",
                "The server returns a permissive Access-Control-Allow-Origin "
                f"('{acao}')" + (" together with credentials" if acac == "true" else "")
                + ", allowing untrusted origins to read responses.",
                {"access_control_allow_origin": acao,
                 "access_control_allow_credentials": acac},
                build_curl("GET", _url(ctx.base_url, "/"),
                           {"Origin": "http://evil.example"}),
                "cors",
            ))
    except httpx.HTTPError:
        pass

    # Security headers
    try:
        h_resp = await ctx.client.get(_url(ctx.base_url, "/"), timeout=10)
        present = {k.lower() for k in h_resp.headers}
        missing = [h for h in EXPECTED_SECURITY_HEADERS if h.lower() not in present]
        if missing:
            findings.append(_finding(
                "security_headers", "Missing security headers", "medium", "API8", "/",
                "The response is missing recommended security headers: "
                f"{', '.join(missing)}.",
                {"missing_headers": missing,
                 "present_headers": sorted(h_resp.headers.keys())},
                build_curl("GET", _url(ctx.base_url, "/")),
                "security_headers",
            ))
    except httpx.HTTPError:
        pass

    # Verbose errors: send an injection-style payload and look for leaked internals.
    verbose_hit = None
    for ep in ctx.endpoints:
        if ep["method"] != "GET" or not ep.get("query_params"):
            continue
        for param in ep["query_params"]:
            resp = await _get(ctx, _fill_path(ep["path"], 1), "a", params={param: "'"})
            if resp is None:
                continue
            text = resp.text.lower()
            if ("traceback" in text or "operationalerror" in text
                    or "select * from" in text or '"query"' in text):
                verbose_hit = (ep["path"], resp)
                break
        if verbose_hit:
            break
    if verbose_hit:
        path, resp = verbose_hit
        findings.append(_finding(
            "verbose_errors", "Verbose error messages", "medium", "API8", path,
            "An error response leaked internal details (stack trace or raw SQL query) "
            "that help an attacker understand the backend.",
            {"status": resp.status_code, "response_excerpt": resp.text[:400]},
            build_curl("GET", _url(ctx.base_url, _fill_path(path, 1)) + "?input='"),
            "verbose_errors",
        ))

    # Weak JWT secret
    token = ctx.auth.token_a
    if token and token.count(".") == 2:
        cracked = None
        for secret in WEAK_JWT_SECRETS:
            try:
                jwt.decode(token, secret, algorithms=["HS256"],
                           options={"verify_exp": False})
                cracked = secret
                break
            except jwt.PyJWTError:
                continue
        if cracked:
            findings.append(_finding(
                "weak_jwt", "Weak JWT signing secret", "medium", "API2", "/",
                "The JWT is signed with a weak, guessable secret that was recovered "
                "from a small wordlist, allowing token forgery.",
                {"recovered_secret": cracked},
                "# recovered via offline signature test against a common-secret wordlist",
                "weak_jwt",
            ))
    return findings


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _login_endpoint(ctx: ScanContext) -> str | None:
    for ep in ctx.endpoints:
        if ep["method"] == "POST" and _is_login(ep["path"], ctx):
            return ep["path"]
    return None


def _is_login(path: str, ctx: ScanContext) -> bool:
    p = path.lower()
    return any(k in p for k in ("login", "signin", "sign-in", "token", "auth"))


CHECKS = [
    ("Broken object level authorization (BOLA/IDOR)", check_bola),
    ("Excessive data exposure", check_excessive_data),
    ("Mass assignment", check_mass_assignment),
    ("Broken function-level authorization", check_function_auth),
    ("Injection", check_injection),
    ("Missing rate limiting", check_rate_limit),
    ("Broken authentication", check_broken_auth),
    ("Security misconfiguration", check_misconfig),
]


async def run_checks(ctx: ScanContext, progress_cb=None) -> list[dict]:
    findings: list[dict] = []
    total = len(CHECKS) + 1
    if progress_cb:
        progress_cb(int(100 * 1 / total), "Discovering objects and endpoints")
    await discover_ids(ctx)
    for i, (label, fn) in enumerate(CHECKS, start=2):
        if progress_cb:
            progress_cb(int(100 * i / total), f"Testing: {label}")
        try:
            findings.extend(await fn(ctx))
        except Exception as exc:  # a single check failing must not abort the scan
            findings.append(_finding(
                "info", f"Check '{label}' could not complete", "info", "API9", "",
                f"The check raised: {exc}", {"error": str(exc)}, "", "info", "owasp",
            ))
    return findings


async def scan_target(base_url: str, endpoints: list, auth: dict,
                      progress_cb=None) -> dict:
    """Run the full OWASP scan against a target. Returns findings + score."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        auth_ctx = await resolve_auth(base_url, auth or {})
        ctx = ScanContext(client=client, base_url=base_url,
                          endpoints=endpoints, auth=auth_ctx)
        findings = await run_checks(ctx, progress_cb)
    scored = [f for f in findings if f["severity"] != "info"]
    score, grade = compute_score(scored)
    return {"findings": findings, "score": score, "grade": grade}
