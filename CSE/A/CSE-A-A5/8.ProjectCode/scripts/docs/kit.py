"""
python-docx helpers shared by every document builder.

House style (all six chapter documents and the full report):
  Times New Roman 12 body, 14 bold headings, 1.5 line spacing, justified,
  numbered figures and tables with captions (SEQ fields, so Word can build the lists),
  page numbers in the footer.

Inline markup accepted by the text helpers:  **bold**  *italic*  `code`
"""

import os
import re

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Inches, Pt, RGBColor

FONT = "Times New Roman"
MONO = "Consolas"
NAVY = RGBColor(0x1B, 0x2A, 0x41)
_MARK = re.compile(r"(\*\*.+?\*\*|`.+?`|\*[^*\s][^*]*?\*)")


def set_font(run, name=FONT, size=None, bold=None, italic=None, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_runs(par, text, size=None, bold=None, italic=None, color=None):
    """Add text with **bold**, *italic* and `code` markup to a paragraph."""
    for part in _MARK.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = par.add_run(part[2:-2])
            set_font(r, FONT, size, True, italic, color)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = par.add_run(part[1:-1])
            set_font(r, MONO, (size or 12) - 1.5, bold, italic, color)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1])
            set_font(r, FONT, size, bold, True, color)
        else:
            r = par.add_run(part)
            set_font(r, FONT, size, bold, italic, color)


def shade(cell_or_par, fill):
    el = cell_or_par._element
    pr = el.get_or_add_tcPr() if hasattr(el, "get_or_add_tcPr") else el.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def add_field(par, instr, placeholder="", size=None, bold=None):
    """Insert a complex field (PAGE, SEQ, TOC ...)."""
    def run_with(child):
        r = par.add_run()
        set_font(r, FONT, size, bold)
        r._element.append(child)
        return r

    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); run_with(b)
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "; run_with(it)
    s = OxmlElement("w:fldChar"); s.set(qn("w:fldCharType"), "separate"); run_with(s)
    r = par.add_run(placeholder); set_font(r, FONT, size, bold)
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end"); run_with(e)


