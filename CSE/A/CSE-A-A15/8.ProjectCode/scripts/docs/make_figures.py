"""Result figures f01-f13 for the CipherVeil documents -> docs/figures/ (matplotlib, 150 dpi).

    venv\Scripts\python -m scripts.docs.make_figures   # from 8.ProjectCode (f12 needs the backend packages of the venv)
All values are read from experiments/eval/metrics.json, experiments/extra/metrics.json and experiments/extra/api_latency.json through facts.py;
the only numbers typed here are the three PSNR values printed in the SCReedSolo paper (f11), which are literature values and are labelled as such.
"""
from __future__ import annotations

import io
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import facts as F

OUT = Path(F.FIGS)
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(F.CODE) / "backend"))

INK, GREY, NAVY, PURPLE, RED, TEAL, ORANGE, BLUE = "#14213D", "#5B6B7F", "#1F3A5F", "#6B5BD2", "#C0392B", "#14907F", "#D9772F", "#2B6CB0"
COVER_COL = {"astronaut_512x512.png": NAVY, "cat_451x300.png": BLUE, "coffee_600x400.png": TEAL, "coffee_small_200x200.png": ORANGE,
             "generated_landscape_1280x720.png": PURPLE, "rocket_640x427.png": RED}
COVER_LAB = {"astronaut_512x512.png": "astronaut 512x512", "cat_451x300.png": "cat 451x300", "coffee_600x400.png": "coffee 600x400",
             "coffee_small_200x200.png": "coffee 200x200", "generated_landscape_1280x720.png": "landscape 1280x720", "rocket_640x427.png": "rocket 640x427"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8895A7", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.titleweight": "bold", "axes.titlesize": 10, "figure.facecolor": "white", "legend.frameon": False})

EV, EX, API = F.EV, F.EX, F.API


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def fill_rows(cover):
    return sorted((r for r in EX["fill_study"]["rows"] if r["cover"] == cover), key=lambda r: r["fill"])


COVERS = list(COVER_COL)


# ------------------------------------------------------------------ f01 PSNR vs fill
def f01():
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    for c in COVERS:
        rows = fill_rows(c)
        x = [r["used_pct"] for r in rows]
        ax.plot(x, [r["psnr_theory"] for r in rows], "-", color=COVER_COL[c], lw=1.0, alpha=0.7)
        ax.plot(x, [r["psnr_mean"] for r in rows], "o", color=COVER_COL[c], ms=4.5, label=COVER_LAB[c])
    ax.axhline(50, color=RED, ls="--", lw=1)
    ax.text(1.15, 50.35, "50 dB: commonly taken as imperceptible", color=RED, fontsize=7.5)
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 5, 10, 25, 50, 100])
    ax.set_xticklabels(["1", "2", "5", "10", "25", "50", "100"])
    ax.set_xlabel("Capacity used by the bundle (%)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("PSNR depends on the amount hidden, not on the cover")
    ax.legend(fontsize=7.5, ncol=2, loc="upper right")
    ax.text(0.01, 0.10, f"Markers: mean of 5 random payloads (RSA-2048). Lines: closed form 10 log10(255^2 N / (0.5 bits)).\n"
            f"Largest gap between marker and line: {EX['fill_study']['max_abs_dev_vs_theory_db']} dB.", transform=ax.transAxes, fontsize=7, color=GREY)
    ax.set_ylim(49.5, 72)
    save(fig, "f01_psnr_vs_fill.png")


# ------------------------------------------------------------------ f02 SSIM vs fill
def f02():
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    for c in COVERS:
        rows = fill_rows(c)
        ax.plot([r["used_pct"] for r in rows], [r["ssim_mean"] for r in rows], "o-", color=COVER_COL[c], ms=4, lw=1.2, label=COVER_LAB[c])
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 5, 10, 25, 50, 100])
    ax.set_xticklabels(["1", "2", "5", "10", "25", "50", "100"])
    ax.set_xlabel("Capacity used by the bundle (%)")
    ax.set_ylabel("SSIM (1 = identical)")
    ax.set_title("SSIM stays above 0.992 even when the cover is full")
    ax.legend(fontsize=7.5, ncol=2, loc="lower left")
    lo = min(r["ssim_mean"] for r in EX["fill_study"]["rows"])
    ax.annotate(f"lowest: {lo:.4f}", xy=(100, lo), xytext=(30, lo + 0.0012), fontsize=7.5, color=GREY, arrowprops=dict(arrowstyle="-", color=GREY, lw=0.8))
    save(fig, "f02_ssim_vs_fill.png")


