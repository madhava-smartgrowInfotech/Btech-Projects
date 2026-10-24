/* SentinelFlow dashboard client (vanilla JS, Chart.js with graceful fallback). */
const $ = (id) => document.getElementById(id);
let charts = {};
let detectionsCache = [];

function fmt(n, d = 1) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: d });
}
function timeStr(ts) {
  try { return new Date(ts * 1000).toLocaleTimeString(); } catch (e) { return "—"; }
}
const chartsAvailable = () => typeof window.Chart !== "undefined";

function makeChart(id, cfg) {
  if (!chartsAvailable()) return null;
  try {
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart($(id), cfg);
    return charts[id];
  } catch (e) { return null; }
}

async function api(path, opts) {
  const r = await fetch(path, opts);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || ("Request failed: " + path));
  return j;
}

async function loadInterfaces() {
  try {
    const j = await api("/api/interfaces");
    const sel = $("ifaceSelect");
    sel.innerHTML = "";
    (j.interfaces || []).forEach((i) => {
      const o = document.createElement("option");
      o.value = i.name; o.textContent = i.display || i.name;
      sel.appendChild(o);
    });
  } catch (e) { /* leave empty */ }
}

async function refreshStatus() {
  try {
    const s = await api("/api/status");
    const pill = $("statusPill");
    const mode = s.mode || "stopped";
    pill.textContent = mode === "live" ? "Live Capture" : mode === "simulation" ? "Simulation Mode" : "Stopped";
    pill.className = "pill " + (mode === "live" ? "live" : mode === "simulation" ? "simulation" : "stopped");
    $("modeNote").textContent = mode === "live" ? "Live Capture from " + (s.interface || "") : mode === "simulation" ? "Simulation Mode — synthetic input, real inference" : "Monitoring stopped";
    $("cMode").textContent = "Mode: " + mode;
    $("cMit").textContent = s.active_mitigations ?? 0;
    const l = s.latest;
    if (l) {
      $("cStatus").textContent = l.prediction;
      $("cStatus").className = "big " + (l.prediction === "Attack" ? "pred-Attack" : "pred-Benign");
      $("cSource").textContent = (l.source || "") + " · " + timeStr(l.timestamp);
      $("cSeverity").textContent = l.severity || "—";
      $("cConf").textContent = ((l.confidence || 0) * 100).toFixed(1) + "%";
      $("cPps").textContent = fmt(l.packet_rate);
      $("cBps").textContent = fmt(l.byte_rate) + " bytes/sec";
      $("cSrc").textContent = l.source_count ?? "—";
      $("cDst").textContent = "dst " + (l.destination_count ?? "—");
      const d = l.detail || {};
      $("cRisk").textContent = "Distributed risk: " + (d.distributed ? d.distributed.distributed_risk_score + " (" + d.distributed.distributed_risk_level + ")" : "—");
    }
  } catch (e) { /* keep old values */ }
}

async function refreshHealth() {
  try {
    const h = await api("/api/health");
    const cur = h.current;
    if (cur) {
      $("hCpu").textContent = fmt(cur.cpu_percent) + "%";
      $("hMem").textContent = fmt(cur.memory_percent) + "%";
      $("hIn").textContent = fmt(cur.bytes_recv, 0);
      $("hOut").textContent = fmt(cur.bytes_sent, 0);
    }
    const rows = h.recent && h.recent.length ? h.recent : (h.history || []);
    if (rows.length && chartsAvailable()) {
      const labels = rows.map((r) => timeStr(r.timestamp));
      makeChart("chHealth", { type: "line", data: { labels, datasets: [
        { label: "CPU %", data: rows.map((r) => r.cpu_percent), borderColor: "#2563eb", tension: 0.3, pointRadius: 0 },
        { label: "Memory %", data: rows.map((r) => r.memory_percent), borderColor: "#7c3aed", tension: 0.3, pointRadius: 0 }] },
        options: { responsive: true, plugins: { legend: { position: "bottom" } } } });
      makeChart("chTraffic", { type: "line", data: { labels, datasets: [
        { label: "Bytes in", data: rows.map((r) => r.bytes_recv), borderColor: "#16a34a", tension: 0.3, pointRadius: 0 },
        { label: "Bytes out", data: rows.map((r) => r.bytes_sent), borderColor: "#d97706", tension: 0.3, pointRadius: 0 }] },
        options: { responsive: true, plugins: { legend: { position: "bottom" } } } });
    }
  } catch (e) { /* ignore */ }
}

async function refreshDetections() {
  try {
    const j = await api("/api/detections?limit=50");
    const rows = j.detections || [];
    detectionsCache = rows;
    const tb = document.querySelector("#detTable tbody");
    tb.innerHTML = "";
    rows.slice(0, 25).forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td>" + timeStr(r.timestamp) + "</td><td>" + (r.interface || "") + "</td><td>" + (r.source || "") + "</td>" +
        "<td class='pred-" + r.prediction + "'>" + r.prediction + "</td><td>" + ((r.confidence || 0) * 100).toFixed(1) + "%</td>" +
        "<td><span class='sev-" + r.severity + "'>" + r.severity + "</span></td><td>" + r.source_count + "</td><td>" + r.destination_count + "</td>" +
        "<td>" + fmt(r.packet_rate, 0) + "</td><td>" + (r.mitigation_status || "") + "</td>";
      tr.onclick = () => showDetail(r.id);
      tr.dataset.id = r.id;
      tb.appendChild(tr);
    });
    const bp = j.by_prediction || {};
    const bs = j.by_severity || {};
    if (!chartsAvailable()) {
      $("cdnHint").hidden = false;
      $("numSummary").textContent = "Benign=" + (bp.Benign || 0) + ", Attack=" + (bp.Attack || 0) + ".";
    } else {
      makeChart("chPred", { type: "doughnut", data: { labels: ["Benign", "Attack"], datasets: [{ data: [bp.Benign || 0, bp.Attack || 0], backgroundColor: ["#16a34a", "#dc2626"] }] }, options: { responsive: true } });
      makeChart("chSev", { type: "bar", data: { labels: ["Low", "Medium", "High", "Critical"], datasets: [{ label: "Detections", data: ["Low", "Medium", "High", "Critical"].map((k) => bs[k] || 0), backgroundColor: "#2563eb" }] }, options: { responsive: true, plugins: { legend: { display: false } } } });
    }
  } catch (e) { /* ignore */ }
}

