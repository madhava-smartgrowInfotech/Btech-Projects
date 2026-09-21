"""PDF -> ordered text lines with page, position and font information (PyMuPDF).

Handles what real policy wordings throw at us:
  * running headers/footers repeated on every page (removed),
  * two-column layouts (read left column, then right column, per band),
  * justified text that PyMuPDF splits into one "line" per word (re-joined),
  * clause numbers printed as a separate span from their text (re-joined),
  * scanned pages without a text layer (reported so the upload can be rejected).
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


@dataclass
class Line:
    page: int  # 1-based
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    size: float
    bold: bool
    column: int = 0  # 0 = left/single, 1 = right, -1 = spanning
    kind: str = "text"  # text | table (one table row, cells joined with " | ")
    bold_lead: str = ""  # leading bold run when the rest of the line is regular ("Accident:" + definition)
    bold_chars: int = 0
    total_chars: int = 0

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


@dataclass
class ParsedPdf:
    page_count: int
    page_sizes: list[tuple[float, float]]
    lines: list[Line]
    two_column: bool
    body_size: float
    text_pages: int
    removed_furniture: int
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        return sum(len(line.text.split()) for line in self.lines)


class ScannedPdfError(ValueError):
    """The PDF has (almost) no text layer - it is a scan or an image export."""


_DIGITS = re.compile(r"\d+")
_WS = re.compile(r"[ \t\u00a0]+")
_BULLET_ONLY = re.compile(r"^[\u2022\u25cf\u25aa\u25a0\u2013\-\*\u00b7]+$")
_UIN = re.compile(r"\b[A-Z]{5,9}\d{5}V\d{6}\b")


_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _clean(text: str) -> str:
    text = _CONTROL.sub(" ", text).replace("\u00ad", "").replace("\ufb01", "fi").replace("\ufb02", "fl").replace("\ufb00", "ff")
    text = text.replace("\ufb03", "ffi").replace("\ufb04", "ffl").replace("\u2011", "-").replace("\t", " ")
    return _WS.sub(" ", text).strip()


def _is_bold_span(span: dict) -> bool:
    font = span.get("font", "").lower()
    return bool(span.get("flags", 0) & 16) or "bold" in font or "semibold" in font or "black" in font


def _letter_spaced(text: str) -> bool:
    tokens = text.split()
    if len(tokens) < 4:
        return False
    singles = sum(1 for t in tokens if len(t) == 1 and t.isalpha())
    return singles / len(tokens) >= 0.6


def _respace(chars: list[dict]) -> str:
    """Rebuild letter-spaced text ("S P E C I F I C") from character positions ("SPECIFIC")."""
    glyphs = [c for c in chars if not c["c"].isspace()]
    if len(glyphs) < 2:
        return "".join(c["c"] for c in glyphs)
    gaps = [b["bbox"][0] - a["bbox"][2] for a, b in zip(glyphs, glyphs[1:])]
    ordered = sorted(gaps)
    typical = ordered[len(ordered) // 2]
    size = max(1.0, glyphs[0]["bbox"][3] - glyphs[0]["bbox"][1])
    threshold = max(typical * 1.6, typical + size * 0.18)
    out = glyphs[0]["c"]
    for gap, glyph in zip(gaps, glyphs[1:]):
        out += (" " if gap > threshold else "") + glyph["c"]
    return out


def _raw_lines(page: pymupdf.Page, pno: int) -> list[Line]:
    out: list[Line] = []
    data = page.get_text("rawdict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE | pymupdf.TEXT_MEDIABOX_CLIP)
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("chars")]
            if not spans:
                continue
            # Skip vertical/rotated text (side stamps, watermarks).
            direction = line.get("dir", (1.0, 0.0))
            if abs(direction[1]) > 0.2:
                continue
            span_texts = ["".join(c["c"] for c in s["chars"]) for s in spans]
            text = _clean("".join(span_texts))
            if not text or _BULLET_ONLY.match(text):
                continue
            if _letter_spaced(text):
                text = _clean(_respace([c for s in spans for c in s["chars"]]))

            bold_chars = sum(len(t.strip()) for s, t in zip(spans, span_texts) if _is_bold_span(s))
            total_chars = sum(len(t.strip()) for t in span_texts) or 1
            lead = ""
            for s, t in zip(spans, span_texts):
                if not t.strip():
                    lead += t
                    continue
                if not _is_bold_span(s):
                    break
                lead += t
            lead = _clean(lead)
            bold = bold_chars / total_chars >= 0.6
            bold_lead = lead if (lead and not bold and len(lead) >= 3) else ""

            x0, y0, x1, y1 = line["bbox"]
            out.append(Line(page=pno, text=text, x0=x0, y0=y0, x1=x1, y1=y1,
                            size=round(max(s["size"] for s in spans), 1), bold=bold,
                            bold_lead=bold_lead, bold_chars=bold_chars, total_chars=total_chars))
    return out


def _furniture_keys(pages: list[list[Line]], heights: list[float]) -> set[str]:
    """Text repeated in the top/bottom margin of many pages = running header/footer."""
    counter: Counter[str] = Counter()
    for lines, height in zip(pages, heights):
        seen: set[str] = set()
        for line in lines:
            if line.y1 < height * 0.12 or line.y0 > height * 0.88:
                key = _DIGITS.sub("#", line.text.lower())
                if key not in seen:
                    seen.add(key)
                    counter[key] += 1
    threshold = max(2, int(len(pages) * 0.35))
    return {key for key, count in counter.items() if count >= threshold}


def _is_page_number(line: Line, height: float) -> bool:
    if not (line.y1 < height * 0.1 or line.y0 > height * 0.9):
        return False
    return bool(re.fullmatch(r"(page\s*)?\d+(\s*(/|of)\s*\d+)?", line.text.lower()))


def _page_is_two_column(lines: list[Line], width: float) -> bool:
    mid = width / 2
    prose = [ln for ln in lines if ln.kind == "text" and len(ln.text.split()) >= 5]
    if len(prose) < 8:
        return False
    left = sum(1 for ln in prose if ln.x1 <= mid + 12)
    right = sum(1 for ln in prose if ln.x0 >= mid - 12)
    crossing = len(prose) - left - right
    return left >= 0.25 * len(prose) and right >= 0.25 * len(prose) and crossing <= 0.12 * len(prose)


def _merge_same_baseline(lines: list[Line]) -> list[Line]:
    """Join fragments that sit on the same baseline (justified words, clause numbers + text)."""
    merged: list[Line] = []
    for line in sorted(lines, key=lambda ln: (round(ln.y0 / 2.5), ln.x0)):
        prev = merged[-1] if merged else None
        if (
            prev is not None
            and prev.kind == "text"
            and line.kind == "text"
            and abs(prev.y0 - line.y0) < 3.0
            and abs(prev.y1 - line.y1) < 4.0
            and line.x0 >= prev.x1 - 2
            and line.x0 - prev.x1 < 60
        ):
            if not prev.bold_lead and prev.bold and not line.bold:
                prev.bold_lead = prev.text  # "Accident:" (bold) + "An accident means..." (regular)
            prev.text = f"{prev.text} {line.text}"
            prev.x1 = max(prev.x1, line.x1)
            prev.y0 = min(prev.y0, line.y0)
            prev.y1 = max(prev.y1, line.y1)
            prev.size = max(prev.size, line.size)
            prev.bold_chars += line.bold_chars
            prev.total_chars += line.total_chars
            prev.bold = prev.bold_chars / max(1, prev.total_chars) >= 0.6
            continue
        merged.append(Line(**line.__dict__))
    return merged


def _order_page(lines: list[Line], width: float, two_column: bool) -> list[Line]:
    if not two_column:
        for ln in lines:
            ln.column = 0
        return _merge_same_baseline(lines)

    mid = width / 2
    for ln in lines:
        if ln.x1 <= mid + 12:
            ln.column = 0
        elif ln.x0 >= mid - 12:
            ln.column = 1
        else:
            ln.column = -1

    # Rows of spanning lines split the page into horizontal bands;
    # each band is read left column first, then right column.
    rows: list[list[Line]] = []
    for ln in sorted((ln for ln in lines if ln.column == -1), key=lambda ln: ln.y0):
        if rows and abs(rows[-1][0].y0 - ln.y0) < 3:
            rows[-1].append(ln)
        else:
            rows.append([ln])

    ordered: list[Line] = []
    band_top = float("-inf")
    for row in [*rows, None]:
        boundary = row[0].y0 if row else float("inf")
        band = [ln for ln in lines if ln.column in (0, 1) and band_top <= ln.y0 < boundary]
        for col in (0, 1):
            ordered.extend(_merge_same_baseline([ln for ln in band if ln.column == col]))
        if row:
            ordered.extend(_merge_same_baseline(row))
            band_top = boundary
    return ordered


def _table_lines(page: pymupdf.Page, pno: int, body_size_hint: float = 10.0) -> list[Line]:
    """Ruled tables -> one Line per row (cells joined with " | "), so rows stay readable."""
    try:
        found = page.find_tables()
    except Exception:  # noqa: BLE001 - table detection is best-effort
        return []
    rows_out: list[Line] = []
    page_area = page.rect.width * page.rect.height or 1.0
    for table in found.tables:
        if table.row_count < 2 or table.col_count < 2:
            continue
        cells = table.extract()
        cell_words = [len((c or "").split()) for row in cells for c in row]
        x0, y0, x1, y1 = table.bbox
        area = (x1 - x0) * (y1 - y0) / page_area
        # Page borders and column frames are often detected as giant "tables" of prose - skip those.
        if max(cell_words, default=0) > 60 or (area > 0.7 and table.row_count < 5):
            continue
        for row_idx, row in enumerate(cells):
            values = [_clean((c or "").replace("\n", " ")) for c in row]
            values = [v for v in values if v]
            if not values:
                continue
            try:
                x0, y0, x1, y1 = table.rows[row_idx].bbox
            except (IndexError, AttributeError):
                x0, y0, x1, y1 = table.bbox
            rows_out.append(Line(page=pno, text=" | ".join(values), x0=x0, y0=y0, x1=x1, y1=y1,
                                 size=body_size_hint, bold=False, kind="table"))
    return rows_out


def _inside(line: Line, boxes: list[tuple[float, float, float, float]]) -> bool:
    cx, cy = (line.x0 + line.x1) / 2, (line.y0 + line.y1) / 2
    return any(b[0] - 1 <= cx <= b[2] + 1 and b[1] - 1 <= cy <= b[3] + 1 for b in boxes)


def parse_pdf(path: str | Path) -> ParsedPdf:
    doc = pymupdf.open(str(path))
    if doc.needs_pass:
        raise ValueError("This PDF is password-protected. Please upload an unlocked copy.")
    try:
        heights = [page.rect.height for page in doc]
        widths = [page.rect.width for page in doc]
        raw_pages = [_raw_lines(page, i + 1) for i, page in enumerate(doc)]
        metadata = {k: v for k, v in (doc.metadata or {}).items() if isinstance(v, str) and v}
        uin_counts = Counter(m for lines in raw_pages for ln in lines for m in _UIN.findall(ln.text))
        if uin_counts:
            metadata["uin"] = uin_counts.most_common(1)[0][0]
        table_pages: list[list[Line]] = []
        for i, page in enumerate(doc):
            size_hint = statistics.median([ln.size for ln in raw_pages[i]]) if raw_pages[i] else 10.0
            table_pages.append(_table_lines(page, i + 1, size_hint))
    finally:
        doc.close()

    text_pages = sum(1 for lines in raw_pages if sum(len(ln.text) for ln in lines) > 200)
    if not raw_pages or text_pages < max(1, int(len(raw_pages) * 0.5)):
        raise ScannedPdfError(
            "This PDF has no readable text layer (it looks like a scan). "
            "Please upload the insurer's original policy wording PDF."
        )

    furniture = _furniture_keys(raw_pages, heights)
    removed = 0
    cleaned_pages: list[list[Line]] = []
    for lines, height in zip(raw_pages, heights):
        kept = []
        for ln in lines:
            key = _DIGITS.sub("#", ln.text.lower())
            in_margin = ln.y1 < height * 0.12 or ln.y0 > height * 0.88
            if (in_margin and key in furniture) or _is_page_number(ln, height):
                removed += 1
                continue
            kept.append(ln)
        cleaned_pages.append(kept)

    # Replace text inside detected tables with one line per table row.
    for i, rows in enumerate(table_pages):
        if not rows:
            continue
        boxes = [(r.x0, r.y0, r.x1, r.y1) for r in rows]
        cleaned_pages[i] = [ln for ln in cleaned_pages[i] if not _inside(ln, boxes)] + rows

    column_votes = [_page_is_two_column(lines, w) for lines, w in zip(cleaned_pages, widths) if len(lines) > 10]
    two_column = bool(column_votes) and sum(column_votes) / len(column_votes) >= 0.5

    ordered: list[Line] = []
    for lines, width in zip(cleaned_pages, widths):
        page_two_col = two_column and _page_is_two_column(lines, width)
        ordered.extend(_order_page(lines, width, page_two_col))

    sizes = [ln.size for ln in ordered if ln.kind == "text" and len(ln.text.split()) >= 6]
    body_size = statistics.median(sizes) if sizes else 10.0
    return ParsedPdf(
        page_count=len(raw_pages),
        page_sizes=list(zip(widths, heights)),
        lines=ordered,
        two_column=two_column,
        body_size=float(body_size),
        text_pages=text_pages,
        removed_furniture=removed,
        metadata=metadata,
    )