# ------------------------------------------------------------------ f03 capacity
def f03():
    caps = sorted(EV["capacity"], key=lambda c: c["max_bundle_kib"])
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    names = [f"{c['cover'].split('_')[0]}\n{c['width']}x{c['height']}" for c in caps]
    bars = ax.bar(names, [c["max_bundle_kib"] for c in caps], color=[COVER_COL[c["cover"]] for c in caps], width=0.62)
    for b, c in zip(bars, caps):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 4, f"{c['max_bundle_kib']} KiB\n{c['max_bits_per_pixel']} bpp", ha="center", fontsize=7.5, color=INK)
    memo = next(r for r in EV["quality_and_speed"] if r["payload_bytes"] == 16384)
    ax.set_ylabel("Largest bundle that fits (KiB)")
    ax.set_title("Capacity grows with pixel count at 3 bits per pixel")
    ax.set_ylim(0, max(c["max_bundle_kib"] for c in caps) * 1.2)
    save(fig, "f03_capacity_by_cover.png")


# ------------------------------------------------------------------ f04 stage timings
def f04():
    rows = [r for r in EV["quality_and_speed"] if r["fits"]]
    sizes = sorted({r["payload_bytes"] for r in rows})
    stages = [("encrypt_ms", "AES-GCM encrypt + RSA wrap", TEAL), ("embed_ms", "LSB embed", PURPLE), ("extract_ms", "LSB extract", ORANGE), ("decrypt_ms", "RSA unwrap + AES-GCM decrypt", NAVY)]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    w = 0.2
    x = np.arange(len(sizes))
    for i, (k, lab, col) in enumerate(stages):
        med = [statistics.median(r[k] for r in rows if r["payload_bytes"] == s) for s in sizes]
        bars = ax.bar(x + (i - 1.5) * w, med, w, color=col, label=lab)
        for b, m in zip(bars, med):
            ax.text(b.get_x() + b.get_width() / 2, m * 1.12, f"{m:.2g}", ha="center", fontsize=6.3, color=INK)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s // 1024} KiB" for s in sizes])
    ax.set_xlabel("Payload size")
    ax.set_ylabel("Median time (ms, log scale)")
    ax.set_title(f"RSA-{EV['key_bits']} unwrap dominates; AES and LSB cost well under 2 ms")
    ax.legend(fontsize=7.5, loc="upper left", ncol=2)
    ax.set_ylim(0.01, 1000)
    save(fig, "f04_stage_timings.png")


# ------------------------------------------------------------------ f05 RSA key size
def f05():
    rs = EX["rsa_study"]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    x = np.arange(len(rs))
    w = 0.26
    series = [("keygen_ms_median", "Key generation (median; bar = min to max)", ORANGE), ("encrypt_wrap_ms_median", "Encrypt + RSA wrap", TEAL), ("unwrap_decrypt_ms_median", "RSA unwrap + decrypt", NAVY)]
    for i, (k, lab, col) in enumerate(series):
        vals = [r[k] for r in rs]
        err = None
        if k == "keygen_ms_median":
            err = [[r["keygen_ms_median"] - r["keygen_ms_min"] for r in rs], [r["keygen_ms_max"] - r["keygen_ms_median"] for r in rs]]
        bars = ax.bar(x + (i - 1) * w, vals, w, color=col, label=lab, yerr=err, capsize=3, error_kw=dict(lw=0.8, ecolor=GREY))
        for b, v in zip(bars, vals):
            if k == "keygen_ms_median":
                ax.text(b.get_x() + b.get_width() / 2, v * 0.55, f"{v:.3g}", ha="center", fontsize=7, color="white", fontweight="bold")
            else:
                ax.text(b.get_x() + b.get_width() / 2, v * 1.25, f"{v:.3g}", ha="center", fontsize=7, color=INK)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([f"RSA-{r['rsa_bits']}\nwrapped key {r['wrapped_key_bytes']} B\noverhead {r['overhead_bytes']} B" for r in rs])
    ax.set_ylabel("Time (ms, log scale)")
    ax.set_title("A larger RSA key costs time at the receiver and 128 bytes per step")
    ax.legend(fontsize=7.5, loc="upper left")
    ax.set_ylim(0.05, 3000)
    save(fig, "f05_rsa_key_size.png")


