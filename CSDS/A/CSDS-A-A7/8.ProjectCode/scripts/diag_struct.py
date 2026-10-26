"""ER, UML class, use-case and sequence diagrams for SHEGUARD (drawn from backend/app/models, routes, services and frontend/src)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


# --------------------------------------------------------------------------- ER
def _table(c, x, top, w, name, cols, fc=BLUE_L, fs=6.0):
    h = 4.2 + 2.55 * len(cols)
    y = top - h
    c.box(x, y, w, h, "", fc="white", r=1.2)
    c.box(x, y + h - 4.2, w, 4.2, name, fc=fc, bold=True, fs=7.6, r=1.2)
    for i, col in enumerate(cols):
        c.text(x + 1.2, y + h - 6.0 - 2.55 * i, col, fs=fs, ha="left")
    return {"x": x, "y": y, "w": w, "h": h}


def er(out):
    c = Canvas(10.4, 10.0)
    W = 24
    X = [2, 32, 62, 80]
    t_users = _table(c, X[0], 97, W, "users", ["PK id", "name", "email (unique, index)", "password_hash (bcrypt)", "created_at"], BLUE_L)
    t_guard = _table(c, X[1], 97, W, "guardians", ["PK id", "FK owner_id -> users", "name", "phone", "email", "telegram_chat_id", "created_at"], GREEN_L)
    t_sess = _table(c, X[0], 74, W, "emergency_sessions", ["PK id", "FK user_id -> users", "share_token (unique, index)", "status (active | cancelled)", "trigger (manual | safephrase)",
                                                          "started_at", "ended_at", "last_lat", "last_lng", "last_update_at"], ROSE_L)
    t_ping = _table(c, X[1], 74, W, "location_pings", ["PK id", "FK session_id -> sessions", "lat", "lng", "ts"], AMBER_L)
    t_evid = _table(c, X[0], 38, W, "evidence", ["PK id", "FK session_id -> sessions", "kind (photo | audio)", "file_path", "sha256 (64 hex)", "lat", "lng", "captured_at"], AMBER_L)
    t_dist = _table(c, X[2], 97, W, "district_risk", ["PK id", "state", "district", "lat", "lng", "crime_rate", "risk_score (0-100)", "risk_tier (low|medium|high)"], GREY_L)

    def card(a, b, la="1", lb="N", fs=7):
        c.text(a[0], a[1], la, fs=fs, bold=True, color=INDIGO)
        c.text(b[0], b[1], lb, fs=fs, bold=True, color=INDIGO)

    # users 1 - N guardians
    yg = 91
    c.line((X[0] + W, yg), (X[1], yg)); card((X[0] + W + 1.2, yg + 1.6), (X[1] - 1.2, yg + 1.6))
    # users 1 - N sessions
    xv = X[0] + 12
    c.line((xv, t_users["y"]), (xv, 74)); card((xv + 1.4, t_users["y"] - 1.8), (xv + 1.4, 74 + 1.8))
    # sessions 1 - N pings
    yp = 66
    c.line((X[0] + W, yp), (X[1], yp)); card((X[0] + W + 1.2, yp + 1.6), (X[1] - 1.2, yp + 1.6))
    # sessions 1 - N evidence
    c.line((xv, t_sess["y"]), (xv, 38)); card((xv + 1.4, t_sess["y"] - 1.8), (xv + 1.4, 38 + 1.8))
    # legend
    c.box(32, 10, 58, 22, "", fc="#f7f8fb", ec="#9aa5ba", lw=0.9, ls="--")
    for i, t in enumerate(["How to read", "PK primary key, FK foreign key; 1 / N = cardinality at each end", "district_risk has no foreign key: it is a lookup table loaded from",
                           "data/district_risk.csv on first start (467 rows) and compared by distance only",
                           "Deleting a user cascades to guardians and sessions, and a session to its pings and",
                           "evidence rows (ORM cascade delete-orphan); the evidence FILES stay on disk",
                           "Evidence files are named {first 16 hex of SHA-256}.{ext} under data/evidence/{session id}/"]):
        c.text(34, 29 - i * 2.9, t, fs=6.0 if i else 6.8, ha="left", bold=(i == 0))
    c.text(52, 5.0, "6 tables, SQLite via SQLAlchemy 2.  Every foreign key points at users or emergency_sessions; the SafePhrase list lives in the browser, not in the database.", fs=6.2, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- UML
def _cls(c, x, top, w, name, attrs, methods, head=BLUE_L, fs=5.6):
    n = max(len(attrs), 1) + max(len(methods), 1)
    h = 4.2 + 2.5 * n + 1.6
    y = top - h
    c.box(x, y, w, h, "", fc="white", r=0.8, lw=1.1)
    c.box(x, y + h - 4.2, w, 4.2, name, fc=head, bold=True, fs=6.6, r=0.8)
    ya = y + h - 6.0
    for a in attrs:
        c.text(x + 1.0, ya, a, fs=fs, ha="left")
        ya -= 2.5
    if not attrs:
        ya -= 2.5
    c.line((x, ya + 1.2), (x + w, ya + 1.2), lw=0.8)
    ya -= 0.2
    for m in methods:
        c.text(x + 1.0, ya, m, fs=fs, ha="left", italic=True)
        ya -= 2.5
    return {"x": x, "y": y, "w": w, "h": h, "top": top}


def uml(out):
    c = Canvas(10.4, 13.6)
    c.zone(1, 96, 102, 39, "Domain model (SQLAlchemy entities, backend/app/models.py)", fc="#f4f5fb")
    W = 13.6
    xs = [3 + i * 16.9 for i in range(6)]
    T = 128
    U = _cls(c, xs[0], T, W, "User", ["id, name", "email (unique)", "password_hash", "created_at"], [], head=BLUE_L)
    G = _cls(c, xs[1], T, W, "Guardian", ["id, owner_id", "name, phone", "email", "telegram_chat_id"], [], head=GREEN_L)
    S = _cls(c, xs[2], T, W, "EmergencySession", ["id, user_id", "share_token", "status, trigger", "started_at, ended_at", "last_lat, last_lng"], [], head=ROSE_L)
    P = _cls(c, xs[3], T, W, "LocationPing", ["id, session_id", "lat, lng", "ts"], [], head=AMBER_L)
    E = _cls(c, xs[4], T, W, "Evidence", ["id, session_id", "kind, file_path", "sha256", "lat, lng", "captured_at"], [], head=AMBER_L)
    D = _cls(c, xs[5], T, W, "DistrictRisk", ["id, state, district", "lat, lng", "crime_rate", "risk_score", "risk_tier"], [], head=GREY_L)
    ly = T - 9

    def card(x, y, t):
        c.text(x, y, t, fs=6.2, bold=True, color=INDIGO)

    c.line((xs[0] + W, ly), (xs[1], ly))
    card(xs[0] + W + 0.8, ly + 1.7, "1"); card(xs[1] - 0.8, ly + 1.7, "*")
    c.line((xs[2] + W, ly), (xs[3], ly))
    card(xs[2] + W + 0.8, ly + 1.7, "1"); card(xs[3] - 0.8, ly + 1.7, "*")
    ys = 98.5
    c.path([(xs[0] + 7, U["y"]), (xs[0] + 7, ys + 5.5), (xs[2] + 4, ys + 5.5), (xs[2] + 4, S["y"])], head=False)
    card(xs[0] + 8.5, U["y"] - 1.7, "1"); card(xs[2] + 5.5, S["y"] - 1.7, "*")
    c.path([(xs[2] + 10, S["y"]), (xs[2] + 10, ys + 2.5), (xs[4] + 7, ys + 2.5), (xs[4] + 7, E["y"])], head=False)
    card(xs[2] + 11.5, S["y"] - 1.7, "1"); card(xs[4] + 8.5, E["y"] - 1.7, "*")
    c.text(52, 97.4, "DistrictRisk is a lookup table with no relation to the other entities. SafePhrase settings are held by the React app (localStorage), not by any entity.", fs=5.8, italic=True)

    # ---- routers and services
    c.zone(1, 44, 102, 51, "Boundary classes (FastAPI routers) and service classes (backend/app/services, auth.py, ws_manager.py)", fc="#f1f9f5")
    RT = [("auth\n/api/auth", ["POST /register", "POST /login", "GET /me"]), ("guardians\n/api/guardians", ["GET, POST", "PUT /{id}", "DELETE /{id}"]),
          ("risk\n/api/risk", ["GET /areas"]), ("routes_plan\n/api/routes", ["POST /plan"]), ("places\n/api/places", ["GET /search"]),
          ("sos\n/api/sos", ["POST /start", "POST /{id}/location", "POST /{id}/cancel", "GET /{id}"]), ("evidence\n/api/sos", ["POST /{id}/evidence", "GET /{id}/evidence"]),
          ("track\n/api/track", ["GET /{share_token}"]), ("ai\n/api/ai", ["POST /ask"]), ("ws\n/ws/track", ["WS /{share_token}"])]
    rw, rg = 9.4, 0.7
    rb = []
    for i, (name, ms) in enumerate(RT):
        x = 1.5 + i * (rw + rg)
        h = 7.2 + 2.2 + 2.5 * len(ms)
        top = 89.5
        c.box(x, top - h, rw, h, "", fc="white", r=0.8, lw=1.0)
        c.box(x, top - 7.2, rw, 7.2, name, fc=INDIGO_L, bold=True, fs=5.3, r=0.8, ec=INDIGO)
        for j, m in enumerate(ms):
            c.text(x + 0.6, top - 9.2 - 2.5 * j, m, fs=4.9, ha="left", italic=True)
        rb.append({"x": x, "y": top - h, "w": rw, "h": h})
    SV = [("Security (auth.py)", ["HS256 JWT, 7 days", "bcrypt hash / verify"], ["get_current_user()", "create_access_token()"], GREY_L),
          ("risk service", ["TIER_WEIGHT 1/2.5/5", "NIGHT_MULTIPLIER 1.6"], ["score_route()", "nearest_district()"], INDIGO_L),
          ("osrm service", ["OSRM_BASE (demo)"], ["get_route_alternatives()"], GREY_L),
          ("gemini service", ["SYSTEM_PROMPT", "GEMINI_MODEL"], ["ask_gemini()"], GREY_L),
          ("telegram / email", ["Bot token, Gmail app", "password (empty here)"], ["send_telegram_message()", "send_email()"], ROSE_L),
          ("ws_manager + hashing", ["viewers by share token"], ["add_viewer(), broadcast()", "sha256_bytes()"], AMBER_L)]
    sx = [1.5 + i * 17.0 for i in range(6)]
    for (name, at, me, col), x in zip(SV, sx):
        _cls(c, x, 64, 15.8, name, at, me, head=col, fs=5.3)
    c.arrow((rb[3]["x"] + 4, rb[3]["y"]), (sx[1] + 6, 64), label="uses", fs=5.4, loff=(4, 0))
    c.arrow((rb[5]["x"] + 4, rb[5]["y"]), (sx[4] + 6, 64), label="uses", fs=5.4, loff=(4, 0))
    c.text(52, 45.8, "Every protected router also depends on Security (get_current_user) and the database session (get_db). routes_plan -> osrm + risk; ai -> gemini; sos -> telegram / email + ws_manager; evidence -> hashing.", fs=5.2, italic=True)

    # ---- frontend
    c.zone(1, 1, 102, 40, "React front end (frontend/src): shell, screens, hooks and libraries that matter", fc="#fff8ee")
    FE = [("App (Shell)", ["user, token, guardians", "riskAreas, settings", "activeSession, activity"], ["startSos(trigger)", "signedIn() / signOut()"], BLUE_L),
          ("RoutesScreen", ["origin, destination", "routes, selected"], ["planRoute()", "choose(place)"], INDIGO_L),
          ("SafePhraseScreen", ["phrases, sensitivity"], ["addPhrase(), edit()", "runTest()"], INDIGO_L),
          ("EmergencyScreen", ["session, evidence", "holdProgress (3 s)"], ["upload(kind, blob)", "cancelSession()"], ROSE_L),
          ("TrackScreen", ["token, track info", "WebSocket"], ["load /api/track", "apply push"], AMBER_L),
          ("Hooks and lib", ["useVoiceTrigger", "useLiveLocation (4 s)", "matchSafePhrase()", "api(), getPosition()"], ["routeRiskLevel()"], GREY_L)]
    fx = [1.5 + i * 17.0 for i in range(6)]
    for (name, at, me, col), x in zip(FE, fx):
        _cls(c, x, 36, 15.8, name, at, me, head=col, fs=5.3)
    c.text(52, 3.6, "App renders one screen at a time and the public /track/{token} page without login. Hooks call the API with the bearer token and use the Web Speech, Geolocation and MediaRecorder APIs.", fs=5.3, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- use case
def usecase(out):
    c = Canvas(10.4, 8.8)
    c.zone(21, 1.5, 58, 84, "SHEGUARD (web app + API)", fc="#fbfbff")

    def actor(x, y, label):
        c.ax.plot([x], [y + 6.2], "o", ms=7, mfc="white", mec="#1b2238")
        c.line((x, y + 5.4), (x, y + 2.4)); c.line((x - 2.6, y + 4.2), (x + 2.6, y + 4.2))
        c.line((x, y + 2.4), (x - 2.2, y)); c.line((x, y + 2.4), (x + 2.2, y))
        c.text(x, y - 2.4, label, fs=7.6, bold=True)

    actor(9, 40, "User")
    actor(95, 66, "Guardian\n(no account)")
    uc = ["Register / log in", "Manage guardians", "Plan a safe route", "Set SafePhrases and sensitivity", "Trigger SOS (tap or phrase)",
          "Stream live location", "Capture photo / audio evidence", "Cancel SOS (hold 3 s)", "Ask the AI assistant"]
    ys = [78 - i * 8.6 for i in range(len(uc))]
    for t, y in zip(uc, ys):
        c.ellipse(40, y, 31, 6, t, fs=6.5)
        c.line((13.5, 45), (24.5, y))
    c.ellipse(67, 78, 22, 6, "Open tracking link", fs=6.5, fc=AMBER_L, ec="#c9a45a")
    c.line((90.5, 74), (78, 78))
    c.ellipse(67, 69, 22, 6, "Watch live position", fs=6.5, fc=AMBER_L, ec="#c9a45a")
    c.line((90.5, 72), (77, 69))
    c.arrow((40, 40.6), (40, 38.0), ls="--")
    c.text(42, 39.3, "<<include>>", fs=5.4, italic=True, ha="left")
    c.box(83, 52, 19.5, 6.5, "OSRM + Nominatim", fc=GREY_L, fs=6.6, bold=True)
    c.box(83, 36.5, 19.5, 8.5, "Telegram + Gmail\n(not configured\nin this run)", fc=ROSE_L, ec="#c98a8a", fs=6.4, bold=True)
    c.box(83, 4.5, 19.5, 6.5, "Gemini API", fc=GREY_L, fs=6.6, bold=True)
    c.arrow((55.5, 60.8), (83, 56.5), ls="--")
    c.arrow((55.5, 43.6), (83, 41.5), ls="--")
    c.arrow((55.5, 9.2), (83, 7.5), ls="--")
    c.text(52, 0.4, "Solid: the user takes part in the use case.  Dashed: the use case calls an external system.  There is no admin role: every account is an ordinary user.", fs=5.9, italic=True)
    c.save(out)


# --------------------------------------------------------------------------- sequence
def sequence(out):
    c = Canvas(10.4, 10.6)
    names = [("User\n(browser)", 7), ("API\n(FastAPI)", 27), ("SQLite +\nevidence/", 45), ("ws_manager", 62), ("Telegram /\nGmail", 79), ("Guardian\n(browser)", 95)]
    top, bot = 100, 1.5
    for n, x in names:
        c.box(x - 6.4, top, 12.8, 5.2, n, fc=INDIGO_L, ec=INDIGO, fs=6.6, bold=True)
        c.line((x, top), (x, bot), color="#9aa5ba", ls="--", lw=0.9)
    X = {"User": 7, "API": 27, "SQLite": 45, "ws": 62, "Alerts": 79, "Guardian": 95}
    y = 96.0

    def msg(a, b, text, dy=4.5, dashed=False, self_=False):
        nonlocal y
        xa, xb = X[a], X[b]
        if self_:
            c.path([(xa, y), (xa + 5, y), (xa + 5, y - 2.0), (xa, y - 2.0)])
            c.text(xa + 6.2, y - 1.0, text, fs=5.9, ha="left")
            y -= dy
            return
        c.arrow((xa, y), (xb, y), ls="--" if dashed else "-", label=text, fs=5.9, loff=(0, 1.6))
        y -= dy

    msg("User", "User", "1  tap SOS or SafePhrase matched; getPosition()", self_=True, dy=5.4)
    msg("User", "API", "2  POST /api/sos/start {lat, lng, trigger}  + Bearer JWT")
    msg("API", "API", "3  decode JWT, load user", self_=True, dy=5.4)
    msg("API", "SQLite", "4  INSERT EmergencySession (share_token = uuid4 hex) + first LocationPing")
    msg("API", "SQLite", "5  SELECT guardians WHERE owner_id = user")
    msg("API", "Alerts", "6  per guardian: Telegram message and email with tracking URL (best effort)")
    msg("Alerts", "API", "sent / not sent for each channel", dashed=True)
    msg("API", "User", "7  200 {session_id, share_token, tracking_url, delivery[]}", dashed=True)
    msg("Guardian", "API", "8  open /track/{token}: GET /api/track/{token}  (no login)")
    msg("API", "Guardian", "status, user name, path, last position", dashed=True)
    msg("Guardian", "ws", "9  WebSocket /ws/track/{token}: add_viewer()")
    msg("User", "API", "10  watchPosition every ~4 s: POST /api/sos/{id}/location")
    msg("API", "SQLite", "11  UPDATE last position; INSERT LocationPing")
    msg("API", "ws", "12  broadcast({type: location, lat, lng, ts})")
    msg("ws", "Guardian", "marker and path update on the map", dashed=True)
    msg("User", "API", "13  POST /api/sos/{id}/evidence (multipart photo or audio)")
    msg("API", "SQLite", "14  SHA-256 of bytes; write file; INSERT Evidence (hash, time, lat, lng)")
    msg("User", "API", "15  hold 3 s: POST /api/sos/{id}/cancel")
    msg("API", "SQLite", "16  status = cancelled; ended_at = now")
    msg("API", "ws", "17  broadcast({type: cancelled})")
    msg("ws", "Guardian", "page shows 'has ended the emergency'", dashed=True)
    c.save(out)
