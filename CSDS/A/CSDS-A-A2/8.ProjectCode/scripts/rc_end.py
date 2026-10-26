"""Chapters 9 and 10, references, design decisions, and the appendices."""
from __future__ import annotations

from doc_common import FF, FV, LT, LV, PB, REFERENCES, SHOTS, pct
from rc_method import excerpt
from rc_results import SCREENS


def sec_decisions(d):
    d.h2("Implementation Decisions and their Reasoning")
    d.table([
        ["Decision", "Alternatives considered", "Reasoning"],
        ["Pre-trained models, no training", "Train a recogniser per class (as the base paper does)", "ArcFace embeddings need one reference photo and no retraining; training data would have to be collected and protected"],
        ["Random active challenge for liveness", "Passive anti-spoofing model; blink detection", "No extra model; works on any camera; transparent thresholds; cannot be prepared in advance. Its weakness against rotated and multiple photos was then measured"],
        ["Two still photographs instead of video", "Continuous video capture", "Works with a browser file upload and a phone camera alike; small payload; simple server logic"],
        ["Thin FastAPI layer over core/", "Rules inside the HTTP handlers", "One implementation shared with the Streamlit UI and with scripts and tests"],
        ["Wizard state on the server", "State in the browser", "Steps cannot be skipped (409); the random challenge and photos never leave the server's control"],
        ["JWT with a device claim", "Cookie sessions", "Stateless API for phones; a stolen token fails on another device"],
        ["Device hash from headers plus X-Device-Id", "Cookies only", "Stable across requests; combined with a per-browser identifier"],
        ["Embeddings stored, photographs not", "Store photographs", "Smaller, less sensitive data; the duplicate scan needs only vectors"],
        ["Haversine, tolerance and accuracy gate", "Vincenty; no tolerance", "0.47% error is negligible against GPS noise; tolerance and gate absorb poor fixes"],
        ["Conservative thresholds (0.40 and 0.45)", "Equal-error threshold (0.19)", "Margin against look-alikes; measured cost 1.3-2.9% retakes or missed duplicates"],
        ["SQLite", "PostgreSQL (the abstract mentioned Supabase)", "Zero setup for one college; adequate for the measured load; PostgreSQL is available by `DATABASE_URL`"],
        ["FastAPI and React", "Django REST Framework (the abstract), Streamlit only", "Typed models and automatic docs; a responsive phone-first interface; Streamlit kept as the original UI"],
        ["Public benchmark and attack experiments", "Only demo runs", "Gives numbers that can be reproduced and exposes the weak points"],
    ], "Implementation decisions", widths=[0.26, 0.26, 0.48], font=9)


