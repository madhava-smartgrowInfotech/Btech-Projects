"""Result charts (PNG, 150 dpi) from docs/evaluation/*.json into docs/charts/.   python scripts/make_result_charts.py"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_common import CH_LABEL, CHALLENGES, CHARTS, FV, GF, LT, LV, PB  # noqa: E402

CHARTS.mkdir(parents=True, exist_ok=True)
IND, COR, GRN, AMB, SKY, GRY = "#3f3fbf", "#e0533a", "#2f9e6d", "#e0a030", "#4a90d9", "#8a93a8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(CHARTS / name, dpi=150, facecolor="white")
    plt.close(fig)


def similarity_hist():
    g, i = np.array(FV["genuine_sims"]), np.array(FV["impostor_sims"])
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    bins = np.linspace(-0.2, 1.0, 61)
    ax.hist(i, bins=bins, color=COR, alpha=0.75, label=f"different people (n = {len(i):,})")
    ax.hist(g, bins=bins, color=IND, alpha=0.75, label=f"same person (n = {len(g):,})")
    ax.axvline(0.40, color="black", ls="--", lw=1.2, label="identity threshold 0.40")
    ax.axvline(0.45, color=GRN, ls="--", lw=1.2, label="duplicate / consistency threshold 0.45")
    ax.set_xlabel("cosine similarity of ArcFace embeddings")
    ax.set_ylabel("image pairs")
    ax.set_title("LFW verification pairs: similarity of same-person and different-person pairs", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    save(fig, "similarity_hist.png")


def threshold_sweep():
    sw = [r for r in FV["sweep"] if 0.0 <= r["threshold"] <= 0.8]
    t = [r["threshold"] for r in sw]
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.plot(t, [100 * r["frr"] for r in sw], color=COR, lw=2, label="false reject rate (same person rejected)")
    ax.plot(t, [100 * r["far"] for r in sw], color=IND, lw=2, label="false accept rate (different person accepted)")
    ax.plot(t, [100 * (1 - r["accuracy"]) for r in sw], color=GRY, lw=1.3, ls=":", label="pair error rate")
    for th, col, lab in ((0.40, "black", "0.40"), (0.45, GRN, "0.45")):
        ax.axvline(th, color=col, ls="--", lw=1.1)
        ax.text(th, 36, lab, fontsize=8, ha="center", color=col, bbox=dict(fc="white", ec="none", pad=0.5))
    ax.set_ylim(0, 40)
    ax.set_xlabel("similarity threshold")
    ax.set_ylabel("rate (%)")
    ax.set_title("Error rates against the similarity threshold (LFW, 4,307 scored pairs)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=1)
    save(fig, "threshold_sweep.png")


def attacks():
    x = np.arange(8)
    w = 0.26
    static = [100 * LV["C_static_replay"][c]["rate"] for c in CHALLENGES]
    bank_l = [100 * PB["by_challenge"][c]["liveness_only_rate"] for c in CHALLENGES]
    bank_f = [100 * PB["by_challenge"][c]["full_chain_rate"] for c in CHALLENGES]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    ax.bar(x - w, static, w, color=GRN, label="one stolen photo (static replay)")
    ax.bar(x, bank_l, w, color=AMB, label="photo bank, liveness check only")
    ax.bar(x + w, bank_f, w, color=COR, label="photo bank, full chain (liveness + face)")
    for xi, v in zip(x - w, static):
        ax.text(xi, v + 1.5, f"{v:.0f}", ha="center", fontsize=7)
    for xi, v in zip(x + w, bank_f):
        ax.text(xi, v + 1.5, f"{v:.0f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([CH_LABEL[c] for c in CHALLENGES], rotation=20, fontsize=8)
    ax.set_ylabel("attack success (%)")
    ax.set_ylim(0, 112)
    ax.set_title("Spoofing attempts that pass each challenge (LFW stills, no live person)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    save(fig, "attack_success.png")


def rotation():
    r = LV["D_rotation_sweep"]
    a = r["angles"]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ax.plot(a, [100 * v for v in r["TILT_LEFT"]], "-o", color=IND, ms=4, label="Tilt left passes")
    ax.plot(a, [100 * v for v in r["TILT_RIGHT"]], "-s", color=COR, ms=4, label="Tilt right passes")
    ax.axvspan(-12, 12, color=GRN, alpha=0.12)
    ax.text(0, 50, "threshold 12 deg:\nno pass inside", ha="center", fontsize=8)
    ax.set_xlabel("rotation applied to a single still photo (degrees)")
    ax.set_ylabel("pass rate (%)")
    ax.set_title("A rotated photo defeats the tilt challenges (300 photos per angle)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8, loc="center left")
    save(fig, "rotation_sweep.png")


def latency():
    B = LT["B_stage_ms"]
    names = [("MediaPipe landmarks (1 frame)", B["mediapipe_landmarks"]), ("InsightFace embedding (1 frame)", B["insightface_embed"]),
             ("AI work per check-in (2 frames)", B["pipeline_ai_total_two_frames"]), ("Face decision, 30 session faces", B["verify_faces"]),
             ("JPEG decode and resize", B["decode_1280px_jpeg"])]
    C = LT["C_http_ms"]
    http = [("Login (PBKDF2)", C["login"]), ("Eligibility check", C["start_eligibility"]), ("Location check", C["location"]),
            ("Liveness (2 uploads)", C["liveness_two_photos"]), ("Face match + record", C["face_match_and_record"]), ("Check-in total (after login)", C["checkin_total_after_login"])]
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 3.5))
    for ax, items, title in ((axs[0], names, "Pipeline stages (ms)"), (axs[1], http, "HTTP steps of one check-in (ms)")):
        y = np.arange(len(items))[::-1]
        ax.barh(y + 0.18, [v["p50"] for _, v in items], 0.34, color=IND, label="median")
        ax.barh(y - 0.18, [v["p95"] for _, v in items], 0.34, color=AMB, label="95th percentile")
        for yi, (_, v) in zip(y, items):
            ax.text(v["p95"] * 1.02 + 2, yi - 0.18, f"{v['p95']:.0f}" if v["p95"] >= 10 else f"{v['p95']:.2f}", va="center", fontsize=7)
            ax.text(v["p50"] * 1.02 + 2, yi + 0.18, f"{v['p50']:.0f}" if v["p50"] >= 10 else f"{v['p50']:.2f}", va="center", fontsize=7)
        ax.set_yticks(y)
        ax.set_yticklabels([n for n, _ in items], fontsize=7.5)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlim(0, max(v["p95"] for _, v in items) * 1.18)
    axs[0].legend(frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "latency.png")


def geofence():
    c = GF["C_gps_noise_simulation"]
    d = c["distances_m"]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    cols = [GRN, SKY, IND, AMB, COR]
    for s, col in zip(c["sigmas_m"], cols):
        ax.plot(d, [100 * v for v in c["p_accept"][str(s)]], color=col, lw=1.8, label=f"GPS error sigma = {s} m")
    ax.axvline(75, color="black", ls="--", lw=1.1)
    ax.text(76.5, 92, "limit 75 m\n(60 + 15)", fontsize=8)
    ax.set_xlabel("true distance of the student from the fence centre (m)")
    ax.set_ylabel("probability the check-in is accepted (%)")
    ax.set_title("Simulated effect of GPS error on the geo-fence (20,000 trials per point)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7.5)
    save(fig, "geofence_noise.png")


def duplicate_scan():
    D = LT["D_duplicate_scan_ms"]
    n = [int(k) for k in D]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.loglog(n, [D[str(k)]["p50"] for k in n], "-o", color=IND, label="median")
    ax.loglog(n, [D[str(k)]["p95"] for k in n], "-s", color=AMB, label="95th percentile")
    ax.set_xlabel("faces already recorded in the session")
    ax.set_ylabel("time for the face decision (ms)")
    ax.set_title("Duplicate-face scan is linear in session size", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8)
    save(fig, "duplicate_scan.png")


def neutral():
    r = LV["A_neutral"]["rejected_by"]
    labels = ["accepted", "not frontal", "several faces", "mouth open", "no face"]
    vals = [LV["A_neutral"]["accepted"], r["not_frontal"], r["multiple_faces"], r["mouth_open"], r["no_face"]]
    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    ax.bar(labels, vals, color=[GRN, AMB, COR, SKY, GRY])
    for i, v in enumerate(vals):
        ax.text(i, v + 8, str(v), ha="center", fontsize=8)
    ax.set_ylabel("LFW photos (of 1,000)")
    ax.set_title("Outcome of the neutral-frame check on 1,000 LFW photos", fontsize=9.5)
    save(fig, "neutral_check.png")


if __name__ == "__main__":
    for f in (similarity_hist, threshold_sweep, attacks, rotation, latency, geofence, duplicate_scan, neutral):
        f()
    print("charts done")
