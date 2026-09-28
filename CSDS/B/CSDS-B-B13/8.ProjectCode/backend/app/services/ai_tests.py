"""F4 - AI-generated business-logic tests.

Gemini reads the parsed API spec and proposes extra business-logic abuse tests
(negative amounts, changed account ids, replayed payment ids). The tests are
constrained to a small executable catalog so the scanner can actually run them
against the live target. When no Gemini key is configured a deterministic
built-in generator produces the same kind of tests, so F4 always works.
"""
import json

import httpx

from ..config import settings
from .authprofile import resolve_auth
from .scanner import _fill_path, _url

TEST_TYPES = {"negative_amount", "foreign_account", "replay", "business_logic"}

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _payment_like(endpoints: list) -> dict | None:
    for ep in endpoints:
        if ep["method"] == "POST" and any(
            k in ep["path"].lower() for k in ("pay", "transfer", "transaction", "charge")
        ):
            return ep
    # fall back to any non-login POST
    for ep in endpoints:
        if ep["method"] == "POST" and "login" not in ep["path"].lower():
            return ep
    return None


def builtin_tests(endpoints: list) -> list[dict]:
    ep = _payment_like(endpoints)
    if not ep:
        return []
    path = ep["path"]
    return [
        {"name": "Negative payment amount", "type": "negative_amount",
         "endpoint": path, "method": "POST",
         "body": {"from_account": 1001, "to": "attacker", "amount": -500, "ref": "neg-1"},
         "rationale": "A negative amount could reverse a transfer and credit the attacker."},
        {"name": "Transfer from another user's account", "type": "foreign_account",
         "endpoint": path, "method": "POST",
         "body": {"from_account": 1003, "to": "attacker", "amount": 100, "ref": "foreign-1"},
         "rationale": "Paying from an account the caller does not own is a broken-object flaw."},
        {"name": "Replayed payment reference", "type": "replay",
         "endpoint": path, "method": "POST",
         "body": {"from_account": 1001, "to": "merchant", "amount": 10, "ref": "replay-1"},
         "rationale": "Re-sending the same payment reference should be rejected (idempotency)."},
    ]


async def gemini_tests(endpoints: list) -> tuple[list[dict], str]:
    """Ask Gemini to propose tests. Returns (tests, generator)."""
    if not settings.gemini_api_key:
        return builtin_tests(endpoints), "builtin"

    endpoint_summary = [
        {"method": e["method"], "path": e["path"],
         "body_fields": e.get("body_fields", [])}
        for e in endpoints
    ]
    prompt = (
        "You are a payment-API security tester. Given these endpoints, propose up to 5 "
        "business-logic abuse tests. Respond with ONLY a JSON array. Each item must have: "
        "name (string), type (one of negative_amount, foreign_account, replay, "
        "business_logic), endpoint (a path from the list), method, body (a JSON object of "
        "request fields), rationale (string). Focus on payment abuse: negative amounts, "
        "transferring from accounts the caller does not own, and replaying payment "
        f"references.\n\nEndpoints:\n{json.dumps(endpoint_summary, indent=2)}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "response_mime_type": "application/json"}}

    for model in (settings.gemini_model, settings.gemini_fallback_model):
        try:
            async with httpx.AsyncClient(timeout=settings.gemini_timeout) as client:
                resp = await client.post(
                    GEMINI_URL.format(model=model),
                    headers={"x-goog-api-key": settings.gemini_api_key,
                             "Content-Type": "application/json"},
                    json=body,
                )
            if resp.status_code != 200:
                continue
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            tests = _sanitise(parsed, endpoints)
            if tests:
                return tests, "gemini"
        except (httpx.HTTPError, KeyError, IndexError, ValueError):
            continue
    # Any failure -> deterministic fallback so F4 still runs.
    return builtin_tests(endpoints), "builtin"


def _sanitise(parsed, endpoints) -> list[dict]:
    valid_paths = {e["path"] for e in endpoints}
    out = []
    if not isinstance(parsed, list):
        return out
    for item in parsed[:5]:
        if not isinstance(item, dict):
            continue
        ttype = item.get("type") if item.get("type") in TEST_TYPES else "business_logic"
        endpoint = item.get("endpoint")
        if endpoint not in valid_paths:
            # snap to a payment-like endpoint if the model invented a path
            pl = _payment_like(endpoints)
            endpoint = pl["path"] if pl else (endpoints[0]["path"] if endpoints else "/")
        out.append({
            "name": str(item.get("name", "AI business-logic test"))[:200],
            "type": ttype,
            "endpoint": endpoint,
            "method": (item.get("method") or "POST").upper(),
            "body": item.get("body") if isinstance(item.get("body"), dict) else {},
            "rationale": str(item.get("rationale", ""))[:500],
        })
    return out


async def run_ai_tests(base_url: str, endpoints: list, auth: dict) -> tuple[list[dict], str]:
    tests, generator = await gemini_tests(endpoints)
    results = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        auth_ctx = await resolve_auth(base_url, auth or {})
        headers = auth_ctx.headers("a")
        for t in tests:
            result, detail = await _execute(client, base_url, t, headers)
            results.append({**t, "result": result, "detail": detail,
                            "generator": generator})
    return results, generator


async def _execute(client, base_url, test, headers) -> tuple[str, str]:
    url = _url(base_url, _fill_path(test["endpoint"], 1))
    method = test.get("method", "POST")
    body = test.get("body", {})
    try:
        r1 = await client.request(method, url, headers=headers, json=body, timeout=10)
    except httpx.HTTPError as exc:
        return "skipped", f"request failed: {exc}"

    accepted = r1.status_code < 400
    text = r1.text[:300]

    if test["type"] == "replay":
        try:
            r2 = await client.request(method, url, headers=headers, json=body, timeout=10)
        except httpx.HTTPError as exc:
            return "skipped", f"replay request failed: {exc}"
        second_ok = r2.status_code < 400
        if accepted and second_ok:
            return "vulnerable", (
                f"Both identical requests were accepted (status {r1.status_code}, "
                f"{r2.status_code}); no idempotency/replay protection. Response: {text}")
        return "safe", f"Replay was rejected (statuses {r1.status_code}, {r2.status_code})."

    if accepted:
        return "vulnerable", (
            f"The abusive request was accepted (status {r1.status_code}). "
            f"Response: {text}")
    return "safe", f"The request was rejected (status {r1.status_code})."
