"""Seat slips with a QR code that opens the candidate's seat in the public lookup."""
from __future__ import annotations

import io
from dataclasses import dataclass
from urllib.parse import quote

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.config import get_settings
from app.services.exports.pdf_common import (
    BRAND, FONT, FONT_BOLD, FONT_MONO, HAIRLINE, INK, MUTED, draw_logo, draw_qr, fit_text, generated_at, register_fonts,
)

PER_PAGE_COLS, PER_PAGE_ROWS = 2, 3


@dataclass
class Slip:
    roll_no: str
    full_name: str
    course_code: str
    course_name: str
    when: str
    hall_code: str
    hall_name: str
    where: str
    seat: str
    accessible: bool
    stamp: str


def lookup_url(roll_no: str) -> str:
    return f"{get_settings().public_base_url}/lookup/{quote(roll_no)}"


def _slip(c: canvas.Canvas, s: Slip, x: float, y: float, w: float, h: float) -> None:
    c.setStrokeColor(HAIRLINE)
    c.setDash(3, 3)
    c.roundRect(x, y, w, h, 8, stroke=1, fill=0)
    c.setDash()
    pad = 6 * mm
    top = y + h - pad
    qr = 22 * mm

    draw_logo(c, x + pad, top - 13, 13)
    draw_qr(c, lookup_url(s.roll_no), x + w - pad - qr, top - qr, qr)
    c.setFont(FONT, 6)
    c.setFillColor(MUTED)
    c.drawCentredString(x + w - pad - qr / 2, top - qr - 8, "Scan to check your seat")

    text_w = w - 2 * pad - qr - 4 * mm
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 13)
    c.drawString(x + pad, top - 33, fit_text(s.full_name, FONT_BOLD, 13, text_w))
    c.setFont(FONT_MONO, 9.5)
    c.setFillColor(MUTED)
    c.drawString(x + pad, top - 46, s.roll_no)

    rows = [
        (s.course_code, s.course_name),
        ("When", s.when),
        ("Hall", f"{s.hall_code} · {s.hall_name}"),
        ("Where", s.where or "-"),
    ]
    ly = top - qr - 26
    for label, value in rows:
        c.setFillColor(MUTED)
        c.setFont(FONT_BOLD, 7.5)
        c.drawString(x + pad, ly, label)
        c.setFillColor(INK)
        c.setFont(FONT, 8.5)
        c.drawString(x + pad + 50, ly, fit_text(value, FONT, 8.5, w - 2 * pad - 50))
        ly -= 13

    badge_w, badge_h = 34 * mm, 17 * mm
    c.setFillColor(BRAND)
    c.roundRect(x + pad, y + pad, badge_w, badge_h, 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(FONT, 7)
    c.drawString(x + pad + 3 * mm, y + pad + badge_h - 5 * mm, "SEAT" + ("  ♿" if s.accessible else ""))
    c.setFont(FONT_BOLD, 22)
    c.drawString(x + pad + 3 * mm, y + pad + 3 * mm, s.seat)

    c.setFillColor(MUTED)
    c.setFont(FONT, 7)
    note_x = x + pad + badge_w + 4 * mm
    c.drawString(note_x, y + pad + 9 * mm, "Bring photo ID.")
    c.drawString(note_x, y + pad + 5.5 * mm, "Arrive 20 minutes early.")
    c.drawString(note_x, y + pad + 2 * mm, "Phones stay in your bag.")


def slips_pdf(slips: list[Slip], title: str, single: bool = False) -> bytes:
    """Six slips per A4 page (cut along the dashed lines), or one larger slip for a candidate's own download."""
    register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(title)
    c.setAuthor("SeatWise")
    width, height = A4
    margin, gap = 10 * mm, 6 * mm
    if single and slips:
        w, h = 120 * mm, 95 * mm
        _slip(c, slips[0], (width - w) / 2, height - 25 * mm - h, w, h)
        c.setFont(FONT, 7)
        c.setFillColor(MUTED)
        c.drawCentredString(width / 2, height - 32 * mm - h, "Keep this slip with you on the day. "
                                                            "Seats can change until the day before - scan the code to check.")
        c.drawString(margin, 5 * mm, f"{slips[0].stamp} · generated {generated_at()}")
        c.showPage()
        c.save()
        return buffer.getvalue()
    per_page = PER_PAGE_COLS * PER_PAGE_ROWS
    w = (width - 2 * margin - (PER_PAGE_COLS - 1) * gap) / PER_PAGE_COLS
    h = (height - 2 * margin - 6 * mm - (PER_PAGE_ROWS - 1) * gap) / PER_PAGE_ROWS
    for i, slip in enumerate(slips):
        pos = i % per_page
        if i and pos == 0:
            c.showPage()
        if pos == 0:
            c.setFont(FONT, 6.5)
            c.setFillColor(MUTED)
            c.drawString(margin, 5 * mm, f"{slip.stamp} · generated {generated_at()}")
        col, row = pos % PER_PAGE_COLS, pos // PER_PAGE_COLS
        _slip(c, slip, margin + col * (w + gap), height - margin - (row + 1) * h - row * gap, w, h)
    if not slips:
        c.setFont(FONT, 12)
        c.drawString(margin, height / 2, "No slips in this selection.")
    c.showPage()
    c.save()
    return buffer.getvalue()
