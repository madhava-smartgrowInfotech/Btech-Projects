"""Drawing helpers for the three decks: mimic the template styles (Review decks: Cambria titles, rounded cards;
Final deck: Calibri, banner, rule and footer) while giving full control of each slide's content."""
import copy
import math
import os

from lxml import etree
from PIL import Image
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

NAVY, INK, SLATE, CARD, EDGE = "1B2A41", "0F172A", "475569", "F6F8FB", "D5DCE6"
ORANGE, BLUE, GREEN, PURPLE, RED = "EB6834", "2A78D6", "1BAF7A", "7C5CD6", "C0392B"
ACCENTS = [ORANGE, BLUE, GREEN, PURPLE, RED, "0E8F9B"]
FNAV, FBLUE = "1F3864", "2E75B6"

WARN = []


def rgb(h):
    return RGBColor.from_string(h)


def est_height(paras, width_in, size, spacing_pt=4, factor=0.52):
    """Rough text height in inches for a list of paragraph strings."""
    cpl = max(1, int(width_in * 72 / (size * factor)))
    lines = 0
    for p in paras:
        for seg in str(p).split("\n"):
            lines += max(1, math.ceil(len(seg) / cpl))
    return lines * size * 1.2 / 72 + len(paras) * spacing_pt / 72


