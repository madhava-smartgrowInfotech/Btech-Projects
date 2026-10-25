"""Draw the ResQAI design diagrams into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: app.py (routes, helpers), auth.py (accounts), train_models.py (data + training),
data/*.json (the only stored data) and frontend/src (React pages, MonitorContext state machine).
    python scripts/docs_build/make_diagrams.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403
from matplotlib.patches import Rectangle  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def route(ax, pts, label=None, lpos=None, color=GREY, fs=7.0, ls="-", lw=1.5):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if len(pts) > 2:
        ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, ls=ls, zorder=4, solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], None, color=color, lw=lw, ls=ls)
    if label:
        ax.text(lpos[0], lpos[1], label, fontsize=fs, ha="center", va="center", color=INK, zorder=6, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


# ---------------------------------------------------------------------------------------------- 01
def system_architecture():
    fig, ax = canvas(10, 9.0, 100, 90)
    panel(ax, 2, 71, 96, 18, "Presentation tier - React 19 + Vite 8 single-page app (port 5302)", PALE_BLUE, BLUE)
    box(ax, 15, 77, 24, 10.5, "Pages\nLanding - Login - Register\nLive monitor - Manual override\nEmergency response", BLUE, fs=7.2)
    box(ax, 40, 77, 24, 10.5, "MonitorContext state\nreadings - event log (25)\n15 s countdown - dispatch", BLUE, fs=7.2)
    box(ax, 64, 77, 22, 10.5, "lib/api.js\nfetch wrapper, Bearer token\n(Vite proxies /api to 8302)", BLUE, fs=7.2)
    box(ax, 87, 77, 20, 10.5, "Leaflet map - Recharts\nsensor trace\nbrowser Geolocation", BLUE, fs=7.0)

    panel(ax, 2, 49, 96, 20, "Application tier - Flask 3 (port 8302): app.py + auth.py", PALE_TEAL, TEAL)
    box(ax, 14, 55, 21, 11, "auth blueprint\nregister - login - me\nscrypt hash, signed token\n5-try lockout", TEAL, fs=7.0)
    box(ax, 37, 55, 21, 11, "/api/simulate\n5 scenario generators\n(mirror training)", TEAL, fs=7.0)
    box(ax, 60, 55, 21, 11, "/api/predict\nbuild_feature_vector\npredict_from_features", TEAL, fs=7.0)
    box(ax, 83, 55, 23, 11, "/api/hospitals - /api/emergency\nhaversine ranking\ndispatch message, id RQ-<time>", TEAL, fs=6.8)

    panel(ax, 2, 25, 96, 22, "Machine-learning tier (scikit-learn 1.x, loaded once at start-up with joblib)", PALE_ORANGE, ORANGE)
    box(ax, 15, 33, 20, 9, "StandardScaler\n11 features", ORANGE, fs=7.2)
    box(ax, 38, 33, 22, 9, "Accident detector\nRandomForest, 200 trees,\ndepth 10, balanced", ORANGE, fs=7.0)
    box(ax, 62, 33, 22, 9, "Severity predictor\nRandomForest, 250 trees,\ndepth 12, balanced", ORANGE, fs=7.0)
    box(ax, 85, 33, 22, 9, "Rule fallback\nacc_magnitude < 15 / 28 / 45\n(only if models missing)", GREY, fs=6.8)

    panel(ax, 2, 1.5, 96, 21, "Data tier - no database: two JSON files and four pickles; outside services in grey", LIGHT, "#B7C3D3")
    store(ax, 14, 9, 22, 9.5, "data/users.json\naccounts, password\nhashes", fs=6.8)
    store(ax, 37, 9, 22, 9.5, "data/hospitals.json\n10 Hyderabad hospitals\n+ default location", fs=6.6)
    store(ax, 60, 9, 22, 9.5, "models/*.pkl\ndetector, severity,\nscaler, feature names", fs=6.7)
    box(ax, 84, 9, 24, 9.5, "OpenStreetMap tiles\nbrowser Geolocation API\n(external, client side)", WHITE, tc=INK, ec=GREY, fs=6.8)

    arrow(ax, (50, 71), (50, 69.2), "HTTP + JSON, Bearer token", lo=(20, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 49), (50, 47.2), "Python calls", lo=(9, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 25), (50, 22.5), "load / read", lo=(7, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


# ---------------------------------------------------------------------------------------------- 02
def high_level_workflow():
    fig, ax = canvas(10, 6.4, 100, 64)
    ax.text(50, 61.2, "One event, end to end: sensor reading to dispatched alert", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    top = [("Sensor reading", "accel, gyro, speed,\njerk (simulated by\n/api/simulate)", BLUE), ("Feature vector", "11 features,\nmagnitudes derived", BLUE), ("Detect", "RandomForest:\naccident or not,\nprobability", TEAL),
           ("Grade severity", "None / Minor /\nModerate / Severe", TEAL), ("Moderate or\nSevere?", "minor and normal\nevents are only logged", ORANGE)]
    xs = [10 + i * 20 for i in range(5)]
    for x, (t, d, c) in zip(xs, top):
        box(ax, x, 46, 17, 14.5, f"{t}\n{d}", c, fs=7.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.7, 46), (b - 8.7, 46), color=NAVY)
    bot = [("Confirm", "15 s countdown;\ncancel button or\nEscape = false alarm", ORANGE), ("Locate", "browser GPS (3 s),\nelse default area", PURPLE), ("Find hospitals", "haversine rank over\n10-entry directory", PURPLE),
           ("Compose alert", "severity, confidence,\nmap link, nearest\nhospital + phone", PURPLE), ("Show", "dispatch dialog,\nmap, 108 / 112\ntap-to-call", PURPLE)]
    for x, (t, d, c) in zip(xs, bot):
        box(ax, x, 18, 17, 14.5, f"{t}\n{d}", c, fs=7.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.7, 18), (b - 8.7, 18), color=NAVY)
    ax.plot([xs[-1], xs[-1]], [38.7, 33], color=NAVY, lw=1.5)
    ax.plot([xs[-1], xs[0]], [33, 33], color=NAVY, lw=1.5)
    arrow(ax, (xs[0], 33), (xs[0], 25.5), color=NAVY)
    ax.text(50, 35.2, "yes: live monitoring pauses and the confirmation dialog opens", ha="center", fontsize=7.4, color=INK)
    ax.text(50, 4.0, "No SMS, call or e-mail is sent in this build: the alert is composed and displayed (demo).  A cancel is logged as 'user confirmed they are OK'.",
            ha="center", fontsize=7.2, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


# ---------------------------------------------------------------------------------------------- 03
def dfd0():
    fig, ax = canvas(9, 5.6, 100, 62)
    circle(ax, 50, 31, 13, "0\nResQAI\nconsole + API", BLUE, fs=9.5)
    box(ax, 11, 31, 18, 10, "Vehicle occupant\n(signed-in user)", WHITE, tc=INK, ec=NAVY, fs=9, bold=True)
    box(ax, 90, 48, 18, 10, "Browser\nGeolocation API", WHITE, tc=INK, ec=NAVY, fs=9, bold=True)
    box(ax, 90, 14, 18, 10, "OpenStreetMap\ntile server", WHITE, tc=INK, ec=NAVY, fs=9, bold=True)
    arrow(ax, (20, 36), (38.5, 35), "registration, credentials,\nscenario choice, manual\nvalues, cancel / send", lo=(-1, 7.5), fs=7.6)
    arrow(ax, (38.5, 27), (20, 26), "detection result, countdown,\ndispatch message, hospitals,\nmap, event log", lo=(-1, -7.5), fs=7.6)
    arrow(ax, (81, 46), (60, 38), "device latitude, longitude", lo=(-4, 5.5), fs=7.6)
    arrow(ax, (60, 24), (81, 16), "tile requests", lo=(-3, -5.5), fs=7.6)
    ax.text(50, 6.0, "sensor readings are generated inside the system (no phone attached); the dispatch message is displayed, not transmitted;\naccounts and the hospital directory are local JSON files",
            ha="center", fontsize=7.4, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


# ---------------------------------------------------------------------------------------------- 04
def dfd1():
    fig, ax = canvas(10, 8.6, 100, 86)
    R = 7.6
    ax.text(50, 83.6, "Authentication (1.0) guards the API only when REQUIRE_AUTH=1; the React console is always behind the login screen", ha="center", fontsize=7.0, color=GREY, style="italic")
    box(ax, 9, 44, 14, 10, "Occupant", WHITE, tc=INK, ec=NAVY, fs=9.5, bold=True)
    circle(ax, 36, 70, R, "2.0\nAcquire\nreading", BLUE, fs=7.4)
    circle(ax, 64, 70, R, "3.0\nDetect and\ngrade", BLUE, fs=7.4)
    circle(ax, 64, 44, R, "4.0\nConfirm\nalert", BLUE, fs=7.4)
    circle(ax, 64, 18, R, "5.0\nLocate and\nrank hospitals", BLUE, fs=6.6)
    circle(ax, 36, 18, R, "6.0\nCompose\ndispatch", BLUE, fs=7.2)
    circle(ax, 36, 44, R, "1.0\nAuthenticate\nuser", BLUE, fs=6.8)
    store(ax, 14, 18, 20, 5.4, "D1  users.json", fs=7.4)
    store(ax, 90, 18, 18, 7.0, "D2  hospitals\n.json", fs=7.0)
    store(ax, 90, 62, 18, 7.0, "D3  model\npickles", fs=7.2)
    route(ax, [(14, 49), (30, 66)], "scenario /\nmanual values", (17.5, 61))
    route(ax, [(43.6, 70), (56.4, 70)], "11-feature\nreading", (50, 74))
    route(ax, [(82, 62), (70, 66)], "scaler + 2 forests", (79.5, 66.6))
    route(ax, [(64, 62.4), (64, 51.6)], "accident, severity,\nprobability", (73.5, 57), color=BLUE)
    route(ax, [(64, 36.4), (64, 25.6)], "confirmed\n(timeout or send)", (74, 31))
    route(ax, [(56.4, 18), (43.6, 18)], "location,\nnearest 3", (50, 22))
    route(ax, [(82, 18), (71.6, 18)], "10 hospitals", (79, 21.5), color=GREY)
    route(ax, [(36, 10.4), (36, 4), (4, 4), (4, 39)], "dispatch message, alert id, map, 108 / 112", (20, 6.4), color=BLUE)
    route(ax, [(56.4, 44), (43.6, 44)], None, None, ls="--")
    ax.text(50, 47.2, "valid session", fontsize=6.6, ha="center")
    route(ax, [(16, 43), (28.4, 43)], "credentials", (22, 40), color=NAVY)
    route(ax, [(28.4, 46), (16, 46)], "token", (22, 48.6), color=BLUE)
    route(ax, [(30, 37), (22, 21)], None, None)
    route(ax, [(20, 22), (28, 38)], None, None, color=BLUE)
    ax.text(18.5, 30.5, "user rows", fontsize=6.6, ha="center", rotation=60)
    route(ax, [(64, 77.6), (64, 80), (16, 80), (16, 49)], None, None, color=BLUE)
    ax.text(40, 81.8, "detection result, severity, probability shown to the occupant (live monitor)", fontsize=6.8, ha="center")
    save(fig, OUT / "04_dfd_level1.png")


# ---------------------------------------------------------------------------------------------- 05
def dfd2():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.text(50, 71.4, "Level 2 of process 3.0 (app.build_feature_vector + app.predict_from_features)", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    box(ax, 8, 44, 12, 9, "2.0\nreading", WHITE, tc=INK, ec=NAVY, fs=8.5, bold=True)
    circle(ax, 25, 44, 6.6, "3.1\nBuild feature\nvector", BLUE, fs=6.4)
    circle(ax, 43, 44, 6.6, "3.2\nScale", BLUE, fs=7.2)
    circle(ax, 62, 57, 6.6, "3.3\nDetect", BLUE, fs=7.2)
    circle(ax, 62, 31, 6.6, "3.4\nGrade\nseverity", BLUE, fs=6.8)
    circle(ax, 80, 44, 6.6, "3.5\nGate and\nrespond", BLUE, fs=6.6)
    circle(ax, 25, 18, 6.2, "3.6\nRule\nfallback", GREY, fs=6.6)
    store(ax, 43, 66, 30, 6, "D3  model pickles (scaler, detector, severity)", fs=6.4)
    box(ax, 92, 18, 14, 9, "4.0 Confirm\nalert", WHITE, tc=INK, ec=NAVY, fs=8, bold=True)
    route(ax, [(14, 44), (18.4, 44)], None, None)
    route(ax, [(31.6, 44), (36.4, 44)], "11 floats", (34, 48))
    route(ax, [(48, 48.5), (56.5, 53.5)], "scaled vector", (55, 50.5))
    route(ax, [(48, 39.5), (56.5, 34.5)], "scaled vector", (55, 37))
    route(ax, [(68, 53.5), (75, 48.5)], "accident flag,\nprobability", (76, 56.5), color=BLUE)
    route(ax, [(68, 34.5), (75, 39.5)], "severity 0-3", (76, 33), color=BLUE)
    route(ax, [(84, 39.5), (90, 22.5)], "JSON response", (92, 31), color=BLUE)
    route(ax, [(43, 63), (43, 50.6)], "scaler", (46.5, 58), ls="--")
    route(ax, [(52, 64), (57.5, 61)], "forests", (58, 66.5), ls="--")
    route(ax, [(25, 37.4), (25, 24.2)], "models\nmissing?", (31, 31), ls="--")
    route(ax, [(31.2, 18), (78, 18), (78, 37.4)], "acc_magnitude -> 0 / 1 / 2 / 3", (52, 21.2), ls="--")
    ax.text(50, 8, "Gate (3.5): if the detector says 'no accident' the severity is forced to 0 (None), whatever the severity forest says.\n"
                   "Model output of the fallback has confidence 0.05 / 0.6 / 0.8 / 0.95 and model_source = 'rule_based_fallback'.", ha="center", fontsize=7.0, color=ORANGE)
    save(fig, OUT / "05_dfd_level2.png")


# ---------------------------------------------------------------------------------------------- 06
def uml_class_diagram():
    fig, ax = canvas(11, 8.6, 110, 86)
    ax.text(55, 83.5, "Design-level class diagram (the backend is module-and-function based; classes are the scikit-learn and React objects the code uses)", ha="center", fontsize=8.0, color=NAVY, fontweight="bold")
    uml_class(ax, 2, 80, 28, "User (users.json)", ["id: hex str", "name: str(2-60)", "email: str (unique)", "password_hash: str", "created: ISO time"], ["_public(user)", "_issue_token(user)"], hdr=BLUE, fs=6.6)
    uml_class(ax, 2, 55, 28, "AuthService (auth.py)", ["TOKEN_MAX_AGE = 12 h", "MAX_FAILED_LOGINS = 5", "LOCKOUT_SECONDS = 300"], ["register()", "login()", "me()", "user_from_request()", "init_app(app) # guard"], hdr=BLUE, fs=6.6)
    uml_class(ax, 40, 80, 30, "SensorReading", ["acc_x, acc_y, acc_z: float", "gyro_x, gyro_y, gyro_z: float", "acc_magnitude: float", "gyro_magnitude: float", "speed_before, speed_change", "jerk: float (abs)"], ["build_feature_vector()", "simulate(scenario)"], hdr=TEAL, fs=6.5)
    uml_class(ax, 40, 51, 30, "Prediction (response)", ["timestamp: ISO-8601 Z", "accident_detected: bool", "severity_level: 0..3", "severity_label: str", "confidence: float", "features_used: dict", "model_source: str"], [], hdr=TEAL, fs=6.5)
    uml_class(ax, 78, 80, 30, "RandomForestClassifier", ["n_estimators: 200 | 250", "max_depth: 10 | 12", "class_weight = 'balanced'", "random_state = 42"], ["fit(X, y)", "predict(X)", "predict_proba(X)"], hdr=ORANGE, fs=6.5, stereotype="detector / severity")
    uml_class(ax, 78, 52, 30, "StandardScaler", ["mean_, scale_  (11)"], ["fit(X)", "transform(X)"], hdr=ORANGE, fs=6.5)
    uml_class(ax, 40, 22, 30, "HospitalDirectory", ["hospitals: 10 x {name, lat,", "   lon, phone, emergency}", "default_location"], ["haversine_km(a, b)", "nearest_hospitals(lat, lon, k)"], hdr=PURPLE, fs=6.5)
    uml_class(ax, 78, 34, 30, "EmergencyAlert (response)", ["status = 'dispatched'", "alert_id: 'RQ-<unix s>'", "location: {lat, lon}", "nearest_hospitals: list(3)", "message: str", "ambulance 108, national 112"], [], hdr=PURPLE, fs=6.5)
    uml_class(ax, 2, 29, 34, "MonitorProvider (React)", ["history[40], events[25]", "result, pending, countdown", "live: bool, dispatch", "COUNTDOWN_SECONDS = 15", "LIVE_INTERVAL_MS = 1500"], ["runReading(reading)", "runScenario(name)", "sendAlert()", "cancelAlert()"], hdr=NAVY, fs=6.5)
    arrow(ax, (16, 55), (16, 59.5), "reads / writes", lo=(7, 0), fs=6.4, color=GREY)
    arrow(ax, (55, 57), (55, 51), "1 produces 1", lo=(7, 0), fs=6.4, color=GREY)
    arrow(ax, (70, 68), (78, 51), "scaled by", lo=(0, 1.5), fs=6.4, color=GREY)
    arrow(ax, (93, 52), (93, 58), "scaled X", lo=(6, 0), fs=6.4, color=GREY)
    arrow(ax, (70, 38), (78, 28), "Moderate/Severe,\nconfirmed", lo=(-1, 4.5), fs=6.2, color=GREY, ls="--")
    arrow(ax, (70, 14), (78, 24), "nearest 3", lo=(1, -3), fs=6.4, color=GREY)
    arrow(ax, (36, 26), (43, 29.5), "api.predict", lo=(-3, 3), fs=6.4, color=GREY, ls="--")
    arrow(ax, (36, 14), (40, 14), "/api/emergency", lo=(-1, 3), fs=6.4, color=GREY, ls="--")
    ax.text(39, 2.6, "Associations: SensorReading -> Prediction (one predict call); Prediction (Moderate/Severe) -> EmergencyAlert\n(after confirmation); detector and severity are two instances of the same class. SensorReading, Prediction and\nEmergencyAlert are transient: JSON in requests and React state, never stored rows.",
            ha="left", va="center", fontsize=6.0, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


# ---------------------------------------------------------------------------------------------- 07
def sequence():
    fig, ax = canvas(11, 9.4, 110, 94)
    ax.text(55, 91.4, "Sequence of the main flow: scenario -> detection -> confirmation -> dispatch", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    actors = [("Occupant", 9), ("React app\n(MonitorContext)", 30), ("Flask API\n(app.py)", 55), ("RF models\n+ scaler", 78), ("Hospital\ndirectory", 98)]
    for n, x in actors:
        box(ax, x, 85, 17, 6.5, n, NAVY, fs=7.6)
        ax.plot([x, x], [81.5, 4], color="#B7C3D3", lw=1.2, ls="--", zorder=1)
    X = dict((n.split("\n")[0], x) for n, x in actors)
    ox, rx, fx, mx, hx = 9, 30, 55, 78, 98
    ys = iter([77, 71, 65, 59, 53, 47, 41, 35, 29, 23, 17, 11, 6.5])

    def msg(a, b, text, y, dashed=False, color=NAVY):
        arrow(ax, (a, y), (b, y), None, color=color, lw=1.4, ls="--" if dashed else "-")
        ax.text((a + b) / 2, y + 1.6, text, ha="center", fontsize=6.6, color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9), zorder=6)

    msg(ox, rx, "click 'Severe crash'", 77)
    msg(rx, fx, "GET /api/simulate?scenario=severe", 71)
    msg(fx, rx, "11-feature reading (JSON)", 66.5, True)
    msg(rx, fx, "POST /api/predict (reading)", 61)
    msg(fx, mx, "scale, detector.predict_proba, severity.predict", 56)
    msg(mx, fx, "accident=1, P, severity=3", 51.5, True)
    msg(fx, rx, "accident_detected, 'Severe', confidence", 47, True)
    ax.add_patch(Rectangle((3, 28), 94, 16.5, fc="#FFF6EC", ec=ORANGE, lw=1.1, zorder=0))
    ax.text(4, 43.2, "alt: Moderate or Severe  ->  15 s confirmation dialog (live monitoring pauses)", fontsize=6.8, color=ORANGE, fontweight="bold", va="center")
    msg(rx, ox, "dialog + countdown 15, 14, ...", 39.5, True)
    msg(ox, rx, "[A] 'I'm fine, cancel' or Esc: alert cancelled, logged", 35)
    ax.text(4, 30.6, "[B] no answer in 15 s, or 'Send alert now' pressed; the browser Geolocation (3 s timeout) is read, then:", fontsize=6.8, color=ORANGE, va="center")
    msg(rx, fx, "POST /api/emergency (severity, confidence, GPS or none)", 25.5)
    msg(fx, hx, "nearest_hospitals(lat, lon, 3)", 21)
    msg(hx, fx, "3 hospitals + distances", 16.5, True)
    msg(fx, rx, "dispatched: id RQ-..., message, hospitals, 112 / 108", 12, True)
    msg(rx, ox, "dispatch dialog, map with markers, event log entry", 7.5, True)
    save(fig, OUT / "07_sequence_main_flow.png")


# ---------------------------------------------------------------------------------------------- 08
def use_case():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.text(50, 73.4, "Use cases of ResQAI", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.add_patch(Rectangle((22, 4), 56, 66, fc="#F7FAFD", ec=NAVY, lw=1.4, zorder=1))
    ax.text(50, 67.4, "ResQAI console and API", ha="center", fontsize=8.6, color=NAVY, fontweight="bold")
    cases = [("Register / sign in", 62), ("Run a crash scenario", 54.5), ("Live monitoring (1.5 s)", 47), ("Enter manual sensor values", 39.5),
             ("Confirm or cancel the alert (15 s)", 32), ("View response map and hospitals", 24.5), ("Call 108 / 112 / 103", 17), ("Switch theme, read event log", 9.5)]
    for t, y in cases:
        ellipse(ax, 50, y, 40, 5.6, t, fs=7.4)
    for ex, ey, t in [(8, 40, "Vehicle occupant\n(driver / rider)")]:
        ax.add_patch(Circle((ex, ey + 8), 2.4, fc=WHITE, ec=NAVY, lw=1.5, zorder=3))
        ax.plot([ex, ex], [ey + 5.6, ey - 1], color=NAVY, lw=1.5)
        ax.plot([ex - 4, ex + 4], [ey + 3, ey + 3], color=NAVY, lw=1.5)
        ax.plot([ex, ex - 3.5], [ey - 1, ey - 7], color=NAVY, lw=1.5)
        ax.plot([ex, ex + 3.5], [ey - 1, ey - 7], color=NAVY, lw=1.5)
        ax.text(ex, ey - 11, t, ha="center", fontsize=7.6, color=INK)
    for ex, ey, t in [(92, 55, "Developer /\nadministrator"), (92, 20, "External services\n(OSM tiles, GPS)")]:
        ax.add_patch(Circle((ex, ey + 8), 2.4, fc=WHITE, ec=GREY, lw=1.5, zorder=3))
        ax.plot([ex, ex], [ey + 5.6, ey - 1], color=GREY, lw=1.5)
        ax.plot([ex - 4, ex + 4], [ey + 3, ey + 3], color=GREY, lw=1.5)
        ax.plot([ex, ex - 3.5], [ey - 1, ey - 7], color=GREY, lw=1.5)
        ax.plot([ex, ex + 3.5], [ey - 1, ey - 7], color=GREY, lw=1.5)
        ax.text(ex, ey - 11, t, ha="center", fontsize=7.2, color=INK)
    for t, y in cases:
        ax.plot([12, 30], [44, y], color=GREY, lw=0.8, zorder=2)
    ellipse(ax, 50, 1.2, 1, 1, "", fc="white", ec="white")
    ax.plot([88, 70], [60, 62], color=GREY, lw=0.8, ls="--")
    ax.text(86, 70.5, "retrain models, set REQUIRE_AUTH,\nrun the test scripts", fontsize=6.6, ha="center", color=GREY)
    ax.plot([88, 70], [27, 22], color=GREY, lw=0.8, ls="--")
    ax.text(24, 5.4, "'Run a crash scenario' includes the severe, moderate, minor, harsh-brake and normal buttons;\nthe Moderate / Severe results trigger 'Confirm or cancel'.", fontsize=6.4, color=GREY, ha="left", va="center", style="italic")
    save(fig, OUT / "08_use_case.png")


# ---------------------------------------------------------------------------------------------- 09
def er_diagram():
    fig, ax = canvas(10, 7.6, 100, 76)
    ax.text(50, 73.4, "Entities: two persisted (solid) and three transient (dashed)", ha="center", fontsize=10, color=NAVY, fontweight="bold")

    def entity(x, ytop, w, title, rows, fc=NAVY, fs=6.6, lh=2.75, dashed=False):
        h = 4.4 + lh * len(rows) + 1.0
        ax.add_patch(Rectangle((x, ytop - h), w, h, fc=WHITE, ec=NAVY, lw=1.4, zorder=2, ls="--" if dashed else "-"))
        ax.add_patch(Rectangle((x, ytop - 4.4), w, 4.4, fc=fc, ec=NAVY, lw=1.4, zorder=3, ls="--" if dashed else "-"))
        ax.text(x + w / 2, ytop - 2.2, title, ha="center", va="center", color=WHITE, fontsize=8.6, fontweight="bold", zorder=4)
        for i, r in enumerate(rows):
            ax.text(x + 1.0, ytop - 4.4 - 1.9 - lh * i, r, ha="left", va="center", fontsize=fs, zorder=4, family="DejaVu Sans Mono")
        return h

    entity(3, 68, 30, "users (users.json)", ["PK email   str (lowercase)", "   id      hex(16)", "   name    str 2-60", "   password_hash scrypt", "   created ISO time"], BLUE)
    entity(70, 68, 28, "hospitals (hospitals.json)", ["PK name    str", "   lat, lon float", "   phone    str", "   emergency bool"], PURPLE)
    entity(36, 68, 30, "ModelArtifacts (pkl)", ["accident_detector.pkl", "severity_predictor.pkl", "feature_scaler.pkl", "feature_names.pkl"], ORANGE)
    entity(3, 40, 30, "SensorReading", ["acc_x, acc_y, acc_z", "gyro_x, gyro_y, gyro_z", "acc_magnitude", "gyro_magnitude", "speed_before", "speed_change, jerk"], TEAL, dashed=True)
    entity(36, 40, 30, "Prediction", ["timestamp", "accident_detected", "severity_level 0-3", "severity_label", "confidence", "model_source"], TEAL, dashed=True)
    entity(70, 40, 28, "EmergencyAlert", ["PK alert_id RQ-<unix s>", "lat, lon", "severity_label", "confidence", "message", "nearest_hospitals[3]"], TEAL, dashed=True)
    route(ax, [(33, 30), (36, 30)], None, None, color=ORANGE)
    ax.text(34.5, 32.3, "1 : 1", fontsize=7, ha="center", color=ORANGE)
    route(ax, [(66, 30), (70, 30)], None, None, color=ORANGE)
    ax.text(68, 32.3, "0..1", fontsize=7, ha="center", color=ORANGE)
    route(ax, [(51, 40), (51, 56)], None, None, color=GREY, ls="--")
    ax.text(52.5, 48, "scored by", fontsize=6.6, ha="left", color=GREY)
    route(ax, [(84, 40), (84, 56)], None, None, color=GREY, ls="--")
    ax.text(85.5, 48, "ranks nearest 3 of", fontsize=6.6, ha="left", color=GREY)
    ax.text(50, 11, "No relational database: users.json (email-keyed) and hospitals.json are the only stored records. SensorReading, Prediction and EmergencyAlert live as JSON in requests\nand as React state (history of 40 points, event log of 25), and are lost on reload; alerts are not stored on the server.\nThe association users - alerts is not recorded: an alert carries no user id.",
            ha="center", fontsize=7.0, color=GREY, style="italic")
    save(fig, OUT / "09_er_diagram.png")


# ---------------------------------------------------------------------------------------------- 10
def flowchart_core():
    fig, ax = canvas(10, 11.9, 100, 119)
    ax.set_ylim(-6, 113)
    ax.text(50, 111, "Core algorithm: predict_from_features, then the confirmation and dispatch rule", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    cx = 34
    box(ax, cx, 103, 40, 6, "POST /api/predict  (JSON sensor payload)", BLUE, fs=7.8)
    box(ax, cx, 93, 40, 7, "build_feature_vector: defaults (acc_z = 9.81),\nacc_magnitude, gyro_magnitude, jerk = |jerk|", TEAL, fs=7.0)
    arrow(ax, (cx, 100), (cx, 96.6), color=NAVY)
    diamond(ax, cx, 80, 36, 11, "models loaded?", fs=8)
    arrow(ax, (cx, 89.4), (cx, 85.6), color=NAVY)
    box(ax, 80, 80, 30, 9, "rule_based_fallback\nacc_magnitude < 15 / 28 / 45\n-> None / Minor / Moderate / Severe", GREY, fs=6.6)
    arrow(ax, (cx + 18, 80), (65, 80), "no", lo=(0, 1.8), fs=8, color=NAVY)
    box(ax, cx, 66, 36, 6.5, "scaler.transform(X)", ORANGE, fs=7.6)
    arrow(ax, (cx, 74.4), (cx, 69.3), "yes", lo=(2.8, 0), fs=8, color=NAVY)
    box(ax, cx, 55, 40, 8, "accident = detector.predict(X)\nconfidence = detector.predict_proba(X)[1]", ORANGE, fs=7.2)
    arrow(ax, (cx, 62.7), (cx, 59), color=NAVY)
    box(ax, cx, 44, 40, 6.5, "severity = severity_model.predict(X)", ORANGE, fs=7.4)
    arrow(ax, (cx, 51), (cx, 47.3), color=NAVY)
    diamond(ax, cx, 31, 36, 11, "accident == 0 ?", fs=8)
    arrow(ax, (cx, 40.7), (cx, 36.6), color=NAVY)
    box(ax, 80, 31, 30, 6.5, "severity = 0 (None)", PALE_TEAL, tc=INK, ec=TEAL, fs=7.4)
    arrow(ax, (cx + 18, 31), (65, 31), "yes", lo=(0, 1.8), fs=8, color=NAVY)
    box(ax, cx, 17, 42, 7, "return accident_detected, severity_label,\nconfidence, features_used, model_source", BLUE, fs=7.0)
    arrow(ax, (cx, 25.4), (cx, 20.6), "no", lo=(2.8, 0), fs=8, color=NAVY)
    ax.plot([80, 80], [27.7, 17], color=NAVY, lw=1.5)
    ax.plot([88, 60], [17, 17], color=NAVY, lw=1.5)
    arrow(ax, (60, 17), (55, 17), color=NAVY)
    ax.plot([80, 80], [75.5, 73], color=NAVY, lw=1.5)
    ax.plot([80, 88], [73, 73], color=NAVY, lw=1.5)
    ax.plot([88, 88], [73, 17], color=NAVY, lw=1.5)
    diamond(ax, cx, 4.5, 40, 8, "severity is Moderate or Severe ?  (client)", fs=6.2)
    arrow(ax, (cx, 13.4), (cx, 8.5), color=NAVY)
    ax.text(70, 5.2, "yes: 15 s countdown, then POST /api/emergency\nno: logged in the event log only", fontsize=6.8, color=INK, ha="left", va="center")
    save(fig, OUT / "10_flowchart_core_algorithm.png")


# ---------------------------------------------------------------------------------------------- 11
def training_pipeline():
    fig, ax = canvas(10, 5.4, 100, 54)
    ax.text(50, 51.4, "Offline pipeline: train_models.py (run once; the .pkl files are shipped)", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    steps = [("Generate", "12,000 events, seed 42\n60/20/10/6/4 % normal,\nbrake, minor, moderate,\nsevere", BLUE), ("Split", "80 / 20, stratified on\naccident\n9,600 train, 2,400 test", TEAL),
             ("Scale", "StandardScaler fitted\non the training part", TEAL), ("Train", "detector: RF 200 trees,\ndepth 10; severity: RF\n250, depth 12, balanced", ORANGE),
             ("Evaluate", "accuracy and\nclassification_report\non the 2,400 test events", ORANGE), ("Save", "joblib.dump: 4 files\nin models/", PURPLE)]
    xs = [9 + i * 16.4 for i in range(6)]
    for x, (t, d, c) in zip(xs, steps):
        box(ax, x, 27, 14.5, 18, f"{t}\n{d}", c, fs=6.6)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.4, 27), (b - 7.4, 27), color=NAVY)
    ax.text(50, 7.5, "Both models see the same scaled 11 features; the severity model is trained on all events with None as class 0.\nNo validation split and no cross-validation in the shipped script; this report adds a five-seed repeat (scripts/measure_metrics.py).",
            ha="center", fontsize=7.2, color=GREY, style="italic")
    save(fig, OUT / "11_training_pipeline.png")


if __name__ == "__main__":
    system_architecture()
    high_level_workflow()
    dfd0()
    dfd1()
    dfd2()
    uml_class_diagram()
    sequence()
    use_case()
    er_diagram()
    flowchart_core()
    training_pipeline()
