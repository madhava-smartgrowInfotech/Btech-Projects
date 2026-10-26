"""Result charts for the documents (docs/figures/*.png, 150 dpi), drawn from the measured JSON only.

    python scripts/docs_build/make_figures.py
"""
import glob
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
M = json.load(open(ROOT / "experiments" / "voting" / "metrics.json", encoding="utf-8"))
B = json.load(open(ROOT / "experiments" / "voting" / "benchmark_1000_voters.json", encoding="utf-8"))

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8795A8", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", name)


def labels(ax, bars, fmt="{:.1f}", dy=0.0):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, fmt.format(b.get_height()), ha="center", va="bottom", fontsize=8)


# f01 - benchmark of 1000 voters
def f01():
    modes = ["Synchronous"] + [f"Batch {k}" for k in B["async_batches"]]
    runs = [B["sync"]] + list(B["async_batches"].values())
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.5))
    thr = [r["throughput"] for r in runs]
    bars = axs[0].bar(modes, thr, color=[NAVY, BLUE, TEAL, PURPLE])
    labels(axs[0], bars, "{:.1f}")
    axs[0].set_ylabel("votes per second")
    axs[0].set_title("Throughput, 1000 voters (shared PC)", fontsize=9.5)
    x = range(len(modes))
    w = 0.26
    for i, (k, c) in enumerate((("mean_ms", BLUE), ("median_ms", TEAL), ("p95_ms", ORANGE))):
        axs[1].bar([j + (i - 1) * w for j in x], [r[k] for r in runs], w, label=k.replace("_ms", ""), color=c)
    axs[1].set_xticks(list(x))
    axs[1].set_xticklabels(modes)
    axs[1].set_ylabel("milliseconds per vote")
    axs[1].set_title("Latency per vote", fontsize=9.5)
    axs[1].legend(frameon=False, fontsize=8)
    save(fig, "f01_benchmark_1000.png")


# f02 - earlier idle runs vs the loaded run
def f02():
    rows = []
    for f in sorted(glob.glob(str(ROOT / "benchmark_results" / "benchmark_*.json"))):
        d = json.load(open(f))
        rows.append((f"{d['voters_count']} voters\n(idle PC)", d["sync"]["throughput"]))
    rows.append(("1000 voters\n(shared PC)", B["sync"]["throughput"]))
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    colors = [TEAL] * (len(rows) - 1) + [ORANGE]
    bars = ax.bar([f"{i + 1}. {r[0]}" for i, r in enumerate(rows)], [r[1] for r in rows], color=colors)
    labels(ax, bars)
    ax.set_ylabel("synchronous votes per second")
    ax.set_title("Same code, different machine load: throughput of the synchronous benchmark", fontsize=9.5)
    plt.setp(ax.get_xticklabels(), fontsize=7.5)
    save(fig, "f02_benchmark_runs.png")