# ------------------------------------------------------------------ Chapter 9 and 10
def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project set out to make classroom attendance fast and hard to fake. The result is Attendance Magic, a web application in which faculty open "
        "a time-bound, geo-fenced session and share a link or QR code, and students check in from a phone. The server runs a fixed chain of checks: eligibility "
        "(session window, roll pattern, repeat marking, device binding), a GPS geo-fence, a random live facial challenge measured on MediaPipe Face Mesh landmarks, and a "
        "face verification with InsightFace embeddings that requires both photos to show the same person, the enrolled person and nobody already recorded in the "
        "session. Every attempt is logged with its stage and reason, and faculty see live records, a map, the log, analytics and an Excel export.",
        "No model was trained. The contribution is the verification chain, its thresholds, the application around it and the evidence: the thresholds were "
        "measured on the public LFW benchmark, the liveness check was attacked with rotated and multiple photographs, and the application was tested with 23 pytest "
        "tests and a 41-check API smoke test.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.p("All six project objectives were implemented, and a seventh (verification) was added; the objectives table at the end of Chapter 8 lists the evidence. Objective 4 (liveness) is "
        "implemented with a measured weakness that is described below.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.numbered([
        f"On the LFW verification protocol the deployed identity threshold (0.40) accepts {pct(FV['at_identity_threshold']['tar'])} of same-person pairs and none of {FV['impostor_pairs']:,} different-person pairs; the area under the ROC curve is {FV['auc']:.3f} and the equal error rate {pct(FV['eer'], 2)}.",
        f"The duplicate threshold (0.45) flags {pct(FV['at_duplicate_threshold']['tar'])} of same-person pairs as the same face, so a second identity using the same face is caught in almost all cases.",
        "A single stolen photograph is rejected by seven of the eight random challenges; a photograph that already shows closed eyes passes the eye challenge 8.2% of the time.",
        "The liveness check is the weakest link: a photograph rotated by 15 degrees or more passes both tilt challenges (98-99%), and an attacker with several photographs of the victim passes the full chain 49-96% of the time depending on the challenge.",
        f"A check-in costs about {LT['C_http_ms']['checkin_total_after_login']['p50']:.0f} ms of server time on a desktop CPU, dominated by two ArcFace embeddings (about {LT['B_stage_ms']['insightface_embed']['p50']:.0f} ms each).",
        f"The single-face rule rejected {pct(FF['rate'])} of LFW photographs, so retakes are a real part of the user experience.",
        "The haversine distance is accurate to 0.47%; the real limit of the geo-fence is GPS noise, which should be taken into account when setting the radius.",
    ])


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.bullets([
        "Lecture, laboratory and tutorial attendance in colleges, with a faculty laptop and student phones.",
        "Attendance at examinations or invigilated events where presence in a room matters (with a smaller radius).",
        "Training sessions and workshops that need a verifiable attendance record with an audit trail.",
        "A teaching platform for face-recognition, liveness and web-security topics, because every decision is transparent and reproducible.",
    ])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        "No live-camera, phone or volunteer trial; the genuine pass rate of the challenges and the real retake rate are unknown.",
        "Liveness is defeated by rotated photographs and by banks of photographs; there is no texture, depth or video-based anti-spoofing.",
        "GPS accuracy, indoor drift and fake-location apps were not studied beyond a simulation.",
        "Single-process SQLite deployment with no load test; the default JWT secret and the manual-location option must be changed for real use.",
        "Evidence comes from public news photographs and a demo set, not from the institution's students.",
    ])


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "**Stronger liveness.** Reject a challenge frame that is only a rotation of the neutral frame (for example by checking background and perspective consistency), require several short challenges in a time-limited capture, and add a passive anti-spoofing model such as silent-face anti-spoofing [5].",
        "**Threshold calibration on real selfies.** Collect consented selfies, measure the genuine pass rate and retake rate of each challenge, and tune the neutral-frame and single-face rules accordingly.",
        "**Better reference enrolment.** Enrol from several photographs and keep the best embedding, to lower the 1.3% false-reject rate.",
        "**Security hardening.** Rate limiting and lockout on sign-in, a strong secret generated at set-up, disabling manual location in production, and a dependency audit.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "E-mail or in-app notification to students who were blocked, with the reason and a retry link.",
        "Attendance percentage reports per student and per course, with shortage alerts.",
        "Multiple faculty per course, an administrator role and department-level reports.",
        "Offline-tolerant check-in with a short grace window for poor connectivity.",
        "An export to the institution's ERP or LMS format.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets([
        "Serve over HTTPS (a reverse proxy with a certificate) so that phone cameras and GPS work without workarounds.",
        "Switch to PostgreSQL through `DATABASE_URL` and test it; run several API workers with the models loaded once per worker.",
        "Move the check-in wizard state from memory to a shared store so that a restart or a second worker does not lose it.",
        "Measure concurrent load; the duplicate scan is linear (41 ms for 5,000 faces) and the embedding takes about 0.18 s per photograph, so a GPU or a small thread pool would raise the ceiling.",
        "Package with containers and document backup of the database, which holds the face embeddings.",
    ])


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "A user study on usability and acceptance, including privacy attitudes towards face capture in class.",
        "Evaluation of liveness on a public presentation-attack dataset so that the active challenge can be compared with passive methods [12].",
        "Detection of fake GPS and of screen replay (moire, specular reflection) in the challenge photographs.",
        "Fairness evaluation of the face-matching thresholds across skin tones, ages and lighting.",
        "A privacy-preserving design that never stores face embeddings centrally (on-device matching with a signed result).",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, r in enumerate(REFERENCES, 1):
        p = d.p(f"[{i}]\t{r}", align="left", line=1.15, space_after=4)
        p.paragraph_format.left_indent = __import__("docx").shared.Inches(0.45)
        p.paragraph_format.first_line_indent = __import__("docx").shared.Inches(-0.45)
        p.paragraph_format.tab_stops.add_tab_stop(__import__("docx").shared.Inches(0.45))


# ------------------------------------------------------------------ appendices
def appendix_a(d):
    d.p("This appendix lists further code that complements Section 6.8 (the geo-fence, liveness, face decision, eligibility and pipeline are listed there).")
    d.h2("Token and Password Handling")
    d.code(excerpt("core/auth.py", 19, 37), "core/auth.py: PBKDF2 password hash and verification")
    d.code(excerpt("core/auth.py", 54, 93), "core/auth.py: JWT issue and verification with the device claim")
    d.h2("Face Embedding and Single-Face Rule")
    d.code(excerpt("core/face_match.py", 58, 85), "core/face_match.py: embed, cosine and byte conversion")
    d.h2("Device Fingerprint")
    d.code(excerpt("core/device.py", 16, 27), "core/device.py: device hash")
    d.h2("Liveness Step of the Check-in Wizard")
    d.code(excerpt("backend/api.py", 538, 564), "backend/api.py: POST /api/checkin/{token}/liveness")
    d.h2("Face Step and Recording")
    d.code(excerpt("backend/api.py", 567, 606), "backend/api.py: POST /api/checkin/{token}/face")


