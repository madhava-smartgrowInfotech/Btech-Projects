"""Chapters 3 and 4: feasibility study, system requirements and analysis."""
from __future__ import annotations

from doc_common import LT

STAGE = LT["B_stage_ms"]
HTTP = LT["C_http_ms"]


def sec_feasibility_technical(d):
    d.h2("Technical Feasibility")
    d.p("Technical feasibility asks whether the required functions can be built with available technology on available hardware. The project answers by "
        "construction and measurement.")
    d.table([
        ["Requirement", "Technology chosen", "Evidence of feasibility"],
        ["Face landmarks on a phone photo", "MediaPipe Face Mesh 0.10.21 (bundled model, CPU)", f"{STAGE['mediapipe_landmarks']['p50']:.1f} ms per image (median)"],
        ["Face embeddings", "InsightFace buffalo_l on ONNX Runtime, CPU", f"{STAGE['insightface_embed']['p50']:.0f} ms per image (median)"],
        ["Whole check-in on the server", "FastAPI + SQLAlchemy + SQLite", f"median {HTTP['checkin_total_after_login']['p50']:.0f} ms, 95th percentile {HTTP['checkin_total_after_login']['p95']:.0f} ms (40 runs)"],
        ["Location on a phone browser", "Geolocation API; haversine on the server", "0.47% distance error against the ellipsoid"],
        ["Camera on a phone browser", "getUserMedia (HTTPS) or file upload", "Upload tab works everywhere; camera needs HTTPS on phones"],
        ["Faculty views", "React 19 + Vite 8, Leaflet, Recharts", "Production build in 23 s; 12 routes"],
        ["Reports", "pandas + openpyxl", "3-sheet workbook generated in memory"],
    ], "Technical feasibility", widths=[0.28, 0.38, 0.34], font=9.5)
    d.p("The only heavy component is the recogniser; at about 0.18 s per photograph on a desktop CPU it is acceptable for a check-in that a student performs "
        "once per class. The first start loads both models (0.8 s and 1.5 s measured) and InsightFace downloads its 280 MB `buffalo_l` pack once.")


def sec_feasibility_economic(d):
    d.h2("Economic Feasibility")
    d.p("Every component is open-source or free to use: Python, FastAPI, SQLAlchemy, SQLite, React, Vite, MediaPipe, InsightFace (the pre-trained model packs "
        "are used for research and education), OpenCV, pandas, openpyxl, Leaflet and OpenStreetMap tiles. There is no licence fee, no cloud bill and no API key. "
        "The system runs on a faculty laptop; students use phones they already own.")
    d.table([
        ["Item", "Attendance Magic", "Typical alternative"],
        ["Software licences", "None", "Per-seat licences for commercial attendance products"],
        ["Hardware", "Existing laptop (tested on a 6-core desktop CPU) and student phones", "Biometric readers or classroom cameras"],
        ["Hosting", "Local SQLite; optional institutional server", "Cloud subscription"],
        ["Maintenance", "Configuration through environment variables; one codebase for two UIs", "Vendor support contract"],
    ], "Cost comparison", widths=[0.24, 0.40, 0.36], font=10)
    d.p("The cost that remains is people's time: enrolling reference photographs and training faculty to create sessions. Both are short tasks "
        "(a session is created from one form).")


def sec_feasibility_operational(d):
    d.h2("Operational Feasibility")
    d.bullets([
        "**Faculty.** Create a session in one form, share a link or QR code, watch records arrive, close the session and export to Excel. No installation on the faculty side beyond starting the application.",
        "**Students.** Open the link on a phone, sign in, allow location, take or upload two photos and read the result; the wizard shows plain reasons for any failure and lets a student retry.",
        "**Administration.** Device resets and re-enrolment are available in the Students screen; every attempt is in the verification log.",
        "**Acceptance risks.** Students may object to face capture; the system stores embeddings rather than photographs, but a policy and consent process is the institution's responsibility. Users with poor cameras or lighting may need retakes (15.7% of LFW photos failed the single-face rule).",
    ])
    d.p("User-acceptance testing with real faculty and students was not carried out (Section 7.8); operational feasibility is therefore argued from the design and "
        "from the demo walkthrough rather than from user feedback.")


def sec_feasibility_schedule(d):
    d.h2("Schedule Feasibility")
    d.p("The repository history and the batch files show the order in which the work was done. Dates are those recorded in the files and the commit history; "
        "durations were not tracked.")
    d.table([
        ["Phase", "Work", "Evidence"],
        ["1", "Batch details, abstract, introduction, literature survey, objectives", "Batch documents dated 19 Sep 2026"],
        ["2", "Core service layer, Streamlit interface, tests, demo scripts", "Project prompts and scaffold committed 21 Sep 2026; 23 pytest tests"],
        ["3", "FastAPI layer and React frontend", "Frontend rebuilt and committed 14 Oct 2026"],
        ["4", "Evaluation, screenshots, diagrams, documents", "Measurements and screenshots generated 15 Oct 2026 (scripts/eval_*.py, capture_*.py)"],
    ], "Project phases", widths=[0.10, 0.52, 0.38], font=10)
    d.p("The scope was achievable in the academic year because the verification models are pre-trained: no data collection or training phase was needed.")


