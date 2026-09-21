import os
import json
from collections import defaultdict
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from db import get_db, init_db, now
from utils.text_extraction import extract_text, clean_text, chunk_text, extract_topics, allowed_file
from utils.rag_engine import RAGEngine
from utils.quiz_generator import generate_quiz

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

init_db()

# In-memory RAG index cache, keyed by user_id. Rebuilt whenever a user's
# documents change. Fine for a single-process student-project deployment.
_rag_cache = {}


def get_engine_for_user(user_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT c.text, c.chunk_index, d.id as doc_id, d.filename as doc_name
           FROM chunks c JOIN documents d ON c.document_id = d.id
           WHERE d.user_id = ?""",
        (user_id,),
    ).fetchall()
    conn.close()
    records = [
        {"text": r["text"], "doc_id": r["doc_id"], "doc_name": r["doc_name"], "chunk_index": r["chunk_index"]}
        for r in rows
    ]
    engine = RAGEngine()
    engine.build_index(records)
    _rag_cache[user_id] = engine
    return engine


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------- AUTH ----

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        interests = request.form.get("interests", "").strip()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("register"))

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            flash("Username already taken.", "danger")
            conn.close()
            return redirect(url_for("register"))

        conn.execute(
            "INSERT INTO users (username, password_hash, interests, created_at) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), interests, now()),
        )
        conn.commit()
        conn.close()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))


# ----------------------------------------------------------- DASHBOARD ----

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    user_id = session["user_id"]
    doc_count = conn.execute("SELECT COUNT(*) c FROM documents WHERE user_id=?", (user_id,)).fetchone()["c"]
    query_count = conn.execute("SELECT COUNT(*) c FROM queries WHERE user_id=?", (user_id,)).fetchone()["c"]
    quiz_rows = conn.execute("SELECT * FROM quiz_results WHERE user_id=?", (user_id,)).fetchall()
    documents = conn.execute(
        "SELECT * FROM documents WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 5", (user_id,)
    ).fetchall()
    conn.close()

    subject_scores = defaultdict(lambda: {"correct": 0, "total": 0})
    for row in quiz_rows:
        subject_scores[row["subject"]]["total"] += 1
        subject_scores[row["subject"]]["correct"] += row["correct"]

    performance = [
        {"subject": subj, "accuracy": round(100 * d["correct"] / d["total"], 1) if d["total"] else 0}
        for subj, d in subject_scores.items()
    ]

    return render_template(
        "dashboard.html",
        doc_count=doc_count,
        query_count=query_count,
        quiz_attempts=len(quiz_rows),
        performance=performance,
        documents=documents,
    )


@app.route("/api/performance")
@login_required
def api_performance():
    conn = get_db()
    rows = conn.execute(
        "SELECT subject, correct FROM quiz_results WHERE user_id=?", (session["user_id"],)
    ).fetchall()
    conn.close()
    subject_scores = defaultdict(lambda: {"correct": 0, "total": 0})
    for row in rows:
        subject_scores[row["subject"]]["total"] += 1
        subject_scores[row["subject"]]["correct"] += row["correct"]
    labels = list(subject_scores.keys())
    data = [round(100 * d["correct"] / d["total"], 1) if d["total"] else 0 for d in subject_scores.values()]
    return jsonify({"labels": labels, "data": data})


# ------------------------------------------------------------- UPLOAD -----

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("document")
        subject = request.form.get("subject", "").strip() or "General"

        if not file or file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
            flash("Unsupported file type. Please upload PDF, DOCX, or TXT.", "danger")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        user_dir = os.path.join(app.config["UPLOAD_FOLDER"], str(session["user_id"]))
        os.makedirs(user_dir, exist_ok=True)
        filepath = os.path.join(user_dir, filename)
        file.save(filepath)

        raw_text = clean_text(extract_text(filepath))
        topics = extract_topics(raw_text)
        chunks = chunk_text(raw_text)

        if not chunks:
            flash("Could not extract any readable text from that file.", "warning")

        conn = get_db()
        cur = conn.execute(
            "INSERT INTO documents (user_id, filename, filepath, subject, topics, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session["user_id"], filename, filepath, subject, json.dumps(topics), now()),
        )
        doc_id = cur.lastrowid
        for idx, chunk in enumerate(chunks):
            conn.execute(
                "INSERT INTO chunks (document_id, chunk_index, text) VALUES (?, ?, ?)",
                (doc_id, idx, chunk),
            )
        conn.commit()
        conn.close()

        get_engine_for_user(session["user_id"])  # refresh RAG index

        flash(f"'{filename}' processed — {len(topics)} topics detected, {len(chunks)} chunks indexed.", "success")
        return redirect(url_for("documents"))

    return render_template("upload.html")


@app.route("/documents")
@login_required
def documents():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM documents WHERE user_id=? ORDER BY uploaded_at DESC", (session["user_id"],)
    ).fetchall()
    conn.close()
    docs = []
    for r in rows:
        d = dict(r)
        d["topics"] = json.loads(d["topics"]) if d["topics"] else []
        docs.append(d)
    return render_template("documents.html", documents=docs)


@app.route("/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document(doc_id):
    conn = get_db()
    doc = conn.execute(
        "SELECT * FROM documents WHERE id=? AND user_id=?", (doc_id, session["user_id"])
    ).fetchone()
    if doc:
        conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
        conn.commit()
        try:
            os.remove(doc["filepath"])
        except OSError:
            pass
        get_engine_for_user(session["user_id"])
        flash("Document removed.", "info")
    conn.close()
    return redirect(url_for("documents"))


# ------------------------------------------------------------ ASK / RAG ---

@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask():
    answer = None
    sources = []
    question = ""

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if question:
            engine = _rag_cache.get(session["user_id"]) or get_engine_for_user(session["user_id"])
            answer, sources = engine.generate_answer(question, api_key=app.config.get("ANTHROPIC_API_KEY") or None)

            conn = get_db()
            conn.execute(
                "INSERT INTO queries (user_id, question, answer, sources, created_at) VALUES (?, ?, ?, ?, ?)",
                (session["user_id"], question, answer, json.dumps([s["doc_name"] for s in sources]), now()),
            )
            conn.commit()
            conn.close()

    conn = get_db()
    history = conn.execute(
        "SELECT * FROM queries WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("ask.html", answer=answer, sources=sources, question=question, history=history)


# -------------------------------------------------------------- QUIZ ------

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    conn = get_db()
    docs = conn.execute(
        "SELECT id, filename, subject FROM documents WHERE user_id=?", (session["user_id"],)
    ).fetchall()
    conn.close()

    if request.method == "GET":
        doc_id = request.args.get("doc_id")
        if not doc_id:
            return render_template("quiz.html", docs=docs, quiz_questions=None)

        conn = get_db()
        doc = conn.execute("SELECT * FROM documents WHERE id=? AND user_id=?", (doc_id, session["user_id"])).fetchone()
        chunk_rows = conn.execute("SELECT text FROM chunks WHERE document_id=?", (doc_id,)).fetchall()
        conn.close()

        if not doc:
            flash("Document not found.", "danger")
            return redirect(url_for("quiz"))

        chunks = [r["text"] for r in chunk_rows]
        questions = generate_quiz(chunks, num_questions=5, subject=doc["subject"])
        session["active_quiz"] = questions
        session["active_quiz_doc"] = doc["filename"]

        if not questions:
            flash("Not enough content in this document to build a quiz yet. Try a longer document.", "warning")
            return redirect(url_for("quiz"))

        return render_template("quiz.html", docs=docs, quiz_questions=questions, doc_name=doc["filename"])

    # POST -> grade the quiz
    questions = session.get("active_quiz", [])
    correct_count = 0
    conn = get_db()
    results = []
    for i, q in enumerate(questions):
        selected = request.form.get(f"q{i}")
        is_correct = selected is not None and int(selected) == q["answer_index"]
        if is_correct:
            correct_count += 1
        conn.execute(
            "INSERT INTO quiz_results (user_id, subject, topic, correct, created_at) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], q["subject"], q["topic"], 1 if is_correct else 0, now()),
        )
        results.append({**q, "selected": int(selected) if selected is not None else None, "is_correct": is_correct})
    conn.commit()
    conn.close()

    score_pct = round(100 * correct_count / len(questions), 1) if questions else 0
    flash(f"Quiz submitted! Score: {correct_count}/{len(questions)} ({score_pct}%)", "success")
    session.pop("active_quiz", None)
    return render_template("quiz.html", docs=docs, quiz_questions=None, results=results, score_pct=score_pct)


# ------------------------------------------------------------ ROADMAP -----

@app.route("/roadmap")
@login_required
def roadmap():
    conn = get_db()
    rows = conn.execute(
        "SELECT subject, topic, correct FROM quiz_results WHERE user_id=?", (session["user_id"],)
    ).fetchall()
    conn.close()

    topic_stats = defaultdict(lambda: {"correct": 0, "total": 0, "subject": "General"})
    for r in rows:
        key = r["topic"]
        topic_stats[key]["total"] += 1
        topic_stats[key]["correct"] += r["correct"]
        topic_stats[key]["subject"] = r["subject"]

    roadmap_items = []
    for topic, stats in topic_stats.items():
        accuracy = 100 * stats["correct"] / stats["total"]
        if accuracy < 50:
            priority = "High"
        elif accuracy < 80:
            priority = "Medium"
        else:
            priority = "Low"
        roadmap_items.append({
            "topic": topic,
            "subject": stats["subject"],
            "accuracy": round(accuracy, 1),
            "attempts": stats["total"],
            "priority": priority,
        })

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    roadmap_items.sort(key=lambda x: (priority_order[x["priority"]], x["accuracy"]))

    return render_template("roadmap.html", roadmap_items=roadmap_items)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
