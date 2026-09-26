"""Invigilator sheets: per hall, the seat-by-seat list with attendance and signature columns."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.services.exports.data import PlanExport, paper_hex
from app.services.exports.pdf_common import (
    BRAND, FONT, FONT_BOLD, FONT_MONO, HAIRLINE, INK, MUTED, draw_logo, generated_at, register_fonts, tint,
)

INSTRUCTIONS = [
    "Open the hall 20 minutes before the start. Seat every candidate exactly as listed - no changes without the controller.",
    "Check each candidate's identity against the roll number, then tick Present and ask for a signature.",
    "Candidates may not leave in the first 30 minutes or the last 15 minutes of the sitting.",
    "Phones, smart watches and notes stay in bags at the front of the hall.",
    "Record absentees before the first 30 minutes end and report any irregularity on this sheet.",
    "Collect scripts seat by seat and count them against the number present before anyone leaves.",
]


def _styles():
    return {
        "title": ParagraphStyle("t", fontName=FONT_BOLD, fontSize=15, leading=19, textColor=INK),
        "sub": ParagraphStyle("s", fontName=FONT, fontSize=9, leading=12, textColor=MUTED),
        "h": ParagraphStyle("h", fontName=FONT_BOLD, fontSize=9.5, leading=12, textColor=INK, spaceBefore=6),
        "body": ParagraphStyle("b", fontName=FONT, fontSize=8, leading=10.5, textColor=INK),
        "cell": ParagraphStyle("c", fontName=FONT, fontSize=8, leading=9.5, textColor=INK),
    }


def invigilator_pdf(export: PlanExport) -> bytes:
    register_fonts()
    st = _styles()
    buffer = io.BytesIO()

    def decorate(canvas, doc):
        width, height = A4
        canvas.saveState()
        draw_logo(canvas, 18 * mm, height - 16 * mm, 14)
        canvas.setFont(FONT, 7)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(width - 18 * mm, height - 12.5 * mm, "Invigilator sheet")
        canvas.setStrokeColor(HAIRLINE)
        canvas.line(18 * mm, 12 * mm, width - 18 * mm, 12 * mm)
        canvas.drawString(18 * mm, 8 * mm, f"{export.stamp} · generated {generated_at()}")
        canvas.drawRightString(width - 18 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm,
                            bottomMargin=18 * mm, title=f"Invigilator sheets - {export.title}", author="SeatWise")
    story = []
    for index, item in enumerate(export.halls):
        hall = item.hall
        present = sum(1 for s in item.seats if s.attendance == "present")
        absent = sum(1 for s in item.seats if s.attendance == "absent")
        story += [
            Paragraph(f"{hall.code} · {hall.name}", st["title"]),
            Paragraph(f"{export.title} · {hall.building or ''} · invigilator: {', '.join(item.invigilators) or 'not assigned'}", st["sub"]),
            Spacer(1, 6),
        ]
        paper_rows = [["Paper", "Courses", "Candidates"]] + [
            [p["paper"], Paragraph("<br/>".join(p["courses"]), st["cell"]), str(p["count"])] for p in item.legend]
        paper_rows.append(["Total", "", str(len(item.seats))])
        papers = Table(paper_rows, colWidths=[30 * mm, 110 * mm, 25 * mm])
        paper_style = [
            ("FONT", (0, 0), (-1, 0), FONT_BOLD, 8), ("FONT", (0, 1), (-1, -1), FONT, 8),
            ("FONT", (0, -1), (-1, -1), FONT_BOLD, 8), ("LINEBELOW", (0, 0), (-1, 0), 0.6, INK),
            ("LINEABOVE", (0, -1), (-1, -1), 0.4, HAIRLINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ]
        for i, p in enumerate(item.legend, start=1):
            paper_style.append(("BACKGROUND", (0, i), (0, i), tint(paper_hex(p["colour"]), 0.75)))
        papers.setStyle(TableStyle(paper_style))
        story += [papers, Spacer(1, 6), Paragraph("Instructions", st["h"])]
        story += [Paragraph(f"{n}. {text}", st["body"]) for n, text in enumerate(INSTRUCTIONS, start=1)]
        story.append(Spacer(1, 8))

        rows = [["Seat", "Roll no.", "Name", "Paper", "Present", "Signature"]]
        for s in item.seats:
            mark = "✓" if s.attendance == "present" else ("absent" if s.attendance == "absent" else "☐")
            rows.append([s.label, s.roll_no, Paragraph(s.full_name + (" ♿" if s.needs_accessible else ""), st["cell"]),
                         s.course_code, mark, ""])
        table = Table(rows, colWidths=[13 * mm, 24 * mm, 56 * mm, 22 * mm, 16 * mm, 43 * mm], repeatRows=1)
        style = [
            ("FONT", (0, 0), (-1, 0), FONT_BOLD, 8), ("FONT", (0, 1), (-1, -1), FONT, 8),
            ("FONT", (1, 1), (1, -1), FONT_MONO, 7.6), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 0), (-1, 0), BRAND), ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), 0.3, HAIRLINE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7fb")]),
            ("TOPPADDING", (0, 1), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 1), (-1, -1), 4.5),
        ]
        for i, s in enumerate(item.seats, start=1):
            style.append(("LINEBEFORE", (0, i), (0, i), 3, colors.HexColor(paper_hex(s.colour))))
        table.setStyle(TableStyle(style))
        story.append(table)
        summary = (f"Present: {present if (present or absent) else '______'}    Absent: {absent if (present or absent) else '______'}"
                   f"    Scripts collected: ______")
        story.append(KeepTogether([
            Spacer(1, 12), Paragraph(summary, st["body"]), Spacer(1, 18),
            Table([["Invigilator signature", "", "Controller signature", ""]],
                  colWidths=[36 * mm, 50 * mm, 36 * mm, 50 * mm],
                  style=TableStyle([("FONT", (0, 0), (-1, -1), FONT, 8), ("LINEBELOW", (1, 0), (1, 0), 0.5, INK),
                                    ("LINEBELOW", (3, 0), (3, 0), 0.5, INK)])),
        ]))
        if index < len(export.halls) - 1:
            story.append(PageBreak())
    if not story:
        story = [Paragraph("No seats in this selection.", st["body"])]
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return buffer.getvalue()
