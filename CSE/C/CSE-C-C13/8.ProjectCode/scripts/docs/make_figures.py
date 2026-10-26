"""Result figures for the CipherVault documents (matplotlib, 150 dpi) -> docs/figures/.

    python -m scripts.docs.make_figures            # all
    python -m scripts.docs.make_figures f01 f05    # selected

Every plotted number is read from docs/metrics/metrics.json and docs/metrics/tests.json (through facts.py); nothing is typed in.
FIGURES = [(key, filename, caption), ...] is importable by the chapter and deck modules.
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from . import facts as F
from .dgm_lib import BLUE, GREY, INK, NAVY, ORANGE, TEAL

RED = "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelsize": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8895A7", "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.grid": True, "grid.color": "#E3E8EF", "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "legend.frameon": False, "legend.fontsize": 8.5})

AES_SIZES = sorted(int(k) for k in F.AES)                      # 1 KiB .. 25 MiB
E2E_SIZES = sorted(int(k) for k in F.E2E)                      # 1 KiB, 1 MiB, 10 MiB
API_SIZES = sorted(int(k) for k in F.API["upload_ms"])         # 1 KiB .. ~25 MiB (26,212,352 B)
PRINCIPALS = ["owner", "editor", "viewer", "stranger"]
OPERATIONS = ["metadata", "download", "update", "list_permissions", "share", "change_role", "revoke", "delete", "file_audit"]
TAMPER_LABEL = {
    "edit_details": "edit details field", "edit_action": "edit action field", "edit_success": "edit success flag", "edit_user": "edit user id",
    "edit_hash": "edit stored hash", "delete_entry_middle": "delete a middle entry", "swap_adjacent": "swap two entries",
    "insert_forged_entry": "insert a forged entry", "truncate_tail": "truncate the tail",
}


def size_label(n):
    if n >= 1024 * 1024:
        v = n / (1024 * 1024)
        return f"{round(v):d} MiB" if abs(v - round(v)) < 0.05 or v > 20 else f"{v:.1f} MiB"
    if n >= 1024:
        return f"{n // 1024} KiB"
    return f"{n} B"


def out(name):
    os.makedirs(F.FIGS, exist_ok=True)
    return os.path.join(F.FIGS, name)


def finish(fig, name):
    fig.tight_layout()
    fig.savefig(out(name), dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", name)


def fmt_ms(v):
    return F.ms(v)


# ------------------------------------------------------------------------------------------------------ captions
def _captions():
    a1, a25 = F.AES[str(AES_SIZES[0])], F.AES[str(AES_SIZES[-1])]
    e1, e10 = F.E2E["1048576"], F.E2E["10485760"]
    api = F.API
    up25, dn25 = api["upload_ms"][str(API_SIZES[-1])], api["download_ms"][str(API_SIZES[-1])]
    tam = F.TAMPER["audit_tamper"]
    caught = sum(1 for k in tam if tam[k]["detected"] == tam[k]["trials"])
    sc = F.SCALE
    big = sc[str(max(int(k) for k in sc))]
    cc = F.CONC["4_workers"]
    return [
        ("f01", "f01_aes_latency_vs_size.png",
         f"Browser Web Crypto latency against plaintext size (median, shaded to p95; log-log). At 25 MiB AES-256-GCM encryption takes {fmt_ms(a25['encrypt']['median'])} ms, "
         f"decryption {fmt_ms(a25['decrypt']['median'])} ms and SHA-256 {fmt_ms(a25['sha256']['median'])} ms; at 1 KiB encryption takes {fmt_ms(a1['encrypt']['median'])} ms."),
        ("f02", "f02_e2e_overhead.png",
         f"End-to-end browser transfer with and without encryption on the same endpoint (median, whisker to p95). For 10 MiB the encrypted upload takes {fmt_ms(e10['encrypted_up']['median'])} ms "
         f"against {fmt_ms(e10['plain_up']['median'])} ms plain, and the encrypted download with decryption and SHA-256 check takes {fmt_ms(e10['encrypted_down']['median'])} ms against {fmt_ms(e10['plain_down']['median'])} ms."),
        ("f03", "f03_api_latency.png",
         f"API latency over loopback (median; marker = p95 where several runs exist). Login with bcrypt cost {F.BCRYPT_COST} takes {fmt_ms(api['login_ms']['median'])} ms; "
         f"the health check takes {fmt_ms(api['health_ms']['median'])} ms and one audit write {fmt_ms(F.M['audit_write_ms']['median'])} ms."),
        ("f04", "f04_api_transfer_scaling.png",
         f"Upload and download of ciphertext through the API against object size (median, shaded to p95). The largest object (about 25 MiB, "
         f"{up25['n']} runs) uploads in {fmt_ms(up25['median'])} ms and downloads in {fmt_ms(dn25['median'])} ms; sample counts shrink with size, so the right-hand points are indicative."),
        ("f05", "f05_rbac_matrix.png",
         f"Access-control matrix measured on the live API: four principals against nine operations on one file. Cell text is the observed HTTP status; "
         f"{F.RBAC['matched']} of {F.RBAC['total']} cells matched the expected allow or deny decision."),
        ("f06", "f06_tamper_detection.png",
         f"Tamper-detection rate per attack class. {caught} of {len(tam)} audit-log edit classes were detected in every trial; truncating the tail of the chain was detected in "
         f"{tam['truncate_tail']['detected']} of {tam['truncate_tail']['trials']} trials, and a full re-hash of later entries is not detected. All {F.TAMPER['ciphertext_bitflip']['trials']} ciphertext bit flips were rejected by AES-GCM."),
        ("f07", "f07_chain_verify_scaling.png",
         f"Time to verify the whole audit chain against its length (median of repeated runs). Verifying {big['checked']} entries takes {fmt_ms(big['verify_ms_median'])} ms; "
         "the cost grows roughly with the number of entries, with scatter caused by other processes on the host."),
        ("f08", "f08_crypto_primitives.png",
         f"Cost of the key-management primitives in the browser (median, log scale; tick = p95). RSA-2048 key generation takes {fmt_ms(F.CRY['rsa_keygen']['median'])} ms once per account, "
         f"PBKDF2 with {F.PBKDF2_ITER:,} iterations {fmt_ms(F.CRY['pbkdf2_120k']['median'])} ms per unlock, RSA-OAEP unwrap {fmt_ms(F.CRY['rsa_unwrap']['median'])} ms and wrap {fmt_ms(F.CRY['rsa_wrap']['median'])} ms per file."),
        ("f09", "f09_test_summary.png",
         f"Automated checks that were run: {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pytest tests, {F.E2E_PASSED} of {F.E2E_TOTAL} API end-to-end checks, "
         f"{F.UI_PASSED} of {F.UI_TOTAL} browser-walk steps and {F.EVAL_PASSED} of {F.EVAL_TOTAL} evaluation checks passed."),
        ("f10", "f10_audit_concurrency.png",
         f"Audit chain after {cc['requests']} concurrent failed logins from {4} workers ({cc['seconds']} s): the chain was valid before the burst and invalid afterwards, "
         f"first broken link at entry {cc['failure_at']} of {cc['checked']}. Concurrent writers read the same previous hash, so the chain forks (a documented defect, not fixed)."),
    ]


FIGURES = _captions()
FIG_FILES = {k: f for k, f, _ in FIGURES}
FIG_CAPTIONS = {k: c for k, _, c in FIGURES}


def fig_path(key):
    return os.path.join(F.FIGS, FIG_FILES[key])


# ------------------------------------------------------------------------------------------------------ f01
def f01():
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    x = np.array(AES_SIZES, dtype=float)
    for key, label, col, mk in (("encrypt", "AES-256-GCM encrypt", NAVY, "o"), ("decrypt", "AES-256-GCM decrypt", TEAL, "s"), ("sha256", "SHA-256 digest", ORANGE, "^")):
        med = np.array([F.AES[str(s)][key]["median"] for s in AES_SIZES])
        p95 = np.array([F.AES[str(s)][key]["p95"] for s in AES_SIZES])
        ax.plot(x, med, color=col, marker=mk, lw=1.8, ms=5, label=label)
        ax.fill_between(x, med, p95, color=col, alpha=0.12, lw=0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([size_label(int(s)) for s in x], fontsize=8)
    ax.set_xlim(x[0] * 0.6, x[-1] * 1.5)
    ax.minorticks_off()
    ax.set_xlabel("Plaintext size")
    ax.set_ylabel("Latency (ms, median)")
    ax.set_title("Browser Web Crypto latency against file size")
    ax.legend(loc="upper left")
    ax.text(0.99, 0.04, "1 KiB and 64 KiB timed in batches of 200 operations;\nshaded band = median to p95", transform=ax.transAxes, ha="right", fontsize=7.5, color=GREY)
    finish(fig, "f01_aes_latency_vs_size.png")


# ------------------------------------------------------------------------------------------------------ f02
def f02():
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    x = np.arange(len(E2E_SIZES))
    w = 0.36
    for ax, (pk, ek, title) in zip(axes, (("plain_up", "encrypted_up", "Upload"), ("plain_down", "encrypted_down", "Download (+ decrypt + SHA-256 check)"))):
        for off, key, col, lab in ((-w / 2, pk, GREY, "plain (no encryption)"), (w / 2, ek, TEAL, "encrypted")):
            med = np.array([F.E2E[str(s)][key]["median"] for s in E2E_SIZES])
            p95 = np.array([F.E2E[str(s)][key]["p95"] for s in E2E_SIZES])
            bars = ax.bar(x + off, med, w, color=col, label=lab, yerr=[np.zeros(len(med)), p95 - med], error_kw=dict(ecolor=INK, lw=0.9, capsize=2.5))
            for b, v in zip(bars, med):
                ax.text(b.get_x() + b.get_width() / 2, 4, fmt_ms(v), ha="center", va="bottom", fontsize=7.5, color="white", fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([size_label(s) for s in E2E_SIZES])
        ax.set_title(title, fontsize=9.5)
        ax.set_xlabel("File size")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Time (ms, median; whisker to p95)")
    axes[0].legend(loc="upper left")
    finish(fig, "f02_e2e_overhead.png")


# ------------------------------------------------------------------------------------------------------ f03
def f03():
    A = F.API
    items = [
        ("GET /api/health", A["health_ms"]["median"], A["health_ms"]["p95"]),
        ("GET /api/auth/me", A["me_ms"]["median"], A["me_ms"]["p95"]),
        ("GET /api/files (list)", A["list_files_ms"]["median"], A["list_files_ms"]["p95"]),
        ("Audit event write", F.M["audit_write_ms"]["median"], F.M["audit_write_ms"]["p95"]),
        ("Share file (1 run)", A["share_ms"], None),
        ("Change role (1 run)", A["change_role_ms"], None),
        ("Revoke access (1 run)", A["revoke_ms"], None),
        ("Download after revoke -> 403 (1 run)", A["download_after_revoke_ms"], None),
        ("POST /auth/login (bcrypt 12)", A["login_ms"]["median"], A["login_ms"]["p95"]),
        ("Failed login (bcrypt 12)", A["login_fail_ms"]["median"], A["login_fail_ms"]["p95"]),
    ]
    items.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    y = np.arange(len(items))
    cols = [ORANGE if "login" in n.lower() else TEAL for n, *_ in items]
    ax.barh(y, [t[1] for t in items], color=cols, height=0.62)
    for yy, (n, med, p95) in zip(y, items):
        if p95:
            ax.plot([p95], [yy], marker="|", color=INK, ms=11, mew=1.4)
        ax.text((p95 or med) * 1.08, yy, fmt_ms(med) + (f"  (p95 {fmt_ms(p95)})" if p95 else ""), va="center", fontsize=7.8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([t[0] for t in items], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(1, 2200)
    ax.set_xlabel("Latency over loopback (ms, median; | = p95)")
    ax.set_title("API latency by operation")
    ax.grid(axis="y", visible=False)
    finish(fig, "f03_api_latency.png")


# ------------------------------------------------------------------------------------------------------ f04
def f04():
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    x = np.array(API_SIZES, dtype=float)
    for key, label, col, mk in (("upload_ms", "Upload (POST /api/files/upload)", NAVY, "o"), ("download_ms", "Download (GET /api/files/{id}/download)", TEAL, "s")):
        med = np.array([F.API[key][str(s)]["median"] for s in API_SIZES])
        p95 = np.array([F.API[key][str(s)]["p95"] for s in API_SIZES])
        ax.plot(x, med, color=col, marker=mk, lw=1.8, ms=5, label=label)
        ax.fill_between(x, med, p95, color=col, alpha=0.13, lw=0)
    ax.set_xscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([size_label(int(s)) for s in x], fontsize=8)
    ax.set_xlim(x[0] * 0.6, x[-1] * 1.5)
    ax.minorticks_off()
    ax.set_xlabel("Ciphertext size")
    ax.set_ylabel("Latency (ms, median)")
    ax.set_title("API transfer time against object size")
    ax.legend(loc="upper left")
    ns = ", ".join(f"{size_label(s)}: n={F.API['upload_ms'][str(s)]['n']}" for s in API_SIZES)
    ax.text(0.02, 0.60, "upload runs per size: " + ns, transform=ax.transAxes, ha="left", va="top", fontsize=7, color=GREY)
    finish(fig, "f04_api_transfer_scaling.png")


# ------------------------------------------------------------------------------------------------------ f05
def f05():
    cells = {(c["principal"], c["operation"]): c for c in F.RBAC["cells"]}
    mat = np.zeros((len(OPERATIONS), len(PRINCIPALS)))
    for i, op in enumerate(OPERATIONS):
        for j, p in enumerate(PRINCIPALS):
            mat[i, j] = 1 if cells[(p, op)]["expected_allowed"] else 0
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.imshow(mat, cmap=ListedColormap(["#F3DDD9", "#CDEFE8"]), vmin=0, vmax=1, aspect="auto")
    for i, op in enumerate(OPERATIONS):
        for j, p in enumerate(PRINCIPALS):
            c = cells[(p, op)]
            ax.text(j, i - 0.08, str(c["status"]), ha="center", va="center", fontsize=10, fontweight="bold", color=TEAL if c["expected_allowed"] else RED)
            ax.text(j, i + 0.27, ("allow" if c["expected_allowed"] else "deny") + (" - match" if c["match"] else " - MISMATCH"), ha="center", va="center", fontsize=6.8, color=INK)
    ax.set_xticks(range(len(PRINCIPALS)))
    ax.set_xticklabels([p.capitalize() for p in PRINCIPALS], fontsize=9)
    ax.set_yticks(range(len(OPERATIONS)))
    ax.set_yticklabels([o.replace("_", " ") for o in OPERATIONS], fontsize=9)
    ax.xaxis.tick_top()
    ax.set_xticks(np.arange(-.5, len(PRINCIPALS), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(OPERATIONS), 1), minor=True)
    ax.grid(which="minor", color="white", lw=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"Expected vs observed access decisions: {F.RBAC['matched']} / {F.RBAC['total']} matched", pad=26)
    finish(fig, "f05_rbac_matrix.png")


# ------------------------------------------------------------------------------------------------------ f06
def f06():
    tam = F.TAMPER["audit_tamper"]
    rows = [(TAMPER_LABEL.get(k, k), v["detected"], v["trials"]) for k, v in tam.items()]
    rows.sort(key=lambda r: (r[1] / r[2], r[0]), reverse=True)
    bf = F.TAMPER["ciphertext_bitflip"]
    rows.append(("flip a ciphertext bit (AES-GCM tag)", bf["detected"], bf["trials"]))
    rows.append(("rewrite and re-hash later entries", 0, None))
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    y = np.arange(len(rows))
    for yy, (lab, d, t) in zip(y, rows):
        rate = (d / t) if t else 0.0
        ax.barh(yy, max(rate * 100, 0.8), color=TEAL if (t and d == t) else RED, height=0.62)
        txt = f"{d} / {t}" if t else "not detected"
        ax.text(max(rate * 100, 0.8) + 1.2 if rate < 0.9 else 99, yy, txt, va="center", ha="left" if rate < 0.9 else "right",
                fontsize=8, color=INK if rate < 0.9 else "white", fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.2)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Trials in which the tampering was detected (%)")
    ax.set_title("Tamper detection: audit-log attacks and ciphertext bit flips")
    ax.grid(axis="y", visible=False)
    note = "wrong AES key also rejected" if F.TAMPER.get("wrong_key_rejected") else ""
    ax.text(0.99, 0.02, note, transform=ax.transAxes, ha="right", fontsize=7.5, color=GREY)
    finish(fig, "f06_tamper_detection.png")


# ------------------------------------------------------------------------------------------------------ f07
def f07():
    ks = sorted(int(k) for k in F.SCALE)
    n = np.array(ks, dtype=float)
    t = np.array([F.SCALE[str(k)]["verify_ms_median"] for k in ks])
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.plot(n, t, color=NAVY, marker="o", lw=1.8, ms=6)
    offs = [(-14, 9), (16, -15)] + [(0, 9)] * (len(n) - 2)
    for xx, yy, o in zip(n, t, offs):
        ax.annotate(fmt_ms(yy), (xx, yy), xytext=o, textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.set_xlabel("Entries in the audit chain")
    ax.set_ylabel("Full-chain verification time (ms, median)")
    ax.set_title("Audit chain verification time against chain length")
    ax.set_ylim(0, max(t) * 1.18)
    ax.text(0.02, 0.95, "measured while other processes shared the CPU", transform=ax.transAxes, fontsize=7.5, color=GREY, va="top")
    finish(fig, "f07_chain_verify_scaling.png")


# ------------------------------------------------------------------------------------------------------ f08
def f08():
    C = F.CRY
    items = [("RSA-2048 key generation\n(once per account)", C["rsa_keygen"]), (f"PBKDF2-HMAC-SHA-256, {F.PBKDF2_ITER:,} it.\n(each vault unlock)", C["pbkdf2_120k"]),
             ("RSA-OAEP unwrap of a file key\n(each download)", C["rsa_unwrap"]), ("RSA-OAEP wrap of a file key\n(each upload / share)", C["rsa_wrap"])]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    y = np.arange(len(items))
    cols = [NAVY, BLUE, TEAL, TEAL]
    ax.barh(y, [d["median"] for _, d in items], color=cols, height=0.6)
    for yy, (_, d) in zip(y, items):
        ax.plot([d["p95"]], [yy], marker="|", color=INK, ms=12, mew=1.4)
        ax.text(d["p95"] * 1.25, yy, f"{fmt_ms(d['median'])} ms (p95 {fmt_ms(d['p95'])})", va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([n for n, _ in items], fontsize=8)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(0.01, 20000)
    ax.set_xlabel("Browser time (ms, median; | = p95; log scale)")
    ax.set_title("Cost of key management primitives")
    ax.grid(axis="y", visible=False)
    finish(fig, "f08_crypto_primitives.png")


# ------------------------------------------------------------------------------------------------------ f09
def f09():
    rows = [("pytest (backend)", F.PYTEST_PASSED, F.PYTEST_TOTAL), ("API end-to-end checks", F.E2E_PASSED, F.E2E_TOTAL),
            ("Browser UI walk (Playwright)", F.UI_PASSED, F.UI_TOTAL), ("evaluate.py checks", F.EVAL_PASSED, F.EVAL_TOTAL)]
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    y = np.arange(len(rows))
    ax.barh(y, [r[2] for r in rows], color="#E3E8EF", height=0.6, label="total")
    ax.barh(y, [r[1] for r in rows], color=TEAL, height=0.6, label="passed")
    for yy, (_, p, t) in zip(y, rows):
        ax.text(p + 0.4, yy, f"{p} / {t} passed", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, max(r[2] for r in rows) * 1.35)
    ax.set_xlabel("Number of tests / checks")
    ax.set_title("Automated test results")
    ax.grid(axis="y", visible=False)
    finish(fig, "f09_test_summary.png")


# ------------------------------------------------------------------------------------------------------ f10
def f10():
    cc = F.CONC["4_workers"]
    total, bad = cc["checked"], cc["failure_at"]
    fig, ax = plt.subplots(figsize=(6.8, 2.9))
    ax.barh([0], [bad - 1], left=0, color=TEAL, height=0.5, label=f"entries 1 to {bad - 1}: links verify")
    ax.barh([0], [1], left=bad - 1, color=RED, height=0.5, label=f"entry {bad}: first broken link")
    ax.barh([0], [total - bad], left=bad, color="#F0B9B2", height=0.5, label=f"entries {bad + 1} to {total}: after the fork")
    ax.set_xlim(0, total * 1.02)
    ax.axvline(bad, color=RED, lw=1.8, ymin=0.3, ymax=0.85)
    ax.set_ylim(-1.7, 1.0)
    ax.set_yticks([])
    ax.set_xlabel("Position in the audit chain (entry id)")
    ax.set_title(f"Chain verification after {cc['requests']} concurrent failed logins ({cc['seconds']} s)", fontsize=9.5)
    ax.legend(loc="lower left", ncol=1, fontsize=7.8)
    ax.grid(axis="y", visible=False)
    ax.text(total * 0.5, 0.62, f"chain valid before the burst: {F.CONC['valid_before']}    chain valid after: {cc['chain_valid_after']}", ha="center", va="center", fontsize=8.5, color=INK)
    finish(fig, "f10_audit_concurrency.png")


def main():
    wanted = set(a.lower() for a in sys.argv[1:])
    for name, fn in [("f01", f01), ("f02", f02), ("f03", f03), ("f04", f04), ("f05", f05), ("f06", f06), ("f07", f07), ("f08", f08), ("f09", f09), ("f10", f10)]:
        if wanted and name not in wanted:
            continue
        try:
            fn()
        except Exception as exc:  # report and continue so one missing metric does not hide the others
            print("FAILED", name, type(exc).__name__, exc)


if __name__ == "__main__":
    main()
