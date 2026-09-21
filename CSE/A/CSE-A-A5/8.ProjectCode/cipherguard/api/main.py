"""
CipherGuard Shield - FastAPI backend.
Serves IDS inference, SecureChannel crypto, metrics, and static frontend.
"""
import base64
import io
import json
import time
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from cipherguard.crypto.secure_channel import SecureChannel, KeyPair, get_cloud_keypair, get_cloud_public_key
from cipherguard.ids.inference import ThreatSenseEngine
from cipherguard.ids.features import FEATURE_NAMES, CATEGORICAL_FEATURES

BASE_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = BASE_DIR / "web"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

app = FastAPI(
    title="CipherGuard Shield",
    description="Secure data transmission platform: SecureChannel (AES-256-GCM + ECDH P-256 + HKDF) + ThreatSense Engine (XGBoost + 1D CNN + Logistic Regression stacking) + Live Monitoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine (lazy load)
engine = ThreatSenseEngine(models_dir=MODELS_DIR)
# In-memory alerts log (recent 500)
alerts_log: list[dict] = []

# Startup: attempt to load engine, but don't crash if not yet trained (train on demand)
@app.on_event("startup")
async def startup_event():
    # Try training if artifacts missing
    try:
        if not (MODELS_DIR / "preprocessor.joblib").exists():
            print("[CipherGuard] No model artifacts found; triggering training...")
            from cipherguard.ids.train import train_pipeline
            train_pipeline(data_dir=BASE_DIR / "data" / "raw", models_dir=MODELS_DIR, reports_dir=REPORTS_DIR)
        engine.load()
        print("[CipherGuard] ThreatSense Engine loaded.")
    except Exception as e:
        print(f"[CipherGuard] Startup engine load failed: {e}")
        # Will retry on first request

def ensure_engine():
    if not engine.loaded:
        try:
            engine.load()
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=f"IDS engine not ready: {e}. Run training first.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"IDS engine error: {e}")

# ---------- Health ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "product": "CipherGuard Shield", "version": "1.0.0", "engine_loaded": engine.loaded}

# ---------- Metrics ----------
@app.get("/api/metrics")
def get_metrics():
    path = REPORTS_DIR / "metrics.json"
    if not path.exists():
        # Try ensure engine triggers training, then recheck
        ensure_engine()
        if not path.exists():
            raise HTTPException(status_code=404, detail="Metrics not found. Train the model first.")
    with open(path) as f:
        return json.load(f)

# ---------- IDS: single record ----------
class IDSRecord(BaseModel):
    dur: Optional[float] = 0
    proto: str = "tcp"
    service: str = "http"
    state: str = "CON"
    spkts: Optional[int] = 5
    dpkts: Optional[int] = 5
    sbytes: Optional[int] = 500
    dbytes: Optional[int] = 500
    rate: Optional[float] = 10000
    sttl: Optional[int] = 62
    dttl: Optional[int] = 62
    sload: Optional[float] = 80000
    dload: Optional[float] = 60000
    sloss: Optional[int] = 0
    dloss: Optional[int] = 0
    sinpkt: Optional[float] = 50
    dinpkt: Optional[float] = 50
    sjit: Optional[float] = 5
    djit: Optional[float] = 5
    swin: Optional[int] = 255
    stcpb: Optional[int] = 1000000
    dtcpb: Optional[int] = 1000000
    dwin: Optional[int] = 255
    tcprtt: Optional[float] = 0.02
    synack: Optional[float] = 0.01
    ackdat: Optional[float] = 0.01
    smean: Optional[int] = 100
    dmean: Optional[int] = 100
    trans_depth: Optional[int] = 1
    response_body_len: Optional[int] = 200
    ct_srv_src: Optional[int] = 2
    ct_state_ttl: Optional[int] = 2
    ct_dst_ltm: Optional[int] = 2
    ct_src_dport_ltm: Optional[int] = 2
    ct_dst_sport_ltm: Optional[int] = 2
    ct_dst_src_ltm: Optional[int] = 2
    is_ftp_login: Optional[int] = 0
    ct_ftp_cmd: Optional[int] = 0
    ct_flw_http_mthd: Optional[int] = 1
    ct_src_ltm: Optional[int] = 2
    ct_srv_dst: Optional[int] = 2
    is_sm_ips_ports: Optional[int] = 0

    class Config:
        extra = "allow"

@app.post("/api/ids/score")
def score_single(record: dict = Body(...)):
    """
    Score a single traffic record. Accepts any dict with feature keys.
    """
    ensure_engine()
    # Validate at least some features
    if not record or not isinstance(record, dict):
        raise HTTPException(status_code=400, detail="Invalid record payload")
    # Fill defaults for missing features
    # Use IDSRecord to set defaults then overlay provided
    try:
        base = IDSRecord(**record).model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid record: {e}")
    # Merge: user-provided values take precedence, but ensure all FEATURE_NAMES present
    merged = {f: record.get(f, base.get(f)) for f in FEATURE_NAMES}
    result = engine.score_single(merged)
    # Log alert if attack
    if result["label"] == "attack":
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "severity": result["severity"],
            "confidence": result["confidence"],
            "label": result["label"],
            "features": {k: merged[k] for k in ["proto", "service", "state", "sbytes", "dbytes", "rate", "ct_srv_src"] if k in merged},
            "scores": {"xgb": result["xgb_score"], "cnn": result["cnn_score"]},
        }
        alerts_log.insert(0, entry)
        if len(alerts_log) > 500:
            alerts_log.pop()
        result["alert"] = entry
    return result

