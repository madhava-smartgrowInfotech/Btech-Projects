"""Scope guard - scans may only hit allow-listed hosts."""
from urllib.parse import urlparse

from ..config import settings


def host_of(url: str) -> str:
    parsed = urlparse(url if "://" in url else "http://" + url)
    return (parsed.hostname or "").lower()


def is_in_scope(url: str, allowlist: list[str] | None = None) -> bool:
    allow = [h.lower() for h in (allowlist or settings.scope_allowlist)]
    host = host_of(url)
    if not host:
        return False
    return host in allow


def scope_error(url: str, allowlist: list[str] | None = None) -> str:
    allow = ", ".join(allowlist or settings.scope_allowlist)
    return (
        f"Host '{host_of(url)}' is not in the scan allow-list ({allow}). "
        "Add it to SCOPE_ALLOWLIST only for targets you are authorised to test."
    )
