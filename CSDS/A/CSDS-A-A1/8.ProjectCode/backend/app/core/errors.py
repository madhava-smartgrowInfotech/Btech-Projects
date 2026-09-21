"""Application errors returned to the client as ``{"detail": ..., "code": ...}``."""

from __future__ import annotations


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, detail: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class NotFound(AppError):
    status_code = 404
    code = "not_found"


class Conflict(AppError):
    status_code = 409
    code = "conflict"


class Unauthorized(AppError):
    status_code = 401
    code = "unauthorized"


class LLMUnavailable(AppError):
    """Gemini could not answer (no key, quota reached, or the service is overloaded)."""

    status_code = 503
    code = "ai_unavailable"


class LLMQuotaExceeded(LLMUnavailable):
    status_code = 429
    code = "ai_quota"
