"""SentinelFlow Flask application: dashboard + REST API + monitoring orchestration."""

import collections
import json
import os
import sys
import threading
import time

import psutil
from flask import Flask, jsonify, render_template, request, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import (  # noqa: E402
    BASELINE_WINDOWS,
    DB_PATH,
    HOST,
    MONITOR_WINDOW_SECONDS,
    PORT,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    QUARANTINE_SECONDS,
)
from database.db import Database  # noqa: E402
from ml import model_loader  # noqa: E402
from monitoring.interface_manager import list_interfaces  # noqa: E402
from monitoring.packet_capture import MonitorEngine  # noqa: E402
from monitoring.simulator import TrafficSimulator  # noqa: E402
from security import detector, distributed_analysis, severity  # noqa: E402
from security.mitigation import MitigationManager  # noqa: E402

app = Flask(__name__, template_folder="templates", static_folder="static")

db = Database(DB_PATH)
mitigation = MitigationManager(db, quarantine_seconds=QUARANTINE_SECONDS)

baseline_rates = collections.deque(maxlen=BASELINE_WINDOWS)
consecutive_suspicious = 0
latest_detection = None
health_buffer = collections.deque(maxlen=120)
state_lock = threading.Lock()

monitor = MonitorEngine(on_window=None)
simulator = TrafficSimulator(on_window=None)


def _baseline():
    if not baseline_rates:
        return None
    vals = list(baseline_rates)
    return {"packet_rate": sum(vals) / len(vals), "windows": len(vals)}


def process_window(features: dict, context: dict, source: str, interface: str) -> dict:
    """Shared inference pipeline for live and simulated windows."""
    global consecutive_suspicious, latest_detection
    if context.get("error"):
        return {"error": context["error"]}
    try:
        ml_result = detector.detect(features)
    except FileNotFoundError as exc:
        return {"error": str(exc)}
    except ValueError as exc:
        return {"error": "Feature validation failed: %s" % exc}

    packet_rate = float(features.get("received_packets_per_second", 0.0)) + float(
        features.get("sent_packets_per_second", 0.0))
    dist = distributed_analysis.compute_distributed_risk(features, context, _baseline())
    baseline_rates.append(packet_rate)

    with state_lock:
        if ml_result["label"] == 1 or dist["distributed_risk_score"] >= 0.7:
            consecutive_suspicious += 1
        else:
            consecutive_suspicious = 0
        persistence = consecutive_suspicious

    sev = severity.assess_severity(ml_result["prediction"], ml_result["confidence"],
                                   features, dist, persistence)
    actions = mitigation.decide(sev["severity"], context,
                                "SentinelFlow %s window (%s)" % (ml_result["prediction"], source))
    mitigation_status = actions[0]["action"] if actions else "monitor"

    record = {
        "timestamp": time.time(),
        "interface": interface,
        "source": source,
        "prediction": ml_result["prediction"],
        "confidence": ml_result["confidence"],
        "severity": sev["severity"],
        "packet_rate": dist["packet_rate"],
        "byte_rate": dist["byte_rate"],
        "source_count": dist["unique_sources"],
        "destination_count": dist["unique_destinations"],
        "distributed_risk": dist["distributed_risk_score"],
        "mitigation_status": mitigation_status,
        "detail": {
            "features": features,
            "context": {k: v for k, v in context.items() if k != "simulated_attack_intended"},
            "distributed": dist,
            "severity": sev,
            "actions": actions,
        },
    }
    try:
        record_id = db.add_detection(record)
        record["id"] = record_id
    except Exception:
        record["id"] = None
    with state_lock:
        latest_detection = record
    return record


def _wire_callbacks():
    monitor.on_window = process_window
    simulator.on_window = process_window


_wire_callbacks()


