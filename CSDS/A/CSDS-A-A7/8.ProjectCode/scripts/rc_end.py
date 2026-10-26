"""Implementation decisions, conclusion, future scope, references and appendices for SHEGUARD."""
from __future__ import annotations

from docx.shared import Inches

from doc_common import NOT_RETRIEVED, REFERENCES, ROOT
from rc_results import AP, AS, CC, DT, EQ, M, REP, RS, SP, extra_block, lat, pc, test_counts


def _grab(rel: str, marker: str, n: int) -> str:
    """n lines of a real source file (path relative to the project root), starting at the first line that contains `marker`."""
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if marker in ln)
    return "\n".join(lines[i:i + n])


def sec_decisions(d):
    d.h2("Implementation Decisions and Reasoning")
    d.p("The table lists the main implementation decisions and the reason for each. Several follow from three constraints: no labelled safety data exist for individual streets, the "
        "project had to run on one ordinary computer without paid services, and the free external services (OSRM, Nominatim, Gemini) have no service guarantee.")
    d.table([["Decision", "Why"],
             ["K-Means [9], [10] on one feature instead of a multi-feature model", "Only the district crime counts were available as open data; the base paper's population, police and socio-economic files were not used. K-Means gives data-driven tiers without labels; the cost, shown in Chapter 8, is that the model is two cut-offs on one number"],
             ["Three tiers (low, medium, high), k = 3", "The interface shows three colours. The indices in Chapter 8 do not single out k = 3 (k = 2 has a higher silhouette, k = 4 a lower Davies-Bouldin value [11], [12])"],
             ["Rate = total crimes / years reported", "Districts reported between 1 and 12 years; averaging per reporting year keeps a district with few years comparable. Population was not available, so it is a count, not a per-capita rate"],
             ["Drop districts that could not be geocoded", "A wrong coordinate would put a risk circle in the wrong place; 467 of 827 were kept (56.5%) and the rest dropped instead of guessed. Geocoding ran once with Nominatim at one request per second and is cached in a CSV"],
             ["Route risk = mean tier weight of every 8th route point (weights 1.0, 2.5, 5.0)", "Cheap, explainable and independent of the routing engine; the weights are a judgement, and changing them to 1/2/3 or 1/3/9 changed no recommendation in the 10 multi-route pairs tested"],
             ["Night multiplier of 1.6 between about 20:30 and 05:30 IST from the server's UTC clock", "No per-user time zone was available; the result is that night scales every route equally and cannot change the ranking"],
             ["OSRM public demo server for alternatives [17], Nominatim for place search", "Free and needing no key; they have no service guarantee and OSRM often returns a single route"],
             ["FastAPI, SQLAlchemy and SQLite [27]", "Typed request models, automatic documentation, no database server to install; sufficient for one machine, but there is no row-level security and no migrations"],
             ["JWT bearer tokens [19] and bcrypt [21] with an owner filter in every query", "Stateless authentication; guardians have no account and reach a session only through an unguessable 32-hex token, so they need no app and no login in an emergency"],
             ["WebSocket per session token [20] for live location", "Pushes each position to every open guardian page without polling; the owner posts about every 4 seconds from `watchPosition`"],
             ["SHA-256 [22] of every evidence file, computed on the server", "Gives each file a fingerprint that changes if one bit changes; stored with time and location"],
             ["Web Speech API [25] with a word-window matcher for SafePhrase", "Needs no model or server of the project; the sensitivity levels set the share of the phrase's words that must be heard. It requires an open Chrome or Edge tab and online recognition"],
             ["Phrases stored only in the browser, shown as a SHA-256 fingerprint", "The server never learns the cover phrase; a user can confirm what is saved without displaying it"],
             ["Gemini through the backend with a fixed safety system prompt [26]", "The key stays on the server; the prompt demands that an emergency answer begins with SOS or emergency services and keeps answers under 150 words"],
             ["React, Vite, Tailwind and Leaflet [28] as an installable PWA", "One code base for phone and desktop; the abstract names Flutter and Supabase, which were not used"],
             ["Telegram and Gmail alerts best-effort, reported per guardian", "The SOS response lists what succeeded so the interface shows it; with no credentials every channel reports not sent"]],
            "Implementation decisions", widths=[0.4, 0.6], font=9)


