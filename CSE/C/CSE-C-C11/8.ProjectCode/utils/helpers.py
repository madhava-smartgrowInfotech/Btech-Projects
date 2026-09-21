"""Miscellaneous formatting/helper functions used across UI pages."""
from __future__ import annotations

from datetime import date
import calendar


def format_currency(amount: float, symbol: str = "\u20b9") -> str:
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    return f"{symbol}{amount:,.2f}"


def month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def current_month_year() -> tuple[int, int]:
    today = date.today()
    return today.month, today.year


def pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def month_name(month: int) -> str:
    return calendar.month_name[month]
