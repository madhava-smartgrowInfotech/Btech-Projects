"""
Thin JSON API for the React frontend.

It reuses the existing Flask project code (db.py, config.py, utils/*, and the RAG-index helper in app.py)
and exposes the same operations that the Flask routes perform. No retrieval, quiz or grading logic is
rewritten here. The Flask app itself (python app.py, port 5000) is untouched.

Run from the project root:  python -m uvicorn backend.main:app --port 8301
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _load_env(path):
    """Minimal .env reader (KEY=VALUE lines); real environment variables win."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(os.path.join(ROOT, ".env"))

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from starlette.middleware.sessions import SessionMiddleware  # noqa: E402
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: E402
from werkzeug.utils import secure_filename  # noqa: E402

from config import Config  # noqa: E402
from db import get_db, init_db, now  # noqa: E402
from utils.quiz_generator import generate_quiz  # noqa: E402
from utils.text_extraction import allowed_file, chunk_text, clean_text, extract_text, extract_topics  # noqa: E402
import app as legacy  # noqa: E402  (reuses get_engine_for_user + the per-user RAG cache)

FRONTEND_PORT = os.environ.get("FRONTEND_PORT", "5301")

api = FastAPI(title="Adaptive Learning Intelligence Platform API", docs_url="/api/docs", openapi_url="/api/openapi.json")
api.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", Config.SECRET_KEY),
    session_cookie="alip_session",
    same_site="lax",
    https_only=False,
    max_age=60 * 60 * 24 * 7,
)
app = api  # uvicorn backend.main:app

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
init_db()

# user_id -> {"doc_name": str, "questions": [...]}  (Flask keeps this in the cookie session)
_active_quizzes = {}


# ------------------------------------------------------------ helpers -----

def current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return {"id": user_id, "username": request.session.get("username", "")}


def _subject_scores(rows):
    scores = defaultdict(lambda: {"correct": 0, "total": 0})
    for row in rows:
        scores[row["subject"]]["total"] += 1
        scores[row["subject"]]["correct"] += row["correct"]
    return scores


def _doc_dict(row, chunk_count=None):
    d = dict(row)
    d.pop("filepath", None)
    d["topics"] = json.loads(d["topics"]) if d.get("topics") else []
    if chunk_count is not None:
        d["chunk_count"] = chunk_count
    return d


# ------------------------------------------------------------- schemas ----

class RegisterBody(BaseModel):
    username: str = ""
    password: str = ""
    interests: str = ""


class LoginBody(BaseModel):
    username: str = ""
    password: str = ""


class AskBody(BaseModel):
    question: str = ""


class QuizGenerateBody(BaseModel):
    doc_id: int


class QuizSubmitBody(BaseModel):
    # answers[i] = chosen option index for question i, or null when left blank
    answers: list[int | None] = []


# ---------------------------------------------------------------- misc ----

@api.get("/api/health")
def health():
    return {"status": "ok", "llm_enabled": bool(Config.ANTHROPIC_API_KEY)}


# ---------------------------------------------------------------- auth ----

@api.post("/api/auth/register", status_code=201)
def register(body: RegisterBody):
    username = body.username.strip()
    if not username or not body.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")
    conn = get_db()
    try:
        if conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            raise HTTPException(status_code=409, detail="Username already taken.")
        conn.execute(
            "INSERT INTO users (username, password_hash, interests, created_at) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(body.password), body.interests.strip(), now()),
        )
        conn.commit()
    finally:
        conn.close()
    return {"message": "Account created. Please log in."}


@api.post("/api/auth/login")
def login(body: LoginBody, request: Request):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (body.username.strip(),)).fetchone()
    conn.close()
    if not (user and check_password_hash(user["password_hash"], body.password)):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    return {"id": user["id"], "username": user["username"], "interests": user["interests"] or ""}


@api.post("/api/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully."}


