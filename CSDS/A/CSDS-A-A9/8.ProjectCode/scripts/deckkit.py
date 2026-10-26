"""Helpers for filling the Review/Final PowerPoint templates in place (python-pptx).

The templates keep their design; these helpers replace text, table cells, chart data and pictures
while preserving the original run formatting.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from pptx.util import Emu
from PIL import Image

A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def shape(slide, sid):
    for sh in slide.shapes:
        if sh.shape_id == sid:
            return sh
    raise KeyError(f"shape id {sid} not on slide")


def _set_par(p, text, size=None):
    runs = p.findall(qn("a:r"))
    if not runs:
        r = etree.SubElement(p, qn("a:r"))
        etree.SubElement(r, qn("a:rPr"), lang="en-US")
        etree.SubElement(r, qn("a:t"))
        runs = [r]
    for extra in runs[1:]:
        p.remove(extra)
    r = runs[0]
    r.find(qn("a:t")).text = text
    rpr = r.find(qn("a:rPr"))
    if size and rpr is not None:
        rpr.set("sz", str(int(size * 100)))
    end = p.find(qn("a:endParaRPr"))
    if size and end is not None:
        end.set("sz", str(int(size * 100)))
    # endParaRPr must stay last
    if end is not None:
        p.remove(end)
        p.append(end)


def set_paras(sh, paras, size=None):
    """Replace all paragraphs of a shape with `paras` (list[str] or str), cloning the first paragraph's format."""
    if isinstance(paras, str):
        paras = [paras]
    body = sh.text_frame._txBody
    ps = body.findall(qn("a:p"))
    proto = copy.deepcopy(ps[0])
    for p in ps:
        body.remove(p)
    for text in paras:
        p = copy.deepcopy(proto)
        _set_par(p, text, size)
        body.append(p)


def est_lines(text, width_px, size_pt, indent_px=0):
    cpl = max(8, (width_px - indent_px) / (size_pt * 1.333 * 0.52))
    return max(1, math.ceil(len(text) / cpl))


def fit_size(paras, width_px, height_px, max_pt, min_pt=9, gap_pt=4, indent_px=0):
    """Largest font size (pt) at which the estimated text height fits the box."""
    if isinstance(paras, str):
        paras = [paras]
    size = max_pt
    while size > min_pt:
        lines = sum(est_lines(t, width_px, size, indent_px) for t in paras)
        h = lines * size * 1.333 * 1.2 + len(paras) * gap_pt * 1.333
        if h <= height_px:
            break
        size -= 0.5
    return size


def fill(slide, sid, paras, max_pt=None, min_pt=9, bullet=False, gap_pt=None):
    """Set text and shrink the font to fit the shape (never above the template size)."""
    sh = shape(slide, sid)
    p0 = sh.text_frame._txBody.find(qn("a:p"))
    rpr = p0.find(qn("a:r")).find(qn("a:rPr"))
    tmpl = int(rpr.get("sz", "1600")) / 100
    cap = min(max_pt or tmpl, tmpl) if max_pt is None else max_pt
    w, h = sh.width / 9525, sh.height / 9525
    size = fit_size(paras, w, h, cap, min_pt, gap_pt=(gap_pt if gap_pt is not None else 4), indent_px=24 if bullet else 0)
    set_paras(sh, paras, size)
    if gap_pt is not None:
        for sp in sh.text_frame._txBody.iter(qn("a:spcPts")):
            sp.set("val", str(int(gap_pt * 100)))
    return size


def set_table(sh, rows, size=None, widths=None, header_size=None, row_h=None, total_px=None):
    """Fill a table with `rows` (first row = header). Rows are added or removed as needed."""
    tbl = sh.table
    trs = tbl._tbl.findall(qn("a:tr"))
    body_proto = trs[-1] if len(trs) > 1 else trs[0]
    need = len(rows)
    while len(trs) < need:
        new = copy.deepcopy(body_proto)
        trs[-1].addnext(new)
        trs = tbl._tbl.findall(qn("a:tr"))
    for tr in trs[need:]:
        tbl._tbl.remove(tr)
    trs = tbl._tbl.findall(qn("a:tr"))
    ncols = len(tbl.columns)
    for ri, (tr, row) in enumerate(zip(trs, rows)):
        tcs = tr.findall(qn("a:tc"))
        for ci in range(ncols):
            txt = row[ci] if ci < len(row) else ""
            body = tcs[ci].find(qn("a:txBody"))
            ps = body.findall(qn("a:p"))
            for extra in ps[1:]:
                body.remove(extra)
            _set_par(ps[0], txt, (header_size if ri == 0 and header_size else size))
    if row_h:
        for tr in tbl._tbl.findall(qn("a:tr")):
            tr.set("h", str(int(row_h * 9525)))
    if widths:
        total = int(total_px * 9525) if total_px else sum(c.width for c in tbl.columns)
        for col, frac in zip(tbl.columns, widths):
            col.width = Emu(int(total * frac))


