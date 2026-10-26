"""Draws the CipherVault design diagrams (matplotlib, 150 dpi) into docs/diagrams/.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; all twelve
    python -m scripts.docs.make_diagrams arch dfd1  # selected keys

01-03 are here; 04 in diagrams_dfd.py, 05 in diagrams_dfd2.py, 06 in diagrams_uml.py, 07/08 in diagrams_more.py,
09 in diagrams_er.py, 10/11/12 in diagrams_flow.py. Every box mirrors a real module, route or file of the product
(backend/app/main.py, api/*.py, services/*.py, db/models.py, core/*.py, frontend/src/lib/vaultCrypto.js and vault.js).
"""

import sys

from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W,
                      arrow, box, canvas, circle, out, panel, save_min as save, txt)


# ------------------------------------------------------------------------------------------------ 01 architecture
def d_arch():
    fig, ax = canvas(W, 7.6, 100)          # height = 69.1
    H_ = 100 * 7.6 / W
    # browser tier
    panel(ax, 1, 49, 98, 19, "Browser: the trusted crypto endpoint (React 19 + Vite dev server, port 5413)")
    box(ax, 14, 56.5, 25, 9, "React single-page app\nLanding, Auth, Dashboard, Files,\nFile detail, Audit, Security", fc=NAVY, fs=8, bold=True)
    box(ax, 41, 56.5, 25, 9, "vaultCrypto.js (Web Crypto)\nAES-256-GCM, RSA-2048-OAEP,\nPBKDF2-SHA-256, SHA-256", fc=TEAL, fs=8, bold=True)
    box(ax, 64, 56.5, 19, 9, "Private key held\nin memory only\n(reload locks vault)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 87, 56.5, 20, 9, "Vite proxy\n/api -> 127.0.0.1:8413\n(or dist served by API)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    arrow(ax, (26.6, 56.5), (28.4, 56.5), color=NAVY)
    # application tier
    panel(ax, 1, 28, 98, 18.5, "Application tier: FastAPI + Uvicorn, 127.0.0.1:8413 (24 endpoints, JWT bearer on all but 4)")
    names = [("auth router\n6 routes", NAVY), ("users router\n2 routes", NAVY), ("files router\n7 routes", NAVY), ("sharing router\n4 routes", NAVY), ("audit router\n3 routes", NAVY)]
    for i, (t, c) in enumerate(names):
        box(ax, 11 + i * 19.5, 38.3, 16.5, 7.4, t, fc=c, fs=8.4, bold=True)
    txt(ax, 50, 31.4, "api/deps.py: JWT bearer check, client IP, login throttle (20 attempts / 300 s)    |    CORS for 8413 and 5413    |    health, config, SPA fallback", 8, GREY)
    arrow(ax, (50, 48.8), (50, 46.2), "HTTP: JSON and multipart ciphertext", color=TEAL, lo=(15, 0), fs=8)
    # service / core tier
    panel(ax, 1, 1, 56, 24.5, "Service and core layer (plain Python)", fc=LIGHT)
    box(ax, 15, 15.5, 25, 10, "permission_service\nget_effective_role\ncan_read / write / delete / share", fc=BLUE, fs=8)
    box(ax, 43, 15.5, 25, 10, "audit_service\nrecord_event (hash chain)\nverify_chain", fc=BLUE, fs=8)
    box(ax, 29, 5.6, 52, 6.4, "core/security.py: bcrypt cost 12, JWT HS256 (120 min)    core/config.py: Settings from .env", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    # persistence
    panel(ax, 59, 1, 40, 24.5, "Persistence (server side)", fc=LIGHT)
    box(ax, 70.5, 14, 21, 14, "SQLAlchemy 2\nSQLite (default) or\nPostgreSQL\n4 tables", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 91, 14, 14, 14, "storage/\nencrypted/\nciphertext\nonly", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    txt(ax, 79, 4, "random 32-hex object names", 8, GREY)
    arrow(ax, (28, 27.8), (28, 20.7), color=NAVY)
    arrow(ax, (44, 27.8), (44, 20.7), color=NAVY)
    arrow(ax, (72, 27.8), (72, 21.2), color=ORANGE)
    arrow(ax, (91, 27.8), (91, 21.2), color=ORANGE)
    ax.set_ylim(0, H_)
    save(fig, out("01_system_architecture.png"))


# ------------------------------------------------------------------------------------------------ 02 workflow
def d_flow():
    fig, ax = canvas(W, 6.4, 100)          # height 58.2
    top = ["1  Register\nbrowser makes RSA-2048\npair; private key sealed\nwith password (PBKDF2)",
           "2  Sign in\nbcrypt check, JWT\n(120 min); fetch key\nbundle",
           "3  Unlock vault\nPBKDF2 -> AES key\ndecrypts private key,\nkept in memory",
           "4  Encrypt + upload\nSHA-256, random FEK + IV,\nAES-256-GCM, wrap FEK,\nPOST ciphertext",
           "5  Server stores\nvalidate, 25 MB limit,\nrandom object name,\nDB row, audit event"]
    bot = ["6  Share\nowner unwraps FEK, wraps\nit for recipient's public\nkey, picks viewer/editor",
           "7  Recipient downloads\nRBAC check, headers carry\nIV + own wrapped FEK",
           "8  Decrypt + verify\nunwrap FEK, AES-GCM tag,\nSHA-256 compared with\nstored digest",
           "9  Audit\nevery step logged;\nverify chain recomputes\nall hashes",
           "10  Revoke / change role\nowner deletes or edits the\npermission row, audited"]
    xs = [10.5 + i * 19.7 for i in range(5)]
    for i, s in enumerate(top):
        box(ax, xs[i], 40.5, 17.6, 14, s, fc=NAVY if i < 3 else TEAL, fs=8)
        if i:
            arrow(ax, (xs[i - 1] + 8.9, 40.5), (xs[i] - 8.9, 40.5), color=GREY)
    for i, s in enumerate(bot):
        x = xs[4 - i]
        fc = [BLUE, BLUE, TEAL, PURPLE, ORANGE][i]
        box(ax, x, 18.5, 17.6, 14, s, fc=fc, fs=8)
        if i:
            arrow(ax, (xs[4 - i + 1] - 8.9, 18.5), (x + 8.9, 18.5), color=GREY)
    arrow(ax, (xs[4], 33.4), (xs[4], 25.6), color=GREY)
    txt(ax, 50, 52.5, "Plaintext and private keys exist only in the browser; the server sees ciphertext, IV, wrapped keys and a plaintext SHA-256.", 8.2, GREY, style="italic")
    box(ax, 27, 3.8, 50, 5.4, "Access is checked on every request by role: owner, editor, viewer", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 77, 3.8, 40, 5.4, "Steps 5-10 each write one hash-chained audit entry", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8)
    save(fig, out("02_high_level_workflow.png"))


# ------------------------------------------------------------------------------------------------ 03 DFD 0
def d_dfd0():
    fig, ax = canvas(W, 5.2, 100)          # height 47.3
    circle(ax, 62, 26, 12, "CipherVault\n0", fc=NAVY, fs=11)
    box(ax, 11, 27, 20, 16, "Owner / Editor /\nViewer\n(signed-in user)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=9.5, bold=True, r=0.6)
    box(ax, 11, 8, 20, 9, "Visitor\n(not signed in)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=9.5, bold=True, r=0.6)
    box(ax, 90, 26, 18, 14, "Deployer\n(.env: JWT secret,\nDB URL, upload\nlimit)", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=9, bold=True, r=0.6, ls="--")
    arrow(ax, (21, 32), (52.2, 32), "credentials, ciphertext + IV + wrapped key,\nshare, revoke, download, verify-chain", lo=(0, 4.2), fs=8, color=NAVY)
    arrow(ax, (51, 21), (21, 21), "JWT, key bundle, ciphertext, wrapped key,\nfile list, audit view, chain result", lo=(0, -4.2), fs=8, color=TEAL)
    arrow(ax, (21, 8), (52.5, 17), "register, login", lo=(6, -3.2), fs=8, color=NAVY)
    arrow(ax, (81, 26), (74.2, 26), "settings", lo=(0, 2.6), fs=8, color=PURPLE, ls="--")
    save(fig, out("03_dfd_level0.png"))


DRAWERS = {"arch": d_arch, "flow": d_flow, "dfd0": d_dfd0}


def main():
    from . import diagrams_dfd as D
    from . import diagrams_dfd2 as D2
    from . import diagrams_er as ER
    from . import diagrams_flow as FL
    from . import diagrams_more as M
    from . import diagrams_uml as U
    all_ = dict(DRAWERS)
    for mod in (D, U, D2, M, ER, FL):
        all_.update(mod.DRAWERS)
    order = ["arch", "flow", "dfd0", "dfd1", "dfd2", "uml", "seq", "usecase", "er", "algo", "keyh", "chain"]
    keys = sys.argv[1:] or [k for k in order if k in all_]
    for k in keys:
        all_[k]()


if __name__ == "__main__":
    main()
