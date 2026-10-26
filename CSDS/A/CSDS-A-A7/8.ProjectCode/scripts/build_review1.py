"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides) for SHEGUARD.

Every number comes from docs/REPORT_FACTS.md or from the base paper tables quoted there.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import BASE_PAPER, BATCH, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, STUDENTS, TITLE, YEAR  # noqa: E402
from pptx import Presentation  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"
BATCH_TAG = "Batch A7"
if os.environ.get("SG_DIAG"):  # test hook: build with stand-in diagram files
    DIAG = Path(os.environ["SG_DIAG"])


def scrub_theme(path):
    """The template's theme is named after another project: rename it."""
    import shutil
    import zipfile
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("ppt/theme/") and item.filename.endswith(".xml"):
                data = data.decode("utf-8").replace("Hidden Risk", PRODUCT).encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 1", TITLE, BATCH_TAG, "women's safety, safe route, SafePhrase, SOS, live tracking, evidence"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = BATCH_TAG
    footer = f"{PRODUCT}  ·  Review 1  ·  {BATCH_TAG}"
    for lay in prs.slide_layouts:  # footer text lives on the layout
        for sh in lay.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, footer)
    for sl in S:
        for sh in sl.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, footer)

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), "AI Powered Women's Safety Platform")
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  {BATCH_TAG} (CSE-DS, Section A)  \u00b7  {YEAR}"], 13)
    set_notes(s, "Review 1 covers problem identification and research for SHEGUARD, a women's safety platform that combines safer route guidance, hands-free emergency activation, live guardian tracking and evidence preservation.")

    # 2 contents
    set_notes(S[1], "Nine parts: the abstract, the base paper and related work, the gap we found, our problem statement and objectives, the approach, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: before, during and after an emergency")
    fill(s, 8, "Women face harassment and assault on isolated streets and in crowds. Most safety apps need the user to open the app and press SOS, then stop at sending one alert: little prevention, no live follow-up, little evidence.", 15)
    fill(s, 13, "SHEGUARD adds safe-route guidance (route alternatives scored by district risk), SafePhrase voice activation and one-tap Smart SOS, live location to guardians by a link, SHA-256-hashed evidence and a Gemini safety assistant.", 15)
    fill(s, 18, "A working web application (installable PWA): React front end, FastAPI back end, SQLite, per-user data access. It is a prototype: no field trial yet.", 16)
    set_notes(s, "The abstract in one slide: the problem, the idea of covering the whole emergency lifecycle, and the deliverable. Note that the abstract names Flutter and Supabase; the implemented system is a React PWA with FastAPI and SQLite.")

    # 4 base paper
    s = S[3]
    fill(s, 5, BASE_PAPER, 13)
    set_paras(shape(s, 7), "Method")
    fill(s, 8, "Open government data (district population, IPC crimes against women 2013, literacy, per-capita expenditure, police strength, forest cover) are cleaned and scaled; Pearson and Spearman correlation pick features; K-Means and Gaussian mixtures form 3-4 safety clusters; maps and cab data raise deviation alerts.", 13)
    set_paras(shape(s, 10), "Data and reported results")
    fill(s, 11, "Results are 'anticipated outcomes': correlation matrices and cluster-selection tables (k=3: Davies-Bouldin 0.970, Calinski-Harabasz 221.0). No accuracy or field result is reported; the cab alert flow is a design, not an evaluation.", 13)
    set_paras(shape(s, 13), "Stated limits and our adaptation")
    fill(s, 14, "The authors note biased and under-reported crime data and missing community data. SHEGUARD adopts the cluster-to-safe-route idea (K-Means on district crime data) and adds SafePhrase, SOS, live tracking and evidence.", 13)
    set_notes(s, "The base paper is SafeRoutes (IEEE Access 2024). It is a clustering and GPS-integration framework whose results section is mostly analysis tables and expected outcomes. SHEGUARD keeps the safety-clustering and safe-route idea but uses far less data (one feature) and implements the emergency features the paper does not cover.")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Agrawal et al., 2024 (base) [1]", "Data ingestion, K-Means and GMM safety clusters, map and cab alerts", "data.gov.in district tables", "Anticipated outcomes; k=3 DB 0.970"],
            ["Farooq et al., 2023 [2]", "Systematic review of IoT women-safety devices", "Studies 2016-2022", "Pulse and pressure sensors most common; calls for auto-activated alerts"],
            ["Batch survey [3], [4], [5], 2025-2026", "Mobile app with alerts; shake-to-alert; cross-platform app (from titles)", "Not retrieved", "Not retrieved"],
            ["Thawale et al., 2025 [6]", "Android app, Google Maps, Firebase, ESP32-CAM, crime-zone classes", "Pre-defined test locations", "Zone accuracy 93 %; SOS delivery 4-6 s (as reported)"],
            ["Shinde et al., 2025 [7]", "Safe-route Android app: crime map, SOS, voice, check-ins", "Public crime records", "Design description; no accuracy figures"],
            ["Sangeeta et al., 2026 [8]", "ExtrAnom video-anomaly benchmark for women-centric crimes", "1,001 videos, 5 categories", "Existing VAD datasets insufficient"]]
    sz = table_size(rows, 1164, 520, [0.22, 0.33, 0.20, 0.25], 14, 9)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "[1], [2], [6], [7] and [8] were read. [3] to [5] come from the batch literature survey and could not be retrieved independently, so only their titles are used and no results are claimed for them. Numbers for [6] are the authors' own, measured on their own test locations.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Supporting evidence: clustering for safety zones")
    ch = replace_chart(s, 4, ["k=2", "k=3", "k=4", "k=5", "k=6", "k=7", "k=8", "k=9", "k=10"],
                       [("Calinski-Harabasz", [264.68, 220.96, 222.71, 207.77, 199.88, 187.94, 180.40, 172.08, 165.65])], number_format="0.0")
    style_chart(ch, "Cluster-selection index printed in the base paper [1] (its Table 4)", ["2F6FB0"], number_format="0.0", legend=False, label_pt=11, axis_title="Calinski-Harabasz index")
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, "Clustering district crime data into 3-4 zones is an accepted way to score area safety without labels [1]. A related app reports 93 % zone accuracy on its own test places [6].", 14)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, "These are other authors' figures on other data (multi-feature 2013 tables, a handful of test places). They motivate the approach; they are not our results.", 15)
    set_notes(s, "The chart reproduces the base paper's own Calinski-Harabasz values as printed in its Table 4 (the column header there is mislabelled 'Explained Variance'). It shows the paper's method of choosing 3-4 clusters; it is not a SHEGUARD measurement.")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    steps = ["Danger arises", "Open app, find phone", "Press SOS button", "One-time alert sent", "Location shared once", "Little evidence kept"]
    for sid, t in zip((5, 8, 11, 14, 17, 20), steps):
        fill(s, sid, t, 14)
    set_paras(shape(s, 24), "SOS apps and wearables")
    fill(s, 25, "SOS and panic-button apps send an alert to contacts; IoT wearables with GPS and GSM send location when triggered. Helplines connect to the police.", 15)
    set_paras(shape(s, 29), "Fastest-route maps")
    fill(s, 30, "Map apps suggest the fastest route without considering safety; follow-up and evidence are left to the user.", 16)
    set_notes(s, "How a user is supported today, from the batch literature survey.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
        (7, 8, "Manual activation", "SOS must be triggered by hand, which is hard when frightened."),
        (12, 13, "Alert only", "Most apps send an alert and stop: no prevention or follow-up."),
        (17, 18, "Speed, not safety", "Routes are chosen for speed; area risk is ignored."),
        (22, 23, "Weak evidence", "Audio, images and timestamps are rarely preserved securely; guardians get one-time alerts.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "The four limitations listed in the batch literature survey.")

    # 9 research gap
    s = S[8]
    gaps = [("Prevention", "Safe-route guidance is rarely joined with emergency features in one app."),
            ("Activation", "Few apps offer hands-free activation besides a button [2]."),
            ("Follow-up", "Guardians usually get one message, not a live location they can watch."),
            ("Evidence", "Photos, audio and timestamps are rarely kept with an integrity check."),
            ("Realisation", "The base paper [1] designs cab alerts but reports no working system.")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fill(s, tid, txt, 16)
    set_notes(s, "Research gap from the batch survey: apps and devices mostly stop at the SOS alert; few combine safe-route prevention, hands-free activation and evidence preservation in one platform.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Build a platform that helps a woman avoid risk before travelling, start an emergency with minimal effort (a spoken phrase or one tap), keep trusted guardians informed with a live location, and preserve time-stamped, hashed evidence, with an AI assistant and per-user data protection.", 22)
    set_paras(shape(s, 8), "Origin, destination, phrase or tap, location")
    set_paras(shape(s, 11), "Scored routes, live guardian link, evidence record")
    set_paras(shape(s, 14), "Assistant advice + access control")
    set_notes(s, "Inputs are the trip, the trigger and the device location; outputs are scored routes, a guardian tracking link and stored evidence; the extra property is protected data.")

    # 11 objectives
    s = S[10]
    fill(s, 4, ["Provide Safe Route guidance using available safety information.",
                "Enable quick emergency activation through SafePhrase and Smart SOS.",
                "Share live location with trusted guardians during an emergency session.",
                "Preserve emergency evidence: timestamps, location, audio and images.",
                "Offer AI-powered safety assistance using the Gemini API.",
                "Protect user data with role-based access and Row Level Security."], 22, bullet=True)
    set_notes(s, "The six objectives as stated in the batch file. In the implementation, objective 6 becomes per-user query scoping in the API (SQLite has no row-level security).")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
        (7, 8, "Safe Route", "OSRM route alternatives scored by district risk tier (K-Means) and time of day; safest highlighted."),
        (12, 13, "SafePhrase + Smart SOS", "Spoken phrase (Web Speech API) or one tap starts the emergency; 3-second hold cancels."),
        (17, 18, "Live guardian tracking", "Position streams over a WebSocket to a no-login tracking link."),
        (22, 23, "Evidence", "Photo or audio saved with time, location and SHA-256 hash."),
        (27, 28, "Assistant and access", "Gemini safety assistant; JWT login, per-user data scoping; React PWA + FastAPI + SQLite.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 13)
    set_notes(s, "Five components. The abstract names Flutter and Supabase; we implemented a React progressive web app with a FastAPI and SQLite back end.")

    # 13 architecture
    s = S[12]
    put_picture(s, DIAG / "01_system_architecture.png", (215, 118, 790, 482), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React PWA, FastAPI services (routes, SOS, tracking, evidence, assistant), SQLite, model file and external services")
    set_notes(s, "Browser to FastAPI. Route scoring, SOS, WebSocket tracking, evidence hashing and the assistant run in the backend; OSRM, Nominatim, Gemini, Telegram and Gmail are external services.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
        (7, 8, "Safer route choice", "Alternatives scored and the lowest-risk one recommended."),
        (12, 13, "Quick activation", "A spoken phrase or one tap starts an SOS."),
        (17, 18, "Live guardian view", "Guardians watch the position without an account."),
        (22, 23, "Tamper-evident evidence", "Hashed photo and audio with time and place."),
        (27, 28, "AI assistance", "Location-aware safety answers from Gemini."),
        (32, 33, "Protected data", "Every query scoped to the logged-in user.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Expected outcomes are targets at this stage; they are measured and reported honestly in the later reviews.")

    # 15 references
    s = S[14]
    fill(s, 4, [f"[{i}] {r}" for i, r in enumerate(REFERENCES[:10], 1)], 14, min_pt=8, bullet=True, gap_pt=2)
    set_notes(s, "References [1] to [10]; the full list is in the report. [3] to [5] were not independently retrieved.")

    set_notes(S[15], "Thank you. Questions are welcome.")
    prs.save(OUT)
    scrub_theme(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
