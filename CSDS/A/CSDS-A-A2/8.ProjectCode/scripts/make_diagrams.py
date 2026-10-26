"""Generate the Attendance Magic design diagrams (PNG, 150 dpi) into docs/diagrams/.

    python scripts/make_diagrams.py

Every diagram is drawn from the real code: core/models.py (tables), backend/api.py (routes and wizard state),
core/services.py (pipeline order) and core/liveness.py / core/face_match.py (decision rules). matplotlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import (AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, ROSE_L, Canvas, anchor)  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"


# ---------------------------------------------------------------------------------------------- 1 architecture
def architecture(out):
    c = Canvas(10.4, 7.4)
    c.zone(2, 59, 100, 13.5, "Users and browsers", fc="#f4f5fb")
    c.box(6, 60.5, 30, 8, "Faculty (laptop browser)\ncreate session, share link / QR,\nrecords, map, log, export", fs=7.4)
    c.box(37, 60.5, 30, 8, "Student (phone browser)\nsign in, GPS, camera or upload,\nrandom challenge, result", fs=7.4)
    c.box(68, 60.5, 30, 8, "Original Streamlit UI (port 8501)\nsame core/ logic and database\n(kept, covered by AppTest)", fs=7.4, ls="--")
    c.zone(2, 42.5, 100, 14.5, "Frontend: React 19 + Vite 8 (port 5102), Neo Brutal Grid design", fc="#eef4fe")
    c.box(6, 44, 30, 8.5, "12 routes, role guards\nlanding, login, check-in wizard,\ndashboard, sessions, students", fs=7.2)
    c.box(37, 44, 30, 8.5, "Capture and maps\ngetUserMedia camera or file upload,\nGeolocation API, Leaflet + OSM tiles", fs=7.2)
    c.box(68, 44, 30, 8.5, "Data layer\nfetch wrapper, X-Device-Id header,\nJWT bearer token, Recharts", fs=7.2)
    for x in (21, 52):
        c.arrow((x, 60.5), (x, 52.5), both=True)
    c.zone(2, 17, 100, 23.5, "Backend: FastAPI (port 8102; Vite proxies /api) - thin HTTP layer, no verification logic", fc="#eef8f2")
    c.box(6, 33, 92, 4.4, "27 endpoints:  auth - sessions - dashboard - students - check-in wizard (state, start, location, neutral, liveness, face, retake, reset) - export - public - qr - health",
          fc=INDIGO_L, ec=INDIGO, fs=7.0, bold=True)
    c.arrow((92, 44), (92, 37.4), label="/api  (HTTP, JSON, multipart)", both=True, loff=(-12, 0))
    svc = ["auth\nPBKDF2 + JWT\ndevice-bound", "device\nfingerprint\nSHA-256", "geofence\nhaversine +\ntolerance", "liveness\nFace Mesh metrics,\n8 challenges", "face_match\nArcFace cosine:\nid, duplicate", "services\neligibility,\npipeline", "export\n3-sheet\n.xlsx"]
    for i, t in enumerate(svc):
        c.box(5 + i * 13.2, 19, 12, 11.5, t, fs=6.6)
        c.arrow((11 + i * 13.2, 33), (11 + i * 13.2, 30.5))
    c.zone(2, 1.5, 100, 13.5, "Storage and models (local, offline)", fc="#fff8e8")
    c.box(6, 3, 38, 8, "SQLite  attendance_magic.db  (SQLAlchemy 2)\n5 tables: users, attendance_sessions, attendance_records,\ndevice_bindings, verification_attempts", fs=7.0)
    c.box(47, 3, 24, 8, "MediaPipe Face Mesh\n468 landmarks (bundled)", fs=7.0)
    c.box(74, 3, 24, 8, "InsightFace buffalo_l\nSCRFD + ArcFace R50, CPU", fs=7.0)
    c.arrow((15, 19), (15, 11), both=True)
    c.arrow((54, 19), (54, 11), both=True)
    c.arrow((70, 19), (80, 11), both=True)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 2 workflow
def workflow(out):
    c = Canvas(10.4, 5.6)
    r1 = [("1  Create session", "faculty sets course,\ntime window, centre,\nradius, allowed rolls", BLUE_L),
          ("2  Share link / QR", "unique token link\n?session=<token>\nshown with a QR code", BLUE_L),
          ("3  Sign in", "student opens the link;\nJWT bound to the\ndevice hash", INDIGO_L),
          ("4  Eligibility", "session live, roll allowed,\nnot already marked,\ndevice binding", INDIGO_L),
          ("5  Geo-fence", "GPS vs centre:\nhaversine <= radius\n+ 15 m tolerance", INDIGO_L)]
    r2 = [("6  Live challenge", "random action; photo 1\nneutral, photo 2 pose;\nFace Mesh metrics", GREEN_L),
          ("7  Face match", "frame consistency, identity\nvs enrolled face, no\nduplicate in session", GREEN_L),
          ("8  Record", "attendance row written;\nsuccess logged with\ndistance and scores", AMBER_L),
          ("9  Monitor", "live records, map,\nverification log,\nanalytics", AMBER_L),
          ("10  Export", "Excel: Summary,\nAttendance (absentees),\nVerification Log", ROSE_L)]
    bw, bh, gap = 16.6, 14, 3.9
    xs = [3 + i * (bw + gap) for i in range(5)]
    row1 = [c.box(x, 31, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, r1)]
    row2 = [c.box(x, 8, bw, bh, "", fc=f) for x, (_, _, f) in zip(xs, r2)]
    for b, (h, t, _) in zip(row1 + row2, r1 + r2):
        c.text(b["x"] + bw / 2, b["y"] + bh - 3.0, h, fs=8.2, bold=True)
        c.text(b["x"] + bw / 2, b["y"] + 5.4, t, fs=6.9)
    for r in (row1, row2):
        for a, b in zip(r[:-1], r[1:]):
            c.arrow(anchor(a, "r"), anchor(b, "l"))
    last, first = anchor(row1[-1], "b"), anchor(row2[0], "t")
    c.path([last, (last[0], 26.5), (first[0], 26.5), first])
    c.box(3, 49, 97.6, 4.6, "A failed stage stops the check-in with a plain reason (outside fence, challenge failed, face does not match, duplicate face) and the attempt is logged.",
          fc=AMBER_L, ec="#c9a45a", fs=7.2, r=1.5)
    c.arrow((xs[2] + bw / 2, 49), (xs[2] + bw / 2, 45), ls=":")
    c.box(3, 2.2, 97.6, 3.8, "Three failed liveness tries lock the wizard; every attempt (pass or block) is stored in verification_attempts for the faculty's log.",
          fc=GREY_L, ec="#9aa5ba", fs=7.1, r=1.5)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 3 DFD 0
def dfd0(out):
    c = Canvas(9.0, 5.2)
    sys_ = c.ellipse(45, 26, 30, 22, "Attendance Magic\n(0)", fc=INDIGO_L, fs=10)
    fac = c.box(3, 19, 16, 14, "FACULTY", fc=GREEN_L, bold=True, fs=9)
    stu = c.box(71, 19, 16, 14, "STUDENT", fc=AMBER_L, bold=True, fs=9)
    c.arrow((19, 30), (30, 30), label="session details,\nroll patterns,\nclose / reset device", lpos=0.5, loff=(0, 5))
    c.arrow((30, 22), (19, 22), label="session link + QR,\nrecords, map, log,\nExcel export", lpos=0.5, loff=(0, -5.5))
    c.arrow((71, 30), (60, 30), label="credentials, GPS fix,\ntwo photos", lpos=0.5, loff=(0, 5))
    c.arrow((60, 22), (71, 22), label="step results, reasons,\nscores, attendance\nconfirmation", lpos=0.5, loff=(0, -5.5))
    c.save(out)


# ---------------------------------------------------------------------------------------------- 4 DFD 1
def dfd1(out):
    c = Canvas(10.4, 6.6)

    def store(name, label, x, y, w):
        c.rect(x, y, w, 5.0, fc="#fff8e8")
        c.line((x + 6.5, y), (x + 6.5, y + 5.0))
        c.text(x + 3.2, y + 2.5, name, fs=7, bold=True)
        c.text(x + 6.5 + (w - 6.5) / 2, y + 2.5, label, fs=6.5)

    def proc(pid, name, cx, cy):
        c.ellipse(cx, cy, 16, 10.4, f"{pid}\n{name}", fc=INDIGO_L, fs=6.9)
    # stores
    store("D1", "users", 6, 59, 26)
    store("D2", "attendance_sessions", 38, 59, 30)
    store("D3", "attendance_records", 72, 59, 28)
    store("D1", "device_bindings", 3, 2.5, 22)
    store("D2", "sessions", 27, 2.5, 18)
    store("D4", "verification_attempts", 49, 2.5, 33)
    store("D3", "records", 86, 2.5, 15)
    # entities
    c.box(0.5, 41, 11, 7.2, "FACULTY", fc=GREEN_L, bold=True, fs=7.5)
    c.box(0.5, 29, 11, 7.2, "STUDENT", fc=AMBER_L, bold=True, fs=7.5)
    # processes
    proc("1", "Authenticate", 24, 45)
    proc("2", "Manage\nsessions", 50, 45)
    proc("8", "Reports and\nexport", 76, 45)
    for pid, name, cx in (("3", "Check\neligibility", 20), ("4", "Verify\nlocation", 38), ("5", "Verify\nliveness", 56), ("6", "Verify\nface", 74), ("7", "Record\nattendance", 92)):
        proc(pid, name, cx, 22)
    # stores <-> processes (top)
    c.arrow((24, 59), (24, 50.2), both=True)
    c.arrow((50, 59), (50, 50.2), both=True)
    c.arrow((76, 59), (76, 50.2), label="read", fs=6.3, loff=(3, 0))
    # entity flows
    c.arrow((11.5, 45), (16, 45), label="login", fs=6.3, loff=(0, 2))
    c.path([(6, 48.2), (6, 54), (50, 54), (50, 50.2)], label="session details", fs=6.3, seg=1, loff=(-12, 1.6))
    c.path([(76, 39.8), (76, 36.5), (3, 36.5), (3, 48.2)], head=True, label="session link, records, Excel export", fs=6.3, seg=1, loff=(-14, -1.6)) if False else None
    c.path([(84, 45), (95, 45), (95, 56), (2.5, 56), (2.5, 48.2)], label="records, map, log, Excel export", fs=6.3, seg=2, loff=(-10, 1.6))
    c.arrow((11.5, 32.5), (16.5, 42.5), label="credentials", fs=6.3, loff=(-3, 0.5))
    c.arrow((9, 29), (14, 24.5), label="link, GPS, photos", fs=6.3, loff=(-1, -3.2))
    # student chain
    for x0, x1 in ((28, 30), (46, 48), (64, 66), (82, 84)):
        c.arrow((x0, 22), (x1, 22))
    # data store reads/writes at the bottom
    c.arrow((14, 7.5), (16, 17.2), label="bindings", fs=6.0, loff=(-4, 0))
    c.arrow((36, 7.5), (24, 17.4), label="session", fs=6.0, loff=(4, 0))
    c.arrow((92, 16.8), (93, 7.5), label="row", fs=6.0, loff=(3, 0))
    for cx in (20, 38, 56, 74, 92):
        tx = min(max(cx, 52), 80)
        c.arrow((cx, 16.8), (tx, 7.5), ls=":", color="#8a93a8", lw=0.9)
    c.text(65, 11.5, "every stage appends an attempt", fs=6.3, italic=True)
    c.text(76, 63, "", fs=6)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 5 DFD 2
def dfd2(out):
    c = Canvas(10.4, 5.8)
    xs = [12, 32, 52, 72, 92]
    labels = ["6.1  Decode and detect@one face per frame", "6.2  Frame consistency@cos(f1, f2) >= 0.45", "6.3  Identity check@cos(f1, enrolled) >= 0.40",
              "6.4  Duplicate scan@max cos(f1, session) < 0.45", "6.5  Decide and log@reason text, scores"]
    for i, (x, t) in enumerate(zip(xs, labels)):
        c.ellipse(x, 33, 18.5, 12, t.replace("@", chr(10)), fc=GREEN_L if i == 4 else INDIGO_L, fs=6.6)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        c.arrow((x0 + 9.3, 33), (x1 - 9.3, 33))
    c.box(1, 48, 22, 4.6, "from process 5: two frames", fc=GREY_L, fs=6.8, r=1.2)
    c.arrow((12, 48), (12, 39.2))

    def store(x, y, w, name, label):
        c.rect(x, y, w, 5.0, fc="#fff8e8")
        c.line((x + 6, y), (x + 6, y + 5))
        c.text(x + 3, y + 2.5, name, fs=7, bold=True)
        c.text(x + 6 + (w - 6) / 2, y + 2.5, label, fs=6.2)
    store(41, 14, 21, "D1", "enrolled embedding")
    store(63, 14, 21, "D3", "session embeddings")
    store(85, 14, 17, "D4", "attempts")
    c.arrow((51, 19), (52, 27), label="read", fs=6.2, loff=(3, 0))
    c.arrow((73, 19), (72, 27), label="read", fs=6.2, loff=(3, 0))
    c.arrow((92, 27), (93, 19), label="write", fs=6.2, loff=(3, 0))
    c.box(27, 44, 74, 4.6, "any check fails -> reason text to the student (retake or start over); no record is written", fc=ROSE_L, fs=6.8, r=1.2)
    for x in xs[1:4]:
        c.arrow((x, 39.2), (x, 44), ls=":", label="fail" if x == 52 else None, fs=6.2, loff=(3, 0))
    c.box(2, 3, 98, 5, "all pass -> process 7 records attendance (identity and duplicate similarities stored with the record)", fc=AMBER_L, ec="#c9a45a", fs=6.9, r=1.2)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 6 ER
def er(out):
    c = Canvas(10.4, 8.6)

    def table(x, y, w, name, cols):
        rowh = 3.0
        h = rowh * (len(cols) + 1)
        c.rect(x, y, w, h, fc="white", lw=1.2, z=1)
        c.rect(x, y + h - rowh, w, rowh, fc=INDIGO_L, lw=1.2, z=2)
        c.text(x + w / 2, y + h - rowh / 2, name, fs=8, bold=True)
        for i, (n, t, tag) in enumerate(cols):
            yy = y + h - rowh * (i + 1.5)
            c.text(x + 1.2, yy, f"{tag:<3}{n}", fs=6.4, ha="left", bold=bool(tag))
            c.text(x + w - 1.2, yy, t, fs=6.2, ha="right", color="#44506b")
        return {"x": x, "y": y, "w": w, "h": h}
    table(2, 40, 31, "attendance_sessions", [("id", "int", "PK"), ("token", "str64 UQ", ""), ("faculty_id", "int", "FK"), ("course_code", "str32", ""), ("course_name", "str128", ""),
                                              ("section", "str32", ""), ("starts_at / ends_at", "datetime", ""), ("latitude / longitude", "float", ""), ("radius_m", "float", ""),
                                              ("allowed_rolls", "text", ""), ("is_closed", "bool", ""), ("created_at", "datetime", "")])
    table(37, 50, 29, "users", [("id", "int", "PK"), ("role", "str16", ""), ("username", "str64 UQ", ""), ("full_name", "str128", ""), ("roll_number", "str32 UQ", ""),
                                ("password_hash", "str256", ""), ("face_embedding", "blob 512xf32", ""), ("created_at", "datetime", "")])
    table(72, 36, 30, "attendance_records", [("id", "int", "PK"), ("session_id", "int", "FK"), ("student_id", "int", "FK"), ("roll_number / name", "str", ""), ("marked_at", "datetime", ""),
                                             ("latitude, longitude", "float", ""), ("gps_accuracy_m", "float", ""), ("distance_m", "float", ""), ("device_hash", "str64", ""),
                                             ("challenge", "str32", ""), ("liveness_score", "float", ""), ("identity_similarity", "float", ""), ("max_duplicate_similarity", "float", ""),
                                             ("face_embedding", "blob", "")])
    table(37, 16, 29, "device_bindings", [("id", "int", "PK"), ("user_id", "int", "FK"), ("device_hash", "str64", ""), ("device_label", "str256", ""), ("first_seen", "datetime", ""), ("last_seen", "datetime", "")])
    table(2, 8, 31, "verification_attempts", [("id", "int", "PK"), ("session_id", "int", "FK"), ("roll_number", "str32", ""), ("stage", "str32", ""), ("passed", "bool", ""),
                                               ("reason", "text", ""), ("device_hash", "str64", ""), ("created_at", "datetime", "")])
    c.arrow((37, 68), (33, 68), both=True, label="1:N", fs=6.4, loff=(0, 2.0))
    c.arrow((66, 62), (72, 62), both=True, label="1:N", fs=6.4, loff=(0, 2.0))
    c.path([(17, 76), (17, 83), (87, 83), (87, 78)], label="1:N (UNIQUE session_id + student_id)", fs=6.4, seg=1, loff=(0, 1.6))
    c.arrow((51, 50), (51, 40.6), both=True, label="1:N", fs=6.4, loff=(2.5, 0))
    c.arrow((17, 40), (17, 35), both=True, label="1:N", fs=6.4, loff=(2.5, 0))
    c.text(36, 2.5, "UNIQUE(user_id, device_hash) on device_bindings", fs=6.8, ha="left", italic=True)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 7 UML
def uml(out):
    c = Canvas(10.4, 7.8)

    def klass(x, y, w, name, attrs, ops=()):
        rowh = 2.6
        n = len(attrs) + len(ops) + 1
        h = rowh * n + 3
        c.rect(x, y, w, h, fc="white", lw=1.2, z=1)
        c.rect(x, y + h - rowh - 0.5, w, rowh + 0.5, fc=INDIGO_L, lw=1.2, z=2)
        c.text(x + w / 2, y + h - (rowh + 0.5) / 2, name, fs=7.6, bold=True)
        yy = y + h - rowh - 2.2
        for a_ in attrs:
            c.text(x + 1, yy, a_, fs=6.2, ha="left")
            yy -= rowh
        if ops:
            c.line((x, yy + rowh / 2 + 0.2), (x + w, yy + rowh / 2 + 0.2), lw=0.8)
            for o in ops:
                yy -= 0.3
                c.text(x + 1, yy, o, fs=6.2, ha="left", color="#2b4a8a")
                yy -= rowh
        return h
    klass(2, 52, 25, "User", ["id, role, username", "full_name, roll_number", "password_hash", "face_embedding: bytes"])
    klass(33, 52, 27, "AttendanceSession", ["token, course_code, section", "starts_at, ends_at", "latitude, longitude, radius_m", "allowed_rolls, is_closed"], ["status(now) -> str", "is_open(now) -> bool"])
    klass(66, 52, 27, "AttendanceRecord", ["session_id, student_id", "distance_m, gps_accuracy_m", "challenge, liveness_score", "identity_similarity", "max_duplicate_similarity", "face_embedding"])
    klass(2, 33, 25, "DeviceBinding", ["user_id, device_hash", "device_label", "first_seen, last_seen"])
    klass(33, 33, 27, "VerificationAttempt", ["session_id, roll_number", "stage, passed, reason", "device_hash, created_at"])
    c.arrow((27, 62), (33, 62), both=True, label="1..*", fs=6.2, loff=(0, 1.6))
    c.arrow((60, 62), (66, 62), both=True, label="1..*", fs=6.2, loff=(0, 1.6))
    c.arrow((14, 52), (14, 47.5), both=True, label="1..*", fs=6.2, loff=(3, 0))
    c.arrow((46, 52), (46, 47.5), both=True, label="1..*", fs=6.2, loff=(3, 0))
    c.zone(2, 1, 100, 29, "Service and decision classes (core/)", fc="#f4f8f4")
    klass(4, 2.5, 23, "face_match", ["MatchResult(passed, reason,", "  identity_similarity,", "  max_duplicate_similarity)"], ["embed(img) -> 512-d", "cosine(a, b)", "verify_faces(...)"])
    klass(30, 2.5, 23, "liveness", ["FaceMetrics(yaw, pitch,", "  roll_deg, mar, ear)", "LivenessResult"], ["analyze(img)", "verify_challenge(c, n, m)", "check_neutral(m)"])
    klass(56, 2.5, 20, "geofence", ["GeoResult(inside,", "  distance_m, allowed_m)"], ["haversine_m(...)", "check_geofence(...)"])
    klass(79, 2.5, 22, "services", ["Eligibility(ok, reason)", "PipelineResult(success,", "  stage, reason, record)"], ["check_eligibility(...)", "run_pipeline(...)", "record_attendance(...)"])
    c.save(out)


# ---------------------------------------------------------------------------------------------- 8 use case
def usecase(out):
    c = Canvas(9.6, 6.2)
    c.zone(21, 2, 58, 58, "Attendance Magic", fc="#fbfbfe")
    fac = [("Create time-bound session", 52), ("Set geo-fence and roll patterns", 45.5), ("Share link and QR", 39), ("View records, map, log, analytics", 32.5),
           ("Export attendance to Excel", 26), ("Close session / reset devices", 19.5), ("Enrol student reference face", 13)]
    stu = [("Register with reference face", 52), ("Sign in (device-bound JWT)", 45.5), ("Pass eligibility check", 39), ("Verify location (GPS)", 32.5),
           ("Complete random live challenge", 26), ("Pass face verification", 19.5), ("View own result", 13)]
    for t, y in fac:
        c.ellipse(36, y, 26, 5.2, t, fs=6.2)
    for t, y in stu:
        c.ellipse(64, y, 26, 5.2, t, fs=6.2, fc=AMBER_L, ec="#b07a2a")
    c.box(2, 28, 14, 8, "FACULTY", fc=GREEN_L, bold=True, fs=8)
    c.box(82, 28, 14, 8, "STUDENT", fc=AMBER_L, bold=True, fs=8)
    for t, y in fac:
        c.line((16, 32), (23.5, y), lw=0.7)
    for t, y in stu:
        c.line((82, 32), (76.5, y), lw=0.7)
    c.text(50, 4.5, "every student step is logged in verification_attempts", fs=6.5, italic=True)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 9 sequence
def sequence(out):
    c = Canvas(10.4, 7.2)
    actors = [("Student", 8), ("React app\n(browser)", 28), ("FastAPI\nbackend", 50), ("core/ services\n+ models", 72), ("SQLite", 94)]
    for t, x in actors:
        c.box(x - 8, 66, 16, 5.5, t, fc=INDIGO_L, fs=7.2, bold=True)
        c.line((x, 66), (x, 1.5), ls=":", color="#8a93a8")
    msgs = [(0, 1, "open /checkin/<token>, sign in", 62.5), (1, 2, "POST /api/auth/login (+ X-Device-Id)", 59), (2, 3, "authenticate -> PBKDF2 verify, issue JWT (dev hash)", 55.5),
            (2, 1, "token, user", 52.5), (1, 2, "POST /start  (JWT)", 49.5), (2, 3, "check_eligibility(session, user, device)", 46.5), (3, 4, "read record, bindings; bind device", 43.5),
            (1, 2, "POST /location  {lat, lon, accuracy}", 40.5), (2, 3, "check_geofence -> inside, distance", 37.5), (1, 2, "POST /liveness  (neutral, challenge photos)", 34.5),
            (2, 3, "analyze x2 (Face Mesh) -> verify_challenge", 31.5), (1, 2, "POST /face", 28.5), (2, 3, "embed x2 (ArcFace) -> verify_faces", 25.5),
            (3, 4, "session embeddings; insert record + attempts", 22.5), (2, 1, "result: marked, distance, scores", 19.5), (1, 0, "\"Marked. Present.\" screen", 16.5)]
    xs = {i: a[1] for i, a in enumerate(actors)}
    for a, b, t, y in msgs:
        c.arrow((xs[a], y), (xs[b], y), label=t, fs=6.4, loff=(0, 1.4))
    c.text(52, 11.5, "Each failed stage returns the reason and writes a verification_attempts row; 3 failed liveness tries lock the wizard.", fs=6.8, italic=True)
    c.save(out)


# ---------------------------------------------------------------------------------------------- 10 flowchart
def flowchart(out):
    c = Canvas(9.4, 8.6)
    cx = 38
    c.terminal(cx, 83, 22, 4, "Start: student opens session link")
    steps = [("Sign in: password check, JWT bound to device hash", 77), ("Eligibility: live? roll allowed? not marked?\ndevice binding ok?", 70)]
    c.arrow((cx, 81), (cx, 79.4))
    c.box(cx - 17, 74.6, 34, 5.6, steps[0][0], fs=7)
    c.arrow((cx, 74.6), (cx, 72.6))
    d1 = c.diamond(cx, 69, 34, 7.6, steps[1][0], fs=6.6)
    c.arrow((cx, 65.2), (cx, 63.3))
    c.text(cx + 2, 64.4, "yes", fs=6.3, ha="left")
    c.box(cx - 17, 58.4, 34, 5.6, "GPS fix: distance d = haversine(student, centre)", fs=7)
    c.arrow((cx, 58.4), (cx, 56.4))
    d2 = c.diamond(cx, 52.6, 34, 7.6, "accuracy <= 150 m and\nd <= radius + 15 m ?", fs=6.8)
    c.arrow((cx, 48.8), (cx, 46.9))
    c.text(cx + 2, 47.9, "yes", fs=6.3, ha="left")
    c.box(cx - 17, 41.4, 34, 5.5, "Random challenge; photo 1 neutral, photo 2 pose;\nFace Mesh yaw, pitch, roll, MAR, EAR", fs=6.6)
    c.arrow((cx, 41.4), (cx, 39.4))
    d3 = c.diamond(cx, 35.6, 34, 7.6, "neutral frame ok and\nchallenge delta >= threshold ?", fs=6.6)
    c.arrow((cx, 31.8), (cx, 29.9))
    c.text(cx + 2, 30.8, "yes", fs=6.3, ha="left")
    c.box(cx - 17, 24.4, 34, 5.5, "Embed both photos (ArcFace 512-d, one face each)", fs=6.8)
    c.arrow((cx, 24.4), (cx, 22.4))
    d4 = c.diamond(cx, 18.6, 34, 7.6, "cos(f1,f2) >= 0.45 and\ncos(f1, enrolled) >= 0.40 ?", fs=6.6)
    c.arrow((cx, 14.8), (cx, 12.9))
    c.text(cx + 2, 13.8, "yes", fs=6.3, ha="left")
    d5 = c.diamond(cx, 9.4, 34, 6.8, "max cos(f1, session faces) < 0.45 ?", fs=6.6)
    c.arrow((cx, 6.0), (cx, 4.2))
    c.text(cx + 2, 5.2, "yes", fs=6.3, ha="left")
    c.terminal(cx, 2.2, 36, 3.6, "Record attendance + log success")
    # rejections on the right
    rej = [(69, "eligibility", "no"), (52.6, "location", "no"), (35.6, "liveness (retry <= 3,\nnew challenge each time)", "no"), (18.6, "face: identity / consistency", "no"), (9.4, "face: duplicate", "no")]
    for y, t, _ in rej:
        c.arrow((cx + 17, y), (62, y))
        c.text(cx + 18.5, y + 1.6, "no", fs=6.3, ha="left")
        c.box(62, y - 3.2, 30, 6.4, f"Blocked at {t}\nreason shown, attempt logged", fc=ROSE_L, fs=6.3)
    c.text(78, 79, "Every stage writes\na verification_attempts row", fs=7, italic=True)
    c.save(out)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "01_system_architecture.png")
    workflow(OUT / "02_high_level_workflow.png")
    dfd0(OUT / "03_dfd_level0.png")
    dfd1(OUT / "04_dfd_level1.png")
    dfd2(OUT / "05_dfd_level2.png")
    er(OUT / "06_er_diagram.png")
    uml(OUT / "07_uml_class_diagram.png")
    usecase(OUT / "08_use_case_diagram.png")
    sequence(OUT / "09_sequence_diagram.png")
    flowchart(OUT / "10_algorithm_flowchart.png")
    print("done")
