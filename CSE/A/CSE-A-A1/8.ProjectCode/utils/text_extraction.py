"""
Handles extracting raw text from uploaded educational documents
(PDF / DOCX / TXT), splitting it into retrieval-friendly chunks,
and pulling out candidate topics/keywords for the knowledge repository.
"""
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer

SUBJECT_HINT_PATTERNS = [
    r"(?im)^\s*subject\s*[:\-]\s*(.+)$",
    r"(?im)^\s*course\s*[:\-]\s*(.+)$",
    r"(?im)^\s*unit\s*\d+\s*[:\-]\s*(.+)$",
    r"(?im)^\s*chapter\s*\d+\s*[:\-]\s*(.+)$",
]


def extract_text(filepath):
    """Return plain text content for a pdf/docx/txt file."""
    ext = filepath.rsplit(".", 1)[-1].lower()
    try:
        if ext == "pdf":
            return _extract_pdf(filepath)
        elif ext == "docx":
            return _extract_docx(filepath)
        elif ext == "txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        return f"[Could not extract text: {e}]"
    return ""


def _extract_pdf(filepath):
    from pypdf import PdfReader
    reader = PdfReader(filepath)
    text_parts = []
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(text_parts)


def _extract_docx(filepath):
    import docx
    doc = docx.Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs)


def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text, chunk_size=180, overlap=30):
    """Split text into overlapping word-based chunks for retrieval."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def detect_subject_hints(text):
    """Look for explicit 'Subject:', 'Unit N:', 'Chapter N:' style lines."""
    hints = []
    for pattern in SUBJECT_HINT_PATTERNS:
        for match in re.finditer(pattern, text):
            hint = match.group(1).strip()
            if hint and len(hint) < 120:
                hints.append(hint)
    # de-duplicate, preserve order
    seen = set()
    unique = []
    for h in hints:
        key = h.lower()
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique[:15]


def extract_topics(text, top_n=12):
    """
    Extract candidate topics/keywords from a document using TF-IDF
    over its sentences. Falls back gracefully on very short text.
    """
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    if len(sentences) < 2:
        return detect_subject_hints(text)

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=500,
            token_pattern=r"(?u)\b[A-Za-z][A-Za-z\-]{2,}\b",
        )
        matrix = vectorizer.fit_transform(sentences)
        scores = matrix.sum(axis=0).A1
        terms = vectorizer.get_feature_names_out()
        ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
        topics = [t for t, s in ranked[:top_n] if s > 0]
    except ValueError:
        topics = []

    hints = detect_subject_hints(text)
    # Prefer explicit hints first, then fill with TF-IDF keywords
    combined = hints + [t for t in topics if t.lower() not in {h.lower() for h in hints}]
    return combined[:top_n] if combined else ["General"]


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
