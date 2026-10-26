"""DFD level 1 (diagram 04) - kept apart so the layout can be tuned on its own.

Five processes mirror the five routers of the backend: authentication (api/auth.py), sharing (api/sharing.py),
encrypt-and-store (files upload / update), retrieve-and-decrypt (files list / get / download) and audit (api/audit.py
plus audit_service). Stores D1-D5 are the four tables and the storage/encrypted directory.
"""

from .dgm_lib import BLUE, GREY, INK, NAVY, ORANGE, PALE_BLUE, PALE_PURPLE, PURPLE, TEAL, W, arrow, box, canvas, ellipse, out, save_min as save, store, txt


def d_dfd1():
    fig, ax = canvas(W, 6.8, 100)          # height 61.8
    H_ = 100 * 6.8 / W
    box(ax, 50, 57, 96, 6, "User: Owner, Editor or Viewer  (browser holds the private key; encrypts, wraps, unwraps and decrypts)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=9.5, bold=True, r=0.6)
    xs = [11, 31, 51, 71, 91]
    procs = ["1.0\nAuthenticate", "2.0\nManage\nsharing", "3.0\nEncrypt and\nstore file", "4.0\nRetrieve and\ndecrypt", "5.0\nAudit and\nverify"]
    down = ["email,\npassword,\nkey bundle", "target user,\nrole,\nwrapped key", "ciphertext,\nIV, wrapped\nkey, SHA-256", "list or\ndownload\nrequest", "audit or\nverify\nrequest"]
    up = ["JWT,\nkey bundle", "status,\npermission\nlist", "file\nmetadata", "ciphertext,\nIV, wrapped\nkey, SHA-256", "entries,\nchain\nresult"]
    for x, p, d, u in zip(xs, procs, down, up):
        ellipse(ax, x, 37, 17, 11.5, p, fc=PALE_BLUE, ec=BLUE, fs=8.6)
        arrow(ax, (x - 2.5, 54), (x - 2.5, 43), color=NAVY, lw=1.3)
        arrow(ax, (x + 2.5, 43), (x + 2.5, 54), color=TEAL, lw=1.3)
        txt(ax, x - 3.4, 48.5, d, 8, NAVY, ha="right")
        txt(ax, x + 3.4, 48.5, u, 8, TEAL, ha="left")
    # data stores
    sx = {"D1": 11, "D3": 31, "D2": 51, "D5": 71, "D4": 91}
    store(ax, sx["D1"], 8, 16, 6, "D1  users", fs=8.6)
    store(ax, sx["D3"], 8, 17, 6, "D3  file_permissions", fs=8.2)
    store(ax, sx["D2"], 8, 16, 6, "D2  files", fs=8.6)
    store(ax, sx["D5"], 8, 17, 6, "D5  storage/\nencrypted/", fs=8.2)
    store(ax, sx["D4"], 8, 16, 6, "D4  audit_logs", fs=8.6)
    # writes (teal) and reads (grey dashed)
    arrow(ax, (11, 31.2), (11, 11.2), color=TEAL, lw=1.3)
    txt(ax, 12.2, 21.5, "user row", 8, TEAL, ha="left")
    arrow(ax, (31, 31.2), (31, 11.2), color=TEAL, lw=1.3)
    txt(ax, 32.2, 26, "permission\nrow", 8, TEAL, ha="left")
    arrow(ax, (51, 31.2), (51, 11.2), color=TEAL, lw=1.3)
    txt(ax, 52.2, 26, "file row", 8, TEAL, ha="left")
    arrow(ax, (55, 31.8), (68, 11.2), color=TEAL, lw=1.3)
    txt(ax, 61.2, 19, "ciphertext", 8, TEAL, ha="right")
    arrow(ax, (71, 11.2), (71, 31.2), color=GREY, lw=1.2, ls="--")
    txt(ax, 72.2, 17.5, "ciphertext", 8, GREY, ha="left")
    arrow(ax, (91, 31.2), (91, 11.2), color=TEAL, lw=1.3)
    txt(ax, 92.2, 22, "hash-chained\nentry", 8, TEAL, ha="left")
    # reads
    arrow(ax, (14.5, 11.2), (27.5, 32.2), color=GREY, lw=1.2, ls="--")
    txt(ax, 17.6, 22.8, "public\nkeys", 8, GREY, ha="left")
    arrow(ax, (46, 11.2), (33, 32.4), color=GREY, lw=1.2, ls="--")
    txt(ax, 38.5, 17.5, "owner id", 8, GREY, ha="center")
    arrow(ax, (48, 11.2), (68, 32.4), color=GREY, lw=1.2, ls="--")
    txt(ax, 60.5, 13.6, "metadata, IV,\nSHA-256", 8, GREY, ha="center")
    txt(ax, 50, 1.6, "Process 4.0 also reads D3 (the caller's role and own wrapped key); dashed grey = read, teal = write", 8, GREY, style="italic")
    # audit events from 1.0 - 4.0
    arrow(ax, (79.5, 37), (82.5, 37), color=PURPLE, lw=1.3, ls="--")
    txt(ax, 81, 41.5, "events", 8, PURPLE)
    box(ax, 82, 25, 15, 8, "audit events from\n1.0 to 4.0 (action,\nuser, file, success,\nIP address)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.6, ls="--")
    ax.set_ylim(0, H_)
    save(fig, out("04_dfd_level1.png"))


DRAWERS = {"dfd1": d_dfd1}
