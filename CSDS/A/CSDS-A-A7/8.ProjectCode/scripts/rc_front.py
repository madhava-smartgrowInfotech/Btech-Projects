"""Front-matter content for the SHEGUARD documents: abbreviations, the abstract, the keywords and the novelty section.

Every figure comes from docs/REPORT_FACTS.md. References are numbered as in doc_common.REFERENCES.
"""
from __future__ import annotations

ABBREVIATIONS = [
    ("AI", "Artificial Intelligence"), ("API", "Application Programming Interface"), ("ARI", "Adjusted Rand Index"),
    ("ASR", "Automatic Speech Recognition"), ("bcrypt", "Adaptive password-hashing function"), ("CORS", "Cross-Origin Resource Sharing"),
    ("CRUD", "Create, Read, Update, Delete"), ("CSS", "Cascading Style Sheets"), ("DB", "Davies-Bouldin (index)"),
    ("DFD", "Data-Flow Diagram"), ("ER", "Entity-Relationship"), ("FK", "Foreign Key"), ("GMM", "Gaussian Mixture Model"),
    ("GPS", "Global Positioning System"), ("GSM", "Global System for Mobile Communications"), ("HTTP", "Hypertext Transfer Protocol"),
    ("IoT", "Internet of Things"), ("IPC", "Indian Penal Code"), ("JSON", "JavaScript Object Notation"), ("JWT", "JSON Web Token"),
    ("LLM", "Large Language Model"), ("ML", "Machine Learning"), ("OSM", "OpenStreetMap"), ("OSRM", "Open Source Routing Machine"),
    ("ORM", "Object-Relational Mapping"), ("PWA", "Progressive Web App"), ("REST", "Representational State Transfer"),
    ("RLS", "Row Level Security"), ("SHA-256", "Secure Hash Algorithm, 256-bit"), ("SMTP", "Simple Mail Transfer Protocol"),
    ("SOS", "Save Our Souls (distress signal)"), ("SQL", "Structured Query Language"), ("UI", "User Interface"),
    ("UML", "Unified Modeling Language"), ("URL", "Uniform Resource Locator"), ("VAD", "Video Anomaly Detection"),
    ("WS", "WebSocket"),
]

ABSTRACT = [
    "Women face harassment, stalking and assault in isolated and in crowded public places. Most safety applications rely on the "
    "user opening the application and pressing an SOS button during the emergency, and most stop at sending one alert: they do "
    "not help to avoid risk beforehand, they do not keep guardians informed as the situation changes, and they rarely preserve "
    "evidence. The base paper by Agrawal et al. (IEEE Access, 2024) clusters districts by crime, police presence and "
    "infrastructure and designs a cab-service alert for deviations into unsafe areas, but its results are anticipated outcomes "
    "and it has no emergency functions.",
    "This project builds SHEGUARD, an installable web application for the whole emergency lifecycle. District-level crimes "
    "against women data for 2001-2012 are reduced to one feature, the average number of counted crimes per reporting year, and "
    "K-Means (k = 3) groups 467 geocoded districts into 278 low, 148 medium and 41 high tiers. Alternatives returned by the "
    "OSRM routing service are scored by the tier of the nearest district at sampled points, with a night multiplier. In an "
    "emergency the user taps SOS or speaks a registered SafePhrase; a session starts, a private tracking link is created, and "
    "the position is pushed over a WebSocket to a read-only page that guardians open without logging in. Photographs and audio "
    "are stored with a time, a location and a SHA-256 hash; a three-second hold cancels the alert; and a Gemini-backed assistant "
    "answers safety questions. The back end is FastAPI with SQLite, the front end is React with TypeScript, and access is "
    "scoped to the logged-in user in the code. The batch abstract names Flutter, Supabase and Row Level Security; none of "
    "these was used.",
    "The study shows what the data and code actually deliver. The clustering has a silhouette of 0.580 and a Davies-Bouldin "
    "index of 0.531, but it amounts to two cut-offs (213.75 and 529.83 crimes a year) on one count; only 56.5% of districts were "
    "geocoded and none exist for Uttar Pradesh, West Bengal or Delhi, so the nearest district to Hyderabad is 149 km away. On "
    "16 real city pairs the night multiplier never changed the recommended route. The SafePhrase matcher, tested on written "
    "transcripts, triggered on 54.2% of phrase variants at its default level with no false trigger in 80 checks. A WebSocket "
    "push reached a viewer in about 15 ms locally, median API times ranged from 2 to 31 ms for ordinary calls, with login "
    "at 279 ms, a 5 MB evidence upload at 61 ms and a live route plan at 1.6 s, and 51 of 57 automated tests pass, the other six documenting real defects. Alert delivery by Telegram and "
    "email and the Gemini assistant could not be demonstrated: no credentials were configured, and the assistant key returned "
    "quota errors. The report states these limits and defects plainly and lists the work needed to move from a validated "
    "prototype to field use.",
]
KEYWORDS = "Keywords: women's safety, safe route, K-Means clustering, emergency SOS, live location tracking, evidence integrity, SafePhrase."


