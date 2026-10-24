"""
ner_processor.py
-----------------
Converts raw OCR/PDF text into structured lab-test records:

    {
        "test_name": "Hemoglobin",
        "result_value": 10.5,
        "unit": "g/dL",
        "reference_low": 12.0,
        "reference_high": 16.0,
        "test_date": datetime | None,
        "confidence_score": 0.0-1.0,
    }

Approach
--------
Lab reports are semi-structured (mostly tabular text), so a hybrid
approach is used rather than free-text NER:

1. Regex-based line parsing extracts the four core fields
   (name / value / unit / range) from each candidate line. This is
   fast, deterministic, and handles the vast majority of real lab
   report layouts.
2. A scikit-learn TF-IDF + cosine-similarity matcher normalizes noisy
   OCR test names (e.g. "Haemogl0bin", "WBC Count") against a curated
   dictionary of common lab test names, improving downstream
   classification and trend-matching consistency.
3. spaCy (if installed) is used only for optional metadata extraction
   -- pulling out the patient name/date line via its NER pipeline --
   which is auxiliary to the core test-value extraction and never
   required for the pipeline to function.

If a CRF-based sequence tagger is added later, it should live in its
own module (e.g. crf_ner.py) implementing the same
`extract_structured_tests(text) -> list[dict]` interface, so it can
be swapped in without touching report_processor.py.
"""

import re
from datetime import datetime

try:
    import spacy
    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        # Model not downloaded; spaCy NER simply becomes a no-op.
        _NLP = None
except ImportError:  # pragma: no cover
    spacy = None
    _NLP = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# Known test name dictionary (used for OCR-noise normalization + fuzzy match)
# ---------------------------------------------------------------------------

KNOWN_TEST_NAMES = [
    "Hemoglobin", "Hematocrit", "RBC Count", "WBC Count", "Platelet Count",
    "MCV", "MCH", "MCHC", "RDW", "Neutrophils", "Lymphocytes", "Monocytes",
    "Eosinophils", "Basophils", "Glucose", "Fasting Glucose", "HbA1c",
    "Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Triglycerides",
    "Urea", "Blood Urea Nitrogen", "Creatinine", "Uric Acid", "Sodium",
    "Potassium", "Chloride", "Calcium", "Phosphorus", "Magnesium",
    "Total Protein", "Albumin", "Globulin", "Bilirubin Total",
    "Bilirubin Direct", "SGOT", "SGPT", "ALT", "AST", "Alkaline Phosphatase",
    "GGT", "TSH", "T3", "T4", "Free T3", "Free T4", "Vitamin D",
    "Vitamin B12", "Iron", "Ferritin", "TIBC", "ESR", "CRP", "PSA",
]

_TEST_NAME_VECTORIZER = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
_KNOWN_NAME_VECTORS = _TEST_NAME_VECTORIZER.fit_transform(KNOWN_TEST_NAMES)

FUZZY_MATCH_THRESHOLD = 0.55


def normalize_test_name(raw_name: str) -> str:
    """
    Clean an OCR-extracted test name and, if it's a close match to a known
    lab test, snap it to the canonical spelling/casing. Otherwise return
    the cleaned raw name unchanged (extraction still succeeds for tests
    outside our reference dictionary).
    """
    cleaned = re.sub(r"[^A-Za-z0-9/() %]", " ", raw_name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" :.-")
    if not cleaned:
        return raw_name.strip()

    try:
        vec = _TEST_NAME_VECTORIZER.transform([cleaned])
        sims = cosine_similarity(vec, _KNOWN_NAME_VECTORS)[0]
        best_idx = sims.argmax()
        if sims[best_idx] >= FUZZY_MATCH_THRESHOLD:
            return KNOWN_TEST_NAMES[best_idx]
    except Exception:
        pass

    # Title-case fallback for unmatched-but-plausible test names
    return cleaned.title() if cleaned.isupper() or cleaned.islower() else cleaned


# ---------------------------------------------------------------------------
# Regex patterns for line-level extraction
# ---------------------------------------------------------------------------

# Matches unit tokens commonly found in lab reports.
_UNIT_RE = r"(?:%|g/dL|mg/dL|mmol/L|IU/L|mIU/L|ng/mL|pg/mL|µg/dL|ug/dL|" \
           r"U/L|mEq/L|cells/cumm|/cumm|10\^\d+/[uµ]L|x10\^\d+/L|fL|pg|" \
           r"mm/hr|sec|K/uL|M/uL|/uL)"

# Stage 1: mandatory name + value (+ optional unit) at the start of the line.
# The rest of the line (the "remainder") is handed to the stage-2 range
# search below, so the range can appear in any common format without
# forcing one giant anchored pattern to match the whole line at once.
_NAME_VALUE_PATTERN = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9()/,.\- ]{1,60}?)\s*[:\-]?\s+"
    r"(?P<value>-?\d+\.?\d*)\s*"
    r"(?P<unit>" + _UNIT_RE + r")?",
    re.IGNORECASE,
)

