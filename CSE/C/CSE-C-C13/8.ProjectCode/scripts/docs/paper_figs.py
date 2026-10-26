"""Compact figures for the two-column IEEE paper -> docs/figures/paper_*.png (drawn at column width so text stays legible).

Architecture and flow are drawn from the real code path (frontend/src/lib/vaultCrypto.js, backend/app/api/*.py); the results chart reads
docs/metrics/metrics.json through facts.py; the output screens are crops of the real 1440x900 captures in docs/screenshots/.

make() returns {"arch", "flow", "results", "tamper", "share", "audit", "files"} -> absolute PNG paths.
Fig. 1 = arch, Fig. 2 = flow, Fig. 3 = results (paper_fig3.png), Fig. 4/5 = share / audit screens (or files).
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image

from . import facts as F

NAVY, BLUE, TEAL, ORANGE, GREEN, RED, GREY = "#1B2A41", "#2F6DB5", "#1E9E8F", "#E08A1E", "#3C9D5D", "#C0392B", "#8A94A6"
PALE = {"blue": "#E4EEF9", "teal": "#DFF3EF", "orange": "#FCEBD3", "green": "#E3F3E8", "grey": "#EEF0F4", "red": "#F9E0DC"}
NL = chr(10)


def _save(fig, name):
    os.makedirs(F.FIGS, exist_ok=True)
    p = os.path.join(F.FIGS, name)
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def _canvas(w, h, xmax, ymax):
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def _box(ax, x, y, w, h, text, fc="grey", ec=NAVY, fs=5.6, bold=False, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1.2", fc=PALE.get(fc, fc), ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=NAVY, fontweight="bold" if bold else "normal", linespacing=1.15)


def _arrow(ax, x1, y1, x2, y2, color=NAVY, style="-|>", lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=6, lw=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0))


def arch():
    fig, ax = _canvas(3.5, 2.9, 100, 83)
    _box(ax, 1, 56, 98, 26, "", "blue")
    ax.text(50, 79, "Browser: React 19 + Vite (trusted crypto endpoint)", ha="center", fontsize=5.2, fontweight="bold", color=NAVY)
    _box(ax, 4, 59, 28, 15, "Key vault" + NL + "RSA-2048 key pair," + NL + "PBKDF2 120,000 it." + NL + "-> AES-GCM wraps" + NL + "private key", "white", fs=4.4)
    _box(ax, 36, 59, 28, 15, "File crypto" + NL + "random 256-bit FEK," + NL + "AES-256-GCM," + NL + "12-byte IV," + NL + "SHA-256 of file", "white", fs=4.4)
    _box(ax, 68, 59, 28, 15, "Key wrapping" + NL + "RSA-OAEP / SHA-256" + NL + "per recipient;" + NL + "UI: files, sharing," + NL + "audit, security", "white", fs=4.4)
    ax.text(50, 53.2, "HTTP / JSON + ciphertext (JWT bearer token)", ha="center", fontsize=4.6, color=GREY, style="italic")
    _arrow(ax, 50, 56, 50, 50.5, style="<|-|>")
    _box(ax, 1, 20, 98, 29, "", "grey")
    ax.text(50, 46, "FastAPI backend (24 endpoints, port 8413)", ha="center", fontsize=5.2, fontweight="bold", color=NAVY)
    _box(ax, 4, 23, 22, 18, "Auth" + NL + "bcrypt cost 12," + NL + "JWT HS256," + NL + "login throttle", "white", fs=4.4)
    _box(ax, 28, 23, 22, 18, "RBAC" + NL + "owner / editor /" + NL + "viewer checked" + NL + "per request", "white", fs=4.4)
    _box(ax, 52, 23, 22, 18, "Files + sharing" + NL + "25 MB limit," + NL + "stores ciphertext," + NL + "wrapped keys", "white", fs=4.4)
    _box(ax, 76, 23, 20, 18, "Audit log" + NL + "SHA-256" + NL + "hash chain," + NL + "verify route", "white", fs=4.4)
    _arrow(ax, 27, 20, 27, 14.5)
    _arrow(ax, 73, 20, 73, 14.5)
    _box(ax, 1, 2, 58, 12, "SQL database (SQLite / PostgreSQL)" + NL + "users, files, file_permissions, audit_logs", "orange", fs=4.6)
    _box(ax, 62, 2, 37, 12, "storage/encrypted/" + NL + "ciphertext only", "green", fs=4.6)
    return _save(fig, "paper_arch.png")


def flow():
    fig, ax = _canvas(3.5, 3.1, 100, 88)
    ax.text(25.5, 85, "Upload and share", ha="center", fontsize=5.4, fontweight="bold", color=NAVY)
    ax.text(75.5, 85, "Download", ha="center", fontsize=5.4, fontweight="bold", color=NAVY)
    left = [("Generate random 256-bit FEK" + NL + "and 12-byte IV", "blue"),
            ("AES-256-GCM encrypt file;" + NL + "SHA-256 of plaintext", "blue"),
            ("Wrap FEK with owner's" + NL + "RSA-2048 public key", "blue"),
            ("POST ciphertext, IV, wrapped FEK," + NL + "hash (JWT, <= 25 MB)", "orange"),
            ("Server stores ciphertext under a" + NL + "random name; audit event", "green"),
            ("Share: owner unwraps FEK, re-wraps" + NL + "with recipient key + role", "teal")]
    right = [("GET download; server checks" + NL + "role (owner / editor / viewer)", "orange"),
             ("Ciphertext + IV + this" + NL + "user's wrapped FEK; audit", "green"),
             ("Unlock: PBKDF2 key opens" + NL + "private key (in memory)", "blue"),
             ("RSA-OAEP unwrap the FEK", "blue"),
             ("AES-GCM decrypt (tag check)," + NL + "compare SHA-256", "blue"),
             ("Match: save file." + NL + "Mismatch: reject", "teal")]
    y = 73
    for (t, c), (t2, c2) in zip(left, right):
        _box(ax, 2, y, 47, 9.2, t, c, fs=4.2)
        _box(ax, 52, y, 47, 9.2, t2, c2, fs=4.2)
        y -= 12.6
    for i in range(5):
        _arrow(ax, 25.5, 73 - i * 12.6, 25.5, 73 - i * 12.6 - 3.2)
        _arrow(ax, 75.5, 73 - i * 12.6, 75.5, 73 - i * 12.6 - 3.2)
    return _save(fig, "paper_flow.png")


def results():
    """Fig. 3: (a) AES-256-GCM / SHA-256 latency vs size, (b) encrypted vs plain transfer."""
    sizes = sorted(int(k) for k in F.AES)
    lab = {1024: "1K", 65536: "64K", 1048576: "1M", 10485760: "10M", 26214400: "25M"}
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.5, 1.85), gridspec_kw={"width_ratios": [1.05, 1]})
    x = np.arange(len(sizes))
    for key, name, col, mk in (("encrypt", "AES enc", NAVY, "o"), ("decrypt", "AES dec", TEAL, "s"), ("sha256", "SHA-256", ORANGE, "^")):
        a.plot(x, [F.AES[str(s)][key]["median"] for s in sizes], color=col, marker=mk, ms=2.6, lw=1.0, label=name)
    a.set_yscale("log")
    a.set_xticks(x)
    a.set_xticklabels([lab[s] for s in sizes], fontsize=5.4)
    a.tick_params(axis="y", labelsize=5.4)
    a.set_xlabel("Plaintext size (B)", fontsize=5.6)
    a.set_ylabel("Median latency (ms)", fontsize=5.6)
    a.set_title("(a) Web Crypto", fontsize=6, fontweight="bold")
    a.legend(fontsize=5, frameon=False, loc="upper left", handlelength=1.4)
    a.grid(color="#E3E8EF", lw=0.5)
    e_sizes = sorted(int(k) for k in F.E2E)
    xe = np.arange(len(e_sizes))
    w = 0.2
    series = [("plain_up", "plain up", GREY), ("encrypted_up", "enc. up", NAVY), ("plain_down", "plain down", "#B4BDCB"), ("encrypted_down", "enc. down", TEAL)]
    for i, (key, name, col) in enumerate(series):
        b.bar(xe + (i - 1.5) * w, [F.E2E[str(s)][key]["median"] for s in e_sizes], w, color=col, label=name)
    b.set_xticks(xe)
    b.set_xticklabels([lab[s] for s in e_sizes], fontsize=5.4)
    b.tick_params(axis="y", labelsize=5.4)
    b.set_xlabel("File size (B)", fontsize=5.6)
    b.set_ylabel("Median time (ms)", fontsize=5.6)
    b.set_title("(b) End to end", fontsize=6, fontweight="bold")
    b.legend(fontsize=4.8, frameon=False, loc="upper left", handlelength=1.0)
    b.grid(axis="y", color="#E3E8EF", lw=0.5)
    for ax_ in (a, b):
        for s in ("top", "right"):
            ax_.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax_.spines[s].set_linewidth(0.6)
    fig.tight_layout(pad=0.3, w_pad=0.8)
    return _save(fig, "paper_fig3.png")


def tamper():
    """Compact tamper-detection bars (optional extra figure)."""
    tam = F.TAMPER["audit_tamper"]
    rows = [(k.replace("_", " "), v["detected"], v["trials"]) for k, v in tam.items()]
    bf = F.TAMPER["ciphertext_bitflip"]
    rows.append(("ciphertext bit flip", bf["detected"], bf["trials"]))
    rows.sort(key=lambda r: r[1] / r[2])
    fig, ax = plt.subplots(figsize=(3.5, 1.9))
    y = np.arange(len(rows))
    for yy, (n, d, t) in zip(y, rows):
        ax.barh(yy, max(d / t * 100, 1.0), color=TEAL if d == t else RED, height=0.6)
        ax.text(2 if d == 0 else 98, yy, f"{d}/{t}", va="center", ha="left" if d == 0 else "right", fontsize=4.8, color=NAVY if d == 0 else "white", fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=5)
    ax.set_xlim(0, 100)
    ax.tick_params(axis="x", labelsize=5)
    ax.set_xlabel("Tampering detected (% of trials)", fontsize=5.4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(pad=0.3)
    return _save(fig, "paper_tamper.png")


def _crop(src, box, out):
    im = Image.open(os.path.join(F.SHOTS, src)).convert("RGB").crop(box)
    p = os.path.join(F.FIGS, out)
    os.makedirs(F.FIGS, exist_ok=True)
    im.save(p, optimize=True)
    return p


def screens():
    """Crops of real captures: the share dialog (09), the audit log with verified chain (10) and the file detail (08)."""
    return {
        "share": _crop("09_share-access.png", (455, 78, 985, 825), "paper_shot_share.png"),
        "audit": _crop("10_audit-log.png", (270, 238, 1420, 640), "paper_shot_audit.png"),
        "files": _crop("08_file-detail.png", (270, 90, 1420, 700), "paper_shot_files.png"),
    }


def make():
    s = screens()
    return {"arch": arch(), "flow": flow(), "results": results(), "tamper": tamper(), "share": s["share"], "audit": s["audit"], "files": s["files"]}


if __name__ == "__main__":
    for k, v in make().items():
        print(k, v)
