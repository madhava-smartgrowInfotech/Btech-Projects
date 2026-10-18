"""HTTP API for AutoSecAI - a thin FastAPI layer over the existing `autosecai` package.

Nothing in `autosecai/` is changed: every route below calls the same functions the Streamlit app calls
(`review_changes`, `RepoIndex`, `store`, `report`, `mlmodel` ...). Run:  python -m backend
"""
from __future__ import annotations

import json
import math
import os
import sys
import threading
import time
import uuid
import zipfile
from collections import OrderedDict
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import networkx as nx  # noqa: E402
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from autosecai import __version__, llm, report, store  # noqa: E402
from autosecai.agents import review_changes  # noqa: E402
from autosecai.codeintel import CONCEPTS, RepoIndex  # noqa: E402
from autosecai.diffutil import (diff_from_versions, fetch_github_pr_diff, fetch_github_repo_zip, files_from_dir,  # noqa: E402
                                files_from_zip, full_files_to_changed, parse_unified_diff)
from autosecai.knowledge import RULES, SEVERITY_ORDER, rule as kb_rule  # noqa: E402
from autosecai.metrics import FEATURE_LABEL, METRICS, metrics_for_source  # noqa: E402
from autosecai.rules import analyze_source  # noqa: E402
from autosecai.samples import AFTER, BEFORE, DEMO_DIFF, DEMO_REPO  # noqa: E402

from . import auth  # noqa: E402

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8311"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5311"))
MAX_FILES = 300

app = FastAPI(title="AutoSecAI API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition"])


@app.on_event("startup")
def _startup() -> None:
    auth.seed_demo()


def clean(o):
    """JSON cannot carry NaN/inf; the model report is plain numbers but be safe."""
    if isinstance(o, float):
        return None if math.isnan(o) or math.isinf(o) else o
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


# ------------------------------------------------------------------ jobs (live agent progress)
JOBS: dict[str, dict] = {}


def start_job(kind: str, work) -> str:
    """Run `work(tick)` in a thread; the UI polls /api/jobs/{id} for the agent messages and the result."""
    now = time.time()
    for k in [k for k, j in JOBS.items() if now - j["started"] > 3600]:
        JOBS.pop(k, None)
    job = dict(id=uuid.uuid4().hex[:12], kind=kind, status="running", messages=[], result=None, error=None, started=now,
               seconds=None)
    JOBS[job["id"]] = job

    def run():
        try:
            job["result"] = work(job["messages"].append)
            job["status"] = "done"
        except HTTPException as e:
            job["error"], job["status"] = str(e.detail), "error"
        except Exception as e:  # network / parsing errors surface as readable messages
            job["error"], job["status"] = f"{type(e).__name__}: {e}", "error"
        job["seconds"] = round(time.time() - now, 2)

    threading.Thread(target=run, daemon=True).start()
    return job["id"]


# ------------------------------------------------------------------ models
class Options(BaseModel):
    ml: bool = True
    min_severity: Literal["critical", "high", "medium", "low", "info"] = "info"
    use_llm: bool = False
    api_key: str | None = None
    gh_token: str | None = None


class ReviewIn(BaseModel):
    kind: Literal["demo-diff", "demo-versions", "diff", "versions", "github", "folder"]
    title: str | None = None
    diff: str | None = None
    old: str | None = None
    new: str | None = None
    filename: str | None = None
    url: str | None = None
    folder: str | None = None
    options: Options = Field(default_factory=Options)


class LoginIn(BaseModel):
    email: str
    password: str


class RegisterIn(LoginIn):
    name: str


class IndexIn(BaseModel):
    source: Literal["demo", "self", "folder", "github"]
    folder: str | None = None
    url: str | None = None
    gh_token: str | None = None


class AskIn(BaseModel):
    question: str
    k: int = 6
    use_llm: bool = False
    api_key: str | None = None


class AnalyzeIn(BaseModel):
    code: str


# ------------------------------------------------------------------ public
@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__}


