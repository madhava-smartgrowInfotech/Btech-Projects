"""Seating charts: one landscape A4 page per hall with the seat grid, colour-coded by paper."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from app.services.engine.graph import seat_label
from app.services.exports.data import PlanExport, paper_hex
from app.services.exports.pdf_common import (
    FONT, FONT_BOLD, FONT_MONO, HAIRLINE, INK, MUTED, draw_logo, fit_text, generated_at, register_fonts, tint,
)

MARGIN = 28


def _page(c: canvas.Canvas, export: PlanExport, index: int, total: int) -> None:
    hall_export = export.halls[index]
    hall = hall_export.hall
    width, height = landscape(A4)

    # Header
    draw_logo(c, MARGIN, height - MARGIN - 18)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 15)
    c.drawRightString(width - MARGIN, height - MARGIN - 12, f"{hall.code} · {hall.name}")
    c.setFont(FONT, 8.5)
    c.setFillColor(MUTED)
    where = ", ".join(x for x in (hall.building, f"floor {hall.floor}" if hall.floor.isdigit() else hall.floor) if x)
    c.drawRightString(width - MARGIN, height - MARGIN - 25, f"{export.title}  ·  {where}")
    c.setStrokeColor(HAIRLINE)
    c.line(MARGIN, height - MARGIN - 34, width - MARGIN, height - MARGIN - 34)

    # Grid geometry
    top = height - MARGIN - 70
    bottom = MARGIN + 72
    label_w = 16
    aisles = set(hall.aisles_after_cols or [])
    gap_units = sum(1 for col in range(1, hall.cols) if col in aisles) * 0.4
    avail_w = width - 2 * MARGIN - label_w
    cell_w = min(avail_w / (hall.cols + gap_units), 72)
    cell_h = min((top - bottom) / hall.rows, cell_w * 0.72, 50)
    grid_w = cell_w * (hall.cols + gap_units)
    left = MARGIN + label_w + (avail_w - grid_w) / 2
    pad = 1.6

    # Front of hall
    c.setFillColor(tint("#898781", 0.75))
    c.roundRect(left + grid_w * 0.3, top + 14, grid_w * 0.4, 6, 3, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont(FONT_BOLD, 7)
    c.drawCentredString(left + grid_w / 2, top + 24, "FRONT OF HALL")

    seats = {(s.row, s.col): s for s in hall_export.seats}
    blocked = set(hall.blocked_seats or [])
    accessible = set(hall.accessible_seats or [])

    def x_of(col: int) -> float:
        extra = sum(0.4 for a in aisles if 0 < a <= col)
        return left + (col + extra) * cell_w

    c.setFont(FONT_BOLD, 7)
    for col in range(hall.cols):
        c.drawCentredString(x_of(col) + cell_w / 2, top + 4, str(col + 1))
    for r in range(hall.rows):
        y = top - (r + 1) * cell_h
        c.setFillColor(MUTED)
        c.setFont(FONT_BOLD, 7)
        c.drawCentredString(left - label_w / 2 - 2, y + cell_h / 2 - 2.5, seat_label(r, 0)[:-1])
        for col in range(hall.cols):
            x = x_of(col)
            label = seat_label(r, col)
            w, h = cell_w - 2 * pad, cell_h - 2 * pad
            if label in blocked:
                c.setStrokeColor(HAIRLINE)
                c.setDash(2, 2)
                c.roundRect(x + pad, y + pad, w, h, 3, stroke=1, fill=0)
                c.setDash()
                continue
            seat = seats.get((r, col))
            if seat is None:
                c.setStrokeColor(HAIRLINE)
                c.roundRect(x + pad, y + pad, w, h, 3, stroke=1, fill=0)
                c.setFillColor(MUTED)
                c.setFont(FONT, 6)
                c.drawString(x + pad + 2.5, y + pad + h - 7.5, label)
                continue
            hexc = paper_hex(seat.colour)
            c.setFillColor(tint(hexc, 0.8))
            c.roundRect(x + pad, y + pad, w, h, 3, stroke=0, fill=1)
            c.setFillColor(colors.HexColor(hexc))
            c.rect(x + pad, y + pad + h - 2.5, w, 2.5, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont(FONT_BOLD, 6.2)
            c.drawString(x + pad + 2.5, y + pad + h - 9.5, label)
            if label in accessible:
                c.drawRightString(x + pad + w - 2.5, y + pad + h - 9.5, "♿")
            size = 7.4 if cell_w > 52 else 6.4
            c.setFont(FONT_MONO, size)
            c.drawString(x + pad + 2.5, y + pad + h / 2 - 3, fit_text(seat.roll_no, FONT_MONO, size, w - 5))
            c.setFillColor(MUTED)
            c.setFont(FONT, 5.6)
            c.drawString(x + pad + 2.5, y + pad + 3, fit_text(seat.course_code, FONT, 5.6, w - 5))

    # Legend
    y = MARGIN + 44
    c.setFont(FONT_BOLD, 7.5)
    c.setFillColor(INK)
    c.drawString(MARGIN, y + 12, "Papers in this hall")
    x = MARGIN
    for item in hall_export.legend:
        text = f"{item['paper']} ({item['count']})"
        c.setFillColor(colors.HexColor(paper_hex(item["colour"])))
        c.roundRect(x, y, 8, 8, 1.5, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(FONT, 7.5)
        c.drawString(x + 11, y + 1, text)
        x += 11 + c.stringWidth(text, FONT, 7.5) + 14
        if x > width - MARGIN - 120:
            x, y = MARGIN, y - 12
    c.setFont(FONT, 7.5)
    c.setFillColor(MUTED)
    staff = ", ".join(hall_export.invigilators) or "not assigned"
    c.drawString(MARGIN, MARGIN + 22, f"{len(hall_export.seats)} of {hall.capacity} seats used · invigilator: {staff} · "
                                      "♿ accessible seat · dashed = not in use")

    # Footer
    c.setStrokeColor(HAIRLINE)
    c.line(MARGIN, MARGIN + 12, width - MARGIN, MARGIN + 12)
    c.setFont(FONT, 6.5)
    c.drawString(MARGIN, MARGIN + 2, f"{export.stamp} · generated {generated_at()}")
    c.drawRightString(width - MARGIN, MARGIN + 2, f"Page {index + 1} of {total}")


def seating_chart_pdf(export: PlanExport) -> bytes:
    register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    c.setTitle(f"Seating charts - {export.title}")
    c.setAuthor("SeatWise")
    for i in range(len(export.halls)):
        _page(c, export, i, len(export.halls))
        c.showPage()
    if not export.halls:
        c.setFont(FONT, 12)
        c.drawString(MARGIN, 500, "No seats in this selection.")
        c.showPage()
    c.save()
    return buffer.getvalue()
