"""SVG drawing helpers written in Python (no JS/templating libraries needed).

`network_map()` draws regions, hubs and allocation spokes on an equirectangular
projection of the network's bounding box. `line_chart()` and `bar_chart()`
render small dashboard charts.
"""
from __future__ import annotations

import html

import numpy as np
import pandas as pd

PALETTE = ["#1f5f8b", "#c8552b", "#2c8c5a", "#8b4a9c", "#c9a227", "#1c9ca0", "#a83b6d",
           "#5c6b2f", "#d06a2d", "#3f57a6", "#7a5230", "#2f7f9d"]


def network_map(regions: pd.DataFrame, hubs: list[int], assign, demand, width=880, height=760) -> str:
    lat, lon = regions.lat.to_numpy(), regions.lon.to_numpy()
    pad = 1.2
    lat0, lat1, lon0, lon1 = lat.min() - pad, lat.max() + pad, lon.min() - pad, lon.max() + pad
    sx = (width - 40) / (lon1 - lon0)
    sy = (height - 40) / (lat1 - lat0)
    s = min(sx, sy)

    def xy(i):
        return 20 + (lon[i] - lon0) * s, height - 20 - (lat[i] - lat0) * s

    dmax = max(float(np.max(demand)), 1.0)
    colour = {h: PALETTE[k % len(PALETTE)] for k, h in enumerate(hubs)}
    parts = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" '
             f'>',
             f'<rect x="0" y="0" width="{width}" height="{height}" rx="10" fill="#f8fafc"/>']
    # spokes
    for i in range(len(regions)):
        h = int(assign[i])
        if h == i:
            continue
        x1, y1 = xy(i)
        x2, y2 = xy(h)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="{colour.get(h, "#999")}" stroke-width="1.2" stroke-opacity="0.55"/>')
    # regions
    for i in range(len(regions)):
        x, y = xy(i)
        r = 3 + 9 * (float(demand[i]) / dmax) ** 0.5
        c = colour.get(int(assign[i]), "#999")
        name = html.escape(str(regions.city[i]))
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" fill-opacity="0.75" '
                     f'stroke="#fff" stroke-width="1"><title>{name}: {int(demand[i]):,} orders -> '
                     f'{html.escape(str(regions.city[int(assign[i])]))}</title></circle>')
    # hubs
    for h in hubs:
        x, y = xy(h)
        parts.append(f'<rect x="{x-9:.1f}" y="{y-9:.1f}" width="18" height="18" rx="3" fill="{colour[h]}" '
                     f'stroke="#111" stroke-width="1.5"><title>HUB {html.escape(str(regions.city[h]))}</title></rect>')
        label = html.escape(str(regions.city[h]))
        parts.append(f'<text x="{x+13:.1f}" y="{y+5:.1f}" font-size="13" font-weight="700" fill="#f8fafc" '
                     f'stroke="#f8fafc" stroke-width="4">{label}</text>')
        parts.append(f'<text x="{x+13:.1f}" y="{y+5:.1f}" font-size="13" font-weight="700" fill="#111">{label}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_chart(labels: list[str], series: dict[str, list[float]], width=880, height=260, y_label="") -> str:
    vals = [v for s in series.values() for v in s if v is not None]
    if not vals:
        return ""
    lo, hi = min(vals) * 0.95, max(vals) * 1.05
    l, r, t, b = 70, 20, 20, 50
    n = len(labels)

    def x(i):
        return l + (width - l - r) * (i / max(n - 1, 1))

    def y(v):
        return t + (height - t - b) * (1 - (v - lo) / (hi - lo or 1))

    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" >']
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        out.append(f'<line x1="{l}" x2="{width-r}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#e3e7ec"/>'
                   f'<text x="{l-6}" y="{y(v)+4:.1f}" font-size="11" text-anchor="end" fill="#666">{_fmt(v)}</text>')
    step = max(1, n // 12)
    for i, lab in enumerate(labels):
        if i % step == 0 or i == n - 1:
            out.append(f'<text x="{x(i):.1f}" y="{height-b+18}" font-size="11" text-anchor="middle" fill="#666">{html.escape(lab)}</text>')
    for k, (name, s) in enumerate(series.items()):
        c = PALETTE[k % len(PALETTE)]
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s) if v is not None)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2.2"/>')
        out.append(f'<rect x="{l + 120*k}" y="{height-16}" width="12" height="12" fill="{c}"/>'
                   f'<text x="{l + 120*k + 16}" y="{height-6}" font-size="12" fill="#333">{html.escape(name)}</text>')
    if y_label:
        out.append(f'<text x="12" y="{t+8}" font-size="11" fill="#666">{html.escape(y_label)}</text>')
    out.append("</svg>")
    return "".join(out)


def bar_chart(labels: list[str], values: list[float], width=880, height=260, fmt=None, highlight: int | None = None) -> str:
    if not values:
        return ""
    hi = max(values) * 1.12
    l, r, t, b = 70, 20, 16, 70
    n = len(values)
    bw = (width - l - r) / n
    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" >']
    for i, (lab, v) in enumerate(zip(labels, values)):
        h = (height - t - b) * (v / hi if hi else 0)
        c = "#c8552b" if i == highlight else "#1f5f8b"
        out.append(f'<rect x="{l + i*bw + bw*0.15:.1f}" y="{height-b-h:.1f}" width="{bw*0.7:.1f}" height="{h:.1f}" fill="{c}" rx="3"/>')
        out.append(f'<text x="{l + i*bw + bw/2:.1f}" y="{height-b-h-5:.1f}" font-size="11" text-anchor="middle" fill="#333">{(fmt or _fmt)(v)}</text>')
        for j, line in enumerate(_wrap(lab, 16)[:3]):
            out.append(f'<text x="{l + i*bw + bw/2:.1f}" y="{height-b+14+j*13}" font-size="10.5" text-anchor="middle" fill="#555">{html.escape(line)}</text>')
    out.append("</svg>")
    return "".join(out)


def _fmt(v: float) -> str:
    if abs(v) >= 1e7:
        return f"{v/1e7:.2f} Cr"
    if abs(v) >= 1e5:
        return f"{v/1e5:.1f} L"
    if abs(v) >= 1e3:
        return f"{v/1e3:.0f}k"
    return f"{v:.2f}" if isinstance(v, float) and v < 10 else f"{v:.0f}"


def _wrap(text: str, n: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines
