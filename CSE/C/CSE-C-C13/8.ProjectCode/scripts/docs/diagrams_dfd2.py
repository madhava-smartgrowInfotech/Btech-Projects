"""DFD level 2 (diagram 05): process 3.0 Encrypt and store file expanded into eight sub-processes.

3.1-3.4 run in the browser (frontend/src/lib/vault.js uploadFile, vaultCrypto.js); 3.5-3.8 run in the FastAPI upload
handler (backend/app/api/files.py) and audit_service.record_event.
"""

from .dgm_lib import BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_TEAL, TEAL, W, arrow, box, canvas, ellipse, out, panel, save_min as save, store, txt


def d_dfd2():
    fig, ax = canvas(W, 6.8, 100)          # height 61.8
    H_ = 100 * 6.8 / W
    panel(ax, 1, 32, 98, 29, "Browser (Web Crypto API, plaintext exists only here)", fc=LIGHT)
    panel(ax, 1, 8.5, 98, 21.5, "Server (FastAPI upload handler, ciphertext only)", fc=LIGHT)
    pw, ph = 19, 11
    top = [(13, "3.1\nHash plaintext\nSHA-256"), (38, "3.2\nEncrypt with\nrandom FEK + IV"), (63, "3.3\nWrap FEK with\nowner public key"), (88, "3.4\nBuild multipart\nrequest + JWT")]
    for x, t in top:
        ellipse(ax, x, 42, pw, ph, t, fc=PALE_BLUE, ec=BLUE, fs=8.4)
    bot = [(88, "3.5\nValidate\nrequest"), (63, "3.6\nWrite ciphertext\nobject"), (38, "3.7\nInsert files\nrow"), (13, "3.8\nRecord audit\nevent")]
    for x, t in bot:
        ellipse(ax, x, 19, pw, ph, t, fc=PALE_BLUE, ec=BLUE, fs=8.4)
    # inputs
    box(ax, 13, 55, 22, 4.6, "File chosen by the user", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.4, r=0.6)
    box(ax, 63, 55, 24, 4.6, "Owner RSA public key (SPKI)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8.4, r=0.6)
    arrow(ax, (13, 52.6), (13, 47.6), color=NAVY)
    arrow(ax, (63, 52.6), (63, 47.6), color=NAVY)
    # browser chain
    arrow(ax, (22.5, 42), (28.5, 42), color=GREY)
    txt(ax, 25.5, 47.2, "plaintext\n+ digest", 8, GREY)
    arrow(ax, (47.5, 42), (53.5, 42), color=GREY)
    txt(ax, 50.5, 47.2, "ciphertext,\nIV, FEK", 8, GREY)
    arrow(ax, (72.5, 42), (78.5, 42), color=GREY)
    txt(ax, 75.5, 47.2, "wrapped FEK\n(256 B)", 8, GREY)
    txt(ax, 38, 35, "SHA-256 of plaintext (64 hex) travels with the request; the plaintext never leaves the browser", 8, GREY, style="italic")
    # browser -> server
    arrow(ax, (88, 36.5), (88, 24.5), color=TEAL)
    ax.text(86.6, 31, "POST /api/files/upload: ciphertext, IV, wrapped FEK, SHA-256, name, size", ha="right", va="center", fontsize=8, color=TEAL, zorder=6, bbox=dict(fc="white", ec="none", pad=0.6))
    # server chain
    arrow(ax, (78.5, 19), (72.5, 19), color=GREY)
    txt(ax, 75.5, 24.2, "valid\nrequest", 8, GREY)
    arrow(ax, (53.5, 19), (47.5, 19), color=GREY)
    txt(ax, 50.5, 24.2, "stored name\n(random hex)", 8, GREY)
    arrow(ax, (28.5, 19), (22.5, 19), color=GREY)
    txt(ax, 25.5, 24.2, "file id", 8, GREY)
    # rejection
    box(ax, 88, 10.8, 20, 4.6, "bad input: 400 / 413 / 401", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.6)
    # stores
    store(ax, 63, 3.8, 18, 5, "D5  storage/encrypted/<hex>", fs=7.6)
    store(ax, 38, 3.8, 14, 5, "D2  files", fs=8.4)
    store(ax, 13, 3.8, 16, 5, "D4  audit_logs", fs=8.4)
    arrow(ax, (63, 13.4), (63, 6.4), color=TEAL)
    arrow(ax, (38, 13.4), (38, 6.4), color=TEAL)
    arrow(ax, (13, 13.4), (13, 6.4), color=TEAL)
    save(fig, out("05_dfd_level2.png"))


DRAWERS = {"dfd2": d_dfd2}
