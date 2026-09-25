"""Contract complexity scoring: readability, legalese density, cross-references, length."""
import re

LEGALESE_TERMS = [
    "hereinafter", "hereto", "hereof", "herein", "heretofore", "thereof", "thereto",
    "whereas", "witnesseth", "notwithstanding", "aforementioned", "aforesaid",
    "pursuant to", "in witness whereof", "party of the first part", "party of the second part",
    "indemnify", "indemnification", "covenant", "wherein", "whereby", "hereunder",
    "null and void", "force majeure", "estoppel", "arbitration", "jurisdiction",
    "notwithstanding anything", "shall not be deemed", "without prejudice",
    "successors and assigns", "sole discretion", "irrevocable", "unconditional",
]

CROSS_REF_RE = re.compile(
    r"\b(?:Section|Clause|Article|Schedule|Annexure|Exhibit)\s+\d+(?:\.\d+)*\b"
    r"|\b(?:herein|hereof|hereto|hereunder|above-mentioned|aforementioned)\b",
    re.IGNORECASE,
)

VOWELS = "aeiouy"


def _count_syllables(word: str) -> int:
    word = word.lower().strip(".,;:!?()[]\"'")
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def flesch_reading_ease(text: str) -> float:
    sentences = _sentences(text)
    words = re.findall(r"[A-Za-z']+", text)
    if not sentences or not words:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    n_sent = len(sentences)
    n_words = len(words)
    score = 206.835 - 1.015 * (n_words / n_sent) - 84.6 * (syllables / n_words)
    return round(max(0.0, min(100.0, score)), 1)


def legalese_density(text: str) -> float:
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    lower = text.lower()
    hits = sum(lower.count(term) for term in LEGALESE_TERMS)
    return round(100.0 * hits / max(len(words), 1), 2)


def cross_reference_count(text: str) -> int:
    return len(CROSS_REF_RE.findall(text))


def avg_sentence_length(text: str) -> float:
    sentences = _sentences(text)
    words = re.findall(r"[A-Za-z']+", text)
    if not sentences:
        return 0.0
    return round(len(words) / len(sentences), 1)


def score_contract(full_text: str, num_clauses: int) -> dict:
    readability = flesch_reading_ease(full_text)  # higher = easier
    legalese = legalese_density(full_text)  # higher = harder
    cross_refs = cross_reference_count(full_text)  # higher = harder
    avg_sent = avg_sentence_length(full_text)  # higher = harder

    # Normalize each component to 0-100 "difficulty" (higher = more complex).
    readability_difficulty = 100 - readability
    legalese_difficulty = min(100.0, legalese * 8)
    cross_ref_difficulty = min(100.0, (cross_refs / max(num_clauses, 1)) * 40)
    sentence_difficulty = min(100.0, max(0.0, (avg_sent - 15) * 3))

    complexity_score = round(
        0.35 * readability_difficulty
        + 0.30 * legalese_difficulty
        + 0.20 * cross_ref_difficulty
        + 0.15 * sentence_difficulty,
        1,
    )

    if complexity_score < 20:
        grade = "A"
    elif complexity_score < 40:
        grade = "B"
    elif complexity_score < 60:
        grade = "C"
    elif complexity_score < 80:
        grade = "D"
    else:
        grade = "F"

    return {
        "complexity_score": complexity_score,
        "complexity_grade": grade,
        "readability_score": readability,
        "legalese_density": legalese,
        "cross_reference_count": cross_refs,
        "avg_sentence_length": avg_sent,
    }
