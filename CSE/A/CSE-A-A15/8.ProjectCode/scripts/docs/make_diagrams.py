"""CipherVeil design diagrams 01-06 (matplotlib, 150 dpi) -> docs/diagrams/.  Diagrams 07-11 live in diagrams_more.py.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; writes all eleven
Every diagram mirrors the code: backend/app/{main,auth,db,config}.py, routes/*.py and services/{crypto,lsb,metrics,pipeline,plots,robustness,benchmark}.py.
"""
from __future__ import annotations

import math
from pathlib import Path

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 01 architecture
def architecture():
    fig, ax = canvas(9.6, 7.3, 100, 76)
    panel(ax, 1, 63, 98, 12.5, "TIER 1 - PRESENTATION (browser)", fc=PALE_BLUE, fs=9)
    box(ax, 25, 67.2, 44, 6.6, "React 18 + Vite + Tailwind  :5315\nLanding · Login · Keys · Send · Receive ·\nAnalysis · Robustness · Operation log", BLUE, fs=7.2)
    box(ax, 62, 67.2, 25, 6.6, "axios client (src/api.js)\nBearer JWT kept in\nlocalStorage", BLUE, fs=7.2)
    box(ax, 87, 67.2, 20, 6.6, "Recharts + three.js\ncharts, landing\nbackdrop", GREY, fs=7.2)
    panel(ax, 1, 31, 98, 30, "TIER 2 - FastAPI application :8315 (backend/app/main.py, 24 routes under /api, JWT HS256 12 h)", fc=PALE_PURPLE, fs=8.5)
    groups = [
        (13.2, "AUTH (3) + HEALTH (1)", "POST /auth/register\nPOST /auth/login\nGET  /auth/me\nGET  /health"),
        (37.6, "KEYS (5)", "GET    /keys\nPOST   /keys/generate\nPOST   /keys/import\nGET    /keys/{id}/export\nDELETE /keys/{id}"),
        (62.4, "SAMPLES (4) + OPS (3)", "GET /samples/covers[/n]\nGET /samples/payloads[/n]\nPOST /send\nPOST /receive\nGET  /ops/{id}/{what}"),
        (86.8, "ANALYSIS (8)", "GET  /analysis/{op}\nGET  .../histogram.png\nGET  .../bitplanes.png\nPOST|GET /robustness/{op}\nGET /benchmark/capacity\nPOST /benchmark/run\nGET /log"),
    ]
    for cx, t, body in groups:
        box(ax, cx, 46.0, 23.6, 22, "", PURPLE, alpha=0.12, ec=PURPLE, lw=1.1)
        ax.text(cx, 55.0, t, ha="center", va="center", fontsize=6.6, fontweight="bold", color=NAVY, zorder=4)
        ax.text(cx - 11.0, 46.5, body, ha="left", va="center", fontsize=5.6, color=INK, zorder=4, family="DejaVu Sans Mono", linespacing=1.4)
    ax.text(50, 33.0, "auth.py: bcrypt (72-byte cap) + PyJWT  ·  Depends(current_user) on every route except register, login, health  ·  25 MB upload cap  ·  "
            "errors as HTTP 400/401/404/409/413", ha="center", fontsize=6.2, color=NAVY, zorder=4)
    panel(ax, 1, 10.5, 98, 19, "TIER 3 - service layer (backend/app/services, pure functions, one process)", fc=PALE_TEAL, fs=8.5)
    box(ax, 17, 19.8, 29, 11, "crypto.py\nAES-256-GCM · RSA-OAEP-SHA256\nkey pairs, fingerprints,\nbundle build / parse", TEAL, fs=6.9)
    box(ax, 50, 19.8, 30, 11, "lsb.py · pipeline.py\nembed / extract / capacity,\nhide() and reveal() with timings\nmetrics.py: PSNR, SSIM, MSE", TEAL, fs=6.9)
    box(ax, 83, 19.8, 29, 11, "robustness.py (9 attacks)\nbenchmark.py (capacity, speed)\nplots.py (histogram, bit planes)", TEAL, fs=6.9)
    arrow(ax, (31.6, 19.8), (34.8, 19.8), color=NAVY, lw=1.8)
    arrow(ax, (65.2, 19.8), (68.4, 19.8), color=NAVY, lw=1.8)
    panel(ax, 1, 0.5, 98, 8.5, "TIER 4 - persistence", fc=LIGHT, fs=8.5)
    box(ax, 25, 3.4, 45, 4.2, "SQLite  data/app.db  (SQLAlchemy 2.0)\nusers · keypairs · oplog", GREY, fs=6.8)
    box(ax, 73, 3.4, 46, 4.2, "Files: data/covers · data/payloads (samples) ·\ndata/outputs/<op>/ cover, stego, restored, plots", GREY, fs=6.6)
    for x in (25, 62, 87):
        arrow(ax, (x, 63.8), (x, 61.2), color=NAVY, lw=1.6)
    arrow(ax, (50, 31), (50, 28.6), color=NAVY, lw=1.6)
    arrow(ax, (25, 10.5), (25, 9.0), color=GREY, lw=1.5)
    arrow(ax, (73, 10.5), (73, 9.0), color=GREY, lw=1.5)
    ax.text(43.5, 61.9, "HTTP + JSON / multipart  (Vite proxy /api -> 8315)", fontsize=6.3, color=NAVY, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.4))
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------- 02 high-level workflow
def workflow():
    fig, ax = canvas(9.8, 7.2, 100, 73.5)
    ax.text(50, 71.6, "Sender lane, receiver lane, and the analysis tools that read the same operation records", ha="center", fontsize=7.6, color=NAVY, fontweight="bold")
    panel(ax, 1, 44, 98, 25.5, "LANE A - SENDER (Send page, POST /api/send)", fc=PALE_BLUE, fs=8.5)
    xa = [8.8, 25.3, 41.8, 58.3, 74.8, 91.3]
    A = [("1  Choose\nreceiver's\nRSA public key", BLUE), ("2  Choose file\nand cover PNG\n(sample or upload)", BLUE), ("3  AES-256-GCM\nencrypt file\n+ header", TEAL),
         ("4  RSA-OAEP wrap\nof the session\nkey", TEAL), ("5  Capacity check,\nLSB embed\n(1 bit / value)", PURPLE), ("6  PNG + PSNR,\nSSIM, hash,\nlog entry", NAVY)]
    for x, (t, c) in zip(xa, A):
        box(ax, x, 56, 13.6, 11.5, t, c, fs=6.5)
    for i in range(5):
        arrow(ax, (xa[i] + 6.9, 56), (xa[i + 1] - 6.9, 56), color=NAVY, lw=1.6)
    ax.text(50, 47.3, "A fresh 256-bit key and 96-bit nonce per message  ·  output is always PNG  ·  oversized payloads are refused before embedding (HTTP 400)",
            ha="center", fontsize=6.3, color=GREY, style="italic")
    # channel
    box(ax, 50, 40.2, 56, 4.4, "Stego PNG travels over any LOSSLESS channel (file, archive, USB, cloud drive)", ORANGE, fs=7.2, bold=True)
    ax.plot([91.3, 91.3], [49.8, 40.2], color=ORANGE, lw=1.6, zorder=1)
    ax.plot([91.3, 78.2], [40.2, 40.2], color=ORANGE, lw=1.6, zorder=1)
    ax.plot([22, 25.3], [40.2, 40.2], color=ORANGE, lw=1.6, zorder=1)
    arrow(ax, (25.3, 40.2), (25.3, 28.0), color=ORANGE, lw=1.6)
    panel(ax, 1, 13, 98, 23, "", fc=PALE_TEAL, fs=8.5)
    ax.text(98, 34.2, "LANE B - RECEIVER (Receive page, POST /api/receive)", ha="right", va="top", color=NAVY, fontsize=8.5, fontweight="bold", zorder=3)
    xb = [8.8, 25.3, 41.8, 58.3, 74.8, 91.3]
    Bx = [("1  Choose own\nRSA private key", TEAL), ("2  Stego PNG\n(upload or a\nsent operation)", TEAL), ("3  Read 32-bit length,\nthen the bundle\nbits from the LSBs", PURPLE),
          ("4  RSA unwrap of\nthe session key", BLUE), ("5  AES-GCM decrypt:\ntag must verify", BLUE), ("6  SHA-256 of file\nequals header\nhash", NAVY)]
    for x, (t, c) in zip(xb, Bx):
        box(ax, x, 22, 13.6, 11.5, t, c, fs=6.3)
    for i in range(5):
        arrow(ax, (xb[i] + 6.9, 22), (xb[i + 1] - 6.9, 22), color=NAVY, lw=1.6)
    ax.text(50, 14.5, "Any failure (no payload, wrong key, modified bit) stops the flow and releases nothing", ha="center", fontsize=6.3, color=GREY, style="italic")
    panel(ax, 1, 0.5, 98, 11, "ANALYSIS TOOLS - read the stored cover / stego pair of a send operation", fc=LIGHT, fs=8.2)
    for x, t in ((17, "Analysis\nPSNR, SSIM, MSE,\nhistograms, bit planes"), (50, "Robustness\n9 attacks, real decrypt\nattempt after each"), (83, "Benchmark + Log\ncapacity, speed per cover;\nevery operation recorded")):
        box(ax, x, 4.6, 29, 5.6, t, GREY, fs=6.4)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------- 03 DFD level 0
