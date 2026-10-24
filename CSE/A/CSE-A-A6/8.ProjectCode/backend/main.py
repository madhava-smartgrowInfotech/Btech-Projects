"""Thin FastAPI layer over the existing desktop modules (core, vision, storage, research).

Run from the project root:  python -m uvicorn backend.main:app --port 8306
No decision logic lives here; see backend/session.py for the session glue.
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import tempfile
import threading
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_env():
    """Read the project-root .env (ports, demo login) without overriding real environment variables."""
    path = ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env()

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from starlette.background import BackgroundTask  # noqa: E402

from backend import content, synthetic  # noqa: E402
from backend.session import RiderSession, SessionError  # noqa: E402
from core import Settings  # noqa: E402
from storage import Store  # noqa: E402

DATA_DIR = Path(os.environ.get('RIDER_DATA_DIR') or ROOT / 'data')
RESEARCH_DIR = Path(os.environ.get('RIDER_RESEARCH_DIR') or ROOT / 'research_results')
MODEL_PATH = ROOT / 'models' / 'face_landmarker.task'

DEMO_EMAIL = os.environ.get('DEMO_EMAIL', 'demo@smartrider.app')
DEMO_PASSWORD = os.environ.get('DEMO_PASSWORD', 'Demo@1234')
AUTH_SECRET = (os.environ.get('AUTH_SECRET') or 'smart-rider-local-demo-secret').encode()
TOKEN_HOURS = 12

app = FastAPI(title='Smart Rider Impairment Warning API', version='1.0.0',
              description='Thin API over the desktop prototype. A camera cannot confirm alcohol use.')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

SESSIONS: dict[str, RiderSession] = {}
SESSIONS_LOCK = threading.Lock()
RESEARCH_LOCK = threading.Lock()


# ----------------------------------------------------------------------------- auth (demo login)
def _sign(payload: str) -> str:
    return hmac.new(AUTH_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_token(email: str) -> str:
    body = base64.urlsafe_b64encode(json.dumps({'sub': email, 'exp': int(time.time()) + TOKEN_HOURS * 3600}).encode()).decode()
    return f'{body}.{_sign(body)}'


def current_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(401, 'Please sign in to continue.')
    token = authorization.split(' ', 1)[1].strip()
    try:
        body, sig = token.rsplit('.', 1)
        if not hmac.compare_digest(sig, _sign(body)):
            raise ValueError
        claims = json.loads(base64.urlsafe_b64decode(body.encode()))
        if claims['exp'] < time.time():
            raise HTTPException(401, 'Your session expired. Please sign in again.')
        return claims['sub']
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, 'Your sign-in is not valid. Please sign in again.')


class Login(BaseModel):
    email: str
    password: str


@app.post('/api/auth/login')
def login(body: Login):
    ok_email = hmac.compare_digest(body.email.strip().lower().encode(), DEMO_EMAIL.lower().encode())
    ok_pass = hmac.compare_digest(body.password.encode(), DEMO_PASSWORD.encode())
    if not (ok_email and ok_pass):
        raise HTTPException(401, 'Email or password is incorrect. Use the demo account shown on the sign-in page.')
    return {'token': make_token(DEMO_EMAIL), 'user': {'email': DEMO_EMAIL, 'name': 'Demo Rider'}}


@app.get('/api/auth/me')
def me(user: str = Depends(current_user)):
    return {'email': user, 'name': 'Demo Rider'}


@app.get('/api/auth/demo')
def demo_hint():
    return {'email': DEMO_EMAIL, 'password': DEMO_PASSWORD}


# ----------------------------------------------------------------------------- public info
@app.get('/api/health')
def health():
    report = RESEARCH_DIR / 'report.json'
    with _store() as store:
        total = store.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    return {'status': 'ok', 'landmark_model': MODEL_PATH.exists(), 'history_events': total, 'model_report': report.exists()}


@app.get('/api/config')
def get_config():
    return content.config()


@app.get('/api/about')
def get_about():
    return content.about()


# ----------------------------------------------------------------------------- store helper
class _store:
    """`with _store() as s:` opens a fresh Store (sqlite connections are bound to their creating thread)."""

    def __enter__(self):
        self.s = Store(DATA_DIR)
        return self.s

    def __exit__(self, *exc):
        self.s.close()


def _session(session_id: str) -> RiderSession:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(404, 'This monitoring session no longer exists. Reload the page to start a new one.')
    return session


def _guard(fn):
    try:
        return fn()
    except SessionError as exc:
        raise HTTPException(exc.status, str(exc))


# ----------------------------------------------------------------------------- sessions
@app.post('/api/session', dependencies=[Depends(current_user)])
def create_session():
    with SESSIONS_LOCK:
        for sid, old in list(SESSIONS.items()):          # drop sessions idle for 15 minutes
            if time.monotonic() - old.touched > 900:
                SESSIONS.pop(sid).close()
        session = RiderSession(DATA_DIR)
        SESSIONS[session.id] = session
    return session.snapshot()


@app.delete('/api/session/{session_id}', dependencies=[Depends(current_user)])
def close_session(session_id: str):
    with SESSIONS_LOCK:
        session = SESSIONS.pop(session_id, None)
    if session:
        session.close()
    return {'closed': session is not None}


@app.get('/api/session/{session_id}', dependencies=[Depends(current_user)])
def get_session(session_id: str):
    return _session(session_id).snapshot()


class SourceBody(BaseModel):
    source: str
    scenario: str | None = None


class ActiveBody(BaseModel):
    active: bool


@app.post('/api/session/{session_id}/source', dependencies=[Depends(current_user)])
def set_source(session_id: str, body: SourceBody):
    session = _session(session_id)
    return _guard(lambda: session.set_source(body.source, body.scenario))


@app.post('/api/session/{session_id}/monitoring', dependencies=[Depends(current_user)])
def set_monitoring(session_id: str, body: ActiveBody):
    session = _session(session_id)
    return _guard(lambda: session.set_monitoring(body.active))


@app.post('/api/session/{session_id}/calibration', dependencies=[Depends(current_user)])
def set_calibration(session_id: str, body: ActiveBody):
    session = _session(session_id)
    return _guard(lambda: session.set_calibration(body.active))


@app.post('/api/session/{session_id}/frame', dependencies=[Depends(current_user)])
def post_frame(session_id: str, frame: UploadFile = File(...)):
    session = _session(session_id)
    data = frame.file.read()
    preview = _guard(lambda: session.frame(data))
    state = session.snapshot()
    state['preview'] = 'data:image/jpeg;base64,' + base64.b64encode(preview).decode()
    return state


@app.post('/api/session/{session_id}/tick', dependencies=[Depends(current_user)])
def tick(session_id: str):
    return _guard(lambda: _session(session_id).tick())


# ----------------------------------------------------------------------------- settings
class SettingsBody(BaseModel):
    ear_threshold: float
    closure_seconds: float
    persistence_seconds: float
    closed_fraction: float
    tilt_degrees: float
    cooldown_seconds: float


@app.get('/api/settings', dependencies=[Depends(current_user)])
def get_settings():
    with _store() as store:
        settings, note = store.load_settings()
    return {'settings': {k: v for k, v in asdict(settings).items() if k != 'calibrated'},
            'calibrated': settings.calibrated, 'note': note}


@app.put('/api/settings', dependencies=[Depends(current_user)])
def put_settings(body: SettingsBody):
    try:
        settings = Settings(**body.model_dump(), calibrated=False).validate()
        with _store() as store:
            store.save_settings(settings)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, str(exc))
    for session in list(SESSIONS.values()):
        session.apply_settings(settings)
    return {'settings': {k: v for k, v in asdict(settings).items() if k != 'calibrated'}, 'calibrated': False,
            'note': 'Thresholds saved. Monitoring stopped; restart to use the new settings.'}


# ----------------------------------------------------------------------------- history
HISTORY_COLUMNS = ['id', 'timestamp', 'source', 'state', 'quality', 'reason', 'ear', 'closure', 'blink_rate',
                   'closed_fraction', 'roll', 'alert']


@app.get('/api/history', dependencies=[Depends(current_user)])
def history(limit: int = 500):
    limit = max(1, min(limit, 500))
    with _store() as store:
        rows = store.recent(limit)
        db = store.db
        total = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        by_state = dict(db.execute('SELECT state, COUNT(*) FROM events GROUP BY state').fetchall())
        simulated = db.execute("SELECT COUNT(*) FROM events WHERE source LIKE 'SIMULATION%'").fetchone()[0]
        alerts = db.execute('SELECT COUNT(*) FROM events WHERE alert = 1').fetchone()[0]
    events = [dict(zip(HISTORY_COLUMNS, r)) for r in rows]
    for e in events:
        e['alert'] = bool(e['alert'])
        e['simulation'] = e['source'].startswith('SIMULATION')
    return {'events': events, 'total': total,
            'summary': {'warnings': by_state.get(content.config()['states']['warning'], 0),
                        'normal': by_state.get('Normal', 0),
                        'unknown': by_state.get('Unable to assess', 0),
                        'alerts': alerts, 'simulation': simulated, 'live': total - simulated}}


@app.get('/api/history/export', dependencies=[Depends(current_user)])
def history_export():
    handle = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
    handle.close()
    with _store() as store:
        store.export(handle.name)
    return FileResponse(handle.name, media_type='text/csv', filename='rider_events.csv',
                        background=BackgroundTask(lambda: os.unlink(handle.name)))


# ----------------------------------------------------------------------------- research (offline only)
def _report_payload():
    report_path = RESEARCH_DIR / 'report.json'
    if not report_path.exists():
        return {'trained': False, 'status': 'Model not trained', 'synthetic': False, 'files': []}
    report = json.loads(report_path.read_text(encoding='utf-8'))
    return {'trained': True, 'status': report.get('status'), 'report': report,
            'synthetic': report.get('dataset_sha256') == synthetic.sha256(),
            'files': sorted(p.name for p in RESEARCH_DIR.iterdir()),
            'confusion_matrix_image': (RESEARCH_DIR / 'confusion_matrix.png').exists()}


@app.get('/api/research', dependencies=[Depends(current_user)])
def research_status():
    return _report_payload()


@app.get('/api/research/sample-csv', dependencies=[Depends(current_user)])
def research_sample():
    return Response(synthetic.csv_text(), media_type='text/csv',
                    headers={'Content-Disposition': 'attachment; filename="synthetic_demo_measurements.csv"'})


@app.post('/api/research/evaluate', dependencies=[Depends(current_user)])
def research_evaluate(file: UploadFile = File(...), test_subjects: str = Form('')):
    from research import evaluate
    ids = [s.strip() for s in test_subjects.replace(';', ',').split(',') if s.strip()]
    if not ids:
        raise HTTPException(422, 'Enter held-out subject IDs first.')
    if not RESEARCH_LOCK.acquire(blocking=False):
        raise HTTPException(409, 'Evaluation already running.')
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'upload.csv'
            path.write_bytes(file.file.read())
            try:
                evaluate(str(path), RESEARCH_DIR, ids)
            except (ValueError, OSError, UnicodeDecodeError) as exc:
                raise HTTPException(422, f'Model not trained: {exc}')
    finally:
        RESEARCH_LOCK.release()
    return _report_payload()


@app.get('/api/research/confusion-matrix', dependencies=[Depends(current_user)])
def research_matrix():
    path = RESEARCH_DIR / 'confusion_matrix.png'
    if not path.exists():
        raise HTTPException(404, 'No confusion matrix yet. Run an evaluation first.')
    return FileResponse(path, media_type='image/png')


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return JSONResponse({'detail': f'Unexpected server error: {exc}'}, status_code=500)
