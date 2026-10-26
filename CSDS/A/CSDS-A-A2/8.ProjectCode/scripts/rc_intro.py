"""Chapter 1 content (Introduction) and the scope / contributions / limitations sections shared with documents 9 and 10."""
from __future__ import annotations

from doc_common import FF, FV, LT, LV, PB, pct


def sec_domain(d):
    d.h2("Domain Overview")
    d.paras(
        "Attendance is a basic record of every educational institution. It decides whether a student is eligible to sit an examination, it supports "
        "scholarships and fee concessions, and it is the first signal that a student is falling behind. Because so much depends on it, the way attendance "
        "is captured matters: it must be quick enough not to eat into teaching time, accurate enough to be trusted, and hard enough to fake that a "
        "recorded presence really means the student was in the room.",
        "The project belongs to the domain of *intelligent attendance management*, which sits between three fields: web application engineering "
        "(sessions, authentication, records, reports), mobile-browser sensing (GPS position and camera capture on the student's phone) and "
        "computer vision (face detection, facial landmarks and face recognition). Each field is mature on its own. The difficulty, and the interest of the "
        "project, lies in joining them so that the strengths of one cover the weaknesses of another: a GPS fix can be spoofed but proves little about "
        "who holds the phone, a face match proves identity but not presence, and a live facial challenge proves that someone responded at this moment "
        "but not who they are.")
    d.h3("Attendance methods in use today")
    d.table([
        ["Method", "How it works", "Main weakness"],
        ["Roll call / paper register", "Faculty read names or pass a sheet", "Class time is lost; errors; a friend can answer for an absentee"],
        ["Shared link or QR code", "Students open a link or scan a code shown in class", "The link or photo of the code can be forwarded to anyone"],
        ["Biometric device (fingerprint)", "A shared reader at the entrance or in the room", "Hardware cost, queues, shared contact surface"],
        ["Camera face recognition", "A classroom camera or webcam identifies faces", "A photo or video can be shown; no proof of location"],
    ], "Common attendance methods and their weaknesses", widths=[0.24, 0.36, 0.40], font=10)


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "The base paper of this project, Dharmaraj et al. [1], describes a desktop application that recognises faces with a Haar cascade and an LBPH "
        "recogniser and writes attendance to subject-wise CSV files. It is a sensible baseline: it is simple, it runs without a GPU and it removes the "
        "roll call. It also shows, by what it leaves out, where the next problem lies. Its identification step answers the question *who is this face?* "
        "but nothing in it asks *is this a live person, and are they in the classroom?* A photograph held in front of the webcam is a face; a student "
        "outside the building who is shown a webcam feed is not detected as absent.",
        "Link-based attendance has the opposite weakness. It is quick and works from a phone, but it proves nothing about the person: whoever receives the link "
        "can use it. Faculty then fall back on roll calls, which brings back the time cost. A system that is fast, hard to forward and hard to "
        "spoof needs several independent checks that fail in different ways, and all of them must finish in a few seconds on the student's own phone.",
        "Recent work reviewed in the literature survey (Chapter 2) points the same way: attendance frameworks that combine face recognition with liveness "
        "checks are now reported [2], [3], [4], [5]. What is rarely reported is the combination of those checks with *location* and with a *per-session "
        "duplicate-identity check* inside a time-bound session that the faculty control. That combination is what Attendance Magic builds.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.p("Manual attendance consumes class time and is prone to errors and proxy marking. Link-based and QR-based digital attendance can be shared with "
        "absent students. Face recognition alone can be spoofed with photos or videos. Existing systems do not confirm that the student is physically "
        "present in the classroom, and one person can mark several identities if the faces recorded in a session are not compared.")
    d.p("**Problem statement.** Given a faculty-defined session (course, time window, geo-fence and roll-number patterns) and students who enrolled a "
        "reference face, accept a student's attendance only if (i) the session is live, the roll number is allowed and the device is eligible, (ii) the GPS "
        "position is inside the geo-fence, (iii) a random live facial challenge is performed, and (iv) the face matches the enrolled face and does not "
        "match any face already recorded in the session; and give faculty the records, a verification log and an Excel export.")