class Deck:
    def __init__(self, prs, style):
        self.prs = prs
        self.style = style  # "review" or "final"
        self.font = None if style == "review" else "Calibri"
        self.body_color = SLATE if style == "review" else "222222"
        self.head_color = INK if style == "review" else FNAV

    # ------------------------------------------------------------------ cleanup
    def wipe(self, slide, keep):
        for shp in list(slide.shapes):
            if keep(shp):
                continue
            rids = []
            el = shp._element
            for blip in el.iter(qn("a:blip")):
                rids.append(blip.get(qn("r:embed")))
            for ch in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/chart}chart"):
                rids.append(ch.get(qn("r:id")))
            el.getparent().remove(el)
            for r in rids:
                if r:
                    try:
                        slide.part.drop_rel(r)
                    except KeyError:
                        pass
        if slide.has_notes_slide:
            slide.notes_slide.notes_text_frame.text = ""

    # ------------------------------------------------------------------ text
    def _fmt_run(self, run, size, bold=False, color=None, italic=False, font=None):
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = rgb(color or self.body_color)
        f = font or self.font
        if f:
            run.font.name = f

    def text(self, slide, x, y, w, h, paras, size=16, bold=False, color=None, align=None, anchor="t", min_size=11,
             bullet=False, spacing=4, name=None, italic=False, font=None, margin=0.0):
        """paras: str or list of str / (str, dict) ; dict keys: bold, color, size, italic."""
        if isinstance(paras, str):
            paras = [paras]
        items = [(p, {}) if isinstance(p, str) else p for p in paras]
        s = size
        plain = [("• " if bullet else "") + t for t, _ in items]
        while s > min_size and est_height(plain, w - 2 * margin, s, spacing) > h:
            s -= 1
        if est_height(plain, w - 2 * margin, s, spacing) > h + 0.05:
            WARN.append(f"text may overflow ({est_height(plain, w, s, spacing):.2f} > {h:.2f} in): {plain[0][:50]}")
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        if name:
            tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(margin)
        tf.margin_top = tf.margin_bottom = Inches(margin)
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        first = True
        for t, o in items:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            if align:
                p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            p.space_after = Pt(spacing)
            if bullet:
                pPr = p._p.get_or_add_pPr()
                pPr.set("marL", str(int(Inches(0.22))))
                pPr.set("indent", str(-int(Inches(0.22))))
                for e in pPr.findall(qn("a:buNone")):
                    pPr.remove(e)
                bu = etree.SubElement(pPr, qn("a:buChar"))
                bu.set("char", "•")
            r = p.add_run()
            r.text = t
            self._fmt_run(r, o.get("size", s), o.get("bold", bold), o.get("color", color), o.get("italic", italic), font)
        return tb

    def title(self, slide, text, size=None):
        """Review decks: edit the template's title placeholder. Final deck: edit 'Text 1'."""
        for shp in slide.shapes:
            if (self.style == "review" and shp.is_placeholder and shp.placeholder_format.type is not None and "TITLE" in str(shp.placeholder_format.type)) or \
               (self.style == "final" and shp.name == "Text 1"):
                self.set_runs(shp, [text])
                if size:
                    for r in shp.text_frame.paragraphs[0].runs:
                        r.font.size = Pt(size)
                return shp
        raise RuntimeError("title shape not found")

    @staticmethod
    def set_runs(shape, texts):
        """Replace paragraph texts keeping the first run's formatting; add/remove paragraphs as needed."""
        tf = shape.text_frame
        paras = tf.paragraphs
        while len(paras) < len(texts):
            new = copy.deepcopy(paras[-1]._p)
            paras[-1]._p.addnext(new)
            paras = tf.paragraphs
        for i, t in enumerate(texts):
            p = paras[i]
            runs = p.runs
            if runs:
                runs[0].text = t
                for r in runs[1:]:
                    r._r.getparent().remove(r._r)
            else:
                p.add_run().text = t
        for p in paras[len(texts):]:
            p._p.getparent().remove(p._p)

    # ------------------------------------------------------------------ shapes
    def rect(self, slide, x, y, w, h, fill=CARD, line=EDGE, radius=0.03, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=0.75):
        s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            s.adjustments[0] = radius
        if fill:
            s.fill.solid()
            s.fill.fore_color.rgb = rgb(fill)
        else:
            s.fill.background()
        if line:
            s.line.color.rgb = rgb(line)
            s.line.width = Pt(lw)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    def badge(self, slide, x, y, d, label, color):
        c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(color)
        c.line.fill.background()
        c.shadow.inherit = False
        tf = c.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = label
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = rgb("FFFFFF")
        if self.font:
            r.font.name = self.font
        return c

    def card(self, slide, x, y, w, h, head, body, accent=BLUE, label=None, body_size=14, head_size=16, bullet=False):
        body_size = max(body_size, 18)
        head_size = max(head_size, 18)
        self.rect(slide, x, y, w, h)
        self.badge(slide, x + 0.2, y + 0.18, 0.5, label or "", accent)
        self.text(slide, x + 0.85, y + 0.12, w - 1.05, 0.62, head, size=head_size, bold=True, color=INK if self.style == "review" else FNAV, anchor="m", min_size=12)
        self.text(slide, x + 0.2, y + 0.85, w - 0.4, h - 1.0, body, size=body_size, bullet=bullet, min_size=11)

    def plain_card(self, slide, x, y, w, h, head, body, accent=BLUE, body_size=14, head_size=16, bullet=False):
        """Card without a badge: coloured top rule, heading, body."""
        body_size = max(body_size, 18)
        head_size = max(head_size, 18)
        self.rect(slide, x, y, w, h)
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(0.09), Inches(h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = rgb(accent)
        bar.line.fill.background()
        bar.shadow.inherit = False
        self.text(slide, x + 0.25, y + 0.12, w - 0.4, 0.5, head, size=head_size, bold=True, color=INK if self.style == "review" else FNAV, anchor="m", min_size=12)
        self.text(slide, x + 0.25, y + 0.68, w - 0.4, h - 0.8, body, size=body_size, bullet=bullet, min_size=11)

    def tile(self, slide, x, y, w, h, big, small, accent=BLUE):
        self.rect(slide, x, y, w, h)
        self.text(slide, x + 0.15, y + 0.12, w - 0.3, h * 0.5, big, size=30, bold=True, color=accent, anchor="m", align="c", min_size=18)
        self.text(slide, x + 0.15, y + h * 0.58, w - 0.3, h * 0.38, small, size=12, align="c", anchor="t", min_size=10)

    def arrow(self, slide, x, y, w=0.22, h=0.3, color="94A3B8"):
        a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
        a.fill.solid()
        a.fill.fore_color.rgb = rgb(color)
        a.line.fill.background()
        a.shadow.inherit = False

    def flow(self, slide, x, y, w, h, steps, gap=0.35, size=13, colors=None):
        size = max(size, 16)
        n = len(steps)
        bw = (w - gap * (n - 1)) / n
        for i, t in enumerate(steps):
            bx = x + i * (bw + gap)
            self.rect(slide, bx, y, bw, h, fill="FFFFFF", line=(colors or ACCENTS)[i % 6], lw=1.5)
            self.text(slide, bx + 0.08, y + 0.06, bw - 0.16, h - 0.12, t, size=size, bold=True, color=INK if self.style == "review" else FNAV, align="c", anchor="m", min_size=10)
            if i < n - 1:
                self.arrow(slide, bx + bw + (gap - 0.22) / 2, y + h / 2 - 0.15, 0.22, 0.3)

    # ------------------------------------------------------------------ pictures
    def picture(self, slide, path, x, y, w, h, frame=True, caption=None, cap_size=12):
        im = Image.open(path)
        iw, ih = im.size
        sc = min(w / iw, h / ih)
        pw, ph = iw * sc, ih * sc
        px, py = x + (w - pw) / 2, y + (h - ph) / 2
        if frame:
            self.rect(slide, px - 0.05, py - 0.05, pw + 0.1, ph + 0.1, fill="FFFFFF", line=EDGE, radius=0.01)
        pic = slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
        pic._element.nvPicPr.cNvPr.set("descr", caption or os.path.basename(path))
        if caption:
            self.text(slide, x, py + ph + 0.1, w, 0.45, caption, size=cap_size, align="c", min_size=10, italic=False)
        return pic

    # ------------------------------------------------------------------ table
    def table(self, slide, x, y, w, col_w, rows, size=12, header_size=None, row_pad=0.1, head_fill=None, bold_first=False, max_h=None):
        """rows[0] is the header. col_w are relative weights."""
        n_cols = len(rows[0])
        tot = sum(col_w)
        widths = [w * c / tot for c in col_w]
        size = 16 if max_h else size
        while True:
            hs = (header_size or size)
            heights = []
            for ri, r in enumerate(rows):
                s_ = hs if ri == 0 else size
                h = max(est_height([str(c) for c in [cell]], widths[ci] - 0.2, s_, 0, 0.52) for ci, cell in enumerate(r)) + row_pad * 2
                heights.append(max(h, 0.3))
            total = sum(heights)
            if not max_h or total <= max_h or size <= 11:
                break
            size -= 1
        if max_h and total > max_h:
            WARN.append(f"table height {total:.2f} > {max_h:.2f}: {rows[0][:2]}")
        gs = slide.shapes.add_table(len(rows), n_cols, Inches(x), Inches(y), Inches(w), Inches(total))
        tbl = gs.table
        tblPr = tbl._tbl.tblPr
        for a in ("firstRow", "bandRow"):
            tblPr.attrib.pop(a, None)
        sid = tblPr.find(qn("a:tableStyleId"))
        if sid is not None:
            tblPr.remove(sid)
        for ci, cw in enumerate(widths):
            tbl.columns[ci].width = Inches(cw)
        for ri, r in enumerate(rows):
            tbl.rows[ri].height = Inches(heights[ri])
            for ci, cell in enumerate(r):
                c = tbl.cell(ri, ci)
                c.margin_left = c.margin_right = Inches(0.08)
                c.margin_top = c.margin_bottom = Inches(0.04)
                c.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = c.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                run = p.add_run()
                run.text = str(cell)
                head = ri == 0
                self._fmt_run(run, hs if head else size, bold=head or (bold_first and ci == 0),
                              color="FFFFFF" if head else (INK if self.style == "review" else "222222"))
                if head:
                    p.alignment = PP_ALIGN.CENTER
                c.fill.solid()
                c.fill.fore_color.rgb = rgb(head_fill or (NAVY if self.style == "review" else FNAV)) if head else rgb("FFFFFF" if ri % 2 else "F6F8FB")
                tcPr = c._tc.get_or_add_tcPr()
                for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                    ln = etree.SubElement(tcPr, qn(tag))
                    ln.set("w", "9525")
                    sf = etree.SubElement(ln, qn("a:solidFill"))
                    clr = etree.SubElement(sf, qn("a:srgbClr"))
                    clr.set("val", EDGE if self.style == "review" else "A6A6A6")
                # fill must come after borders in schema order: move solidFill to the end
                for sfill in tcPr.findall(qn("a:solidFill")):
                    tcPr.remove(sfill)
                    tcPr.append(sfill)
        return gs, total

    # ------------------------------------------------------------------ chart
    def bar_chart(self, slide, x, y, w, h, cats, series, colors=None, number_format="0.00", title=None, horizontal=False, legend=True, maxv=None, font_size=12):
        cd = CategoryChartData()
        cd.categories = cats
        for name, vals in series:
            cd.add_series(name, vals)
        gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd)
        ch = gf.chart
        ch.font.size = Pt(font_size)
        if self.font:
            ch.font.name = self.font
        ch.has_title = bool(title)
        if title:
            ch.chart_title.text_frame.text = title
            ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(font_size + 1)
            ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
        ch.has_legend = legend and len(series) > 1
        if ch.has_legend:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        plot = ch.plots[0]
        plot.gap_width = 60
        plot.has_data_labels = True
        plot.data_labels.number_format = number_format
        plot.data_labels.number_format_is_linked = False
        plot.data_labels.font.size = Pt(font_size - 1)
        cols = colors or [GREEN, "64748B", BLUE, PURPLE]
        for i, s in enumerate(plot.series):
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = rgb(cols[i % len(cols)])
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = rgb("E2E8F0")
        va.format.line.fill.background()
        if maxv:
            va.maximum_scale = maxv
        va.minimum_scale = 0
        return gf