def _health_sampler():
    prev_sent = prev_recv = None
    while True:
        try:
            cpu = float(psutil.cpu_percent(interval=None))
            mem = float(psutil.virtual_memory().percent)
            net = psutil.net_io_counters()
            sample = {
                "timestamp": time.time(),
                "cpu_percent": cpu,
                "memory_percent": mem,
                "bytes_sent": int(net.bytes_sent),
                "bytes_recv": int(net.bytes_recv),
                "packets_sent": int(getattr(net, "packets_sent", 0)),
                "packets_recv": int(getattr(net, "packets_recv", 0)),
            }
            with state_lock:
                health_buffer.append(sample)
            db.add_health(sample)
        except Exception as exc:
            # Best-effort background sampling: report and continue with the next sample.
            print("SentinelFlow health sample skipped: %s" % exc)
        time.sleep(5)


threading.Thread(target=_health_sampler, daemon=True).start()


# -- pages ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("dashboard.html", product=PRODUCT_NAME, tagline=PRODUCT_TAGLINE)


# -- APIs -------------------------------------------------------------
@app.route("/api/status")
def api_status():
    with state_lock:
        latest = dict(latest_detection) if latest_detection else None
    mitigation.get_active()
    return jsonify({
        "product": PRODUCT_NAME,
        "monitoring": monitor.running or simulator.running,
        "mode": ("simulation" if simulator.running else ("live" if monitor.running else "stopped")),
        "interface": simulator.running and "simulation" or monitor.interface,
        "window_seconds": simulator.window_seconds if simulator.running else monitor.window_seconds,
        "windows_completed": monitor.windows_completed + simulator.windows_completed,
        "model_trained": model_loader.is_trained(),
        "latest": latest,
        "active_mitigations": len(mitigation.get_active()),
        "capture_error": monitor.last_error,
    })


@app.route("/api/health")
def api_health():
    with state_lock:
        live = dict(health_buffer[-1]) if health_buffer else None
        recent = list(health_buffer)[-30:]
    history = db.get_health_history(limit=30)
    return jsonify({"current": live, "recent": recent, "history": history})


@app.route("/api/interfaces")
def api_interfaces():
    try:
        return jsonify({"interfaces": list_interfaces()})
    except Exception as exc:
        return jsonify({"error": "Interface discovery failed: %s" % exc}), 500


