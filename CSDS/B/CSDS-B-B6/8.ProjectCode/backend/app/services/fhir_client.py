"""FHIR REST client the platform uses to talk to hospital servers (service JWT with SMART-style scopes)."""
from datetime import datetime, timedelta, timezone

import httpx
import jwt

from ..config import HOSPITAL_SHARED_SECRET, HOSPITALS


class HospitalError(Exception):
    pass


def service_token(hkey: str, scope: str) -> str:
    return jwt.encode({"iss": "unihealth-platform", "aud": f"hospital-{hkey}", "scope": scope,
                       "exp": datetime.now(timezone.utc) + timedelta(seconds=60)},
                      HOSPITAL_SHARED_SECRET, algorithm="HS256")


def _call(method: str, hkey: str, path: str, scope: str, **kw) -> dict:
    url = f"{HOSPITALS[hkey]['base_url']}{path}"
    try:
        r = httpx.request(method, url, headers={"Authorization": f"Bearer {service_token(hkey, scope)}"}, timeout=30, **kw)
    except httpx.HTTPError as e:
        raise HospitalError(f"{HOSPITALS[hkey]['name']} is unreachable ({e.__class__.__name__})")
    if r.status_code >= 400:
        try:
            msg = r.json()["detail"]["issue"][0]["diagnostics"]
        except Exception:
            msg = r.text[:200]
        raise HospitalError(f"{HOSPITALS[hkey]['name']}: {msg}")
    return r.json()


def get(hkey: str, path: str, scope: str = "system/*.read", **params) -> dict:
    return _call("GET", hkey, path, scope, params=params)


def post(hkey: str, path: str, body: dict | None = None, scope: str = "system/*.write") -> dict:
    return _call("POST", hkey, path, scope, json=body)


def bundle_resources(bundle: dict) -> list[dict]:
    return [e["resource"] for e in bundle.get("entry", [])]


def metadata(hkey: str) -> dict:
    try:
        return httpx.get(f"{HOSPITALS[hkey]['base_url']}/metadata", timeout=5).json()
    except httpx.HTTPError as e:
        raise HospitalError(str(e))
