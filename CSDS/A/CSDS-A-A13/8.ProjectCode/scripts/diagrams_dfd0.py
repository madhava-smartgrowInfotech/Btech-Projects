"""Context diagram (DFD level 0)."""
from __future__ import annotations

import math

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, INDIGO, INDIGO_L, Canvas

CX, CY, A, B = 52, 28, 14.5, 19


def edge_x(y: float, side: str) -> float:
    dx = A * math.sqrt(max(0.0, 1 - ((y - CY) / B) ** 2))
    return CX - dx if side == "l" else CX + dx


def dfd0(out):
    c = Canvas(10.4, 5.6)
    c.ellipse(CX, CY, 2 * A, 2 * B, "0\nSeatWise\nexam seating\nmanagement\nsystem", fc=INDIGO_L, ec=INDIGO, fs=9.5)
    c.box(1, 36, 16, 10, "Exam controller\n(administrator)", fc=BLUE_L, fs=8, bold=True)
    c.box(1, 9, 16, 10, "Invigilator", fc=GREEN_L, fs=8.5, bold=True)
    c.box(87, 23, 16, 10, "Candidate", fc=AMBER_L, fs=8.5, bold=True)
    # administrator
    y_in, y_out = 44, 37.5
    c.arrow((17, y_in), (edge_x(y_in, "l"), y_in))
    c.text(28.5, y_in + 4.6, "course, hall, candidate and\ntimetable files, rules, seed,\nswap and publish commands", fs=6.6)
    c.arrow((edge_x(y_out, "l"), y_out), (17, y_out), ls="--")
    c.text(28.5, y_out - 4.6, "validation reports, plans,\nscorecards, charts, lists,\nanalytics, audit trail", fs=6.6)
    # invigilator
    y_in, y_out = 17.5, 11
    c.arrow((17, y_in), (edge_x(y_in, "l"), y_in))
    c.text(28.5, y_in + 4.0, "attendance marks,\nscanned slips, submit", fs=6.6)
    c.arrow((edge_x(y_out, "l"), y_out), (17, y_out), ls="--")
    c.text(28.5, y_out - 3.8, "my halls, seat maps,\nregister counts", fs=6.6)
    # candidate
    y_in, y_out = 31.2, 24.8
    c.arrow((87, y_in), (edge_x(y_in, "r"), y_in))
    c.text(76.5, y_in + 3.0, "candidate ID", fs=6.8)
    c.arrow((edge_x(y_out, "r"), y_out), (87, y_out), ls="--")
    c.text(76.5, y_out - 4.0, "hall, seat, hall map,\nQR seat slip (PDF)", fs=6.6)
    c.text(52, 3.6, "Context diagram (level 0). Solid arrows: data in. Dashed arrows: data out.", fs=7.6, italic=True)
    c.save(out)
