"""Shared visual design tokens for a clean, consistent UI."""

import customtkinter as ctk

BG = "#0f172a"          # slate-900
SURFACE = "#1e293b"      # slate-800
SURFACE_ALT = "#273549"
BORDER = "#334155"       # slate-700
TEXT = "#f1f5f9"         # slate-100
TEXT_MUTED = "#94a3b8"   # slate-400
ACCENT = "#22d3ee"        # cyan-400
ACCENT_HOVER = "#06b6d4"
ACCENT_SOFT = "#164e63"
SUCCESS = "#4ade80"
WARNING = "#fbbf24"
DANGER = "#f87171"

FONT_FAMILY = "Segoe UI"


def font(size=14, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def apply_appearance():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def section_card(parent, **kwargs):
    defaults = dict(fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def primary_button(parent, **kwargs):
    defaults = dict(
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        text_color="#0f172a",
        corner_radius=10,
        font=font(14, "bold"),
        height=40,
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def secondary_button(parent, **kwargs):
    defaults = dict(
        fg_color=SURFACE_ALT,
        hover_color=BORDER,
        text_color=TEXT,
        corner_radius=10,
        font=font(14),
        height=40,
        border_width=1,
        border_color=BORDER,
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def danger_button(parent, **kwargs):
    defaults = dict(
        fg_color="#7f1d1d",
        hover_color="#991b1b",
        text_color=TEXT,
        corner_radius=10,
        font=font(14),
        height=40,
    )
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)