def sec_need(d):
    d.h2("Need for the System")
    d.bullets([
        "**Time.** A faculty member should not spend the first minutes of every class collecting attendance; a student should be able to complete a check-in in seconds.",
        "**Integrity.** Attendance records feed eligibility decisions; proxy attendance undermines them and is unfair to students who attend.",
        "**Evidence.** When a record is disputed, faculty need to see which checks passed, at what distance, with which challenge and similarity scores; Attendance Magic logs every attempt with its stage and reason.",
        "**Low cost.** Colleges rarely install new hardware for attendance. A system that runs in the browsers students already carry, on a faculty laptop, with free software, is deployable immediately.",
        "**Privacy by design.** Only a 512-number embedding of the enrolled face and of each recorded face is stored, and photographs are processed in memory and not saved by the application.",
    ])


def sec_objectives(d):
    d.h2("Objectives")
    d.p("The objectives were fixed in the project definition and are listed with the module that implements each:")
    d.table([
        ["No.", "Objective", "Implemented by"],
        ["1", "Enable faculty to create time-bound attendance sessions with configurable geo-fences", "services.create_session; session form; unique link and QR code"],
        ["2", "Authenticate students securely using JWT, device identification and roll-number restrictions", "core/auth.py, core/device.py, device bindings, roll patterns"],
        ["3", "Verify physical presence by checking the student's GPS location against the session boundary", "core/geofence.py (haversine + tolerance + accuracy gate)"],
        ["4", "Detect liveness through a random live facial challenge using MediaPipe", "core/liveness.py (Face Mesh metrics, 8 challenges)"],
        ["5", "Prevent duplicate identities by matching InsightFace embeddings within each session", "core/face_match.py (consistency, identity, duplicate)"],
        ["6", "Provide attendance summaries and Excel export for faculty", "core/export.py; session records, map, log, analytics"],
        ["7", "Verify the system with tests and measure its checks (added by the team)", "pytest, API smoke test, LFW and attack evaluations"],
    ], "Project objectives and their implementation", widths=[0.07, 0.53, 0.40], font=9.5)


def sec_scope(d):
    d.h2("Scope of the System")
    d.h3("In scope")
    d.bullets([
        "Faculty and student accounts with registration, sign-in and a reference-face enrolment; a React web application and the original Streamlit interface over one shared service layer.",
        "Time-bound sessions with a geo-fence (centre, radius), roll-number patterns, a share link and a QR code; closing a session and resetting a student's device bindings.",
        "The six-step student check-in: sign-in, eligibility, location, live challenge, face verification, result; three liveness tries; every attempt logged.",
        "Faculty views: live records with present and absent students, a map, the verification log, analytics, a dashboard and an Excel export with three sheets.",
        "Local, offline operation on a laptop CPU with SQLite (PostgreSQL is supported by configuration but was not tested).",
        "Evaluation of the verification thresholds and of the liveness check on the public LFW benchmark, plus timing and geo-fence experiments.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Training or fine-tuning any recognition model; the two models are used as published.",
        "Depth, infrared or texture-based anti-spoofing, deepfake or replay-video detection, and detection of fake GPS (mock-location) apps.",
        "Continuous video liveness: the challenge uses two still photographs.",
        "Institution-wide integration (LMS, ERP, student information systems), multi-college tenancy and role hierarchies beyond faculty and student.",
        "E-mail or SMS notification, parent alerts and dress-code checks.",
        "Hardware attendance devices.",
    ])
    d.h3("Assumptions")
    d.bullets([
        "Students carry a smartphone or laptop with a camera and a browser that allows camera and location access (phones need HTTPS for both).",
        "The faculty member sets the geo-fence around the actual classroom and the session window around the actual class.",
        "Each student enrols one clear, frontal reference photograph under the faculty's or the institution's supervision.",
        "The server runs on a machine the institution controls; the default JWT secret is replaced before real use.",
    ])


