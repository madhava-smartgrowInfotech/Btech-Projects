"""Chapter 7 content: system testing."""
from __future__ import annotations

from doc_common import CHARTS, GF, LT

B = LT["B_stage_ms"]
C = LT["C_http_ms"]


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.p("Testing combined four layers. *Unit tests* (pytest) check the pure functions of `core/` with synthetic landmarks and embeddings so that they run without a "
        "camera. *Model-backed tests* run the real MediaPipe and InsightFace models on the sample photograph bundled with InsightFace. An *API smoke test* "
        "drives the whole FastAPI application in-process through its HTTP interface with the real models and a throw-away database. *Scripted attack and "
        "benchmark experiments* (`scripts/eval_*.py`) measure the behaviour of the checks on public images. The React interface was checked by a production "
        "build and by Playwright walkthroughs that produced the screenshots of Chapter 8.")
    d.table([
        ["Layer", "Tool", "Count / result"],
        ["Unit and model-backed tests", "pytest 9.1.1 (tests/test_core.py)", "23 tests passed in 17.8 s"],
        ["API end-to-end smoke test", "scripts/smoke_test.py (FastAPI TestClient, real models)", "41 of 41 checks passed in 9.9 s"],
        ["Headless pipeline demo", "scripts/demo_pipeline.py", "2 passes and 8 blocked attempts, each at the intended stage"],
        ["Attack and threshold experiments", "scripts/eval_*.py on LFW", "Chapter 8"],
        ["UI walkthrough", "Playwright with Chrome (scripts/capture_screenshots.py)", "34 screens captured with data"],
    ], "Test layers", widths=[0.28, 0.40, 0.32], font=9.5)


def sec_unit(d):
    d.h2("Unit Tests")
    d.table([
        ["Test", "Items", "What it checks"],
        ["test_password_hash_roundtrip", "1", "correct password verifies; wrong password and a malformed hash do not"],
        ["test_jwt_bound_to_device", "1", "claims round-trip; a token presented from another device and a tampered token raise TokenError"],
        ["test_haversine_known_distance", "1", "Charminar to Golconda Fort lies between 8 and 9 km (about 8.5 km)"],
        ["test_geofence_inside_outside_and_accuracy", "1", "a point about 7 m away is inside, one 556 m away is outside, an accuracy of 1,000 m is rejected"],
        ["test_metrics_from_synthetic_landmarks", "1", "yaw 0.2, pitch 0.6, roll 10 degrees, MAR 0.4 and EAR 0.25 are recovered from constructed 478-point landmarks"],
        ["test_verify_challenge", "11", "with the mirrored-camera setting, each challenge passes for the right movement and fails for the wrong direction or too little movement"],
        ["test_neutral_frame_must_be_frontal_and_single_face", "1", "a turned head and two faces are rejected, a frontal single face is accepted"],
        ["test_verify_faces_identity_and_duplicate_logic", "1", "identity pass, wrong person, duplicate of another roll (duplicate_of set), frames of different people, missing enrolment (required and optional), embedding bytes round-trip"],
        ["test_roll_patterns", "1", "wildcard and explicit roll patterns, case-insensitive; explicit lists are de-duplicated and wildcard lists return None"],
        ["test_session_lifecycle_and_eligibility", "1", "live, upcoming, expired and closed sessions; device binding and reset; roll not allowed; record, 'already marked', one device one roll per session; session embeddings; success attempt logged; Excel bytes"],
        ["test_models_on_sample_image", "1", "real models: two faces found in the sample photograph, one face for Face Mesh, a mirrored copy scores above 0.8 and two people below 0.3, a rotated copy passes TILT_LEFT and a still copy fails OPEN_MOUTH"],
        ["test_streamlit_faculty_flow, test_streamlit_student_flow_to_liveness_step", "2", "Streamlit AppTest end-to-end flows of the original interface"],
    ], "Unit and model-backed tests (23 items in 13 test functions)", widths=[0.40, 0.08, 0.52], font=9)


