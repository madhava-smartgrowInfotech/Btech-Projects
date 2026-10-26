"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations, organisation (SHEGUARD).

Every figure comes from docs/REPORT_FACTS.md and experiments/study/*.json. References are numbered as in doc_common.REFERENCES.
"""
from __future__ import annotations

from doc_common import PRODUCT


def sec_domain(d):
    d.h2("Introduction to the Project Domain")
    d.paras(
        "Women's safety in public places is a continuing social concern. Harassment, stalking and assault occur on isolated streets "
        "late at night and also in crowded places such as buses, markets and stations. Technology has long been proposed as a "
        "remedy. A systematic review of Internet-of-Things (IoT) devices for women's safety covering studies from 2016 to 2022 [2] "
        "describes wearables with pulse and pressure sensors, alert transmission over GPS, GSM and Raspberry Pi boards, and a few "
        "machine-learning classifiers, and concludes that systems with automatic activation, less human interaction and better "
        "accuracy are still needed. Smartphone applications that send a location with an emergency message are the cheapest "
        "form of the same idea [3], [4], [5], [6].",
        "The domain of this project is **personal safety on a smartphone, across the whole emergency lifecycle**: before a journey "
        "(choose a route with less exposure to risk), at the moment of danger (start help with as little effort as possible), "
        "during the emergency (keep trusted people informed of where the user is) and after it (keep evidence that cannot be "
        "quietly altered). It sits between several established areas. Location intelligence supplies routes and maps from "
        "OpenStreetMap data [17], [18]. Unsupervised learning supplies a way to group areas into risk tiers when no labelled "
        "ground truth exists [9], [10], [14], [15]. Real-time web communication supplies the live location channel [20]. Speech "
        "recognition in the browser supplies a hands-free trigger [25]. Cryptographic hashing supplies a fingerprint for evidence "
        "files [22], and a large language model supplies an assistant that answers safety questions [26].",
        f"**{PRODUCT}**, the system built in this project, combines these ideas into one installable web application. A user "
        "registers, adds trusted guardians, and can plan a route between two places in India; each OpenStreetMap routing "
        "alternative is scored against a table of 467 districts that K-Means has grouped into low, medium and high risk tiers. "
        "In an emergency the user taps SOS or speaks a pre-registered SafePhrase; the application creates a session, shares a "
        "private tracking link with the guardians, streams the user's position to anyone viewing the link over a WebSocket, lets "
        "the user capture photographs and audio that are stored with a time, a location and a SHA-256 hash, and can be cancelled "
        "only by a three-second hold. A Gemini-backed assistant answers safety questions. Everything is scoped to the logged-in "
        "user, and guardians need no account.",
        "One point of wording must be made at the outset. The batch abstract names Flutter, Supabase and Postgres Row Level "
        "Security. What was built and measured is a **React and TypeScript web application that installs as a progressive web "
        "app, a FastAPI back end and a SQLite database**, with per-user filtering in the code in place of database row-level "
        "security. The reasons and consequences are explained in Chapters 4 to 6, and the difference is stated again wherever "
        "it matters.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "Four observations motivated the project, and they follow the batch introduction. First, women face harassment, stalking "
        "and assault in isolated as well as crowded places, so a safety aid cannot assume that help is nearby or that the user is "
        "alone. Second, most safety applications reduce the problem to an SOS button: the user must open the application, find "
        "the button and press it, and in a real emergency a frightened user may be unable to do several things in sequence. "
        "Government helplines and panic-button applications connect the user to a call centre or a contact, and IoT wearables send "
        "a GPS position when a button is pressed [2], [6], but each of them needs a deliberate action at the worst moment.",
        "Third, most applications stop at the alert. Map applications suggest the fastest route and do not consider safety, so "
        "prevention is left to the user; guardians receive a one-time message rather than a position that keeps updating, so "
        "the people who want to help cannot follow the user; and evidence such as audio, images, times and places is rarely "
        "captured securely, so after an incident there is little that can be relied on. Fourth, research systems that do use "
        "data, such as the base paper [1], concentrate on the area-risk side, clustering regions by crime, police presence and "
        "infrastructure, and treat the in-the-moment side as outside their scope.",
        "Taken together, these observations show a gap between what a route-risk study provides and what a user needs from a "
        "single application at each stage of an incident. The base paper [1] demonstrates that unsupervised clustering of "
        "district-level data can produce safety zones and that map services can carry them to the traveller. This project asks "
        "whether the same safe-route idea can be placed inside a complete platform, with hands-free activation, a live guardian "
        "link and tamper-evident evidence, and how honestly such a platform can be built and measured by a student team without "
        "access to police data, a deployed alert gateway or a field trial.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.paras(
        "Women face safety threats in both isolated and crowded public places. Existing applications require manual SOS "
        "activation, which is difficult in an emergency. Most solutions stop at sending an alert and do not support prevention or "
        "follow-up. Emergency evidence is rarely captured or stored securely.",
        "**Formal statement.** Given a user's start point and destination, a set of trusted guardians, and the user's position "
        "during an emergency, (i) rank the routing alternatives between two places by the risk of the districts they pass "
        "through, with a higher weight at night; (ii) start an emergency session from a single tap or from a spoken phrase that "
        "the user registered; (iii) deliver a private tracking link to every guardian and update their view of the user's "
        "position as it changes, without requiring them to log in; (iv) capture photographs and audio during the session and "
        "store each with a time, a location and a hash that exposes later alteration; (v) answer the user's safety questions; and "
        "(vi) allow only the user to see and change their own guardians, sessions and evidence.")
    d.p("The problem is a systems problem as much as a modelling problem: six functions have to work together, on a phone, at "
        "short notice, and be linked to the same emergency record.")


def sec_need(d):
    d.h2("Need for the Proposed System")
    d.p("A safety platform is needed that helps prevent risk, activates help with minimal effort, keeps guardians informed and "
        "preserves evidence. Separate tools for each task leave the user to combine them at the moment when the user is least able to, "
        "and an alert without a live position or without evidence is of limited use afterwards. The need can be stated as four "
        "requirements.")
    d.bullets([
        "**Prevention.** The user should be able to compare routes before travelling and see which pass through districts of higher recorded risk.",
        "**Low-effort activation.** Help should start from one tap or one spoken phrase, and a stray tap must not end an alert once it has begun.",
        "**Continuous information.** Guardians should see a position that keeps moving, through a link that needs no account, until the user confirms safety.",
        "**Traceable evidence.** Photographs and audio should be kept with a time, a place and a hash, and every record should be visible only to its owner and to those holding the session link.",
    ])
    d.p("SHEGUARD is proposed to meet these four requirements in one application, and the evaluation in Chapter 8 states how far each is met.")


def sec_objectives(d):
    d.h2("Objectives")
    d.p("The project has six objectives, taken from the batch objectives document:")
    d.numbered([
        "Provide Safe Route guidance using available safety information.",
        "Enable quick emergency activation through SafePhrase and Smart SOS (delivered as a one-tap SOS and a spoken SafePhrase; there is no shake, power-button or automatic trigger).",
        "Share live location with trusted guardians during an emergency session.",
        "Preserve emergency evidence such as timestamps, location, audio and images securely.",
        "Offer AI-powered safety assistance using the Gemini API.",
        "Protect user data with role-based access and Row Level Security (delivered as per-user filtering of every query and a share-token view for guardians; there is no database row-level security and no role beyond the user).",
    ])
    d.p("Chapter 8 measures each of these objectives against the results, and states where an objective was met only in part.")


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets([
        "User registration and login with bcrypt-hashed passwords and a signed token, and a profile of trusted guardians (name, phone, email, Telegram chat id).",
        "Safe Route: place search, route alternatives from the public OSRM server, a 467-district risk table from K-Means (k = 3) on district-level crimes-against-women data for 2001-2012, a per-route risk score with a night multiplier, and a map with a risk layer.",
        "Emergency activation by a one-tap SOS button or by a SafePhrase heard through the browser's speech recognition, with sensitivity levels and hold-for-three-seconds cancellation.",
        "A live location session that streams the user's position about every four seconds to a read-only tracking page over a WebSocket, with no guardian login.",
        "Alert messages to guardians by Telegram and email (implemented, but not exercised with real credentials in this work).",
        "Evidence capture: photograph and audio clip saved with timestamp, location and SHA-256 hash.",
        "A safety assistant that forwards questions to the Gemini API with a safety-focused system prompt.",
        "An installable progressive web application, a SQLite database of six tables, and an automated test suite with measured API latencies.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "A native Flutter application and a Supabase back end, which the batch abstract names; the platform is a React web application with a FastAPI and SQLite back end.",
        "Postgres Row Level Security and an administrator or police role; access control is per-user filtering in the code.",
        "Automatic triggers such as shaking the phone, pressing the power button, fall detection or listening while the screen is off.",
        "Wearable hardware, IoT sensors, cab-vendor integration and deviation alerts of the kind designed in the base paper [1].",
        "Live police, crowd or lighting data, population-normalised crime rates, and any validation of the risk tiers against real incidents.",
        "Video evidence, cloud storage of evidence, and integration with official emergency services; the application tells the user to call the emergency number and does not call it.",
        "Production hardening such as HTTPS termination, rate limiting, a hosted database, migrations and load testing.",
    ])
    d.h3("Assumptions")
    d.bullets([
        "The user's browser is Chrome or Edge (for speech recognition), has location permission and a network connection, and the page is open in the foreground.",
        "A guardian has a Telegram chat id, an email address, or the tracking link by some other route; delivery of the link is best-effort.",
        "District-level crime counts for 2001-2012 are an acceptable, if coarse and old, proxy for the relative exposure of an area.",
        "The application runs on one machine with a single SQLite database for one demonstration deployment, and the public OSRM and Nominatim servers are available.",
    ])


def sec_contrib(d):
    d.h2("Key Contributions")
    d.numbered([
        "**An integrated platform for the whole emergency lifecycle.** One application that links route guidance, one-tap and spoken activation, live guardian tracking, hashed evidence and an assistant, with 19 REST endpoints, one WebSocket route and six database tables, extending the safe-route idea of the base paper [1] into a working system.",
        "**An area-risk table with its limits measured.** K-Means (k = 3) on one feature, the average number of counted crimes per reporting year, groups 467 geocoded districts into 278 low, 148 medium and 41 high tiers (silhouette 0.580, Davies-Bouldin 0.531). The study shows that this amounts to two cut-offs (213.75 and 529.83 crimes a year), compares other tiering methods (agreement 49% to 83%), and shows that 56.5% of districts were geocoded and that none exist for Uttar Pradesh, West Bengal or Delhi.",
        "**A route scorer evaluated on real routes.** Alternatives from OSRM are scored by sampling the polyline and weighting the nearest district's tier 1.0, 2.5 or 5.0. On 16 real city pairs, 10 had two alternatives; the night multiplier of 1.6 never changed the recommended route, and the safest alternative cost 3.7 minutes more on average.",
        "**A SafePhrase matcher with a measured trade-off.** A word-window matcher over the browser transcript, with four sensitivity levels, triggered on 54.2% of 24 written phrase variants at the default level with no false trigger in 80 checks, and on 100% at the most sensitive level with 10% false triggers.",
        "**Live guardian tracking and tamper-evident evidence.** Position pushes reach a viewer in about 16 to 20 ms on the local machine; each photograph or audio file is stored with a SHA-256 hash that changes if a single bit is flipped.",
        "**A tested and honestly documented code base.** A suite of 57 automated tests (51 pass, 6 expected failures that document real defects), live access-control probes, measured latencies and the defects found by testing are reported instead of hidden.",
    ])
    d.p("Contributions 1, 5 and 6 are engineering contributions; contributions 2, 3 and 4 are those whose quality was measured. "
        "Compared with the base paper [1], which clusters multi-source district data (population, literacy, expenditure, police "
        "strength, forest cover) with K-Means and Gaussian mixtures and designs a cab-service deviation alert, this project uses "
        "one feature and a simpler tiering, and adds the in-the-moment functions the base paper does not have. The data, features "
        "and tasks differ, so no numeric head-to-head is claimed.")


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.bullets([
        "**Old, coarse, count-based data.** The risk table uses district counts for 2001-2012, not rates per population, and 40% of the counted crimes are cruelty by husband or relatives, which says little about street safety. Populous and well-reporting districts rank high.",
        "**Partial geocoding.** Only 467 of 827 district entries (56.5%) were geocoded; Uttar Pradesh, West Bengal, Delhi, Uttarakhand and Tripura have none. The nearest district to Hyderabad is 149.0 km away and to Lucknow 231.3 km, and the scorer has no distance limit.",
        "**One-feature clustering without ground truth.** The tiers are two thresholds on one number, fitted on all 467 points with no held-out set and no validation against incidents. Assignments near the cut-offs move with the K-Means initialisation (adjusted Rand index against the shipped tiers: minimum 0.659, mean 0.790 over 30 runs).",
        "**The night multiplier does not change the recommendation.** It scales every route by the same factor (16 of 16 pairs unchanged), and 6 of 16 trips returned only one route.",
        "**Alert delivery and the assistant were not demonstrated.** The Telegram and Gmail credentials were empty, so every delivery reports not sent; the Gemini key returned quota errors (0 of 10 probes answered), and a provider timeout returns a 500 error.",
        "**SafePhrase accuracy is unknown on real speech.** The matcher was tested on written transcripts only; the browser's recogniser accuracy was not measured, and it needs an open Chrome or Edge tab and an online service.",
        "**Defects found by testing.** Stored evidence files can be fetched without a token if the link is known; there is no upload size limit, no login lockout, no check of coordinate ranges, and no check of a WebSocket token; the tracking page keeps its location trail after a session ends.",
        "**Differences from the abstract.** There is no Flutter application, Supabase service, Row Level Security or automatic Smart SOS trigger; the application is a browser-based progressive web app.",
        "**Single machine, single database,** no load, concurrency or penetration testing, no test on real phones or with a screen reader, and no user study.",
        "**No numeric comparison with the base paper.** It reports anticipated outcomes and cluster-selection tables on multi-feature data; SHEGUARD reports measurements on one feature.",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem statement, objectives, scope, contributions, limitations"],
             ["2", "Literature Survey", "Base paper, related work by theme, datasets and algorithms, strengths and limitations, research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, platform, user roles"],
             ["5", "System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Pipeline, data, algorithms, mathematics, application, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, validation, performance, acceptance, limits"],
             ["8", "Results and Output Screens", "Output screens, measured results, comparison, failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, deployment, research"]],
            "Organisation of the report", widths=[0.1, 0.3, 0.6], font=10)
    (d.p if not getattr(d, "report", False) else (lambda *a, **k: None))("The report ends with the references, Appendix A (important code), Appendix B (installation and user guide) and Appendix C (additional screens).")