def sec_contrib(d):
    d.h2("Key Contributions")
    d.p("Measured values quoted below are taken from the project's own experiments (Chapter 8).")
    d.numbered([
        "**One time-bound check-in that combines six independent checks** (eligibility, device, geo-fence, live challenge, identity and duplicate-face) in a fixed, logged sequence, where the base paper's system performs identity only.",
        "**A random live facial challenge built on Face Mesh landmark metrics** (yaw, pitch, roll, mouth and eye aspect ratios) with eight actions, a neutral-frame check and a three-try lock. A single stolen photo passes none of seven challenges and 8.2% of 'close eyes'.",
        f"**A per-session duplicate-face check and device binding** that blocks one person marking several roll numbers; at threshold 0.45 a second capture of an already recorded face is detected {pct(FV['at_duplicate_threshold']['tar'])} of the time on LFW pairs.",
        f"**Measured thresholds.** On the LFW verification protocol the deployed identity threshold (0.40) accepts {pct(FV['at_identity_threshold']['tar'])} of same-person pairs and none of {FV['impostor_pairs']:,} different-person pairs (AUC {FV['auc']:.3f}).",
        "**An honest attack evaluation.** The project measures where its own liveness check fails (rotated photo, photo bank), so the limits are known rather than assumed.",
        "**A complete, reproducible application**: React 19 front end, FastAPI back end (27 endpoints), SQLite storage, Excel export, 23 pytest tests, a 41-check API smoke test and scripts that regenerate every screenshot, diagram and measurement.",
    ])
    d.h3("Novelty against the base paper")
    d.table([
        ["Aspect", "Base paper [1]", "Attendance Magic"],
        ["Recognition", "Haar cascade + LBPH trained on 25-30 images per student", "Pre-trained ArcFace embeddings from one reference photo"],
        ["Spoof resistance", "None described", "Random live challenge (8 actions), three tries, then lock"],
        ["Location", "None", "GPS geo-fence with radius, tolerance and accuracy gate"],
        ["Identity abuse", "None described", "Duplicate-face scan in the session; device binding; roll patterns"],
        ["Time control", "Instructor starts and stops scanning", "Time-bound sessions with unique link, QR code and close"],
        ["Records", "CSV files", "Database with attempt log; Excel with absentees and verification log"],
        ["Evidence", "~92-95% recognition in classroom tests (size not stated)", "Thresholds and attacks measured on LFW; tests and timings reported"],
    ], "Novelty of Attendance Magic compared with the base paper", widths=[0.18, 0.38, 0.44], font=9.5)


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.p("The limitations below are real and are repeated in the results and conclusion chapters; none is hidden by the numbers quoted elsewhere.")
    d.bullets([
        "**No live-camera or volunteer trial.** All photographs used in evaluation are still images from the public LFW benchmark (and a demo set of stand-in photographs). The genuine pass rate of each live challenge and the retake rate for real selfies were not measured.",
        f"**Liveness is the weakest link.** A single photo rotated by 15 degrees or more passes both tilt challenges (98-99%). An attacker holding several photos of the victim passes the full chain {pct(PB['by_challenge']['TURN_LEFT']['full_chain_rate'], 0)} of the time for a head-turn challenge and {pct(PB['by_challenge']['OPEN_MOUTH']['full_chain_rate'], 0)} for open mouth (LFW identities with 10 or more photos, so an upper bound for ordinary students).",
        f"**Single-face rule.** {pct(FF['rate'])} of LFW photos ({FF['rejected']:,} of {FF['images']:,}) are rejected by the rule that exactly one face is allowed (almost all as 'more than one face'). LFW crops are tight and low resolution, so selfie behaviour may differ.",
        "**Neutral frame strictness.** Only 32.9% of LFW press photos satisfy the neutral-frame check (|yaw| <= 0.10, mouth closed, one face); students are instructed to look straight, so acceptance should be higher, but was not measured.",
        "**GPS.** Real phone GPS error and indoor drift were not measured (a simulation is reported); fake-location apps are not detected; the default tolerance is 15 m.",
        "**Scale.** One uvicorn process and SQLite; no load test. Model inference runs on the CPU at about 0.18 s per face.",
        "**Security hardening.** The default JWT secret is a placeholder, passwords have no lockout, and camera and GPS on phones need HTTPS, which was not set up.",
        "**Project definition versus build.** The abstract mentioned Django REST Framework and PostgreSQL on Supabase; the implementation uses FastAPI and SQLite (PostgreSQL by configuration, untested).",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([
        ["Chapter", "Content"],
        ["1  Introduction", "Domain, motivation, problem, need, objectives, scope, contributions, limitations"],
        ["2  Literature Survey", "Base paper analysis, related work by theme, research gap"],
        ["3  Feasibility Study", "Technical, economic, operational and schedule feasibility"],
        ["4  System Requirements and Analysis", "Existing and proposed system, requirements, roles"],
        ["5  System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
        ["6  Methodology and Software Implementation", "Pipeline, data, algorithms, mathematics, application, API, security, installation"],
        ["7  System Testing", "Strategy and results of unit, integration, functional, security, performance tests"],
        ["8  Results and Output Screens", "Screens, measured results, comparison, failures, objectives versus outcomes"],
        ["9  Conclusion", "Summary, findings, applications, limitations"],
        ["10  Future Scope", "Improvements, features, deployment, research"],
        ["Appendices", "A: important code; B: installation and user guide; C: additional screens"],
    ], "Organisation of the report", widths=[0.34, 0.66], font=10)