@app.post("/api/ids/score-batch")
async def score_batch(file: UploadFile = File(...)):
    ensure_engine()
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10 MB)")
        df = pd.read_csv(io.BytesIO(content), low_memory=False)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    # Normalize columns
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    # Drop id/label/attack_cat if present for scoring (but keep if user wants)
    # Map case
    for f in FEATURE_NAMES:
        if f not in df.columns and f.lower() in df.columns:
            df = df.rename(columns={f.lower(): f})

    # Check minimal features
    missing = [f for f in FEATURE_NAMES if f not in df.columns]
    if missing:
        # Fill missing with defaults rather than error, but warn
        for m in missing:
            df[m] = 0 if m not in CATEGORICAL_FEATURES else "-"
        # Note: continue

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="CSV is empty")
    if len(df) > 10000:
        raise HTTPException(status_code=400, detail="CSV too many rows (max 10000)")

    # Score
    try:
        res = engine.predict_proba(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}")

    # Build per-row results
    results = []
    attack_count = 0
    normal_count = 0
    for i in range(len(df)):
        label = res["labels"][i]
        conf = res["ensemble_proba"][i]
        if label == "attack":
            attack_count += 1
            severity = "critical" if conf >= 0.85 else "high" if conf >= 0.70 else "medium"
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "severity": severity,
                "confidence": float(conf),
                "label": label,
                "features": {k: str(df.iloc[i][k]) if k in df.columns else "" for k in ["proto", "service", "state"]},
                "scores": {"xgb": float(res["xgb_proba"][i]), "cnn": float(res["cnn_proba"][i])},
            }
            alerts_log.insert(0, entry)
            if len(alerts_log) > 500:
                alerts_log.pop()
        else:
            normal_count += 1
        results.append({
            "row": i,
            "label": label,
            "confidence": float(conf),
            "xgb_score": float(res["xgb_proba"][i]),
            "cnn_score": float(res["cnn_proba"][i]),
        })

    return {
        "total": len(df),
        "attack_count": attack_count,
        "normal_count": normal_count,
        "results": results[:1000],  # cap response
    }

# ---------- Alerts ----------
@app.get("/api/alerts")
def get_alerts(limit: int = 100):
    limit = max(1, min(limit, 500))
    return {"alerts": alerts_log[:limit], "total": len(alerts_log)}

@app.delete("/api/alerts")
def clear_alerts():
    alerts_log.clear()
    return {"cleared": True}

# ---------- SecureChannel ----------
class EncryptRequest(BaseModel):
    plaintext: str = Field(..., description="Text to encrypt")
    # Optional: if user wants to provide session key, but we use ECDH ephemeral in demo

class DecryptRequest(BaseModel):
    ciphertext: str
    nonce: str
    tag: str
    ephemeral_public: Optional[str] = None  # for ECDH path; if not provided, try direct session key path via stored cloud key? For simplicity we do direct key.

# Simple in-memory last session key for demo decrypt round-trip (since ephemeral private not exposed)
_last_session_keys: dict[str, bytes] = {}  # map fingerprint -> key

