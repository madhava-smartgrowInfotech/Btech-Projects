"""Chapter 6 content: methodology and software implementation."""
from __future__ import annotations

from doc_common import CH_LABEL, CH_THRESH, CHALLENGES, FF, FV, LV, ROOT, pct

APP = ROOT


def excerpt(rel, start, end):
    lines = (APP / rel).read_text(encoding="utf-8").splitlines()[start - 1:end]
    return "\n".join(lines)


def sec_method_overview(d):
    d.h2("Overall Methodology")
    d.p("The methodology is a verification chain rather than a learning pipeline: no model is trained. Two pre-trained models supply measurements (facial "
        "landmarks and face embeddings) and deterministic rules turn those measurements into decisions. The chain runs in the order of the check-in wizard, "
        "and each stage can end the check-in with a stored reason.")
    d.table([
        ["Step", "Input", "Computation", "Output / decision"],
        ["1 Sign-in", "username or roll number, password, X-Device-Id", "PBKDF2-HMAC-SHA256 verify; JWT with device hash", "token or 401"],
        ["2 Eligibility", "session, user, device hash", "window, roll pattern, existing record, device record, device binding", "eligible or reason"],
        ["3 Location", "latitude, longitude, accuracy", "haversine distance; limit = radius + 15 m; accuracy <= 150 m", "inside or reason"],
        ["4 Challenge", "neutral photo, challenge photo, challenge code", "Face Mesh landmarks to yaw, pitch, roll, MAR, EAR; compare with thresholds", "pass (score) or reason; retry up to 3"],
        ["5 Face", "the two photos", "ArcFace 512-d embeddings; cosines: consistency, identity, duplicate", "pass or reason"],
        ["6 Record", "all of the above", "insert the attendance row and success attempt", "record id; result screen"],
    ], "Stages of the verification chain", widths=[0.13, 0.24, 0.40, 0.23], font=9)
    d.p("The same chain is available in two forms: `services.run_pipeline` executes it in one call (used by the demo script and tests) and the FastAPI wizard "
        "executes it step by step, keeping the intermediate state on the server. Both call the same functions of `core/`.")


def sec_dataset(d):
    d.h2("Dataset")
    d.p("There is no training dataset because no model is trained. Data enters the project in three ways.")
    d.table([
        ["Data", "Source", "Size", "Use"],
        ["LFW verification pairs", "Labeled Faces in the Wild [9], pairs.txt protocol (research benchmark, downloaded from figshare, not redistributed)", "13,233 images, 5,749 people; 6,000 pairs (3,000 same, 3,000 different) in 10 folds of 600; 7,701 unique images used", "Evaluate identity, duplicate and consistency thresholds"],
        ["LFW stills", "Same dataset", "1,000 random photos (seed 7); 157 identities with 10 or more photos", "Neutral-frame, static replay, rotation and photo-bank attack experiments"],
        ["Demo data", "Created by scripts/seed_demo.py and capture_screenshots.py", "1 faculty and 6 student accounts, 2 sessions, 30 attempts logged in the live session", "Screens, smoke test, walkthrough"],
    ], "Data used in the project", widths=[0.17, 0.32, 0.30, 0.21], font=9)
    d.p("**Split.** The LFW protocol is used exactly as published: the identity threshold is evaluated on all scored pairs, and the 10-fold accuracy "
        f"({pct(FV['ten_fold_accuracy_mean'], 2)} mean, standard deviation {pct(FV['ten_fold_accuracy_std'], 2)}) picks the best threshold on nine folds and tests on the tenth. "
        "The deployed thresholds (0.40 and 0.45) were set before the evaluation and were not tuned on it.")
    d.p("**Licence and privacy.** LFW images are news photographs of public figures, distributed for research on face recognition. They are used here only "
        "to evaluate the verification chain and, with their file names anonymised, as stand-ins for student photographs in the demo screenshots; they are not redistributed with the project. "
        "No student photographs were collected.")


