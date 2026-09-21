"""Errors with a plain-language message for the UI."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = logging.getLogger("app.errors")


class AppError(Exception):
    """An expected failure the user can act on."""

    def __init__(self, message: str, status_code: int = 400, details: object | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFound(AppError):
    def __init__(self, what: str):
        super().__init__(f"{what} was not found.", 404)


def _field_name(loc: tuple) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts) or "request"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        body = {"detail": exc.message}
        if exc.details is not None:
            body["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        problems = [f"{_field_name(tuple(e['loc']))}: {e['msg']}" for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": "; ".join(problems), "details": problems})

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        log.exception("Unhandled error", extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Something went wrong on the server. The error has been logged."})
