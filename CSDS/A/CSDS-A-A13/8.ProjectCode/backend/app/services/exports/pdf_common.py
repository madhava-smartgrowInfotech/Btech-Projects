"""Fonts, colours and small drawing helpers shared by the PDF exports."""
from __future__ import annotations

from datetime import datetime, timezone

import qrcode
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.core.config import ASSETS_DIR

FONT = "SeatWiseSans"
FONT_BOLD = "SeatWiseSans-Bold"
FONT_MONO = "SeatWiseMono"
_registered = False

INK = colors.HexColor("#141833")
MUTED = colors.HexColor("#5f6377")
HAIRLINE = colors.HexColor("#d9dbe6")
BRAND = colors.HexColor("#493ee5")
TEAL = colors.HexColor("#5eead4")


def register_fonts() -> None:
    """DejaVu fonts (bundled, open licence) cover accented and non-Latin names."""
    global _registered
    if _registered:
        return
    folder = ASSETS_DIR / "fonts"
    pdfmetrics.registerFont(TTFont(FONT, str(folder / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(folder / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_MONO, str(folder / "DejaVuSansMono.ttf")))
    pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_BOLD, italic=FONT, boldItalic=FONT_BOLD)
    _registered = True


def tint(hex_colour: str, amount: float) -> colors.Color:
    """Mix a colour with white (amount = share of white)."""
    base = colors.HexColor(hex_colour)
    return colors.Color(base.red + (1 - base.red) * amount, base.green + (1 - base.green) * amount,
                        base.blue + (1 - base.blue) * amount)


def draw_logo(c, x: float, y: float, size: float = 18) -> None:
    """The SeatWise mark: a 3 x 3 seat grid in an alternating pattern."""
    c.setFillColor(BRAND)
    c.roundRect(x, y, size, size, size * 0.25, stroke=0, fill=1)
    cell = size * 6 / 32
    for i in range(9):
        r, col = divmod(i, 3)
        c.setFillColor(TEAL if (r + col) % 2 else colors.white)
        cx = x + size * (5 + col * 8) / 32
        cy = y + size - size * (5 + r * 8) / 32 - cell
        c.roundRect(cx, cy, cell, cell, cell * 0.3, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, size * 0.72)
    c.drawString(x + size + 5, y + size * 0.26, "Seat")
    width = pdfmetrics.stringWidth("Seat", FONT_BOLD, size * 0.72)
    c.setFillColor(BRAND)
    c.drawString(x + size + 5 + width, y + size * 0.26, "Wise")


def draw_qr(c, data: str, x: float, y: float, size: float) -> None:
    """A crisp vector QR code (one rectangle per dark module)."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    module = size / n
    c.setFillColor(colors.black)
    for r, line in enumerate(matrix):
        for col, dark in enumerate(line):
            if dark:
                c.rect(x + col * module, y + size - (r + 1) * module, module + 0.05, module + 0.05, stroke=0, fill=1)


def generated_at() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%d %b %Y %H:%M")


def fit_text(text: str, font: str, size: float, width: float) -> str:
    if pdfmetrics.stringWidth(text, font, size) <= width:
        return text
    while text and pdfmetrics.stringWidth(text + "…", font, size) > width:
        text = text[:-1]
    return text + "…"
