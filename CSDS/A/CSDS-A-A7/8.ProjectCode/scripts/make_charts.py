"""Result charts (PNG, 150 dpi) from experiments/study/*.json and the product data into docs/charts/.

    venv\\Scripts\\python scripts/make_charts.py
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from doc_common import CHARTS, ROOT, STUDY  # noqa: E402

CHARTS.mkdir(parents=True, exist_ok=True)
GREEN, AMBER, RED, BLUE, GREY, PURPLE = "#2e8b57", "#e0a030", "#c8453c", "#2f6fb0", "#9aa5ba", "#7a4fc9"
TIER_COL = {"low": GREEN, "medium": AMBER, "high": RED}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 10, "axes.titleweight": "bold"})


def save(fig, name):
    fig.savefig(CHARTS / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


M = json.loads((STUDY / "metrics.json").read_text(encoding="utf-8"))
A = json.loads((STUDY / "api_metrics.json").read_text(encoding="utf-8"))
S = json.loads((STUDY / "safephrase.json").read_text(encoding="utf-8"))
risk = pd.read_csv(ROOT / "data" / "district_risk.csv")

# 01 k sweep -------------------------------------------------------------------------------------------------
ks = M["k_sweep"]
fig, ax = plt.subplots(figsize=(5.2, 3.3))
x = [r["k"] for r in ks]
ax.plot(x, [r["silhouette"] for r in ks], "o-", color=BLUE, label="Silhouette (higher is better)")
ax.set_xlabel("Number of clusters k")
ax.set_ylabel("Silhouette", color=BLUE)
ax2 = ax.twinx()
ax2.spines["right"].set_visible(True)
ax2.plot(x, [r["davies_bouldin"] for r in ks], "s--", color=RED, label="Davies-Bouldin (lower is better)")
ax2.set_ylabel("Davies-Bouldin", color=RED)
ax.axvline(3, color=GREY, ls=":")
ax.text(3.05, ax.get_ylim()[0] + 0.005, "k = 3 (shipped)", fontsize=8, color="#555")
ax.set_title("Cluster-quality indices against k (467 districts, one feature)")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=7.5, loc="upper right")
save(fig, "01_k_sweep.png")

# 02 distribution of crime rate with tiers --------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.6, 3.3))
bins = np.linspace(0, 1200, 41)
bottom = np.zeros(len(bins) - 1)
for t in ("low", "medium", "high"):
    h, _ = np.histogram(risk[risk.risk_tier == t].crime_rate, bins=bins)
    ax.bar(bins[:-1], h, width=np.diff(bins), align="edge", color=TIER_COL[t], label=f"{t} ({(risk.risk_tier == t).sum()} districts)", bottom=bottom, edgecolor="white", linewidth=0.4)
    bottom += h
e = M["one_feature_equivalence"]
for thr in (e["threshold_low_medium"], e["threshold_medium_high"]):
    ax.axvline(thr, color="#333", ls="--", lw=1)
    ax.text(thr + 8, ax.get_ylim()[1] * 0.92, f"{thr:.1f}", fontsize=8)
ax.set_xlabel("Average crimes against women per reporting year (7 counted categories)")
ax.set_ylabel("Number of districts")
ax.set_title("The three tiers are two cut-offs on one number")
ax.legend(fontsize=8)
save(fig, "02_crime_rate_tiers.png")

# 03 agreement of alternative tierings -------------------------------------------------------------------------
alt = M["alternative_tiering"]
names = {"agglomerative_ward": "Ward hierarchical", "gaussian_mixture": "Gaussian mixture", "fixed_100_300_cutoffs": "Fixed 100 / 300 cut-offs", "equal_count_terciles": "Equal-count terciles"}
order = ["agglomerative_ward", "gaussian_mixture", "fixed_100_300_cutoffs", "equal_count_terciles"]
fig, ax = plt.subplots(figsize=(5.4, 2.9))
vals = [alt[k]["agreement_with_kmeans"] * 100 for k in order]
ax.barh([names[k] for k in order][::-1], vals[::-1], color=[BLUE, BLUE, GREY, GREY][::-1])
for i, v in enumerate(vals[::-1]):
    ax.text(v + 1, i, f"{v:.1f} %", va="center", fontsize=8.5)
ax.set_xlim(0, 100)
ax.set_xlabel("Districts given the same tier as the shipped K-Means (%)")
ax.set_title("Agreement of other tiering methods with K-Means")
save(fig, "03_tiering_agreement.png")

# 04 nearest district per city --------------------------------------------------------------------------------
cov = M["city_coverage"]["nearest_district_km"]
items = sorted(cov.items(), key=lambda kv: -kv[1])[:20]
fig, ax = plt.subplots(figsize=(5.4, 4.2))
ax.barh([k for k, _ in items][::-1], [v for _, v in items][::-1], color=[RED if v > 100 else AMBER if v > 50 else BLUE for _, v in items][::-1])
ax.axvline(100, color="#333", ls="--", lw=1)
ax.text(102, 0.3, "100 km", fontsize=8)
for i, (_, v) in enumerate(items[::-1]):
    ax.text(v + 2, i, f"{v:.0f}", va="center", fontsize=7.5)
ax.set_xlabel("Distance from the city centre to the nearest geocoded district (km)")
ax.set_title("Coverage of the district table: 20 farthest of 40 cities")
save(fig, "04_city_coverage.png")

# 05 geocode coverage by state --------------------------------------------------------------------------------
cv = pd.DataFrame(M["coverage_by_state"]).head(16)
fig, ax = plt.subplots(figsize=(5.8, 4.0))
y = np.arange(len(cv))[::-1]
ax.barh(y, cv.total, color="#d5d9e2", label="districts in the crime file")
ax.barh(y, cv.geocoded, color=BLUE, label="geocoded and used")
ax.set_yticks(y, [s.title() for s in cv.state], fontsize=8)
ax.set_xlabel("Districts")
ax.set_title("Geocoding coverage, 16 largest states (11 states/UTs have none)")
ax.legend(fontsize=8, loc="lower right")
save(fig, "05_state_coverage.png")

# 06 route scores day vs night --------------------------------------------------------------------------------
rt = [r for r in M["routes"] if "error" not in r and r["alternatives"] > 1]
fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.3), sharey=False)
for ax, key, ttl in ((axs[0], "score_day", "Daytime (12:30 IST)"), (axs[1], "score_night", "Night (23:30 IST)")):
    for i, r in enumerate(rt):
        ax.plot([i, i], r[key], "-", color=GREY, lw=1)
        ax.plot(i, r[key][0], "o", color=BLUE, ms=4)
        ax.plot(i, r[key][1], "s", color=AMBER, ms=4)
    ax.set_xticks(range(len(rt)), [r["pair"].replace(" - ", "\n") for r in rt], fontsize=5.5, rotation=90)
    ax.set_title(ttl, fontsize=9)
axs[0].set_ylabel("Route risk score")
axs[0].plot([], [], "o", color=BLUE, label="route 0 (OSRM first)")
axs[0].plot([], [], "s", color=AMBER, label="route 1")
axs[0].legend(fontsize=7)
fig.suptitle("Night multiplies every score by 1.6 and never reorders routes (10 pairs with alternatives)", fontsize=9, fontweight="bold")
save(fig, "06_route_scores_day_night.png")

# 07 API latency ----------------------------------------------------------------------------------------------
lat = A["latency"]
short = {"GET /api/health": "health", "GET /api/risk/areas (467 rows)": "risk areas", "POST /api/auth/login (bcrypt)": "login (bcrypt)", "GET /api/auth/me": "me",
         "POST /api/guardians": "add guardian", "GET /api/guardians": "list guardians",
         "POST /api/sos/start (30 guardians, no channel configured)": "SOS start", "POST /api/sos/{id}/location": "location push",
         "GET /api/track/{token} (public)": "track page", "POST /api/sos/{id}/evidence (100 KB)": "evidence 100 KB",
         "POST /api/sos/{id}/evidence (1 MB)": "evidence 1 MB", "POST /api/sos/{id}/evidence (5 MB)": "evidence 5 MB",
         "GET /api/sos/{id}/evidence": "evidence list", "POST /api/routes/plan (live OSRM + 467-district scoring)": "route plan (live OSRM)"}
rows = [(short[k], v["median_ms"], v["p95_ms"]) for k, v in lat.items() if k in short]
fig, ax = plt.subplots(figsize=(5.8, 4.2))
y = np.arange(len(rows))[::-1]
ax.barh(y + 0.2, [r[1] for r in rows], height=0.38, color=BLUE, label="median")
ax.barh(y - 0.2, [r[2] for r in rows], height=0.38, color=AMBER, label="95th percentile")
ax.set_xscale("log")
ax.set_yticks(y, [r[0] for r in rows], fontsize=8)
ax.set_xlabel("Milliseconds (log scale)")
ax.set_title("API latency on 127.0.0.1 (n = 5 to 30 calls each)")
for yi, r in zip(y, rows):
    ax.text(r[2] * 1.12, yi - 0.2, f"{r[2]:.0f}", va="center", fontsize=7)
ax.legend(fontsize=8)
save(fig, "07_api_latency.png")

# 08 SafePhrase recall vs false triggers ---------------------------------------------------------------------
sens = ["Low", "Medium", "High", "Ultra"]
rec = [S["by_sensitivity"][s]["recall"] * 100 for s in sens]
fp = [S["by_sensitivity"][s]["false_trigger_rate"] * 100 for s in sens]
fig, ax = plt.subplots(figsize=(5.2, 3.2))
xx = np.arange(4)
ax.bar(xx - 0.2, rec, 0.38, color=GREEN, label="recall on 24 phrase transcripts")
ax.bar(xx + 0.2, fp, 0.38, color=RED, label="false triggers on 80 ordinary-speech checks")
for i, (a, b) in enumerate(zip(rec, fp)):
    ax.text(i - 0.2, a + 2, f"{a:.0f}", ha="center", fontsize=8)
    ax.text(i + 0.2, b + 2, f"{b:.0f}", ha="center", fontsize=8)
ax.set_xticks(xx, [f"{s}\n({int(S['thresholds'][s] * 100)} % of words)" for s in sens])
ax.set_ylabel("Percent")
ax.set_ylim(0, 115)
ax.set_title("SafePhrase matcher on written transcripts (no audio)")
ax.legend(fontsize=7.5, loc="upper left")
save(fig, "08_safephrase_sensitivity.png")

# 09 crime mix ------------------------------------------------------------------------------------------------
mix = M["crime_mix"]
lab = ["Cruelty by husband /\nrelatives", "Assault on\nmodesty", "Rape", "Kidnapping &\nabduction", "Insult to\nmodesty", "Dowry deaths"]
val = [mix["cruelty_by_husband_share_of_all_counted_crimes"], mix["assault_on_modesty_share"], mix["rape_share"], mix["kidnapping_share"],
       mix["insult_modesty_share"], mix["dowry_deaths_share"]]
fig, ax = plt.subplots(figsize=(5.4, 3.1))
ax.bar(lab, [v * 100 for v in val], color=[RED, AMBER, PURPLE, BLUE, GREY, "#555"])
for i, v in enumerate(val):
    ax.text(i, v * 100 + 0.8, f"{v * 100:.1f} %", ha="center", fontsize=8)
ax.set_ylabel("Share of all counted crimes (%)")
ax.set_title("What the risk score counts (district file, 2001-2012)")
plt.setp(ax.get_xticklabels(), fontsize=7)
save(fig, "09_crime_mix.png")

# 10 map of districts by tier --------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(4.9, 5.2))
for t in ("low", "medium", "high"):
    s = risk[risk.risk_tier == t]
    ax.scatter(s.lng, s.lat, s=12 if t == "low" else 20, color=TIER_COL[t], alpha=0.85, label=f"{t} ({len(s)})", edgecolors="none")
cities = {"Delhi": (77.209, 28.614), "Hyderabad": (78.487, 17.385), "Lucknow": (80.946, 26.847), "Kolkata": (88.364, 22.573), "Mumbai": (72.878, 19.076), "Chennai": (80.271, 13.083)}
for n, (lo, la) in cities.items():
    ax.plot(lo, la, "k*", ms=8)
    ax.text(lo + 0.5, la + 0.4, n, fontsize=8)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal")
ax.set_title("The 467 geocoded districts by tier\n(gaps: Uttar Pradesh, West Bengal, Delhi, Uttarakhand)")
ax.legend(fontsize=8, loc="upper right")
save(fig, "10_district_map.png")

# 11 test outcomes by area (parsed from experiments/study/pytest.xml) -----------------------------------------
import xml.etree.ElementTree as ET  # noqa: E402

AREAS = [("Authentication", ("health", "register", "login_ok", "password", "me_requires", "expired")), ("Guardians", ("guardian",)),
         ("Risk data", ("risk_areas", "tier_counts")), ("Route planning", ("route_plan",)),
         ("SOS lifecycle", ("sos_", "location", "cancel", "sessions_are")), ("Guardian view + WebSocket", ("tracking", "websocket_pushes")),
         ("Evidence", ("evidence", "audio_kind", "flipped")), ("AI endpoint", ("ai_", "gemini_without")), ("Places search", ("places",))]
root = ET.parse(STUDY / "pytest.xml").getroot()
cases = [(tc.get("classname").split(".")[-1], tc.get("name"), any(c.tag == "skipped" for c in tc)) for tc in root.iter("testcase")]
counts = {a: 0 for a, _ in AREAS}
counts["Scorer + model artefacts"] = 0
gaps = 0
for cls, name, skipped in cases:
    if skipped:
        gaps += 1
    elif cls == "test_scoring":
        counts["Scorer + model artefacts"] += 1
    else:
        for a, keys in AREAS:
            if any(k in name for k in keys):
                counts[a] += 1
                break
        else:
            raise SystemExit("unclassified test " + name)
assert sum(counts.values()) + gaps == len(cases)
fig, ax = plt.subplots(figsize=(5.4, 3.4))
labs = list(counts) + ["Known defects (expected fail)"]
vals = list(counts.values()) + [gaps]
ax.barh(labs[::-1], vals[::-1], color=[AMBER] + [GREEN] * len(counts))
for i, v in enumerate(vals[::-1]):
    ax.text(v + 0.15, i, str(v), va="center", fontsize=8)
ax.set_xlabel(f"Tests ({len(cases) - gaps} pass, {gaps} documented defects fail as expected)")
ax.set_title("Automated tests by area")
save(fig, "11_tests_by_area.png")
