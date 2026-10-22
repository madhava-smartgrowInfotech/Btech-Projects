"""PeerScope PDF extraction service (PyMuPDF)."""
from __future__ import annotations

import re
from pathlib import Path

SECTION_PATTERNS: dict[str, list[str]] = {
    "summary": [r"^\s*summary\s*$", r"^\s*overview\s*$"],
    "introduction": [r"^\s*1?\s*introduction\s*$", r"^\s*1\s+introduction"],
    "related_work": [r"related work", r"background", r"literature review"],
    "methodology": [r"methodology", r"^\s*method\s*$", r"approach", r"model\b", r"architecture"],
    "experiments": [r"experiment", r"evaluation\b", r"setup"],
    "results": [r"^\s*results?\s*$", r"findings"],
    "discussion": [r"discussion"],
    "conclusion": [r"conclusion", r"future work", r"concluding"],
    "references": [r"^\s*references\s*$", r"^\s*bibliography\s*$"],
}

_WS = re.compile(r"[ \t\xa0]+")


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ _WS.sub(" ", ln).strip() for ln in text.split("\n")]
    # Drop empty runs but keep paragraph breaks.
    out: list[str] = []
    blank = False
    for ln in lines:
        if not ln:
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip()


def extract_pdf(path: str | Path) -> dict:
    """Extract normalized text, pages, sections, references and metadata."""
    import fitz  # PyMuPDF (imported lazily)

    doc = fitz.open(path)
    try:
        pages: list[dict] = []
        full_parts: list[str] = []
        for i, page in enumerate(doc, start=1):
            t = page.get_text("text") or ""
            t = _normalize(t)
            pages.append({"page": i, "text": t, "chars": len(t)})
            full_parts.append(t)
        full_text = "\n\n".join(p for p in full_parts if p).strip()
        words = re.findall(r"[A-Za-z0-9']+", full_text)
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", full_text) if s.strip()]

        lines = full_text.split("\n")
        title = ""
        for ln in lines[:25]:
            s = ln.strip()
            if len(s) >= 12 and len(s) <= 220 and not s.endswith("."):
                title = s
                break
        if not title and lines:
            title = (lines[0] or "Untitled paper").strip()[:220]

        sections = _detect_sections(full_text)
        references = _extract_references(full_text)
        paper_summary = _build_summary(full_text, sections)

        return {
            "title": title or "Untitled paper",
            "paper_summary": paper_summary,
            "full_text": full_text,
            "pages": pages,
            "page_count": len(pages),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "char_count": len(full_text),
            "sections": sections,
            "references": references,
            "reference_count": len(references),
        }
    finally:
        doc.close()


def _detect_sections(full_text: str) -> dict[str, dict]:
    found: dict[str, dict] = {}
    lines = full_text.split("\n")
    # Candidate headings: short lines (<80 chars).
    positions: list[tuple[int, str]] = []
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if not s or len(s) > 80:
            continue
        low = s.lower().strip("0123456789. ")
        for key, pats in SECTION_PATTERNS.items():
            if any(re.search(p, low) for p in pats):
                if key not in found:
                    positions.append((idx, key))
                break
    positions.sort()
    for n, (line_idx, key) in enumerate(positions):
        end = positions[n + 1][0] if n + 1 < len(positions) else len(lines)
        body = "\n".join(lines[line_idx + 1 : end]).strip()
        found[key] = {
            "heading_line": lines[line_idx].strip(),
            "char_count": len(body),
            "word_count": len(re.findall(r"[A-Za-z0-9']+", body)),
            "preview": body[:600],
        }
    return found


def _extract_references(full_text: str) -> list[str]:
    low = full_text.lower()
    m = re.search(r"\n\s*references\s*\n", low)
    if not m:
        m = re.search(r"\n\s*bibliography\s*\n", low)
    if not m:
        # Fallback: bracket-style reference lines.
        cands = re.findall(r"(?m)^\s*\[\d+\].{20,300}$", full_text)
        return [c.strip()[:300] for c in cands[:60]]
    tail = full_text[m.end():]
    items = re.split(r"\n(?=\[\d+\]|\d+\.\s+[A-Z])", tail)
    refs = [re.sub(r"\s+", " ", it).strip()[:300] for it in items if len(it.strip()) > 25]
    return refs[:60]


def _build_summary(full_text: str, sections: dict) -> str:
    for key in ("summary", "introduction"):
        if key in sections and sections[key]["preview"]:
            return sections[key]["preview"][:900]
    paras = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 120]
    return (paras[0] if paras else full_text[:900])[:900]