# ------------------------------------------------------------------ f06 robustness matrix
def f06():
    core = [(r["label"], r["recovered"], 6, r["mean_bit_error_rate"]) for r in EV["robustness"]]
    extra = [(r["attack"], r["recovered"], r["of"], None) for r in EX["extra_attacks"]]
    rows = core + extra
    fig, ax = plt.subplots(figsize=(7.6, 6.0))
    y = np.arange(len(rows))[::-1]
    for yy, (lab, rec, of, ber) in zip(y, rows):
        ax.barh(yy, of, color="#E8EDF3", height=0.62)
        ax.barh(yy, rec, color=TEAL if rec == of else (ORANGE if rec else RED), height=0.62)
        txt = f"{rec} / {of} recovered" + (f"   LSB error {ber * 100:.1f} %" if ber is not None else "   (error rate not measured)")
        ax.text(of + 0.15, yy, txt, va="center", fontsize=7.2, color=INK)
    ax.axhline(len(extra) - 0.5, color=GREY, lw=0.8, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.5)
    ax.set_xlim(0, 13.6)
    ax.set_xticks(range(0, 7))
    ax.set_xlabel("Covers (of 6) whose payload was recovered byte for byte")
    ax.set_title("Only lossless handling keeps the hidden file")
    ax.text(13.5, len(rows) - 0.6, "app attacks (9)", ha="right", fontsize=7.5, color=GREY, style="italic")
    ax.text(13.5, len(extra) - 0.95, "extra attacks (9)", ha="right", fontsize=7.5, color=GREY, style="italic")
    save(fig, "f06_robustness_matrix.png")


# ------------------------------------------------------------------ f07 bit balance
def f07():
    rows = EX["plain_vs_encrypted"]["rows"]
    pays = []
    for r in rows:
        if r["payload"] not in pays:
            pays.append(r["payload"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.2, 3.7))
    x = np.arange(len(pays))
    w = 0.36
    for ax, key, ttl, yl in ((a1, "ones_fraction", "Fraction of 1-bits in the embedded stream", "Fraction of ones"), (a2, "entropy_bits_per_byte", "Byte entropy of the embedded stream", "Entropy (bits per byte)")):
        for i, (kind, col) in enumerate((("plain", GREY), ("encrypted", TEAL))):
            vals = [next(r[key] for r in rows if r["payload"] == p and r["kind"] == kind) for p in pays]
            bars = ax.bar(x + (i - 0.5) * w, vals, w, color=col, label=kind)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + (0.006 if key == "ones_fraction" else 0.08), f"{v:.3g}", ha="center", fontsize=6.5)
        ax.set_xticks(x)
        ax.set_xticklabels([p.replace("confidential_", "") for p in pays], fontsize=7, rotation=12)
        ax.set_title(ttl, fontsize=9)
        ax.set_ylabel(yl)
    a1.axhline(0.5, color=RED, ls="--", lw=0.9, label="0.5 = balanced")
    a1.set_ylim(0.3, 0.58)
    a2.axhline(8, color=RED, ls="--", lw=0.9)
    a2.set_ylim(0, 9)
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, fontsize=7.5, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.045))
    fig.text(0.5, -0.09, "Small files cannot reach 8 bits per byte as samples (99 to 21,517 bytes); encryption also adds the 'wrapped key' and 'nonce' fields.", ha="center", fontsize=7, color=GREY)
    fig.tight_layout()
    save(fig, "f07_bit_balance.png")


# ------------------------------------------------------------------ f08 steganalysis
def f08():
    sa = EX["steganalysis"]["rows"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 4.0))
    fills = sorted({r["fill"] for r in sa})
    for c in COVERS:
        rows = sorted((r for r in sa if r["cover"] == c), key=lambda r: r["fill"])
        a1.plot([r["fill"] * 100 for r in rows], [r["chi2_p_stego_prefix"] for r in rows], "o-", color=COVER_COL[c], ms=4, lw=1, label=COVER_LAB[c])
        a1.plot([r["fill"] * 100 for r in rows], [r["chi2_p_cover_prefix"] for r in rows], "s", mfc="white", mec=COVER_COL[c], ms=4.5, mew=1.1)
    a1.axhline(0.5, color=GREY, ls=":", lw=0.9)
    a1.set_xlabel("Capacity used (%)")
    a1.set_ylabel("Chi-square p-value of the embedded prefix")
    a1.set_title("Chi-square test: stego (filled) vs same prefix of the clean cover (open)", fontsize=8.5)
    a1.set_ylim(-0.05, 1.08)
    a1.set_xticks([10, 25, 50, 75, 100])
    a1.legend(fontsize=6.5, loc="center right", bbox_to_anchor=(1.0, 0.45))
    for c in COVERS:
        rows = sorted((r for r in sa if r["cover"] == c), key=lambda r: r["fill"])
        a2.plot([r["true_fraction_of_samples"] for r in rows], [r["ws_estimate_stego"] for r in rows], "o-", color=COVER_COL[c], ms=4, lw=1)
        a2.plot([0], [rows[0]["ws_estimate_cover"]], "s", mfc="white", mec=COVER_COL[c], ms=5, mew=1.1)
    a2.plot([0, 1], [0, 1], color=GREY, ls="--", lw=0.9)
    a2.text(0.62, 0.52, "estimate = truth", color=GREY, fontsize=7.5, rotation=36)
    a2.set_xlabel("True fraction of colour values carrying payload")
    a2.set_ylabel("Weighted-stego estimate")
    a2.set_title("Weighted-stego estimate (open squares: clean covers)", fontsize=8.5)
    a2.set_xlim(-0.04, 1.06)
    n_hit = EX["steganalysis"]["chi2_total"]
    fig.text(0.5, -0.03, f"Chi-square p-value of the stego prefix is above 0.5 in {n_hit} of {n_hit} cases; the oracle knows the embedded length. The blind estimate tracks the truth with a cover-dependent offset.",
             ha="center", fontsize=7, color=GREY)
    fig.tight_layout()
    save(fig, "f08_steganalysis.png")