def sec_feasibility_summary(d):
    d.h2("Advantages and Constraints")
    d.table([
        ["Advantages", "Constraints"],
        ["No new hardware; runs on phones and a laptop", "Camera and GPS on phones need HTTPS"],
        ["Free software end to end; offline operation", "Single-process SQLite deployment; no load test"],
        ["Six independent checks, each logged with a reason", "Liveness can be beaten by rotated photos and photo banks"],
        ["Pre-trained models need no training data", "Models are used as published; thresholds tuned only by measurement"],
        ["One shared service layer for two interfaces", "GPS accuracy, indoor drift and mock-location apps not handled"],
    ], "Advantages and constraints", widths=[0.5, 0.5], font=10)


# ------------------------------------------------------------------------ Chapter 4
def sec_existing(d):
    d.h2("Existing System and its Limitations")
    d.p("Existing attendance practice in a college combines a paper register or roll call, an occasional shared link or QR code in the learning "
        "platform, and in some departments a biometric device or a face-recognition webcam. The base paper [1] is the representative of the last group.")
    d.table([
        ["Limitation", "Where it comes from", "Consequence"],
        ["Time lost and errors", "Roll call, paper registers, manual typing", "Less teaching time; wrong or missing marks"],
        ["Shareable proof", "Links and QR codes", "A student who is absent can mark present"],
        ["Spoofable identity", "Face recognition without liveness", "A photograph or video of a student is accepted"],
        ["No presence proof", "No location check", "Marking from outside the classroom"],
        ["Multiple identities", "No comparison of faces within a session", "One person marks several roll numbers"],
        ["Weak records", "CSV or paper only", "No reason or evidence stored for a disputed mark"],
    ], "Limitations of the existing system", widths=[0.24, 0.38, 0.38], font=10)


def sec_proposed(d):
    d.h2("Proposed System and its Advantages")
    d.p("Attendance Magic is a web application in which a faculty member opens a time-bound attendance session and shares a unique link or QR code. A student "
        "opens the link on a phone, signs in, and the server runs six checks in sequence; only a student who passes all of them is recorded as present. Each check "
        "closes one of the limitations above.")
    d.table([
        ["Check", "Rule", "Closes the gap of"],
        ["Eligibility", "Session live; roll matches the pattern; not already marked; device registered", "Late, wrong-class and repeat marking; shared devices"],
        ["Geo-fence", "GPS within radius + 15 m; accuracy at most 150 m", "Remote marking"],
        ["Live challenge", "Random action; Face Mesh metric exceeds the threshold; three tries", "A static photograph"],
        ["Frame consistency", "Both photos show the same person (cosine >= 0.45)", "Swapping people between photos"],
        ["Identity", "Live face matches the enrolled embedding (cosine >= 0.40)", "Marking for someone else"],
        ["Duplicate", "Live face does not match any other record in the session (cosine < 0.45)", "One person, several roll numbers"],
    ], "The checks of the proposed system", widths=[0.20, 0.50, 0.30], font=9.5)
    d.h3("Advantages")
    d.bullets([
        "Several independent checks that fail in different ways, so the chain is stronger than any single check.",
        "Fast for the student (about 0.56 s of server time per check-in) and for faculty (one form per session).",
        "Transparent: every outcome has a stored reason, and thresholds are visible in the configuration and on the result screen.",
        "Cheap and private: browser-based, free software, embeddings stored instead of photographs.",
    ])


def sec_requirements_functional(d):
    d.h2("Functional Requirements")
    d.table([
        ["ID", "Requirement", "Status"],
        ["FR1", "Faculty and students can register (students with a reference face) and sign in; sign-in returns a device-bound JWT", "Done"],
        ["FR2", "Faculty can create a session with course, section, start time, duration, centre, radius and allowed roll patterns", "Done"],
        ["FR3", "The system issues a unique link and a QR code for each session", "Done"],
        ["FR4", "A student can check in only while the session is live and only with an allowed roll number, once, from a registered device", "Done"],
        ["FR5", "The student's GPS position is compared with the geo-fence; poor accuracy is rejected", "Done"],
        ["FR6", "A random live challenge is issued; two photos are analysed; three failed tries lock the wizard", "Done"],
        ["FR7", "The live face is compared with the enrolled face and with other faces in the session", "Done"],
        ["FR8", "Every attempt (pass or block) is logged with its stage and reason", "Done"],
        ["FR9", "Faculty can view records, a map, the log and analytics, close a session, reset devices, re-enrol a face", "Done"],
        ["FR10", "Faculty can export Summary, Attendance (with absentees) and Verification Log to Excel", "Done"],
    ], "Functional requirements", widths=[0.09, 0.78, 0.13], font=9.5)


