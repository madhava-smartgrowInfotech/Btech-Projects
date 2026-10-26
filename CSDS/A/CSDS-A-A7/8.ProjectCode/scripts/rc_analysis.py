"""Chapters 3 and 4 content: feasibility study, existing and proposed system, requirements, platform, user roles (SHEGUARD).

Facts come from docs/REPORT_FACTS.md; reference numbers follow doc_common.REFERENCES.
"""
from __future__ import annotations


def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.paras(
        "SHEGUARD needs seven technical capabilities: scoring areas by risk, finding route alternatives, reacting to a spoken phrase, "
        "streaming a live position to people who have no account, storing evidence in a way that shows tampering, calling a language model, and "
        "serving all of it to a phone browser. Each was available as a mature, free component that runs on an ordinary computer without a GPU.",
        "**Area-risk model.** K-Means [9], [10] from scikit-learn [16] groups the 467 geocoded districts into three tiers in well under a second, and the "
        "silhouette [11], Davies-Bouldin [12] and Calinski-Harabasz [13] indices evaluate the grouping. **Routing and maps.** The OSRM public demo server [17] "
        "returns driving alternatives with full geometry, Nominatim [29] resolves place names, and Leaflet [28] draws OpenStreetMap [18] tiles in the browser. "
        "**Voice.** The browser's Web Speech API [25] provides continuous recognition; the project adds a word-window matcher that costs about 1.5 microseconds per "
        "transcript. **Live tracking.** FastAPI [27] supports WebSockets [20] natively, so a position can be pushed to every viewer of a session; the measured delay from "
        "posting a position to its arrival at a guardian's browser was 15.4 ms on average with one viewer and 14.6 ms with five.",
        "**Evidence.** SHA-256 [22] of a 1 MB file takes about 1.05 ms, and one flipped bit changes the digest. **Security.** JWT [19] and bcrypt [21] are "
        "standard; bcrypt login takes 285 ms on average (279 ms median), which is the price of slow hashing. **Assistant.** The Gemini API [26] needs only an HTTPS call and a key. "
        "**Measured serving cost.** On the development machine (12-thread Intel Core i5-12500, 15.7 GB of memory, no GPU) the median response time is 2.1 ms for the "
        "health route, 31.1 ms for the 467-row risk list, 14.7 ms for a location push, 13.3 ms for a 100 KB evidence upload and 1.6 s for a route plan that includes "
        "the live OSRM call.",
        "**Verified by construction.** The system was built and run end to end: the 12-step live smoke test passes, 51 of 57 automated tests pass and the other six "
        "are expected failures that document defects, and every output screen in Chapter 8 was captured from the running application.")
    d.table([["Risk", "Likelihood and effect", "Mitigation in the prototype"],
             ["No labelled ground truth for 'risky'", "Certain; the tiers cannot be validated against incidents", "Cluster indices reported as separation only; limits stated in Chapters 8 and 9"],
             ["Old, coarse, count-based data", "Certain; 2001-2012 district counts, not rates per population", "Planner screen carries a disclaimer; population normalisation listed as future work"],
             ["Incomplete geocoding", "Certain; 56.5 % of districts, none for 11 states and union territories", "Nearest-district fallback keeps the planner working; gap measured (Hyderabad 149 km from the nearest district)"],
             ["Free services without a guarantee", "OSRM demo, Nominatim and the Gemini free tier are rate-limited; Gemini returned 503 and 429 in this run", "Errors are mapped to plain messages; a self-hosted router and a paid key are future work"],
             ["Alert channels need user credentials", "Telegram token and Gmail app password were empty; no alert was ever sent", "Delivery is reported per guardian; the tracking link still works"],
             ["Browser limits for speech", "Recognition needs Chrome or Edge, a foreground tab and an online recogniser", "A clear error is shown; native app listed as future work"],
             ["Single-process SQLite", "Limits concurrent users and has no migrations", "Acceptable for a prototype; a server database is listed as future work"]],
            "Technical risks and their handling", widths=[0.24, 0.38, 0.38], font=9.5)
    d.p("Two technical risks are stated openly. First, the risk model is a one-feature clustering of old district counts that cannot be validated, so the technology is "
        "feasible but the meaning of the score is limited. Second, the two outward channels that make an alert useful, Telegram and email, were not exercised, so "
        "the end-to-end alert to a real guardian is not demonstrated. Both limits are discussed in Chapters 6 to 9.")


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.table([["Item", "Choice", "Cost"],
             ["Machine learning", "scikit-learn K-Means, pandas, NumPy (open source)", "No licence fee"],
             ["Back end", "Python 3.11, FastAPI, SQLAlchemy, SQLite, Uvicorn (open source)", "No licence fee"],
             ["Front end", "React 19, TypeScript, Vite, Tailwind CSS, Leaflet, a PWA plug-in (open source)", "No licence fee"],
             ["Routing, geocoding, tiles", "OSRM public demo server, Nominatim, OpenStreetMap tiles", "Free; subject to usage policies and no service guarantee"],
             ["AI assistant", "Gemini API, free tier", "Free within a quota; the quota was exhausted during this run"],
             ["Alerts", "Telegram Bot API and Gmail SMTP with an app password", "Free to use; credentials needed from the user"],
             ["Hardware", "An ordinary desktop or laptop (development machine: Core i5-12500, 15.7 GB), no GPU, a phone with Chrome for field use", "Existing machine"],
             ["Data", "Two Kaggle datasets under CC0; district coordinates from Nominatim (ODbL)", "No fee; staff time only"],
             ["Hosting, SMS, native apps, support", "Not used or not costed", "Not estimated"]],
            "Cost elements of the project", widths=[0.2, 0.5, 0.3], font=9.5)
    d.p("Because every component is open source or a free tier, the cost of building and running the prototype is limited to the development machine and the team's time. "
        "A monetary estimate of a real deployment was not made: a hosted server and database, a routing service with a service-level agreement, a paid language-model "
        "quota, SMS or push notification delivery, a native mobile application and the collection of current, population-normalised crime data would all add cost "
        "that this project did not measure. The benefit to users, for example faster help or fewer incidents, was not measured either.")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.bullets([
        "**Users.** A user needs a phone or computer with Chrome or Edge and an account (name, email, password of at least six characters). Guardians need only a browser to open a link.",
        "**Setup.** `setup.bat` creates the Python environment and installs the front end, `ml/train_risk_model.py` rebuilds the model (a few seconds), `run.bat` starts both servers, `scripts/seed_demo.py` creates a demo account, and the README documents the optional keys. Phone testing over HTTPS uses a Cloudflare quick tunnel (`run_phone.bat`).",
        "**Everyday use.** A user adds guardians once, searches a destination to see route alternatives, and in an emergency taps SOS or says a SafePhrase; guardians open the link; the user adds evidence and ends the session with a three-second hold.",
        "**Trust.** The planner and the landing page state that route risk comes from historical district data, the SafePhrase screen shows only fingerprints of the phrases, and the emergency screen shows plainly how many guardians were reached.",
        "**Maintenance.** The risk table is regenerated by re-running the training script and re-seeding; owner scoping is repeated in each route, so a new route needs the same check; there are no migrations.",
        "**Limits of operation.** The prototype is a single-process application with a SQLite file. It has not been load-tested beyond five simultaneous WebSocket viewers, has no hosted deployment, and has not been used by real users in a field trial.",
    ])
    sec_feasibility_legal(d)