class Doc:
    def __init__(self, title, header_text=None, a4=True, report=False):
        self.report = report
        self.lm, self.rm = (Inches(1.0), Inches(0.85)) if report else (Inches(1.25), Inches(1.0))
        self.tm = Inches(0.9) if report else Inches(1.0)
        self.doc = Document()
        self.title = title
        self.header_text = header_text or title
        self.fig_no = 0
        self.tab_no = 0
        sec = self.doc.sections[0]
        if a4:
            sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        sec.left_margin, sec.right_margin = self.lm, self.rm
        sec.top_margin, sec.bottom_margin = self.tm, self.tm
        self._styles()
        self._numbered_sections = False

    # ------------------------------------------------------------------ styles
    def _styles(self):
        st = self.doc.styles
        n = st["Normal"]
        n.font.name = FONT
        n.font.size = Pt(12)
        n.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        pf = n.paragraph_format
        pf.line_spacing = 1.5
        pf.space_after = Pt(5 if self.report else 6)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for name, size, before, after in ((("Heading 1", 14, 12, 8), ("Heading 2", 14, 10, 5), ("Heading 3", 12, 8, 4)) if self.report else (("Heading 1", 14, 18, 10), ("Heading 2", 14, 14, 6), ("Heading 3", 12, 10, 4))):
            h = st[name]
            h.font.name = FONT
            h.font.size = Pt(size)
            h.font.bold = True
            h.font.italic = name == "Heading 3"
            h.font.color.rgb = RGBColor(0, 0, 0)
            rpr = h.element.get_or_add_rPr()
            rf = rpr.find(qn("w:rFonts"))
            if rf is None:
                rf = OxmlElement("w:rFonts"); rpr.append(rf)
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rf.set(qn(a), FONT)
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(a)) is not None:
                    del rf.attrib[qn(a)]
            h.paragraph_format.space_before = Pt(before)
            h.paragraph_format.space_after = Pt(after)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.line_spacing = 1.15
            h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        from docx.enum.style import WD_STYLE_TYPE
        for nm, left in (("TOC 1", 0), ("TOC 2", 0.25), ("Table of Figures", 0)):
            try:
                sty = st[nm]
            except KeyError:
                sty = st.add_style(nm, WD_STYLE_TYPE.PARAGRAPH)
            sty.base_style = st["Normal"]
            sty.font.name = FONT
            sty.font.size = Pt(10.5)
            sty.paragraph_format.line_spacing = 1.0
            sty.paragraph_format.space_after = Pt(0)
            sty.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            sty.paragraph_format.left_indent = Inches(left)
        cap = st["Caption"]
        cap.font.name = FONT
        cap.font.size = Pt(11)
        cap.font.bold = True
        cap.font.italic = False
        cap.font.color.rgb = RGBColor(0, 0, 0)
        cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.line_spacing = 1.15
        cap.paragraph_format.space_after = Pt(10)

    # ------------------------------------------------------------ text blocks
    def h1(self, text, page_break=True):
        h = self.doc.add_heading(text, level=1)
        if page_break:
            h.paragraph_format.page_break_before = True
        return h

    def h2(self, text):
        return self.doc.add_heading(text, level=2)

    def h3(self, text):
        return self.doc.add_heading(text, level=3)

    def p(self, text, align=None, size=None, bold=None, italic=None, space_after=None, keep_next=False, indent=None):
        par = self.doc.add_paragraph()
        add_runs(par, text, size, bold, italic)
        if align == "center":
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "left":
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif align == "right":
            par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if space_after is not None:
            par.paragraph_format.space_after = Pt(space_after)
        if keep_next:
            par.paragraph_format.keep_with_next = True
        if indent:
            par.paragraph_format.left_indent = Inches(indent)
        return par

    def bullets(self, items, size=None, style="•"):
        for it in items:
            par = self.doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.5)
            par.paragraph_format.first_line_indent = Inches(-0.25)
            par.paragraph_format.space_after = Pt(3)
            add_runs(par, f"{style}\t" if False else f"{style}  ", size)
            add_runs(par, it, size)

    def numbered(self, items, size=None, start=1):
        for i, it in enumerate(items, start):
            par = self.doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.5)
            par.paragraph_format.first_line_indent = Inches(-0.3)
            par.paragraph_format.space_after = Pt(3)
            add_runs(par, f"{i}.  ", size)
            add_runs(par, it, size)

    def code(self, text, size=8):
        if self.report:
            size = min(size, 7.6)
        for line in text.rstrip("\n").split("\n"):
            par = self.doc.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf = par.paragraph_format
            pf.line_spacing = 1.0
            pf.space_after = Pt(0)
            pf.left_indent = Inches(0.1)
            r = par.add_run(line if line else " ")
            set_font(r, MONO, size)
            shade(par, "F3F5F8")
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        sp.paragraph_format.line_spacing = 0.6

    def equation(self, text):
        """Centred, numbered display equation (plain Unicode text; Cambria Math is used for the glyphs)."""
        self.eq_no = getattr(self, "eq_no", 0) + 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.line_spacing = 1.15
        par.paragraph_format.space_after = Pt(6)
        r = par.add_run(text)
        set_font(r, "Cambria Math", 12, False, True)
        r2 = par.add_run(f"      ({self.eq_no})")
        set_font(r2, FONT, 12)

    def page_break(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def spacer(self, pts=12):
        par = self.doc.add_paragraph()
        par.paragraph_format.space_after = Pt(pts)
        par.paragraph_format.line_spacing = 1.0
        return par

    # ---------------------------------------------------------------- figures
    def _caption(self, label, text, seq, container=None):
        for pre in ("Figure: ", "Table: ", "Figure - ", "Table - "):
            if text.startswith(pre):
                text = text[len(pre):]
                text = text[:1].upper() + text[1:]
        par = (container or self.doc).add_paragraph(style="Caption")
        r = par.add_run(f"{label} ")
        set_font(r, FONT, 11, True)
        add_field(par, f"SEQ {seq} \\* ARABIC", str(self.fig_no if seq == "Figure" else self.tab_no), 11, True)
        r = par.add_run(": ")
        set_font(r, FONT, 11, True)
        add_runs(par, text, 11, True)
        return par

    def _fit(self, path, width_in, max_h=None):
        """In report mode shrink pictures so none is taller than max_h inches (default 3.7) and none wider than 0.85 of the request."""
        if not self.report:
            return width_in
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        if os.sep + "diagrams" + os.sep in path:   # design diagrams carry small text: keep them large enough to read
            return min(width_in * 0.97, (max_h or 4.3) * w / h)
        width_in = width_in * 0.88
        mh = max_h or 3.1
        return min(width_in, mh * w / h)

    def figure(self, path, caption, width_in=5.6):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        self.fig_no += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.paragraph_format.line_spacing = 1.0
        par.paragraph_format.space_after = Pt(4)
        width_in = self._fit(path, width_in)
        par.add_run().add_picture(path, width=Inches(width_in))
        self._caption("Figure", caption, "Figure")
        return self.fig_no

    def figure_pair(self, items, width_in=2.7):
        """Pictures side by side in a borderless table, each with its own numbered caption. items: [(path, caption), ...]"""
        for path, _ in items:
            if not os.path.exists(path):
                raise FileNotFoundError(path)
        t = self.doc.add_table(rows=1, cols=len(items))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for cell, (path, caption) in zip(t.rows[0].cells, items):
            self.fig_no += 1
            par = cell.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.keep_with_next = True
            par.paragraph_format.line_spacing = 1.0
            par.paragraph_format.space_after = Pt(4)
            par.add_run().add_picture(path, width=Inches(self._fit(path, width_in, 3.4)))
            self._caption("Figure", caption, "Figure", container=cell)
        for row in t.rows:
            cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); row._tr.get_or_add_trPr().append(cs)
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        sp.paragraph_format.line_spacing = 0.8
        return self.fig_no

    def table(self, caption, header, rows, widths=None, size=10.5, align=None):
        if self.report:
            size = max(9.0, size - 1.0)
        self.tab_no += 1
        cap = self._caption("Table", caption, "Table")
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_after = Pt(4)
        t = self.doc.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            par = c.paragraphs[0]
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            par.paragraph_format.line_spacing = 1.0
            par.paragraph_format.space_after = Pt(2)
            add_runs(par, h, size, True, None, RGBColor(255, 255, 255))
            shade(c, "1B2A41")
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                cells[i].text = ""
                par = cells[i].paragraphs[0]
                par.paragraph_format.line_spacing = 1.0
                par.paragraph_format.space_after = Pt(2)
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT if (align is None or align[i] == "l") else (WD_ALIGN_PARAGRAPH.CENTER if align[i] == "c" else WD_ALIGN_PARAGRAPH.RIGHT)
                add_runs(par, str(v), size)
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Inches(w)
        # repeat header row, keep rows together
        trpr = t.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trpr.append(th)
        for row in t.rows:
            cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); row._tr.get_or_add_trPr().append(cs)
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(6)
        sp.paragraph_format.line_spacing = 0.8
        return self.tab_no

    # ------------------------------------------------------- lists of things
    def toc_field(self, instr, placeholder="Right-click and choose Update Field to build this list."):
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
        par.paragraph_format.line_spacing = 1.15
        add_field(par, instr, placeholder, 12)

    # --------------------------------------------------------- sections / page numbers
    def new_section(self, fmt=None, start=None, footer=True):
        """Start a new page section; fmt: 'lowerRoman' | 'decimal' | None; start: first page number."""
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        sec.left_margin, sec.right_margin = self.lm, self.rm
        pg = sec._sectPr.find(qn("w:pgNumType"))
        if pg is None:
            pg = OxmlElement("w:pgNumType")
            sec._sectPr.append(pg)
        if fmt:
            pg.set(qn("w:fmt"), fmt)
        if start is not None:
            pg.set(qn("w:start"), str(start))
        sec.footer.is_linked_to_previous = False
        sec.header.is_linked_to_previous = False
        self._fill_footer(sec, footer)
        return sec

    def _fill_footer(self, sec, numbers=True):
        f = sec.footer
        for par in list(f.paragraphs):
            for r in list(par.runs):
                r._element.getparent().remove(r._element)
        par = f.paragraphs[0]
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.line_spacing = 1.0
        if numbers:
            add_field(par, "PAGE", "1", 11)
        h = sec.header
        hp = h.paragraphs[0]
        for r in list(hp.runs):
            r._element.getparent().remove(r._element)
        if numbers and self.header_text:
            hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            hp.paragraph_format.line_spacing = 1.0
            r = hp.add_run(self.header_text)
            set_font(r, FONT, 10, False, True, RGBColor(0x55, 0x55, 0x55))

    def footer_numbers(self):
        """Page numbers + running header on the current (first) section."""
        self._fill_footer(self.doc.sections[0], True)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.doc.save(path)
        return path