def sec_preprocessing(d):
    d.h2("Preprocessing")
    d.bullets([
        "**Image decoding.** `decode_image` decodes the uploaded bytes with OpenCV and shrinks any image whose longer side exceeds 1,280 px (area interpolation) to keep inference fast on phone photos.",
        "**Colour order.** Images are kept in BGR for InsightFace and converted to RGB for MediaPipe.",
        "**Single-face rule.** Face Mesh must find exactly one face in each photo; InsightFace must find one face, or a second face whose width is at most half that of the largest face.",
        "**Neutral frame.** The first photo must be frontal (|yaw| <= 0.10) and the mouth closed (MAR <= 0.25), so that later changes are measured from a known pose.",
        "**Mirroring.** Selfie cameras mirror the image; with `AM_CAMERA_MIRRORED = true` the left and right challenges flip their sign so that 'turn left' refers to the student's left.",
        "**Embedding normalisation.** Embeddings are L2-normalised before storage and before every comparison, so a dot product is a cosine similarity.",
        "**Roll patterns.** Allowed roll numbers are upper-cased and matched with `fnmatch`; an explicit list (no wildcards) is also used to list absentees.",
    ])
    d.p(f"On the LFW sample the neutral-frame check accepted {LV['A_neutral']['accepted']} of {LV['A_neutral']['sample']:,} photos "
        f"({pct(LV['A_neutral']['rate'])}); it rejected {LV['A_neutral']['rejected_by']['not_frontal']} as not frontal, {LV['A_neutral']['rejected_by']['multiple_faces']} for several faces, "
        f"{LV['A_neutral']['rejected_by']['mouth_open']} for an open mouth and {LV['A_neutral']['rejected_by']['no_face']} for no face. The single-face rule of the recogniser "
        f"rejected {FF['rejected']:,} of {FF['images']:,} LFW images ({pct(FF['rate'])}), {FF['reasons']['multiple_faces']:,} of them as 'more than one face'.")


def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    d.table([
        ["Decision", "Chosen", "Alternatives", "Justification"],
        ["Liveness approach", "Active random challenge on landmark metrics", "Passive texture / learned anti-spoofing [5], [12]; blink detection [11]", "No extra model, works on any camera, thresholds are transparent, and the unpredictable action defeats a prepared photo; its weaknesses are measured (Chapter 8)"],
        ["Landmarks", "MediaPipe Face Mesh [8] (legacy solutions API, 468 points)", "dlib 68 points, 3-D head-pose solvers", "Fast on CPU, bundled model, includes lips and eyelids for MAR and EAR"],
        ["Recogniser", "InsightFace buffalo_l (SCRFD + ArcFace R50) [6], [7]", "LBPH [1], FaceNet [13]", "No per-student training; margin-trained embeddings; one reference photo; high verification accuracy (Section 8.2)"],
        ["Similarity", "Cosine on L2-normalised 512-d embeddings", "Euclidean distance, classifier head", "Standard for ArcFace; a dot product; thresholds are interpretable"],
        ["Distance", "Haversine on a sphere [14]", "Vincenty [15]", "0.47% error (0.35 m at the 75 m limit) is far below GPS noise; far simpler"],
        ["Tokens", "JWT HS256 with a device claim [16]", "Server sessions", "Stateless API; a stolen token fails on another device"],
        ["Password hash", "PBKDF2-HMAC-SHA256, 200,000 iterations [17]", "bcrypt, Argon2", "Available in the Python standard library; no extra dependency"],
    ], "Algorithm choices", widths=[0.15, 0.24, 0.23, 0.38], font=8.5)


