"""Chapter 5 content and the diagram catalogue (shared with the block-diagram document)."""
from __future__ import annotations

from doc_common import DIAG, SHOTS

# key -> (file, caption, landscape, explanation paragraphs)
DIAGRAMS = {
    "architecture": ("01_system_architecture.png", "System architecture of Attendance Magic", False, [
        "The architecture has four layers. Users work in a browser: the faculty member on a laptop and the student on a phone. The original Streamlit "
        "interface (port 8501) is kept and uses the same core services. The React front end (port 5102) provides twelve routes, the camera and "
        "location capture (getUserMedia or file upload, and the Geolocation API), the Leaflet map and the Recharts charts; its data layer sends the "
        "device identifier in the X-Device-Id header and the JWT as a bearer token. The Vite development server forwards /api to the back end, so phones need "
        "only one address.",
        "The FastAPI back end (port 8102) is deliberately thin: its 27 endpoints translate HTTP to calls into the `core/` package and keep the per-student check-in "
        "wizard state on the server. `core/` holds all rules: authentication, device fingerprint, geo-fence, liveness, face matching, eligibility "
        "and the pipeline, and Excel export. Storage is a local SQLite database with five tables, and the two pre-trained models, MediaPipe Face Mesh and "
        "InsightFace buffalo_l, run on the CPU in the same process."]),
    "workflow": ("02_high_level_workflow.png", "High-level workflow from session creation to export", False, [
        "The workflow has ten steps. The faculty member creates a session (1) and shares its link and QR code (2). The student opens the link and signs in (3); "
        "the server checks eligibility (4) and the geo-fence (5), issues a random live challenge (6) and verifies the face (7). A successful check-in writes the "
        "attendance record (8); the faculty member monitors records, map, log and analytics (9) and exports to Excel (10).",
        "A failed stage stops the check-in with a plain reason and the attempt is logged. Three failed liveness tries lock the wizard until the student starts over."]),
    "dfd0": ("03_dfd_level0.png", "Data-flow diagram, level 0 (context diagram)", False, [
        "The context diagram shows Attendance Magic as one process with two external entities. The faculty member sends session details, roll patterns and "
        "commands (close, reset devices) and receives the session link and QR code, records, map, log and the Excel export. The student sends credentials, a GPS "
        "fix and two photos and receives the result of each step, with reasons, scores and the attendance confirmation."]),
    "dfd1": ("04_dfd_level1.png", "Data-flow diagram, level 1", False, [
        "Level 1 opens the system into eight processes and four data stores. Process 1 authenticates users against D1 (users). Process 2 manages sessions in D2 "
        "(attendance_sessions). Processes 3 to 6 form the student's verification chain: eligibility (reads D1 device bindings and D2 sessions), location, liveness "
        "and face verification. Process 7 writes the attendance record to D3 (attendance_records). Process 8 produces records, map, analytics and the Excel "
        "export from D2 and D3. Processes 3 to 7 append a row to D4 (verification_attempts) at every stage, shown by the dotted lines."]),
    "dfd2": ("05_dfd_level2.png", "Data-flow diagram, level 2: expansion of process 6 (verify face)", False, [
        "Level 2 opens the face-verification process into five steps. The two frames arriving from the liveness step are decoded and one face is "
        "detected in each (6.1). Frame consistency (6.2) requires the two photos to show the same person (cosine similarity at least 0.45). Identity (6.3) compares the first "
        "frame with the enrolled embedding in D1 (at least 0.40). The duplicate scan (6.4) compares it with every embedding already recorded in the session in D3 "
        "(maximum below 0.45). The decision (6.5) writes the reason and scores to D4 and either passes control to process 7 or returns the reason to the student."]),
    "usecase": ("08_use_case_diagram.png", "Use-case diagram", False, [
        "The faculty member can create a time-bound session, set the geo-fence and roll patterns, share the link and QR code, view records, map, log and analytics, "
        "export to Excel, close a session or reset devices, and enrol a student's reference face. The student can register with a reference face, sign in with a "
        "device-bound token, pass the eligibility check, verify location, complete the random live challenge, pass face verification and view the result. Every "
        "student step is logged in verification_attempts."]),
    "sequence": ("09_sequence_diagram.png", "Sequence diagram of a student check-in", False, [
        "The sequence follows the main flow. The student opens the session link and signs in; the React app posts the credentials with the device identifier to "
        "`/api/auth/login`, and `core.services.authenticate` verifies the PBKDF2 hash and issues a JWT carrying the device hash. `POST /start` runs "
        "`check_eligibility` (reading the session, the existing record and the device bindings and binding the device on first use). `POST /location` runs "
        "`check_geofence`. `POST /liveness` receives the two photos, runs Face Mesh on each and `verify_challenge`. `POST /face` embeds both photos, "
        "runs `verify_faces` against the enrolled and the session embeddings, re-checks eligibility and inserts the record and the success attempt. The result "
        "returns to the student as the 'Marked. Present.' screen."]),
    "er": ("06_er_diagram.png", "Entity-relationship diagram of the Attendance Magic database (5 tables)", True, [
        "The database has five tables. `users` holds faculty and students (the student's reference embedding is a 512-float binary column). "
        "`attendance_sessions` belongs to a faculty user through `faculty_id` and holds the window, the geo-fence and the allowed roll patterns. "
        "`attendance_records` links a session and a student and stores the evidence of the check-in (distance, accuracy, challenge, liveness score, identity "
        "and duplicate similarities, device hash and the face embedding); a unique constraint on (session_id, student_id) makes a second record impossible. "
        "`device_bindings` stores the devices a student has used, unique per user and device. `verification_attempts` is the audit log, one row per stage attempt."]),
    "uml": ("07_uml_class_diagram.png", "UML class diagram: persistent entities and decision classes", True, [
        "The upper part of the class diagram shows the five persistent entities and their associations; `AttendanceSession` has the derived methods "
        "`status` (upcoming, live, expired or closed) and `is_open`. The lower part shows the modules of `core/` and the plain result classes they return: "
        "`MatchResult` from face matching, `FaceMetrics` and `LivenessResult` from liveness, `GeoResult` from the geo-fence and `Eligibility` and "
        "`PipelineResult` from the services. Each decision returns a result object with a boolean outcome and a human-readable reason, which is what the "
        "API passes to the screen and writes to the log."]),
    "flowchart": ("10_algorithm_flowchart.png", "Flowchart of the core check-in algorithm", False, [
        "The flowchart is the control flow of `run_pipeline` and of the equivalent API wizard. After sign-in, eligibility is checked; then the geo-fence "
        "(accuracy at most 150 m and distance at most radius plus 15 m); then the liveness challenge on two photos (retry up to three times, with a new random "
        "challenge each time); then the embeddings of both photos; then frame consistency and identity; then the duplicate scan. Any 'no' leads to a block "
        "with a stored reason; only a full 'yes' chain records attendance."]),
}
ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]


