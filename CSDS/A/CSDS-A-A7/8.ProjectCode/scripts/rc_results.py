"""Chapter 8 content: output screens, measured results, comparison with the base paper, failure analysis, objectives (SHEGUARD).

Every figure is read from experiments/study/*.json (through doc_common) or from docs/REPORT_FACTS.md.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from doc_common import CHARTS, SHOTS, STUDY, study

M = study("metrics.json")
AP = study("api_metrics.json")
SP = study("safephrase.json")
AS = study("assistant.json")["summary"]
LAT = AP["latency"]
REP = M["reproduction"]
EQ = M["one_feature_equivalence"]
RS = M["route_summary"]
CC = M["city_coverage"]
DT = M["data"]


def pc(x, n=1):
    return f"{x * 100:.{n}f}%"


def lat(key):
    return LAT[key]


# (file, caption, what it shows)
SCREENS = [
    ("01_landing.png", "Landing page", "The public home page: \"Get home safer. Alert the people who care.\", the four-step explanation (add guardians, plan a route or keep SafePhrase listening, tap SOS or say the phrase, cancel with a 3-second hold) and the buttons Get started free, I have an account, Log in and Sign up. The small print states that route risk uses historical district crime data (2001-2012), not live conditions, and that SHEGUARD does not replace emergency services. The hero picture is an illustration shipped with the app."),
    ("02_register.png", "Registration form", "The Create your account form filled in for the test user: full name, e-mail, a password of at least six characters and the terms checkbox. The account was created through this form; the API answered HTTP 200 and returned a token and the profile."),
    ("03_profile_guardians.png", "Profile with three trusted guardians", "The Profile and Guardians screen after three guardians were added through the form: Meena Reddy (mother, phone and e-mail), Karthik Reddy (brother, phone and Telegram chat ID) and Divya Rao (friend, phone, e-mail and Telegram chat ID). The banner confirms that the last guardian \"will be alerted in your next emergency\"."),
    ("04_dashboard.png", "Dashboard", "The signed-in home screen: the large SOS button, three status tiles (3 guardians added, area risk here \"Medium - GURGAON\" because the browser position was set to central Delhi and the nearest district in the table is Gurgaon, battery 100%), the SafePhrase tile (one active phrase, listening off) and shortcuts to the AI Guardian, Safe Routes, the guardian tracker and a local siren."),
    ("05_route_search.png", "Destination search", "The Safe Routes screen with \"Jaipur\" typed into the search box. The suggestions come from the OpenStreetMap Nominatim service through the backend (`GET /api/places/search`); the start point is the browser position (Delhi)."),
    ("06_route_delhi_jaipur.png", "Delhi to Jaipur: two scored alternatives", "Two real OSRM driving routes from Delhi to Jaipur on the Leaflet map with the district risk circles: the \"Safest route\" of 274.1 km and 204 min (samples 33% low, 25% medium, 42% high) and \"Alternative 1\" of 299.5 km and 205 min (19% low, 5% medium, 76% high). Both carry the badge HIGH risk, because at least 20% of the sampled points lie in high-tier districts. The safety-tips panel shows the unavailable message of the AI assistant."),
    ("07_route_details.png", "Route cards and the assistant panel", "The same plan scrolled to the route cards and the \"Safety tips for this route\" panel. The panel would show Gemini-written advice; during this run the Gemini key's quota was exhausted (HTTP 429), so the interface shows \"The AI assistant is unavailable right now. Please try again in a few minutes.\" instead of an invented answer."),
    ("08_route_hyderabad_vijayawada.png", "Hyderabad to Vijayawada", "A single route of 269.1 km and 213 min with 20% low, 0% medium and 80% high samples, labelled HIGH risk. Only one alternative was returned by OSRM, so there is nothing to choose between. The risk circles near Vijayawada, Guntur, Machilipatnam and Eluru are the high-tier Andhra Pradesh districts; none is drawn around Hyderabad itself because the nearest geocoded district is 149 km away."),
    ("09_ai_assistant.png", "AI Guardian chat", "The assistant screen after the question \"What should I do if I feel unsafe walking alone at night?\" was sent. The reply bubble is the failure message \"The AI assistant is unavailable right now\" (the backend returned HTTP 502 for Google's quota error 429). The screen is a real capture of the failure path; no answer from Gemini could be captured in this run."),
    ("10_safephrase.png", "SafePhrase settings", "The SafePhrase screen: the Turn listening on button, a Test a phrase panel that never sends an alert, the default phrase \"help me sheguard\" with its SHA-256 fingerprint prefix, the form for a new cover sentence and the four sensitivity levels (Low 100% of words, Medium 85%, High 75%, Ultra 60%). Phrases are stored in the browser only."),
    ("11_safephrase_added.png", "Second SafePhrase added", "After saving the cover sentence \"bring my blue bag\" (label \"casual cover\"): the list now holds two active phrases, the new one above the default \"help me sheguard\", and only the beginning of a SHA-256 fingerprint of each sentence is displayed. The sentences are stored in this browser, not on the server."),
    ("12_emergency_started.png", "Emergency screen after SOS", "One tap on SOS at the Hyderabad position opened the emergency screen: \"Guardian tracking active\", the delivery report **0 of 3 guardians reached by Telegram or email** (no Telegram bot token or Gmail credentials are configured, so each channel reports not sent), the live tracking link `http://localhost:5107/track/...` with a Copy link button, the live map, the Capture photo and Record audio buttons and the call button."),
    ("13_emergency_evidence.png", "Evidence captured", "A photograph and a 3-second audio clip were saved: each row shows a green tick, the kind, the beginning of the SHA-256 hash and the time stamp. The photograph is one of the application's own screenshots and the audio is Chrome's built-in test tone (fake microphone), so the evidence content is a stand-in; the hashing, storage and listing are real."),
    ("14_guardian_tracking.png", "Guardian's live tracking page", "The read-only page a guardian opens from the link, in a second browser with no login: \"Asha Reddy may need help\", status active with start and last-update times, \"Live - position updates as it changes\", the map with the moving position and the pink trail, and the note to contact emergency services (112 / 911)."),
    ("15_hold_to_cancel.png", "Hold-to-cancel", "The cancel button while it is being held: \"KEEP HOLDING... 55%\". The user must keep pressing for three seconds, so a stray tap cannot end the alert. The evidence rows and the call button are visible above it."),
    ("16_dashboard_after_sos.png", "Dashboard after cancelling", "After the three-second hold the app returned to the dashboard: two active phrases, the SOS button ready again and, under Recent activity on this device, the entries \"Emergency cancelled - Confirmed safe by hold-to-cancel\", \"Audio evidence saved\" and \"Photo evidence saved\" (hashed and time-stamped)."),
    ("17_guardian_cancelled.png", "Guardian's page after cancel", "The same tracking page after the user confirmed safety: \"Asha Reddy has ended the emergency\", status cancelled, \"Location sharing has stopped\", with the full trail kept on the map. The cancel message reached the open page through the WebSocket."),
    ("18_profile_activity.png", "Profile with recent activity", "The profile screen again at the end of the run: the account header with the Sign out button, the three trusted guardians with their Remove buttons, the Add guardian form (disabled until a name is typed) and, further down, the Safety tools section."),
]
MAIN_FILES = ["04_dashboard.png", "06_route_delhi_jaipur.png", "08_route_hyderabad_vijayawada.png", "09_ai_assistant.png", "10_safephrase.png",
              "12_emergency_started.png", "13_emergency_evidence.png", "14_guardian_tracking.png", "16_dashboard_after_sos.png", "17_guardian_cancelled.png"]
KEY_SINGLE = {"06_route_delhi_jaipur.png", "12_emergency_started.png", "14_guardian_tracking.png"}
_BY_FILE = {s[0]: s for s in SCREENS}
MAIN = [_BY_FILE[f] for f in MAIN_FILES]
EXTRA = [s for s in SCREENS if s[0] not in MAIN_FILES]
assert len({s[0] for s in SCREENS}) == 18


def _short(d, text):
    if getattr(d, "report", False):
        cut = text.find(". ", 110)
        return text[:cut + 1] if cut > 0 else text
    return text


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("Every screen below is a real capture of SHEGUARD running on 26 October 2026 with real data in it: an account registered through the form, three guardians added "
        "through the profile screen, real OSRM routes and Nominatim place search, a real SOS session with a moving position, evidence saved with its hash, and the guardian's "
        "page opened in a second, logged-out browser. The browser position was set by the test script to the centres of Delhi and Hyderabad (a phone's GPS was not used), the "
        "microphone was Chrome's built-in test device and the evidence photograph is one of the application's own screenshots. The captures are 1440 by 900 pixels.")
    pending = []

    def flush():
        for i in range(0, len(pending), 2):
            pair = pending[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t in pair], width=3.15, max_h=2.2)
            for f, cap, text in pair:
                d.p(f"**{cap}.** {_short(d, text)}", size=10.5, line=1.25)
        pending.clear()

    for f, cap, text in MAIN:
        if f in KEY_SINGLE:
            flush()
            d.figure(SHOTS / f, cap, width=4.4)
            d.p(_short(d, text), size=10.5, line=1.3)
        else:
            pending.append((f, cap, text))
    flush()
    if all_screens:
        d.h3("Additional screens")
        extra_block(d)


def extra_block(d):
    """The screens not shown in Chapter 8 of the full report, in side-by-side pairs with one paragraph each."""
    for i in range(0, len(EXTRA), 2):
        pair = EXTRA[i:i + 2]
        d.figure_pair([(SHOTS / f, cap) for f, cap, _t in pair], width=3.15, max_h=2.2)
        for f, cap, text in pair:
            d.p(f"**{cap}.** {text}", size=10.5, line=1.25)


# ------------------------------------------------------------------------------------------------ test counts from the pytest run
_AREAS = [("Authentication", ("health", "register", "login_ok", "password", "me_requires", "expired")), ("Guardians", ("guardian",)),
          ("Risk data", ("risk_areas", "tier_counts")), ("Route planning", ("route_plan",)),
          ("SOS lifecycle", ("sos_", "location", "cancel", "sessions_are")), ("Guardian view and WebSocket", ("tracking", "websocket_pushes")),
          ("Evidence", ("evidence", "audio_kind", "flipped")), ("AI endpoint", ("ai_", "gemini_without")), ("Places search", ("places",))]


def test_counts():
    root = ET.parse(STUDY / "pytest.xml").getroot()
    cases = [(tc.get("classname").split(".")[-1], tc.get("name"), any(c.tag == "skipped" for c in tc)) for tc in root.iter("testcase")]
    counts = {a: 0 for a, _ in _AREAS}
    counts["Scorer and model artefacts"] = 0
    gaps = 0
    for cls, name, skipped in cases:
        if skipped:
            gaps += 1
        elif cls == "test_scoring":
            counts["Scorer and model artefacts"] += 1
        else:
            for a, keys in _AREAS:
                if any(k in name for k in keys):
                    counts[a] += 1
                    break
    return counts, gaps, len(cases)


# ------------------------------------------------------------------------------------------------ results
def sec_engine_results(d):
    d.h2("Model Performance")
    sil, dbi, chi = REP["silhouette"], REP["davies_bouldin"], REP["calinski_harabasz"]
    d.p("SHEGUARD contains one trained model, the area-risk model: K-Means with three clusters on a single number per district, the average number of recorded crimes against "
        "women per reporting year. Everything else that is scored (the route score, the SafePhrase matcher) is rule-based. There is **no ground truth** for \"how risky a district is\" and "
        "therefore no accuracy, precision or recall for this model and no train/test split: the model is fitted on all 467 districts, and the only measures available "
        "are internal cluster-quality indices, which describe how well one number separates into groups, not whether the groups predict harm. All figures come from "
        "`experiments/metrics.json`, `experiments/eval/metrics.json` and the re-run in `experiments/study/metrics.json`, produced on an Intel Core i5-12500 with 15.7 GB RAM and no GPU; "
        "fitting takes well under a second.")
    d.table([["Measure", "Result", "Data"],
             ["Districts clustered", f"{REP['tier_counts']['low'] + REP['tier_counts']['medium'] + REP['tier_counts']['high']} of {DT['district_state_pairs']} ({pc(DT['geocode_rate'])} geocoded)", "district file 2001-2012"],
             ["Silhouette (shipped, k = 3)", f"**{sil:.4f}**", "467 districts"],
             ["Davies-Bouldin (lower is better)", f"**{dbi:.3f}**", "467 districts"],
             ["Calinski-Harabasz", f"{chi:.1f}", "467 districts"],
             ["Tiers low / medium / high", f"{REP['tier_counts']['low']} / {REP['tier_counts']['medium']} / {REP['tier_counts']['high']}", "mean 97.76 / 327.92 / 720.93 crimes per year"],
             ["Re-run agrees with the shipped table", pc(REP["agreement_with_shipped_district_risk_csv"], 0), "district_risk.csv"],
             ["Stability over 30 random starts (adjusted Rand index)", f"min {M['seed_stability']['min_ari_vs_shipped']:.3f}, mean {M['seed_stability']['mean_ari']:.3f}", "k = 3, n_init = 1"],
             ["Route scoring sanity check", "all-high route 5.0, all-low route 1.0 (pass)", "ml/eval.py"],
             ["Routes scored (16 real city pairs)", f"{RS['pairs_routed']} routed, {RS['pairs_with_alternatives']} with an alternative", "OSRM demo server"],
             ["Time to score one route", f"{RS['score_one_route_ms_mean']:.0f} ms", "pure Python, 467 districts"],
             ["Automated tests", "51 passed, 6 documented defects fail as expected", "pytest"]],
            "Headline results of the area-risk model and the route scorer", widths=[0.4, 0.34, 0.26], font=9.5)

    d.h3("Choice of the number of clusters")
    ks = M["k_sweep"]
    d.table([["k", "Silhouette", "Davies-Bouldin", "Inertia"]] + [[str(r["k"]), f"{r['silhouette']:.4f}", f"{r['davies_bouldin']:.4f}", f"{r['inertia']:.2f}"] for r in ks],
            "Cluster-quality indices for k = 2 to 8 on the standardised crime rate", widths=[0.15, 0.28, 0.3, 0.27], font=10, align=["c", "c", "c", "c"])
    d.figure(CHARTS / "01_k_sweep.png", "Silhouette and Davies-Bouldin index against the number of clusters", width=3.9)
    d.p(f"The shipped k = 3 is **a design choice, not the optimum of either index**: k = 2 has the highest silhouette ({ks[0]['silhouette']:.3f}) and k = 4 has both a higher silhouette ({ks[2]['silhouette']:.3f}) and a "
        f"lower Davies-Bouldin value ({ks[2]['davies_bouldin']:.3f}) than k = 3 ({ks[1]['silhouette']:.3f}, {ks[1]['davies_bouldin']:.3f}). Three tiers were chosen because the interface shows low, medium and high. The differences "
        "between k = 3 to 8 in silhouette are small (0.553 to 0.596), so the data do not strongly prefer one number.")

    d.h3("What the tiers are")
    rng = EQ["tier_ranges_crimes_per_year"]
    d.table([["Tier", "Crimes per year (min to max)", "Districts", "Share"]] + [[t.capitalize(), f"{rng[t][0]:.1f} to {rng[t][1]:.1f}", str(REP["tier_counts"][t]), pc(REP["tier_counts"][t] / 467, 0)] for t in ("low", "medium", "high")],
            "Value ranges of the three tiers", widths=[0.2, 0.4, 0.2, 0.2], font=10, align=["l", "c", "c", "c"])
    d.figure(CHARTS / "02_crime_rate_tiers.png", "Distribution of the crime rate with the two cut-offs that K-Means found", width=4.1)
    d.p(f"Because the only feature is one number, K-Means is equivalent to two thresholds: **{EQ['threshold_low_medium']:.2f} and {EQ['threshold_medium_high']:.2f} crimes per year**, which reproduce the K-Means tiers for "
        f"{pc(EQ['threshold_rule_agreement_with_kmeans'], 0)} of districts. The model is therefore a data-driven pair of cut-offs, not a multi-feature classifier. The silhouette of 0.58 means that these three groups are cleanly separated along "
        "this one axis; it does not mean that the groups describe safety.")
    alt = M["alternative_tiering"]
    d.p(f"Other ways of cutting the same number disagree with K-Means for many districts (Figure on tiering agreement): Ward hierarchical clustering agrees for {pc(alt['agglomerative_ward']['agreement_with_kmeans'])}, a Gaussian mixture for "
        f"{pc(alt['gaussian_mixture']['agreement_with_kmeans'])}, fixed cut-offs of 100 and 300 for {pc(alt['fixed_100_300_cutoffs']['agreement_with_kmeans'])} and equal-count terciles for {pc(alt['equal_count_terciles']['agreement_with_kmeans'])}. "
        f"Across 30 random starts the adjusted Rand index against the shipped clustering ranges from {M['seed_stability']['min_ari_vs_shipped']:.2f} upward (mean {M['seed_stability']['mean_ari']:.2f}), so districts near the cut-offs change tier with the initialisation. The size "
        "of the 41-district \"high\" group is a property of the method chosen.")
    if not getattr(d, "report", False):
        d.figure(CHARTS / "03_tiering_agreement.png", "Agreement of other tiering methods with the shipped K-Means", width=3.9)

    d.h3("What the score counts")
    mix = M["crime_mix"]
    d.p(f"The crime rate adds seven recorded categories. Cruelty by husband or relatives is {pc(mix['cruelty_by_husband_share_of_all_counted_crimes'])} of everything counted, assault on modesty {pc(mix['assault_on_modesty_share'])}, rape {pc(mix['rape_share'])}, "
        f"kidnapping and abduction {pc(mix['kidnapping_share'])}, insult to modesty {pc(mix['insult_modesty_share'])} and dowry deaths {pc(mix['dowry_deaths_share'])}. A district's tier is therefore driven mainly by recorded domestic-violence counts, which say little about "
        "the safety of a street at night. The measure is also a raw count, not a rate per head of population: the highest values are West Godavari (1,191.6), Vijayawada (1,059.0), Guntur (1,032.5), Jaipur (1,001.4) and Krishna (895.2), and large or "
        "well-reporting districts rank high. Vijayawada, Jaipur and Mumbai are averages over only 5 reported years.")
    if not getattr(d, "report", False):
        d.figure(CHARTS / "09_crime_mix.png", "Share of each crime category in the counted total", width=3.9)

    d.h3("Coverage of the district table")
    d.p(f"Only {DT['geocoded_pairs']} of {DT['district_state_pairs']} district entries ({pc(DT['geocode_rate'])}) could be geocoded; the others were dropped rather than guessed. The table has **no district at all for "
        "Uttar Pradesh (77 entries), West Bengal (30), Delhi (24), Uttarakhand (13), Tripura (10)** and six small union territories. The consequence appears when the nearest district to a city centre is measured "
        f"(40 cities): the median is {CC['median_km']:.1f} km, but {CC['over_100km']} cities are more than 100 km from any district, among them Hyderabad ({CC['nearest_district_km']['Hyderabad']:.0f} km), "
        f"Secunderabad ({CC['nearest_district_km']['Secunderabad']:.0f} km), Warangal ({CC['nearest_district_km']['Warangal']:.0f} km), Kolkata ({CC['nearest_district_km']['Kolkata']:.0f} km), Lucknow ({CC['nearest_district_km']['Lucknow']:.0f} km) and Kanpur ({CC['nearest_district_km']['Kanpur']:.0f} km). "
        "The scorer takes the nearest district however far away it is.")
    d.figure(CHARTS / "04_city_coverage.png", "Distance from city centres to the nearest district in the risk table (20 farthest of 40 cities)", width=4.0)
    if not getattr(d, "report", False):
        d.figure_pair([(CHARTS / "05_state_coverage.png", "Geocoded districts per state"), (CHARTS / "10_district_map.png", "The 467 districts by tier")], width=3.15, max_h=3.1)

    d.h3("Route scoring on real routes")
    d.p(f"Sixteen real city pairs were routed through OSRM and scored. {RS['pairs_with_alternatives']} pairs returned two alternatives and {16 - RS['pairs_with_alternatives']} returned one, so for {pc((16 - RS['pairs_with_alternatives']) / 16)} of trips there was nothing to choose between. "
        f"The recommended (lowest-score) route was also the OSRM-fastest in {RS['recommended_is_fastest']} of 16 pairs, and where an alternative existed the safest pick cost {RS['mean_extra_minutes_when_alternatives']:.1f} minutes more on average. "
        f"Along the 16 routes the mean distance to the nearest district was {RS['mean_nearest_district_km_along_routes']:.1f} km (maximum {RS['max_nearest_district_km_along_routes']:.1f} km).")
    pick = [r for r in M["routes"] if r["pair"] in ("Delhi - Jaipur", "Delhi - Agra", "Hyderabad - Warangal", "Lucknow - Kanpur", "Bhopal - Indore", "Chandigarh - Delhi", "Mumbai - Pune", "Kolkata - Patna")]
    rows = [["Pair", "Routes", "Km", "Score by day", "Score at night", "Nearest district, mean km"]]
    for r in pick:
        rows.append([r["pair"], str(r["alternatives"]), " / ".join(f"{x:.0f}" for x in r["distance_km"]), " / ".join(f"{x:.2f}" for x in r["score_day"]),
                     " / ".join(f"{x:.2f}" for x in r["score_night"]), f"{r['nearest_district_km_mean']:.0f}"])
    d.table(rows, "Scores of eight of the 16 routed pairs (lower is safer; the first number is OSRM's first route)", widths=[0.22, 0.09, 0.15, 0.18, 0.19, 0.17], font=9, align=["l", "c", "c", "c", "c", "c"])
    d.figure(CHARTS / "06_route_scores_day_night.png", "Route scores by day and at night for the pairs that returned two alternatives", width=4.7)
    nm = M["night_multiplier"]
    d.p(f"**The night factor changes the numbers but never the choice.** The same route scores {nm['day_score']:.1f} by day and {nm['night_score']:.1f} at night (ratio {nm['ratio']:.1f}); because the multiplier of {nm['constant']} is applied to every sampled point of every route, the ranking "
        f"was identical by day and at night for all {RS['ranking_same_day_night']} of 16 pairs. It affects only the displayed value and the route label. Changing the tier weights to 1/2/3 or 1/3/9 changed the recommended route in "
        f"{RS['weights_change_ranking']} of {RS['multi_route_pairs']} pairs, and changing the sampling step (1, 4, 16, 32 instead of 8) changed it in {RS['sample_n_changes_ranking']} of {RS['multi_route_pairs']}.")
    d.p(f"Scoring one route takes about {RS['score_one_route_ms_mean']:.0f} ms because every sampled point is compared with all 467 districts in Python; a live `POST /api/routes/plan` including the OSRM call took "
        f"{lat('POST /api/routes/plan (live OSRM + 467-district scoring)')['mean_ms'] / 1000:.1f} s on average (see the table of response times).")


def sec_product_results(d):
    d.h2("Software Verification Results")
    counts, gaps, total = test_counts()
    passed = total - gaps
    d.p(f"The project has a pytest suite in `tests/` that uses a throw-away SQLite database and replaces OSRM, Gemini, Telegram and Gmail by stubs, so it runs offline in about 14 s. "
        f"**{passed} of {total} tests pass; the other {gaps} are expected failures** that assert the behaviour a hardened system should have and fail on the shipped code. They are kept visible instead of being deleted.")
    d.table([["Area", "Tests", "What is checked"],
             ["Authentication", str(counts["Authentication"]), "register, duplicate e-mail, validation (short password, bad e-mail, missing field), login and wrong password, bcrypt hash stored, token required, forged and expired token rejected"],
             ["Guardians", str(counts["Guardians"]), "create, list, update, delete; another user's guardian cannot be read, edited or deleted"],
             ["Risk data", str(counts["Risk data"]), "467 districts served with three tiers and scores in 0-100; tier counts 278 / 148 / 41"],
             ["Route planning", str(counts["Route planning"]), "alternatives sorted by risk, first one recommended; login required; OSRM failure gives 502; no route gives 404"],
             ["SOS lifecycle", str(counts["SOS lifecycle"]), "session and tracking link, alert fan-out to every configured channel, ordered location trail, cancel and no updates afterwards, owner-only access, login and coordinates required"],
             ["Guardian view and WebSocket", str(counts["Guardian view and WebSocket"]), "public page with owner name and last position; unknown token 404; WebSocket pushes a location and the cancel message"],
             ["Evidence", str(counts["Evidence"]), "SHA-256 equals the hash of the stored file; one flipped bit changes it; audio accepted, other kinds and empty files rejected; count on the session; other users get 404"],
             ["AI endpoint", str(counts["AI endpoint"]), "answer returned, login and question required, provider error gives 502, missing key gives a clear error"],
             ["Places search", str(counts["Places search"]), "login required, one-character query rejected"],
             ["Scorer and model artefacts", str(counts["Scorer and model artefacts"]), "haversine distance, nearest district, tier weights 1.0 / 2.5 / 5.0, night factor 1.6 on every route, no reordering at night, empty route, no-district fallback, night window in UTC, shipped model loads, district table consistent, tiers are threshold bands"],
             ["Known defects (expected fail)", str(gaps), "see the next table"]],
            "Automated test results by area", widths=[0.24, 0.08, 0.68], font=9)
    d.figure(CHARTS / "11_tests_by_area.png", "Automated tests by area", width=3.9) if not getattr(d, "report", False) else None
    d.table([["Defect (test that documents it)", "Observed behaviour"],
             ["Gemini timeout", "An `httpx.ReadTimeout` is not caught, so the API answers HTTP 500 instead of 502 (seen live: the first two assistant calls returned 500 after 20 s)"],
             ["Latitude 999", "`POST /api/sos/start` with latitude and longitude 999 is accepted (HTTP 200)"],
             ["Unknown trigger", "`trigger` is a free string: any value is stored"],
             ["WebSocket token", "`/ws/track/{token}` accepts a token that matches no session"],
             ["Upload size", "No limit: a 20 MB \"audio\" upload was accepted in 0.24 s"],
             ["Evidence served as HTML", "A file named page.html uploaded as a photo is served back from `/evidence-files/` as text/html on the API origin"]],
            "The six documented defects", widths=[0.3, 0.7], font=9.5)

    d.h3("Response time")
    keys = [("GET /api/health", "Health check"), ("GET /api/risk/areas (467 rows)", "Risk areas (467 rows)"), ("POST /api/auth/login (bcrypt)", "Log in (bcrypt)"), ("GET /api/auth/me", "Profile"),
            ("POST /api/guardians", "Add guardian"), ("POST /api/sos/start (30 guardians, no channel configured)", "Start SOS (30 guardians, no channel configured)"),
            ("POST /api/sos/{id}/location", "Push a location"), ("GET /api/track/{token} (public)", "Guardian tracking page"),
            ("POST /api/sos/{id}/evidence (100 KB)", "Upload evidence 100 KB"), ("POST /api/sos/{id}/evidence (1 MB)", "Upload evidence 1 MB"), ("POST /api/sos/{id}/evidence (5 MB)", "Upload evidence 5 MB"),
            ("POST /api/routes/plan (live OSRM + 467-district scoring)", "Plan a route (live OSRM)")]
    d.table([["Endpoint", "n", "Mean (ms)", "Median (ms)", "95th percentile (ms)"]] + [[n, str(lat(k)["n"]), f"{lat(k)['mean_ms']:.1f}", f"{lat(k)['median_ms']:.1f}", f"{lat(k)['p95_ms']:.1f}"] for k, n in keys],
            "API response times (server and client on 127.0.0.1, one client, sequential calls)", widths=[0.42, 0.07, 0.15, 0.15, 0.21], font=9.5, align=["l", "c", "c", "c", "c"])
    if not getattr(d, "report", False):
        d.figure(CHARTS / "07_api_latency.png", "Median and 95th-percentile response time per endpoint", width=4.4)
    w1, w5 = AP["websocket"]["one_viewer_post_to_receive"], AP["websocket"]["five_viewers_post_to_all_received"]
    d.p(f"Every call except log-in and route planning answers within a few tens of milliseconds. The bcrypt log-in takes about {lat('POST /api/auth/login (bcrypt)')['median_ms']:.0f} ms, which is intended, and a route plan about "
        f"{lat('POST /api/routes/plan (live OSRM + 467-district scoring)')['median_ms'] / 1000:.1f} s because it waits for the public OSRM server. The time from a location being posted to a guardian's page receiving it over the WebSocket was "
        f"{w1['mean_ms']:.1f} ms on average for one viewer (95th percentile {w1['p95_ms']:.1f} ms) and {w5['mean_ms']:.1f} ms until all five of five viewers had it (95th percentile {w5['p95_ms']:.1f} ms), 30 trials each. "
        "**The time to deliver an alert by Telegram or e-mail was not measured**, because no credentials are configured; with real channels the start-SOS request would wait for each guardian's send in turn, and `send_email` is a blocking call inside an asynchronous route. "
        "No load test with many concurrent users was run.")

    d.h3("Access control and input handling")
    ac, ih = AP["access_control"], AP["input_handling"]
    d.table([["Probe", "Result"],
             ["No token on guardians, SOS start, AI and route planning", f"HTTP {ac['no token: GET /api/guardians']} on all four"],
             ["Forged or tampered JWT", f"HTTP {ac['forged token: GET /api/auth/me']}"],
             ["User B reads, pushes to, cancels, lists evidence of or uploads to user A's session", "HTTP 404 on all five"],
             ["User B edits or deletes user A's guardian; B's own list", f"HTTP 404 on both; B sees {ac['user B sees A guardians in own list (count)']} guardians"],
             ["Public tracking page with a wrong / the right token", f"HTTP {ac['public track with wrong token']} / {ac['public track with right token']}"],
             ["Stored evidence file requested with no token", f"HTTP {ac['GET stored evidence file with no token']} (file name needs the 16-hex hash prefix; a guessed name gives HTTP {ac['guessing evidence file with session id only']})"],
             ["25 consecutive wrong passwords", "all HTTP 401, no lockout or rate limit"],
             ["Password of six characters, \"aaaaaa\"", "accepted: the only rule is a minimum length of six"],
             ["Location push after cancel", f"HTTP {ih['location push after cancel']} (correct)"],
             ["Tracking page after cancel", f"HTTP {ih['track page after cancel (still readable)']} with the whole trail ({ih['track page exposes path points']} points); there is no expiry"],
             ["Evidence kind video; empty file", f"HTTP {ih['evidence: kind=video']} on both"]],
            "Access-control and input probes against the live API", widths=[0.55, 0.45], font=9.5)
    ei = AP["evidence_integrity"]
    d.p(f"**Evidence integrity.** The hash is computed on the server when the file arrives. Recomputing it from the stored file gives the same 64-character value, and flipping one bit of the stored file changes it; hashing 1 MB takes about {ei['sha256_1MB_ms']:.1f} ms. "
        "There is no verification endpoint, and the hash is stored in the same database as the file path, so tampering is detected only if someone recomputes and compares.")

    d.h3("SafePhrase matcher")
    bs = SP["by_sensitivity"]
    d.table([["Sensitivity (share of words needed)", "Recall on 24 phrase transcripts", "False triggers on 80 ordinary-speech checks"]] +
            [[f"{s} ({int(SP['thresholds'][s] * 100)}%)", f"{bs[s]['triggered']}/{bs[s]['positive_transcripts']} = {pc(bs[s]['recall'])}", f"{bs[s]['false_triggers']}/{bs[s]['negative_checks']} = {pc(bs[s]['false_trigger_rate'])}"] for s in ("Low", "Medium", "High", "Ultra")],
            "The product's SafePhrase matcher on written transcripts", widths=[0.34, 0.33, 0.33], font=10, align=["l", "c", "c"])
    if not getattr(d, "report", False):
        d.figure(CHARTS / "08_safephrase_sensitivity.png", "Recall and false triggers by sensitivity level", width=3.9)
    d.p(f"The matcher in `frontend/src/lib/safephrase.ts` was run unchanged on hand-written transcripts of two phrases (\"help me sheguard\" and \"please call my brother now\"): exact, embedded in a sentence, one word dropped, one word misheard and reordered, "
        f"plus 40 ordinary sentences. **No audio and no speech recogniser were involved**, so the accuracy of Chrome's recogniser on the phrase was not measured. Exact and embedded phrases trigger at every level (10 of 10). At the default Medium level the recall is "
        f"{pc(bs['Medium']['recall'])}, because for a three-word phrase one missing word (2 of 3 = 0.67) is below 0.85, so Medium behaves like Low. Ultra finds all 24 but also fires on sentences such as \"can you help me with my homework\" and \"tell me about sheguard\" "
        f"({bs['Ultra']['false_triggers']} of 80). A match costs {SP['match_microseconds']:.1f} microseconds.")

    d.h3("AI safety assistant")
    d.p(f"Ten fixed prompts (five general, three emergencies, two off-topic) were sent once each through `POST /api/ai/ask`. **{AS['answered']} of {AS['prompts']} were answered.** All {AS['failed']} returned HTTP 502 because Google replied with error 429 (quota exceeded). "
        "Earlier in the same run the first two calls returned HTTP 500 after a 20 s read timeout and one returned a 503 \"high demand\" error from Google. The questions the evaluation was designed to answer, whether the first line of an emergency answer points to SOS or emergency "
        "services as the system prompt demands and whether answers stay under 150 words, **could therefore not be measured**. The endpoint, its error mapping and its login check are covered by the stubbed tests only.")
    d.p("The end-to-end flow was also executed in the browser as shown in the output screens: registration, guardians, route planning, SOS with a moving position, evidence, the guardian's live page and hold-to-cancel; and the earlier `scripts/smoke_test.py` passes all 12 live steps (the Gemini step only warns).")


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("The base paper [1] (SafeRoutes, IEEE Access 2024) clusters regions for women's safety from public Indian data: 2001 and 2011 district population, the 2013 IPC crimes against women, literacy, per-capita expenditure, police strength and forest cover. "
        "After imputation, scaling and a Pearson and Spearman correlation analysis it applies K-Means and Gaussian mixture models, finds that three to four clusters suit its data, scores clusters against \"dummy\" data from globally safe cities and designs a cab-service integration with a 1.96x safety buffer and "
        "deviation alerts. Its results are largely \"anticipated\": correlation matrices and cluster-selection tables, no accuracy figures and no evaluation of the cab integration. SHEGUARD adopts the district-clustering idea and the safe-route guidance and adds a full emergency workflow. "
        "**The two works use different data, different numbers of features and different sizes, so their numbers cannot be compared and no claim of being better is made.**")
    d.table([["Measure", "Base paper [1] (as printed in its tables)", "SHEGUARD"],
             ["Features clustered", "Many (crime, population, literacy, expenditure, police, forest cover)", "One (average crimes per year)"],
             ["Data year", "IPC 2013 and census data", "District crimes 2001-2012"],
             ["Number of districts", "Not stated", "467 (of 827 entries)"],
             ["Algorithms compared", "K-Means, Gaussian mixture, hierarchical (Ward)", "K-Means in the product; Gaussian mixture and Ward only in this project's study"],
             ["Preferred number of clusters", "3-4", "3 (design choice; k = 4 scores better)"],
             ["Silhouette at k = 3", "0.416 (Table 3)", f"{REP['silhouette']:.3f}"],
             ["Davies-Bouldin at k = 3", "0.970 (Table 5)", f"{REP['davies_bouldin']:.3f}"],
             ["Calinski-Harabasz at k = 3", "221.0 (Table 4)", f"{REP['calinski_harabasz']:.1f}"],
             ["Travel integration", "Cab vendors, deviation alerts (designed, not evaluated)", "OSRM alternatives scored by risk (implemented, 16 pairs scored)"],
             ["Emergency features", "None", "SOS, SafePhrase, live guardian link, hash-stamped evidence, assistant (implemented; delivery channels and assistant not verified live)"]],
            "SHEGUARD and the base paper", widths=[0.24, 0.4, 0.36], font=9)
    d.p("The paper's silhouette column is headed \"Explained Variance\" and its Figure 11 shows silhouette values near 0.25-0.31, which differ from Table 3; the table values are quoted as printed. SHEGUARD's indices are higher because a single count "
        "is inherently easier to separate into groups than a multi-feature space, which is not evidence of a better safety model. What SHEGUARD lacks compared with the paper: population and per-capita normalisation, police-presence and socio-economic features, a "
        "cluster-selection analysis inside the product and cab-vendor deviation alerts.")
    d.p("The other papers read for this project give context rather than comparable numbers. The IoT review [2] (2016-2022 studies) found that pulse-rate and pressure sensors dominate wearable devices and that systems with automatic activation and little human interaction are still needed, "
        "which motivates SafePhrase and one-tap SOS. The ESP32-camera application [6] reports SOS delivery in 4-6 seconds and 93% accuracy on crime-zone classification of pre-defined test locations, on its own hardware and data; SHEGUARD's alert delivery was not measured. "
        "The batch survey entries [3], [4] and [5] could not be retrieved, so no result from them is used.")


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.p("The following are real exchanges with the running application on 26 October 2026 (coordinates and identifiers as stored; long coordinate lists are omitted).")
    d.table([["Input", "Output"],
             ["Hyderabad (17.385, 78.4867) to Vijayawada (16.5062, 80.648), `POST /api/routes/plan`", "One route, 273.5 km, 217 min, risk score 4.246 by day; 91 low, 0 medium and 392 high samples; recommended"],
             ["One tap on SOS at (17.385, 78.4867), trigger manual", "Session 44 with a 32-character share token and tracking URL; delivery report for three guardians: Telegram false, e-mail false"],
             ["Four location updates while moving north-east, then (17.412, 78.512)", "Seven stored points in the trail; last position and last-update time kept on the session"],
             ["Photo and a 3-second audio clip uploaded", "Two evidence rows with 64-character SHA-256 values and the capture location and time"],
             ["Guardian opens the tracking link", "Public read-only payload with name, status, last position and the full path"],
             ["Hold the cancel button for three seconds", "Status cancelled, end time set, WebSocket message `cancelled` pushed to the guardian page"],
             ["Question to the assistant", "HTTP 502 with Google quota error 429; the interface shows the unavailable message"]],
            "Sample inputs and outputs", widths=[0.45, 0.55], font=9.5)
    d.code('POST /api/routes/plan   {"origin_lat": 17.385, "origin_lng": 78.4867, "dest_lat": 16.5062, "dest_lng": 80.648}\n'
           '{"routes": [{"index": 0, "distance_m": 273495.9, "duration_s": 13023.3, "risk_score": 4.246,\n'
           '             "risk_tiers": {"low": 91, "medium": 0, "high": 392}, "is_night": false,\n'
           '             "recommended": true, "coordinates": [[17.385, 78.4867], ... 3857 points]}],\n'
           ' "safest_index": 0}', "A real route-plan response (coordinates shortened)")
    d.code('POST /api/sos/start   {"lat": 17.385, "lng": 78.4867, "trigger": "manual"}\n'
           '{"session_id": 44, "share_token": "d21e7f4cf5e04f11addfa109a3721d23",\n'
           ' "tracking_url": "http://localhost:5107/track/d21e7f4cf5e04f11addfa109a3721d23",\n'
           ' "started_at": "2026-10-26T14:36:06.208981",\n'
           ' "delivery": [{"guardian": "Meena Reddy (mother)", "telegram": false, "email": false},\n'
           '              {"guardian": "Karthik Reddy (brother)", "telegram": false, "email": false},\n'
           '              {"guardian": "Divya Rao (friend)", "telegram": false, "email": false}]}', "The start-SOS response of the captured session (read back from the database and the screenshot)")
    d.code('GET /api/track/d21e7f4cf5e04f11addfa109a3721d23        (no login)\n'
           '{"status": "cancelled", "trigger": "manual", "started_at": "2026-10-26T14:36:06", "ended_at": "2026-10-26T14:36:55",\n'
           ' "last_lat": 17.412, "last_lng": 78.512, "last_update_at": "2026-10-26T14:36:44", "user_name": "Asha Reddy",\n'
           ' "path": [{"lat": 17.385, "lng": 78.4867}, {"lat": 17.385, "lng": 78.4867}, {"lat": 17.3895, "lng": 78.4905},\n'
           '          {"lat": 17.395, "lng": 78.496}, {"lat": 17.401, "lng": 78.502}, {"lat": 17.4075, "lng": 78.5075}, {"lat": 17.412, "lng": 78.512}]}',
           "The guardian's tracking payload after the session was cancelled (timestamps rounded to seconds)")
    d.code('GET /api/sos/44/evidence\n'
           '[{"id": 77, "kind": "photo", "sha256": "894273f4fafd77e1b2a310395099313a0b15b6f2a520edec769b0ac36d191dd7", "lat": 17.385, "lng": 78.4867},\n'
           ' {"id": 78, "kind": "audio", "sha256": "aa9433e57325c5438bcb36665386ee822892d42d8fd91054d6ecbdc13f0d9bc1", "lat": 17.385, "lng": 78.4867}]',
           "The two evidence records of the session (capture times omitted)")


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("Where it works")
    w1 = AP["websocket"]["one_viewer_post_to_receive"]
    d.bullets([
        "The emergency workflow runs end to end in a browser: register, add guardians, start an SOS, stream a moving position, save hashed evidence, let a guardian follow without an account and cancel with a deliberate three-second hold; the guardian's page receives location and cancel messages in "
        f"about {w1['mean_ms']:.0f} ms on this machine.",
        "User data are separated: every probe of another user's session, evidence or guardians returned 404, unauthenticated calls returned 401, and 51 automated tests pass.",
        "The risk model is reproducible (shipped numbers re-created exactly) and the route scorer ranks an all-high-risk route above an all-low-risk route (5.0 against 1.0).",
        f"Evidence hashing detects a single flipped bit, and uploads of 100 KB to 5 MB take {lat('POST /api/sos/{id}/evidence (100 KB)')['median_ms']:.0f} to {lat('POST /api/sos/{id}/evidence (5 MB)')['median_ms']:.0f} ms (median).",
        "The interface is honest about its limits: the landing page and route screens say that risk comes from 2001-2012 district data, and failures (no alert channel, assistant unavailable) are shown as such.",
    ])
    d.h3("Where it fails or is weak")
    d.table([["Observation", "Cause", "Effect / handling"],
             [f"Hyderabad is {CC['nearest_district_km']['Hyderabad']:.0f} km, Warangal {CC['nearest_district_km']['Warangal']:.0f} km, Kolkata {CC['nearest_district_km']['Kolkata']:.0f} km and Lucknow {CC['nearest_district_km']['Lucknow']:.0f} km from the nearest district in the table",
              "Only 56.5% of districts were geocoded; Uttar Pradesh, West Bengal and Delhi have none; the scorer has no distance limit", "Routes through these cities are scored with a district hundreds of kilometres away; extend geocoding and cap the distance"],
             ["The night multiplier never changes which route is recommended (16 of 16 pairs)", "The same factor 1.6 multiplies every sampled point of every route", "Night only changes the displayed number; use time-dependent tier weights or night-specific data"],
             ["37.5% of the trips tested returned a single route", "OSRM demo server returns alternatives only when they exist", "Nothing to compare; add waypoints or another routing engine"],
             ["Guardians reached: 0 of 3 in every captured emergency", "TELEGRAM_BOT_TOKEN, GMAIL_ADDRESS and GMAIL_APP_PASSWORD are empty", "Only the in-app link works; alert delivery is unverified, and `send_email` blocks the event loop"],
             ["The AI assistant answered 0 of 10 prompts", "Gemini quota exhausted (429), 503 under load, and a 20 s read timeout that returns 500", "Interface shows a friendly message; map timeouts to 502 and add retries or a fallback"],
             [f"SafePhrase Medium recall {pc(bs_rec('Medium'))}; Ultra false triggers {pc(bs_fp('Ultra'))}", "Word-window rule: one wrong word fails a three-word phrase at Medium; 60% of words is too loose", "Use phrases of five or more words, test with real speech, add a confirmation step"],
             ["Stored evidence is retrievable by URL with no login; an .html upload is served as text/html; no size limit", "Static mount of the evidence folder and the client's extension is kept", "Serve files through an authorised route, force a safe content type, cap upload size"],
             ["Impossible coordinates, free-text trigger and unknown WebSocket tokens are accepted; no login lockout", "No range validation, no rate limiting", "Add schema validation and throttling"],
             ["A district's tier follows raw counts dominated by domestic-violence reports (40% of the counted total)", "Single feature, no population normalisation", "Use rates per population and street-level categories"]],
            "Failure and weakness analysis", widths=[0.34, 0.33, 0.33], font=8.5)


def bs_rec(level):
    return SP["by_sensitivity"][level]["recall"]


def bs_fp(level):
    return SP["by_sensitivity"][level]["false_trigger_rate"]


def sec_results_limits(d):
    d.h2("Limits of the Results")
    d.bullets([
        "**No ground truth.** The cluster indices (silhouette 0.58, Davies-Bouldin 0.53) measure separation of one number, not agreement with real danger; no train/test split exists and no field validation was done.",
        "**Old, coarse data.** The district file covers 2001-2012, counts are not per head of population, 56.5% of districts are geocoded and several large states are missing.",
        "**Written transcripts, not speech.** The SafePhrase figures test the matching rule on hand-made text; the recogniser was not measured.",
        "**Injected position and stand-in media.** The screenshots use a position set by the test script, a test-tone microphone and the application's own screenshot as the photograph; no phone, GPS or camera was used.",
        "**Unverified channels.** Alert delivery by Telegram and e-mail and the Gemini assistant could not be demonstrated returning results in this run.",
        "**Small single-machine measurements.** Timings come from one desktop with sequential calls (5 to 30 per endpoint), one client and no concurrent load; no user study was carried out.",
        "**No numeric comparison with the base paper** is possible, as explained in the section Comparison with the Base Paper.",
    ])


def sec_objectives(d):
    d.h2("Objectives Against Outcomes")
    d.table([["Objective", "Outcome", "Evidence"],
             ["1. Provide Safe Route guidance using available safety information", "Partly achieved", "Working OSRM + district-risk scoring with a heat layer and route cards, but the data are 2001-2012 counts with 56.5% geocoding and gaps around Hyderabad, Kolkata and Lucknow; night factor never reorders routes; 37.5% of trips have one route"],
             ["2. Quick emergency activation through SafePhrase and Smart SOS", "Partly achieved", "One-tap SOS and hold-to-cancel work; SafePhrase matcher tested on written text only (Medium recall 54.2%, Ultra false triggers 10%); no shake, power-button or automatic trigger"],
             ["3. Share live location with trusted guardians during an emergency", "Achieved (link); delivery unverified", f"WebSocket push about {AP['websocket']['one_viewer_post_to_receive']['mean_ms']:.0f} ms, no guardian login, public tracking page; Telegram and e-mail delivery reported 0 of 3 because no credentials are configured"],
             ["4. Preserve evidence (timestamps, location, audio, images) securely", "Partly achieved", "Photo and audio saved with time, location and SHA-256 (tamper changes the hash); files retrievable by URL without login, no size limit, no verification endpoint"],
             ["5. AI-powered safety assistance using the Gemini API", "Implemented, not demonstrated", "Endpoint, system prompt and interface exist; 0 of 10 probe prompts answered (quota 429, timeout returns 500)"],
             ["6. Protect user data with role-based access and Row Level Security", "Partly achieved", "bcrypt + JWT, every query scoped to the owner (all cross-user probes 404); no database RLS (SQLite) and no roles beyond user and token-based guardian"]],
            "Objectives against outcomes", widths=[0.34, 0.16, 0.5], font=9)
