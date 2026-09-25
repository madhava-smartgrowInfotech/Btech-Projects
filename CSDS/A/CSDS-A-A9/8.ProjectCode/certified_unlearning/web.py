"""Localhost web application implemented with Python's standard library."""

from __future__ import annotations

import json
import threading
import webbrowser
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .engine import FederatedUnlearningEngine


PAGE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Certified Federated Unlearning Lab</title>
  <style>
    :root{--navy:#111d36;--blue:#2563eb;--cyan:#0891b2;--ink:#172033;--muted:#667085;--line:#e3e8f0;--bg:#f3f6fb;--ok:#16803c;--bad:#b42318}
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
    header{background:linear-gradient(120deg,var(--navy),#243b67);color:white;padding:30px max(24px,calc((100vw - 1180px)/2));box-shadow:0 8px 30px #14213d22}
    header h1{font-size:clamp(24px,3vw,36px);margin:0 0 7px;letter-spacing:-.8px} header p{margin:0;color:#cbd7ef}
    main{max-width:1180px;margin:0 auto;padding:25px 20px 50px}.nav{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px}
    .nav button{background:transparent;color:#46536b}.nav button.active{background:white;color:var(--blue);box-shadow:0 5px 20px #16213e12}
    button{border:0;border-radius:9px;padding:10px 15px;font-weight:700;cursor:pointer;font-size:14px;transition:.15s}button:hover{transform:translateY(-1px)}
    button.primary{background:var(--blue);color:white}button.secondary{background:#e8eef9;color:#263857}button.danger{background:#fff0ef;color:var(--bad)}button:disabled{opacity:.45;cursor:not-allowed;transform:none}
    .panel{display:none}.panel.active{display:block}.card{background:white;border:1px solid var(--line);border-radius:14px;padding:19px;box-shadow:0 5px 18px #14213d0a}
    .topline{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:17px}.topline h2{margin:0 0 5px;font-size:21px}.topline p{margin:0;color:var(--muted);font-size:14px}
    .actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}
    .metric{background:white;border:1px solid var(--line);border-radius:13px;padding:16px}.metric b{font-size:26px;color:var(--navy);display:block}.metric span{font-size:11px;letter-spacing:.7px;color:var(--muted);font-weight:700}
    table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;color:var(--muted);font-size:11px;letter-spacing:.6px;text-transform:uppercase;background:#f8fafc}th,td{padding:12px;border-bottom:1px solid var(--line)}
    .pill{padding:4px 9px;border-radius:99px;font-size:12px;font-weight:700}.active-pill{color:var(--ok);background:#eaf8ef}.removed-pill{color:var(--bad);background:#fff0ef}.waiting-pill{color:#805d0b;background:#fff7d6}
    select,input{border:1px solid #ccd4e1;border-radius:8px;padding:10px 12px;font-size:14px;background:white;color:var(--ink)}select{min-width:260px}
    pre{white-space:pre-wrap;word-break:break-word;background:#101827;color:#d9e5f7;border-radius:12px;padding:18px;min-height:180px;line-height:1.55;overflow:auto}
    .certificate{display:grid;grid-template-columns:1fr 1fr;gap:12px}.cert-box{border:1px solid var(--line);border-radius:10px;padding:13px}.cert-box label{display:block;color:var(--muted);font-size:11px;text-transform:uppercase}.cert-box strong{font-size:16px}.full{grid-column:1/-1}
    .status{position:fixed;right:20px;bottom:18px;max-width:470px;background:var(--navy);color:white;padding:12px 16px;border-radius:10px;box-shadow:0 8px 30px #0003;opacity:0;transform:translateY(12px);pointer-events:none;transition:.2s}.status.show{opacity:1;transform:none}.status.error{background:var(--bad)}
    .empty{text-align:center;padding:45px;color:var(--muted)}.hash{font-family:ui-monospace,monospace;font-size:12px}.audit-ok{color:var(--ok);font-weight:700}.audit-bad{color:var(--bad);font-weight:700}
    @media(max-width:760px){.metrics{grid-template-columns:1fr 1fr}.certificate{grid-template-columns:1fr}.topline{flex-direction:column}table{display:block;overflow:auto}.full{grid-column:auto}}
  </style>
</head>
<body>
<header><h1>Certified Federated Unlearning Lab</h1><p>Privacy-preserving client removal · differential-privacy bounds · verifiable compliance</p></header>
<main>
  <nav class="nav">
    <button class="active" data-tab="training">Federated Training</button>
    <button data-tab="unlearning">Certified Unlearning</button>
    <button data-tab="explorer">Model Explorer</button>
    <button data-tab="audit">Compliance Audit</button>
  </nav>

  <section id="training" class="panel active">
    <div class="topline"><div><h2>Federated training overview</h2><p>Raw records remain in client datasets; only clipped updates enter the noisy aggregate.</p></div><div class="actions"><button class="secondary" onclick="newSession()">New session</button><button class="primary" id="trainBtn" onclick="train()">Train global model</button></div></div>
    <div class="metrics">
      <div class="metric"><b id="mClients">—</b><span>ACTIVE CLIENTS</span></div><div class="metric"><b id="mEpsilon">—</b><span>DP EPSILON</span></div><div class="metric"><b id="mPerplexity">—</b><span>PERPLEXITY</span></div><div class="metric"><b id="mAccuracy">—</b><span>NEXT-CHAR ACCURACY</span></div>
    </div>
    <div class="card"><table><thead><tr><th>Client</th><th>Domain</th><th>Records</th><th>Clipped L2</th><th>Clip scale</th><th>State</th></tr></thead><tbody id="clientRows"></tbody></table></div>
  </section>

  <section id="unlearning" class="panel">
    <div class="topline"><div><h2>Right-to-be-forgotten request</h2><p>Remove an active client's tracked update and independently verify the retained model.</p></div><div class="actions"><select id="clientSelect"></select><button class="primary" id="unlearnBtn" onclick="unlearn()" disabled>Execute &amp; certify</button></div></div>
    <div class="card" id="certificate"><div class="empty">A verification certificate will appear here after unlearning.</div></div>
  </section>

  <section id="explorer" class="panel">
    <div class="topline"><div><h2>Model explorer</h2><p>Sample the current character language model before and after an unlearning request.</p></div><div class="actions"><input id="seed" value="privacy" aria-label="Seed text"><button class="primary" id="generateBtn" onclick="generateText()" disabled>Generate sample</button></div></div>
    <pre id="sample">Train the global model to enable generation.</pre>
    <div class="card"><b>Method notes</b><p>Every client update is L2-clipped. Gaussian noise provides the displayed one-shot (ε, δ) release bound. Unlearning subtracts the tracked parameter update, renormalizes retained clients, compares with a clean retained-only recomputation, evaluates a loss-based membership attack, and records the result.</p></div>
  </section>

  <section id="audit" class="panel">
    <div class="topline"><div><h2>Compliance audit ledger</h2><p>Training and deletion events are linked to their predecessor using SHA-256.</p></div><div class="actions"><span id="auditState"></span><button class="secondary" onclick="verifyAudit()">Verify hash chain</button></div></div>
    <div class="card"><table><thead><tr><th>#</th><th>Event</th><th>Time (UTC)</th><th>Client</th><th>Status</th><th>Record hash</th></tr></thead><tbody id="auditRows"></tbody></table></div>
  </section>
</main><div id="toast" class="status"></div>
<script>
let state={};
const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const n=(v,d=3)=>Number(v).toFixed(d);
document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav button,.panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')});
function toast(message,error=false){const e=document.getElementById('toast');e.textContent=message;e.className='status show'+(error?' error':'');setTimeout(()=>e.className='status',3500)}
async function api(path,method='GET',body=null){const options={method,headers:{'Content-Type':'application/json'}};if(body)options.body=JSON.stringify(body);const response=await fetch(path,options);const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data}
async function refresh(){state=await api('/api/state');render()}
function render(){
  const m=state.metrics;document.getElementById('mClients').textContent=m?m.active_clients:'—';document.getElementById('mEpsilon').textContent=m?n(m.epsilon):'—';document.getElementById('mPerplexity').textContent=m?n(m.perplexity,2):'—';document.getElementById('mAccuracy').textContent=m?n(m.next_character_accuracy*100,1)+'%':'—';
  document.getElementById('clientRows').innerHTML=state.contributions.map(c=>`<tr><td><b>${esc(c.display_name)}</b></td><td>${esc(c.domain)}</td><td>${c.record_count}</td><td>${state.trained?n(c.clipped_norm):'—'}</td><td>${state.trained?n(c.clip_scale):'—'}</td><td><span class="pill ${!state.trained?'waiting-pill':c.active?'active-pill':'removed-pill'}">${!state.trained?'Not trained':c.active?'Active':'Removed'}</span></td></tr>`).join('');
  const select=document.getElementById('clientSelect');const previous=select.value;select.innerHTML=state.active_clients.map(c=>`<option value="${esc(c.client_id)}">${esc(c.display_name)} — ${esc(c.domain)}</option>`).join('');if([...select.options].some(o=>o.value===previous))select.value=previous;
  document.getElementById('unlearnBtn').disabled=!state.trained||state.active_clients.length<=1;document.getElementById('generateBtn').disabled=!state.trained;
  if(state.latest_certificate)renderCertificate(state.latest_certificate);
  const audit=state.audit;document.getElementById('auditState').innerHTML=`<span class="${audit.valid?'audit-ok':'audit-bad'}">${esc(audit.detail)}</span>`;
  document.getElementById('auditRows').innerHTML=audit.records.length?audit.records.map(r=>`<tr><td>${r.sequence}</td><td>${esc(r.event_type)}</td><td>${esc(r.timestamp_utc||r.issued_at_utc||'')}</td><td>${esc(r.client_id||'—')}</td><td>${esc(r.status||'—')}</td><td class="hash">${esc((r.record_hash||'').slice(0,24))}…</td></tr>`).join(''):'<tr><td colspan="6" class="empty">No audit events yet.</td></tr>';
}
function renderCertificate(c){document.getElementById('certificate').innerHTML=`<div class="topline"><div><span class="pill active-pill">${esc(c.status)}</span><h2>${esc(c.certificate_id)}</h2><p>${esc(c.client_name)} · ${esc(c.issued_at_utc)}</p></div><button class="secondary" onclick="location.href='/api/certificate/latest'">Download JSON</button></div><div class="certificate"><div class="cert-box"><label>Privacy guarantee</label><strong>ε ${n(c.epsilon,4)} · δ ${c.delta}</strong></div><div class="cert-box"><label>Utility retained</label><strong>${n(c.utility_retention_percent,2)}%</strong></div><div class="cert-box"><label>Residual influence L2</label><strong>${Number(c.residual_influence_l2).toExponential(3)}</strong></div><div class="cert-box"><label>Reference retrain L2</label><strong>${Number(c.reference_retrain_l2).toExponential(3)}</strong></div><div class="cert-box"><label>Membership AUC</label><strong>${n(c.membership_auc_before)} → ${n(c.membership_auc_after)}</strong></div><div class="cert-box"><label>Perplexity</label><strong>${n(c.perplexity_before)} → ${n(c.perplexity_after)}</strong></div><div class="cert-box full"><label>Audit record hash</label><strong class="hash">${esc(c.audit_record_hash)}</strong></div></div>`}
async function train(){busy('trainBtn',true);try{await api('/api/train','POST');await refresh();toast('Federated training completed')}catch(e){toast(e.message,true)}finally{busy('trainBtn',false)}}
async function newSession(){try{await api('/api/session','POST');await refresh();document.getElementById('certificate').innerHTML='<div class="empty">A verification certificate will appear here after unlearning.</div>';document.getElementById('sample').textContent='Train the global model to enable generation.';toast('New session created; audit history preserved')}catch(e){toast(e.message,true)}}
async function unlearn(){const id=document.getElementById('clientSelect').value;if(!id)return;busy('unlearnBtn',true);try{await api('/api/unlearn','POST',{client_id:id});await refresh();toast('Client contribution removed and certified')}catch(e){toast(e.message,true)}finally{busy('unlearnBtn',false)}}
async function generateText(){try{const x=await api('/api/generate','POST',{seed:document.getElementById('seed').value});document.getElementById('sample').textContent=x.text;toast('Sample generated')}catch(e){toast(e.message,true)}}
async function verifyAudit(){try{const x=await api('/api/audit/verify','POST');toast(x.detail,!x.valid);await refresh()}catch(e){toast(e.message,true)}}
function busy(id,on){const b=document.getElementById(id);b.disabled=on;if(on)b.dataset.old=b.textContent,b.textContent='Working…';else if(b.dataset.old)b.textContent=b.dataset.old}
refresh().catch(e=>toast(e.message,true));
</script></body></html>"""


class ApplicationState:
    def __init__(self, audit_path: str | Path) -> None:
        self.audit_path = Path(audit_path)
        self.engine = FederatedUnlearningEngine(audit_path=self.audit_path)
        self.lock = threading.RLock()

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            metrics = asdict(self.engine.metrics()) if self.engine.trained else None
            valid, detail = self.engine.audit.verify()
            active_clients = [
                {
                    "client_id": client_id,
                    "display_name": self.engine.clients[client_id].display_name,
                    "domain": self.engine.clients[client_id].domain,
                }
                for client_id in self.engine.active_client_ids
            ]
            return {
                "trained": self.engine.trained,
                "session_id": self.engine.session_id,
                "metrics": metrics,
                "contributions": [asdict(item) for item in self.engine.contributions()],
                "active_clients": active_clients,
                "latest_certificate": self.engine.certificates[-1].to_dict() if self.engine.certificates else None,
                "audit": {"valid": valid, "detail": detail, "records": self.engine.audit.read_all()},
            }


def make_handler(application: ApplicationState) -> type[BaseHTTPRequestHandler]:
    class RequestHandler(BaseHTTPRequestHandler):
        server_version = "CertifiedUnlearning/1.0"

        def log_message(self, format: str, *args: object) -> None:
            print(f"[localhost] {self.address_string()} - {format % args}")

        def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK, headers: dict[str, str] | None = None) -> None:
            encoded = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(encoded)

        def _body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise ValueError("Request body is too large")
            if not length:
                return {}
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            return payload

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                if path == "/":
                    encoded = PAGE.encode("utf-8")
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(encoded)
                elif path == "/api/state":
                    self._json(application.snapshot())
                elif path == "/api/health":
                    self._json({"status": "ok", "service": "certified-federated-unlearning"})
                elif path == "/api/certificate/latest":
                    with application.lock:
                        if not application.engine.certificates:
                            self._json({"error": "No certificate is available"}, HTTPStatus.NOT_FOUND)
                            return
                        certificate = application.engine.certificates[-1]
                        valid, detail = application.engine.audit.verify()
                        payload = {**certificate.to_dict(), "audit_valid": valid, "audit_verification": detail}
                        self._json(
                            payload,
                            headers={"Content-Disposition": f'attachment; filename="{certificate.certificate_id}.json"'},
                        )
                else:
                    self._json({"error": "Route not found"}, HTTPStatus.NOT_FOUND)
            except Exception as error:
                self._json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            try:
                body = self._body()
                with application.lock:
                    if path == "/api/train":
                        result = asdict(application.engine.train())
                    elif path == "/api/session":
                        application.engine = FederatedUnlearningEngine(audit_path=application.audit_path)
                        result = {"session_id": application.engine.session_id}
                    elif path == "/api/unlearn":
                        client_id = str(body.get("client_id", ""))
                        if not client_id:
                            raise ValueError("client_id is required")
                        result = application.engine.unlearn(client_id).to_dict()
                    elif path == "/api/generate":
                        result = {"text": application.engine.generate(str(body.get("seed", "privacy")), length=180)}
                    elif path == "/api/audit/verify":
                        valid, detail = application.engine.audit.verify()
                        result = {"valid": valid, "detail": detail}
                    else:
                        self._json({"error": "Route not found"}, HTTPStatus.NOT_FOUND)
                        return
                self._json(result)
            except (ValueError, KeyError, RuntimeError, json.JSONDecodeError) as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            except Exception as error:
                self._json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    return RequestHandler


def run_web(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False) -> None:
    """Start the local web application and serve until interrupted."""

    application = ApplicationState("data/audit_log.jsonl")
    server = ThreadingHTTPServer((host, port), make_handler(application))
    url = f"http://{host}:{port}"
    print(f"Certified Federated Unlearning Lab is running at {url}")
    print("Press Ctrl+C to stop the server.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()