@app.get("/api/public/stats")
def public_stats():
    """Real numbers from the trained model report, for the landing page."""
    from autosecai.mlmodel import load_report
    R = load_report()
    best = R["best"]
    return clean(dict(functions=R["n_functions"], vulnerable=R["n_vulnerable"], best_model=best, f1=R["results"][best]["f1"],
                      accuracy=R["results"][best]["accuracy"], recall=R["results"][best]["recall"],
                      type_accuracy=R["type_accuracy"], metrics=len(METRICS), models=len(R["results"]),
                      selectors=len(R["fs_scores"]), agents=7))


@app.get("/api/public/rules")
def public_rules():
    """Titles of the weakness classes in the rule knowledge base."""
    return {"rules": sorted({r["title"] for r in RULES.values() if r.get("category") == "security"})}


_EXAMPLE: dict = {}


@app.get("/api/public/example")
def public_example():
    """One real finding from the built-in demo pull request, for the landing page (computed once, not saved)."""
    if not _EXAMPLE:
        r = review_changes(parse_unified_diff(DEMO_DIFF), title="Demo: add user API", source_label="built-in demo diff")
        sec = [f for f in r["findings"] if f["category"] == "security" and f["in_diff"]]
        f = next((x for x in sec if x["rule_id"] == "SQLI"), sec[0])
        keep = ("title", "file", "line", "severity", "cwe", "snippet", "explanation", "remediation", "patch", "fix_verified")
        _EXAMPLE.update(verdict=r["verdict"], score=r["score"], files=r["stats"]["files"], security=len(sec),
                        finding={k: f[k] for k in keep})
    return _EXAMPLE


@app.post("/api/auth/login")
def login(body: LoginIn):
    user = auth.authenticate(body.email, body.password)
    return {"token": auth.make_token(user), "user": user}


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterIn):
    user = auth.register(body.name, body.email, body.password)
    return {"token": auth.make_token(user), "user": user}


@app.get("/api/auth/demo")
def demo_account():
    """The seeded demo credentials, shown on the sign-in page."""
    return {"email": auth.DEMO_EMAIL, "password": auth.DEMO_PASSWORD}


@app.get("/api/auth/me")
def me(user: dict = Depends(auth.current_user)):
    return user


# ------------------------------------------------------------------ meta
PIPELINE = [("Ingestion", "Parses the PR: files, hunks, changed lines"),
            ("Static Analysis", "AST + taint tracking for Python, regex rules for JS/PHP/Java"),
            ("ML Risk", "14 source-code metrics -> Random Forest (base paper)"),
            ("Security Reasoner", "Source→sink flow, impact, CWE/OWASP, ML corroboration"),
            ("Remediation", "Safe patches, verified by re-scanning"),
            ("Quality Reviewer", "Complexity, nesting, size, error handling"),
            ("Judge", "De-dupes, scores risk, verdict, PR comment")]

SUGGESTED = ["Where is the authentication mechanism implemented?", "Which files define the routes / API endpoints?",
             "Where is the login form in the UI?", "How does the app talk to the database?",
             "Where is configuration and secret handling?", "What are the entry points of this application?"]


def _safe_means() -> dict:
    from autosecai.mlmodel import load_bundle
    return load_bundle()["safe_stats"]["mean"]


@app.get("/api/meta")
def meta(_: dict = Depends(auth.current_user)):
    safe = _safe_means()
    return clean(dict(
        version=__version__, severities=sorted(SEVERITY_ORDER, key=SEVERITY_ORDER.get, reverse=True),
        pipeline=[dict(name=n, text=t) for n, t in PIPELINE], suggested=SUGGESTED, llm_env=llm.available(),
        metrics=[dict(id=m[0], key=m[1], name=m[2], meaning=m[3], label=FEATURE_LABEL[m[1]], safe_mean=safe.get(m[1], 0))
                 for m in METRICS]))


@app.get("/api/samples")
def samples(_: dict = Depends(auth.current_user)):
    return dict(demo_diff=DEMO_DIFF, before=BEFORE, after=AFTER, filename="services/users.py", repo_files=sorted(DEMO_REPO))