def diagram(d, key, extra=None):
    """Write the explanation, then the figure (landscape page for the wide ones)."""
    fname, caption, landscape, paras = DIAGRAMS[key]
    for t in paras:
        d.p(t)
    if extra:
        for t in extra:
            d.p(t)
    d.figure(DIAG / fname, caption, landscape=landscape)


# ------------------------------------------------------------------ Chapter 5
def sec_arch(d):
    d.h2("System Architecture")
    d.p("Attendance Magic has a layered architecture in which the rules live in one place. The principle is that the HTTP layer and both user interfaces "
        "contain no verification logic: they call the `core/` package, which can also be driven from scripts and unit tests.")
    diagram(d, "architecture")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams (Levels 0, 1 and 2)")
    d.p("The data-flow diagrams use the Yourdon notation: ellipses are processes, open rectangles are data stores and rounded boxes are external entities.")
    for k in ("dfd0", "dfd1", "dfd2"):
        diagram(d, k)


def sec_uml(d):
    d.h2("UML Diagrams")
    d.h3("Use cases")
    diagram(d, "usecase")
    d.h3("Sequence of the main flow")
    diagram(d, "sequence")
    d.h3("Class diagram")
    diagram(d, "uml")
    d.h3("Flowchart of the core algorithm")
    diagram(d, "flowchart")