function showDetail(id) {
  const r = detectionsCache.find((x) => String(x.id) === String(id));
  if (!r) return;
  const d = r.detail || {};
  const f = d.features || {}, dist = d.distributed || {}, sev = d.severity || {};
  let html = "<p><b>" + r.prediction + "</b> @ " + ((r.confidence || 0) * 100).toFixed(1) + "% confidence · severity <b>" + r.severity + "</b> (" + (sev.severity_score ?? "—") + ")</p>";
  html += "<p><b>Measured traffic:</b> " + fmt(r.packet_rate, 0) + " pkt/s, " + fmt(r.byte_rate, 0) + " bytes/s, " + r.source_count + " sources, " + r.destination_count + " destinations.</p>";
  if (dist.explanation) html += "<p><b>Distributed-traffic explanation:</b> " + dist.explanation + " (score " + dist.distributed_risk_score + ", " + dist.distributed_risk_level + ").</p>";
  if (sev.factors) html += "<p><b>Severity factors:</b><br>• " + sev.factors.join("<br>• ") + "</p>";
  if (sev.recommendation) html += "<p><b>Recommended mitigation:</b> " + sev.recommendation + "</p>";
  html += "<p><b>Mitigation status:</b> " + (r.mitigation_status || "—") + " · <b>Recovery:</b> quarantines auto-expire (default ~40 s).</p>";
  if (f.received_packets !== undefined) html += "<p><b>Model features:</b> <code>" + Object.entries(f).map(([k, v]) => k + "=" + fmt(v, 1)).join(", ") + "</code></p>";
  $("threatDetail").innerHTML = html;
}

async function refreshMitigations() {
  try {
    const j = await api("/api/mitigations");
    $("activeMit").innerHTML = (j.active || []).length ? (j.active || []).map((a) => "<div>• <b>" + a.ip + "</b> — " + a.reason + " (" + a.remaining_seconds + "s left)</div>").join("") : "None";
    $("histMit").innerHTML = (j.history || []).length ? j.history.slice(0, 30).map((h) => "<div>" + timeStr(h.timestamp) + " · " + h.ip + " · " + h.status + " · " + h.reason + "</div>").join("") : "None";
  } catch (e) { /* ignore */ }
}

async function refreshModel() {
  try {
    const j = await api("/api/model/metrics");
    if (!j.trained) { $("modelPerf").textContent = "Model not trained yet. Run: python ml/train_model.py"; return; }
    const m = j.metrics;
    $("modelPerf").innerHTML = "<p>Accuracy <b>" + (m.accuracy * 100).toFixed(2) + "%</b> · Precision <b>" + (m.precision * 100).toFixed(2) + "%</b> · Recall <b>" + (m.recall * 100).toFixed(2) + "%</b> · F1 <b>" + (m.f1 * 100).toFixed(2) + "%</b> · ROC-AUC <b>" + (m.roc_auc !== null && m.roc_auc !== undefined ? (m.roc_auc * 100).toFixed(2) + "%" : "n/a") + "</b> · test samples <b>" + m.test_samples + "</b></p>" +
      "<p class='hint'>Dataset: " + m.dataset_provenance + (m.is_synthetic ? " (synthetic input — metrics describe the fallback, not CICIDS2017 captures)" : "") + "</p>";
    const imp = j.feature_importance || {};
    const keys = Object.keys(imp);
    if (keys.length && chartsAvailable()) {
      // feature importance shown via server PNG; charts here focus on predictions
    }
    $("imgCm").src = "/static/results/confusion_matrix.png";
    $("imgRoc").src = "/static/results/roc_curve.png";
    $("imgFi").src = "/static/results/feature_importance.png";
  } catch (e) { $("modelPerf").textContent = "Model metrics unavailable."; }
}

async function tick() {
  await refreshStatus();
  await refreshHealth();
  await refreshDetections();
  await refreshMitigations();
}

$("btnLive").onclick = async () => {
  try { await api("/api/monitor/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ interface: $("ifaceSelect").value }) }); }
  catch (e) { alert("Live capture failed: " + e.message + "\nTip: use Start Simulation instead."); }
  tick();
};
$("btnDemo").onclick = async () => { try { await api("/api/demo/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ window_seconds: 5 }) }); } catch (e) { alert(e.message); } tick(); };
$("btnStop").onclick = async () => { try { await api("/api/monitor/stop", { method: "POST" }); } catch (e) {} try { await api("/api/demo/stop", { method: "POST" }); } catch (e) {} tick(); };
$("btnSettings").onclick = async () => {
  try {
    await api("/api/settings", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ window_seconds: parseInt($("setWindow").value, 10), quarantine_seconds: parseInt($("setQuar").value, 10) }) });
    $("setMsg").textContent = "Saved.";
  } catch (e) { $("setMsg").textContent = "Error: " + e.message; }
};

loadInterfaces().then(() => { refreshModel(); tick(); setInterval(tick, 3000); setInterval(refreshModel, 15000); });