# ------------------------------------------------------------------ reviews
def _opts_dict(o: Options) -> dict:
    return dict(use_llm=o.use_llm, api_key=o.api_key or None, ml=o.ml, min_severity=o.min_severity)


def _review_job(prepare, source: str, opts: Options) -> str:
    def work(tick):
        changed, title = prepare(tick)
        if not changed:
            raise HTTPException(422, "The change contains no files to analyse.")
        if len(changed) > MAX_FILES:
            raise HTTPException(422, f"Too many files ({len(changed)}; limit {MAX_FILES}). Narrow the change.")
        r = review_changes(changed, title=title, source_label=source, progress=tick, **_opts_dict(opts))
        store.save(r)
        return dict(review_id=r["id"], verdict=r["verdict"], score=r["score"])
    return start_job("review", work)


@app.post("/api/reviews", status_code=202)
def create_review(body: ReviewIn, _: dict = Depends(auth.current_user)):
    o = body.options
    k = body.kind
    title = (body.title or "").strip()
    if k == "demo-diff":
        return {"job_id": _review_job(lambda t: (parse_unified_diff(DEMO_DIFF), "Demo: add user API"), "Demo PR", o)}
    if k == "demo-versions":
        return {"job_id": _review_job(lambda t: ([diff_from_versions(BEFORE, AFTER, "services/users.py")],
                                                 "Demo: refactor user service"), "Demo PR", o)}
    if k == "diff":
        if not (body.diff or "").strip():
            raise HTTPException(422, "Paste a unified diff or upload a .diff / .patch file.")
        changed = parse_unified_diff(body.diff)
        if not changed:
            raise HTTPException(422, "No files were found in that diff. Make sure it is a unified diff "
                                     "(starts with `diff --git` or `---/+++`).")
        return {"job_id": _review_job(lambda t: (changed, title or "Pasted pull request"), "Paste diff", o)}
    if k == "versions":
        if not (body.new or "").strip():
            raise HTTPException(422, "Paste the “After” version of the file.")
        fname = (body.filename or "app.py").strip() or "app.py"
        changed = [diff_from_versions(body.old or None, body.new, fname)]
        return {"job_id": _review_job(lambda t: (changed, title or "Local change"), "Compare two versions", o)}
    if k == "github":
        url = (body.url or "").strip()
        if not url:
            raise HTTPException(422, "Enter a GitHub pull request URL.")

        def prepare(tick):
            tick("Fetching pull request from GitHub…")
            diff, m = fetch_github_pr_diff(url, o.gh_token or None)
            tick(f"Fetched {m['repo']}#{m['number']} by {m['author']}: {m['changed_files']} files, +{m['additions']}/-{m['deletions']}")
            return parse_unified_diff(diff), f"{m['repo']}#{m['number']}: {m['title']}"
        return {"job_id": _review_job(prepare, url, o)}
    # folder
    folder = (body.folder or "").strip()
    if not folder:
        raise HTTPException(422, "Enter a folder path.")
    if not Path(folder).is_dir():
        raise HTTPException(422, "That folder does not exist on the machine running the API.")
    files = files_from_dir(folder)
    if not files:
        raise HTTPException(422, "No source files were found in that folder.")
    return {"job_id": _review_job(lambda t: (full_files_to_changed(files), title or "Repository scan"), "Upload files / repo", o)}


async def _read_uploads(files: list[UploadFile]) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in files:
        data = await f.read()
        name = f.filename or "file"
        if name.lower().endswith(".zip"):
            try:
                out.update(files_from_zip(data))
            except zipfile.BadZipFile:
                raise HTTPException(422, f"{name} is not a valid zip file.")
        else:
            out[name] = data.decode("utf-8", errors="replace")
    return out