def sec_database(d):
    d.h2("Database Design")
    d.p("The schema is defined with SQLAlchemy 2 in `core/models.py` and created on first start (`init_db`). Timestamps are stored in UTC and displayed in "
        "the configured time zone (Asia/Kolkata by default). The tables and their columns are:")
    d.table([
        ["Table", "Columns", "Keys and constraints"],
        ["users", "id, role ('faculty' or 'student'), username, full_name, roll_number, password_hash, face_embedding (512 x float32, 2,048 bytes), created_at", "PK id; username unique; roll_number unique"],
        ["attendance_sessions", "id, token, faculty_id, course_code, course_name, section, starts_at, ends_at, latitude, longitude, radius_m, allowed_rolls, is_closed, created_at", "PK id; token unique and indexed; FK faculty_id -> users"],
        ["attendance_records", "id, session_id, student_id, roll_number, student_name, marked_at, latitude, longitude, gps_accuracy_m, distance_m, device_hash, challenge, liveness_score, identity_similarity, max_duplicate_similarity, face_embedding", "PK id; FKs to sessions and users; UNIQUE(session_id, student_id)"],
        ["device_bindings", "id, user_id, device_hash, device_label, first_seen, last_seen", "PK id; FK user_id; UNIQUE(user_id, device_hash)"],
        ["verification_attempts", "id, session_id, roll_number, stage (eligibility, location, liveness, face, success), passed, reason, device_hash, created_at", "PK id; FK session_id"],
    ], "Database tables", widths=[0.19, 0.53, 0.28], font=9)
    diagram(d, "er")
    d.p("**Design notes.** The embedding is stored as raw float32 bytes (`ndarray.tobytes`) and read back with `np.frombuffer`, which is compact and exact. "
        "The record repeats the student's roll number and name so that an export stays correct if an account changes. The attempts table is append-only and "
        "carries no foreign key to users because attempts may involve roll numbers that do not exist as accounts.")


def sec_modules(d):
    d.h2("Module Design")
    d.table([
        ["Module", "Responsibility", "Key functions"],
        ["config.py", "All settings with environment overrides", "radius, tolerance, accuracy limit, challenge thresholds, face thresholds, JWT, device limit"],
        ["core/auth.py", "Passwords and tokens", "hash_password, verify_password, issue_token, verify_token (device claim)"],
        ["core/device.py", "Device identification", "fingerprint (SHA-256 of user-agent, language, client hints and X-Device-Id), label"],
        ["core/geofence.py", "Presence by location", "haversine_m, check_geofence"],
        ["core/liveness.py", "Random challenge", "random_challenge, metrics_from_landmarks, analyze, check_neutral, verify_challenge, decode_image"],
        ["core/face_match.py", "Face identity", "embed, cosine, verify_faces (consistency, identity, duplicate)"],
        ["core/services.py", "Business logic", "register_user, authenticate, create_session, check_eligibility, record_attendance, run_pipeline, roll_allowed"],
        ["core/export.py", "Excel report", "records_dataframe, to_excel_bytes (Summary, Attendance, Verification Log)"],
        ["backend/api.py", "HTTP layer", "27 endpoints, auth dependencies, check-in wizard state, QR generation"],
        ["frontend/src", "React application", "12 pages, UI components, camera and location components, API client"],
    ], "Modules of Attendance Magic", widths=[0.20, 0.28, 0.52], font=9)


def sec_ui(d):
    d.h2("User Interface Design")
    d.p("The React interface follows a 'Neo Brutal Grid' design: thick black borders, hard offset shadows, a lime, coral and sky palette on an off-white grid, "
        "monospace labels and a light and dark theme. The design goals were legibility on a phone in bright light, large touch targets, and the reason for "
        "every outcome shown in words and colour (not colour alone).")
    d.bullets([
        "**Public pages:** landing page with live statistics, how-it-works page, sign-in for each role, registration with reference-face upload, and a page to paste a session link.",
        "**Student check-in:** a six-step stepper (Sign in, Eligibility, Location, Live challenge, Face match, Done) with the session header on top; each step shows one task and its error, if any.",
        "**Faculty area:** a sidebar (Dashboard, Sessions, New session, Students), KPI tiles, tabs for records, map, log and analytics on a session, and a drawer for managing one student.",
        "**Accessibility:** labelled controls, reduced-motion support and text labels next to every status colour.",
    ])
    d.figure(SHOTS / "05_login_student.png", "Student sign-in screen", width=4.8)
    d.figure(SHOTS / "09_create_session.png", "New-session form with geo-fence preview", width=4.4, max_h=5.6)
