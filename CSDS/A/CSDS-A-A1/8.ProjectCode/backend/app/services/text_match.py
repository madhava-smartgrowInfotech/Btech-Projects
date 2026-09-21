"""Fuzzy text matching used to verify quotes against the policy text (and by the evaluation)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

_WS = re.compile(r"\s+")
_NON_WORD = re.compile(r"[^0-9a-z%₹]+")


def normalise(text: str) -> str:
    """Lower-case, fold ligatures/quotes, join hyphenated line breaks, keep words, digits, % and ₹."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = text.replace("-\n", "").replace("­", "")
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def contains_text(haystack: str, needle: str, min_token_overlap: float = 0.85) -> bool:
    """True when ``needle`` appears in ``haystack`` exactly (after normalisation) or nearly so.

    The near match requires ``min_token_overlap`` of the needle's tokens inside a window of the
    haystack about the needle's length - this tolerates line breaks, table cells and small OCR-like
    differences without accepting unrelated text.
    """
    hay = normalise(haystack)
    ndl = normalise(needle)
    if not ndl:
        return False
    if ndl in hay:
        return True
    need_tokens = ndl.split()
    hay_tokens = hay.split()
    n = len(need_tokens)
    if n == 0 or len(hay_tokens) < max(1, int(n * 0.6)):
        return False
    need = set(need_tokens)
    window = max(n + 4, int(n * 1.5))
    for start in range(0, max(1, len(hay_tokens) - n + 1)):
        seen = set(hay_tokens[start:start + window])
        if len(need & seen) / len(need) >= min_token_overlap:
            return True
    return False


def contains_any(haystack: str, needles: Sequence[str], min_token_overlap: float = 0.85) -> bool:
    return any(contains_text(haystack, n, min_token_overlap) for n in needles if n)


def token_overlap(a: str, b: str) -> float:
    ta, tb = set(normalise(a).split()), set(normalise(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))