@app.post("/api/reviews/upload", status_code=202)
async def create_review_upload(files: list[UploadFile] = File(...), title: str = Form("Repository scan"),
                               options: str = Form("{}"), _: dict = Depends(auth.current_user)):
    try:
        o = Options(**json.loads(options or "{}"))
    except (ValueError, TypeError):
        raise HTTPException(422, "Options must be valid JSON.")
    contents = await _read_uploads(files)
    if not contents:
        raise HTTPException(422, "No source files were found in the upload.")
    return {"job_id": _review_job(lambda t: (full_files_to_changed(contents), title.strip() or "Repository scan"),
                                  "Upload files / repo", o)}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str, _: dict = Depends(auth.current_user)):
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "That job is no longer available.")
    return {k: j[k] for k in ("id", "kind", "status", "result", "error", "seconds")} | {"messages": list(j["messages"])}


@app.get("/api/reviews")
def list_reviews(limit: int = Query(200, ge=1, le=500), _: dict = Depends(auth.current_user)):
    return store.list_reviews(limit)


def _load(review_id: str) -> dict:
    r = store.load(review_id)
    if not r:
        raise HTTPException(404, "That review was not found. It may have been deleted.")
    return r


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str, _: dict = Depends(auth.current_user)):
    return clean(_load(review_id))


@app.delete("/api/reviews/{review_id}")
def delete_review(review_id: str, _: dict = Depends(auth.current_user)):
    _load(review_id)
    store.delete(review_id)
    return {"deleted": review_id}


EXPORTS = {
    "md": (report.to_markdown, "text/markdown; charset=utf-8", "md"),
    "sarif": (report.to_sarif, "application/sarif+json", "sarif"),
    "json": (report.to_json, "application/json", "json"),
    "csv": (report.to_csv, "text/csv; charset=utf-8", "csv"),
}


@app.get("/api/reviews/{review_id}/export/{fmt}")
def export_review(review_id: str, fmt: str, _: dict = Depends(auth.current_user)):
    if fmt not in EXPORTS:
        raise HTTPException(404, f"Unknown export format “{fmt}”. Use one of: {', '.join(EXPORTS)}.")
    fn, mime, ext = EXPORTS[fmt]
    r = _load(review_id)
    return Response(fn(r), media_type=mime, headers={"Content-Disposition": f'attachment; filename="autosecai-{review_id}.{ext}"'})