def appendix_b(d):
    d.h2("Installation")
    d.numbered([
        "Install Python 3.11 (mediapipe 0.10.21 has no wheel for newer versions) and Node.js.",
        "Windows: run `setup.bat` once. It creates `venv\\`, installs `requirements.txt` and `backend\\requirements.txt`, seeds the demo accounts and runs `npm install` in `frontend\\`. The first run downloads the InsightFace `buffalo_l` model (about 280 MB) to `%USERPROFILE%\\.insightface`.",
        "Linux or macOS: `python3.11 -m venv .venv`, activate it, `pip install -r requirements.txt -r backend/requirements.txt`, `python scripts/seed_demo.py`, then `cd frontend && npm install`.",
        "Optionally copy `.env.example` to `.env` and set `AM_JWT_SECRET`, `AM_ALLOW_MANUAL_LOCATION=false`, ports and thresholds.",
    ])
    d.h2("Running")
    d.bullets([
        "Windows: `run.bat` starts the API on http://127.0.0.1:8102 and the React app on http://localhost:5102 and opens the browser; `stop.bat` stops both.",
        "Manual: `venv\\Scripts\\python -m uvicorn backend.api:app --host 127.0.0.1 --port 8102` and, in `frontend\\`, `npm run dev`.",
        "Original interface: `venv\\Scripts\\streamlit run app.py` (port 8501).",
        "Tests: `venv\\Scripts\\python -m pytest -q` (23 tests) and `venv\\Scripts\\python scripts\\smoke_test.py` (41 checks).",
    ])
    d.h2("Demo accounts")
    d.table([
        ["Role", "Login", "Password"],
        ["Faculty", "faculty@college.edu", "faculty123"],
        ["Students", "23K91A6706, 23K91A6740, 23K91A6757, 24K95A6704", "student123"],
    ], "Demo accounts created by scripts/seed_demo.py (change before real use)", widths=[0.2, 0.6, 0.2], font=10)
    d.h2("Faculty guide")
    d.numbered([
        "Sign in at the faculty portal and open **New session**.",
        "Enter the course code, name, section, date, start time and duration; set the classroom location with **Get my location** (or the manual tab for testing); set the radius (60 m is the default) and the allowed roll numbers (a pattern such as `23K91A67*` or an explicit list, which also lists absentees).",
        "Press **Create session**; show the QR code or send the link.",
        "Watch the session page: records appear with distance and scores; the **Verification log** shows blocked attempts and their reasons; the **Map** shows positions.",
        "Use **Students > Manage** to enrol a face or remove a student's device bindings; use **Close session now** when the class ends and **Export to Excel** for the report.",
    ])
    d.h2("Student guide")
    d.numbered([
        "Open the session link on your phone (or paste it on the check-in page) and sign in with your roll number and password. New students register first with a clear, frontal photograph.",
        "Allow location access and press **Get my location**, then **Verify my location**.",
        "Read the random challenge. Take photo 1 looking straight at the camera with your mouth closed; take photo 2 while performing the action. Camera access needs HTTPS on phones; otherwise use **Upload photo**.",
        "Press **Verify challenge**. If it fails, read the reason, take both photos again (a new challenge is issued); after three failures press **Start over**.",
        "The face match runs automatically; a green *Marked. Present.* screen means your attendance is recorded.",
    ])
    d.h2("Troubleshooting")
    d.table([
        ["Symptom", "Cause and remedy"],
        ["'GPS accuracy too low'", "Move near a window or outdoors and retry; faculty can increase the radius"],
        ["'This device is not registered to your account'", "Use your usual device or ask faculty to reset your devices"],
        ["'No face detected' or 'More than one face'", "Face the camera in good light with nobody behind you; retake"],
        ["Camera is off on a phone", "Open the site over HTTPS or use the upload tab"],
        ["'This login token was issued to a different device'", "Sign in again on this device"],
    ], "Common problems", widths=[0.40, 0.60], font=10)


def appendix_c(d):
    d.p("Additional screens of the application that are not shown in Chapter 8. Each caption names the screen; the behaviour of every screen is described in Chapter 8 and in the application guide of Appendix B.")
    rest = [(f, c) for f, c, _desc, in_main in SCREENS if not in_main]
    for i in range(0, len(rest), 2):
        d.figure_pair([(SHOTS / f, c) for f, c in rest[i:i + 2]], width=2.95, max_h=3.4)