@api.get("/api/auth/me")
def me(request: Request):
    """The signed-in user, or null (HTTP 200) when nobody is signed in, so the app can check quietly on load."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    conn = get_db()
    row = conn.execute("SELECT id, username, interests FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        request.session.clear()
        return None
    return {"id": row["id"], "username": row["username"], "interests": row["interests"] or ""}


# ----------------------------------------------------------- dashboard ----

@api.get("/api/dashboard")
def dashboard(user=Depends(current_user)):
    conn = get_db()
    uid = user["id"]
    doc_count = conn.execute("SELECT COUNT(*) c FROM documents WHERE user_id=?", (uid,)).fetchone()["c"]
    query_count = conn.execute("SELECT COUNT(*) c FROM queries WHERE user_id=?", (uid,)).fetchone()["c"]
    quiz_rows = conn.execute("SELECT * FROM quiz_results WHERE user_id=?", (uid,)).fetchall()
    documents = conn.execute(
        "SELECT * FROM documents WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 5", (uid,)
    ).fetchall()
    conn.close()
    performance = [
        {"subject": subj, "accuracy": round(100 * d["correct"] / d["total"], 1) if d["total"] else 0, "attempts": d["total"]}
        for subj, d in _subject_scores(quiz_rows).items()
    ]
    return {
        "username": user["username"],
        "doc_count": doc_count,
        "query_count": query_count,
        "quiz_attempts": len(quiz_rows),
        "performance": performance,
        "documents": [_doc_dict(r) for r in documents],
    }


# ----------------------------------------------------------- documents ----

@api.get("/api/documents")
def list_documents(user=Depends(current_user)):
    conn = get_db()
    rows = conn.execute(
        """SELECT d.*, (SELECT COUNT(*) FROM chunks c WHERE c.document_id = d.id) AS chunk_count
           FROM documents d WHERE d.user_id=? ORDER BY d.uploaded_at DESC""",
        (user["id"],),
    ).fetchall()
    conn.close()
    return [_doc_dict(r, r["chunk_count"]) for r in rows]


@api.post("/api/documents", status_code=201)
async def upload_document(
    document: UploadFile = File(...),
    subject: str = Form(""),
    user=Depends(current_user),
):
    if not document.filename:
        raise HTTPException(status_code=400, detail="Please choose a file to upload.")
    if not allowed_file(document.filename, Config.ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF, DOCX, or TXT.")
    content = await document.read()
    if len(content) > Config.MAX_CONTENT_LENGTH:
        raise HTTPException(status_code=413, detail="File is too large. The limit is 16 MB.")

    subject = subject.strip() or "General"
    filename = secure_filename(document.filename)
    user_dir = os.path.join(Config.UPLOAD_FOLDER, str(user["id"]))
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    raw_text = clean_text(extract_text(filepath))
    topics = extract_topics(raw_text)
    chunks = chunk_text(raw_text)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO documents (user_id, filename, filepath, subject, topics, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user["id"], filename, filepath, subject, json.dumps(topics), now()),
    )
    doc_id = cur.lastrowid
    for idx, chunk in enumerate(chunks):
        conn.execute("INSERT INTO chunks (document_id, chunk_index, text) VALUES (?, ?, ?)", (doc_id, idx, chunk))
    conn.commit()
    row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    conn.close()

    legacy.get_engine_for_user(user["id"])  # refresh RAG index
    return {
        "document": _doc_dict(row, len(chunks)),
        "topics_count": len(topics),
        "chunks_count": len(chunks),
        "warning": None if chunks else "Could not extract any readable text from that file.",
    }


@api.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int, user=Depends(current_user)):
    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id=? AND user_id=?", (doc_id, user["id"])).fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")
    conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    try:
        os.remove(doc["filepath"])
    except OSError:
        pass
    legacy.get_engine_for_user(user["id"])
    return {"message": "Document removed."}


# ------------------------------------------------------------ ask / RAG ---

@api.post("/api/ask")
def ask(body: AskBody, user=Depends(current_user)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please type a question.")
    engine = legacy._rag_cache.get(user["id"]) or legacy.get_engine_for_user(user["id"])
    answer, sources = engine.generate_answer(question, api_key=Config.ANTHROPIC_API_KEY or None)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO queries (user_id, question, answer, sources, created_at) VALUES (?, ?, ?, ?, ?)",
        (user["id"], question, answer, json.dumps([s["doc_name"] for s in sources]), now()),
    )
    conn.commit()
    created = conn.execute("SELECT created_at FROM queries WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return {
        "id": cur.lastrowid,
        "question": question,
        "answer": answer,
        "sources": sources,
        "created_at": created["created_at"],
        "llm_enabled": bool(Config.ANTHROPIC_API_KEY),
    }


@api.get("/api/ask/history")
def ask_history(user=Depends(current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM queries WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user["id"],)
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["sources"] = json.loads(d["sources"]) if d.get("sources") else []
        out.append(d)
    return out


# ---------------------------------------------------------------- quiz ----

@api.post("/api/quiz/generate")
def quiz_generate(body: QuizGenerateBody, user=Depends(current_user)):
    conn = get_db()
    doc = conn.execute("SELECT * FROM documents WHERE id=? AND user_id=?", (body.doc_id, user["id"])).fetchone()
    chunk_rows = conn.execute("SELECT text FROM chunks WHERE document_id=?", (body.doc_id,)).fetchall()
    conn.close()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    questions = generate_quiz([r["text"] for r in chunk_rows], num_questions=5, subject=doc["subject"])
    if not questions:
        raise HTTPException(
            status_code=422,
            detail="Not enough content in this document to build a quiz yet. Try a longer document.",
        )
    _active_quizzes[user["id"]] = {"doc_name": doc["filename"], "questions": questions}
    return {
        "doc_id": doc["id"],
        "doc_name": doc["filename"],
        "subject": doc["subject"],
        # answer_index stays on the server until the quiz is graded
        "questions": [{"question": q["question"], "options": q["options"], "topic": q["topic"]} for q in questions],
    }


@api.post("/api/quiz/submit")
def quiz_submit(body: QuizSubmitBody, user=Depends(current_user)):
    active = _active_quizzes.get(user["id"])
    if not active:
        raise HTTPException(status_code=409, detail="No active quiz. Generate a quiz from one of your documents first.")
    questions = active["questions"]

    correct_count = 0
    results = []
    conn = get_db()
    for i, q in enumerate(questions):
        selected = body.answers[i] if i < len(body.answers) else None
        is_correct = selected is not None and selected == q["answer_index"]
        if is_correct:
            correct_count += 1
        conn.execute(
            "INSERT INTO quiz_results (user_id, subject, topic, correct, created_at) VALUES (?, ?, ?, ?, ?)",
            (user["id"], q["subject"], q["topic"], 1 if is_correct else 0, now()),
        )
        results.append({**q, "selected": selected, "is_correct": is_correct})
    conn.commit()
    conn.close()
    _active_quizzes.pop(user["id"], None)

    return {
        "doc_name": active["doc_name"],
        "correct": correct_count,
        "total": len(questions),
        "score_pct": round(100 * correct_count / len(questions), 1) if questions else 0,
        "results": results,
    }


# ------------------------------------------------------------- roadmap ----

@api.get("/api/roadmap")
def roadmap(user=Depends(current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT subject, topic, correct FROM quiz_results WHERE user_id=?", (user["id"],)
    ).fetchall()
    conn.close()

    topic_stats = defaultdict(lambda: {"correct": 0, "total": 0, "subject": "General"})
    for r in rows:
        stats = topic_stats[r["topic"]]
        stats["total"] += 1
        stats["correct"] += r["correct"]
        stats["subject"] = r["subject"]

    items = []
    for topic, stats in topic_stats.items():
        accuracy = 100 * stats["correct"] / stats["total"]
        priority = "High" if accuracy < 50 else "Medium" if accuracy < 80 else "Low"
        items.append(
            {
                "topic": topic,
                "subject": stats["subject"],
                "accuracy": round(accuracy, 1),
                "attempts": stats["total"],
                "priority": priority,
            }
        )
    order = {"High": 0, "Medium": 1, "Low": 2}
    items.sort(key=lambda x: (order[x["priority"]], x["accuracy"]))
    return items