def novelty(d):
    d.h2("Novelty Compared with the Base Paper")
    d.p("The base paper [1] (Agrawal et al., IEEE Access, 2024) is a clustering-and-GPS framework for women's safety on urban "
        "journeys: it ingests public data, clusters regions with K-Means and Gaussian mixture models, and designs a cab-service "
        "integration with deviation alerts. SHEGUARD keeps the first idea, grouping districts into risk tiers without labels, "
        "and uses it to guide routes on a map. The rest is different: SHEGUARD adds the functions that the base paper does not "
        "have, and it leaves out data and analysis that the base paper has. The table lists the differences. None of the "
        "additions is claimed as new to the field, and the two works are not compared numerically because their data, "
        "features and tasks differ.")
    d.table([["Element", "Base paper [1]", "SHEGUARD (this project)"],
             ["Stage of the incident", "Before and during a journey: area risk, safe path, deviation alert", "Before (route scoring), during (SOS, live link) and after (hashed evidence)"],
             ["Input data", "Population 2001 and 2011, IPC 2013, literacy, expenditure, police strength, forest cover", "District crimes against women 2001-2012 reduced to one count per year; 467 geocoded districts"],
             ["Learning", "K-Means and Gaussian mixture, 3-4 clusters chosen with silhouette, Calinski-Harabasz, Davies-Bouldin and BIC", "K-Means with k = 3 fixed; indices reported; Ward and Gaussian mixture tiers compared in the study"],
             ["Reference scoring", "Dummy data of globally safest cities, score 100 for the best cluster", "Tier weights 1.0, 2.5 and 5.0; night factor 1.6"],
             ["Travel integration", "Maps APIs and cab vendors; 1.96 times buffer; alerts and rerouting (not implemented or evaluated)", "OSRM alternatives scored and sorted; recommended route highlighted on a Leaflet map"],
             ["Activation", "None", "One-tap SOS; spoken SafePhrase with four sensitivity levels; three-second hold to cancel"],
             ["Guardians", "Cab drivers are alerted", "Telegram and email to each guardian; private tracking link; live position over a WebSocket with no guardian login"],
             ["Evidence", "None", "Photograph and audio with time, location and SHA-256 hash"],
             ["Assistant and platform", "None", "Gemini-backed assistant; installable React web application; FastAPI and SQLite"],
             ["Access control", "Not discussed", "Per-user filtering of every query, bcrypt and signed tokens; no Row Level Security, no administrator role"],
             ["Evidence of performance", "Anticipated outcomes; cluster-selection tables", "Measured clustering quality, route-scoring study, SafePhrase matcher test, API latencies, 57 automated tests and live access-control probes"]],
            "What differs from the base paper", widths=[0.2, 0.38, 0.42], font=9.5)
    d.p("The abstract of the batch names a Flutter application, a Supabase back end and Postgres Row Level Security. These were "
        "not used: the delivered system is a React and TypeScript progressive web app with a FastAPI and SQLite back end, "
        "and the isolation of users' data is done in the application code. The batch abstract also names a Smart SOS; the "
        "delivered activation is a one-tap button and a spoken phrase, with no shake, power-button or automatic trigger. "
        "What the base paper has and SHEGUARD lacks is also stated plainly: population-normalised and multi-feature data, "
        "police-presence and socio-economic features, an analysis that selects the number of clusters, and the cab-service "
        "integration with deviation alerts.")
