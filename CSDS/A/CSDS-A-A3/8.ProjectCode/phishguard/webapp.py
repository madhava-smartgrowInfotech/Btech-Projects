"""Objective 6 - real-time URL classification through a simple web interface.

Pages
    /            check a URL
    /report      submit a community report (phishing / safe)
    /community   crowdsourced threat-intelligence board
    /models      model comparison (accuracy, precision, recall, F1) + retrain
JSON API
    GET  /api/check?url=...
    POST /api/report   {"url": ..., "verdict": "phishing"|"safe", "reporter": ..., "note": ...}
    GET  /api/stats
    POST /api/retrain
    POST /api/sync
"""
from __future__ import annotations

import threading

from flask import (Flask, jsonify, redirect, render_template, request,
                   url_for)
from jinja2 import DictLoader

from . import config
from .detector import Detector
from .retrain import maybe_auto_retrain, retrain
from .threat_intel import ThreatIntel
from .train import load_metrics

# --------------------------------------------------------------------------- #
# Templates (kept in Python so the project stays single-language)
# --------------------------------------------------------------------------- #
BASE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}PhishGuard{% endblock %}</title>
<style>
:root{
  --ink:#1c2430; --ink-2:#4a5566; --line:#d9dee6; --paper:#f4f6f9; --panel:#ffffff;
  --safe:#1d7a4c; --safe-bg:#e3f3ea; --warn:#a8690f; --warn-bg:#fbefd6;
  --bad:#b3261e; --bad-bg:#fbe4e2; --blue:#2b4c9b; --blue-bg:#e6ecf9;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.55 "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--blue)}
header{background:var(--ink);color:#fff}
.nav{max-width:1040px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:26px;flex-wrap:wrap}
.brand{font-weight:700;font-size:19px;letter-spacing:.2px;color:#fff;text-decoration:none}
.brand small{display:block;font-weight:400;font-size:12px;opacity:.7}
.nav a.link{color:#c9d3e3;text-decoration:none;font-size:15px}
.nav a.link.active,.nav a.link:hover{color:#fff;border-bottom:2px solid #fff}
main{max-width:1040px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:30px;margin:0 0 6px;font-weight:700}
h2{font-size:20px;margin:26px 0 10px}
.lead{color:var(--ink-2);margin:0 0 22px;max-width:70ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px 22px;margin-bottom:18px}
form.check{display:flex;gap:10px;flex-wrap:wrap}
input[type=text],input[type=url],textarea,select{font:inherit;padding:12px 14px;border:1.5px solid var(--line);
  border-radius:8px;width:100%;background:#fff}
input:focus,textarea:focus,select:focus{outline:2px solid var(--blue);outline-offset:1px;border-color:var(--blue)}
form.check input[type=text]{flex:1 1 420px}
button,.btn{font:inherit;font-weight:600;padding:12px 20px;border-radius:8px;border:0;cursor:pointer;
  background:var(--ink);color:#fff;text-decoration:none;display:inline-block}
button.secondary,.btn.secondary{background:#fff;color:var(--ink);border:1.5px solid var(--line)}
button.danger{background:var(--bad)} button.ok{background:var(--safe)}
.verdict{border-radius:12px;padding:26px 28px;margin:0 0 18px;border:1px solid transparent}
.verdict.phishing{background:var(--bad-bg);border-color:#efb7b2}
.verdict.suspicious{background:var(--warn-bg);border-color:#efd39b}
.verdict.safe{background:var(--safe-bg);border-color:#b6dfc5}
.verdict.unknown{background:#eee}
.verdict .word{font-size:44px;font-weight:800;line-height:1;margin:0 0 6px;letter-spacing:-.5px}
.verdict.phishing .word{color:var(--bad)} .verdict.suspicious .word{color:var(--warn)}
.verdict.safe .word{color:var(--safe)}
.verdict .url{word-break:break-all;font-family:Consolas,Menlo,monospace;font-size:15px;margin:0 0 10px}
.meter{height:12px;background:rgba(0,0,0,.08);border-radius:6px;overflow:hidden;margin:12px 0 6px}
.meter i{display:block;height:100%;background:linear-gradient(90deg,var(--safe),var(--warn) 45%,var(--bad))}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.stat b{display:block;font-size:26px;font-weight:700}
.stat span{color:var(--ink-2);font-size:14px}
table{width:100%;border-collapse:collapse;font-size:15px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--ink-2);font-size:13px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr.best td{background:var(--blue-bg);font-weight:600}
.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.tag.phishing,.tag.confirmed_phishing{background:var(--bad-bg);color:var(--bad)}
.tag.safe,.tag.confirmed_safe{background:var(--safe-bg);color:var(--safe)}
.tag.suspicious,.tag.pending{background:var(--warn-bg);color:var(--warn)}
.tag.ml,.tag.community,.tag.none{background:var(--blue-bg);color:var(--blue)}
ul.flags{margin:8px 0 0;padding-left:20px} ul.flags li{margin:3px 0}
.flash{padding:12px 16px;border-radius:8px;margin-bottom:16px;background:var(--blue-bg);color:var(--blue)}
.flash.err{background:var(--bad-bg);color:var(--bad)}
.muted{color:var(--ink-2);font-size:14px}
.row{display:flex;gap:14px;flex-wrap:wrap} .row>*{flex:1 1 300px}
label{font-weight:600;font-size:14px;display:block;margin:12px 0 6px}
details summary{cursor:pointer;font-weight:600}
code{font-family:Consolas,Menlo,monospace;font-size:14px;background:#eef1f5;padding:1px 5px;border-radius:4px}
.bar{height:8px;background:var(--blue);border-radius:4px}
footer{max-width:1040px;margin:0 auto;padding:0 20px 30px;color:var(--ink-2);font-size:13px}
@media (max-width:600px){.verdict .word{font-size:34px} h1{font-size:24px}}
</style>
</head>
<body>
<header><div class="nav">
  <a class="brand" href="{{ url_for('index') }}">PhishGuard<small>Dynamic phishing URL detection</small></a>
  <a class="link {{ 'active' if page=='index' }}" href="{{ url_for('index') }}">Check URL</a>
  <a class="link {{ 'active' if page=='report' }}" href="{{ url_for('report') }}">Report</a>
  <a class="link {{ 'active' if page=='community' }}" href="{{ url_for('community') }}">Threat intelligence</a>
  <a class="link {{ 'active' if page=='models' }}" href="{{ url_for('models') }}">Models</a>
</div></header>
<main>
{% if msg %}<div class="flash {{ 'err' if err }}">{{ msg }}</div>{% endif %}
{% block body %}{% endblock %}
</main>
<footer>Batch A3 · CSE (Data Science) · Machine learning + crowdsourced threat intelligence · model {{ metrics.best_model|default('not trained')|replace('_',' ') }} v{{ metrics.model_version|default('-') }}</footer>
</body></html>"""

INDEX = r"""{% extends "base.html" %}{% block body %}
<h1>Is this link safe?</h1>
<p class="lead">Paste any URL. It is checked first against community-confirmed threat intelligence,
then scored by the best of three trained classifiers using lexical, structural and domain features.</p>
<div class="panel">
<form class="check" method="post" action="{{ url_for('index') }}">
  <input type="text" name="url" placeholder="e.g. http://paypal-secure-login.verify-account.tk/signin" value="{{ url or '' }}" required autofocus>
  <button type="submit">Check</button>
</form>
</div>
{% if r %}
<div class="verdict {{ r.verdict }}">
  <p class="word">{{ {'phishing':'Phishing','suspicious':'Suspicious','safe':'Looks safe','unknown':'Unknown'}[r.verdict] }}</p>
  <p class="url">{{ r.normalized_url }}</p>
  <p>{{ r.reason }}</p>
  {% if r.probability is not none %}
  <div class="meter"><i style="width:{{ (r.probability*100)|round(1) }}%"></i></div>
  <p class="muted">Phishing probability {{ (r.probability*100)|round(1) }}% ·
    decided by <span class="tag {{ r.decided_by }}">{{ r.decided_by }}</span>
    {% if r.ml_probability is not none %} · raw model score {{ (r.ml_probability*100)|round(1) }}%{% endif %}</p>
  {% endif %}
  {% if r.red_flags %}<strong>Red flags</strong><ul class="flags">{% for f in r.red_flags %}<li>{{ f }}</li>{% endfor %}</ul>{% endif %}
  <p style="margin:16px 0 0">
    <a class="btn secondary" href="{{ url_for('report', url=r.normalized_url, verdict='phishing') }}">Report as phishing</a>
    <a class="btn secondary" href="{{ url_for('report', url=r.normalized_url, verdict='safe') }}">Report as safe</a>
  </p>
</div>
<div class="panel"><details><summary>Extracted features ({{ r.features|length }})</summary>
<table style="margin-top:10px"><thead><tr><th>Feature</th><th class="num">Value</th></tr></thead><tbody>
{% for k,v in r.features.items() %}<tr><td><code>{{ k }}</code></td><td class="num">{{ v }}</td></tr>{% endfor %}
</tbody></table></details></div>
{% endif %}
<div class="grid">
  <div class="stat"><b>{{ stats.checks }}</b><span>URLs checked</span></div>
  <div class="stat"><b>{{ stats.confirmed_phishing }}</b><span>community-confirmed phishing URLs</span></div>
  <div class="stat"><b>{{ stats.reports }}</b><span>community reports</span></div>
  <div class="stat"><b>{{ (metrics.models[metrics.best_model].f1*100)|round(2) if metrics else '-' }}%</b><span>F1 of active model ({{ metrics.best_model|default('-')|replace('_',' ') }})</span></div>
</div>
{% if checks %}
<h2>Recent checks</h2>
<div class="panel"><table><thead><tr><th>URL</th><th>Verdict</th><th class="num">Probability</th><th>Decided by</th></tr></thead><tbody>
{% for c in checks %}<tr><td style="word-break:break-all"><a href="{{ url_for('index', url=c.url) }}">{{ c.url[:90] }}</a></td>
<td><span class="tag {{ c.verdict }}">{{ c.verdict }}</span></td>
<td class="num">{{ (c.probability*100)|round(1) if c.probability is not none else '-' }}%</td><td>{{ c.decided_by }}</td></tr>{% endfor %}
</tbody></table></div>
{% endif %}
{% endblock %}"""

REPORT = r"""{% extends "base.html" %}{% block body %}
<h1>Report a URL</h1>
<p class="lead">Crowdsourced reports keep the system current with newly created phishing sites.
A URL is confirmed once {{ threshold }} more people agree than disagree; confirmed URLs override the model instantly
and are folded into the next retraining.</p>
<div class="panel">
<form method="post" action="{{ url_for('report') }}">
  <label for="url">URL</label>
  <input type="text" id="url" name="url" value="{{ url or '' }}" required>
  <div class="row">
    <div><label for="verdict">Your verdict</label>
      <select id="verdict" name="verdict">
        <option value="phishing" {{ 'selected' if verdict=='phishing' }}>Phishing / malicious</option>
        <option value="safe" {{ 'selected' if verdict=='safe' }}>Safe / legitimate (false positive)</option>
      </select></div>
    <div><label for="reporter">Your name or handle (optional)</label>
      <input type="text" id="reporter" name="reporter" placeholder="anonymous"></div>
  </div>
  <label for="note">What did you see? (optional)</label>
  <textarea id="note" name="note" rows="3" placeholder="e.g. fake bank login page asking for OTP"></textarea>
  <p style="margin-top:16px"><button type="submit">Submit report</button>
  <a class="btn secondary" href="{{ url_for('index') }}">Cancel</a></p>
</form>
</div>
{% endblock %}"""

COMMUNITY = r"""{% extends "base.html" %}{% block body %}
<h1>Crowdsourced threat intelligence</h1>
<p class="lead">Every reported URL, its vote tally and consensus status. Confirmed entries are
used to retrain the model; {{ stats.awaiting_training }} are waiting for the next retrain
(automatic after {{ auto_every }} new confirmations).</p>
<div class="grid">
  <div class="stat"><b>{{ stats.urls_tracked }}</b><span>URLs tracked</span></div>
  <div class="stat"><b>{{ stats.confirmed_phishing }}</b><span>confirmed phishing</span></div>
  <div class="stat"><b>{{ stats.confirmed_safe }}</b><span>confirmed safe</span></div>
  <div class="stat"><b>{{ stats.pending }}</b><span>pending consensus</span></div>
</div>
<div class="panel" style="margin-top:18px">
<form method="post" action="{{ url_for('sync') }}" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
  <span>Pull the latest URLs from public feeds (OpenPhish, URLhaus) as trusted reports.</span>
  <button type="submit" class="secondary">Sync feeds</button>
</form>
</div>
<div class="panel"><table><thead><tr><th>URL</th><th>Status</th><th class="num">Phishing</th><th class="num">Safe</th><th>Source</th><th>Updated</th><th></th></tr></thead><tbody>
{% for e in entries %}<tr>
<td style="word-break:break-all"><a href="{{ url_for('index', url=e.url_norm) }}">{{ e.url_norm[:80] }}</a></td>
<td><span class="tag {{ e.status }}">{{ e.status|replace('_',' ') }}</span></td>
<td class="num">{{ e.phishing_votes }}</td><td class="num">{{ e.safe_votes }}</td>
<td>{{ e.source }}</td><td class="muted">{{ e.last_updated[:16]|replace('T',' ') }}</td>
<td style="white-space:nowrap"><a href="{{ url_for('report', url=e.url_norm, verdict='phishing') }}">+phish</a> ·
<a href="{{ url_for('report', url=e.url_norm, verdict='safe') }}">+safe</a></td>
</tr>{% else %}<tr><td colspan="7" class="muted">No reports yet. Check a URL and report it, or sync the public feeds.</td></tr>{% endfor %}
</tbody></table></div>
{% endblock %}"""

MODELS = r"""{% extends "base.html" %}{% block body %}
<h1>Model comparison</h1>
{% if not metrics %}
<div class="panel">No model has been trained yet. Run <code>python run.py train</code>.</div>
{% else %}
<p class="lead">Random Forest, XGBoost and Logistic Regression trained on the same
{{ metrics.n_features }} features ({{ metrics.train_rows }} training / {{ metrics.test_rows }} test URLs
{% if metrics.crowd_rows %}, including {{ metrics.crowd_rows }} community-confirmed URLs weighted x{{ metrics.crowd_weight }}{% endif %}).
Best model by F1: <strong>{{ metrics.best_model|replace('_',' ') }}</strong>, version {{ metrics.model_version }},
trained {{ metrics.trained_at[:16]|replace('T',' ') }} UTC.</p>
<div class="panel"><table>
<thead><tr><th>Model</th><th class="num">Accuracy</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">F1-score</th><th class="num">ROC-AUC</th><th class="num">False-positive rate</th><th class="num">Train time</th></tr></thead>
<tbody>{% for name,m in metrics.models.items() %}
<tr class="{{ 'best' if name==metrics.best_model }}"><td>{{ name|replace('_',' ')|title }}</td>
<td class="num">{{ (m.accuracy*100)|round(2) }}%</td><td class="num">{{ (m.precision*100)|round(2) }}%</td>
<td class="num">{{ (m.recall*100)|round(2) }}%</td><td class="num">{{ (m.f1*100)|round(2) }}%</td>
<td class="num">{{ m.roc_auc }}</td><td class="num">{{ (m.false_positive_rate*100)|round(2) }}%</td>
<td class="num">{{ m.train_seconds }}s</td></tr>{% endfor %}
</tbody></table></div>
<div class="row">
{% for name,m in metrics.models.items() %}
<div class="panel"><h2 style="margin-top:0">{{ name|replace('_',' ')|title }}</h2>
<p class="muted">Confusion matrix (test set): TP {{ m.confusion_matrix.tp }} · TN {{ m.confusion_matrix.tn }} · FP {{ m.confusion_matrix.fp }} · FN {{ m.confusion_matrix.fn }}</p>
<table><tbody>{% for f in m.top_features[:10] %}
<tr><td><code>{{ f.feature }}</code></td><td style="width:45%"><div class="bar" style="width:{{ (f.importance / m.top_features[0].importance * 100)|round(0) }}%"></div></td><td class="num">{{ f.importance }}</td></tr>
{% endfor %}</tbody></table></div>
{% endfor %}
</div>
{% endif %}
<div class="panel">
<form method="post" action="{{ url_for('retrain_route') }}" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
  <span>Retrain all three models on the base dataset plus {{ stats.confirmed_phishing + stats.confirmed_safe }} community-confirmed URLs
  ({{ stats.awaiting_training }} not yet used). Takes about a minute.</span>
  <button type="submit">Retrain now</button>
</form>
</div>
{% endblock %}"""


# --------------------------------------------------------------------------- #
# App factory
# --------------------------------------------------------------------------- #
def create_app(ti: ThreatIntel | None = None, detector: Detector | None = None) -> Flask:
    app = Flask(__name__)
    app.jinja_loader = DictLoader({"base.html": BASE, "index.html": INDEX, "report.html": REPORT,
                                   "community.html": COMMUNITY, "models.html": MODELS})
    ti = ti or ThreatIntel()
    det = detector or Detector(ti)
    state = {"retraining": False}

    def ctx(page, **kw):
        return dict(page=page, metrics=load_metrics(), stats=ti.stats(), **kw)

    # ---- pages -----------------------------------------------------------
    @app.route("/", methods=["GET", "POST"])
    def index():
        url = request.form.get("url") if request.method == "POST" else request.args.get("url")
        r = msg = None
        err = False
        if url:
            try:
                r = det.check(url)
            except Exception as exc:  # noqa: BLE001
                msg, err = f"Could not check that URL: {exc}", True
        return render_template("index.html", **ctx("index", url=url, r=r, msg=msg, err=err,
                                                    checks=ti.recent_checks(12)))

    @app.route("/report", methods=["GET", "POST"])
    def report():
        if request.method == "POST":
            try:
                entry = ti.report(request.form["url"], request.form["verdict"],
                                  request.form.get("reporter") or "anonymous",
                                  request.form.get("note", ""))
                if maybe_auto_retrain(ti, det):
                    state["retraining"] = True
                return redirect(url_for("index", url=entry["url_norm"]))
            except Exception as exc:  # noqa: BLE001
                return render_template("report.html", **ctx(
                    "report", url=request.form.get("url"), verdict=request.form.get("verdict"),
                    threshold=config.CONSENSUS_THRESHOLD, msg=str(exc), err=True))
        return render_template("report.html", **ctx(
            "report", url=request.args.get("url", ""), verdict=request.args.get("verdict", "phishing"),
            threshold=config.CONSENSUS_THRESHOLD))

    @app.route("/community")
    def community():
        return render_template("community.html", **ctx(
            "community", entries=ti.recent(200), auto_every=config.AUTO_RETRAIN_EVERY,
            msg=request.args.get("msg")))

    @app.route("/models")
    def models():
        return render_template("models.html", **ctx("models", msg=request.args.get("msg")))

    @app.route("/retrain", methods=["POST"])
    def retrain_route():
        def job():
            retrain(ti, verbose=False)
            det.reload()
            state["retraining"] = False
        state["retraining"] = True
        threading.Thread(target=job, daemon=True).start()
        return redirect(url_for("models", msg="Retraining started in the background - refresh in a minute."))

    @app.route("/sync", methods=["POST"])
    def sync():
        out = ti.sync_feeds()
        parts = [f"{k}: {'+%d URLs' % v['added'] if v['ok'] else 'failed (' + v['error'][:60] + ')'}"
                 for k, v in out.items()]
        maybe_auto_retrain(ti, det)
        return redirect(url_for("community", msg="Feed sync - " + "; ".join(parts)))

    # ---- JSON API --------------------------------------------------------
    @app.get("/api/check")
    def api_check():
        url = request.args.get("url", "")
        try:
            return jsonify(det.check(url))
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/report")
    def api_report():
        body = request.get_json(silent=True) or request.form
        try:
            entry = ti.report(body.get("url", ""), body.get("verdict", ""),
                              body.get("reporter", "anonymous"), body.get("note", ""))
            maybe_auto_retrain(ti, det)
            entry.pop("reports", None)
            return jsonify(entry)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/stats")
    def api_stats():
        return jsonify({"threat_intel": ti.stats(), "metrics": load_metrics(),
                        "retraining": state["retraining"]})

    @app.post("/api/retrain")
    def api_retrain():
        summary = retrain(ti, verbose=False)
        det.reload()
        return jsonify(summary)

    @app.post("/api/sync")
    def api_sync():
        return jsonify(ti.sync_feeds())

    return app
