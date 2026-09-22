"""Pre-builds the standard spoken phrases (screen guides + scam advice) in English, Hindi and Telugu.

The MP3 files go to backend/app/assets/voice/ and are committed, so these phrases work even
without internet. Personalised warnings (with your name and the amount) are created on demand.
Needs internet (gTTS). Existing files are kept. Run: venv\\Scripts\\python scripts\\build_voice_cache.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("JWT_SECRET", "voice-cache-builder-does-not-sign-tokens-000000")

from app.i18n.messages import ADVICE, GUIDES, LANGS  # noqa: E402
from app.services.voice import PREBUILT, clean_for_speech, synthesize, voice_key  # noqa: E402


def main() -> int:
    PREBUILT.mkdir(parents=True, exist_ok=True)
    phrases = [(lang, text) for group in (GUIDES, ADVICE) for entry in group.values() for lang, text in entry.items() if lang in LANGS]
    made = kept = failed = 0
    for lang, text in phrases:
        key = voice_key(lang, clean_for_speech(text))
        if (PREBUILT / f"{key}.mp3").exists():
            kept += 1
            continue
        try:
            synthesize(text, lang, target_dir=PREBUILT)
            made += 1
        except Exception as exc:  # no internet - the app still works, phrases are made on first use
            failed += 1
            print(f"[!] {lang}: {str(exc)[:80]}")
            if failed >= 3:
                break
    print(f"voice phrases: {made} created, {kept} already present, {failed} failed ({len(phrases)} total) -> {PREBUILT}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
