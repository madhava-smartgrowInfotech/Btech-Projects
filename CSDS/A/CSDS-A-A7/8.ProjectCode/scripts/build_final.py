"""Build 16.Final_PPT.pptx from D:\\abstracts\\Templates\\Final_PPT.pptx (28 slides) for SHEGUARD.

    python scripts/build_final.py
Every number comes from docs/REPORT_FACTS.md and experiments/study/*.json (latencies are read from api_metrics.json, the last run).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import fill, put_picture, set_notes, set_paras, set_table, shape, table_size  # noqa: E402
from doc_common import BATCH, CHARTS, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, SHOTS, STUDENTS, TITLE, YEAR, study  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Final_PPT.pptx"
OUT = BATCH / "16.Final_PPT.pptx"
FOOT = "Dept. of CSE  |  Batch A7  |  Final Review"

M = study("metrics.json")
A = study("api_metrics.json")
SP = study("safephrase.json")
LAT = A["latency"]
WS = A["websocket"]


def lat(key):
    v = LAT[key]
    return v["median_ms"], v["p95_ms"]


def px(v):
    return Emu(int(v * 9525))


def table(s, rows, widths, max_pt=16, h=430, w=1180):
    sz = table_size(rows, w, h, widths, max_pt, 8)
    tshape = [sh for sh in s.shapes if sh.has_table][0]
    set_table(tshape, rows, sz, widths=widths, header_size=sz)


def two_pics(s, left, right, cap_l, cap_r, ids_remove=(7, 9), cap_ids=(8, 10), box_h=352, top=182, cap_top=546):
    put_picture(s, left, (43, top, 576, box_h), remove_ids=(ids_remove[0],), name=cap_l)
    put_picture(s, right, (657, top, 576, box_h), remove_ids=(ids_remove[1],), name=cap_r)
    set_paras(shape(s, cap_ids[0]), cap_l, 13)
    set_paras(shape(s, cap_ids[1]), cap_r, 13)
    for cid in cap_ids:
        c = shape(s, cid)
        c.top = px(cap_top)
        c.height = px(100)


def diagram_with_panel(s, img, points, pic_box, panel_box, size=16):
    """Large diagram on the left, key points (the template's caption shape, moved and left-aligned) on the right."""
    put_picture(s, img, pic_box, remove_ids=(7,), name=Path(img).stem)
    cap = shape(s, 8)
    cap.left, cap.top, cap.width, cap.height = (px(v) for v in panel_box)
    fill(s, 8, ["\u2022  " + p for p in points], size, min_pt=11, gap_pt=6)
    for p in cap.text_frame.paragraphs:
        p.alignment = PP_ALIGN.LEFT
        for r in p.runs:
            r.font.italic = False
            r.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    cap.text_frame.vertical_anchor = MSO_ANCHOR.TOP


def build():
    r = M["reproduction"]
    e = M["one_feature_equivalence"]
    st = M["seed_stability"]
    rs = M["route_summary"]
    cc = M["city_coverage"]
    med = SP["by_sensitivity"]["Medium"]
    ult = SP["by_sensitivity"]["Ultra"]
    hi = SP["by_sensitivity"]["High"]

    prs = Presentation(SRC)
    S = list(prs.slides)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author = f"{PRODUCT}: Final Review", TITLE, "Batch A7"
    cp.keywords = "women's safety, safe route, K-Means, SOS, live tracking, evidence hashing"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A7"
    for s in S[1:]:
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("Dept. of CSE"):
                set_paras(sh, FOOT)

    # 1 title
    s = S[0]
    set_paras(shape(s, 4), TITLE)
    set_paras(shape(s, 5), "Final Review")
    set_paras(shape(s, 6), "Team Details : Batch A7")
    set_paras(shape(s, 7), [f"{rn}   {n}" for n, rn in STUDENTS], 16)
    set_paras(shape(s, 8), ["Under the Esteemed Guidance of", GUIDE, f"{GUIDE_DESIG}, Department of CSE (Data Science)"])
    set_paras(shape(s, 9), f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)  \u00b7  Academic Year {YEAR}", 12)
    set_notes(s, "Final review of SHEGUARD: a women's safety web app with district-risk safe routes, SafePhrase and one-tap SOS, live guardian tracking, hashed evidence and an AI assistant.")

    # 2 contents
    s = S[1]
    fill(s, 7, ["Abstract", "Base Paper & Literature Survey", "Research Gap & Problem Statement", "Objectives", "Proposed System & Architecture", "Methodology & Pipeline",
                "Design & Implementation", "Results, Parameter Analysis, Testing & Comparison", "Output Screens", "Conclusion & Future Scope", "References"], 20, bullet=True)

    # 3 abstract
    s = S[2]
    fill(s, 7, ["Women face harassment on isolated and crowded streets; most safety apps need a manual SOS press and stop at sending one alert.",
                "SHEGUARD is a working web app (React PWA + FastAPI + SQLite) covering before, during and after an emergency: safe-route scoring, SafePhrase and one-tap SOS, live guardian tracking and SHA-256 evidence capture.",
                f"Area risk: K-Means (k=3) on 467 districts of 2001-2012 crime counts - silhouette {r['silhouette']:.3f}, Davies-Bouldin {r['davies_bouldin']:.3f}; OSRM routes are scored against it.",
                f"Measured: 51 automated tests pass (6 documented defects), WebSocket push {WS['one_viewer_post_to_receive']['mean_ms']:.0f} ms, SafePhrase matcher recall {med['recall'] * 100:.0f} % with no false trigger at the default level.",
                "Honest limits: the model is two cut-offs on one number; no districts for Uttar Pradesh, West Bengal or Delhi; the Gemini key hit its quota; Telegram and Gmail were not configured, so alerts were never delivered; no field trial.",
                "Keywords: women's safety, safe route, clustering, SOS, live tracking, evidence integrity."], 17, bullet=True)
    set_notes(s, "Abstract: problem, approach, headline measurements and the honest limits. The abstract mentions Flutter and Supabase; the shipped system uses React and FastAPI with SQLite.")

    # 4 base paper
    s = S[3]
    fill(s, 7, [REFERENCES[0],
                "Task: data-driven safe zones for women's safety. Seven data.gov.in datasets (district crimes 2013, population, literacy, per-capita expenditure, police strength, forest cover) feed imputation, scaling, Pearson and Spearman analysis.",
                "Method: K-Means and Gaussian mixture models, 3-4 clusters; Silhouette, Calinski-Harabasz, Davies-Bouldin, BIC and a Ward dendrogram select the number; dummy 'safest city' data scores the clusters.",
                "Travel part: maps API and cab integration with a 1.96x safety buffer and deviation alerts - designed, not implemented or evaluated.",
                "Results are 'anticipated outcomes' (correlation matrices, cluster tables); k=3 in its tables: Davies-Bouldin 0.970, Calinski-Harabasz 221.0, silhouette 0.416. No accuracy figures.",
                "We adopt its safe-route idea and add SafePhrase, one-tap SOS, live guardian link, hashed evidence and an assistant."], 16, bullet=True)
    set_notes(s, "Read from Documentary/Base paper 2.pdf. Its tables are on multi-feature 2013 data; ours are on one feature, so the indices are not comparable.")

    # 5 literature survey
    s = S[4]
    rows = [["Author / Year", "Methodology", "Dataset", "Key Results", "Limitations"],
            ["Agrawal et al., 2024 (base) [1]", "K-Means, GMM, cab-vendor alerts", "data.gov.in district data, 2013 crimes", "Cluster tables; anticipated outcomes", "Travel part not built or tested"],
            ["Farooq et al., 2023 [2]", "Systematic review of IoT devices for women's safety", "Studies from 2016 to 2022", "Pulse and pressure sensors most used; GPS, GSM, Raspberry Pi; logistic regression, HMM, decision trees", "Calls for auto-activation with less human interaction"],
            ["Thawale et al., 2025 [6]", "Android app, ESP32-CAM, Firebase, crime-zone classes", "Historical crime data, test locations", "Reports 93 % zone accuracy; SOS in 4-6 s", "Needs extra hardware; own test locations"],
            ["Shinde et al., 2025 [7]", "Safe-route app: SOS, heatmap, voice commands, safety check", "Crime reports, traffic, crowd density (design)", "System design described", "Not examined for measured results"],
            ["Sangeeta et al., 2026 [8]", "ExtrAnom video-anomaly benchmark", "1,001 videos, 5 crime types", "Existing datasets insufficient for women-centric events", "Video, not a safety app"],
            ["Batch survey [3], [4], [5]", "Mobile alert, shake-to-alert, cross-platform app", "Not retrieved", "Not retrieved", "Listed only; nothing quoted"]]
    table(s, rows, [0.17, 0.23, 0.18, 0.24, 0.18], 17, 460)
    set_notes(s, "[1], [2], [6], [7], [8] were read from PDFs; [3]-[5] could not be retrieved so no results are claimed for them.")

    # 6 research gap
    s = S[5]
    rows = [["Author / Paper", "Research Gap"],
            ["Base paper [1]", "Zones and route deviation for cabs only; no hands-free activation, live guardian link or evidence capture; its travel integration is not implemented"],
            ["IoT review [2], ESP32 app [6]", "Extra hardware (wearables, camera module); the review itself asks for auto-activation with less human interaction"],
            ["Route app [7], mobile alert apps [3]-[5]", "SOS and location sharing; safe-route scoring, voice activation and evidence preservation are rarely joined"],
            ["Existing practice (batch survey)", "Manual SOS that is hard to press in an emergency; routes chosen for speed; evidence rarely kept securely; one-time alerts, not live updates"],
            ["All reviewed work", "No single platform joins safe-route prevention, hands-free activation, live guardian tracking and evidence preservation. SHEGUARD prototypes it - without yet proving the risk model on real incidents"]]
    table(s, rows, [0.27, 0.73], 18, 440)
    set_notes(s, "The gap follows the batch literature survey (research gap) and the papers read. The prototype closes the integration gap, not the evidence gap.")

    # 7 problem statement
    s = S[6]
    fill(s, 7, ["Women face safety threats in isolated and in crowded public places.",
                "Existing apps need a manual SOS press, which is difficult for a frightened user.",
                "Most solutions stop at sending an alert; they do not help prevent risk or support follow-up.",
                "Emergency evidence is rarely captured or stored securely.",
                "Need: a platform that helps prevent risk, activates help with minimal effort, keeps guardians informed with live location and preserves evidence."], 20, bullet=True)

    # 8 objectives
    s = S[7]
    fill(s, 7, ["Safe-route guidance - partly met: OSRM routes scored against 467 district risk tiers (2001-2012 data, 56 % geocoded).",
                "Quick activation (SafePhrase, Smart SOS) - partly met: one-tap SOS and voice matcher; no shake or automatic trigger.",
                "Live location to guardians - met: WebSocket push, guardians need no account.",
                "Evidence preserved securely - partly met: timestamp, location, SHA-256; files are publicly retrievable by URL.",
                "AI assistance with Gemini - implemented, not demonstrated: the key's quota was exhausted (HTTP 429).",
                "Protect data with role-based access and RLS - partly met: per-user query scoping, bcrypt, JWT; no RLS (SQLite) and one role only."], 19, bullet=True)

    # 9 proposed system
    s = S[8]
    fill(s, 7, ["Prevent - plan a route: OSRM alternatives are scored by the risk of the nearest district at every 8th point; the lowest score is recommended.",
                "Activate - tap SOS, or say a SafePhrase (browser speech recognition + word-window matcher); cancel only by a 3-second hold.",
                "Inform - a session with an unguessable share link; position streams every ~4 s over WebSocket to the guardian's read-only page.",
                "Alert - Telegram message and email per guardian with the link (code complete; not configured in this run, so reported as 'not sent').",
                "Preserve - photo or audio saved with time, location and a SHA-256 hash.",
                "Assist - Gemini answers safety questions with an SOS-first system prompt (quota exhausted in this run).",
                "Protect - bcrypt passwords, JWT, every query scoped to the owner."], 18, bullet=False)

    # 10 architecture
    s = S[9]
    diagram_with_panel(s, DIAG / "01_system_architecture.png",
                       ["React 19 + Vite + TypeScript PWA with Leaflet map, Web Speech API, geolocation and MediaRecorder",
                        "FastAPI: 10 routers, 19 REST endpoints + 1 WebSocket, JWT + bcrypt, owner-scoped queries",
                        "Services: OSRM routing, district-risk scorer, Gemini, Telegram, Gmail, SHA-256 hashing",
                        "Storage: SQLite (6 tables), evidence folder, risk_model.joblib and district_risk.csv",
                        "External: OSRM demo server, Nominatim, OSM tiles, Gemini API"],
                       (43, 178, 640, 494), (700, 200, 540, 440), 17)

    # 11 methodology
    s = S[10]
    put_picture(s, DIAG / "02_high_level_workflow.png", (57, 178, 1161, 424), remove_ids=(7,), name="High-level workflow")
    set_paras(shape(s, 8), "End-to-end workflow: register, add guardians, plan a safe route or listen for a SafePhrase, SOS, alert and live tracking, evidence, cancel by 3-second hold", 14)

    # 12 dataset, features, model
    s = S[11]
    set_paras(shape(s, 4), "Dataset, Features & Model")
    fill(s, 7, ["Crime data: Kaggle 'Crime in India' district file (CC0), 2001-2012: 9,017 rows, 8,597 after dropping TOTAL rows; 35 states/UTs; 827 district pairs; 7 crime columns.",
                "Geocoding: Nominatim resolved 467 of 827 districts (56.5 %); the rest were dropped, not guessed. No geocoded district exists for Uttar Pradesh (77), West Bengal (30), Delhi (24) and 8 other states/UTs.",
                "Feature: one number per district - crimes per reporting year (sum of 7 columns / years reported); a count, not a rate per population.",
                f"Model: StandardScaler + K-Means k=3 (random_state 42): tiers low {r['tier_counts']['low']} / medium {r['tier_counts']['medium']} / high {r['tier_counts']['high']}. Equivalent to two cut-offs at {e['threshold_low_medium']:.1f} and {e['threshold_medium_high']:.1f} crimes a year (100 % agreement).",
                "Route score: every 8th point -> nearest district (haversine) -> weight 1.0 / 2.5 / 5.0 -> mean; night (about 20:30-05:30 IST) x 1.6. No train/test split: unsupervised, no ground truth.",
                "Browser side: SafePhrase = share of phrase words inside a window of spoken words (100 / 85 / 75 / 60 %)."], 15.5, bullet=True)
    set_notes(s, "The 2001-2012 file and the district-level counts are old and coarse; the documents say so. The state-year 2001-2021 file is not used by any feature.")

    # 13 decision workflow
    s = S[12]
    diagram_with_panel(s, DIAG / "10_algorithm_flowchart.png",
                       ["Route scoring: OSRM alternatives -> sample every 8th point -> nearest district -> tier weight -> mean -> x1.6 at night -> sort -> first is recommended",
                        "SafePhrase: normalise transcript -> exact substring hit, else best word share in a sliding window -> compare with the sensitivity threshold -> start SOS",
                        "The night factor scales every route equally, so it never changes which route is recommended (16 of 16 test pairs)"],
                       (43, 178, 560, 494), (630, 210, 610, 420), 17)

    # 14 user-system interaction
    s = S[13]
    set_paras(shape(s, 4), "User\u2013System Interaction")
    diagram_with_panel(s, DIAG / "09_sequence_diagram.png",
                       ["The browser gets its position and calls POST /api/sos/start; the API stores the session, notifies each guardian and returns the tracking link",
                        "While active, the device pushes its position about every 4 s; the API stores the ping and broadcasts it over the WebSocket",
                        "Evidence uploads are hashed on the server; cancel is a 3-second hold and the guardian page changes to 'ended'"],
                       (43, 178, 560, 494), (630, 210, 610, 420), 17)

    # 15 database
    s = S[14]
    diagram_with_panel(s, DIAG / "06_er_diagram.png",
                       ["6 SQLite tables: users, guardians, emergency_sessions, location_pings, evidence, district_risk",
                        "A user owns guardians and sessions; a session holds many pings and evidence rows",
                        "share_token is unique per session: the only key a guardian ever holds",
                        "district_risk is loaded from data/district_risk.csv at start-up (467 rows)"],
                       (43, 178, 560, 494), (630, 210, 610, 420), 17)

    # 16 implementation highlights
    s = S[15]
    rows = [["Module", "Implementation"],
            ["Area risk", "pandas + scikit-learn: per-district crimes per year, StandardScaler, K-Means k=3, risk_score 0-100, joblib model, CSV loaded into SQLite"],
            ["Safe route", "httpx call to OSRM (alternatives, full geometry), haversine nearest district in pure Python, weighted mean, sort; about 300 ms per route to score"],
            ["SOS and tracking", "FastAPI async routes, per-session share_token, WebSocket manager that broadcasts location and cancel messages to viewers"],
            ["Evidence", "multipart upload, server-side SHA-256, file saved as <hash prefix>.<ext>, row with kind, location and time"],
            ["SafePhrase", "Web Speech API in continuous mode, word-window matcher in TypeScript, phrases and fingerprints kept in the browser"],
            ["Security and UI", "bcrypt, JWT (7 days), owner checks on every query; React 19, Tailwind 4, Leaflet, installable PWA; 51 backend tests"]]
    table(s, rows, [0.18, 0.82], 18, 440)

    # 17 results
    s = S[16]
    set_paras(shape(s, 4), "Results \u2013 Measured Performance")
    rows = [["Measure", "Result", "Note"],
            ["Cluster quality, k=3, 467 districts", f"silhouette {r['silhouette']:.3f}; Davies-Bouldin {r['davies_bouldin']:.3f}", f"Calinski-Harabasz {r['calinski_harabasz']:.1f}; one feature, no held-out set"],
            ["Tiers low / medium / high", f"{r['tier_counts']['low']} / {r['tier_counts']['medium']} / {r['tier_counts']['high']}", "mean 97.8 / 327.9 / 720.9 crimes a year"],
            ["Stability over 30 random inits", f"ARI min {st['min_ari_vs_shipped']:.3f}, mean {st['mean_ari']:.3f}", "districts near the cut-offs move"],
            ["Geocoding coverage", "467 of 827 (56.5 %)", f"nearest district to 40 cities: median {cc['median_km']:.1f} km, max {cc['max_km']:.1f} km"],
            ["16 real city pairs routed", f"{rs['pairs_with_alternatives']} had 2 routes; safest = fastest in {rs['recommended_is_fastest']}", f"day and night order identical in {rs['ranking_same_day_night']} of 16"],
            ["SafePhrase matcher (default level)", f"recall {med['recall'] * 100:.1f} %; {med['false_triggers']} false triggers", "24 written transcripts; no audio"],
            ["WebSocket push to guardian", f"mean {WS['one_viewer_post_to_receive']['mean_ms']:.1f} ms (p95 {WS['one_viewer_post_to_receive']['p95_ms']:.1f})", "localhost, 30 trials"],
            ["Automated tests", "51 passed, 6 expected-fail", "the 6 document real defects"]]
    table(s, rows, [0.34, 0.30, 0.36], 18, 420)
    set_paras(shape(s, 8), "Cluster indices measure separation of one number, not safety; there is no ground truth for risk. Alert delivery and the Gemini assistant could not be measured.", 13)
    set_notes(s, "All values from experiments/study/*.json, last run. There is no accuracy figure for the risk model because there are no labels.")

    # 18 tier results + SafePhrase trade-off (confusion-matrix equivalents)
    s = S[17]
    set_paras(shape(s, 4), "Tier Results & SafePhrase Trade-off")
    two_pics(s, CHARTS / "02_crime_rate_tiers.png", CHARTS / "08_safephrase_sensitivity.png",
             "Tier-by-tier result: 278 low, 148 medium, 41 high districts - two cut-offs on one number",
             f"SafePhrase matcher: recall {med['recall'] * 100:.0f} % (Medium) to {ult['recall'] * 100:.0f} % (Ultra); false triggers 0 % to {ult['false_trigger_rate'] * 100:.0f} %")
    set_notes(s, "There is no classifier confusion matrix because the area-risk model is unsupervised. Left: how districts fall into tiers. Right: the matcher's recall against false triggers on written transcripts.")

    # 19 parameter analysis
    s = S[18]
    set_paras(shape(s, 4), "Parameter Analysis: k and Other Tierings")
    alt = M["alternative_tiering"]
    two_pics(s, CHARTS / "01_k_sweep.png", CHARTS / "03_tiering_agreement.png",
             "k sweep: k=2 has the highest silhouette, k=4 beats k=3 on both indices - k=3 is a three-tier UI choice",
             f"Other methods agree with K-Means on {alt['agglomerative_ward']['agreement_with_kmeans'] * 100:.0f} % (Ward) to {alt['equal_count_terciles']['agreement_with_kmeans'] * 100:.0f} % (terciles) of districts",
             box_h=330)
    set_notes(s, "Tier weights 1/2.5/5 were tested against 1/2/3 and 1/3/9: the recommended route changed in 0 of 10 pairs with alternatives; changing the sampling step changed it in 1 of 10.")

    # 20 performance & testing
    s = S[19]
    h = lat("GET /api/health")
    rk = lat("GET /api/risk/areas (467 rows)")
    lg = lat("POST /api/auth/login (bcrypt)")
    loc = lat("POST /api/sos/{id}/location")
    sos = lat("POST /api/sos/start (30 guardians, no channel configured)")
    ev = lat("POST /api/sos/{id}/evidence (1 MB)")
    ev5 = lat("POST /api/sos/{id}/evidence (5 MB)")
    rp = lat("POST /api/routes/plan (live OSRM + 467-district scoring)")
    rows = [["Measurement", "Result (median / 95th percentile)"],
            ["API latency on 127.0.0.1", f"health {h[0]:.1f} / {h[1]:.1f} ms; risk areas {rk[0]:.1f} / {rk[1]:.1f}; location push {loc[0]:.1f} / {loc[1]:.1f}; SOS start {sos[0]:.1f} / {sos[1]:.1f}; evidence 1 MB {ev[0]:.1f} / {ev[1]:.1f}, 5 MB {ev5[0]:.1f} / {ev5[1]:.1f}; login (bcrypt) {lg[0]:.0f} / {lg[1]:.0f}"],
            ["Live route plan", f"{rp[0] / 1000:.2f} s median / {rp[1] / 1000:.2f} s p95 including the OSRM call; scoring one route about 300 ms"],
            ["WebSocket push", f"{WS['one_viewer_post_to_receive']['median_ms']:.1f} ms median with 1 viewer; mean {WS['five_viewers_post_to_all_received']['mean_ms']:.1f} ms to 5 viewers"],
            ["Automated tests", "51 passed, 6 expected-fail, 0 failed (57 tests, offline): auth, guardians, routes, SOS, evidence, WebSocket, scorer"],
            ["Defects found", "Gemini timeout gives HTTP 500; latitude 999 accepted; any WebSocket token accepted; no upload size limit; .html upload served as text/html; evidence files readable without login; no login lockout"],
            ["Machine", "Intel Core i5-12500, 15.7 GB RAM, no GPU; K-Means fits in under a second"],
            ["Not measured", "real alert delivery, Gemini answers, real GPS / microphone, load beyond 5 viewers, user study"]]
    table(s, rows, [0.20, 0.80], 17, 450)
    set_notes(s, "Latencies are from the last run of scripts/measure_api.py on a live server; single client, sequential calls.")

    # 21 comparison
    s = S[20]
    rows = [["System", "Task and data", "Method", "Reported / measured", "Extras", "Comparable?"],
            ["Base paper [1]", "District safe zones; seven data.gov.in datasets, 2013 crimes, many features", "K-Means, GMM; Pearson, Spearman; cab alerts (designed)", "k=3: DB 0.970, CH 221.0, silhouette 0.416; anticipated outcomes", "Heatmaps, cab-vendor integration", "-"],
            ["Thawale et al. [6]", "Android app with ESP32-CAM; historical crime data, test locations", "Zone classification, GPS, Firebase", "Reports 93 % zone accuracy; SOS in 4-6 s", "Camera evidence, extra hardware", "No: other task and data"],
            ["SHEGUARD", "Web app; 2001-2012 district counts, 467 geocoded districts, one feature", "K-Means k=3 on one feature; OSRM route scoring; SafePhrase; WebSocket tracking", f"DB {r['davies_bouldin']:.3f}, CH {r['calinski_harabasz']:.1f}, silhouette {r['silhouette']:.3f}; 51 tests pass; push {WS['one_viewer_post_to_receive']['mean_ms']:.0f} ms", "SafePhrase, SOS, live link, SHA-256 evidence, assistant", "No: different data and feature count"]]
    table(s, rows, [0.11, 0.2, 0.2, 0.22, 0.14, 0.13], 17, 420)
    set_paras(shape(s, 8), "Different data, features and tasks: no numeric head-to-head is possible. Indices on one feature are not comparable with indices on many features.", 13)
    set_notes(s, "State plainly: no claim that SHEGUARD is better than either paper; the comparison is of scope and approach. The base paper's results are anticipated outcomes.")

    # 22-24 outputs
    s = S[21]
    set_paras(shape(s, 4), "Output \u2013 Safe Route Planning")
    two_pics(s, SHOTS / "06_route_delhi_jaipur.png", SHOTS / "08_route_hyderabad_vijayawada.png",
             "Delhi to Jaipur: two real OSRM routes (274.1 and 299.5 km), both HIGH risk, with district risk circles",
             "Hyderabad to Vijayawada: one route, 269.1 km, HIGH (20 / 0 / 80 % low / medium / high samples)")
    s = S[22]
    set_paras(shape(s, 4), "Output \u2013 Emergency, Evidence and Guardian View")
    two_pics(s, SHOTS / "13_emergency_evidence.png", SHOTS / "14_guardian_tracking.png",
             "Active SOS: tracking link, '0 of 3 guardians reached' (no channel configured), photo and audio with SHA-256",
             "Guardian's page with no login: live position and path over WebSocket")
    s = S[23]
    set_paras(shape(s, 4), "Output \u2013 SafePhrase and AI Assistant")
    two_pics(s, SHOTS / "10_safephrase.png", SHOTS / "09_ai_assistant.png",
             "SafePhrase settings: stored phrase, SHA-256 fingerprint, four sensitivity levels (default Medium)",
             "AI assistant: the Gemini key's quota was exhausted, so the app shows its 'unavailable' message")

    # 25 conclusion
    s = S[24]
    fill(s, 7, ["Built SHEGUARD: a working web platform with safe-route scoring, SafePhrase and one-tap SOS, live guardian tracking, SHA-256 evidence and an assistant.",
                f"Measured: silhouette {r['silhouette']:.3f} and Davies-Bouldin {r['davies_bouldin']:.3f} for the risk tiers; 51 tests pass; WebSocket push about {WS['one_viewer_post_to_receive']['mean_ms']:.0f} ms; SafePhrase recall {med['recall'] * 100:.0f} % at the default level with no false trigger.",
                "Key finding: the risk 'model' is two cut-offs on one old, un-normalised number; the night factor never changes a recommendation; major cities lie far from any district (Hyderabad 149 km).",
                "Limits: Telegram / Gmail alerts and the Gemini answer were not demonstrated; evidence files are publicly retrievable; no field trial; built as a React PWA, not Flutter + Supabase.",
                "Objectives: live tracking met; route, activation, evidence and access control partly met; assistant implemented but not demonstrated."], 19, bullet=True)

    # 26 future scope
    s = S[25]
    fill(s, 7, ["Replace the one-feature tiers with population-normalised, multi-feature risk (police, infrastructure, recent years) and geocode the missing states.",
                "Make the night factor change the ranking, cap the nearest-district distance and warn where there is no data.",
                "Configure and test real Telegram / SMS / email delivery; move sending off the event loop; add shake or power-button triggers.",
                "Fix the defects: Gemini timeout handling, input ranges, authenticated evidence files, upload limits, login throttling, WebSocket token check.",
                "Field trial with real users on phones, a native or Flutter client, hosted database with row-level security, HTTPS and load testing."], 20, bullet=True)

    # 27 references
    s = S[26]
    fill(s, 7, [f"[{i}] {rf}" for i, rf in enumerate(REFERENCES, 1)], 8.5, min_pt=8.5, bullet=True, gap_pt=0.5)

    set_notes(S[27], "Thank you. Questions are welcome.")
    # drop the template's own pictures (old confusion matrix, charts...) that are no longer referenced by any shape
    for sl in S:
        xml = sl._element.xml
        for rel in list(sl.part.rels.values()):
            if rel.reltype.endswith("/image") and rel.rId not in xml.replace('r:embed="' + rel.rId + '"', "", 0) and f'"{rel.rId}"' not in xml:
                sl.part.drop_rel(rel.rId)
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