def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project built SHEGUARD, a women's safety platform that supports a user before, during and after an emergency. Before: OSRM route alternatives are scored against an area-risk table made by "
        "K-Means clustering of district crime counts and shown on a map with a heat layer. During: one tap on SOS, or a spoken SafePhrase, starts an emergency session that streams the position over a WebSocket "
        "to a read-only tracking page that guardians open from a link without an account, and that can try to alert them by Telegram and e-mail. After: photographs and audio are saved with time, place and a SHA-256 hash, and "
        "a three-second hold cancels the emergency. A Gemini-backed assistant answers safety questions. The system has 19 HTTP endpoints, one WebSocket route, six database tables, a React web application "
        "installable as a PWA and a pytest suite of 57 tests.",
        f"On the measured side: the K-Means model (k = 3) on {REP['tier_counts']['low'] + REP['tier_counts']['medium'] + REP['tier_counts']['high']} districts has silhouette {REP['silhouette']:.2f} and Davies-Bouldin {REP['davies_bouldin']:.2f}, but it is two cut-offs "
        f"({EQ['threshold_low_medium']:.1f} and {EQ['threshold_medium_high']:.1f} crimes per year) on one number, built from 2001-2012 counts with {pc(DT['geocode_rate'])} of districts geocoded. Guardian pages receive a position in about "
        f"{AP['websocket']['one_viewer_post_to_receive']['mean_ms']:.0f} ms locally, all cross-user access probes were refused and 51 tests pass, with six more documenting defects. Not demonstrated in this run: alert delivery by Telegram or e-mail (no credentials) and any answer from the Gemini assistant (quota exhausted).")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.p("Of the six objectives of the project, one is achieved as far as it could be tested (live location sharing through a link), one is implemented but not demonstrated (the Gemini assistant), and four are achieved in part. Safe route guidance "
        "(objective 1) works but rests on coarse historical data with large coverage gaps. Quick activation (objective 2) has a working one-tap SOS and a SafePhrase matcher that was tested on text only. Evidence preservation (objective 4) hashes and time-stamps "
        "files but serves them by URL without a login, and data protection (objective 6) is done with owner-scoped queries rather than database Row Level Security. Chapter 8 gives the evidence for each objective.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    bs = SP["by_sensitivity"]
    d.numbered([
        f"**The risk model is two thresholds.** K-Means on one feature reproduces exactly as cut-offs at {EQ['threshold_low_medium']:.1f} and {EQ['threshold_medium_high']:.1f} crimes per year; a silhouette of {REP['silhouette']:.2f} shows clean separation of that number, not safety.",
        f"**The tiers depend on the method.** Ward clustering agrees with the shipped tiers for {pc(M['alternative_tiering']['agglomerative_ward']['agreement_with_kmeans'], 0)} of districts, a Gaussian mixture for {pc(M['alternative_tiering']['gaussian_mixture']['agreement_with_kmeans'], 0)}, and random starts move districts near the cut-offs (adjusted Rand index down to {M['seed_stability']['min_ari_vs_shipped']:.2f}).",
        f"**Coverage decides usefulness.** Only {pc(DT['geocode_rate'])} of districts are in the table; Hyderabad is {CC['nearest_district_km']['Hyderabad']:.0f} km, Kolkata {CC['nearest_district_km']['Kolkata']:.0f} km and Lucknow {CC['nearest_district_km']['Lucknow']:.0f} km from the nearest one, and the scorer has no distance limit.",
        f"**The night factor is cosmetic.** It multiplies all routes by 1.6, so the recommended route is the same by day and night in {RS['ranking_same_day_night']} of 16 test pairs; and {16 - RS['pairs_with_alternatives']} of 16 trips returned only one route.",
        "**The score counts mostly domestic violence in raw numbers.** Cruelty by husband or relatives is 40.0% of all counted crimes, and counts are not divided by population, so big districts rank high.",
        f"**Live tracking is fast and hardware-light.** A guardian's page receives a position in about {AP['websocket']['one_viewer_post_to_receive']['mean_ms']:.0f} ms (local), every other call except log-in and route planning answers in tens of milliseconds, and guardians need no account.",
        f"**SafePhrase trades recall for false alarms.** On written transcripts Medium recalls {pc(SP['by_sensitivity']['Medium']['recall'])} with no false triggers and Ultra recalls {pc(SP['by_sensitivity']['Ultra']['recall'], 0)} with {pc(SP['by_sensitivity']['Ultra']['false_trigger_rate'], 0)} false triggers; real speech was not tested.",
        "**Testing found real defects:** uncaught Gemini timeouts (500), unvalidated coordinates and triggers, no upload limit, publicly retrievable evidence files, an HTML upload served as text/html, no login lockout and a WebSocket that accepts any token.",
        f"**External services decide the experience.** The assistant answered {AS['answered']} of {AS['prompts']} prompts (quota 429) and no alert channel was configured, so the two features that depend on third-party accounts could not be shown working.",
    ])


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.p("In its present form SHEGUARD is a working prototype and a teaching platform for a women's safety application; it must not be relied on in a real emergency, and its route risk must not be read as a statement about the safety of a place. "
        "With population-normalised and more recent data, full geocoding, configured alert channels and the security fixes listed under the limitations, the same structure could support four uses: a guardian-facing live link that needs no app; a "
        "quick-activation channel for users who cannot reach a phone; a route comparison that includes safety next to time; and an evidence log that a user can later show with its hash and time stamp.")


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        f"The risk model uses one feature, old data (2001-2012), raw counts and {pc(DT['geocode_rate'])} of districts; it has no ground truth, no held-out set and no field validation.",
        "Uttar Pradesh, West Bengal, Delhi and Uttarakhand have no district in the table; the scorer assigns the nearest district however far away it is, and the night multiplier does not change the ranking.",
        "SafePhrase needs an open Chrome or Edge tab with internet speech recognition; only the matching rule was tested, on written text.",
        "Alert delivery by Telegram and e-mail was never exercised (no credentials) and `send_email` blocks the event loop; the Gemini assistant could not be demonstrated (quota 429) and a timeout returns HTTP 500.",
        "Evidence files are retrievable by URL without login, uploads have no size limit, there is no verification endpoint and no tracking-link expiry.",
        "Access control is owner-scoped queries, not Row Level Security; there is no admin role, no rate limiting, a permissive CORS setting and a minimum password rule of six characters.",
        "A browser-based PWA instead of a native Flutter app; SQLite on one machine; no load test beyond five WebSocket viewers; no user study and no field trial.",
    ])


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "**Rebuild the risk model on better data:** population-normalised rates, newer years, the base paper's police-presence and socio-economic features, and a comparison of K-Means, Gaussian mixture and hierarchical clustering with the Silhouette, Davies-Bouldin and Calinski-Harabasz indices [11]-[13].",
        "**Complete the geocoding** for the 360 missing district entries (for example by district headquarters from an administrative gazetteer) and cap the distance to the nearest district, falling back to \"unknown\" instead of a far district.",
        "**Make the night factor meaningful:** time-dependent tier weights or incident data by hour, and the user's own time zone.",
        "**Fix the known defects:** map timeouts to HTTP 502, validate coordinates and trigger values, cap uploads, serve evidence through an authorised route with a safe content type, authenticate the WebSocket, and add login throttling.",
        "**Verify evidence:** a verification endpoint, a hash anchored outside the database (for example sent to the guardians with the alert), and an expiry for tracking links.",
        "**Move blocking work off the request path:** send Telegram and e-mail alerts concurrently or from a background task so one slow send cannot delay the others or stall the server.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "Shake, power-button or fall detection and a missed check-in timer, the automatic triggers that the IoT review [2] and the shake-to-alert work [4] point to.",
        "A native mobile build (the abstract names Flutter) that can listen with the screen off, use the camera and the real battery level, and send SMS through the phone when there is no data.",
        "Deviation alerts when a route is left, in the spirit of the base paper's safety buffer [1], and a safety check-in at intervals.",
        "Crowd-sourced incident reports and a heat map that updates, as in [7].",
        "Optional wearable or camera hardware for evidence [6] and an official helpline integration.",
        "Regional-language interface and speech recognition tuned to Indian accents.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.p("The next step is a hosted deployment: HTTPS, a managed database in place of SQLite, object storage for evidence with signed URLs, a strong secret key and restricted CORS from the environment, rate limiting, a background worker for alerts, and a "
        "process manager. A paid or self-hosted routing engine and geocoder would replace the public OSRM and Nominatim demo servers, and the Gemini quota should be monitored with a fallback answer. A load test with many concurrent sessions and WebSocket viewers, "
        "a measured battery and data cost on real phones and a continuous-integration run of the 57 tests would turn the single-machine timings of this report into capacity figures.")


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "Whether district-level crime statistics predict risk on a route at all: compare route scores with incident reports at street level, and study the bias of under-reporting that the base paper [1] also notes.",
        "Learning risk from several features with a model that can be validated against held-out incidents, instead of unsupervised clustering without ground truth.",
        "Speech activation under noise: false-accept and false-reject rates of on-device keyword spotting against the web recogniser, on real speakers.",
        "Privacy-preserving evidence and location sharing: end-to-end encrypted trails, and consent models for guardians.",
        "A user study with women and guardians on trust, false alarms and the effort of cancelling.",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, ref in enumerate(REFERENCES, 1):
        p = d.p(f"[{i}]\t{ref}", align="left", size=11, line=1.2, space_after=4)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)
    d.p("Entries " + ", ".join(f"[{n}]" for n in sorted(NOT_RETRIEVED)) + " come from the batch literature survey and could not be retrieved independently; they are listed as given and no result from them is used in this report.",
        italic=True, size=10.5)


