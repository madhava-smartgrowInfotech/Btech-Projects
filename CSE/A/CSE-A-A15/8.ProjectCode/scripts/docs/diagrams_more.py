"""CipherVeil design diagrams 05 and 07-11 (matplotlib, 150 dpi) -> docs/diagrams/.  Called by make_diagrams.main().

05 DFD level 2 (process 3.0)  07 sequence (send then receive)  08 use case  09 ER  10 flowchart of embed and extract  11 bundle and LSB layout.
"""
from __future__ import annotations

from pathlib import Path

from matplotlib.patches import Ellipse, Rectangle

from . import facts as F
from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 05 DFD level 2
def dfd2():
    fig, ax = canvas(10, 6.8, 100, 68)
    ax.text(50, 65.8, "Level 2: process 3.0 Encrypt and hide (routes/ops.py send, services/pipeline.hide)", ha="center", fontsize=7.4, color=NAVY, fontweight="bold")
    box(ax, 7.5, 54.5, 13, 7.0, "USER\n(sender role)", PALE_ORANGE, tc=INK, ec=ORANGE, fs=6.8, bold=True)
    P = [("3.1", "Validate\ninputs", 24, 54.5), ("3.2", "Header +\nAES-256-GCM\nencrypt", 43, 54.5), ("3.3", "RSA-OAEP\nwrap session\nkey", 62, 54.5), ("3.4", "Assemble\nbundle\nCVL1", 81, 54.5),
         ("3.5", "Capacity\ncheck,\nLSB embed", 81, 29), ("3.6", "PNG encode,\nPSNR, SSIM,\nMSE", 62, 29), ("3.7", "Persist\nand log", 43, 29)]
    for no, t, x, y in P:
        circle(ax, x, y, 6.8, f"{no}\n{t}", NAVY if no in ("3.2", "3.3", "3.5") else BLUE, fs=6.0)
    store(ax, 30, 41, 20, 5, "D2  keypairs\n(public_pem)", fs=6.2)
    store(ax, 8, 40, 15, 5.2, "D5  covers\n+ payloads", fs=6.2)
    store(ax, 24, 14, 22, 5.2, "D4  data/outputs/<op>\ncover.png, stego.png", fs=6.0)
    store(ax, 62, 14, 20, 5, "D3  oplog\n(details JSON)", fs=6.2)

    def fl(p, q, t=None, color=NAVY, lo=(0, 1.4), fs=5.6, ls="-"):
        arrow(ax, p, q, t, color=color, lw=1.3, fs=fs, lo=lo, ls=ls)

    fl((14.0, 54.5), (17.2, 54.5), None)
    ax.text(15.6, 59.7, "key_id, file,\ncover", fontsize=5.5, ha="center", color=INK)
    fl((29, 43.5), (26.5, 48.0), "public PEM", color=TEAL, lo=(6.0, -0.3), fs=5.5)
    fl((30.8, 54.5), (36.2, 54.5), "bytes, name", lo=(0, 1.9), fs=5.4)
    fl((49.8, 54.5), (55.2, 54.5), "AES key,\nnonce, ct+tag", lo=(0, 2.7), fs=5.4)
    fl((68.8, 54.5), (74.2, 54.5), "wrapped\nkey", lo=(0, 2.4), fs=5.4)
    fl((81, 47.7), (81, 35.8), "bundle bytes", lo=(5.4, 0), fs=5.5)
    fl((8, 42.8), (19.8, 49.8), "cover sample", color=TEAL, lo=(-4.0, 2.4), fs=5.4)
    fl((28.5, 50.0), (75.0, 32.0), "cover RGB array", color=TEAL, lo=(-3.0, 4.0), fs=5.4, ls=(0, (3, 2)))
    fl((74.2, 29), (68.8, 29), "stego\narray", lo=(0, 2.4), fs=5.4)
    fl((55.2, 29), (49.8, 29), "PNG, quality\n+ timings", lo=(0, 2.5), fs=5.4)
    fl((38.5, 25), (26.5, 16.8), "cover.png,\nstego.png", color=TEAL, lo=(-4.4, 1.0), fs=5.4)
    fl((47, 24.2), (58.0, 16.6), "event record", color=GREY, lo=(5.2, 0.5), fs=5.4, ls=(0, (3, 2)))
    box(ax, 87, 8, 24, 11, "Errors stop the flow:\n3.1 empty file, bad PEM, no cover\n3.5 bundle larger than capacity\n-> HTTP 400 + failed oplog row", PALE_ORANGE, tc=INK, ec=ORANGE, fs=5.9)
    ax.text(50, 1.2, "Process 3.2 uses a fresh 256-bit key and 96-bit nonce per call; AAD is the magic CVL1. Process 3.5 writes length(32 bits) + bundle into the LSB of each R, G, B value.",
            ha="center", fontsize=5.6, color=GREY, style="italic")
    save(fig, OUT / "05_dfd_level2.png")


