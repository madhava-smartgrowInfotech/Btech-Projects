"""Parse PDF/DOCX contracts and split them into clauses with page numbers."""
import re

import fitz  # PyMuPDF
from docx import Document


class ParsedPage:
    __slots__ = ("text", "page_number")

    def __init__(self, text: str, page_number: int):
        self.text = text
        self.page_number = page_number


def extract_pages(file_path: str, content_type: str) -> list[ParsedPage]:
    if file_path.lower().endswith(".pdf") or "pdf" in content_type:
        return _extract_pdf(file_path)
    if file_path.lower().endswith(".docx") or "wordprocessingml" in content_type:
        return _extract_docx(file_path)
    raise ValueError("Unsupported file type. Upload a PDF or DOCX contract.")


def _extract_pdf(file_path: str) -> list[ParsedPage]:
    pages = []
    with fitz.open(file_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            pages.append(ParsedPage(text=text, page_number=i + 1))
    return pages


def _extract_docx(file_path: str) -> list[ParsedPage]:
    doc = Document(file_path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    # DOCX has no native page breaks in python-docx; treat whole doc as page 1.
    return [ParsedPage(text=full_text, page_number=1)]


CLAUSE_HEADER_RE = re.compile(
    r"^\s*(?:(?:Article|Section|Clause)\s+)?(\d{1,2}(?:\.\d{1,2})*)[\.\):]?\s+\S",
    re.MULTILINE,
)


def split_into_clauses(pages: list[ParsedPage]) -> list[dict]:
    """Split page text into clause-sized chunks, numbered headings preferred,
    falling back to paragraph/sentence grouping. Returns list of
    {text, page_number, index_in_doc}."""
    clauses = []
    idx = 0
    for page in pages:
        text = page.text.strip()
        if not text:
            continue
        chunks = _split_page_text(text)
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 25:
                continue
            clauses.append({"text": chunk, "page_number": page.page_number, "index_in_doc": idx})
            idx += 1

    if not clauses:
        raise ValueError("No readable clauses were found in this document.")
    return clauses


def _split_page_text(text: str) -> list[str]:
    headers = list(CLAUSE_HEADER_RE.finditer(text))
    if len(headers) >= 2:
        chunks = []
        for i, m in enumerate(headers):
            start = m.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            chunks.append(text[start:end])
        return chunks

    # Fallback: split on blank-line-delimited paragraphs, merge short ones.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    merged = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) < 400:
            buffer = f"{buffer}\n{p}".strip()
        else:
            if buffer:
                merged.append(buffer)
            buffer = p
    if buffer:
        merged.append(buffer)
    return merged