def appendix_a(d):
    d.p("The listings below are extracted from the source files when this report is built, so they match the code that produced the results.")
    d.h2("Route Risk Scoring")
    d.code(_grab("backend/app/services/risk.py", "def score_route", 26), "score_route() in backend/app/services/risk.py")
    d.h2("Training the Area-Risk Model")
    d.code(_grab("ml/train_risk_model.py", "X = data[[\"crime_rate\"]]", 20), "K-Means fit and tier naming in ml/train_risk_model.py")
    d.h2("Starting an Emergency")
    d.code(_grab("backend/app/routes/sos.py", "session = models.EmergencySession(", 13) + "\n    ...\n" + _grab("backend/app/routes/sos.py", "delivery = []", 6),
           "Session creation and guardian alerts in backend/app/routes/sos.py")
    if getattr(d, "report", False):
        d.p("The listings of the location broadcast, the evidence upload and the SafePhrase matcher are given in the chapter on implementation and are not repeated here.")
        return
    d.h2("Live Location Broadcast")
    d.code(_grab("backend/app/ws_manager.py", "async def broadcast", 9), "TrackingConnectionManager.broadcast() in backend/app/ws_manager.py")
    d.h2("Evidence Hashing and Storage")
    d.code(_grab("backend/app/routes/evidence.py", "data = await file.read()", 20), "Hashing and storing evidence in backend/app/routes/evidence.py")
    d.h2("SafePhrase Matching")
    d.code(_grab("frontend/src/lib/safephrase.ts", "export function matchSafePhrase", 36), "matchSafePhrase() in frontend/src/lib/safephrase.ts")