def sec_math(d):
    d.h2("Mathematical Formulation")
    d.h3("Geo-fence")
    d.p("For a student at latitude phi2 and longitude lambda2 and a centre at phi1 and lambda1 (radians), the great-circle distance on a sphere of radius R = 6,371,000 m is")
    d.code("a = sin^2((phi2 - phi1)/2) + cos(phi1) cos(phi2) sin^2((lambda2 - lambda1)/2)\nd = 2 R asin( sqrt(a) )")
    d.p("The check-in is accepted if the reported accuracy is at most 150 m and d <= r + t, where r is the session radius (60 m by default) and t = 15 m is the tolerance. "
        "Against the ellipsoidal (Vincenty) distance at latitude 17.385 degrees the spherical formula is off by a constant 0.469%, which is 0.35 m at 75 m and 4.7 m at 1 km.")
    d.h3("Landmark metrics")
    d.p("Let p_i be the 2-D landmark with Face Mesh index i, and x_L, x_R the x-coordinates of the cheek landmarks 234 and 454. With nose tip 1, chin 152, eye corners "
        "(33, 133) and (263, 362), eyelids (159, 145) and (386, 374) and lip landmarks 13, 14, 61, 291:")
    d.code("yaw   = (x_nose - min(x_L, x_R)) / |x_R - x_L| - 0.5\n"
           "pitch = (y_nose - y_eyes_mid) / (y_chin - y_eyes_mid)\n"
           "roll  = atan2(y_Reye - y_Leye, x_Reye - x_Leye)        (degrees)\n"
           "MAR   = |p13 - p14| / |p61 - p291|\n"
           "EAR   = mean over both eyes of |top - bottom| / |outer - inner|")
    d.p("A frontal, mouth-closed face has yaw near 0 (measured standard deviation 0.053 on accepted LFW frames), pitch near 0.35, MAR near 0.09 and EAR near 0.28.")
    d.h3("Challenge decision")
    d.p("With the neutral frame n and the challenge frame c, and s = -1 for mirrored cameras and +1 otherwise, the measured quantity m is:")
    d.table([
        ["Challenge", "Measured quantity m", "Pass if", "Score"],
        ["Turn left / right", "s (yaw_c - yaw_n) / -s (yaw_c - yaw_n)", "m >= 0.12", "min(1, m/0.12)"],
        ["Look up / down", "-(pitch_c - pitch_n) / (pitch_c - pitch_n)", "m >= 0.08", "min(1, m/0.08)"],
        ["Tilt left / right", "s (roll_c - roll_n) / -s (roll_c - roll_n)", "m >= 12 degrees", "min(1, m/12)"],
        ["Open mouth", "MAR_c", "m >= 0.35", "min(1, m/0.35)"],
        ["Close eyes", "2 x 0.18 - EAR_c", "EAR_c <= 0.18", "min(1, m/0.18)"],
    ], "Challenge decision rules", widths=[0.20, 0.38, 0.20, 0.22], font=9.5)
    d.h3("Face decision")
    d.p("With L2-normalised embeddings f1 (neutral photo), f2 (challenge photo), e (enrolled) and g_j (faces already recorded in the session), and cos(a, b) = a . b:")
    d.code("consistent = cos(f1, f2) >= 0.45\nidentity   = cos(f1, e)  >= 0.40\nunique     = max_j cos(f1, g_j) < 0.45\npass       = consistent and identity and unique")
    d.p("The three thresholds are environment settings (`AM_FRAME_CONSISTENCY_THRESHOLD`, `AM_IDENTITY_THRESHOLD`, `AM_DUPLICATE_THRESHOLD`). Section 8.2 shows how "
        "they sit between the same-person and different-person similarity distributions.")


