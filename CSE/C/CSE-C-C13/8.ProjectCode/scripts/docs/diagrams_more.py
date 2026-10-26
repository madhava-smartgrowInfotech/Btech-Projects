"""Sequence diagram (07) and use-case diagram (08).

Sequence: frontend/src/lib/vault.js (uploadFile, shareWith, fetchAndDecrypt) against backend/app/api/files.py and
sharing.py. Use cases: the rules of services/permission_service.py and the routes of the five routers.
"""

from matplotlib.patches import FancyBboxPatch, Rectangle

from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W, actor, arrow, box,
                      canvas, ellipse, out, save_min as save, txt)


def d_seq():
    HI = 10.4
    fig, ax = canvas(W, HI, 100)
    H_ = 100 * HI / W
    names = ["Owner's browser\n(React + Web Crypto)", "FastAPI\n(files, sharing routers)", "Database\n(users, files, perms,\naudit_logs)", "storage/\nencrypted/", "Editor / Viewer\nbrowser"]
    xs = [9, 34, 57, 75, 91]
    cols = [NAVY, BLUE, ORANGE, ORANGE, TEAL]
    top = H_ - 5.0
    for x, n, c in zip(xs, names, cols):
        box(ax, x, top, 16.5, 8, n, fc=c, fs=8, bold=True, r=0.8)

    def msg(y, a, b, text, color=NAVY, dashed=False):
        arrow(ax, (xs[a], y), (xs[b], y), color=color, lw=1.4, ls="--" if dashed else "-")
        ax.text((xs[a] + xs[b]) / 2, y + 0.8, text, ha="center", va="bottom", fontsize=8, color=INK, zorder=6, linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9))

    def note(y, k, text, fc=PALE_ORANGE, ec=ORANGE, w=28, h=6):
        x = xs[k] + (w / 2 - 7.5 if k == 0 else (-(w / 2 - 7.5) if k == 4 else 0))
        box(ax, x, y, w, h, text, fc=fc, tc=INK, ec=ec, fs=8, r=0.6)

    def title(y, text):
        ax.text(50, y, text, ha="center", va="center", fontsize=9, fontweight="bold", color=NAVY, zorder=6,
                bbox=dict(fc="white", ec="none", pad=1.0))

    y = top - 7.0
    title(y, "A. Upload  (vault.js uploadFile -> files.py upload)")
    y -= 5.0
    note(y, 0, "SHA-256 of the file; random FEK and IV; AES-256-GCM;\nwrap FEK with the owner's RSA public key", w=37, h=5.6)
    y -= 7.0
    msg(y, 0, 1, "POST /api/files/upload (JWT)\nciphertext, IV, wrapped FEK, SHA-256")
    y -= 5.4
    box(ax, xs[1] + 11.5, y + 1.2, 22.0, 4.8, "validate: 12-byte IV, 64-hex\ndigest, base64, <= 25 MB (413)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.6)
    y -= 4.4
    msg(y, 1, 3, "write ciphertext under a random 32-hex name", color=ORANGE)
    y -= 4.0
    msg(y, 1, 2, "INSERT files; INSERT audit_logs (upload)", color=ORANGE)
    y -= 4.0
    msg(y, 1, 0, "201 Created: file metadata, no key material", color=TEAL, dashed=True)
    y -= 5.0
    title(y, "B. Share  (vault.js shareWith -> sharing.py share_file)")
    y -= 4.8
    note(y, 0, "GET /api/users?q=..., unwrap own FEK with private\nkey, wrap it for the recipient's public key", w=37, h=5.6)
    y -= 6.6
    msg(y, 0, 1, "POST /api/files/{id}/share\nuser_id, role, 256-byte wrapped FEK")
    y -= 5.6
    msg(y, 1, 2, "owner only (else 403); INSERT file_permissions;\nINSERT audit_logs (share)", color=ORANGE)
    y -= 4.6
    msg(y, 1, 0, "200 Shared", color=TEAL, dashed=True)
    y -= 5.0
    title(y, "C. Download and decrypt  (vault.js fetchAndDecrypt -> files.py download)")
    y -= 4.4
    msg(y, 4, 1, "GET /api/files/{id} and /download (JWT)")
    y -= 5.4
    msg(y, 1, 2, "get_effective_role; pick caller's wrapped FEK;\nINSERT audit_logs (download)", color=ORANGE)
    y -= 4.2
    msg(y, 1, 3, "read ciphertext object", color=ORANGE)
    y -= 4.2
    msg(y, 1, 4, "200 ciphertext + headers: IV, own wrapped FEK, SHA-256", color=TEAL, dashed=True)
    y -= 5.2
    note(y, 4, "unwrap FEK with own private key;\nAES-GCM decrypt (tag check);\ncompare SHA-256, then save", fc=PALE_TEAL, ec=TEAL, w=30, h=7.0)
    y -= 6.6
    msg(y, 4, 1, "DELETE /api/files/{id}  (caller is editor or viewer)", color=PURPLE)
    y -= 4.0
    msg(y, 1, 4, "403 owner only; audit: unauthorized_access", color=PURPLE, dashed=True)
    for x in xs:
        ax.plot([x, x], [top - 4.0, y - 2.5], color=GREY, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.set_ylim(y - 2.5, H_)
    save(fig, out("07_sequence_upload_share_download.png"))


def d_usecase():
    fig, ax = canvas(W, 9.0, 100)          # height 81.8
    H_ = 100 * 9.0 / W
    ax.add_patch(Rectangle((23, 1.5), 59, H_ - 3, fc="#FAFBFD", ec=NAVY, lw=1.5, zorder=0))
    ax.text(52.5, H_ - 3.2, "CipherVault (React + FastAPI)", ha="center", va="center", fontsize=10, fontweight="bold", color=NAVY, zorder=3)
    rows = [("Register  (browser generates RSA key pair)", "v"), ("Sign in  (bcrypt check, JWT)", "v"),
            ("Unlock vault  (password -> private key)", "r"), ("List own and shared files", "r"), ("Download, decrypt and verify", "r"),
            ("Replace file content", "e"), ("Upload encrypted file", "o"), ("Share file as viewer or editor", "o"),
            ("Change a user's role", "o"), ("Revoke access", "o"), ("Delete file", "o"), ("View file history", "o")]
    y0, dy = H_ - 9.5, 6.0
    pos = {}
    for i, (t, g) in enumerate(rows):
        cy = y0 - i * dy
        ellipse(ax, 40, cy, 30, 5.2, t, fc=PALE_BLUE, ec=BLUE, fs=8)
        pos[i] = cy
    # right column
    ellipse(ax, 70, 56, 21, 5.2, "View audit log", fc=PALE_PURPLE, ec=PURPLE, fs=8)
    ellipse(ax, 70, 48, 21, 5.2, "Verify audit chain", fc=PALE_PURPLE, ec=PURPLE, fs=8)
    box(ax, 70, 31, 22, 14, "Every use case on the left\nwrites one hash-chained\naudit entry; denied\nattempts are logged as\nunauthorized_access", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8, r=0.8)
    box(ax, 70, 14, 22, 12, "Roles are per file: one\naccount can own one file\nand only view another.\nowner > editor > viewer", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.8)
    # actors
    ax_x = 8
    ya = {"v": 66, "r": 49, "e": 33, "o": 11}
    labels = {"v": "Visitor\n(not signed in)", "r": "Viewer\n(read)", "e": "Editor\n(read + update)", "o": "Owner\n(all rights)"}
    for k in ya:
        actor(ax, ax_x, ya[k], labels[k], fs=8.5)
    # generalisation: editor -> viewer, owner -> editor
    arrow(ax, (ax_x, ya["e"] + 9.8), (ax_x, ya["r"] - 5.0), color=NAVY, lw=1.3)
    txt(ax, ax_x + 1.2, (ya["e"] + 9.8 + ya["r"] - 5.0) / 2, "inherits", 8, GREY, ha="left")
    arrow(ax, (ax_x, ya["o"] + 9.8), (ax_x, ya["e"] - 5.0), color=NAVY, lw=1.3)
    txt(ax, ax_x + 1.2, (ya["o"] + 9.8 + ya["e"] - 5.0) / 2, "inherits", 8, GREY, ha="left")
    # associations
    grp = {"v": [0, 1], "r": [2, 3, 4], "e": [5], "o": [6, 7, 8, 9, 10, 11]}
    for k, idxs in grp.items():
        for i in idxs:
            ax.plot([ax_x + 2.4, 25.0], [ya[k] + 4.2, pos[i]], color=GREY, lw=1.0, zorder=2)
    # auditor
    actor(ax, 92, 46, "Auditor\n(any signed-in\nuser)", fs=8.5, color=PURPLE)
    ax.plot([90, 81], [50, 56], color=PURPLE, lw=1.0, zorder=2)
    ax.plot([90, 81], [50, 48], color=PURPLE, lw=1.0, zorder=2)
    save(fig, out("08_use_case.png"))


DRAWERS = {"seq": d_seq, "usecase": d_usecase}