def appendix_b(d):
    d.h2("Installation Guide")
    d.p("SHEGUARD runs on Windows with Python 3.10 or newer and Node.js 18 or newer on the path. The steps below are those of the project's own run guide; the ports 8107 and 5107 are fixed in the configuration.")
    d.numbered([
        "Run `setup.bat`. It copies `.env.example` to `.env`, creates the virtual environment `venv`, installs `backend\\requirements.txt` and runs `npm install` in `frontend`.",
        "Fill in `.env`: `GEMINI_API_KEY` for the assistant, `TELEGRAM_BOT_TOKEN` for Telegram alerts and `GMAIL_ADDRESS` with `GMAIL_APP_PASSWORD` for e-mail alerts, and a long random `JWT_SECRET`. The application runs without the first three; the assistant and the alert channels then report that they are unavailable.",
        "Train the area-risk model (a few seconds): `venv\\Scripts\\python.exe ml\\train_risk_model.py`. It writes `models\\risk_model.joblib`, `data\\district_risk.csv` and `experiments\\metrics.json`; the backend loads the table into its database the first time it starts.",
        "Run `run.bat`. It opens the backend (port 8107) and the frontend (port 5107) in two windows and the browser at http://localhost:5107.",
        "Create the demo account (backend running): `venv\\Scripts\\python.exe scripts\\seed_demo.py`, then log in as demo@sheguard.app with password Demo@1234, or register a new account.",
        "To try it on a phone, install the tunnel once with `winget install --id Cloudflare.cloudflared`, run `run_phone.bat` and open the `https://....trycloudflare.com` link in the phone's Chrome; use the browser menu to Add to Home screen.",
        "Check the system: `venv\\Scripts\\python.exe scripts\\smoke_test.py` (12 live steps), `venv\\Scripts\\python.exe -m pytest tests -q` (57 tests, offline), `cd frontend` and `npm run build`, and `venv\\Scripts\\python.exe ml\\eval.py` for the cluster indices.",
        "Reproduce this report's measurements: `scripts\\run_experiments.py` (risk model and route scoring, uses the cached OSRM answers), `scripts\\measure_api.py` (latency and probes, needs the backend running), `node scripts\\safephrase_eval.mjs`, `scripts\\assistant_eval.py` and `scripts\\capture_screenshots.py`.",
    ])
    d.h2("User Guide")
    d.table([["Task", "How"],
             ["Create an account", "Sign up with name, e-mail and a password of at least six characters; accept the terms"],
             ["Add guardians", "Profile and Guardians, enter name and a phone, e-mail or Telegram chat ID (the guardian sends /start to the bot first), Add guardian"],
             ["Plan a safer route", "Safe Routes, allow location (or tap the map for the start), type a destination and pick a suggestion; the route cards show distance, time, tier shares and a risk label; Hide risk areas toggles the circles"],
             ["Start an emergency", "Press SOS on the dashboard, or turn listening on in SafePhrase and say a saved phrase; the emergency screen shows who was alerted and the tracking link"],
             ["Share the link", "Copy link and send it to a guardian; the page needs no login and shows the moving position"],
             ["Save evidence", "On the emergency screen use Capture photo or Record audio; each item is listed with its hash and time"],
             ["Cancel", "Hold the cancel button for three seconds; guardians see that the emergency ended"],
             ["Ask the assistant", "AI Guardian, type a question or choose a suggestion; in danger use SOS or call 112"],
             ["Set SafePhrase", "SafePhrase, add a cover sentence of several words, choose a sensitivity and use Test a phrase before relying on it"]],
            "User guide", widths=[0.26, 0.74], font=10)
    d.p("SHEGUARD is a prototype: route risk comes from 2001-2012 district data, alert delivery and the assistant depend on keys that must be configured, and the application must not be relied on in a real emergency.")


def appendix_c(d):
    d.p("Additional captures of the running application (26 October 2026, 1440 by 900 pixels).")
    extra_block(d)
