"""AgriVision — AI Plant Disease Detection Platform (Flask MVP per PRD v1.0)."""
from __future__ import annotations
import csv, io, json, os, sqlite3, uuid, time
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, request, jsonify, render_template, redirect, url_for,
                   session, g, send_file, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import config
from disease_db import CLASSES, display_name, get_disease_info
from inference import predict

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
os.makedirs(config.UPLOAD_DIR, exist_ok=True)

# ---------------- DB ----------------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(config.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_e=None):
    d = g.pop("db", None)
    if d is not None:
        d.close()

def init_db():
    d = sqlite3.connect(config.DB_PATH)
    d.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, phone TEXT,
      full_name TEXT, password_hash TEXT NOT NULL, role TEXT DEFAULT 'farmer',
      region TEXT DEFAULT '', language TEXT DEFAULT 'en',
      crops TEXT DEFAULT '[]', created_at TEXT, is_active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS results(
      id TEXT PRIMARY KEY, user_id TEXT NOT NULL, image_path TEXT,
      image_size INTEGER, predicted TEXT, confidence REAL, top3 TEXT,
      severity TEXT, crop_hint TEXT, latency_ms INTEGER, created_at TEXT,
      bookmarked INTEGER DEFAULT 0,
      FOREIGN KEY(user_id) REFERENCES users(id));
    """)
    # seed demo user
    if not d.execute("SELECT 1 FROM users WHERE email=?", ("demo@agrivision.ai",)).fetchone():
        d.execute("INSERT INTO users(id,email,phone,full_name,password_hash,role,region,language,crops,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), "demo@agrivision.ai", "+919876543210", "Demo Farmer",
             generate_password_hash("demo1234"), "farmer", "Maharashtra", "en",
             json.dumps(["tomato", "potato"]), datetime.utcnow().isoformat()))
    d.commit(); d.close()

init_db()

def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    row = db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None

def login_required(fn):
    @wraps(fn)
    def w(*a, **kw):
        if not current_user():
            if request.path.startswith("/api/"):
                return jsonify({"error": "AUTHENTICATION_REQUIRED", "message": "Please login to continue"}), 401
            return redirect(url_for("login", next=request.path))
        return fn(*a, **kw)
    return w

@app.context_processor
def inject():
    return {"user": current_user(), "now": datetime.utcnow()}

# ---------------- Pages ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        row = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if row and check_password_hash(row["password_hash"], pw):
            session["uid"] = row["id"]
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email or not request.form.get("password"):
            flash("Email and password are required.", "error")
            return render_template("register.html")
        try:
            db().execute("INSERT INTO users(id,email,phone,full_name,password_hash,role,region,language,crops,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), email, request.form.get("phone", ""),
                 request.form.get("full_name", ""), generate_password_hash(request.form["password"]),
                 request.form.get("role", "farmer"), request.form.get("region", ""),
                 request.form.get("language", "en"), json.dumps([request.form.get("crop", "tomato")]),
                 datetime.utcnow().isoformat()))
            db().commit()
            flash("Account created — please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    u = current_user()
    rows = db().execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC LIMIT 6", (u["id"],)).fetchall()
    total = db().execute("SELECT COUNT(*) c FROM results WHERE user_id=?", (u["id"],)).fetchone()["c"]
    healthy = db().execute("SELECT COUNT(*) c FROM results WHERE user_id=? AND severity='none'", (u["id"],)).fetchone()["c"]
    urgent = db().execute("SELECT COUNT(*) c FROM results WHERE user_id=? AND severity='high'", (u["id"],)).fetchone()["c"]
    recent = [dict(r) | {"info": get_disease_info(r["predicted"])} for r in rows]
    return render_template("dashboard.html", recent=recent, total=total, healthy=healthy, urgent=urgent)

@app.route("/detect", methods=["GET", "POST"])
@login_required
def detect():
    if request.method == "POST":
        f = request.files.get("image")
        crop_hint = request.form.get("crop_type", "general")
        if not f or not f.filename:
            flash("Please choose a leaf image.", "error")
            return render_template("detect.html")
        ext = f.filename.rsplit(".", 1)[-1].lower()
        if ext not in config.ALLOWED_EXT:
            flash("Image must be JPG, PNG, JPEG or WEBP (max 10 MB).", "error")
            return render_template("detect.html", crop=crop_hint)
        data = f.read()
        out = predict(data, crop_hint)
        info = get_disease_info(out["predicted"])
        # save image
        name = f"{uuid.uuid4().hex}.{ext if ext != 'webp' else 'png'}"
        path = os.path.join(config.UPLOAD_DIR, name)
        with open(path, "wb") as fh:
            fh.write(data)
        rid = str(uuid.uuid4())
        db().execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, current_user()["id"], f"static/uploads/{name}", len(data),
             out["predicted"], out["confidence"], json.dumps(out["top3"]),
             info["severity"], crop_hint, out["latency_ms"],
             datetime.utcnow().isoformat(), 0))
        db().commit()
        return redirect(url_for("result", rid=rid))
    return render_template("detect.html", crop=request.args.get("crop", "tomato"))

@app.route("/result/<rid>")
@login_required
def result(rid):
    r = db().execute("SELECT * FROM results WHERE id=? AND user_id=?", (rid, current_user()["id"])).fetchone()
    if not r:
        flash("Result not found.", "error")
        return redirect(url_for("history"))
    r = dict(r)
    r["top3"] = json.loads(r["top3"])
    r["info"] = get_disease_info(r["predicted"])
    r["peers"] = [(c, p, get_disease_info(c)) for c, p in r["top3"][1:]]
    return render_template("result.html", r=r)

@app.route("/history")
@login_required
def history():
    u = current_user()
    q, crop, dis = request.args.get("q", ""), request.args.get("crop", ""), request.args.get("disease", "")
    rows = db().execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC LIMIT 200", (u["id"],)).fetchall()
    items = []
    for r in rows:
        r = dict(r)
        info = get_disease_info(r["predicted"])
        r["info"] = info
        if q and q.lower() not in (info["name"] + info["crop"]).lower():
            continue
        if crop and crop.lower() not in info["crop"].lower() and crop.lower() not in (r["crop_hint"] or "").lower():
            continue
        if dis == "healthy" and not info["healthy"]:
            continue
        if dis == "diseased" and info["healthy"]:
            continue
        items.append(r)
    crops = sorted({i["info"]["crop"] for i in items})
    return render_template("history.html", items=items, q=q, crop=crop, disease=dis, crops=crops)

@app.route("/history/<rid>/delete", methods=["POST"])
@login_required
def delete_result(rid):
    r = db().execute("SELECT * FROM results WHERE id=? AND user_id=?", (rid, current_user()["id"])).fetchone()
    if r:
        try:
            os.remove(os.path.join(os.path.dirname(__file__), r["image_path"]))
        except OSError:
            pass
        db().execute("DELETE FROM results WHERE id=?", (rid,))
        db().commit()
        flash("Record deleted.", "success")
    return redirect(url_for("history"))

@app.route("/history/<rid>/export")
@login_required
def export_one(rid):
    fmt = request.args.get("format", "csv")
    r = db().execute("SELECT * FROM results WHERE id=? AND user_id=?", (rid, current_user()["id"])).fetchone()
    if not r:
        return "Not found", 404
    info = get_disease_info(r["predicted"])
    if fmt == "pdf":
        return export_pdf([dict(r)], info)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["result_id", "date", "crop_hint", "predicted", "confidence", "severity", "latency_ms"])
    w.writerow([r["id"], r["created_at"], r["crop_hint"], display_name(r["predicted"]), r["confidence"], r["severity"], r["latency_ms"]])
    return send_file(io.BytesIO(buf.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name=f"agrivision-{rid[:8]}.csv")

@app.route("/history/export")
@login_required
def export_all():
    rows = db().execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC", (current_user()["id"],)).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["result_id", "date", "crop_hint", "predicted", "confidence", "severity"])
    for r in rows:
        w.writerow([r["id"], r["created_at"], r["crop_hint"], display_name(r["predicted"]), r["confidence"], r["severity"]])
    return send_file(io.BytesIO(buf.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name="agrivision-history.csv")

def export_pdf(rows, info=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return "PDF export needs `pip install reportlab`.", 500
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    y = H - 60
    c.setFont("Helvetica-Bold", 18); c.drawString(50, y, "AgriVision — Disease Report"); y -= 24
    c.setFont("Helvetica", 10); c.drawString(50, y, f"Generated {datetime.utcnow():%Y-%m-%d %H:%M UTC}  •  agrivision.ai"); y -= 30
    for r in rows:
        r = dict(r); inf = info or get_disease_info(r["predicted"])
        for line in [f"Result: {r['id']}", f"Date: {r['created_at']}", f"Disease: {inf['name']}",
                     f"Confidence: {r['confidence']*100:.2f}%   Severity: {inf['severity']}",
                     f"Symptoms: {inf['symptoms'][:220]}",
                     f"Treatment: {inf['treatments'][0]['detail'][:220]}",
                     f"Prevention: {inf['prevention'][:220]}"]:
            c.setFont("Helvetica", 10); c.drawString(50, y, line[:110]); y -= 16
            if y < 60:
                c.showPage(); y = H - 60
        y -= 12
    c.save(); buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name="agrivision-report.pdf")

@app.route("/analytics")
@login_required
def analytics():
    rows = db().execute("SELECT predicted, severity, created_at FROM results WHERE user_id=? ORDER BY created_at", (current_user()["id"],)).fetchall()
    dist: dict[str, int] = {}
    sev = {"high": 0, "medium": 0, "low": 0, "none": 0}
    timeline: dict[str, int] = {}
    for r in rows:
        dist[get_disease_info(r["predicted"])["disease"]] = dist.get(get_disease_info(r["predicted"])["disease"], 0) + 1
        sev[r["severity"]] = sev.get(r["severity"], 0) + 1
        day = (r["created_at"] or "")[:10]
        timeline[day] = timeline.get(day, 0) + 1
    return render_template("analytics.html", dist=dist, sev=sev, timeline=timeline, total=len(rows))

@app.route("/encyclopedia")
def encyclopedia():
    q = request.args.get("q", "").lower()
    cards = [get_disease_info(c) for c in CLASSES]
    if q:
        cards = [x for x in cards if q in (x["name"] + x["crop"] + x["symptoms"]).lower()]
    crops = sorted(set(x["crop"] for x in [get_disease_info(c) for c in CLASSES]))
    return render_template("encyclopedia.html", cards=cards, q=q, crops=crops)

@app.route("/disease/<path:name>")
def disease_detail(name):
    cls = next((c for c in CLASSES if display_name(c) == name or c == name), None)
    if not cls:
        return "Disease not found", 404
    return render_template("disease_detail.html", d=get_disease_info(cls))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    u = current_user()
    if request.method == "POST":
        db().execute("UPDATE users SET full_name=?, region=?, language=?, crops=? WHERE id=?",
            (request.form.get("full_name", u["full_name"]), request.form.get("region", u["region"]),
             request.form.get("language", u["language"]), json.dumps(request.form.getlist("crops") or ["tomato"]), u["id"]))
        db().commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", u=u, crops=json.loads(u["crops"] or "[]"))

# ---------------- REST API (PRD §11) ----------------
@app.route("/api/v1/auth/register", methods=["POST"])
def api_register():
    d = request.get_json(force=True, silent=True) or {}
    if not d.get("email") or not d.get("password"):
        return jsonify({"error": "INVALID_REQUEST", "message": "email and password required"}), 400
    try:
        uid = str(uuid.uuid4())
        db().execute("INSERT INTO users(id,email,phone,full_name,password_hash,role,region,language,crops,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (uid, d["email"].lower(), d.get("phone", ""), d.get("full_name", ""),
             generate_password_hash(d["password"]), d.get("role", "farmer"),
             d.get("region", ""), d.get("language", "en"), "[]", datetime.utcnow().isoformat()))
        db().commit()
        return jsonify({"user_id": uid, "email": d["email"], "message": "Verification email sent"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "EMAIL_EXISTS", "message": "Email already registered"}), 409

@app.route("/api/v1/detect/upload", methods=["POST"])
@login_required
def api_detect():
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "NO_IMAGE", "message": "image file required"}), 400
    ext = (f.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in config.ALLOWED_EXT:
        return jsonify({"error": "INVALID_IMAGE_FORMAT", "message": "Image must be JPG, PNG, or JPEG"}), 400
    data = f.read()
    crop_hint = request.form.get("crop_type", "general")
    out = predict(data, crop_hint)
    info = get_disease_info(out["predicted"])
    name = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(config.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)
    rid = str(uuid.uuid4())
    db().execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (rid, current_user()["id"], f"static/uploads/{name}", len(data), out["predicted"],
         out["confidence"], json.dumps(out["top3"]), info["severity"], crop_hint,
         out["latency_ms"], datetime.utcnow().isoformat(), 0))
    db().commit()
    return jsonify({"result_id": rid, "predicted_disease": info["name"], "confidence": out["confidence"],
        "top_3_predictions": [{"disease": display_name(c), "confidence": p} for c, p in out["top3"]],
        "severity": info["severity"], "processing_time_ms": out["latency_ms"],
        "recommendations": {"treatments": info["treatments"], "prevention": info["prevention"],
                            "urgent_action": info["urgent"]}})

@app.route("/api/v1/history")
@login_required
def api_history():
    lim = min(int(request.args.get("limit", 20)), 100)
    off = int(request.args.get("offset", 0))
    total = db().execute("SELECT COUNT(*) c FROM results WHERE user_id=?", (current_user()["id"],)).fetchone()["c"]
    rows = db().execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (current_user()["id"], lim, off)).fetchall()
    return jsonify({"total_count": total, "results": [
        {"result_id": r["id"], "predicted_disease": display_name(r["predicted"]), "confidence": r["confidence"],
         "detection_date": r["created_at"], "crop_type": r["crop_hint"]} for r in rows]})

@app.route("/api/v1/history/<rid>")
@login_required
def api_one(rid):
    r = db().execute("SELECT * FROM results WHERE id=? AND user_id=?", (rid, current_user()["id"])).fetchone()
    if not r:
        return jsonify({"error": "NOT_FOUND"}), 404
    return jsonify({"result_id": r["id"], "predicted_disease": display_name(r["predicted"]),
        "disease_details": get_disease_info(r["predicted"]), "image_url": "/" + r["image_path"],
        "created_at": r["created_at"]})

@app.route("/api/v1/analytics/dashboard")
@login_required
def api_analytics():
    rows = db().execute("SELECT predicted FROM results WHERE user_id=?", (current_user()["id"],)).fetchall()
    dist: dict[str, int] = {}
    for r in rows:
        k = display_name(r["predicted"]); dist[k] = dist.get(k, 0) + 1
    return jsonify({"total_detections": len(rows), "disease_distribution": dist})

@app.route("/api/v1/diseases")
def api_diseases():
    return jsonify([get_disease_info(c) for c in CLASSES])

@app.route("/health")
def health():
    return {"status": "ok", "classes": len(CLASSES)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
