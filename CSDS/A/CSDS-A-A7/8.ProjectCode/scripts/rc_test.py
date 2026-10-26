"""Chapter 7 content: system testing (SHEGUARD). Counts come from tests/ (experiments/study/pytest.xml) and the measurements in experiments/study/."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from doc_common import CHARTS, STUDY, study

A = study("api_metrics.json")
S = study("safephrase.json")
M = study("metrics.json")
AS = None
try:
    AS = study("assistant.json")
except Exception:  # noqa: BLE001
    pass

AREAS = [("Authentication and health", ("health", "register", "login_ok", "password", "me_requires", "expired")), ("Guardians", ("guardian",)),
         ("Risk data", ("risk_areas", "tier_counts")), ("Route planning", ("route_plan",)),
         ("SOS lifecycle", ("sos_", "location", "cancel", "sessions_are")), ("Guardian view and WebSocket", ("tracking", "websocket_pushes")),
         ("Evidence", ("evidence", "audio_kind", "flipped")), ("AI endpoint", ("ai_", "gemini_without")), ("Places search", ("places",))]


def _cases():
    root = ET.parse(STUDY / "pytest.xml").getroot()
    return [(tc.get("classname").split(".")[-1], tc.get("name"), any(c.tag == "skipped" for c in tc)) for tc in root.iter("testcase")]


def _counts():
    cases = _cases()
    api_pass = [c for c in cases if c[0] == "test_api" and not c[2]]
    unit = [c for c in cases if c[0] == "test_scoring"]
    gaps = [c for c in cases if c[2]]
    areas = {a: 0 for a, _ in AREAS}
    for _, name, _ in api_pass:
        for a, keys in AREAS:
            if any(k in name for k in keys):
                areas[a] += 1
                break
        else:
            raise SystemExit("unclassified test " + name)
    return cases, api_pass, unit, gaps, areas


def _suite_seconds():
    root = ET.parse(STUDY / "pytest.xml").getroot()
    ts = root.find("testsuite") if root.tag != "testsuite" else root
    return float(ts.get("time"))


def fig(d, name, caption, width=4.8):
    p = CHARTS / name
    if p.exists():
        d.figure(p, caption, width=width)
    else:
        print("MISSING FIGURE", p)


def sec_test_strategy(d):
    cases, api_pass, unit, gaps, areas = _counts()
    n = len(cases)
    d.h2("Testing Strategy")
    d.paras(
        "SHEGUARD is checked at five levels: automated tests of the back end and the scoring logic, measurements of the risk model and the route scorer on the project's own data, probes against the running API for "
        "latency, access control and input handling, an offline evaluation of the SafePhrase matcher, and a scripted walk-through of the whole product in a real browser. The levels answer different questions. "
        "The automated tests ask whether the code behaves as designed, deterministically and without any outside service. The measurements ask how consistent and how well covered the risk model is. The probes ask whether "
        "one user can reach another's emergency data and how quickly the server answers. The matcher evaluation asks how often a spoken phrase would be recognised and how often ordinary speech would raise a false alarm. "
        "The walk-through asks whether a person can use the product from registration to cancelling an emergency.",
        f"The suite is written with pytest and FastAPI's test client. Every run points `DATABASE_URL` at a throw-away SQLite file, copies the district table into a temporary data folder, redirects evidence uploads to a temporary "
        "folder, and replaces the four outside services (OSRM, Gemini, Telegram, Gmail) with stubs, so it needs no network and no key. Passwords are really hashed, tokens are really signed, the 467-district table is "
        f"really loaded and the real scorer runs. The suite contains **{n} tests: {len(api_pass) + len(unit)} pass and {len(gaps)} are expected failures (strict xfail)** that assert the behaviour a hardened system should have and "
        f"fail today, so that known gaps are reported rather than hidden. A full run takes about {_suite_seconds():.0f} seconds. The suite was written during this documentation run, because the project shipped with a smoke "
        "script only.")


def sec_unit(d):
    cases, api_pass, unit, gaps, areas = _counts()
    d.h2("Unit Testing")
    d.table([["Test (tests/test_scoring.py)", "What it checks"],
             ["test_haversine_known_distance", "Delhi to Jaipur is about 235 km (tolerance 8 km); identical points give 0"],
             ["test_nearest_district_picks_closest", "The nearest of three districts is returned for two query points"],
             ["test_tier_weights_order_scores", "A route in low, medium and high districts scores exactly 1.0, 2.5 and 5.0 by day"],
             ["test_night_multiplies_every_score_by_the_same_factor", "At night the score is 1.6 times the daytime score for all three tiers"],
             ["test_night_never_reorders_two_routes", "A mixed route and a medium route keep the same order by day and by night"],
             ["test_empty_route_scores_zero", "A route with no coordinates scores 0.0"],
             ["test_no_districts_defaults_to_medium", "With no district rows every sample counts as medium (score 2.5)"],
             ["test_nearest_district_has_no_distance_limit", "A point more than 1,000 km from every district is still assigned one (documents the coverage weakness)"],
             ["test_night_window_boundaries_in_utc", "15:00 UTC is night, 14:59 and 00:00 UTC are not"],
             ["test_shipped_model_artifact_loads_and_has_three_tiers", "`risk_model.joblib` loads, has three clusters and the tier names low, medium, high"],
             ["test_district_table_is_consistent", "467 rows; risk scores in 0-100; mean crime rate rises from low to medium to high; coordinates inside India"],
             ["test_tiers_are_threshold_bands_on_crime_rate", "The highest low-tier rate is below the lowest medium-tier rate, and likewise for medium and high"]],
            f"Unit tests ({len(unit)})", widths=[0.42, 0.58], font=9)
    d.p("These twelve tests cover the pure logic that must be exact: the distance formula, the nearest-district lookup, the tier weights, the night factor and its window, the degenerate inputs, and the artefacts of the "
        "area-risk model. Two of them are deliberately uncomfortable: they pin down that the night factor cannot reorder routes and that the lookup has no distance limit, so the documents and the tests say the same thing.")


def sec_integration(d):
    cases, api_pass, unit, gaps, areas = _counts()
    d.h2("Integration Testing")
    d.p(f"The {len(api_pass)} passing tests in `tests/test_api.py` call the application through its HTTP and WebSocket interface, so routing, validation, authentication, the database and the services are exercised together.")
    descr = {
        "Authentication and health": "Health endpoint; registration returns a token; duplicate e-mail refused (400); invalid payloads give 422; login with a wrong password or unknown e-mail gives 401; the password is stored as a bcrypt hash; protected routes need a valid token; a forged or expired token is refused",
        "Guardians": "Create, list, update and delete; a second user sees none of them and cannot edit or delete them (404); no token gives 401",
        "Risk data": "`/api/risk/areas` returns the 467 districts with the three tiers and scores in 0-100, and the tier counts match the published metrics (278 / 148 / 41)",
        "Route planning": "Alternatives are sorted by score and exactly the first is recommended; no token gives 401; an OSRM failure gives 502; an empty result gives 404",
        "SOS lifecycle": "Session and 32-character token created; guardians are alerted on every configured channel and the delivery report is correct; pings are stored in order; cancel stops further updates (400); sessions are private to their owner; missing coordinates give 422",
        "Guardian view and WebSocket": "The public tracking page shows the owner and the last position; an unknown token gives 404; a WebSocket viewer receives a `location` message and then `cancelled`",
        "Evidence": "SHA-256 of the upload equals the hash of the stored file; one flipped bit changes the hash; photo and audio accepted, other kinds rejected; empty file rejected; evidence count on the session; another user's session gives 404",
        "AI endpoint": "Answer returned through a stub; login and a question are required; a provider error gives 502; a missing key raises a clear message",
        "Places search": "Needs login; a one-character query is refused (422)",
    }
    d.table([["Area", "Tests", "What is checked"]] + [[a, str(areas[a]), descr[a]] for a, _ in AREAS],
            f"Integration tests ({len(api_pass)} passing)", widths=[0.2, 0.08, 0.72], font=8.5)
    d.table([["Group", "Tests", "Passed", "Expected failures"],
             ["Unit (test_scoring.py)", str(len(unit)), str(len(unit)), "0"],
             ["Integration (test_api.py)", str(len(api_pass) + len(gaps)), str(len(api_pass)), str(len(gaps))],
             ["**Total**", f"**{len(cases)}**", f"**{len(unit) + len(api_pass)}**", f"**{len(gaps)}**"]],
            "Automated test inventory (pytest, 26 October 2026)", widths=[0.4, 0.2, 0.2, 0.2], font=10, align=["l", "c", "c", "c"])
    fig(d, "11_tests_by_area.png", "Automated tests by area", width=4.6)
    d.p("The web front end is exercised only by the browser walk-through of the next section. It is covered by the TypeScript compiler (`npm run build` runs `tsc --noEmit` and passes) but by no automated user-interface tests.")


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("Two functional runs were made against the live application on 26 October 2026. The first is the project's own `scripts/smoke_test.py`, which drives the real API through twelve steps with real external calls "
        "(OSRM for the route, Gemini for the assistant). The second is a scripted browser walk-through (Playwright driving the installed Chrome at 1440 x 900) that registers an account through the interface, "
        "adds guardians, plans routes, starts a real emergency with live position updates, uploads evidence, opens the guardian's page in a second, logged-out browser context and cancels; the screenshots in Chapter 8 are its captures. "
        "The browser's geolocation is set by the test script to fixed city centres and its microphone is Chrome's built-in test tone, so position and audio are injected, not taken from a phone.")
    d.table([["No.", "Smoke-test step", "Observed"],
             ["1", "Health check", "Pass"],
             ["2", "Register a new user", "Pass: token returned"],
             ["3", "Log in", "Pass"],
             ["4", "Add a guardian", "Pass"],
             ["5", "Read risk areas", "Pass: 467 districts"],
             ["6", "Plan a route (Hyderabad to Secunderabad, real OSRM)", "Pass: one route returned, risk score 1.0"],
             ["7", "Start SOS", "Pass: session and share token; delivery report telegram false, email false (no credentials configured)"],
             ["8", "Push a location update", "Pass"],
             ["9", "Upload photo evidence", "Pass: 64-character SHA-256"],
             ["10", "Read the public tracking page", "Pass: two location points"],
             ["11", "Cancel the SOS and re-read the tracking page", "Pass: status cancelled"],
             ["12", "Ask the AI assistant", "Warning, not a pass: HTTP 500 (read timeout); later probes returned 502 with Google quota error 429"]],
            "Smoke test of the live API", widths=[0.07, 0.43, 0.5], font=9)
    d.table([["No.", "Requirement", "Test performed in the browser", "Observed"],
             ["F1", "Register and sign in", "Fill the registration form, accept the terms, create the account", "Pass: lands on the dashboard"],
             ["F2", "Trusted guardians", "Add three guardians (name, phone, e-mail, Telegram ID) on the profile page", "Pass: Trusted guardians (3) listed; the dashboard shows 3 added"],
             ["F3", "Area risk at the user's position", "Open the dashboard with the position set to Delhi", "Pass: tile reads Medium - GURGAON (Delhi has no district of its own in the table)"],
             ["F4", "Place search", "Type Jaipur on Safe routes", "Pass: suggestions from Nominatim"],
             ["F5", "Safe route with alternatives", "Select Jaipur from Delhi", "Pass: two routes, 274.1 km / 204 min and 299.5 km / 205 min, both labelled HIGH risk, risk circles drawn"],
             ["F6", "Single-route case", "Plan Hyderabad to Vijayawada", "Pass: one route, 269.1 km / 213 min, HIGH risk (20 / 0 / 80 % low / medium / high samples)"],
             ["F7", "AI assistant", "Send a safety question", "Fail by environment: reply \"The AI assistant is unavailable right now\" (Gemini quota error); the route advice panel shows the same message"],
             ["F8", "SafePhrase settings", "Open SafePhrase, add a second cover phrase", "Pass: phrase listed with a SHA-256 fingerprint, sensitivity buttons shown, two active phrases"],
             ["F9", "Start an emergency", "Press the SOS button", "Pass: Guardian tracking active, tracking link, live map; 0 of 3 guardians reached because no Telegram or Gmail credentials are configured"],
             ["F10", "Evidence", "Upload a photo, record a 3-second audio clip", "Pass: two rows with SHA-256 prefixes and times"],
             ["F11", "Live tracking", "Open the link in a clean browser context while the position moves", "Pass: the guardian page shows the owner's name, status active and a growing path"],
             ["F12", "Hold to cancel", "Hold the cancel button for three seconds", "Pass: the capture shows the progress ring part-way (\"Keep holding...\"), then the dashboard with the event in recent activity; the guardian page reads \"has ended the emergency\""]],
            "Functional test cases (browser walk-through)", widths=[0.06, 0.2, 0.3, 0.44], font=8)
    d.p("Every step passed except the assistant, which could not be demonstrated because the shared API key had exhausted its quota, and the delivery of alerts, which was not testable without credentials. "
        "The walk-through therefore proves that the session, the tracking link, the live path, the evidence list and the cancellation work from the interface, and does not prove that a guardian is actually notified.")
    if AS is not None:
        sm = AS["summary"]
        d.p(f"A separate probe of the assistant with {sm['prompts']} fixed prompts (five general, three emergency, two off-topic; `scripts/assistant_eval.py`) answered {sm['answered']} of {sm['prompts']}; "
            f"all {sm['failed']} failed with HTTP 502 (Google quota error 429). Whether the emergency prompts get an SOS-first reply, as the system prompt requires, was therefore not measured.")


def sec_security_test(d):
    ac = A["access_control"]
    ih = A["input_handling"]
    d.h2("Security Testing")
    d.p("Access control was probed against the running server with two freshly registered users, A and B (`scripts/measure_api.py`), and the same rules are asserted by the automated tests. The expected result in every case is a refusal.")
    rows = [["No token: guardians, SOS start, AI, route plan", f"{ac['no token: GET /api/guardians']} / {ac['no token: POST /api/sos/start']} / {ac['no token: POST /api/ai/ask']} / {ac['no token: POST /api/routes/plan']}", "Refused"],
            ["Forged token; token with its signature changed", f"{ac['forged token: GET /api/auth/me']}; {ac['tampered signature: GET /api/auth/me']}", "Refused"],
            ["User B reads, pushes a location to, cancels A's session", f"{ac['user B reads user A session']} / {ac['user B pushes location to A session']} / {ac['user B cancels A session']}", "Refused"],
            ["User B lists or uploads evidence on A's session", f"{ac['user B lists A evidence']} / {ac['user B uploads evidence to A session']}", "Refused"],
            ["User B edits or deletes A's guardian", f"{ac['user B edits A guardian']} / {ac['user B deletes A guardian']}", "Refused"],
            ["User B's own guardian list after A added guardians", f"{ac['user B sees A guardians in own list (count)']} entries", "Isolated"],
            ["Guardian tracking page with a wrong token", str(ac["public track with wrong token"]), "Refused"],
            ["Guardian tracking page with the right token (no login)", str(ac["public track with right token"]), "Allowed by design"],
            ["District list without login", str(ac["public GET /api/risk/areas without login"]), "Public by design"],
            ["Stored evidence file fetched with no token", str(ac["GET stored evidence file with no token"]), "**Allowed: finding**"],
            ["Evidence file name guessed from the session id alone", str(ac["guessing evidence file with session id only"]), "Refused (needs the hash prefix)"]]
    d.table([["Probe", "HTTP status", "Result"]] + rows, "Access-control probes on the live API", widths=[0.5, 0.25, 0.25], font=9)
    d.p("Ownership checks hold in every probe, and the guardian link behaves as designed. The weaknesses are elsewhere.")
    d.h3("Documented defects (expected-failure tests)")
    big = ih["evidence: 20 MB upload (accepted = no size limit)"]
    d.table([["Test", "Desired behaviour", "Observed today"],
             ["test_gemini_timeout_should_be_502", "A provider timeout is reported as 502", "The read timeout is not caught: HTTP 500 after about 20 s (seen live on the first two assistant calls)"],
             ["test_sos_rejects_impossible_latitude", "Reject latitude 999", f"Accepted (HTTP {ih['sos/start: latitude 999 (accepted = no range check)']})"],
             ["test_sos_rejects_unknown_trigger", "Only `manual` or `safephrase`", "Any string is stored"],
             ["test_websocket_rejects_unknown_token", "Refuse a token that matches no session", f"Connection {A['websocket']['unknown_token_connection']}"],
             ["test_evidence_has_a_size_limit", "Refuse very large uploads", f"A 20 MB file was accepted (HTTP {big['status']}) in {big['seconds']} s"],
             ["test_evidence_files_not_served_as_html", "Never serve uploads as HTML", "An `.html` upload labelled photo is served back as `text/html` from the API origin"]],
            "The six known defects, asserted as expected failures", widths=[0.34, 0.28, 0.38], font=9)
    d.h3("Further findings")
    d.bullets([
        "Login has no lock-out: 25 consecutive wrong passwords all returned 401 and none 429.",
        "A six-character password such as `aaaaaa` is accepted; the only rule is a minimum length of six.",
        f"After cancellation the tracking page still returns the full location trail ({A['input_handling']['track page exposes path points']} points in the probe) and never expires, although its 404 message says \"expired\".",
        "Stored evidence is retrievable without a token by anyone who has the link; CORS allows every origin; the JWT secret in use is not the development default.",
        "Evidence integrity: the stored hash matches the stored file and one flipped bit changes the hash, but there is no verification endpoint and the hash sits in the same database as the file path.",
        "Location push after cancellation is correctly refused (400).",
    ])
    d.p("**Not tested:** penetration testing, cross-site scripting in the front end, brute-force limits beyond the 25 attempts, token replay, HTTPS deployment and the Telegram and Gmail channels.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.p("The SafePhrase matcher is the only component with a pass-or-fail behaviour that is not covered by the API tests. Its real TypeScript was transpiled and run unchanged (`scripts/safephrase_eval.mjs`) on hand-written transcripts: "
        "24 that should trigger (two phrases, five kinds of utterance) and 40 ordinary sentences checked against both phrases (80 negative checks). **No audio and no speech recogniser were involved**, so the figures describe the matching rule only; "
        "how well Chrome's recogniser hears \"sheguard\" was not measured.")
    rows = []
    for s in ["Low", "Medium", "High", "Ultra"]:
        b = S["by_sensitivity"][s]
        rows.append([f"{s} ({int(S['thresholds'][s] * 100)} % of words)", f"{b['triggered']}/{b['positive_transcripts']} = {b['recall'] * 100:.1f} %", f"{b['false_triggers']}/{b['negative_checks']} = {b['false_trigger_rate'] * 100:.1f} %"])
    d.table([["Sensitivity", "Recall on 24 phrase transcripts", "False triggers on 80 ordinary-speech checks"]] + rows, "SafePhrase matcher on written transcripts", widths=[0.3, 0.35, 0.35], font=9.5, align=["l", "c", "c"])
    cats = ["exact", "embedded", "one_word_dropped", "one_word_misheard", "reordered"]
    names = {"exact": "Exact phrase", "embedded": "Phrase inside a sentence", "one_word_dropped": "One word dropped", "one_word_misheard": "One word misheard", "reordered": "Words reordered"}
    d.table([["Kind of transcript"] + ["Low", "Medium", "High", "Ultra"]] + [[names[c]] + [f"{S['by_sensitivity'][s]['by_category'][c]['hit']}/{S['by_sensitivity'][s]['by_category'][c]['n']}" for s in ["Low", "Medium", "High", "Ultra"]] for c in cats],
            "Triggered transcripts per kind and sensitivity", widths=[0.36, 0.16, 0.16, 0.16, 0.16], font=9.5, align=["l", "c", "c", "c", "c"])
    d.p(f"Exact and embedded phrases and reordered words trigger at every level. The default, Medium (85 %), behaves exactly like Low for the three-word default phrase, because two words of three is 0.67: one misrecognised word blocks the alert "
        f"and recall is {S['by_sensitivity']['Medium']['recall'] * 100:.1f} %. Ultra (60 %) catches every test phrase but also fires on {S['by_sensitivity']['Ultra']['false_triggers']} of 80 ordinary checks, for example \"can you help me with my homework\" and \"tell me about sheguard\". "
        f"There is no setting that is both tolerant and quiet. One match costs about {S['match_microseconds']} microseconds.")
    fig(d, "08_safephrase_sensitivity.png", "SafePhrase recall and false triggers by sensitivity (written transcripts)", width=4.4)
    ih = A["input_handling"]
    d.table([["Case", "Behaviour observed", "Result"],
             ["Registration with a 5-character password", f"HTTP {ih['register: 5-char password']}", "Pass"],
             ["Registration with a malformed e-mail or a duplicate", f"HTTP {ih['register: bad email']} and {ih['register: duplicate email']}", "Pass"],
             ["SOS start without a latitude", f"HTTP {ih['sos/start: missing lat']}", "Pass"],
             ["SOS start with latitude 999", f"Accepted (HTTP {ih['sos/start: latitude 999 (accepted = no range check)']})", "Gap (xfail)"],
             ["Evidence of kind `video`", f"HTTP {ih['evidence: kind=video']}", "Pass"],
             ["Empty evidence file", f"HTTP {ih['evidence: empty file']}", "Pass"],
             ["Location push after the session is cancelled", f"HTTP {ih['location push after cancel']}", "Pass"],
             ["AI request with no question", f"HTTP {ih['ai/ask: empty body']}", "Pass"],
             ["Route between points with one OSRM alternative", "Six of 16 real city pairs returned a single route; it is recommended and labelled", "Pass, nothing to compare"],
             ["Route through a city far from any district", "Scored with a district up to 231.3 km away (Lucknow); Hyderabad 149.0 km", "Gap: no distance limit"],
             ["Daytime and night-time scoring", "Same order for all 16 pairs; scores differ by exactly 1.6", "As designed"],
             ["Route planning when OSRM is down", "HTTP 502 with a message", "Pass (stubbed test)"]],
            "Validation and edge cases", widths=[0.36, 0.46, 0.18], font=9)


def sec_performance(d):
    L = A["latency"]
    W = A["websocket"]
    d.h2("Performance Testing")
    d.p("Response times were measured against the live server over 127.0.0.1 with one sequential client (`scripts/measure_api.py`) on an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory and no discrete GPU, running Windows 11, "
        "with other work present on the machine, so the figures are indicative rather than a benchmark. (The address 127.0.0.1 is used because `localhost` adds about two seconds of IPv6 fallback per call on this machine.)")
    names = {"GET /api/health": "Health check", "GET /api/risk/areas (467 rows)": "District list (467 rows)", "POST /api/auth/login (bcrypt)": "Log in (bcrypt verification)",
             "GET /api/auth/me": "Current user", "POST /api/guardians": "Add a guardian", "GET /api/guardians": "List guardians",
             "POST /api/sos/start (30 guardians, no channel configured)": "Start SOS (30 guardians, no alert channel configured)", "POST /api/sos/{id}/location": "Push a location",
             "GET /api/track/{token} (public)": "Guardian tracking page", "POST /api/sos/{id}/evidence (100 KB)": "Upload evidence, 100 KB", "POST /api/sos/{id}/evidence (1 MB)": "Upload evidence, 1 MB",
             "POST /api/sos/{id}/evidence (5 MB)": "Upload evidence, 5 MB", "GET /api/sos/{id}/evidence": "List evidence", "POST /api/routes/plan (live OSRM + 467-district scoring)": "Plan a route (live OSRM call)"}
    d.table([["Request", "Runs", "Median (ms)", "95th percentile (ms)", "Max (ms)"]] + [[names[k], str(v["n"]), f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"] for k, v in L.items()],
            "API response times (live server)", widths=[0.42, 0.1, 0.15, 0.19, 0.14], font=9, align=["l", "c", "c", "c", "c"])
    fig(d, "07_api_latency.png", "API latency, median and 95th percentile (logarithmic axis)", width=4.8)
    one, five = W["one_viewer_post_to_receive"], W["five_viewers_post_to_all_received"]
    d.p(f"A location update reaches a guardian's WebSocket quickly: measured from the moment the owner's `POST` is sent to the moment the viewer receives the frame, the mean is {one['mean_ms']:.1f} ms with one viewer (median {one['median_ms']:.1f} ms, "
        f"95th percentile {one['p95_ms']:.1f} ms, maximum {one['max_ms']:.1f} ms) and {five['mean_ms']:.1f} ms until all of five viewers have it (95th percentile {five['p95_ms']:.1f} ms), over {one['n']} trials each. "
        f"Every ordinary request completes in under {-(-max(v['median_ms'] for k, v in L.items() if 'login' not in k and 'routes/plan' not in k) // 10) * 10:.0f} ms at the median except log-in, which takes about {L['POST /api/auth/login (bcrypt)']['median_ms']:.0f} ms because bcrypt is deliberately slow, and route planning, which takes a median of {L['POST /api/routes/plan (live OSRM + 467-district scoring)']['median_ms'] / 1000:.1f} s because it waits for the public OSRM server and then scores each alternative in pure Python "
        f"(about {M['route_summary']['score_one_route_ms_mean']:.0f} ms per route). Computing the SHA-256 of 1 MB takes about {A['evidence_integrity']['sha256_1MB_ms']:.1f} ms, so hashing is not the cost of an evidence upload.")
    d.p("The SOS-start figure excludes any real alert: no Telegram or Gmail credentials were configured, so the time to deliver a message to a guardian was **not measured**. With real channels the request waits for each Telegram call and each SMTP exchange in turn (10 s timeout each), "
        "and the blocking SMTP call would also stall the event loop; this is read from the code. **Not measured:** many simultaneous users, more than five viewers per session, memory use under load, a large database, the front end's load time on a phone, battery drain of continuous speech recognition or position watching, and other hardware.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user-acceptance test was carried out: no woman, guardian or other external user tried the product, and no usability or comprehension measure was collected. The browser walk-through described under functional testing was written and run "
        "by the project team; it shows that the intended flow works end to end on one machine, not that real users find it understandable, trustworthy or fast enough in a frightening situation. "
        "A field trial with consenting volunteers, on real phones and a real mobile network, with working Telegram and e-mail delivery, is the most important piece of future work. It should also measure how long it takes a guardian to notice an alert and how often a spoken phrase is "
        "recognised by the browser's recogniser in a noisy street.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "The risk model has no ground truth: silhouette 0.580 and Davies-Bouldin 0.531 describe how well one number separates into three groups, not how well the tiers predict danger on a street. No correlation with real incidents, and no population-normalised comparison, was measured.",
        "The data are district counts for 2001-2012, 56.5 % of districts were geocoded, 11 of 35 states and union territories have no district in the table (including Uttar Pradesh, West Bengal and Delhi), and the nearest district to Hyderabad is 149 km away; route scores in uncovered areas reflect a distant district.",
        "The route scorer was exercised on 16 real city pairs, of which six had no alternative route; recommended routes cost on average 3.7 extra minutes when there was a choice, and the night factor cannot change the choice at all.",
        "The SafePhrase results are on hand-written transcripts of two phrases. They say nothing about speech-recognition accuracy, accents, background noise, a locked phone or a backgrounded browser tab.",
        "The AI assistant was never observed returning an answer in this run (quota error 429, earlier 503 and a read timeout); its behaviour, including the SOS-first rule for emergencies, is untested. The Telegram and Gmail alert channels were never run with real credentials.",
        f"The {len(_cases())} automated tests use stubs for all outside services and a temporary database; there are no automated front-end tests, no load or concurrency tests beyond five WebSocket viewers, no penetration tests, no iOS Safari or screen-reader check and no test over a real phone and mobile network.",
        "Position and microphone input in the browser walk-through were injected by the test script (fixed city centres and a test tone), the evidence photo is one of the application's own screenshots, and all timings come from one machine that was not idle.",
        "No user study was carried out. Six defects are recorded as expected failures; the further weaknesses (public evidence URLs, no login lock-out, a trail that never expires, an unbounded nearest-district lookup, a blocking e-mail call) were found by probing or reading the code.",
    ])
