"""Tokenisation and domain query expansion for keyword (BM25) search over policy wordings."""

from __future__ import annotations

import re
import unicodedata

_TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*")

STOPWORDS = frozenset(
    """a an the and or of to in on for by with from at as is are was were be been being this that these those it
    its if then than any all such under upon into within without which who whom whose what when where how do does
    did can could shall should will would may might must i me my we our you your he she they them their his her
    there here also other only not no nor so very per via etc""".split()
)

# Query-side expansion: plain-language phrasing -> the vocabulary policy wordings actually use.
SYNONYMS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(co-?pay(ment)?s?|copay)\b"), "co payment copayment"),
    (re.compile(r"\b(ped|pre-?existing|preexisting)\b"), "pre existing disease"),
    (re.compile(r"\b(after how long|how long|how many (months|years)|when can i claim|waiting|wait)\b"),
     "waiting period months"),
    (re.compile(r"\b(knee|hip|joint)\s+replacement\b"), "joint replacement surgery arthroplasty"),
    (re.compile(r"\bcataract\b"), "cataract eye lens"),
    (re.compile(r"\broom\b"), "room rent accommodation"),
    (re.compile(r"\bicu\b"), "intensive care unit icu"),
    (re.compile(r"\b(pregnan\w*|deliver\w*|childbirth|maternity|baby)\b"), "maternity newborn"),
    (re.compile(r"\b(day ?care)\b"), "day care treatment"),
    (re.compile(r"\bcashless\b"), "cashless network provider pre authorization"),
    (re.compile(r"\b(reimburse\w*)\b"), "reimbursement claim"),
    (re.compile(r"\b(documents?|papers?|proofs?)\b"), "documents required claim form"),
    (re.compile(r"\b(ayurved\w*|homeopath\w*|unani|siddha|naturopathy)\b"), "ayush"),
    (re.compile(r"\b(sum insured|cover(age)? amount|si)\b"), "sum insured"),
    (re.compile(r"\b(no claim bonus|ncb|bonus)\b"), "cumulative bonus"),
    (re.compile(r"\b(restor\w*|recharge|reload|refill)\b"), "restoration recharge sum insured"),
    (re.compile(r"\b(free ?look|cancel\w*)\b"), "free look period cancellation"),
    (re.compile(r"\b(grace|late payment|renew\w*)\b"), "grace period renewal"),
    (re.compile(r"\b(mental|psychiatr\w*|depression)\b"), "mental illness"),
    (re.compile(r"\b(robotic|modern treatment\w*|stem cell)\b"), "modern treatments"),
    (re.compile(r"\b(home treatment|treatment at home|domiciliary)\b"), "domiciliary home care"),
    (re.compile(r"\b(opd|out-?patient)\b"), "opd out patient"),
    (re.compile(r"\b(teeth|tooth|dental)\b"), "dental treatment"),
    (re.compile(r"\b(spectacles?|glasses|contact lens\w*|lasik)\b"), "spectacles contact lens refractive error"),
    (re.compile(r"\b(bariatric|obesity|weight loss)\b"), "obesity weight control"),
    (re.compile(r"\b(sub-?limits?|cap(ping|ped)?)\b"), "sub limit limit"),
    (re.compile(r"\b(hospitali[sz]ed|admitted|admission)\b"), "hospitalization in patient"),
    (re.compile(r"\b(excluded|not covered|exclusions?)\b"), "exclusion excluded"),
    (re.compile(r"\b(ambulance)\b"), "ambulance road air"),
    (re.compile(r"\b(claim (process|procedure|steps?)|how (do|to) (i )?claim|file a claim)\b"),
     "claim procedure intimation notification"),
    (re.compile(r"\b(intimat\w*|inform the insurer|notify)\b"), "intimation notification of claim"),
]


def _normalise_word(word: str) -> str:
    # British -> American spelling used inconsistently across wordings.
    word = re.sub(r"isation$", "ization", word)
    word = re.sub(r"ise(d|s)?$", r"ize\1", word) if len(word) > 5 else word
    # Light plural / suffix folding.
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).lower().replace("-", " ")
    return [_normalise_word(t) for t in _TOKEN.findall(text) if t not in STOPWORDS and len(t) > 1 or t.isdigit()]


def expand_query(query: str) -> str:
    """Append policy vocabulary for plain-language phrases (used for BM25 only)."""
    lowered = query.lower()
    extra = [replacement for pattern, replacement in SYNONYMS if pattern.search(lowered)]
    return f"{query} {' '.join(extra)}" if extra else query