# ------------------------------------------------------------------ 07 sequence
def sequence():
    fig, ax = canvas(10, 10.6, 100, 106)
    names = ["User", "React\nconsole", "FastAPI\nroutes/ops.py", "pipeline.py", "crypto.py", "lsb.py +\nmetrics.py", "SQLite +\ndata/outputs"]
    xs = [8, 22, 37, 52, 66, 80, 92.5]
    cols = [ORANGE, BLUE, NAVY, TEAL, TEAL, TEAL, GREY]
    for x, n, c in zip(xs, names, cols):
        box(ax, x, 102, 12.0, 5.4, n, c, fs=6.0, bold=True)
        ax.plot([x, x], [99.2, 2], color="#9AA7B8", lw=1.0, ls=(0, (4, 3)), zorder=1)

    def msg(i, j, y, text, dashed=False, color=NAVY, fs=5.5):
        x1, x2 = xs[i], xs[j]
        ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2, ls="--" if dashed else "-"))
        ax.text((x1 + x2) / 2, y + 1.15, text, ha="center", fontsize=fs, color=INK, bbox=dict(fc="white", ec="none", pad=0.3))

    def selfmsg(i, y, text):
        x = xs[i]
        ax.plot([x, x + 4.5, x + 4.5], [y, y, y - 2.4], color=NAVY, lw=1.2)
        ax.annotate("", xy=(x, y - 2.4), xytext=(x + 4.5, y - 2.4), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.2))
        ax.text(x + 5.5, y - 1.2, text, fontsize=5.4, ha="left", va="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.2))

    def act(i, y1, y2):
        ax.add_patch(Rectangle((xs[i] - 0.8, y2), 1.6, y1 - y2, fc=PALE_BLUE, ec=NAVY, lw=0.8, zorder=2))

    ax.text(1, 95.6, "A. Send: encrypt a file and hide it in a cover", fontsize=6.8, fontweight="bold", color=NAVY)
    msg(0, 1, 93.0, "pick key, file, cover; press 'Encrypt and hide'")
    msg(1, 2, 89.6, "POST /api/send  (multipart) + Bearer JWT")
    act(2, 89.6, 42.5)
    selfmsg(2, 87.4, "current_user(), get_key(): key belongs to user")
    msg(2, 6, 82.0, "SELECT keypairs (public_pem)", fs=5.4)
    msg(2, 3, 79.0, "hide(public_pem, name, data, cover)")
    act(3, 79.0, 50.5)
    msg(3, 4, 75.6, "encrypt_bundle(public_pem, name, data)")
    act(4, 75.6, 67.0)
    selfmsg(4, 73.5, "AES-256-GCM(key, nonce, AAD=CVL1); RSA-OAEP wrap")
    msg(4, 3, 66.6, "bundle (CVL1 | wrapped key | nonce | ct+tag)", dashed=True)
    msg(3, 5, 63.6, "embed(cover, bundle): capacity check, write LSBs")
    act(5, 63.6, 46)
    msg(5, 3, 60.6, "stego array (or StegoError -> HTTP 400)", dashed=True)
    msg(3, 5, 57.6, "to_png_bytes(); imperceptibility(cover, stego)")
    msg(5, 3, 54.6, "PNG bytes, PSNR / SSIM / MSE", dashed=True)
    msg(3, 2, 51.4, "result: capacity, timings_ms, quality", dashed=True)
    msg(2, 6, 48.0, "log_op(send) + write cover.png, stego.png")
    msg(2, 1, 44.4, "200 JSON {op_id, quality, hashes}", dashed=True)
    msg(1, 0, 41.2, "stego image, PSNR, SSIM, SHA-256 shown", dashed=True)
    ax.plot([1, 99], [37.0, 37.0], color="#C9D2DE", lw=1.0)
    ax.text(1, 34.2, "B. Receive: extract the bundle and restore the file", fontsize=6.8, fontweight="bold", color=NAVY)
    msg(0, 1, 31.6, "pick private key and stego PNG; press 'Extract and decrypt'")
    msg(1, 2, 28.2, "POST /api/receive  (stego upload or op id)")
    act(2, 28.2, 6)
    msg(2, 3, 25.0, "reveal(private_pem, stego array)")
    act(3, 25.0, 9)
    msg(3, 5, 21.8, "extract(arr): 32-bit length, then bundle bits")
    msg(5, 3, 18.8, "bundle bytes (or 'no hidden payload')", dashed=True)
    msg(3, 4, 15.8, "decrypt_bundle(private_pem, bundle)")
    act(4, 15.8, 9.0)
    selfmsg(4, 13.8, "magic, key size, RSA unwrap, GCM tag, SHA-256")
    msg(4, 3, 8.6, "filename, data, hash_match (or CryptoError -> 400)", dashed=True)
    msg(2, 6, 5.0, "log_op(receive); write restored.bin", fs=5.4)
    msg(2, 1, 2.0, "200 JSON, then GET /ops/{id}/restored downloads the file", dashed=True, fs=5.4)
    save(fig, OUT / "07_sequence_flow.png")


# --------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.add_patch(Rectangle((24, 1.5), 56, 73, fc="#FAFBFD", ec=NAVY, lw=1.5, zorder=0))
    ax.text(52, 71.8, "CipherVeil (system boundary)", ha="center", fontsize=8, fontweight="bold", color=NAVY)

    def actor(x, y, name):
        ax.add_patch(Ellipse((x, y + 5.2), 3.6, 3.6, fc=WHITE, ec=NAVY, lw=1.4, zorder=3))
        ax.plot([x, x], [y + 3.4, y - 1.8], color=NAVY, lw=1.4, zorder=3)
        ax.plot([x - 3, x + 3], [y + 1.8, y + 1.8], color=NAVY, lw=1.4, zorder=3)
        ax.plot([x, x - 2.6], [y - 1.8, y - 6.0], color=NAVY, lw=1.4, zorder=3)
        ax.plot([x, x + 2.6], [y - 1.8, y - 6.0], color=NAVY, lw=1.4, zorder=3)
        ax.text(x, y - 8.6, name, ha="center", va="center", fontsize=7.2, fontweight="bold", color=NAVY)
        return (x, y + 1.8)

    snd = actor(9, 50, "Sender")
    rcv = actor(9, 20, "Receiver")
    ev = actor(91, 28, "Evaluator /\nDeveloper")
    L = [("signin", "Register / sign in", 66.5), ("gen", "Generate RSA keypair\n(2048 / 3072 / 4096)", 59.0), ("imp", "Import or export a key\n(PEM, public or private)", 51.5),
         ("send", "Encrypt and hide a file\nin a cover PNG", 44.0), ("recv", "Extract and decrypt,\nverify hashes", 36.5), ("ana", "View PSNR, SSIM,\nhistograms, bit planes", 29.0),
         ("rob", "Run 9 robustness attacks", 21.5), ("bench", "Capacity and speed\nbenchmark", 14.5), ("log", "Browse operation log", 7.0)]
    R = [("cap", "Check cover capacity", 44.0), ("tag", "Verify AES-GCM tag\nand SHA-256", 36.5), ("eval", "Run evaluation and tests\n(ml/eval.py, pytest)", 14.5)]
    U = {}
    for k, t, y in L:
        ellipse(ax, 38, y, 22, 7.0 if "\n" in t else 5.2, t, fs=6.4)
        U[k] = (38, y)
    for k, t, y in R:
        ellipse(ax, 66, y, 22, 7.0 if "\n" in t else 5.2, t, fs=6.4)
        U[k] = (66, y)

    def link(a, key, side="l"):
        x2, y2 = U[key]
        x2 += -11.0 if side == "l" else 11.0
        ax.plot([a[0] + (3 if side == "l" else -3), x2], [a[1], y2], color=GREY, lw=1.0, zorder=1)

    for k in ("signin", "gen", "imp", "send", "ana", "rob", "bench", "log"):
        link(snd, k)
    for k in ("signin", "gen", "imp", "recv", "ana", "log"):
        link(rcv, k)
    link(ev, "eval", "r")
    for a, b, lab in (("send", "cap", "<<include>>"), ("recv", "tag", "<<include>>")):
        (x1, y1), (x2, y2) = U[a], U[b]
        arrow(ax, (x1 + 11.0, y1), (x2 - 11.0, y2), None, color=ORANGE, lw=1.2, ls=(0, (4, 2)))
        ax.text((x1 + x2) / 2, y1 + 1.5, lab, ha="center", fontsize=5.8, color=ORANGE, style="italic")
    ax.text(52, 0.1, "Sender and receiver are roles of one signed-in user (any user can use every page); the evaluator also runs the command-line scripts.",
            ha="center", fontsize=5.7, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")



# --------------------------------------------------------------- 09 ER
def er():
    fig, ax = canvas(10, 6.4, 100, 64)

    def entity(x, y, w, name, attrs, color, ls="-"):
        lh = 2.6
        h = 4.2 + lh * len(attrs) + 0.8
        ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY if ls == "-" else GREY, lw=1.3, ls=ls, zorder=2))
        ax.add_patch(Rectangle((x, y - 4.2), w, 4.2, fc=color, ec=NAVY if ls == "-" else GREY, lw=1.3, zorder=3))
        ax.text(x + w / 2, y - 2.1, name, ha="center", va="center", color=WHITE, fontsize=7.6, fontweight="bold", zorder=4)
        for i, a in enumerate(attrs):
            ax.text(x + 0.9, y - 4.2 - 1.6 - i * lh, a, ha="left", va="center", fontsize=6.0, color=INK, zorder=4, family="DejaVu Sans Mono")
        return y - h

    ub = entity(3, 60, 26, "users", ["PK id            int", "UQ username      str(40)", "   pw_hash       str(100) bcrypt", "   created_at    datetime"], BLUE)
    kb = entity(37, 60, 30, "keypairs", ["PK id            int", "FK user_id       int -> users.id", "   name          str(60)", "   bits          2048|3072|4096", "   fingerprint   str(40)",
                                         "   public_pem    text", "   private_pem   text, NULL = public-only", "   created_at    datetime"], TEAL)
    ob = entity(37, 28.5, 30, "oplog", ["PK id            int", "FK user_id       int -> users.id", "   op            str(30)", "   ok            bool", "   details       text (JSON, no secrets)", "   created_at    datetime"], PURPLE)
    fb = entity(73, 44, 25, "files data/outputs/<op_id>/", ["cover.png         (send)", "stego.png         (send)", "restored.bin      (receive)", "histogram.png     (cached)", "bitplanes.png     (cached)", "robustness.json   (attacks)"], GREY, ls="--")
    # users 1 - 0..N keypairs
    ax.plot([29, 37], [52.5, 52.5], color=NAVY, lw=1.5, zorder=1)
    ax.text(30.4, 54.2, "1", fontsize=7, color=NAVY, fontweight="bold", ha="center")
    ax.text(35.4, 54.2, "0..N", fontsize=7, color=NAVY, fontweight="bold", ha="center")
    ax.text(33, 50.4, "owns", fontsize=6.2, ha="center", color=GREY, style="italic")
    # users 1 - 0..N oplog
    ax.plot([26, 26, 37], [ub, 13.5, 13.5], color=NAVY, lw=1.5, zorder=1)
    ax.text(27.3, ub - 2.2, "1", fontsize=7, color=NAVY, fontweight="bold")
    ax.text(32.5, 15.0, "0..N", fontsize=7, color=NAVY, fontweight="bold", ha="center")
    ax.text(26.8, 26, "performs", fontsize=6.2, color=GREY, style="italic", rotation=90, va="center")
    # oplog 1 - 0..1 files
    ax.plot([67, 85.5, 85.5], [17, 17, fb], color=GREY, lw=1.5, ls=(0, (4, 2)), zorder=1)
    ax.text(76.5, 18.6, "1 : 0..1   (folder named by op_id)", fontsize=6.2, ha="center", color=GREY, fontweight="bold")
    ax.plot([52, 52], [28.5, 34.2], color=ORANGE, lw=1.4, ls=(0, (4, 2)), zorder=1)
    ax.text(53.0, 31.4, "logical link: details.key_id", fontsize=5.8, color=ORANGE, fontweight="bold")
    box(ax, 13.5, 30.5, 22, 10.5, "Logical link (orange, no foreign key):\noplog.details.key_id holds the\nkeypairs.id used by a send or\nreceive, plus its fingerprint", PALE_ORANGE, tc=INK, ec=ORANGE, fs=5.7)
    box(ax, 13.5, 12.0, 22, 12.5, "Created by SQLAlchemy create_all()\nin SQLite (data/app.db). Passwords\nare bcrypt hashes; private_pem is\nstored unencrypted (local-machine\nthreat model). Samples are plain files.", LIGHT, tc=INK, ec="#B7C3D3", fs=5.7)
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------- 10 flowchart
def algo():
    fig, ax = canvas(10, 11.8, 100, 118)
    ax.text(25, 115.6, "EMBED  (send)", ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.text(75, 115.6, "EXTRACT  (receive)", ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.plot([50, 50], [2, 114], color="#C9D2DE", lw=1.0, ls=(0, (3, 3)))

    def term(x, y, t, c=GREY):
        box(ax, x, y, 18, 4.2, t, c, fs=6.6, r=2.0, bold=True)

    def step(x, y, t, c=BLUE, h=7.4, w=32):
        box(ax, x, y, w, h, t, c, fs=6.1)

    def dec(x, y, t, w=32, h=9.0):
        diamond(ax, x, y, w, h, t, fs=5.7)

    def err(x, y, t, w=13.5):
        box(ax, x, y, w, 8.0, t, PALE_ORANGE, tc=INK, ec=ORANGE, fs=5.0)

    def down(x, y1, y2, label=None, color=NAVY):
        arrow(ax, (x, y1), (x, y2), label, color=color, lw=1.4, lo=(2.4, 0), fs=5.8)

    # ---- embed (centre x=18)
    xe = 18
    term(xe, 111.6, "Start")
    step(xe, 101.6, "Read file; load cover as RGB\narray (alpha dropped); take\nthe key's public PEM")
    step(xe, 90.6, "header = {name, size, sha256}\nplaintext =\nlen(header) | header | file", TEAL)
    step(xe, 79.6, "AES-256-GCM encrypt (fresh key,\n96-bit nonce, AAD = CVL1);\nwrap key with RSA-OAEP", TEAL)
    step(xe, 68.6, "bundle = CVL1 | wrapped_len |\nwrapped_key | nonce |\nciphertext + tag", TEAL)
    dec(xe, 56.4, "len(bundle) <=\n(H x W x 3 - 32) / 8 ?")
    err(41.8, 56.4, "Reject:\n'cover holds\nonly N bytes'\n(HTTP 400)")
    arrow(ax, (xe + 16, 56.4), (41.8 - 6.75, 56.4), "no", color=ORANGE, lw=1.3, lo=(0, 1.6), fs=5.8)
    step(xe, 43.6, "frame = 32-bit length | bundle\nbits = unpackbits(frame)", PURPLE)
    step(xe, 33.0, "flat RGB values [0 : n] =\n(value AND 0xFE) OR bit\n(row-major)", PURPLE)
    step(xe, 22.4, "Encode PNG (lossless);\nPSNR, SSIM, MSE vs the\noriginal cover", NAVY)
    step(xe, 11.8, "Save cover.png, stego.png;\nwrite oplog row; return JSON", NAVY, h=6.6)
    term(xe, 3.6, "End: stego PNG")
    for a, b in ((109.5, 105.3), (97.9, 94.3), (86.9, 83.3), (75.9, 72.3), (64.9, 60.9)):
        down(xe, a, b)
    down(xe, 51.9, 47.3, "yes")
    for a, b in ((39.9, 36.7), (29.3, 26.1), (18.7, 15.1), (8.5, 5.7)):
        down(xe, a, b)
    # ---- extract (centre x=70)
    xr = 70
    term(xr, 111.6, "Start")
    step(xr, 101.6, "Load stego as RGB array;\nown RSA private key", BLUE, h=6.6)
    step(xr, 91.6, "L = first 32 LSBs as an integer\n(the bundle length)", PURPLE, h=6.6)
    dec(xr, 80.5, "0 < L <=\ncapacity ?")
    err(92.5, 80.5, "Error:\n'no hidden\npayload found'\n(HTTP 400)")
    step(xr, 68.0, "bundle = packbits of the next\nL x 8 LSBs", PURPLE, h=6.6)
    dec(xr, 56.4, "magic == CVL1 and\nwrapped_len == key bytes ?")
    err(92.5, 56.4, "Error:\n'no bundle' /\n'wrong key\nsize'")
    step(xr, 43.4, "RSA-OAEP unwrap of the session\nkey; AES-GCM decrypt (tag\nmust verify)", TEAL)
    dec(xr, 31.6, "Unwrap and\ntag OK ?")
    err(92.5, 31.6, "Error:\n'not the key' /\n'data was\nmodified'")
    step(xr, 19.4, "Parse header; compare SHA-256\nof the file with the header\nhash (hash_match)", NAVY)
    step(xr, 9.4, "Save restored.bin; show both\nhashes; write oplog row", NAVY, h=6.6)
    term(xr, 2.6, "End: restored file")
    for y, e in ((80.5, 92.5), (56.4, 92.5), (31.6, 92.5)):
        arrow(ax, (xr + 16, y), (e - 6.75, y), "no", color=ORANGE, lw=1.3, lo=(0, 1.6), fs=5.8)
    for a, b in ((109.5, 104.9), (98.3, 94.9), (88.3, 85.0)):
        down(xr, a, b)
    down(xr, 76.0, 71.7, "yes")
    down(xr, 64.7, 61.0)
    down(xr, 51.9, 47.1, "yes")
    down(xr, 39.7, 36.1)
    down(xr, 27.1, 23.1, "yes")
    down(xr, 15.7, 12.7)
    down(xr, 6.1, 4.7)
    save(fig, OUT / "10_flowchart_algorithm.png")


# --------------------------------------------------------------- 11 bundle layout
def bundle():
    rs = {r["rsa_bits"]: r for r in F.EX["rsa_study"]}
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.text(50, 71.6, "What is hidden: the CVL1 bundle and how its bits are written into the image", ha="center", fontsize=8.2, fontweight="bold", color=NAVY)
    ax.text(1.5, 66.4, "1. Bundle (bytes); the RSA key is k bytes long (256 / 384 / 512)", fontsize=7.2, fontweight="bold", color=NAVY)
    segs = [("MAGIC\n'CVL1'\n4 B", 4.5, ORANGE), ("wrapped\nlen\n2 B", 4.5, PURPLE), ("wrapped AES key  (RSA-OAEP-SHA256)\nk bytes = RSA bits / 8", 27, BLUE), ("nonce\n12 B", 8, TEAL),
            ("ciphertext = AES-256-GCM( header_len | header | file )\n+ 16-byte tag", 47, NAVY)]
    x = 1.5
    for t, w, c in segs:
        box(ax, x + w / 2, 58.4, w - 0.5, 8.4, t, c, fs=6.0, r=0.6)
        x += w
    ax.text(1.5, 51.4, "Overhead for a short file name (measured):  " + "   ".join(f"RSA-{b}: {rs[b]['overhead_bytes']} B" for b in sorted(rs)) +
            "     (= wrapped key + 4 + 2 + 12 + 2 + header JSON + 16)", fontsize=6.3, color=INK)
    ax.text(1.5, 47.6, "AES-GCM additional data = 'CVL1'; the header JSON {name, size, sha256} sits INSIDE the encrypted part.", fontsize=6.2, color=GREY, style="italic")
    ax.text(1.5, 42.6, "2. Embedding: one bit per colour value, row by row from the top-left pixel; the 32-bit length comes first", fontsize=7.2, fontweight="bold", color=NAVY)
    box(ax, 13.5, 36.4, 25, 5.0, "length = len(bundle), 32 bits\n(big-endian)", ORANGE, fs=6.0, r=0.6)
    box(ax, 50, 36.4, 40, 5.0, "bundle bits, most significant bit first\nframe = length | bundle -> np.unpackbits", NAVY, fs=6.0, r=0.6)
    cols = ["#D9534F", "#3A9B5C", "#3B72C4"]
    fills = ["#F6DAD8", "#DDF0E3", "#DCE7F7"]
    labels = "RGB"

    def row(y, first_pixel, n_pix, caption):
        for p in range(n_pix):
            px0 = 3.5 + p * 23.4
            for c in range(3):
                v = (first_pixel + p) * 3 + c
                xx = px0 + c * 7.4
                ax.add_patch(Rectangle((xx, y), 7.0, 7.2, fc=fills[c], ec=cols[c], lw=1.1, zorder=2))
                ax.text(xx + 2.7, y + 4.8, labels[c], ha="center", fontsize=6.2, color=cols[c], fontweight="bold", zorder=3)
                ax.text(xx + 2.7, y + 2.0, "7 bits kept", ha="center", fontsize=3.9, color=GREY, zorder=3)
                ax.add_patch(Rectangle((xx + 5.2, y), 1.8, 7.2, fc=ORANGE if v < 32 else NAVY, ec="none", zorder=3))
                ax.text(xx + 3.5, y - 1.5, f"v{v}", ha="center", fontsize=5.0, color=INK)
            ax.text(px0 + 10.8, y - 3.4, f"pixel {first_pixel + p}", ha="center", fontsize=6.0, color=INK)
        ax.text(98, y + 3.6, "...", fontsize=12, color=GREY, ha="right")
        ax.text(1.5, y + 9.6, caption, fontsize=6.2, color=INK)

    row(21.5, 0, 4, "Values v0-v11 (pixels 0-3): the first 12 of the 32 length bits (orange stripe = the last bit of the value, the only one that changes)")
    row(6.2, 10, 4, "Values v30-v41 (pixels 10-13): v30 and v31 finish the length, v32 onward carry the bundle bits (navy)")
    ax.text(50, 0.3, "A value is replaced by (value AND 0xFE) OR bit: it changes by at most 1, and in about half of the cases. Capacity = (width x height x 3 - 32) / 8 bytes = 3.0 bits per pixel.",
            fontsize=5.7, color=GREY, ha="center", style="italic")
    save(fig, OUT / "11_bundle_layout.png")


def main():
    dfd2()
    sequence()
    use_case()
    er()
    algo()
    bundle()


if __name__ == "__main__":
    main()