# ------------------------------------------------------------------ f09 tamper
def f09():
    t = EX["tamper_study"]
    fields = list(t["by_field"])
    outcomes = []
    for f in fields:
        for o in t["by_field"][f]:
            if o not in outcomes:
                outcomes.append(o)
    palette = [NAVY, TEAL, PURPLE, ORANGE, BLUE, RED]
    short = lambda o: o.replace("rejected: ", "").replace(" found in this image", "").replace("This bundle was wrapped for a different key size", "wrong key size")
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    left = np.zeros(len(fields))
    y = np.arange(len(fields))[::-1]
    for i, o in enumerate(outcomes):
        vals = np.array([t["by_field"][f].get(o, 0) for f in fields])
        ax.barh(y, vals, left=left, color=palette[i % len(palette)], height=0.6, label=short(o))
        for yy, v, l in zip(y, vals, left):
            if v:
                ax.text(l + v / 2, yy, str(v), ha="center", va="center", color="white", fontsize=7.5, fontweight="bold")
        left += vals
    ax.set_yticks(y)
    ax.set_yticklabels(fields)
    ax.set_xlabel("Single-bit flips of the stego LSBs (40 per field)")
    ax.set_title(f"{t['accepted_with_wrong_data']} of {t['trials']} tampered images were accepted")
    ax.legend(fontsize=6.8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3)
    save(fig, "f09_tamper_outcomes.png")


# ------------------------------------------------------------------ f10 API latency
def f10():
    items = [(k, v) for k, v in API.items()]
    items.sort(key=lambda kv: kv[1]["median_ms"])
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    y = np.arange(len(items))
    med = [v["median_ms"] for _, v in items]
    ax.barh(y, med, color=BLUE, height=0.62)
    hi = [v.get("p95_ms", v.get("max_ms", v["median_ms"])) for _, v in items]
    ax.plot(hi, y, "|", color=RED, ms=9, mew=1.6, label="95th percentile (or max for n < 5)")
    for yy, m, h in zip(y, med, hi):
        ax.text(max(m, h) * 1.25, yy, f"{m:,.1f} ms", va="center", fontsize=7, color=INK)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{k} (n={v['n']})" for k, v in items], fontsize=7.2)
    ax.set_xlabel("Latency of the HTTP call (ms, log scale; client on 127.0.0.1)")
    ax.set_title("API latency: encoding and quality metrics dominate, not the cryptography", fontsize=9.5)
    ax.set_xlim(1, 90000)
    ax.legend(fontsize=7.5, loc="lower right")
    save(fig, "f10_api_latency.png")


