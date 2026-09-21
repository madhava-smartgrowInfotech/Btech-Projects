"""Ordered PDF lines -> clause-level chunks with numbering, heading path, pages and highlight boxes."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.pdf_parser import Line, ParsedPdf

MAX_WORDS = 380
TARGET_WORDS = 260
MIN_PART_WORDS = 60
MIN_STANDALONE_WORDS = 12

_UPPER_START = r"(?=[\"“'(]?[A-Z])"
# "4.2.1 Text" / "4.2.1. Text" - multi-level numbering.
_NUMBERED = re.compile(rf"^(?P<ref>\d{{1,2}}(?:\.\d{{1,2}}){{1,4}})\.?\s+{_UPPER_START}(?P<rest>.+)$")
# "3. Text" - single-level numbering (needs emphasis and sequence checks).
_TOP_NUMBER = re.compile(rf"^(?P<ref>\d{{1,2}})\.\s*{_UPPER_START}(?P<rest>.+)$")
_DEF = re.compile(r"^(?P<ref>Def(?:inition)?\.?\s*\d{1,3})\.?\s+(?P<rest>.+)$", re.I)
_EXCL = re.compile(r"^(?:Code\s*[-–:]?\s*)?(?P<ref>Excl\s*\d{1,2})\b[\s:.\-–)]*(?P<rest>.*)$", re.I)
_SECTION = re.compile(
    r"^(?P<ref>(?:SECTION|Section|PART|Part|CHAPTER|Chapter|ANNEXURE|Annexure|SCHEDULE|Schedule)"
    r"\s+(?:[IVX]{1,5}|[A-Z]|\d{1,2}))\b[\s:.\-–)]*(?P<rest>.*)$"
)
_ROMAN = re.compile(r"^(?P<ref>[IVX]{1,5})\.\s+(?P<rest>[A-Z].*)$")
_LETTER = re.compile(r"^(?P<ref>[A-H])[.)]\s+(?P<rest>[A-Z].*)$")
_SUB_ITEM = re.compile(r"^(\(?[a-z]{1,2}\)|\(?[ivx]{1,5}[.)]|\(?\d{1,2}\)|[•\-–·*]|[a-z]\.)\s", re.I)
_CODE_EXCL = re.compile(r"\(?\s*Code\s*[-–:]?\s*(?P<code>Excl\s*\d{1,2})\s*\)?", re.I)
_MENTIONS_CODE = re.compile(r"\(?\bCode\s*[-–:]?\s*(Excl\s*\d{1,2}\s*\)?)?\s*$|\(\s*Code\s*[-–:]?\s*Excl", re.I)
# "b. Rest Cure...: Code – Excl05" / "ii) ..." - a lettered or roman list item.
_LETTER_ITEM = re.compile(r"^\(?(?P<marker>[a-z]|[ivx]{1,5}|[A-Z])[.)]\s+(?P<rest>.+)$")
_NUMBER_ITEM = re.compile(r"^(?P<marker>\d{1,2})[.)](?!\d)\s*(?P<rest>.+)$")
_ITEM_START = re.compile(r"^\(?(?:[a-z]|[ivx]{1,5}|[A-Z]|\d{1,2}(?:\.\d{1,2})*)[.)]\s")
# "... for domestic reasons. Code – Excl13" - the code closes the item instead of opening it.
_END_CODE = re.compile(r"\(?\s*\bCode\s*[-–:]?\s*(?P<code>Excl\s*\d{1,2})\s*\)?[.:;]?\s*$", re.I)
_UIN = re.compile(r"\b[A-Z]{5,9}\d{5}V\d{6}\b")
_LEAD_IN_SPLIT = re.compile(r"^(.{3,80}?)(?::|\s[-–]\s|\s(?:means|is defined as|shall mean|refers to)\b)", re.I)


@dataclass
class Chunk:
    ordinal: int
    clause_ref: str | None
    heading: str | None
    section_path: str
    text: str
    page_start: int
    page_end: int
    bboxes: list[dict[str, float]]
    word_count: int

    def index_text(self) -> str:
        """Text used for BM25 and embeddings: heading context + clause text."""
        parts = [p for p in (self.section_path, self.heading) if p]
        prefix = " > ".join(parts)
        return f"{prefix}\n{self.text}" if prefix else self.text


@dataclass
class _Segment:
    ref: str | None
    depth: float
    heading: str | None
    lines: list[Line] = field(default_factory=list)
    path: list[str] = field(default_factory=list)
    complete: bool = False

    @property
    def words(self) -> int:
        return sum(len(ln.text.split()) for ln in self.lines)


def _norm_excl(code: str) -> str:
    digits = re.sub(r"\D", "", code)
    return f"Excl{int(digits):02d}" if digits else code


def _is_major_heading(line: Line, body_size: float) -> bool:
    words = line.text.split()
    if not (1 <= len(words) <= 9) or not line.bold:
        return False
    letters = [c for c in line.text if c.isalpha()]
    all_caps = bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.85
    return line.size >= body_size + 0.9 or (all_caps and len(letters) > 3)


def _heading_from(rest: str) -> str:
    rest = _CODE_EXCL.sub("", rest).strip().rstrip(":-–(").strip()
    # "Day Care Treatment: We will cover..." -> "Day Care Treatment"
    colon = rest.find(":")
    if 0 < colon <= 90 and 1 <= len(rest[:colon].split()) <= 10 and rest[colon + 1:].strip():
        return rest[:colon].strip().rstrip("-–(").strip()
    match = _LEAD_IN_SPLIT.match(rest)
    if match and len(match.group(1).split()) <= 8:
        return match.group(1).strip()  # "Accident means a sudden..." -> "Accident"
    words = rest.split()
    if len(words) <= 14:
        return rest
    return " ".join(words[:8]) + "…"


class _Classifier:
    """Decides whether a line opens a new clause, keeping track of top-level numbering."""

    def __init__(self, body_size: float) -> None:
        self.body = body_size
        self.last_top: int | None = None
        self.context_depth: float = 0.0  # depth of the innermost open heading (set by segment())

    def classify(self, line: Line, prev: Line | None, nxt: Line | None = None,
                 item_text: str | None = None) -> tuple[str | None, float, str] | None:
        """``item_text`` is this line plus the rest of its list item, when the line opens a lettered item."""
        if line.kind == "table":
            return None
        text = line.text
        emphasised = line.bold or line.size >= self.body + 0.5 or bool(line.bold_lead)
        words = text.split()

        # "(Code-" at the end of the previous line: this "Excl04)" line continues that clause.
        if prev is not None and re.search(r"(\(|\b)Code\s*[-–:]?\s*$", prev.text, re.I):
            return None
        if m := _EXCL.match(text):
            title_continues = (
                prev is not None
                and prev.page == line.page
                and (prev.bold or bool(prev.bold_lead))
                and not prev.text.rstrip().endswith((".", ";", ":"))
            )
            if title_continues:
                return None  # the code closes a clause title that wrapped onto this line
            ref = _norm_excl(m.group("ref"))
            return ref, 3, _heading_from(m.group("rest") or ref)
        # An item that carries an exclusion code ("5. Cosmetic surgery (Code- Excl08)") is always its own
        # clause but never a top-level section, even when its list number looks like the next section.
        numbered_item = re.match(r"^(\d{1,2})[.)]\s*(.*)$", text)
        if numbered_item:
            continues = (nxt is not None and nxt.page == line.page and not _ITEM_START.match(nxt.text)
                         and not re.match(r"^\(?\d{1,2}(\.\d{1,2})*[.)]?\s", nxt.text))
            window = text + " " + (nxt.text[:60] if continues else "")
            if code := _CODE_EXCL.search(window):
                title = _NUMBER_ITEM.match(item_text).group("rest") if item_text else numbered_item.group(2)
                title = re.sub(r"^(?:\d{1,2}\.)+\s*", "", title)  # "1.9. Breach of law" -> "Breach of law"
                return _norm_excl(code.group("code")), 99, _heading_from(title)
            if _MENTIONS_CODE.search(text):
                return numbered_item.group(1), 99, _heading_from(numbered_item.group(2))
        # A list item that carries an exclusion code is its own clause, whether the code closes its title
        # ("b. Rest Cure...: Code – Excl05: Expenses...") or the whole item ("j. Treatments in spas... Code – Excl13").
        # A code mentioned in prose ("ii. Exclusion no. 3 (Code Excl 03) as stated...") does neither.
        if item_text and (item := _LETTER_ITEM.match(text) or _NUMBER_ITEM.match(text)):
            body = item.group("rest")
            whole = (_LETTER_ITEM.match(item_text) or _NUMBER_ITEM.match(item_text)).group("rest")
            title = _CODE_EXCL.search(body[:220])
            if (title and not numbered_item and len(body[: title.start()].split()) <= 14
                    and re.match(r"\s*([:.\-–]|$)", body[title.end():])):
                return _norm_excl(title.group("code")), 99, _heading_from(body)
            closing = _END_CODE.search(whole)
            if closing and (whole[: closing.start()].rstrip().endswith((".", ";", ")", "-", "–", ":"))
                            or closing.group(0).lstrip()[:1] == "("):
                return _norm_excl(closing.group("code")), 99, _heading_from(whole[: closing.start()])
        if (m := _SECTION.match(text)) and emphasised:
            self.last_top = None
            return m.group("ref").title(), 0.5, _heading_from(m.group("rest") or m.group("ref"))
        if m := _DEF.match(text):
            return "Def. " + re.sub(r"\D", "", m.group("ref")), 2, _heading_from(m.group("rest"))
        if m := _NUMBERED.match(text):
            ref = m.group("ref")
            first = int(ref.split(".")[0])
            if self.last_top is None or first >= self.last_top:
                self.last_top = first
            return ref, ref.count(".") + 1, _heading_from(m.group("rest"))
        if (m := _TOP_NUMBER.match(text)) and emphasised:
            number = int(m.group("ref"))
            in_sequence = (self.last_top is None and number <= 2) or (
                self.last_top is not None and self.last_top < number <= self.last_top + 3
            )
            if in_sequence:
                self.last_top = number
                return m.group("ref"), 1, _heading_from(m.group("rest"))
            # A numbered list inside a clause (e.g. the exclusions list restarting at 1).
            return m.group("ref"), 99, _heading_from(m.group("rest"))
        if (m := _ROMAN.match(text)) and emphasised and len(words) <= 8:
            self.last_top = None
            return m.group("ref"), 0.5, _heading_from(m.group("rest"))
        nested = max(1.2, self.context_depth + 0.5)  # lettered/unnumbered headings nest under the open clause
        if (m := _LETTER.match(text)) and line.bold and len(words) <= 12:
            return m.group("ref"), nested, _heading_from(m.group("rest"))
        if _SUB_ITEM.match(text) or _TOP_NUMBER.match(text):
            return None
        if line.bold and (prev is None or not prev.bold or prev.page != line.page):
            if _is_major_heading(line, self.body):
                return None, max(1.5, nested), text.strip().rstrip(":")
            if words and text[0].isupper():  # a bold line starting in lower case continues a sentence
                return None, 99, _heading_from(text)
        lead = line.bold_lead.strip()
        if lead and lead[0].isupper() and len(lead.split()) <= 10:
            after_sentence = prev is None or prev.page != line.page or prev.text.rstrip().endswith(
                (".", ":", ";", ")")
            )
            if lead.endswith(":") or after_sentence:
                return None, 99, _heading_from(lead)
        return None


def _join_lines(lines: list[Line]) -> str:
    out = ""
    for line in lines:
        text = line.text
        if not out:
            out = text
            continue
        if line.kind == "table":
            out += "\n" + text
        elif out.endswith("-") and text[:1].islower():
            out += text
        elif _SUB_ITEM.match(text) or out.endswith((":", ";")) or re.match(r"^(\d+(\.\d+)*\.?|Excl\d+)\s", text):
            out += "\n" + text
        else:
            out += " " + text
    return out.strip()


def _boxes(lines: list[Line]) -> list[dict[str, float]]:
    boxes: list[dict[str, float]] = []
    current: dict[str, float] | None = None
    current_key: tuple[int, int] | None = None
    for ln in lines:
        key = (ln.page, ln.column)
        if current is not None and key == current_key and ln.y0 - current["y1"] < 30:
            current["x0"] = min(current["x0"], ln.x0)
            current["y0"] = min(current["y0"], ln.y0)
            current["x1"] = max(current["x1"], ln.x1)
            current["y1"] = max(current["y1"], ln.y1)
        else:
            current = {"page": ln.page, "x0": ln.x0, "y0": ln.y0, "x1": ln.x1, "y1": ln.y1}
            current_key = key
            boxes.append(current)
    return [{k: (int(v) if k == "page" else round(v, 1)) for k, v in b.items()} for b in boxes]


def _explode_giant_lines(lines: list[Line]) -> list[Line]:
    """Split any single line longer than MAX_WORDS into sentence groups (same position)."""
    out: list[Line] = []
    for ln in lines:
        if len(ln.text.split()) <= MAX_WORDS:
            out.append(ln)
            continue
        sentences = re.split(r"(?<=[.;:])\s+", ln.text)
        buf: list[str] = []
        for sentence in sentences:
            buf.append(sentence)
            if sum(len(s.split()) for s in buf) >= TARGET_WORDS // 2:
                out.append(Line(**{**ln.__dict__, "text": " ".join(buf)}))
                buf = []
        if buf:
            out.append(Line(**{**ln.__dict__, "text": " ".join(buf)}))
    return out


def _split_long(lines: list[Line]) -> list[list[Line]]:
    """Split an over-long clause at sub-item or sentence boundaries into ~TARGET_WORDS parts."""
    lines = _explode_giant_lines(lines)
    total = sum(len(ln.text.split()) for ln in lines)
    if total <= MAX_WORDS:
        return [lines]
    parts: list[list[Line]] = []
    current: list[Line] = []
    count = 0
    for ln in lines:
        words = len(ln.text.split())
        at_boundary = bool(_SUB_ITEM.match(ln.text)) or ln.kind == "table" or (
            bool(current) and current[-1].text.rstrip().endswith((".", ";", ":"))
        )
        if count >= TARGET_WORDS and at_boundary:
            parts.append(current)
            current, count = [], 0
        elif count >= MIN_PART_WORDS and count + words > MAX_WORDS + 40:
            parts.append(current)
            current, count = [], 0
        current.append(ln)
        count += words
    if current:
        if parts and count < MIN_PART_WORDS:
            parts[-1].extend(current)
        else:
            parts.append(current)
    return parts


def _excl_ref(seg: _Segment) -> None:
    """Give clauses that carry an IRDAI exclusion code ("Code- Excl03") that code as their reference."""
    if seg.ref and seg.ref.startswith("Excl"):
        return
    head = " ".join(ln.text for ln in seg.lines[:5])[:520]
    m = _CODE_EXCL.search(head)
    if not m:
        return
    before = head[: m.start()].strip()
    numbered_title = bool(seg.ref and seg.ref.isdigit()) and "." not in before.split(" ", 1)[-1]
    if len(before.split()) > (40 if numbered_title else 14):
        return  # a mention inside prose ("subject to Code Excl01"), not the clause title
    seg.ref = _norm_excl(m.group("code"))
    before = re.sub(r"^\(?(?:[ivx]{1,4}|\d{1,2}(?:\.\d{1,2})*)[.)]?\s*", "", before, flags=re.I).strip(" :-–(")
    if before:
        seg.heading = _heading_from(before)


def _item_text(lines: list[Line], idx: int, max_lines: int = 16) -> tuple[str, int]:
    """The list item opened at ``idx``: its text and line count, up to the next item or table, or up to
    the exclusion code that closes it ("... domestic reasons - Code Excl 13")."""
    parts = [lines[idx].text]
    for ln in lines[idx + 1: idx + max_lines]:
        if ln.kind == "table" or _ITEM_START.match(ln.text):
            break
        closes_code = re.match(r"^\(?Code\b", ln.text, re.I) or re.search(r"(\(|\b)Code\s*[-–:]?\s*$", parts[-1], re.I)
        if _EXCL.match(ln.text) and not closes_code:
            break  # the next clause's code
        parts.append(ln.text)
        if _END_CODE.search(ln.text) or (closes_code and _EXCL.match(ln.text)):
            break  # the code closes this item
    return " ".join(parts), len(parts)


def segment(parsed: ParsedPdf) -> list[Chunk]:
    classifier = _Classifier(parsed.body_size)
    segments: list[_Segment] = []
    stack: list[tuple[float, str]] = []
    current = _Segment(ref=None, depth=0, heading=None)
    prev: Line | None = None

    lines = parsed.lines
    inside_item_until = -1  # lines of a list item already closed by its exclusion code
    for idx, line in enumerate(lines):
        nxt = lines[idx + 1] if idx + 1 < len(lines) else None
        classifier.context_depth = stack[-1][0] if stack else 0.0
        item_text, item_lines = None, 1
        if idx > inside_item_until and (_LETTER_ITEM.match(line.text) or _NUMBER_ITEM.match(line.text)):
            item_text, item_lines = _item_text(lines, idx)
        result = None if idx <= inside_item_until else classifier.classify(line, prev, nxt, item_text)
        if result is not None:
            ref, depth, heading = result
            if current.lines:
                segments.append(current)
            if depth < 99:
                while stack and stack[-1][0] >= depth:
                    stack.pop()
            ancestors = [title for _, title in stack]
            current = _Segment(ref=ref, depth=depth, heading=heading, lines=[line], path=ancestors)
            if item_text and depth == 99 and ref and ref.startswith("Excl"):
                current.complete = True  # a whole exclusion item: never folded into its neighbour
                if _END_CODE.search(item_text):
                    inside_item_until = idx + item_lines - 1
            label = f"{ref} {heading}".strip() if ref else (heading or "")
            if depth < 99 and label:
                stack.append((depth, label[:120]))
        else:
            current.lines.append(line)
        prev = line
    if current.lines:
        segments.append(current)

    # Fold heading-only segments into the following segment.
    merged: list[_Segment] = []
    carry: list[Line] = []
    for idx, seg in enumerate(segments):
        if carry:
            seg.lines = carry + seg.lines
            carry = []
        if seg.words < MIN_STANDALONE_WORDS and not seg.complete and idx < len(segments) - 1:
            carry = seg.lines
            continue
        merged.append(seg)
    if carry and merged:
        merged[-1].lines.extend(carry)

    chunks: list[Chunk] = []
    for seg in merged:
        _excl_ref(seg)
        parts = _split_long(seg.lines)
        for k, part in enumerate(parts):
            text = _join_lines(part)
            if not text:
                continue
            heading = seg.heading
            if heading and k > 0:
                heading = f"{heading} (continued)"
            chunks.append(Chunk(
                ordinal=len(chunks) + 1,
                clause_ref=seg.ref,
                heading=heading[:300] if heading else None,
                section_path=" > ".join(seg.path)[:600],
                text=text,
                page_start=min(ln.page for ln in part),
                page_end=max(ln.page for ln in part),
                bboxes=_boxes(part),
                word_count=len(text.split()),
            ))
    return chunks


def find_uin(parsed: ParsedPdf) -> str | None:
    """The IRDAI Unique Identification Number printed most often (often only in the page footer)."""
    if parsed.metadata.get("uin"):
        return parsed.metadata["uin"]
    counts = Counter(m for ln in parsed.lines for m in _UIN.findall(ln.text))
    if not counts:
        return None
    return counts.most_common(1)[0][0]