def sec_model_training(d):
    d.h2("Models, Configuration and Training")
    d.p("**No model is trained in this project.** There is therefore no training set, no loss curve, no epochs and no validation split; the documents of the "
        "earlier reviews that listed 'training configuration' refer to the configuration of the verification chain given below. Both models are used as published:")
    d.table([
        ["Model", "Role", "Details"],
        ["MediaPipe Face Mesh 0.10.21 (legacy solutions API)", "Landmarks for liveness", "static_image_mode, up to 3 faces, refine_landmarks on, min detection confidence 0.5; 468 landmarks; bundled model; CPU"],
        ["InsightFace buffalo_l (insightface 2.0, ONNX Runtime 1.31, CPUExecutionProvider)", "Detection and recognition", "detection (SCRFD) and recognition (ArcFace ResNet-50) modules only; det_size 640 x 640; 512-d embeddings; about 280 MB download on first use"],
    ], "Pre-trained models", widths=[0.30, 0.20, 0.50], font=9.5)
    d.table([
        ["Setting", "Default", "Environment variable"],
        ["Geo-fence radius / tolerance / accuracy limit", "60 m / 15 m / 150 m", "AM_DEFAULT_RADIUS_M, AM_GEOFENCE_TOLERANCE_M, AM_MAX_GPS_ACCURACY_M"],
        ["Challenge thresholds", "yaw 0.12, pitch 0.08, roll 12 deg, MAR 0.35, EAR 0.18", "AM_LIVENESS_YAW_DELTA, _PITCH_DELTA, _ROLL_DEG, _MAR, _EAR"],
        ["Neutral frame", "|yaw| <= 0.10, MAR <= 0.25", "(constants in config.py)"],
        ["Face thresholds", "consistency 0.45, identity 0.40, duplicate 0.45", "AM_FRAME_CONSISTENCY_THRESHOLD, AM_IDENTITY_THRESHOLD, AM_DUPLICATE_THRESHOLD"],
        ["Enrolment required", "true", "AM_REQUIRE_ENROLLMENT"],
        ["Devices per student", "1", "AM_MAX_DEVICES_PER_STUDENT"],
        ["JWT validity / password iterations", "120 min / 200,000", "AM_JWT_EXPIRY_MINUTES / (constant)"],
        ["Liveness tries", "3", "(constant in ui/student.py)"],
        ["Camera mirrored", "true", "AM_CAMERA_MIRRORED"],
        ["Time zone / database", "Asia/Kolkata / SQLite file", "AM_TIMEZONE / DATABASE_URL"],
    ], "Configuration of the verification chain", widths=[0.34, 0.34, 0.32], font=9)


def sec_app_arch(d):
    d.h2("Application Architecture")
    d.p("The back end is a FastAPI application (`backend/api.py`). At start-up it creates the tables and loads the two models in a background thread, so the "
        "first request after start-up does not pay the model-loading time (0.8 s and 1.5 s measured). Every protected endpoint declares a dependency that "
        "verifies the bearer token against the device hash recomputed from the request (`current_claims`), and a second dependency that enforces the role "
        "(`faculty_claims` or `student_claims`).")
    d.p("**Check-in wizard state.** A student's progress is kept in a server-side dictionary keyed by (user, session, device): the step, the current random "
        "challenge, the number of failed liveness tries, the GPS fix, the distance, the liveness score and, between the liveness and face steps, the two "
        "photographs as bytes. The photographs are dropped from the state after a successful record, the whole state on `reset` and on sign-out, and the photographs are never written to disk. The React page reads the state "
        "from `/state` when it loads, so a refresh returns the student to the same step.")
    d.p("**Front end.** React 19 with React Router 7; each page is a lazy-loaded chunk (the production build splits 20 chunks, the largest 581 kB or 194 kB "
        "gzipped). A small fetch wrapper adds the device id and the token and turns error responses into readable messages. The camera component calls "
        "`getUserMedia`, mirrors the captured frame to match `camera_mirrored`, and every photo slot has an upload tab for testing without a camera. Maps use Leaflet "
        "with OpenStreetMap tiles.")


def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.h3("Geo-fence check")
    d.p("`check_geofence` rejects a fix whose reported accuracy is worse than the limit, then compares the haversine distance with the radius plus the tolerance. "
        "The returned object carries the distance, the allowed distance and a sentence for the student.")
    d.code(excerpt("core/geofence.py", 29, 60), "core/geofence.py: check_geofence")
    d.h3("Liveness: landmark metrics and challenge decision")
    d.code(excerpt("core/liveness.py", 79, 105), "core/liveness.py: metrics_from_landmarks")
    d.code(excerpt("core/liveness.py", 208, 254), "core/liveness.py: verify_challenge")
    d.h3("Face decision")
    d.code(excerpt("core/face_match.py", 99, 158), "core/face_match.py: verify_faces")
    d.h3("Eligibility and the pipeline")
    d.code(excerpt("core/services.py", 198, 236), "core/services.py: check_eligibility")
    d.code(excerpt("core/services.py", 276, 314), "core/services.py: run_pipeline")