# f03 - validate_chain vs height
def f03():
    d = M["growth"]["validate_chain_by_height"]
    h = [v["height_blocks"] for v in d.values()]
    t = [v["median_ms"] for v in d.values()]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(h, t, "o-", color=NAVY, lw=2)
    for a, b in zip(h, t):
        ax.annotate(f"{b:.0f} ms", (a, b), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_xlabel("blocks in the chain")
    ax.set_ylabel("validate_chain() median, ms")
    ax.set_title("Integrity check time grows linearly with chain length", fontsize=9.5)
    ax.set_ylim(0, max(t) * 1.2)
    save(fig, "f03_validate_chain_growth.png")


# f04 - stage breakdown of one vote
def f04():
    st = M["vote_stage_breakdown_ms_mean"]
    names = ["Authorise\n(token)", "Encrypt + hash\n+ sign", "propose_block\n(3 validators)", "Persist\n(ballot, commit)"]
    vals = [st["authorise"], st["encrypt_sign_hash"], st["propose_block"], st["persist"]]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    bars = ax.bar(names, vals, color=[BLUE, TEAL, PURPLE, ORANGE])
    labels(ax, bars, "{:.2f}")
    ax.set_ylabel("mean milliseconds (n = 60 votes)")
    ax.set_title("Where one vote spends its time (in-process)", fontsize=9.5)
    save(fig, "f04_vote_stage_breakdown.png")


# f05 - micro timings, log scale
def f05():
    mt = M["micro_timings"]
    order = ["verhoeff_validate", "aadhaar_salted_sha256", "sha256_tx_payload", "aes256gcm_decrypt", "aes256gcm_encrypt", "ed25519_sign", "ed25519_verify", "argon2id_hash", "argon2id_verify"]
    names = ["Verhoeff check", "Aadhaar salted\nSHA-256", "SHA-256 of tx", "AES-GCM\ndecrypt", "AES-GCM\nencrypt", "Ed25519\nsign", "Ed25519\nverify", "Argon2id\nhash", "Argon2id\nverify"]
    vals = [mt[k]["mean_ms"] for k in order]
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    bars = ax.bar(names, vals, color=[TEAL] * 7 + [ORANGE] * 2)
    ax.set_yscale("log")
    ax.set_ylabel("mean milliseconds (log scale)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:.3g}", ha="center", fontsize=7.5)
    ax.set_title("Cost of each primitive: password hashing dwarfs the cryptography of the vote itself", fontsize=9.5)
    plt.setp(ax.get_xticklabels(), fontsize=7.5)
    save(fig, "f05_micro_timings.png")


# f06 - tamper detection matrix
def f06():
    cases = M["tamper_study"]["cases"]
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.set_xlim(0, 2)
    ax.set_ylim(0, len(cases))
    ax.invert_yaxis()
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(["Product check\nvalidate_chain()", "Stricter audit\n(signatures + cross-check)"], fontsize=9)
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(cases))])
    ax.set_yticklabels([c["case"] for c in cases], fontsize=8)
    ax.tick_params(length=0)
    for i, c in enumerate(cases):
        for j, key in enumerate(("validate_chain_detects", "strict_audit_detects")):
            ok = c[key]
            ax.add_patch(plt.Rectangle((j + 0.04, i + 0.08), 0.92, 0.84, color=TEAL if ok else RED, alpha=0.9))
            ax.text(j + 0.5, i + 0.5, "detected" if ok else "MISSED", ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
    n = sum(c["validate_chain_detects"] for c in cases)
    ax.set_title(f"Tamper study: {n} of {len(cases)} cases caught by the product check", fontsize=9.5, pad=34)
    save(fig, "f06_tamper_matrix.png")


# f07 - HTTP latency per step
def f07():
    lat = M["http"]["latency"]
    steps = ["login", "verify", "cast", "end_to_end"]
    names = ["Login\n(Argon2id)", "Aadhaar\nverify", "Cast\n(block commit)", "Whole voter\njourney"]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    w = 0.26
    for i, (k, c) in enumerate((("mean_ms", BLUE), ("median_ms", TEAL), ("p95_ms", ORANGE))):
        bars = ax.bar([j + (i - 1) * w for j in range(4)], [lat[s][k] for s in steps], w, color=c, label=k.replace("_ms", ""))
        labels(ax, bars, "{:.0f}", 0)
    ax.set_xticks(range(4))
    ax.set_xticklabels(names)
    ax.set_ylabel("milliseconds over HTTP (127.0.0.1)")
    ax.set_title("End-to-end latency through uvicorn, 27 voters", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8)
    save(fig, "f07_http_latency.png")


# f08 - comparison with the base paper (approximate, read from its Figures 6 and 9)
def f08():
    lat = M["http"]["latency"]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    names = ["Base paper\nregistration tx\n(Geth, approx.)", "Base paper\nvoting tx\n(Geth, approx.)", "AegisBallot\ncast, in-process\n(1000-voter run)", "AegisBallot\ncast over HTTP\n(27 voters)"]
    vals = [2000, 3000, B["sync"]["mean_ms"], lat["cast"]["mean_ms"]]
    bars = ax.bar(names, vals, color=[GREY, GREY, TEAL, BLUE])
    ax.set_yscale("log")
    ax.set_ylim(10, 6000)
    ax.set_ylabel("milliseconds per transaction (log scale)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:,.0f}", ha="center", fontsize=8)
    ax.set_title("Per-transaction time: order of magnitude only - different chain, hardware and definition", fontsize=9.2)
    plt.setp(ax.get_xticklabels(), fontsize=7.5)
    save(fig, "f08_base_paper_comparison.png")


# f09 - growth of per-vote latency along the chain (first 100 vs last 100)
def f09():
    g = M["growth"]
    names = ["first 100 votes", "all 300 votes", "last 100 votes"]
    keys = ["per_vote_first_100", "per_vote_all", "per_vote_last_100"]
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    w = 0.3
    for i, (k, c) in enumerate((("mean_ms", BLUE), ("median_ms", TEAL), ("p95_ms", ORANGE))):
        bars = ax.bar([j + (i - 1) * w for j in range(3)], [g[x][k] for x in keys], w, color=c, label=k.replace("_ms", ""))
        labels(ax, bars, "{:.0f}")
    ax.set_xticks(range(3))
    ax.set_xticklabels(names)
    ax.set_ylabel("milliseconds per vote")
    ax.set_title("Per-vote cost while the chain grows (in-process)", fontsize=9.5)
    ax.set_ylim(0, 48)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    save(fig, "f09_vote_cost_growth.png")


if __name__ == "__main__":
    for fn in (f01, f02, f03, f04, f05, f06, f07, f08, f09):
        fn()