def sec_requirements_nonfunctional(d):
    d.h2("Non-Functional Requirements")
    d.table([
        ["ID", "Requirement", "How it is met / measured"],
        ["NFR1 Performance", "A check-in should take seconds", f"Median {HTTP['checkin_total_after_login']['p50']:.0f} ms server time (95th percentile {HTTP['checkin_total_after_login']['p95']:.0f} ms)"],
        ["NFR2 Security", "Passwords hashed, tokens signed and device-bound, role checks", "PBKDF2 200,000 iterations; JWT HS256 with device claim; 401/403 tests"],
        ["NFR3 Privacy", "Minimise stored biometric data", "Embeddings only; photos not written to disk"],
        ["NFR4 Usability", "Plain reasons; retry paths", "Reason text on every block; start over / retake buttons"],
        ["NFR5 Portability", "Run on Windows, Linux, macOS", "Python 3.11 and Node; scripts for Windows (setup.bat, run.bat) and Linux (run.sh)"],
        ["NFR6 Maintainability", "One implementation of the rules", "Thin API and Streamlit UI both call core/"],
        ["NFR7 Reliability", "Never write a record unless every check passed", "Eligibility re-checked before the record is written; unique constraint per session and student"],
        ["NFR8 Configurability", "Thresholds and limits adjustable", "All settings in config.py with environment overrides"],
    ], "Non-functional requirements", widths=[0.20, 0.34, 0.46], font=9.5)


def sec_requirements_platform(d):
    d.h2("Hardware and Software Requirements")
    d.h3("Hardware")
    d.table([
        ["Role", "Requirement"],
        ["Server / faculty machine", "x86-64 CPU (measured on an Intel Core i5-12500, 6 cores / 12 threads), 8 GB RAM recommended (15.7 GB available in the test machine), disk space for the Python environment, node_modules and the 280 MB InsightFace model pack; no GPU"],
        ["Student device", "Phone or laptop with a camera, GPS (phones) and a current browser"],
        ["Network", "Local network or internet between devices and the server; internet only for map tiles and first model download"],
    ], "Hardware requirements", widths=[0.28, 0.72], font=10)
    d.h3("Software")
    d.table([
        ["Layer", "Software and version"],
        ["Language and runtime", "Python 3.11.9 (mediapipe 0.10.21 has no wheel for newer Python); Node v24.19.0 for the frontend"],
        ["Computer vision", "mediapipe 0.10.21, insightface 2.0, onnxruntime 1.31.0, opencv-python-headless 4.10.0.84, numpy 1.26.4"],
        ["Backend", "fastapi 0.143.0, uvicorn 0.54.0, pydantic 2.14.1, SQLAlchemy 2.1.4, PyJWT 2.15.1, pandas 3.0.6, openpyxl 3.1.5, qrcode 8.2"],
        ["Original UI", "streamlit 1.64.0, streamlit-js-eval 1.0.0"],
        ["Frontend", "React 19, Vite 8, React Router 7, Leaflet, Recharts, Framer Motion, GSAP, Lenis, lucide-react"],
        ["Testing", "pytest 9.1.1, Playwright (screenshots and walkthroughs)"],
        ["Database", "SQLite (default); PostgreSQL through DATABASE_URL (untested)"],
    ], "Software requirements", widths=[0.24, 0.76], font=9.5)


def sec_roles(d):
    d.h2("User Roles and Constraints")
    d.table([
        ["Role", "Can", "Cannot"],
        ["Faculty", "Create and close own sessions, view records, map, log and analytics, export, list students, enrol faces, reset devices", "Mark attendance (HTTP 403 on the check-in endpoints); open another faculty's session (HTTP 404)"],
        ["Student", "Register, sign in, check in to a live session from a registered device, see own result", "Use faculty endpoints (HTTP 403); check in twice; check in from a second device without reset"],
        ["Visitor (no account)", "See the landing page and the public session header from a link", "Check in or see records"],
    ], "User roles", widths=[0.16, 0.44, 0.40], font=9.5)
    d.p("**Constraints.** Camera and GPS on phones need HTTPS (localhost is exempt on the laptop itself). Each student has one device by default "
        "(`AM_MAX_DEVICES_PER_STUDENT = 1`). A session window, radius and roll patterns are fixed by the faculty at creation. The check-in wizard keeps its "
        "state in server memory, so a server restart abandons wizards in progress (attendance records are unaffected).")