def sec_feasibility_legal(d):
    d.h2("Data, Legal and Ethical Feasibility")
    d.paras(
        "The project handles sensitive data. Account data are a name, an email address and a bcrypt hash; guardian data are names, phone numbers, email addresses and "
        "Telegram chat identifiers of third parties; emergency data are a location trail and photo or audio evidence. The two crime datasets are published under CC0 "
        "[23], [24] and the district coordinates derive from OpenStreetMap data under the ODbL [29]. The aggregate counts contain no personal information, but "
        "labelling a district 'high risk' from counts alone can stigmatise it, because large and well-reporting districts rank high; the screen therefore calls the "
        "result a guide to the area, not live conditions.",
        "Two privacy facts need to be stated. Anyone who holds a tracking link can see the person's name and the whole location trail, and the link does not expire; "
        "and stored evidence files can be fetched by anyone who knows the file URL, because the static mount has no authentication. A production system would need "
        "consent from guardians, expiring links, authenticated evidence download, a retention policy and a privacy notice. The system does not replace emergency "
        "services and says so in the interface.")


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The project followed the phases below. The durations are indicative relative weeks for a four-member team; no calendar dates are claimed because the "
        "repository history does not record them reliably.")
    d.table([["Phase", "Indicative duration", "Outcome"],
             ["Problem study and survey", "Weeks 1-2", "Problem statement, objectives, base paper and literature survey"],
             ["Data and model", "Weeks 3-5", "Two Kaggle datasets, geocoding of 827 district pairs (467 resolved, at one request per second), K-Means risk tiers, evaluation script"],
             ["Back end", "Weeks 4-7", "FastAPI routers, JWT security, guardians, route scoring, SOS sessions, WebSocket push, evidence hashing, Gemini and alert services"],
             ["Front end", "Weeks 6-10", "React PWA: landing, authentication, dashboard, safe routes with Leaflet, SafePhrase, emergency and tracking screens"],
             ["Testing and measurement", "Weeks 10-12", "Smoke test, 57 automated tests, risk-model, route, API and SafePhrase measurements"],
             ["Documentation", "Weeks 12-13", "Review decks, chapter documents, final report and conference-style paper"]],
            "Project schedule (indicative)", widths=[0.26, 0.2, 0.54], font=9.5)
    d.p("The schedule was feasible because each heavy component was an existing library or free service. The work that did not fit is the part that depends on other "
        "people: real alert credentials, a field trial with guardians, and current, normalised crime data.")


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints")
    d.table([["Advantages", "Constraints"],
             ["Runs on one laptop with no GPU and no paid service", "Risk score is a one-feature clustering of 2001-2012 district counts; it cannot be validated"],
             ["One platform joins safe routes, hands-free trigger, live tracking, evidence and an assistant", "Only 467 of 827 districts are geocoded; several large cities have no nearby district"],
             ["Guardians need no account: a link opens a live, read-only page", "The tracking link never expires and evidence files are fetchable by URL"],
             ["Every user's data is scoped to the owner (verified by probes)", "No Row Level Security, no administrator role, a single user role"],
             ["Evidence is stored with time, place and a SHA-256 hash", "No verification endpoint; no upload size limit"],
             ["Measured latencies are low (2 ms to 31 ms median for most routes)", "Telegram, Gmail and Gemini were not working in this run; single-process SQLite, no load test"]],
            "Advantages and constraints of the project", widths=[0.5, 0.5], font=10)