@app.route("/api/detections")
def api_detections():
    try:
        limit = max(min(int(request.args.get("limit", 50)), 500), 1)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid 'limit' parameter; expected an integer."}), 400
    try:
        rows = db.get_detections(limit=limit)
        for r in rows:
            try:
                r["detail"] = json.loads(r.get("detail_json", "{}"))
            except Exception:
                r["detail"] = {}
            r.pop("detail_json", None)
        return jsonify({
            "detections": rows,
            "by_prediction": db.count_by_prediction(),
            "by_severity": db.count_by_severity(),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/detections/latest")
def api_latest():
    with state_lock:
        latest = dict(latest_detection) if latest_detection else None
    if latest is None:
        try:
            rows = db.get_detections(limit=1)
            if rows:
                r = rows[0]
                try:
                    r["detail"] = json.loads(r.get("detail_json", "{}"))
                except Exception:
                    r["detail"] = {}
                r.pop("detail_json", None)
                latest = r
        except Exception as exc:
            print("SentinelFlow stored-detection fallback read failed: %s" % exc)
    if latest is None:
        return jsonify({"detection": None, "message": "No detections recorded yet."})
    return jsonify({"detection": latest})


@app.route("/api/mitigations")
def api_mitigations():
    try:
        active = mitigation.get_active()
        history = db.get_mitigations(limit=100)
        return jsonify({"active": active, "history": history,
                        "quarantine_seconds": mitigation.quarantine_seconds})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        return jsonify({
            "window_seconds": monitor.window_seconds or MONITOR_WINDOW_SECONDS,
            "quarantine_seconds": mitigation.quarantine_seconds,
            "interface": monitor.interface,
        })
    data = request.get_json(silent=True) or {}
    if "window_seconds" in data:
        try:
            w = int(data["window_seconds"])
            if w < 2 or w > 120:
                return jsonify({"error": "window_seconds must be between 2 and 120."}), 400
            monitor.window_seconds = w
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid window_seconds; expected an integer."}), 400
    if "quarantine_seconds" in data:
        try:
            q = int(data["quarantine_seconds"])
            if q < 5 or q > 3600:
                return jsonify({"error": "quarantine_seconds must be between 5 and 3600."}), 400
            mitigation.set_duration(q)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid quarantine_seconds; expected an integer."}), 400
    if "interface" in data and isinstance(data["interface"], str) and not (monitor.running or simulator.running):
        monitor.interface = data["interface"]
    return jsonify({"ok": True, "window_seconds": monitor.window_seconds,
                    "quarantine_seconds": mitigation.quarantine_seconds})


def _require_stopped():
    if monitor.running or simulator.running:
        return jsonify({"error": "Stop the current session before starting a new one."}), 409
    return None


@app.route("/api/monitor/start", methods=["POST"])
def api_monitor_start():
    busy = _require_stopped()
    if busy:
        return busy
    data = request.get_json(silent=True) or {}
    interface = str(data.get("interface", "") or "").strip()
    window = data.get("window_seconds", monitor.window_seconds or MONITOR_WINDOW_SECONDS)
    try:
        window = int(window)
        if window < 2 or window > 120:
            return jsonify({"error": "window_seconds must be between 2 and 120."}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid window_seconds; expected an integer."}), 400
    if not interface:
        ifaces = list_interfaces()
        interface = ifaces[0]["name"] if ifaces else "default"
    try:
        monitor.last_error = ""
        monitor.start_live(interface, window)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409
    except Exception as exc:
        return jsonify({"error": "Live capture could not start: %s" % exc}), 500
    return jsonify({"ok": True, "mode": "live", "interface": interface, "window_seconds": window})


@app.route("/api/monitor/stop", methods=["POST"])
def api_monitor_stop():
    monitor.stop()
    return jsonify({"ok": True})


@app.route("/api/demo/start", methods=["POST"])
def api_demo_start():
    busy = _require_stopped()
    if busy:
        return busy
    data = request.get_json(silent=True) or {}
    window = data.get("window_seconds", 5)
    try:
        window = int(window)
        if window < 2 or window > 120:
            return jsonify({"error": "window_seconds must be between 2 and 120."}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid window_seconds; expected an integer."}), 400
    try:
        simulator.start(window_seconds=window)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 409
    return jsonify({"ok": True, "mode": "simulation", "window_seconds": window})


@app.route("/api/demo/stop", methods=["POST"])
def api_demo_stop():
    simulator.stop()
    return jsonify({"ok": True})


@app.route("/api/model/metrics")
def api_metrics():
    metrics_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "metrics.json")
    if not os.path.exists(metrics_path):
        return jsonify({"trained": False, "message": "Model not trained yet. Run: python ml/train_model.py"})
    try:
        with open(metrics_path, "r", encoding="utf-8") as fh:
            metrics = json.load(fh)
        feat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "feature_importance.json")
        importance = {}
        if os.path.exists(feat_path):
            with open(feat_path, "r", encoding="utf-8") as fh:
                importance = json.load(fh)
        cm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "confusion_matrix.json")
        cm = None
        if os.path.exists(cm_path):
            with open(cm_path, "r", encoding="utf-8") as fh:
                cm = json.load(fh)
        return jsonify({"trained": True, "metrics": metrics,
                        "feature_importance": importance, "confusion_matrix": cm})
    except Exception as exc:
        return jsonify({"error": "Failed to read model metrics: %s" % exc}), 500


@app.route("/static/results/<path:filename>")
def static_results(filename):
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    return send_from_directory(results_dir, filename)


@app.errorhandler(404)
def _404(_exc):
    return jsonify({"error": "Unknown endpoint."}), 404


@app.errorhandler(500)
def _500(exc):
    return jsonify({"error": "Internal server error: %s" % exc}), 500


if __name__ == "__main__":
    print("Starting %s on http://%s:%d" % (PRODUCT_NAME, HOST, PORT))
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)