def table_size(rows, width_px, height_px, widths=None, max_pt=14, min_pt=8):
    """Choose a font size at which all rows fit the available height (estimated)."""
    ncols = len(rows[0])
    fr = widths or [1 / ncols] * ncols
    size = max_pt
    while size > min_pt:
        total = 0
        for row in rows:
            lines = max(est_lines(str(c), width_px * fr[i] - 16, size) for i, c in enumerate(row))
            total += lines * size * 1.333 * 1.2 + 14
        if total <= height_px:
            break
        size -= 0.5
    return size


def replace_chart(slide, sid, categories, series, number_format="#,##0"):
    sh = shape(slide, sid)
    cd = CategoryChartData(number_format=number_format)
    cd.categories = categories
    for name, vals in series:
        cd.add_series(name, vals)
    sh.chart.replace_data(cd)
    return sh.chart


def remove(slide, sid):
    sh = shape(slide, sid)
    sh._element.getparent().remove(sh._element)


def put_picture(slide, path, box, remove_ids=(), name=None):
    """Place an image inside box=(l,t,w,h) in px (96 dpi), keeping its aspect ratio, centred."""
    for sid in remove_ids:
        remove(slide, sid)
    l, t, w, h = box
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    pic = slide.shapes.add_picture(str(path), Emu(int((l + (w - pw) / 2) * 9525)), Emu(int((t + (h - ph) / 2) * 9525)),
                                   Emu(int(pw * 9525)), Emu(int(ph * 9525)))
    if name:
        pic.name = name
        pic._element.nvPicPr.cNvPr.set("descr", name)
    return pic


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def replace_everywhere(prs, mapping):
    """Replace text in slide layouts and masters (footers)."""
    for m in prs.slide_masters:
        shapes = list(m.shapes)
        for lay in m.slide_layouts:
            shapes += list(lay.shapes)
        for sh in shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        for a, b in mapping.items():
                            if a in r.text:
                                r.text = r.text.replace(a, b)


def drop_slide_notes_text(prs):
    for s in prs.slides:
        if s.has_notes_slide:
            s.notes_slide.notes_text_frame.text = ""


def style_chart(chart, title, colors, number_format="#,##0", legend=True, labels=True, label_pt=8, axis_title=None):
    """Re-title and re-colour a template chart after replace_data()."""
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_LEGEND_POSITION
    from pptx.util import Pt

    chart.has_title = True
    chart.chart_title.text_frame.text = title
    for p in chart.chart_title.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(13)
            r.font.bold = True
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(10)
    va = chart.value_axis
    va.minimum_scale = 0
    va.maximum_scale = None
    va.major_unit = None
    va.has_major_gridlines = True
    va.tick_labels.number_format = number_format
    va.tick_labels.number_format_is_linked = False
    va.tick_labels.font.size = Pt(10)
    chart.category_axis.tick_labels.font.size = Pt(10)
    if axis_title:
        va.has_title = True
        va.axis_title.text_frame.text = axis_title
        for p in va.axis_title.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(10)
                r.font.bold = False
    plot = chart.plots[0]
    try:
        plot.vary_by_categories = False
    except Exception:
        pass
    plot.has_data_labels = labels
    if labels:
        dl = plot.data_labels
        dl.number_format = number_format
        dl.number_format_is_linked = False
        dl.font.size = Pt(label_pt)
        dl.show_value = True
    for s, col in zip(plot.series, colors):
        if labels:
            sdl = s.data_labels
            sdl.number_format = number_format
            sdl.number_format_is_linked = False
            sdl.font.size = Pt(label_pt)
            sdl.show_value = True
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = RGBColor.from_string(col)