def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.paras(
        "Today a woman who feels unsafe relies on a mix of tools. Panic-button and SOS apps send an alert to emergency contacts when the user presses a button; "
        "government helplines and apps connect the user to the police; IoT wearables with GPS and GSM modules send a location alert when triggered [2]; and ordinary "
        "map applications suggest the fastest route without any notion of safety. The literature survey of this project reviews five papers; the closest to this work "
        "are an ESP32-camera safety application that classifies crime zones and reports an SOS delivery time of four to six seconds and a crime-zone classification "
        "accuracy of 93 % on its own test locations [6], a safe-route recommendation system described at design level [7], and the base paper [1], which clusters regions "
        "by crime, police presence and infrastructure and proposes alerts when a cab leaves a safe path.",
        "A systematic review of IoT devices for women's safety [2] found that the devices mostly depend on a button or on sensors worn on the body and concluded that "
        "systems with automatic alert activation and less human interaction are still needed. That is the gap this project addresses on a phone: the user "
        "should not have to find and press a button while frightened.")
    d.table([["Limitation of the existing system", "Consequence"],
             ["The SOS must be triggered manually", "Hard to do when the user is frightened or cannot reach the phone"],
             ["Most apps only send an alert", "No prevention before and no follow-up after the emergency"],
             ["Routes are chosen for speed, not safety", "Users are led through areas that may be unsafe"],
             ["Evidence such as audio, images and time is rarely kept securely", "Little proof after the event"],
             ["Guardians receive a one-time alert", "They cannot see where the person is moving"],
             ["Wearable and camera systems need extra hardware [2], [6]", "Cost and the habit of carrying a device limit use"]],
            "Limitations of the existing system", widths=[0.46, 0.54], font=10)


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.p("SHEGUARD joins prevention, quick activation, live communication and evidence in one web application. Before a journey, the user searches a destination and "
        "sees route alternatives scored against district risk; the safest is highlighted on a map with a risk layer. During an emergency, a tap or a spoken cover "
        "phrase starts a session that gives each guardian a link to a live map, sends the position every few seconds and lets the user add photos and audio clips "
        "stored with their time, place and SHA-256 hash. A three-second hold ends the session. An assistant answers safety questions with Gemini.")
    d.table([["Feature", "What it does", "Advantage over the existing system"],
             ["F1 Safe route", "OSRM alternatives scored by district tier and time of day; safest first, with a risk heat layer", "Route choice considers risk, not only speed (but see the limits of the data)"],
             ["F2 Area-risk model", "K-Means (k = 3) on district crime counts gives low, medium and high tiers and a 0-100 score", "A data-driven tiering of 467 districts"],
             ["F3 SafePhrase", "Web Speech recognition plus a word-window matcher with four sensitivity levels", "Hands-free start without touching the phone"],
             ["F4 Smart SOS", "One-tap SOS; hold three seconds to cancel", "Fast start, protected against accidental cancel"],
             ["F5 Live tracking", "Position every ~4 s pushed over a WebSocket to a no-login guardian page", "Guardians see movement, not a single alert"],
             ["F6 Alerts", "Telegram message and email with the tracking link, delivery reported per guardian", "Free channels; honest delivery status (not exercised here)"],
             ["F7 Evidence", "Photo or audio with time, location and SHA-256", "Evidence preserved with an integrity fingerprint"],
             ["F8 AI assistant", "Gemini answers safety questions and gives three tips for a selected route", "Guidance at the moment of doubt (not demonstrated in this run)"],
             ["F9 Access control and PWA", "JWT, owner-scoped queries, per-session share token; installable PWA", "Private data, installable on a phone"]],
            "Features of SHEGUARD", widths=[0.2, 0.46, 0.34], font=9.5)
    d.p("The advantages listed are those the built system demonstrates or that the code provides; they do not include a measured reduction in response time or in "
        "incidents, which was not tested.")
    d.p("The table below maps each limitation of the existing system to the feature that answers it and states how far the prototype actually goes. 'Demonstrated' "
        "means it works in the running application; 'Partial' means only part of the need is met; 'Not demonstrated' means the code exists but the outside service "
        "did not work in this run.")
    d.table([["Limitation of the existing system", "Answering feature", "Status in the prototype"],
             ["Manual SOS only", "F3 SafePhrase, F4 Smart SOS", "Partial: one-tap and phrase trigger work; the phrase matcher was tested on written transcripts only; no shake or automatic trigger"],
             ["Alert only, no prevention", "F1, F2 safe route and risk model", "Partial: works, but on old, coarse, count-based data with coverage gaps"],
             ["Speed-only routes", "F1 safe route", "Demonstrated on real OSRM routes; the recommended route was the fastest in 11 of 16 test pairs"],
             ["Evidence not preserved", "F7 evidence", "Partial: hashed, timed and located; files publicly retrievable; no verify route"],
             ["One-time alert to guardians", "F5 live tracking, F6 alerts", "Tracking demonstrated; Telegram and email not configured, so never delivered"],
             ["Extra hardware needed", "Whole platform runs in a phone browser", "Demonstrated as software; no field trial"]],
            "How the proposed system answers the limitations", widths=[0.28, 0.3, 0.42], font=9.5)
    d.p("**Data requirements.** The planner needs the origin and destination coordinates, the 467-row district table and the server clock; the SOS needs the device "
        "position and at least one guardian with a Telegram chat id or an email address for an alert to be attempted; the evidence needs a camera or microphone "
        "permission; the assistant needs a Gemini key; SafePhrase needs a browser with speech recognition and microphone permission.")


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.table([["ID", "Requirement", "Satisfied by"],
             ["FR1", "A visitor shall register with a name, a valid email and a password of at least six characters, and log in; the system shall issue a signed token valid for seven days", "POST /api/auth/register, /login, GET /me; Register and Login screens"],
             ["FR2", "A user shall add, edit and delete guardians (name, phone, email, Telegram chat id) and see only their own", "GET/POST /api/guardians, PUT/DELETE /{id}; Profile screen"],
             ["FR3", "The system shall list the 467 district risk areas with tier and score", "GET /api/risk/areas; ml/train_risk_model.py"],
             ["FR4", "A user shall search a destination in India and receive route alternatives scored by risk, sorted safest first", "GET /api/places/search, POST /api/routes/plan; Safe Routes screen"],
             ["FR5", "A user shall store SafePhrases and a sensitivity level and have the system listen for them", "lib/safephrase.ts, useVoiceTrigger; SafePhrase screen"],
             ["FR6", "A user shall start an emergency by one tap or a matched phrase; the system shall create a session with a random share token and alert each guardian by Telegram and email where configured", "POST /api/sos/start; Dashboard and navigation SOS button"],
             ["FR7", "While a session is active the position shall be stored and pushed to viewers of the share token", "POST /api/sos/{id}/location, WS /ws/track/{token}; useLiveLocation"],
             ["FR8", "A guardian shall open the share link without logging in and see status, path and live position", "GET /api/track/{token}; Track screen"],
             ["FR9", "A user shall add photo or audio evidence to an own session; the system shall store its SHA-256, time and position", "POST /api/sos/{id}/evidence; Emergency screen"],
             ["FR10", "A user shall cancel a session by holding a button for three seconds; viewers shall be told", "POST /api/sos/{id}/cancel; hold-to-cancel button"],
             ["FR11", "A user shall ask a safety question and receive an answer from the assistant", "POST /api/ai/ask; AI Guardian screen"],
             ["FR12", "Every owner-scoped route shall refuse another user's data", "owner/user id checks in each route; probes in Chapter 7"],
             ["FR13", "The app shall be installable and usable full-screen on a phone", "vite-plugin-pwa manifest and service worker"]],
            "Functional requirements", widths=[0.08, 0.57, 0.35], font=9.5)
    sec_requirements_lifecycle(d)