@app.get("/api/reviews/{review_id}/patched")
def patched_file(review_id: str, path: str, _: dict = Depends(auth.current_user)):
    patched = _load(review_id).get("patched") or {}
    if path not in patched:
        raise HTTPException(404, "No auto-fixed version of that file exists for this review.")
    return Response(patched[path], media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{Path(path).name}"'})


# ------------------------------------------------------------------ codebase assistant
INDEXES: "OrderedDict[str, RepoIndex]" = OrderedDict()
MAX_INDEXES = 6
SELF_EXCLUDE = ("frontend/", "docs/", "scripts/", "data/", ".env")


def _graph(ix: RepoIndex) -> dict:
    _, edges = ix.file_graph()
    connected = sorted({n for e in edges for n in e})
    if len(connected) < 2:
        return dict(nodes=[], edges=[])
    G = nx.Graph()
    G.add_nodes_from(connected)
    G.add_edges_from(edges)
    pos = nx.spring_layout(G, seed=4, k=1.2 / max(len(G) ** .5, 1))
    deg = dict(G.degree())
    return dict(nodes=[dict(id=n, label=Path(n).name, x=float(pos[n][0]), y=float(pos[n][1]), degree=deg[n]) for n in G],
                edges=[list(e) for e in edges])


def _index_payload(index_id: str, ix: RepoIndex) -> dict:
    o = ix.overview()
    o["by_concept"] = [dict(key=k, label=CONCEPTS[k]["label"], files=v) for k, v in o["by_concept"].items() if v]
    return clean(dict(index_id=index_id, name=ix.name, files=len(ix.files), units=len(ix.chunks), overview=o,
                      guide=ix.onboarding_guide(), graph=_graph(ix)))


def _register_index(ix: RepoIndex | None) -> dict:
    if ix is None or not ix.chunks:
        raise HTTPException(422, "Nothing to index - check the source.")
    index_id = uuid.uuid4().hex[:10]
    INDEXES[index_id] = ix
    while len(INDEXES) > MAX_INDEXES:
        INDEXES.popitem(last=False)
    return _index_payload(index_id, ix)


@app.post("/api/codebase/index")
def index_repo(body: IndexIn, _: dict = Depends(auth.current_user)):
    if body.source == "demo":
        ix = RepoIndex(DEMO_REPO, "demo-shop")
    elif body.source == "self":
        files = {p: t for p, t in files_from_dir(str(ROOT)).items() if not p.startswith(SELF_EXCLUDE)}
        ix = RepoIndex(files, "AutoSecAI")
    elif body.source == "folder":
        folder = (body.folder or "").strip()
        if not folder or not Path(folder).is_dir():
            raise HTTPException(422, "That folder does not exist on the machine running the API.")
        ix = RepoIndex(files_from_dir(folder), Path(folder).name)
    else:
        url = (body.url or "").strip()
        if not url:
            raise HTTPException(422, "Enter a GitHub repository URL.")
        try:
            ix = RepoIndex(fetch_github_repo_zip(url, body.gh_token or None), url.rstrip("/").split("/")[-1])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(502, f"Indexing failed: {e}")
    return _register_index(ix)


@app.post("/api/codebase/index/upload")
async def index_upload(files: list[UploadFile] = File(...), _: dict = Depends(auth.current_user)):
    out: dict[str, str] = {}
    for f in files:
        try:
            out.update(files_from_zip(await f.read()))
        except zipfile.BadZipFile:
            raise HTTPException(422, f"{f.filename} is not a valid zip file.")
    name = (files[0].filename or "upload").rsplit(".", 1)[0]
    return _register_index(RepoIndex(out, name) if out else None)


def _index(index_id: str) -> RepoIndex:
    ix = INDEXES.get(index_id)
    if not ix:
        raise HTTPException(404, "That index is no longer loaded. Index the repository again.")
    return ix


@app.get("/api/codebase/{index_id}")
def get_index(index_id: str, _: dict = Depends(auth.current_user)):
    return _index_payload(index_id, _index(index_id))


@app.post("/api/codebase/{index_id}/ask")
def ask(index_id: str, body: AskIn, _: dict = Depends(auth.current_user)):
    if not body.question.strip():
        raise HTTPException(422, "Type a question about the codebase.")
    return clean(_index(index_id).ask(body.question.strip(), k=max(1, min(body.k, 12)), use_llm=body.use_llm,
                                      api_key=body.api_key or None))


# ------------------------------------------------------------------ model lab
@app.get("/api/lab/report")
def lab_report(_: dict = Depends(auth.current_user)):
    from autosecai.mlmodel import load_report
    return clean(load_report())


@app.post("/api/lab/analyze")
def lab_analyze(body: AnalyzeIn, _: dict = Depends(auth.current_user)):
    from autosecai.mlmodel import predict_metrics
    rows = metrics_for_source(body.code)
    if not rows:
        raise HTTPException(422, "Could not parse that as Python.")
    functions = []
    for m in rows:
        p = predict_metrics(m)
        functions.append(dict(name=m["name"], probability=p["probability"], vuln_type=p["vuln_type"], drivers=p["drivers"],
                              metrics=[dict(key=k, label=FEATURE_LABEL[k], value=m[k]) for k in FEATURE_LABEL]))
    fs, _m = analyze_source(body.code, "snippet.py")
    findings = [dict(rule_id=f.rule_id, line=f.line, severity=f.severity, title=f.extra.get("title") or kb_rule(f.rule_id)["title"])
                for f in fs if f.category == "security"]
    return clean(dict(functions=functions, findings=findings))


@app.post("/api/lab/retrain", status_code=202)
def lab_retrain(_: dict = Depends(auth.current_user)):
    def work(tick):
        import autosecai.mlmodel as mm
        tick("Generating corpus, selecting features, balancing, training 9 models…")
        mm.train_all()
        mm._cache.clear()
        tick("Models retrained and reloaded")
        return dict(ok=True)
    return {"job_id": start_job("retrain", work)}


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})
