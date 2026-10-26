"""Flowcharts 10, 11 and 12 of the CipherVault design.

10  core algorithm: encrypt-and-upload (vault.js uploadFile + files.py upload) and download-decrypt-verify (fetchAndDecrypt + download)
11  key hierarchy: password -> PBKDF2 -> AES key -> private key -> RSA unwrap -> FEK -> file (vaultCrypto.js)
12  audit hash chain: audit_service.record_event / verify_chain with the two weaknesses measured in docs/REPORT_FACTS.md
"""

from .dgm_lib import (BLUE, GREY, INK, LIGHT, NAVY, ORANGE, PALE_BLUE, PALE_ORANGE, PALE_PURPLE, PALE_TEAL, PURPLE, TEAL, W,
                      arrow, box, canvas, diamond, out, panel, pline, save_min as save, txt)


def _yes(ax, x, y, t="yes", c=TEAL):
    txt(ax, x, y, t, 8.2, c, bold=True)


def _no(ax, x, y, t="no", c=ORANGE):
    txt(ax, x, y, t, 8.2, c, bold=True)


# ------------------------------------------------------------------------------------------------ 10 algorithm
def d_algo():
    HI = 9.9
    fig, ax = canvas(W, HI, 100)          # height 90
    H_ = 100 * HI / W
    ax.text(16, H_ - 3, "Encrypt and upload", ha="center", va="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.text(71, H_ - 3, "Download, decrypt and verify", ha="center", va="center", fontsize=10, fontweight="bold", color=NAVY)
    ax.plot([49.5, 49.5], [3, H_ - 6], color="#C9D3E0", lw=1.0, ls="--")
    # ---------- left column
    L = 16
    ly = [83, 76, 69, 62, 55, 48, 41, 31, 22.5, 15, 7.5]
    box(ax, L, ly[0], 28, 5, "uploadFile(file, me)  [browser]", fc=NAVY, fs=8.2, bold=True, r=2.4)
    diamond(ax, L, ly[1], 24, 7.2, "0 < size <= 25 MB?", fs=8.2)
    box(ax, L, ly[2], 28, 4.8, "SHA-256 of the plaintext", fc=BLUE, fs=8)
    box(ax, L, ly[3], 28, 5.4, "random FEK (AES-256) and\nrandom 12-byte IV", fc=BLUE, fs=8)
    box(ax, L, ly[4], 28, 5.4, "AES-256-GCM encrypt:\nciphertext = data + 16-byte tag", fc=BLUE, fs=8)
    box(ax, L, ly[5], 28, 5.4, "RSA-OAEP (SHA-256) wrap FEK\nwith owner's public key (256 B)", fc=BLUE, fs=8)
    box(ax, L, ly[6], 28, 5.4, "POST /api/files/upload\n(multipart, JWT)", fc=BLUE, fs=8)
    diamond(ax, L, ly[7], 28, 8.4, "JWT valid, IV 12 B,\ndigest 64 hex, size ok?", fs=8)
    box(ax, L, ly[8], 28, 5.4, "[server] write ciphertext to\nstorage/encrypted/<32-hex>", fc=TEAL, fs=8)
    box(ax, L, ly[9], 28, 5.4, "INSERT files row;\naudit event 'upload'", fc=TEAL, fs=8)
    box(ax, L, ly[10], 28, 5, "201 Created + metadata", fc=NAVY, fs=8.2, bold=True, r=2.4)
    hs = [2.5, 3.6, 2.4, 2.7, 2.7, 2.7, 2.7, 4.2, 2.7, 2.7, 2.5]
    for i in range(10):
        arrow(ax, (L, ly[i] - hs[i]), (L, ly[i + 1] + hs[i + 1]), color=GREY)
    for i in (1, 7):
        txt(ax, L + 1.2, (ly[i] - hs[i] + ly[i + 1] + hs[i + 1]) / 2, "yes", 8.2, TEAL, ha="left", bold=True)
    box(ax, 40.5, ly[1], 14, 6.2, "error shown;\nnothing sent", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.7)
    arrow(ax, (L + 12, ly[1]), (33.4, ly[1]), color=ORANGE)
    _no(ax, 29.5, ly[1] + 1.6)
    box(ax, 40.5, ly[7], 14, 7.0, "400 / 401 / 413;\nnothing stored", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.7)
    arrow(ax, (L + 14, ly[7]), (33.4, ly[7]), color=ORANGE)
    _no(ax, 31.7, ly[7] + 1.6)
    # ---------- right column
    R = 71
    ry = [83, 75.5, 67, 58.5, 50, 42, 33.5, 25.5, 16.5, 8]
    box(ax, R, ry[0], 31, 5, "fetchAndDecrypt(id, key)  [browser]", fc=NAVY, fs=8.2, bold=True, r=2.4)
    box(ax, R, ry[1], 32, 5.4, "GET /api/files/{id} (JWT): metadata,\nIV, caller's own wrapped FEK", fc=BLUE, fs=8)
    diamond(ax, R, ry[2], 26, 7.6, "role is owner,\neditor or viewer?", fs=8.2)
    box(ax, R, ry[3], 32, 5.8, "[server] GET .../download: ciphertext,\nIV, wrapped FEK, SHA-256; audit", fc=TEAL, fs=8)
    box(ax, R, ry[4], 31, 5.4, "unwrap FEK: RSA-OAEP with\nthe user's private key", fc=BLUE, fs=8)
    diamond(ax, R, ry[5], 24, 7.2, "AES-GCM tag valid?", fs=8.2)
    box(ax, R, ry[6], 31, 4.8, "plaintext = AES-256-GCM decrypt", fc=BLUE, fs=8)
    diamond(ax, R, ry[7], 28, 7.6, "SHA-256(plaintext) =\nstored digest?", fs=8.2)
    box(ax, R, ry[8], 31, 4.8, "save file from a Blob", fc=BLUE, fs=8)
    box(ax, R, ry[9], 31, 5, "plaintext only on user's disk", fc=NAVY, fs=8, bold=True, r=2.4)
    hr = [2.5, 2.7, 3.8, 2.9, 2.7, 3.6, 2.4, 3.8, 2.4, 2.5]
    for i in range(9):
        arrow(ax, (R, ry[i] - hr[i]), (R, ry[i + 1] + hr[i + 1]), color=GREY)
    for i in (2, 5, 7):
        txt(ax, R + 1.2, (ry[i] - hr[i] + ry[i + 1] + hr[i + 1]) / 2, "yes", 8.2, TEAL, ha="left", bold=True)
    for i, t, hw in ((2, "403 +\naudit\ndenied", 13), (5, "error:\ncorrupt\nor wrong\nkey", 12), (7, "error:\ndigest\nmismatch,\nnot saved", 14)):
        box(ax, 93.4, ry[i], 11.6, 8.2, t, fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.7)
        arrow(ax, (R + hw, ry[i]), (87.5, ry[i]), color=ORANGE)
        _no(ax, (R + hw + 87.5) / 2, ry[i] + 1.6)
    ax.set_ylim(0, H_)
    save(fig, out("10_flowchart_encrypt_upload.png"))


# ------------------------------------------------------------------------------------------------ 11 key hierarchy
def d_keyh():
    HI = 7.8
    fig, ax = canvas(W, HI, 100)          # height 70.9
    H_ = 100 * HI / W
    panel(ax, 1, 40, 58, 29.5, "Browser, at registration and unlock (vaultCrypto.js)", fc=LIGHT)
    panel(ax, 61, 40, 38, 29.5, "Server database (what is stored)", fc=LIGHT)
    box(ax, 10, 57, 15, 7.4, "Account password\n(typed, never sent\nto be kept)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 30, 57, 17, 7.4, "PBKDF2-HMAC-\nSHA-256, 120,000\niterations, 16-byte salt", fc=BLUE, fs=8)
    box(ax, 50, 57, 15, 7.4, "AES-256-GCM key\n(key-encryption\nkey, not exported)", fc=TEAL, fs=8)
    arrow(ax, (17.6, 57), (21.4, 57), color=GREY)
    arrow(ax, (38.6, 57), (42.4, 57), color=GREY)
    box(ax, 21, 46, 36, 6.6, "RSA-2048 key pair (generated once in the browser):\nprivate key as PKCS#8, public key as SPKI", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    box(ax, 51, 46, 14, 6.6, "private key\nbundle JSON\n{salt, iv, data}", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8)
    arrow(ax, (39.2, 46), (43.8, 46), "AES-GCM", color=PURPLE, lo=(0, 2.6), fs=8)
    arrow(ax, (50, 53.4), (51, 49.4), color=TEAL)
    # server column
    box(ax, 80, 62, 34, 5, "users.password_hash: bcrypt, cost 12", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 80, 55, 34, 5, "users.public_key (SPKI, base64)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 80, 48, 34, 5, "users.encrypted_private_key (bundle)\nusers.private_key_salt", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    box(ax, 80, 43.0, 34, 2.6, "never stored: password, private key, FEK in clear", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.5)
    arrow(ax, (58.2, 46), (62.6, 48), color=PURPLE, lw=1.2)
    # file layer
    panel(ax, 1, 1, 98, 36, "Per file (uploadFile, shareWith, fetchAndDecrypt)", fc=LIGHT)
    box(ax, 12, 22, 17, 8, "File bytes\n+ SHA-256\n(plaintext digest)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8)
    box(ax, 33, 22, 18, 8, "File encryption\nkey (FEK):\nrandom AES-256", fc=TEAL, fs=8)
    box(ax, 55, 22, 18, 8, "AES-256-GCM\nwith random\n12-byte IV", fc=BLUE, fs=8)
    box(ax, 83, 22, 30, 8, "files: ciphertext object + iv\n+ plaintext_sha256", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    arrow(ax, (20.6, 22), (24, 22), color=GREY)
    arrow(ax, (42, 22), (46, 22), color=GREY)
    arrow(ax, (64, 22), (68, 22), color=GREY)
    box(ax, 33, 8.5, 28, 7.0, "RSA-OAEP (SHA-256): wrap FEK with a public key\n-> 256-byte wrapped FEK", fc=BLUE, fs=8)
    arrow(ax, (33, 18), (33, 12.2), color=TEAL)
    box(ax, 70, 8.5, 38, 7.0, "files.owner_wrapped_fek (owner) and one\nfile_permissions.wrapped_fek per recipient", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8)
    arrow(ax, (47.2, 8.5), (50.9, 8.5), color=GREY)
    box(ax, 10.5, 8.5, 14, 6.4, "owner's or recipient's\npublic key (SPKI)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.6)
    arrow(ax, (17.6, 8.5), (18.9, 8.5), color=GREY)
    txt(ax, 3, 32.2, "A recipient does the reverse: fetches the own wrapped FEK and unwraps it with the own private key after unlock", 8, GREY, ha="left", style="italic")
    txt(ax, 83, 31.4, "Server sees ciphertext only", 8, ORANGE, bold=True)
    ax.set_ylim(0, H_)
    save(fig, out("11_key_hierarchy.png"))


# ------------------------------------------------------------------------------------------------ 12 audit chain
def d_chain():
    HI = 6.6
    fig, ax = canvas(W, HI, 100)          # height 60
    H_ = 100 * HI / W
    fields = "id, timestamp_utc, user_id, file_id,\naction, success, ip_address, details,\nprevious_hash, current_hash"
    xs = [15, 50, 85]
    heads = ["entry n-1", "entry n", "entry n+1"]
    for i, (x, h) in enumerate(zip(xs, heads)):
        box(ax, x, 49, 24, 6, h, fc=NAVY if i != 1 else TEAL, fs=9.5, bold=True, r=0.8)
        box(ax, x, 38.5, 24, 12.5, fields, fc="white", tc=INK, ec=NAVY, fs=8, r=0.8)
    for x0 in (27.2, 62.2):
        arrow(ax, (x0, 38.5), (x0 + 10.6, 38.5), color=ORANGE, lw=1.6)
        txt(ax, x0 + 5.3, 43.4, "next\nprevious_hash\n= this\ncurrent_hash", 8, ORANGE)
    box(ax, 15, 56.8, 24, 4.4, "first entry: previous_hash = GENESIS", fc=PALE_PURPLE, tc=INK, ec=PURPLE, fs=8, r=0.5)
    # hash input
    box(ax, 50, 24, 96, 7.0, "current_hash = SHA-256( previous_hash | timestamp.isoformat() | user_id | file_id | action | success | details )\nrecord_event reads the last row's current_hash, hashes the new entry, INSERTs and commits (no lock)", fc=PALE_TEAL, tc=INK, ec=TEAL, fs=8.4, r=0.8)
    arrow(ax, (50, 32.1), (50, 27.8), color=TEAL)
    # verify
    box(ax, 28, 11.6, 54, 8.6, "verify_chain(): walk entries in id order; for each row check\nprevious_hash == the previous row's current_hash and\nrecompute SHA-256 of its fields == stored current_hash;\nreturn (valid, entries checked, first failing id)", fc=PALE_BLUE, tc=INK, ec=BLUE, fs=8, r=0.8)
    box(ax, 77.5, 11.6, 41, 8.6, "Measured: 8 of 9 tamper types caught (edits, delete,\nswap, insert). NOT caught: tail truncation (0/199) and a\nrewrite that recomputes later hashes. 100 concurrent\nwriters forked the chain (first bad entry 5047)", fc=PALE_ORANGE, tc=INK, ec=ORANGE, fs=8, r=0.8)
    ax.set_ylim(0, H_)
    save(fig, out("12_audit_hash_chain.png"))


DRAWERS = {"algo": d_algo, "keyh": d_keyh, "chain": d_chain}