def sec_integration(d):
    d.h2("Integration Tests")
    d.p("The API smoke test registers a faculty member and three students with reference faces, creates a live session and runs the real six-step wizard through "
        "HTTP. Its 41 checks cover:")
    d.table([
        ["Group", "Checks"],
        ["Meta (4)", "health, 8 challenges in the configuration, models loaded, QR code returns a PNG"],
        ["Registration and sign-in (10)", "faculty registration, a student without a face is rejected, three students with faces, wrong-portal login 403, bad password 401, faculty login, /me with a device-bound token, token from another device 401"],
        ["Session (4)", "create a live session, public session by token, invalid token 404, faculty cannot check in"],
        ["Student A check-in (8)", "eligibility, outside the fence blocked, inside passes, neutral frame accepted, static photo fails the challenge (2 tries left), tilted frame passes liveness and face match, identity similarity above the threshold, second attempt 'already marked'"],
        ["Proxy attempts (2)", "same face under another roll blocked as duplicate; someone else's face blocked as identity mismatch"],
        ["Faculty screens (13)", "sessions list, session detail with blocked attempts, records, verification log, Excel export, dashboard totals, students list, reset devices, re-enrolment, student on faculty API 403, close session, closed session refuses check-in, stats"],
    ], "Groups of the API smoke test (41 checks, all passed)", widths=[0.30, 0.70], font=9.5)


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("Each functional requirement of Section 4.3 was exercised by at least one automated check or one of the scripted scenarios below. The scenarios "
        "were run with `demo_pipeline.py` (service layer), the smoke test (HTTP) and the UI walkthrough (browser).")
    d.table([
        ["Scenario", "Expected", "Observed"],
        ["Genuine student, inside the fence, right challenge", "Attendance recorded", "Recorded (distance 7.7 m, liveness 1.00)"],
        ["Same student again", "Blocked at eligibility", "'Attendance already marked for this session.'"],
        ["Student 556 m away", "Blocked at location", "'Outside geo-fence: you are 556 m away, limit is 75 m.'"],
        ["Static photo for OPEN_MOUTH", "Blocked at liveness", "'Mouth open ratio: measured 0.073, required 0.350'"],
        ["Another person's face under this roll number", "Blocked at identity", "'Face does not match ... similarity 0.02, required >= 0.40'"],
        ["Same face under a second roll number", "Blocked as duplicate", "'This face has already marked attendance in this session as 23K91A6706 (similarity 1.00)'"],
        ["Roll number not on the list", "Blocked at eligibility", "'Roll number 99X99X9999 is not allowed in this session.'"],
        ["Second device for the same student", "Blocked at eligibility", "'This device is not registered to your account.'"],
        ["Three failed challenges", "Wizard locked", "'Check-in locked after repeated failed liveness challenges'"],
        ["Closed session", "Refused", "'This session was closed by the faculty.'"],
    ], "Functional scenarios", widths=[0.34, 0.24, 0.42], font=9)
    d.p("In the demo pipeline the same photograph is used for enrolment and check-in, so the identity similarity is 1.00 there; with different photographs of one "
        "person (the UI walkthrough, using LFW images) the identity similarities were 0.59, 0.63 and 0.86.")


