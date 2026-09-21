"""Check that the Gemini API key and models in .env work.

Usage (from the project root):
    venv\\Scripts\\python scripts\\check_gemini.py

Runs four small checks and prints a clear pass/fail line for each:
  1. the key is present and accepted (lists the models it can use)
  2. the main model answers and returns schema-constrained JSON in English, Hindi and Telugu
  3. the lite model answers
  4. the embedding model returns a vector (only needed when EMBEDDING_PROVIDER=gemini)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from google import genai
    from google.genai import errors, types
except ImportError:
    print("[FAIL] The google-genai package is not installed. Run setup.bat first.")
    sys.exit(1)


class TermTranslation(BaseModel):
    english: str
    hindi: str
    telugu: str


def explain(exc: Exception) -> str:
    if isinstance(exc, errors.APIError):
        code = getattr(exc, "code", None)
        message = getattr(exc, "message", "") or str(exc)
        if code == 400 and "API key" in message:
            return "Google rejected the key. Copy it again from https://aistudio.google.com/apikey (it starts with 'AIza')."
        if code == 403:
            return "The key is not allowed to use this API. Create a new key in AI Studio for a project with the Gemini API enabled."
        if code == 404:
            return "This model name does not exist for your key. Pick one from the list above and update .env."
        if code == 429:
            return "Rate limit or daily quota reached. Wait a minute (or until tomorrow for daily limits) and run again."
        return f"API error {code}: {message}"
    return f"{type(exc).__name__}: {exc}"


def main() -> int:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    main_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    lite_model = os.getenv("GEMINI_LITE_MODEL", "gemini-3.5-flash-lite").strip()
    embed_model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip()
    provider = os.getenv("EMBEDDING_PROVIDER", "local").strip()

    if not key:
        print("[FAIL] GEMINI_API_KEY is empty in .env")
        return 1
    print(f"Key found: {key[:6]}...{key[-4:]} ({len(key)} characters)")

    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=90_000))
    ok = True

    # 1. Key accepted + model list
    try:
        names = []
        for m in client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            if "generateContent" in actions or "embedContent" in actions:
                names.append(m.name.removeprefix("models/"))
        flash = sorted(n for n in names if "flash" in n)
        print(f"[OK]   Key accepted - {len(names)} models available")
        print("       Flash models: " + ", ".join(flash))
        for wanted in (main_model, lite_model):
            if wanted not in names:
                print(f"[WARN] {wanted} is not in your model list")
    except Exception as exc:  # noqa: BLE001 - report any failure in plain words
        print(f"[FAIL] Could not list models - {explain(exc)}")
        return 1

    # 2. Main model (then fallbacks): structured JSON + Hindi/Telugu
    fallbacks = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "").split(",") if m.strip()]
    served_by = None
    for model in [main_model, *fallbacks]:
        for attempt in (1, 2):
            try:
                start = time.perf_counter()
                resp = client.models.generate_content(
                    model=model,
                    contents="Translate the health-insurance term 'waiting period' into Hindi and Telugu.",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TermTranslation,
                        temperature=0,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    ),
                )
                elapsed = time.perf_counter() - start
                parsed: TermTranslation = resp.parsed
                print(f"[OK]   {model} returned JSON in {elapsed:.1f}s: "
                      f"en='{parsed.english}' hi='{parsed.hindi}' te='{parsed.telugu}'")
                served_by = model
                break
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] {model} attempt {attempt} - {explain(exc)}")
                time.sleep(4)
        if served_by:
            break
    if served_by is None:
        ok = False
        print("[FAIL] No model in GEMINI_MODEL / GEMINI_FALLBACK_MODELS returned an answer")
    elif served_by != main_model:
        print(f"[OK]   Fallback works: {served_by} answered while {main_model} was unavailable")

    # 3. Lite model
    try:
        start = time.perf_counter()
        resp = client.models.generate_content(
            model=lite_model,
            contents="Reply with exactly the two words: PolicyLens ready",
            config=types.GenerateContentConfig(
                temperature=0,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        elapsed = time.perf_counter() - start
        print(f"[OK]   {lite_model} replied in {elapsed:.1f}s: {resp.text.strip()!r}")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"[FAIL] {lite_model} - {explain(exc)}")

    # 4. Embeddings (optional)
    try:
        resp = client.models.embed_content(model=embed_model, contents="cataract surgery waiting period")
        dims = len(resp.embeddings[0].values)
        print(f"[OK]   {embed_model} returned a {dims}-dimension vector")
    except Exception as exc:  # noqa: BLE001
        level = "FAIL" if provider == "gemini" else "WARN"
        ok = ok and provider != "gemini"
        print(f"[{level}] {embed_model} - {explain(exc)}"
              + ("" if provider == "gemini" else " (not needed: EMBEDDING_PROVIDER=local)"))

    print("\nAll Gemini checks passed." if ok else "\nSome Gemini checks failed - see the lines above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