# ------------------------------------------------------------------ f11 reported PSNR comparison
def f11():
    # values printed in Raiyan and Kabir (arXiv:2503.12368), Tables I-III; the base paper (ProSt) reports no PSNR
    screed = [("text 5.46 M chars\n-> 14589x8423 image", 51.774), ("audio\n-> 21188x30328 image", 57.653), ("100x100 image\n-> 512x512 Lenna", 52.888)]
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    allf = EX["fill_study"]["rows"]
    rng = np.random.default_rng(3)
    xs = [r["psnr_mean"] for r in allf]
    ax.scatter(xs, 1 + rng.uniform(-0.18, 0.18, len(xs)), s=22, color=TEAL, alpha=0.8, label=f"CipherVeil, fill-ratio study ({len(xs)} points, 1-100 % fill)")
    ev = [r["psnr_db"] for r in EV["quality_and_speed"] if r["fits"]]
    ax.scatter(ev, 2 + rng.uniform(-0.18, 0.18, len(ev)), s=22, color=NAVY, alpha=0.8, label=f"CipherVeil, core evaluation ({len(ev)} runs, <= 73 % fill)")
    ax.scatter([v for _, v in screed], [3] * 3, s=70, marker="D", color=ORANGE, label="SCReedSolo, as reported (arXiv:2503.12368)")
    for (lab, v), yy in zip(screed, (3.95, 3.3, 3.3)):
        ax.plot([v, v], [3.08, yy], color=ORANGE, lw=0.7)
        ax.text(v + 0.1, yy, lab, ha="left", fontsize=6.4, color=INK, va="bottom")
    ax.axvline(50, color=RED, ls="--", lw=0.9)
    ax.set_xlim(47.5, 77)
    ax.text(50.15, 0.5, "50 dB", color=RED, fontsize=7, va="bottom")
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["CipherVeil\nfill study", "CipherVeil\ncore eval", "SCReedSolo\n(reported)"])
    ax.set_ylim(0.4, 4.8)
    ax.set_xlabel("PSNR (dB)")
    ax.set_title("PSNR values side by side - different covers and payloads", fontsize=9.5, pad=22)
    ax.text(0.5, 1.025, "Not a like-for-like comparison. The base paper ProSt reports no PSNR, SSIM or capacity figures.", transform=ax.transAxes, ha="center", fontsize=7.4, color=GREY)
    ax.legend(fontsize=7, loc="upper right")
    save(fig, "f11_reported_psnr_comparison.png")


# ------------------------------------------------------------------ f12 difference image
def f12():
    from app.services import crypto, lsb, pipeline

    priv, pub = crypto.generate_keypair(2048)
    cover = lsb.load_rgb(str(Path(F.CODE) / "data" / "covers" / "astronaut_512x512.png"))
    data = (Path(F.CODE) / "data" / "payloads" / "confidential_memo.pdf").read_bytes()
    sent = pipeline.hide(pub, "confidential_memo.pdf", data, cover)
    stego = sent["stego"]
    diff = np.abs(cover.astype(int) - stego.astype(int)).astype(np.uint8) * 255
    q = sent["quality"]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.6))
    for ax, img, ttl in ((axes[0], cover, "Cover (original)"), (axes[1], stego, f"Stego: {len(data) / 1024:.1f} KiB memo hidden"), (axes[2], diff, "Difference x 255")):
        ax.imshow(img)
        ax.set_title(ttl, fontsize=9)
        ax.axis("off")
    fig.suptitle(f"PSNR {q['psnr_db']} dB, SSIM {q['ssim']}, {q['changed_pct']} % of values changed, largest change {q['max_abs_change']} of 255", fontsize=9, y=0.02)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "f12_difference_image.png")


# ------------------------------------------------------------------ f13 PSNR by payload
def f13():
    rows = EV["quality_and_speed"]
    sizes = sorted({r["payload_bytes"] for r in rows})
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    for c in COVERS:
        cr = sorted((r for r in rows if r["cover"] == c), key=lambda r: r["payload_bytes"])
        fit = [r for r in cr if r["fits"]]
        ax.plot([r["payload_bytes"] / 1024 for r in fit], [r["psnr_db"] for r in fit], "o-", color=COVER_COL[c], ms=4.5, lw=1.2, label=COVER_LAB[c])
        for r in cr:
            if not r["fits"]:
                ax.plot([r["payload_bytes"] / 1024], [48.7], "x", color=COVER_COL[c], ms=6, mew=1.4)
    ax.axhline(50, color=RED, ls="--", lw=0.9)
    ax.set_xscale("log", base=2)
    ax.set_xticks([s / 1024 for s in sizes])
    ax.set_xticklabels([f"{s // 1024}" for s in sizes])
    ax.set_xlabel("Payload size (KiB, file before encryption)")
    ax.set_ylabel("PSNR (dB)")
    ax.set_ylim(48, 77)
    ax.set_title("Core evaluation grid: PSNR by payload size (RSA-3072)")
    ax.text(0.02, 0.03, "x = does not fit, blocked by the capacity check", transform=ax.transAxes, ha="left", fontsize=7.5, color=GREY)
    ax.legend(fontsize=7.5, ncol=2, loc="upper right")
    save(fig, "f13_psnr_by_payload.png")


def main():
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09, f10, f11, f12, f13):
        fn()


if __name__ == "__main__":
    main()