def _edge_pt(c, hw, hh, u):
    """Point where the ray from rectangle centre c in direction u leaves the rectangle."""
    t = min(hw / abs(u[0]) if u[0] else 1e9, hh / abs(u[1]) if u[1] else 1e9)
    return (c[0] + u[0] * t, c[1] + u[1] * t)


def dfd0():
    fig, ax = canvas(9.2, 6.2, 100, 67)
    cc, r = (50, 33.5), 12.5
    circle(ax, cc[0], cc[1], r, "CipherVeil\nplatform\n(API + services)", NAVY, fs=9)
    ents = {
        "snd": ((14, 56), "SENDER\n(user, send role)", "login, key choice, file,\ncover image", "stego PNG, PSNR / SSIM,\nSHA-256 of the file"),
        "rcv": ((86, 56), "RECEIVER\n(user, receive role)", "login, private key,\nstego PNG", "restored file, both\nSHA-256 values, verdict"),
        "lib": ((14, 11), "SAMPLE LIBRARY\n(covers, payloads)", "6 cover PNGs,\n4 sample files", None),
        "dev": ((86, 11), "EVALUATOR /\nDEVELOPER", "ml/eval.py, tests,\nrun_experiments.py", "metrics.json, test\nresults, screenshots"),
    }
    hw, hh = 10.4, 4.8
    for key, (c, name, to_lab, from_lab) in ents.items():
        box(ax, c[0], c[1], 2 * hw, 2 * hh, name, PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2, bold=True)
        v = (cc[0] - c[0], cc[1] - c[1])
        d = math.hypot(*v)
        u = (v[0] / d, v[1] / d)
        n = (-u[1], u[0])
        off = 2.4 if (from_lab and to_lab) else 0.0
        e1 = _edge_pt(c, hw, hh, u)
        if to_lab:
            p_out = (e1[0] + n[0] * off, e1[1] + n[1] * off)
            q_out = (cc[0] - u[0] * r + n[0] * off * 0.6, cc[1] - u[1] * r + n[1] * off * 0.6)
            arrow(ax, p_out, q_out, None, color=NAVY, lw=1.5)
            mx, my = (p_out[0] + q_out[0]) / 2 + n[0] * 6.2, (p_out[1] + q_out[1]) / 2 + n[1] * 6.2
            ax.text(mx, my, to_lab, ha="center", va="center", fontsize=6.3, color=INK, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
        if from_lab:
            p_in = (e1[0] - n[0] * off, e1[1] - n[1] * off)
            q_in = (cc[0] - u[0] * r - n[0] * off * 0.6, cc[1] - u[1] * r - n[1] * off * 0.6)
            arrow(ax, q_in, p_in, None, color=TEAL, lw=1.5)
            sgn = -1 if to_lab else 1
            mx, my = (p_in[0] + q_in[0]) / 2 + sgn * n[0] * 6.2, (p_in[1] + q_in[1]) / 2 + sgn * n[1] * 6.2
            ax.text(mx, my, from_lab, ha="center", va="center", fontsize=6.3, color=INK, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
    ax.text(50, 2.0, "Level 0: one process. Sender and receiver are two roles of the same signed-in user. The sample library is read-only data that ships with the product.",
            ha="center", fontsize=5.9, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


# --------------------------------------------------------------- 04 DFD level 1
def dfd1():
    fig, ax = canvas(10, 9.4, 100, 94)
    ys = {"1": 80, "2": 67, "3": 54, "4": 41, "5": 28, "6": 15}
    names = {"1": "1.0\nAuthenticate", "2": "2.0\nManage\nkeys", "3": "3.0\nEncrypt\nand hide", "4": "4.0\nExtract and\ndecrypt", "5": "5.0\nAnalyse\nquality", "6": "6.0\nAttack and\nbenchmark"}
    PX = 46
    box(ax, 9, 47.5, 15, 17, "USER\n(sender,\nreceiver or\nanalyst)", PALE_ORANGE, tc=INK, ec=ORANGE, fs=6.8, bold=True)
    for k, y in ys.items():
        circle(ax, PX, y, 5.7, names[k], NAVY if k in "34" else BLUE, fs=5.9)
    circle(ax, PX, 3.8, 3.5, "7.0\nLog", GREY, fs=5.6)
    stores = {"D1": (84, 80, "D1  users"), "D2": (84, 60, "D2  keypairs"), "D5": (84, 49, "D5  data/covers\n+ data/payloads"), "D4": (84, 27, "D4  data/outputs/<op>"), "D3": (84, 3.8, "D3  oplog")}
    for k, (x, y, t) in stores.items():
        store(ax, x, y, 21, 5.6, t, fs=6.0)

    def fl(p, q, t=None, color=NAVY, lo=(0, 1.3), fs=5.3, ls="-", style="-|>"):
        arrow(ax, p, q, t, color=color, lw=1.2, fs=fs, lo=lo, ls=ls, style=style)

    labels = {"1": "credentials / JWT", "2": "key actions / key list", "3": "file, cover, key id /\nstego PNG, quality", "4": "stego PNG, key id /\nfile, both hashes",
              "5": "op id / metrics, plots", "6": "run attacks / report"}
    for k, y in ys.items():
        fl((16.6, 47.5), (PX - 5.8, y), None, color=NAVY, style="<|-|>")
        t = 0.45
        lx = 16.6 + (PX - 5.8 - 16.6) * t
        ly = 47.5 + (y - 47.5) * t
        ax.text(lx, ly + 1.4, labels[k], ha="center", va="bottom", fontsize=5.1, color=INK, zorder=6, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9), linespacing=1.1)
    # processes <-> stores (right)
    fl((PX + 5.8, 80), (73.5, 80), "user row", style="<|-|>", lo=(0, 1.3))
    fl((PX + 5.8, 67), (73.5, 61.4), "PEMs, name,\nfingerprint", style="<|-|>", lo=(2.5, 2.5))
    fl((73.5, 59.0), (PX + 5.3, 55.8), "public key", color=TEAL, lo=(1.5, 2.0))
    fl((73.5, 58.3), (PX + 5.2, 43.5), "private key", color=TEAL, lo=(-6.0, 1.5))
    fl((73.5, 49.8), (PX + 5.8, 53.0), "sample file / cover", color=TEAL, lo=(1.5, -2.6))
    fl((PX + 5.4, 52.0), (73.5, 28.6), "cover.png, stego.png", lo=(-3.8, -5.0))
    fl((PX + 5.8, 40.0), (73.5, 26.6), "restored.bin", lo=(-1.0, -3.4))
    fl((73.5, 27.0), (PX + 5.4, 28.4), "cover + stego", color=TEAL, lo=(-1.0, 1.9))
    fl((PX + 5.0, 16.5), (73.5, 24.6), "stego,\nrobustness.json", style="<|-|>", lo=(0.8, -3.8))
    # log bus
    ax.plot([30.5, 30.5], [80, 3.8], color=GREY, lw=1.1, ls=(0, (3, 2)), zorder=1)
    ax.plot([30.5] * 6, list(ys.values()), "o", color=GREY, ms=2.5, zorder=2)
    fl((30.5, 3.8), (PX - 3.6, 3.8), "event record", color=GREY, ls=(0, (3, 2)), lo=(-0.5, 1.2))
    fl((PX + 3.6, 3.8), (73.5, 3.8), "log row", color=GREY, lo=(0, 1.3))
    ax.text(30, 89.8, "Every process 1.0-6.0 hands an event record to 7.0 (dashed bus); 7.0 appends it to D3. No key or file content is logged.", fontsize=5.6, color=GREY, style="italic", ha="left")
    ax.text(74, 10.0, "6.0 also reads the private\nkey of the operation from D2", fontsize=5.3, color=GREY, style="italic", ha="left")
    ax.text(50, 0.6, "Level 1: seven processes, five data stores. Process 3.0 is expanded in level 2.", ha="center", fontsize=6, color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


# --------------------------------------------------------------- 06 UML class
def uml():
    fig, ax = canvas(10.2, 8.4, 100, 82.5)
    X1, W1 = 5, 22
    u = uml_class(ax, X1, 80, W1, "User", ["id: int  PK", "username: str(40) UQ", "pw_hash: str(100)", "created_at: datetime"], [], hdr=BLUE, stereotype="table")
    k = uml_class(ax, X1, u[1] - 4.2, W1, "KeyPair", ["id: int  PK", "user_id: int  FK", "name: str(60)", "bits: int", "fingerprint: str(40)", "public_pem: text", "private_pem: text|None", "created_at: datetime"],
                  [], hdr=BLUE, stereotype="table")
    o = uml_class(ax, X1, k[1] - 4.2, W1, "OpLog", ["id: int  PK", "user_id: int  FK", "op: str(30)", "ok: bool", "details: text (JSON)", "created_at: datetime"], ["data() -> dict"], hdr=BLUE, stereotype="table")
    X2, W2 = 31, 33
    cr = uml_class(ax, X2, 80, W2, "crypto", ["MAGIC = b'CVL1'", "ALLOWED_BITS = (2048, 3072, 4096)", "CryptoError(ValueError)"],
                   ["generate_keypair(bits)", "fingerprint(public_pem)", "encrypt_bundle(pub, name, data)", "decrypt_bundle(priv, bundle)", "load_public / load_private"], hdr=TEAL, stereotype="module")
    ls = uml_class(ax, X2, cr[1] - 4.2, W2, "lsb", ["LEN_BITS = 32", "StegoError(ValueError)"], ["load_rgb(source)", "capacity_bytes(arr)", "embed(arr, bundle)", "extract(arr)", "to_png_bytes(arr)"], hdr=TEAL, stereotype="module")
    mt = uml_class(ax, X2, ls[1] - 4.2, W2, "metrics", [], ["imperceptibility(cover, stego)", "  -> psnr_db, ssim, mse, max_abs_change"], hdr=TEAL, stereotype="module")
    X3, W3 = 72, 26
    pl = uml_class(ax, X3, 80, W3, "pipeline", [], ["hide(pub, name, data, cover)", "reveal(priv, stego)"], hdr=NAVY, stereotype="module")
    rb = uml_class(ax, X3, pl[1] - 4.2, W3, "robustness", ["ATTACKS: 9 (key, label, fn)"], ["run_attacks(stego, priv,", "    sha256, bundle_len)"], hdr=NAVY, stereotype="module")
    bm = uml_class(ax, X3, rb[1] - 4.2, W3, "benchmark", [], ["capacity_table(covers)", "run(covers, sizes, key_bits)"], hdr=NAVY, stereotype="module")
    rt = uml_class(ax, X3, bm[1] - 4.2, W3, "routes (5 APIRouters)", ["auth, keys, samples,", "ops, analysis"], ["current_user(): JWT guard", "log_op(db, uid, op, ok, d)"], hdr=PURPLE, stereotype="FastAPI")
    # associations among tables
    ax.plot([X1 + 8, X1 + 8], [u[1], k[1] + k[3]], color=NAVY, lw=1.3)
    ax.text(X1 + 9.0, u[1] - 1.8, "1", fontsize=6.5, color=NAVY, fontweight="bold")
    ax.text(X1 + 9.0, k[1] + k[3] + 1.2, "0..*", fontsize=6.5, color=NAVY, fontweight="bold")
    ax.text(X1 + 13.0, (u[1] + k[1] + k[3]) / 2 - 0.5, "owns", fontsize=5.8, color=GREY, style="italic")
    yo = o[1] + o[3] - 7
    ax.plot([X1, 2.4, 2.4, X1], [u[1] + 2.0, u[1] + 2.0, yo, yo], color=NAVY, lw=1.3)
    ax.text(0.9, (u[1] + 2.0 + yo) / 2, "1  to  0..*   (performs)", fontsize=5.8, color=NAVY, rotation=90, va="center", fontweight="bold")
    # pipeline uses crypto, lsb, metrics (solid), robustness uses crypto + lsb (dashed), benchmark uses pipeline
    ty = lambda c, d: c[1] + c[3] - d
    arrow(ax, (X3, pl[1] + pl[3] - 5), (X2 + W2, ty(cr, 7)), None, color=PURPLE, lw=1.3)
    arrow(ax, (X3, pl[1] + pl[3] - 6.5), (X2 + W2, ty(ls, 6.5)), None, color=PURPLE, lw=1.3)
    arrow(ax, (X3, pl[1] + pl[3] - 8.5), (X2 + W2, ty(mt, 5.5)), None, color=PURPLE, lw=1.3)
    arrow(ax, (X3, rb[1] + rb[3] - 7), (X2 + W2, ty(cr, 13)), None, color=PURPLE, lw=1.2, ls=(0, (4, 2)))
    arrow(ax, (X3, rb[1] + rb[3] - 9), (X2 + W2, ty(ls, 11)), None, color=PURPLE, lw=1.2, ls=(0, (4, 2)))
    xb = X3 + W3 + 1.0
    ax.plot([X3 + W3, xb, xb], [bm[1] + bm[3] - 6, bm[1] + bm[3] - 6, pl[1] + pl[3] - 7.5], color=PURPLE, lw=1.2, ls=(0, (4, 2)))
    arrow(ax, (xb, pl[1] + pl[3] - 7.5), (X3 + W3, pl[1] + pl[3] - 7.5), None, color=PURPLE, lw=1.2, ls=(0, (4, 2)))
    # routes -> services, ORM (one bottom bus)
    yb = min(rt[1], o[1]) - 3.2
    ax.plot([X3 + W3 / 2, X3 + W3 / 2], [rt[1], yb], color=NAVY, lw=1.3)
    ax.plot([X3 + W3 / 2, X1 + W1 / 2], [yb, yb], color=NAVY, lw=1.3)
    arrow(ax, (X1 + W1 / 2, yb), (X1 + W1 / 2, o[1]), None, color=NAVY, lw=1.3)
    ax.text(50, yb + 1.4, "routes persist through the ORM session (get_db) and call pipeline, robustness, benchmark and crypto", fontsize=5.9, color=NAVY, ha="center",
            bbox=dict(fc="white", ec="none", pad=0.3))
    ax.text(50, 0.4, "Both error classes are mapped to HTTP 400 by the routes. Solid purple: uses. Dashed: also uses. Modules are drawn as classes with static functions; tables are SQLAlchemy models.", ha="center", fontsize=5.7, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")



def main():
    architecture()
    workflow()
    dfd0()
    dfd1()
    uml()
    try:
        from . import diagrams_more
    except ImportError:
        return
    diagrams_more.main()


if __name__ == "__main__":
    main()
