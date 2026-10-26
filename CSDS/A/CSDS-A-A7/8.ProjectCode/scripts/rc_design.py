"""Chapter 5 content: architecture, workflow, DFDs, UML, database, modules, user interface; plus the diagram registry (SHEGUARD).

Diagrams are drawn by scripts/make_diagrams.py from the real routers, models, services and React screens; each paragraph below was
checked against the picture and against backend/app and frontend/src.
"""
from __future__ import annotations

from doc_common import DIAG, SHOTS

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]

DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of SHEGUARD",
                     ["The diagram has four layers and a column of outside services. At the top is the browser: a React 19 and TypeScript single-page application built "
                      "with Vite (port 5107, which proxies `/api` and `/ws` to the backend) and installable as a PWA. It contains the nine signed-in and signed-out "
                      "screens plus the public `/track/{token}` page, a Leaflet map that draws OpenStreetMap tiles, route lines, risk circles and the live path, the "
                      "Web Speech API with the SafePhrase matcher (`lib/safephrase.ts`), the device APIs (geolocation, camera or file input, MediaRecorder, battery), and "
                      "`localStorage`, which holds the JWT, the SafePhrase list, the active session and a short activity log.",
                      "Below it is the FastAPI application on port 8107. Its ten routers (`auth`, `guardians`, `risk`, `routes_plan`, `places`, `sos`, `evidence`, `track`, "
                      "`ai` and the WebSocket route `ws`) call six service blocks: security (bcrypt and HS256 JWT, `get_current_user`), the risk scorer, the OSRM client, "
                      "the Gemini client, the alert senders (`telegram.py`, `email.py`) and the evidence and live-push helpers (`hashing.py`, `ws_manager.py`). "
                      "SQLAlchemy maps six models to one SQLite file; the district table is seeded from `data/district_risk.csv` when the application starts. "
                      "Storage is local: the database, the model and data files (`risk_model.joblib` and the two district CSV files) and the evidence folder. "
                      "On the right are the outside services: OpenStreetMap tiles (called by the browser), Nominatim for place search, the OSRM public demo server for "
                      "route alternatives, the Gemini API for the assistant, and the Telegram Bot API and Gmail SMTP for alerts. The last two are shaded because their "
                      "credentials were empty in this run, so no alert was ever sent."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow",
                 ["The nine steps follow one person from sign-up to the end of an emergency. Steps 1 to 4 prepare: register or log in (a bcrypt-hashed password and a "
                  "JWT valid for seven days), add guardians, plan a safe route (place search, OSRM alternatives, district risk score, safest first) and keep SafePhrase "
                  "listening. Step 5 starts an emergency by one tap or a matched phrase and calls `POST /api/sos/start`. Steps 6 to 9 run while the session is active: "
                  "the alert and tracking link go to the guardians (Telegram and email, best effort), the position is pushed about every four seconds to the guardian's "
                  "map, photo or audio evidence is stored with a SHA-256 hash, and holding the cancel button for three seconds ends the session. The dashed tenth box is "
                  "the AI Guardian, which can be used at any time. The note at the bottom states what did not work in this run: the Telegram and Gmail channels were not "
                  "configured and the Gemini key had run out of quota."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context)",
             ["At the highest level SHEGUARD is one process with five external entities. The user sends registration and login details, guardians, a destination, the "
              "device location, a SafePhrase or tap that starts an SOS, photo or audio evidence and questions for the assistant; the user receives a token, the risk "
              "areas, the ranked routes, the tracking link, the evidence hashes and the assistant's answer. The guardian, who has no account, sends only the share "
              "token (by opening the link) and receives a read-only page with the path, the status and live pushes. OSRM and Nominatim receive a route request or a "
              "place query and return route alternatives or place matches. The Gemini API receives a question with the user's approximate location and returns "
              "text. The process sends an alert text with the tracking link to Telegram and Gmail; both are shaded because they were not configured in this run."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1",
             ["Level 1 splits SHEGUARD into seven processes: authenticate and manage guardians (1.0), plan a safe route (2.0), serve risk areas (3.0), SOS session (4.0), "
              "live tracking (5.0), capture evidence (6.0) and the AI assistant (7.0). Five data stores are used: D1 holds users and guardians, D2 the 467 district-risk "
              "rows, D3 the sessions and location pings, D4 the evidence rows and files, and D5 is the browser's `localStorage` (token, SafePhrases, active session). "
              "Process 1.0 issues the JWT; the owner check is made in 2.0 and 4.0 to 7.0, while 3.0 (`GET /api/risk/areas`) is public. Process 2.0 only reads D2; "
              "4.0 creates the session and the first ping in D3 and sends the alerts; 5.0 reads D3 and pushes new pings to the guardian over the WebSocket; 6.0 writes "
              "D4; 7.0 keeps no store because the assistant has no memory between questions."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: Plan safe route (process 2.0)",
             ["Process 2.0 is expanded into nine steps that follow `plan_route()` and `score_route()`. The request with the origin and destination coordinates is "
              "validated and the user is identified from the JWT (2.1). The OSRM public demo server returns driving alternatives with the full geometry (2.2); an "
              "OSRM failure gives HTTP 502 and an empty result HTTP 404. All 467 district rows are read from D2 (2.3). Every eighth point of each polyline is "
              "sampled (2.4) and mapped to the nearest district by haversine distance over all 467 rows, with no distance limit (2.5). The tier weight (low 1.0, "
              "medium 2.5, high 5.0) is applied and multiplied by 1.6 when the server clock is in the night window, UTC hour 15 or later (2.6). The mean weight is "
              "the route score, rounded to three decimals, together with the tier counts (2.7); routes are sorted by ascending score and the first is marked "
              "`recommended` (2.8), and the list is returned with `safest_index = 0` (2.9). Nothing is written to the database."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram",
                ["There is one signed-in actor, the user. The user registers or logs in, manages guardians, plans a safe route, sets SafePhrases and their sensitivity, "
                 "triggers an SOS by tap or phrase, streams the live location, captures photo or audio evidence, cancels the SOS by holding the button for three seconds "
                 "and asks the AI assistant. Triggering an SOS includes streaming the location. The guardian is the second actor and has no account: the guardian can "
                 "open the tracking link and watch the live position. The dashed arrows show which use cases call an outside system: route planning calls OSRM and "
                 "Nominatim, the SOS calls Telegram and Gmail (not configured in this run) and the assistant calls Gemini. There is no administrator role: every account is "
                 "an ordinary user."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram: from SOS trigger to cancellation",
                 ["The sequence shows the main flow in 17 numbered steps across six participants. In the browser, a tap or a matched SafePhrase obtains the position and "
                  "posts `POST /api/sos/start` with the bearer token (1, 2). The API decodes the JWT (3), inserts the `EmergencySession` with a random 32-hex `share_token` "
                  "and the first `LocationPing` (4), reads the owner's guardians (5) and asks the alert senders to send a Telegram message and an email with the tracking "
                  "URL, each reporting sent or not sent (6); the response carries the session id, the token, the URL and the delivery list (7). A guardian opens the link "
                  "and the page loads the path with `GET /api/track/{token}` without logging in (8), then opens the WebSocket, which registers the viewer in the "
                  "connection manager (9). About every four seconds the browser posts a new position (10); the API updates the session and stores a ping (11) and the "
                  "manager broadcasts it (12), so the marker and path move on the guardian's map. Evidence is uploaded as multipart data, hashed with SHA-256, written to "
                  "disk and recorded (13, 14). Holding the cancel button for three seconds posts the cancellation (15); the status becomes cancelled (16) and a "
                  "`cancelled` message is broadcast (17), after which the guardian's page says that the emergency has ended."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram (6 tables)",
           ["Six tables are created by SQLAlchemy in SQLite. A user owns many guardians and many emergency sessions; a session has many location pings and many evidence "
            "rows. The `district_risk` table is a lookup table with no foreign key: it holds the 467 geocoded districts with their crime rate, 0-100 risk score and "
            "tier, and is read by distance only. ORM cascades delete a user's guardians and sessions and a session's pings and evidence rows, but the evidence files stay "
            "on disk. The SafePhrase list is not in the database: it lives in the browser. The `evidence.file_path` column holds the path relative to `data/`, and the "
            "file name is the first 16 hexadecimal characters of the SHA-256 followed by the extension."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram",
            ["The upper part shows the six SQLAlchemy entities with their main attributes: `User` has many `Guardian` and many `EmergencySession`; a session has many "
             "`LocationPing` and many `Evidence`; `DistrictRisk` stands alone. The middle part shows the boundary classes, the ten routers with their routes, and the "
             "service classes behind them: security (`get_current_user`, `create_access_token`), the risk service with its tier weights and the night multiplier "
             "(`score_route`, `nearest_district`), the OSRM client, the Gemini client with its system prompt, the Telegram and email senders, and the connection "
             "manager with the hashing helper. Arrows show that `routes_plan` uses the OSRM client and the risk service and that `sos` uses the senders and the manager. "
             "The lower part shows the React side: the `App` shell that holds the user, the token, the guardians, the SafePhrase settings and the active session; the "
             "route, SafePhrase, emergency and tracking screens; and the hooks and libraries (`useVoiceTrigger`, `useLiveLocation`, `matchSafePhrase`, `api`, "
             "`getPosition`)."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowcharts of the two core algorithms: score_route() and matchSafePhrase()",
                  ["The left flowchart is the route-scoring algorithm. An empty route scores 0.0 with no tiers. Otherwise every eighth coordinate is sampled; for each "
                   "sample the nearest district is found by haversine distance (a missing district counts as medium), the tier weight is taken, multiplied by 1.6 at "
                   "night, and the tier is counted. When no samples remain, the score is the total weight divided by the number of samples, rounded to three decimals. "
                   "The planner then sorts the routes by ascending score and marks the first as recommended. The note under the chart states a consequence of the "
                   "design: because the night factor multiplies every route by the same number, it changes the displayed score but never the order.",
                   "The right flowchart is the SafePhrase matcher that runs in the browser on every recognition result. The transcript is lower-cased, reduced to letters, "
                   "digits and single spaces, and an empty result returns no match. For each enabled phrase, a whole-phrase substring match returns a match with "
                   "confidence 1 and the SOS starts. Otherwise a window as long as the phrase is slid across the transcript, the best share of phrase words found in a "
                   "window is kept, and the phrase counts only if that share reaches the sensitivity threshold (Low 1.0, Medium 0.85, High 0.75, Ultra 0.60) and beats any "
                   "earlier phrase. The best match, or none, is returned."]),
}


def diagram(d, key, width=None):
    fname, caption, paras = DIAGRAMS[key]
    d.figure(DIAG / fname, caption, width=width, max_h=3.9 if getattr(d, "report", False) else 4.5)
    for p in paras:
        d.p(p)


def sec_arch(d):
    d.h2("System Architecture")
    d.p("SHEGUARD is a single-machine web application: a React progressive web app, a FastAPI back end, a SQLite database, one trained scikit-learn "
        "clustering model whose output is stored as a table, and a handful of free outside services. The abstract of the project names Flutter and Supabase; "
        "the implementation uses React and FastAPI with SQLite, and this chapter describes what was built. The figure below shows the layers.")
    diagram(d, "architecture")
    d.p("The design follows five principles. **Keep guardians account-free**: a guardian never logs in; the alert carries an unguessable 32-character link "
        "that opens a read-only page and a read-only WebSocket, so a frightened family member does not have to install or sign in to anything. **Scope every "
        "query to its owner**: guardians, sessions and evidence carry an owner or user identifier and every route compares it with the user in the JWT, "
        "which is this project's SQLite-compatible replacement for the Row Level Security named in the abstract. **Treat alerts as best effort**: each channel "
        "reports sent or not sent, the SOS itself never fails because an alert failed, and the screen shows exactly which guardians were reached. **Keep the "
        "voice phrase on the device**: the SafePhrase list is stored only in the browser, and only a SHA-256 fingerprint of each phrase is displayed. **Be "
        "honest about the data**: the planner screen states that routes are scored against district crime data from 2001 to 2012 and are a guide to the area, not "
        "live conditions.")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("The data-flow diagrams show how data moves through SHEGUARD at three levels of detail: the context (level 0), the seven main processes with "
        "their data stores (level 1) and the expansion of the route-planning process (level 2).")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("Three UML views describe the design: the use-case diagram (who does what), the class diagram (what the code contains) and the sequence "
        "diagram (how the main flow runs). The two core algorithms are shown as flowcharts in Chapter 6.")
    diagram(d, "usecase")
    diagram(d, "uml")
    diagram(d, "sequence")


def sec_database(d):
    d.h2("Database Design")
    d.p("The database is SQLite, created by SQLAlchemy 2 at start-up with `create_all`; there are no migrations. Timestamps are stored in UTC. Uploaded photographs "
        "and audio clips are not stored in the database: they are files under `data/evidence/{session id}/`, and the table keeps the relative path, the SHA-256 "
        "hash, the kind, the capture position and the time.")
    diagram(d, "er")
    d.table([["Table", "Purpose", "Key columns"],
             ["users", "Accounts", "id, name, email (unique, indexed), password_hash (bcrypt), created_at"],
             ["guardians", "Trusted contacts of one user", "id, owner_id (FK users), name, phone, email, telegram_chat_id, created_at"],
             ["emergency_sessions", "One emergency", "id, user_id (FK users), share_token (unique, indexed, uuid4 hex), status (active, cancelled), trigger (manual, safephrase), started_at, ended_at, last_lat, last_lng, last_update_at"],
             ["location_pings", "The path of a session", "id, session_id (FK), lat, lng, ts"],
             ["evidence", "Photo or audio of a session", "id, session_id (FK), kind (photo, audio), file_path, sha256 (64 hex characters), lat, lng, captured_at"],
             ["district_risk", "Risk lookup loaded from the model output", "id, state, district, lat, lng, crime_rate (crimes per reporting year), risk_score (0-100), risk_tier (low, medium, high); 467 rows"]],
            "Database tables", widths=[0.2, 0.25, 0.55], font=9)
    d.p("Four design points should be noted. First, `status` and `trigger` are plain strings checked only by the application: the API accepts any trigger text, which "
        "is one of the known gaps. Second, the share token is the only credential a guardian has, so it is generated with `uuid4().hex` and stored with a unique "
        "index; the tracking route returns 404 for an unknown token but the session never expires, and a cancelled session stays readable. Third, the evidence hash and the "
        "evidence path live in the same database, so the hash proves integrity only for someone who recomputes it from the stored file; no route does that. Fourth, the "
        "`district_risk` table is filled once, from `data/district_risk.csv`, and is not updated when the model is retrained unless the database is recreated.")


def sec_modules(d):
    d.h2("Module Design")
    d.table([["Module", "Code", "Responsibility"],
             ["Application", "backend/app/main.py", "Creates the FastAPI app, CORS (all origins), the `/evidence-files` static mount, table creation and the district seed at start-up, the `/api/health` route; includes the ten routers"],
             ["Configuration and database", "app/config.py, db.py", "Reads `.env` (ports, JWT secret, keys, database URL), data and evidence folders; engine and session dependency"],
             ["Security", "app/auth.py", "bcrypt hashing, HS256 JWT (7 days) creation and decoding, `get_current_user`"],
             ["Models and schemas", "app/models.py, schemas.py, seed.py", "Six SQLAlchemy models, the Pydantic request types (password of at least 6 characters, email validation), the district seed"],
             ["Auth and guardians API", "routes/auth.py, guardians.py", "Register, login, current user; guardian list, create, update, delete scoped to the owner"],
             ["Risk and route API", "routes/risk.py, routes_plan.py, places.py", "Public district list; route planning (OSRM plus scoring); Nominatim place search for India, five results"],
             ["SOS API", "routes/sos.py, track.py, evidence.py, ws.py", "Start, location push, cancel, read; evidence upload with SHA-256 and list; public track page; guardian WebSocket"],
             ["AI API", "routes/ai.py, services/gemini.py", "Forwards a question and optional position to Gemini with a fixed safety system prompt (temperature 0.4, 400 output tokens, 20 s timeout)"],
             ["Services", "services/osrm.py, risk.py, telegram.py, email.py, hashing.py, ws_manager.py", "OSRM client; haversine, tier weights and night factor; Telegram and Gmail senders (return False without credentials); SHA-256; viewers grouped by share token"],
             ["Risk model", "ml/train_risk_model.py, ml/eval.py", "Aggregates 7 crime columns per district, StandardScaler and K-Means (k = 3), tier naming and 0-100 score, silhouette and Davies-Bouldin, route-scorer sanity check"],
             ["Data scripts", "scripts/download_data.py, geocode_districts.py, seed_demo.py, smoke_test.py", "Dataset download, Nominatim geocoding (1 request per second), demo account, 12-step live smoke test"],
             ["Tests and measurements", "tests/, scripts/run_experiments.py, measure_api.py, safephrase_eval.mjs, assistant_eval.py", "57 pytest tests (51 pass, 6 expected failures that document defects); risk-model, route, API, SafePhrase and assistant measurements"],
             ["Web application", "frontend/src/", "26 TypeScript files, about 2,950 lines: the `App` shell, ten screens, the navigation, the Leaflet map, three hooks (voice trigger, live location, battery) and five libraries (API client, geo helpers, SafePhrase matcher, siren, storage)"]],
            "Modules of SHEGUARD", widths=[0.19, 0.3, 0.51], font=9)
    d.p("The browser, not the server, owns the SafePhrase feature, the three-second hold-to-cancel rule, the battery reading and the local siren (a three-second "
        "oscillator tone that never touches the network). The server owns authentication, data and every outside call except the map tiles.")


def sec_ui(d):
    d.h2("User Interface Design")
    d.paras(
        "The web application has a landing page, a log-in page and a sign-up page for visitors, and a sidebar layout for signed-in users with five destinations: "
        "Dashboard, Safe Routes, AI Guardian, SafePhrase and Profile and Guardians, plus a permanent red button that starts or reopens the emergency. On a phone the "
        "sidebar becomes a top bar with a small SOS button and a bottom navigation bar, and the route screen adds a floating SOS button. The dashboard shows the number of guardians, the risk tier of the nearest district, the battery level "
        "(or 'not shared by this browser'), the SafePhrase listening state, the large SOS button, shortcuts including a local siren, and the recent activity. The "
        "Safe Routes screen has a destination search box, a map with route lines and optional risk circles, one card per route with its distance, duration and the "
        "share of sampled points per risk tier, and a panel of three short AI tips for the selected route. The emergency screen shows who was alerted, the tracking "
        "link with a copy button, the live map, the evidence buttons and list, a call button and the hold-to-cancel button. The public tracking page shows only the "
        "person's name, the status, the map and a reminder to call the emergency number.",
        "Design decisions follow from the situation. The emergency flow needs few taps, so the SOS button is always visible and a stray tap cannot end an alert "
        "because cancelling needs a three-second hold with a visible progress bar. Colour is paired with text (a risk badge says LOW, MODERATE or HIGH). Failures "
        "are shown in plain words: when the assistant is unavailable the screen says so instead of showing a provider error. The planner's disclaimer states that the "
        "scores come from 2001-2012 district data.",
        "Two limitations of the interface are stated. The route screen asks the assistant for tips every time a route is selected, so each planning action also "
        "spends a Gemini request; and the emergency screen's call button reads 'Call 911' while India's emergency number is 112. The screens below were captured from "
        "the running application; the complete set is in Chapter 8 and Appendix C.")
    d.figure_pair([(SHOTS / "01_landing.png", "Landing page for visitors"),
                   (SHOTS / "04_dashboard.png", "Dashboard: SOS button, status tiles and SafePhrase state")])
    d.figure_pair([(SHOTS / "06_route_delhi_jaipur.png", "Safe Routes: two alternatives scored by district risk"),
                   (SHOTS / "10_safephrase.png", "SafePhrase settings: phrases, fingerprint, sensitivity")])
    d.figure_pair([(SHOTS / "13_emergency_evidence.png", "Emergency screen with hashed photo and audio evidence"),
                   (SHOTS / "14_guardian_tracking.png", "Guardian's tracking page, no login")])
