"""Gemini access (google-genai SDK) with JSON-schema output, fallback models, rate limiting and caching.

* ``generate_json`` sends a prompt with a Pydantic response schema and returns the parsed object.
* Models are tried in order: GEMINI_MODEL, then GEMINI_FALLBACK_MODELS. A model that answers
  503/504 (overloaded) or 429 (quota) is retried once, then skipped for a cool-down period.
* Requests are paced to LLM_MAX_RPM.
* Responses can be cached on disk by content hash (``cache=True``) so repeated work - re-running the
  evaluation, re-importing a known PDF - does not spend quota. Cached replies are marked as such.
* Every call is logged to the ``llm_calls`` table for the usage panel.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.core.errors import LLMQuotaExceeded, LLMUnavailable
from app.core.logging import get_logger, log_event

log = get_logger("gemini")
T = TypeVar("T", bound=BaseModel)

_client = None
_client_lock = threading.Lock()
_rate_lock = threading.Lock()
_recent_calls: deque[float] = deque()
_cooldown: dict[str, float] = {}
_thinking_unsupported: set[tuple[str, str]] = set()

COOLDOWN_SECONDS = 600


@dataclass
class CallMeta:
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached: bool = False
    attempts: int = 1

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def get_client():  # noqa: ANN201 - genai.Client
    global _client
    settings = get_settings()
    if not settings.gemini_configured:
        raise LLMUnavailable("No Gemini API key is configured. Add GEMINI_API_KEY to .env and restart PolicyLens.",
                             code="ai_not_configured")
    if _client is None:
        with _client_lock:
            if _client is None:
                from google import genai
                from google.genai import types

                _client = genai.Client(
                    api_key=settings.gemini_api_key,
                    http_options=types.HttpOptions(timeout=settings.gemini_timeout_seconds * 1000),
                )
    return _client


def model_chain(prefer_lite: bool = False) -> list[str]:
    s = get_settings()
    chain = [s.gemini_lite_model, s.gemini_model, *s.gemini_fallback_models] if prefer_lite else [
        s.gemini_model, *s.gemini_fallback_models]
    seen: list[str] = []
    for m in chain:
        if m and m not in seen:
            seen.append(m)
    return seen


def _pace() -> None:
    limit = max(1, get_settings().llm_max_rpm)
    with _rate_lock:
        now = time.time()
        while _recent_calls and now - _recent_calls[0] > 60:
            _recent_calls.popleft()
        if len(_recent_calls) >= limit:
            wait = 60 - (now - _recent_calls[0]) + 0.2
            if wait > 0:
                time.sleep(wait)
        _recent_calls.append(time.time())


def _cache_path(key: str):  # noqa: ANN202
    folder = get_settings().cache_dir / "llm"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{key}.json"


def _record(purpose: str, meta: CallMeta | None, user_id: int | None, ok: bool, error: str | None = None,
            model: str | None = None) -> None:
    try:
        from app.core.db import SessionLocal
        from app.models import LlmCall

        with SessionLocal() as db:
            db.add(LlmCall(
                user_id=user_id, purpose=purpose, model=(meta.model if meta else model) or "unknown",
                input_tokens=meta.input_tokens if meta else None, output_tokens=meta.output_tokens if meta else None,
                latency_ms=meta.latency_ms if meta else 0, ok=ok, cached=bool(meta and meta.cached),
                error=(error or "")[:500] or None,
            ))
            db.commit()
    except Exception:  # noqa: BLE001 - usage logging must never break a request
        log.debug("could not record llm call", exc_info=True)


def _classify_error(exc: Exception) -> tuple[str, str]:
    """-> (kind, message) where kind is retry | quota | fatal."""
    code = getattr(exc, "code", None)
    message = str(getattr(exc, "message", "") or exc)
    lowered = message.lower()
    if code == 429 or "resource_exhausted" in lowered or "quota" in lowered:
        return "quota", message
    if code in (500, 502, 503, 504) or "deadline" in lowered or "unavailable" in lowered or "overloaded" in lowered:
        return "retry", message
    if exc.__class__.__name__ in ("ReadTimeout", "ConnectTimeout", "TimeoutException", "ConnectError"):
        return "retry", message or "timeout"
    return "fatal", message


class _Ping(BaseModel):
    ok: bool


def probe_models() -> dict[str, str]:
    """Send one tiny request to each model in the chain (background, at startup).

    Overloaded models are put in cool-down right away, so the first real question does not wait
    on them. Stops at the first model that answers.
    """
    from google.genai import types

    status: dict[str, str] = {}
    if not get_settings().gemini_configured:
        return status
    client = get_client()
    for model in model_chain():
        start = time.perf_counter()
        try:
            client.models.generate_content(
                model=model, contents="Reply with ok=true.",
                config=types.GenerateContentConfig(
                    temperature=0, response_mime_type="application/json", response_schema=_Ping,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
            status[model] = f"ok ({round((time.perf_counter() - start) * 1000)} ms)"
            _cooldown.pop(model, None)
            break
        except Exception as exc:  # noqa: BLE001
            kind, message = _classify_error(exc)
            status[model] = f"{kind}: {message[:80]}"
            if kind != "fatal":
                _cooldown[model] = time.time() + COOLDOWN_SECONDS
    log_event(log, "model_probe", **{m.replace("-", "_").replace(".", "_"): s for m, s in status.items()})
    return status


def model_health() -> dict[str, object]:
    now = time.time()
    return {m: ("cooling down" if _cooldown.get(m, 0) > now else "available") for m in model_chain()}


def generate_json(
    *,
    prompt: str | list[Any],
    schema: type[T],
    purpose: str,
    system: str | None = None,
    user_id: int | None = None,
    temperature: float = 0.2,
    prefer_lite: bool = False,
    cache: bool = False,
    refresh: bool = False,
    cache_salt: str = "",
    max_output_tokens: int | None = None,
    thinking: str | None = "low",
) -> tuple[T, CallMeta]:
    """Call Gemini with a response schema and return (parsed object, call metadata)."""
    from google.genai import errors as genai_errors
    from google.genai import types

    client = get_client()
    chain = model_chain(prefer_lite)
    prompt_text = prompt if isinstance(prompt, str) else json.dumps(prompt, ensure_ascii=False, default=str)
    cache_key = hashlib.sha256(
        "|".join([purpose, schema.__name__, json.dumps(schema.model_json_schema(), sort_keys=True), system or "",
                  prompt_text, str(temperature), cache_salt]).encode("utf-8")
    ).hexdigest()[:40]

    if cache and not refresh:
        path = _cache_path(cache_key)
        if path.exists():
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                parsed = schema.model_validate(stored["data"])
                meta = CallMeta(model=stored.get("model", chain[0]), latency_ms=0, cached=True,
                                input_tokens=stored.get("input_tokens"), output_tokens=stored.get("output_tokens"))
                _record(purpose, meta, user_id, ok=True)
                return parsed, meta
            except (ValidationError, KeyError, json.JSONDecodeError):
                path.unlink(missing_ok=True)

    now = time.time()
    active = [m for m in chain if _cooldown.get(m, 0) < now] or chain
    last_error: tuple[str, str] = ("retry", "No model answered")
    attempts = 0

    for model in active:
        for attempt in (1, 2):
            attempts += 1
            _pace()
            config_kwargs: dict[str, Any] = dict(
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=schema,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            if system:
                config_kwargs["system_instruction"] = system
            if max_output_tokens:
                config_kwargs["max_output_tokens"] = max_output_tokens
            if thinking and (model, thinking) not in _thinking_unsupported:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)
            start = time.perf_counter()
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt, config=types.GenerateContentConfig(**config_kwargs)
                )
                latency = round((time.perf_counter() - start) * 1000)
                parsed = resp.parsed
                if parsed is None:
                    text = (resp.text or "").strip()
                    if not text:
                        raise ValueError("Empty response from the model")
                    parsed = schema.model_validate_json(text)
                elif not isinstance(parsed, schema):
                    parsed = schema.model_validate(parsed)
                usage = getattr(resp, "usage_metadata", None)
                meta = CallMeta(
                    model=model, latency_ms=latency, attempts=attempts,
                    input_tokens=getattr(usage, "prompt_token_count", None),
                    output_tokens=getattr(usage, "candidates_token_count", None),
                )
                _record(purpose, meta, user_id, ok=True)
                log_event(log, "llm_ok", purpose=purpose, model=model, ms=latency,
                          tokens_in=meta.input_tokens, tokens_out=meta.output_tokens)
                if cache:
                    _cache_path(cache_key).write_text(json.dumps({
                        "model": model, "input_tokens": meta.input_tokens, "output_tokens": meta.output_tokens,
                        "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "data": parsed.model_dump(mode="json"),
                    }, ensure_ascii=False), encoding="utf-8")
                return parsed, meta
            except genai_errors.APIError as exc:
                kind, message = _classify_error(exc)
                if getattr(exc, "code", None) == 400 and "thinking" in message.lower():
                    _thinking_unsupported.add((model, thinking or ""))
                    continue
                last_error = (kind, message)
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                last_error = ("retry", f"Invalid response: {exc}")
            except Exception as exc:  # noqa: BLE001 - network errors, timeouts
                last_error = _classify_error(exc)
            log_event(log, "llm_error", purpose=purpose, model=model, attempt=attempt, kind=last_error[0],
                      error=last_error[1][:160])
            _record(purpose, None, user_id, ok=False, error=last_error[1], model=model)
            if last_error[0] == "fatal":
                raise LLMUnavailable(f"The AI service rejected the request: {last_error[1][:200]}")
            overloaded = "high demand" in last_error[1].lower() or "overloaded" in last_error[1].lower()
            if attempt == 1 and last_error[0] == "retry" and not overloaded:
                time.sleep(2.0)  # a network blip or timeout: one quick retry on the same model
                continue
            break  # overloaded or out of quota: move straight to the next model
        _cooldown[model] = time.time() + COOLDOWN_SECONDS

    if last_error[0] == "quota":
        raise LLMQuotaExceeded(
            "The Gemini free-tier limit has been reached for now. Please wait a minute (or until tomorrow for the "
            "daily limit) and try again."
        )
    raise LLMUnavailable("The AI service is busy right now. Please try again in a moment.")