def sec_security_test(d):
    d.h2("Security Testing")
    d.table([
        ["Test", "Result"],
        ["Wrong password", "HTTP 401 'Incorrect username / roll number or password.'"],
        ["Student account on the faculty portal login", "HTTP 403 'This account is a student account. Please use the student portal.'"],
        ["Faculty token replayed from another device", "HTTP 401 'This login token was issued to a different device.'"],
        ["Tampered token", "TokenError 'Invalid authentication token.'"],
        ["Student token on a faculty endpoint", "HTTP 403"],
        ["Faculty token on the check-in endpoints", "HTTP 403 'Faculty accounts cannot mark attendance.'"],
        ["Check-in steps out of order", "HTTP 409 'Complete the previous step first.'"],
        ["Another faculty's session", "HTTP 404 (not revealed)"],
    ], "Security tests", widths=[0.46, 0.54], font=9.5)
    d.p("Not performed: penetration testing, brute-force testing of sign-in, HTTPS configuration review and a review of the dependency versions for known "
        "vulnerabilities.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.table([
        ["Case", "Behaviour"],
        ["No face, several faces or a turned head in the neutral photo", "Rejected with a specific message before the challenge is evaluated"],
        ["Second, small face in the background", "Tolerated if its width is at most half that of the main face"],
        ["Student has no enrolled face", "Blocked with 'Please enrol your face first' when enrolment is required"],
        ["GPS accuracy worse than 150 m", "Blocked with 'GPS accuracy too low'"],
        ["Session end before start, radius not positive", "Session creation rejected"],
        ["Duration outside 1-600 minutes, empty password under 6 characters", "Rejected by the form and the API model"],
        ["Session expires while the student is in the wizard", "Eligibility is re-checked before the record is written; the check-in is refused"],
        ["Page refresh in the middle of the wizard", "Wizard state is read back from the server, the student continues at the same step"],
        ["Explicit roll list", "Absentees are listed in the records view and in the Excel export"],
    ], "Edge cases", widths=[0.42, 0.58], font=9.5)


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Measurements were made on an Intel Core i5-12500 (6 cores, 12 threads, 15.7 GB RAM) running Windows 11 with Python 3.11.9, CPU only. Other desktop "
        "applications were running; a run made while the CPU was at about 100% from other processes gave an embedding median of 277 ms instead of 176 ms, "
        "so the figures below should be read as typical rather than best case. Network time is excluded because the HTTP test uses an in-process client.")
    d.table([
        ["Stage (median / 95th percentile, ms)", "Value"],
        ["Model load at start: MediaPipe / InsightFace", f"{LT['A_cold_start_ms']['mediapipe_face_mesh']:.0f} / {LT['A_cold_start_ms']['insightface_buffalo_l']:.0f} (single load)"],
        ["JPEG decode and resize (1280 x 886)", f"{B['decode_1280px_jpeg']['p50']:.1f} / {B['decode_1280px_jpeg']['p95']:.1f}"],
        ["MediaPipe landmarks, one photo", f"{B['mediapipe_landmarks']['p50']:.1f} / {B['mediapipe_landmarks']['p95']:.1f}"],
        ["Challenge decision", f"{B['verify_challenge_maths']['p50']:.3f} / {B['verify_challenge_maths']['p95']:.3f}"],
        ["InsightFace embedding, one photo", f"{B['insightface_embed']['p50']:.0f} / {B['insightface_embed']['p95']:.0f}"],
        ["Face decision with 30 session faces", f"{B['verify_faces']['p50']:.2f} / {B['verify_faces']['p95']:.2f}"],
        ["AI work for one check-in (2 landmark + 2 embedding passes)", f"{B['pipeline_ai_total_two_frames']['p50']:.0f} / {B['pipeline_ai_total_two_frames']['p95']:.0f}"],
        ["HTTP: login (PBKDF2)", f"{C['login']['p50']:.0f} / {C['login']['p95']:.0f}"],
        ["HTTP: eligibility / location", f"{C['start_eligibility']['p50']:.0f} / {C['start_eligibility']['p95']:.0f} and {C['location']['p50']:.0f} / {C['location']['p95']:.0f}"],
        ["HTTP: liveness (two uploads)", f"{C['liveness_two_photos']['p50']:.0f} / {C['liveness_two_photos']['p95']:.0f}"],
        ["HTTP: face match and record", f"{C['face_match_and_record']['p50']:.0f} / {C['face_match_and_record']['p95']:.0f}"],
        ["HTTP: complete check-in after login", f"{C['checkin_total_after_login']['p50']:.0f} / {C['checkin_total_after_login']['p95']:.0f} (40 runs)"],
    ], "Performance measurements", widths=[0.62, 0.38], font=9.5)
    d.figure(CHARTS / "latency.png", "Latency of the pipeline stages and of the HTTP steps of one check-in (median and 95th percentile)", width=6.0)
    D = LT["D_duplicate_scan_ms"]
    d.p(f"The duplicate scan is a linear loop over the embeddings already recorded in the session. It took {D['10']['p50']:.2f} ms for 10 faces, {D['100']['p50']:.2f} ms for 100, "
        f"{D['1000']['p50']:.1f} ms for 1,000 and {D['5000']['p50']:.0f} ms for 5,000, so a lecture-sized session adds no noticeable time.")
    d.figure(CHARTS / "duplicate_scan.png", "Time of the duplicate-face scan against the number of faces recorded in the session", width=4.4)
    d.p("**Not measured:** concurrent users (a single uvicorn process serialises model inference behind a lock), memory use, other hardware, mobile network latency.")


def sec_uat(d):
    d.h2("User Acceptance")
    d.p("No user-acceptance test with real faculty or students was carried out. The interface was verified by the team through the walkthrough that produced the "
        "screenshots. A trial with volunteers is the first item of future work: it should record the genuine pass rate of each challenge, the number of retakes "
        "per check-in, the time to complete a check-in on a phone and a short usability questionnaire.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "All face photographs are still images from LFW or stand-ins for student photographs; no live camera, phone browser or human volunteer was involved.",
        "The challenge photo in the automated flows is either a real second photograph that satisfies the issued challenge or a rotated copy for the tilt challenges; this exercises the logic but is not the same as a person performing the action.",
        "GPS positions are supplied by the test (or by the browser's emulated geolocation); real phone GPS behaviour was not measured.",
        "No load, stress, soak or penetration testing was done; the tests run in one process on one machine.",
        "Coverage was not measured with a coverage tool; the 23 tests concentrate on `core/`, and the React interface has no automated unit tests.",
    ])