def sec_api(d):
    d.h2("API Design")
    d.p("All endpoints are under `/api`, accept and return JSON (photos as multipart form data) and are documented automatically at `/docs` "
        "(Figure in Appendix C). Errors use HTTP status codes with a `detail` message that the UI shows to the user: 400 invalid input, 401 not signed in or token "
        "problem, 403 wrong role, 404 not found, 409 wizard step out of order.")
    d.table([
        ["Method and path", "Role", "Purpose"],
        ["GET /api/health, /api/config, /api/models, /api/stats", "public", "status, public settings and thresholds, loaded models, landing-page totals"],
        ["GET /api/qr?text=", "public", "QR code PNG for a link"],
        ["POST /api/auth/register", "public", "create a faculty or student account (student: reference face required, checked for a frontal single face)"],
        ["POST /api/auth/login, /logout; GET /api/auth/me", "any", "sign in (JWT bound to the device), sign out, current user and device"],
        ["GET, POST /api/sessions; GET /api/sessions/{id}", "faculty", "list own sessions, create a session, detail with records, rows and attempts"],
        ["POST /api/sessions/{id}/close; GET .../export", "faculty", "close a session; download the Excel report"],
        ["GET /api/dashboard", "faculty", "aggregates: totals, per-session rows, checks by stage, latest attempts"],
        ["GET /api/students; POST /api/students/{id}/reset-devices, /enroll", "faculty", "list students, remove device bindings, replace a reference face"],
        ["GET /api/public/sessions/{token}", "public", "session header for the check-in page"],
        ["GET /api/checkin/{token}/state; POST .../start, /location, /neutral, /liveness, /face, /retake, /reset", "student", "the check-in wizard (eligibility, location, neutral-frame check, challenge, face verification, retake, start over)"],
    ], "REST API of Attendance Magic (27 endpoints)", widths=[0.46, 0.12, 0.42], font=9)


def sec_security(d):
    d.h2("Security and Error Handling")
    d.table([
        ["Threat", "Control", "Evidence"],
        ["Password disclosure", "PBKDF2-HMAC-SHA256, 200,000 iterations, 16-byte random salt; constant-time comparison", "test_password_hash_roundtrip"],
        ["Token theft", "JWT HS256 with 120-minute expiry and a device claim checked on every request", "test_jwt_bound_to_device; smoke test: token from another device -> 401"],
        ["Privilege misuse", "Role dependencies; session ownership check (404 for another faculty's session)", "smoke test: student on faculty API -> 403; faculty check-in -> 403"],
        ["Forwarded link", "Link grants only a sign-in page; every check still applies", "demo scenarios 3-6"],
        ["Repeat or proxy marking", "UNIQUE(session_id, student_id); device may mark one roll per session; duplicate-face scan", "smoke test; demo scenarios 2, 6, 8"],
        ["Out-of-order calls", "Wizard steps enforced on the server (HTTP 409)", "api._require_step"],
        ["Cross-origin abuse", "CORS limited to localhost origins", "api.py middleware"],
        ["Bad input", "Pydantic models, image decode errors -> 400, face errors -> reasons", "api._read_image, FaceError"],
    ], "Security controls", widths=[0.20, 0.50, 0.30], font=9)
    d.p("**Known weaknesses.** The default `AM_JWT_SECRET` is a placeholder and PyJWT warns that the 30-byte default is shorter than the recommended 32 bytes; it must be changed "
        "for any real use. There is no rate limit or lockout on sign-in, the manual-location tab is enabled by default for testing (`AM_ALLOW_MANUAL_LOCATION`) and must be "
        "disabled in production, and wizard state in memory is lost on restart.")


def sec_install(d):
    d.h2("Installation and Execution")
    d.p("Windows: run `setup.bat` once (creates a Python 3.11 virtual environment, installs the requirements, seeds the demo accounts and runs `npm install`) "
        "and `run.bat` every time; it starts the API on port 8102 and the React app on port 5102 and opens the browser. `stop.bat` stops both. Linux and macOS: "
        "`pip install -r requirements.txt -r backend/requirements.txt`, `python scripts/seed_demo.py`, `uvicorn backend.api:app --port 8102` and `npm run dev` in "
        "`frontend/`. The original interface starts with `streamlit run app.py`. Full steps are in Appendix B and in `docs/03_HOW_TO_RUN.md`.")