def sec_requirements_lifecycle(d):
    d.h2("Session Lifecycle Requirements")
    d.p("An emergency session has two states, `active` and `cancelled`. The rules below are enforced in the SOS routes; a request that breaks them is refused with "
        "HTTP 404 (not the owner's session) or 400 (session not active).")
    d.table([["From", "To", "Who may do it", "Side effect"],
             ["(none)", "active", "Signed-in user", "Session and first ping created; share token issued; guardians alerted (best effort)"],
             ["active", "active", "Owner", "Location ping stored; viewers receive a location message"],
             ["active", "cancelled", "Owner", "`ended_at` set; viewers receive a cancelled message"],
             ["cancelled", "any", "Nobody", "Location pushes are refused (HTTP 400); the tracking page stays readable"]],
            "Session state transitions", widths=[0.2, 0.22, 0.2, 0.38], font=9.5)
    d.p("The `trigger` value (`manual` or `safephrase`) and the coordinates are not validated by the server, and the cancel route does not check that the session is "
        "still active (so, by the code, cancelling twice succeeds twice); both are noted among the known gaps.")


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([["ID", "Requirement", "How it is met / measured"],
             ["NFR1 Performance", "Interactive operations shall respond within a fraction of a second on a laptop", "Median 2.1 ms health, 31.1 ms risk list, 4.9 ms profile, 14.7 ms location push, 8.3 ms track page, 13.3 ms evidence 100 KB, 279.0 ms login (bcrypt), 1.6 s route plan with live OSRM"],
             ["NFR2 Live delay", "Guardians shall see a new position quickly", "WebSocket delay 15.4 ms mean with 1 viewer, 14.6 ms with 5 (local machine, 30 trials)"],
             ["NFR3 Security", "Passwords hashed, tokens signed, data owner-scoped", "bcrypt, HS256 JWT [19], the owner and token probes all pass; known gaps listed (public evidence URL, no lockout, no expiry of links)"],
             ["NFR4 Integrity", "Evidence shall show tampering", "SHA-256 at upload; one flipped bit changes the digest (tested); no verify route"],
             ["NFR5 Reliability", "Failures shall be reported plainly", "Alert delivery reported per guardian; OSRM failure is 502; assistant failure is shown as a friendly message; a Gemini timeout still returns 500 (known gap)"],
             ["NFR6 Usability", "Few taps in an emergency; plain labels; responsive layout", "Persistent SOS button, hold-to-cancel with progress, bottom navigation on phones"],
             ["NFR7 Portability", "Runs on Windows with Python 3.11 and Node.js", "Run and measured on Windows 11, Python 3.11.9, Node 24.19.0, Chrome"],
             ["NFR8 Maintainability", "Configuration outside the code; automated tests", "`.env` settings; 57 pytest tests; strict TypeScript, `npm run build` passes"],
             ["NFR9 Honesty", "Limits of the data shall be visible to the user", "Planner and landing page state that scores use 2001-2012 district data"]],
            "Non-functional requirements", widths=[0.19, 0.31, 0.5], font=9.5)
    d.p("**Assumptions.** The system assumes that the user's device gives a position, that guardians have supplied at least one reachable channel, that a browser with speech "
        "recognition is used for SafePhrase, and that the free outside services are reachable. **Constraints.** The prototype runs as one process with a SQLite file, "
        "the district table is loaded once from the CSV at start-up, and the risk tiers can only be as good as the 2001-2012 counts they come from.")


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.table([["Item", "Requirement"],
             ["Machine used for development and measurement", "12th Gen Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, no discrete GPU"],
             ["Disk", "Small: the two CSV datasets, the 467-row tables and a 3 KB model file; evidence files grow with use; the Python environment and `node_modules` need additional space"],
             ["User device", "A phone or computer with Chrome or Edge, a location permission, and microphone and camera permissions for SafePhrase and evidence; a battery reading is shown only where the browser exposes it"],
             ["Minimum machine", "Not measured; the system was run only on the machine above"],
             ["Python and Node", "Python 3.11.9; Node.js 24.19.0"],
             ["Back-end libraries", "FastAPI 0.115.6, Uvicorn 0.32.1, SQLAlchemy 2.0.36, PyJWT 2.10.1, bcrypt 4.2.1, httpx 0.28.1, websockets 14.1, pandas 2.2.3, NumPy 2.1.3, scikit-learn 1.5.2, joblib 1.4.2, pytest 9.1.1"],
             ["Front-end libraries", "React 19.0.1, Vite 6, Tailwind CSS 4.1, Leaflet 1.9.4, TypeScript 5.8, vite-plugin-pwa 0.21"],
             ["Database", "SQLite (file `data/app.db`) through SQLAlchemy"],
             ["External services", "OSRM demo server, Nominatim, OpenStreetMap tiles, Gemini API (key), Telegram Bot API (token), Gmail SMTP (address and app password)"],
             ["Phone testing", "A Cloudflare quick tunnel gives an HTTPS address (needed for geolocation, microphone and the PWA install)"],
             ["Browser", "A current Chrome was used for all captures; other browsers were not tested"]],
            "Hardware and software requirements", widths=[0.28, 0.72], font=9.5)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.p("SHEGUARD has one signed-in role and one link-based viewer. The abstract of the project mentions role-based access; in the implementation there is no "
        "administrator and no role column. Authorisation is by ownership: every protected route loads the user from the JWT and compares it with the owner of the "
        "guardian, session or evidence row.")
    d.table([["Actor", "Can do", "Cannot do"],
             ["User (signed in)", "Manage own guardians; plan routes; set SafePhrases; start, update, cancel and read own SOS sessions; upload and list evidence of own sessions; ask the assistant; search places", "Read, update or cancel another user's session, guardians or evidence (404)"],
             ["Guardian (link holder)", "Open `/track/{share_token}`; read the session status, name, path and last position; receive live pushes", "Log in, change anything, or see any other session; the link is the only credential"],
             ["Visitor (not signed in)", "Read the landing page; list the district risk areas (`GET /api/risk/areas`); register and log in", "Call any other protected route (401)"]],
            "Actors and permissions", widths=[0.2, 0.48, 0.32], font=9.5)
    d.paras(
        "**Constraints.** A password must have at least six characters and an email must be valid; there is no strength rule. A location push is accepted only for an "
        "active session of the caller. Evidence must be of kind `photo` or `audio` and non-empty; there is no size limit. The browser, not the server, enforces the "
        "three-second hold.",
        "**Known gaps.** The prototype does not range-check coordinates, does not validate `trigger`, accepts any WebSocket token, does not expire tracking links, serves "
        "stored evidence files without authentication, has no login lockout and has no real Row Level Security. These gaps are recorded as expected-failure tests and "
        "discussed in Chapter 7.")