@app.post("/api/crypto/encrypt")
def crypto_encrypt(req: EncryptRequest):
    if not req.plaintext:
        raise HTTPException(status_code=400, detail="Plaintext cannot be empty")
    if len(req.plaintext.encode()) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="Payload too large (max 1 MB)")
    # Use ephemeral ECDH to cloud public key
    cloud_pub = get_cloud_public_key()
    # Generate ephemeral and encrypt
    from cipherguard.crypto.secure_channel import KeyPair, SecureChannel
    ephemeral = KeyPair.generate()
    session_key = SecureChannel.derive_session_key(ephemeral.private_key, cloud_pub)
    enc = SecureChannel.encrypt(req.plaintext.encode(), session_key)
    # Store session key keyed by ephemeral_public for decrypt demo (in real world cloud would derive via its private key)
    eph_pub_b64 = base64.b64encode(ephemeral.public_bytes_raw()).decode()
    # Also store under simple id
    _last_session_keys[eph_pub_b64] = session_key
    return {
        "ciphertext": enc["ciphertext"],
        "nonce": enc["nonce"],
        "tag": enc["tag"],
        "ephemeral_public": eph_pub_b64,
        "algorithm": "AES-256-GCM",
        "key_exchange": "ECDH P-256 + HKDF-SHA256",
        "note": "Ciphertext, nonce, tag are real values. Decrypt with /api/crypto/decrypt using the same ephemeral_public.",
    }

@app.post("/api/crypto/decrypt")
def crypto_decrypt(req: DecryptRequest):
    if not req.ciphertext or not req.nonce or not req.tag:
        raise HTTPException(status_code=400, detail="ciphertext, nonce, tag required")
    try:
        ct = base64.b64decode(req.ciphertext)
        nonce = base64.b64decode(req.nonce)
        tag = base64.b64decode(req.tag)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")

    # Derive session key: prefer stored ephemeral key, otherwise try ECDH with cloud private
    session_key = None
    if req.ephemeral_public and req.ephemeral_public in _last_session_keys:
        session_key = _last_session_keys[req.ephemeral_public]
    elif req.ephemeral_public:
        # Derive via cloud private key + ephemeral public (real ECDH)
        try:
            eph_pub_bytes = base64.b64decode(req.ephemeral_public)
            eph_pub = KeyPair.load_public_from_bytes(eph_pub_bytes)
            cloud_priv = get_cloud_keypair().private_key
            session_key = SecureChannel.derive_session_key(cloud_priv, eph_pub)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid ephemeral_public: {e}")
    else:
        raise HTTPException(status_code=400, detail="ephemeral_public required for decryption (ECDH)")

    try:
        pt = SecureChannel.decrypt(ct, nonce, tag, session_key)
        return {"plaintext": pt.decode(errors="replace"), "verified": True}
    except Exception as e:
        # AESGCM tag mismatch etc.
        raise HTTPException(status_code=400, detail=f"Decryption failed (tag verification or key mismatch): {e}")

@app.post("/api/crypto/encrypt-file")
async def encrypt_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    cloud_pub = get_cloud_public_key()
    from cipherguard.crypto.secure_channel import KeyPair, SecureChannel
    ephemeral = KeyPair.generate()
    session_key = SecureChannel.derive_session_key(ephemeral.private_key, cloud_pub)
    enc = SecureChannel.encrypt(content, session_key)
    eph_pub_b64 = base64.b64encode(ephemeral.public_bytes_raw()).decode()
    _last_session_keys[eph_pub_b64] = session_key
    return {
        "filename": file.filename,
        "ciphertext": enc["ciphertext"],
        "nonce": enc["nonce"],
        "tag": enc["tag"],
        "ephemeral_public": eph_pub_b64,
        "original_size": len(content),
        "encrypted_size": len(base64.b64decode(enc["ciphertext"])),
    }

# ---------- Frontend ----------
# Serve static
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

@app.get("/")
def index():
    idx = WEB_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return JSONResponse({"message": "CipherGuard Shield API. Frontend not found. See /docs"})

# Catch-all for frontend routes: serve index.html for SPA-like nav (but we have anchors)
@app.get("/{path:path}")
def catch_all(path: str):
    # If API path, let 404
    if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi"):
        raise HTTPException(status_code=404)
    idx = WEB_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    raise HTTPException(status_code=404)
