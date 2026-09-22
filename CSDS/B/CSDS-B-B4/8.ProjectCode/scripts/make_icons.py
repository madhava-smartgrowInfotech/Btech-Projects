"""Renders the PWA / favicon PNG icons for the web app from the logo geometry.

Run: venv\Scripts\python scripts\make_icons.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "frontend" / "public"
SS = 4  # supersampling factor for smooth edges


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _bezier(p0, p1, p2, n=24):
    return [
        ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1])
        for t in (i / n for i in range(1, n + 1))
    ]


def shield_points(scale: float, ox: float, oy: float):
    # Symmetric version of the SVG shield path (viewBox 32x32).
    right = [(16, 2.4), (27.2, 6.6), (27.2, 14.8)] + _bezier((27.2, 14.8), (27.2, 25.2), (16, 29.6))
    left = [(32 - x, y) for x, y in reversed(right[:-1])]
    return [(ox + x * scale, oy + y * scale) for x, y in right + left]


def render(size: int, padding: float, background: tuple[int, int, int] | None, rounded: bool) -> Image.Image:
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if background:
        if rounded:
            draw.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=background + (255,))
        else:
            draw.rectangle([0, 0, S, S], fill=background + (255,))
    inner = S * (1 - 2 * padding)
    scale = inner / 32
    ox = oy = S * padding
    # gradient shield: draw into a mask, then fill with a vertical gradient
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(shield_points(scale, ox, oy), fill=255)
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    top, mid, bot = (45, 212, 191), (13, 148, 136), (17, 94, 89)
    for y in range(S):
        t = y / S
        c = _lerp(top, mid, t / 0.55) if t < 0.55 else _lerp(mid, bot, (t - 0.55) / 0.45)
        gd.line([(0, y), (S, y)], fill=c + (255,))
    img.paste(grad, (0, 0), mask)
    # check mark
    w = int(2.7 * scale)
    pts = [(10.6, 16.3), (14.4, 20.0), (21.7, 11.9)]
    pts = [(ox + x * scale, oy + y * scale) for x, y in pts]
    draw.line(pts, fill=(255, 255, 255, 255), width=w, joint="curve")
    for p in (pts[0], pts[-1]):
        draw.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=(255, 255, 255, 255))
    # saffron clock badge
    cx, cy, r = ox + 24.6 * scale, oy + 24.4 * scale, 3.6 * scale
    ring = 1.4 * scale
    draw.ellipse([cx - r - ring, cy - r - ring, cx + r + ring, cy + r + ring], fill=(background or (255, 255, 255)) + (255,))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 158, 11, 255))
    hw = max(1, int(1.1 * scale))
    draw.line([(cx, cy), (cx, cy - 2.0 * scale)], fill=(255, 255, 255, 255), width=hw)
    draw.line([(cx, cy), (cx + 1.5 * scale, cy + 0.9 * scale)], fill=(255, 255, 255, 255), width=hw)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dark = (11, 18, 21)
    render(192, 0.14, dark, True).save(OUT / "pwa-192.png")
    render(512, 0.14, dark, True).save(OUT / "pwa-512.png")
    render(512, 0.22, dark, False).save(OUT / "pwa-maskable-512.png")
    render(180, 0.12, dark, False).save(OUT / "apple-touch-icon.png")
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