# Stage 2a: two-sided numeric range, e.g. "12-16", "12 - 16", "12 to 16".
_TWO_SIDED_RANGE_PATTERN = re.compile(
    r"(?P<low>-?\d+\.?\d*)\s*(?:-|to|–|—)\s*(?P<high>-?\d+\.?\d*)"
)

# Stage 2b: one-sided range, e.g. "<5", ">10", "< 200".
_ONE_SIDED_RANGE_PATTERN = re.compile(r"([<>])\s*(-?\d+\.?\d*)")

# Trailing unit that may appear after the range, e.g. "12-16 g/dL".
_TRAILING_UNIT_PATTERN = re.compile(r"(" + _UNIT_RE + r")\s*\)?\s*$", re.IGNORECASE)

# Common test-date formats found on lab reports.
_DATE_PATTERNS = [
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    r"\b(\d{4}-\d{2}-\d{2})\b",
    r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b",
]

_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%y", "%m/%d/%y",
    "%Y-%m-%d", "%d %B %Y", "%d %b %Y",
]

# Lines that are clearly headers/noise, not a test row.
_NOISE_LINE_RE = re.compile(
    r"^(patient|name|age|sex|gender|date|report|lab|address|doctor|dr\.|"
    r"hospital|sample|specimen|page|test\s*name|result|reference|units?|"
    r"parameter|investigation)\b\s*:?\s*$",
    re.IGNORECASE,
)


def extract_test_date(text: str):
    """Find the first plausible test/report date in the document."""
    for pattern in _DATE_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        raw = match.group(1)
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def extract_patient_name(text: str):
    """
    Best-effort patient name extraction. Tries an explicit 'Patient Name:'
    label first, then falls back to spaCy PERSON NER if available.
    """
    label_match = re.search(
        r"(?:patient\s*name|name)\s*[:\-]\s*([A-Za-z .]{2,50})", text, re.IGNORECASE
    )
    if label_match:
        return label_match.group(1).strip()

    if _NLP is not None:
        try:
            doc = _NLP(text[:2000])  # limit for performance
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text
        except Exception:
            pass
    return None


def _parse_one_sided_range(line: str):
    """Handle '<5' / '>10' style reference limits, returning (low, high)."""
    match = _ONE_SIDED_RANGE_PATTERN.search(line)
    if not match:
        return None, None
    symbol, value = match.group(1), float(match.group(2))
    if symbol == "<":
        return None, value
    return value, None


def extract_structured_tests(text: str) -> list:
    """
    Main entry point: parse raw OCR/PDF text into a list of structured
    test-result dicts (name/value/unit/range/date/confidence).

    Lines that don't look like a test row (headers, patient info, blank
    lines) are skipped. Lines that match a numeric value but no range
    are still kept (range fields set to None) since result classification
    can still show the raw value even without a reference range.
    """
    test_date = extract_test_date(text)
    results = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line) < 3:
            continue
        if _NOISE_LINE_RE.match(line):
            continue
        # Skip lines with no digit at all -- can't be a result row
        if not re.search(r"\d", line):
            continue

        match = _NAME_VALUE_PATTERN.match(line)
        if not match:
            continue

        name_raw = match.group("name")
        try:
            value = float(match.group("value"))
        except (TypeError, ValueError):
            continue

        unit = match.group("unit") or ""
        remainder = line[match.end():]

        # A bare "Test 220" line with nothing else after it isn't useful
        # enough to trust unless it at least has a unit -- otherwise it's
        # likely a mis-parsed header/noise line.
        low_val = high_val = None

        range_match = _TWO_SIDED_RANGE_PATTERN.search(remainder)
        if range_match:
            low_val = float(range_match.group("low"))
            high_val = float(range_match.group("high"))
        else:
            low_val, high_val = _parse_one_sided_range(remainder)

        if not unit:
            trailing_unit_match = _TRAILING_UNIT_PATTERN.search(remainder)
            if trailing_unit_match:
                unit = trailing_unit_match.group(1)

        confidence = 0.9 if (low_val is not None and high_val is not None) else 0.6
        if not unit:
            confidence -= 0.1
        if low_val is None and high_val is None and not unit:
            # Too little structure to be confident this is a real test row
            continue

        results.append({
            "test_name": normalize_test_name(name_raw),
            "result_value": value,
            "unit": unit.strip() if unit else None,
            "reference_low": low_val,
            "reference_high": high_val,
            "test_date": test_date,
            "confidence_score": round(max(confidence, 0.1), 2),
        })

    return _deduplicate(results)


def _deduplicate(results: list) -> list:
    """Drop exact duplicate rows that sometimes occur from OCR line-doubling."""
    seen = set()
    deduped = []
    for r in results:
        key = (r["test_name"].lower(), r["result_value"], r["unit"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped
