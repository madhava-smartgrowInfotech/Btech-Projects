"""PhishGuard API server for the React frontend (port 8103).

A thin layer over the existing Flask app: it reuses `phishguard.webapp.create_app()`
unchanged (every original page and /api route keeps its behaviour) and only adds
a few read-only JSON endpoints the new UI needs, plus CORS headers.

    python backend/server.py            # serves on BACKEND_PORT from .env (default 8103)

Added endpoints (read-only):
    GET /api/health                 -> {ok, model_ready, model, model_version}
    GET /api/config                 -> thresholds + feature names by group
    GET /api/checks?limit=N         -> recent URL checks (ThreatIntel.recent_checks)
    GET /api/intel?limit=N&status=S -> threat-intel entries (ThreatIntel.recent)
    GET /api/intel/lookup?url=U     -> one entry with its latest reports (ThreatIntel.lookup)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import jsonify, request  # noqa: E402

from phishguard import config  # noqa: E402
from phishguard.detector import Detector  # noqa: E402
from phishguard.features import FEATURE_NAMES  # noqa: E402
from phishguard.threat_intel import ThreatIntel  # noqa: E402
from phishguard.webapp import create_app  # noqa: E402

# FEATURE_NAMES is ordered lexical (23) -> structural (9) -> domain (15), see features.py
FEATURE_GROUPS = {
    "lexical": FEATURE_NAMES[:23],
    "structural": FEATURE_NAMES[23:32],
    "domain": FEATURE_NAMES[32:],
}
STATUSES = {"pending", "confirmed_phishing", "confirmed_safe"}


def read_env(path: Path = ROOT / ".env") -> dict:
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _limit(default: int, cap: int = 500) -> int:
    try:
        return max(1, min(cap, int(request.args.get("limit", default))))
    except ValueError:
        return default


def build_app(ti: ThreatIntel | None = None, detector: Detector | None = None):
    ti = ti or ThreatIntel()
    det = detector or Detector(ti)
    app = create_app(ti, det)

    @app.after_request
    def cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return resp

    @app.get("/api/health")
    def api_health():
        return jsonify({"ok": True, "model_ready": det.ready, "model": det.model_name,
                        "model_version": det.model_version})

    @app.get("/api/config")
    def api_config():
        return jsonify({
            "consensus_threshold": config.CONSENSUS_THRESHOLD,
            "auto_retrain_every": config.AUTO_RETRAIN_EVERY,
            "crowd_sample_weight": config.CROWD_SAMPLE_WEIGHT,
            "phishing_threshold": config.PHISHING_THRESHOLD,
            "suspicious_threshold": config.SUSPICIOUS_THRESHOLD,
            "threat_feeds": list(config.THREAT_FEEDS),
            "feature_count": len(FEATURE_NAMES),
            "feature_groups": FEATURE_GROUPS,
        })

    @app.get("/api/checks")
    def api_checks():
        return jsonify(ti.recent_checks(_limit(20)))

    @app.get("/api/intel")
    def api_intel():
        status = request.args.get("status") or None
        if status and status not in STATUSES:
            return jsonify({"error": f"unknown status '{status}'"}), 400
        return jsonify(ti.recent(_limit(200), status))

    @app.get("/api/intel/lookup")
    def api_intel_lookup():
        url = request.args.get("url", "").strip()
        if not url:
            return jsonify({"error": "Please enter a URL."}), 400
        return jsonify({"entry": ti.lookup(url)})

    return app


if __name__ == "__main__":
    env = read_env()
    port = int(os.environ.get("BACKEND_PORT") or env.get("BACKEND_PORT") or 8103)
    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    print(f"PhishGuard API -> http://{host}:{port}")
    build_app().run(host=host, port=port, threaded=True)
