/* StoryVox frontend application logic */
const $ = (id) => document.getElementById(id);
const state = { languages: [], currentStory: null, currentAudioId: null };

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3200);
}
function setStatus(el, msg, kind) {
  el.textContent = msg || "";
  el.className = "status" + (kind ? " " + kind : "");
}
function showProgress(id, on) { $(id).classList.toggle("hidden", !on); }

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    ["creator", "history", "evaluation"].forEach((t) => $("tab-" + t).classList.add("hidden"));
    $("tab-" + btn.dataset.tab).classList.remove("hidden");
    if (btn.dataset.tab === "history") loadHistory();
    if (btn.dataset.tab === "evaluation") loadEvaluations();
  });
});

async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || ("Request failed (" + res.status + ")"));
  return data;
}

async function initMeta() {
  const langs = await api("/api/languages");
  state.languages = langs;
  $("language").innerHTML = langs.map((l) => `<option value="${l.code}">${l.name}</option>`).join("");
  const meta = await api("/api/meta");
  $("style").innerHTML = meta.styles.map((s) => `<option>${s}</option>`).join("");
  $("length").innerHTML = meta.lengths.map((s) => `<option>${s}</option>`).join("");
}

function renderResult(story) {
  state.currentStory = story;
  $("emptyResult").classList.add("hidden");
  $("resultBody").classList.remove("hidden");
  $("resTitle").textContent = story.title;
  $("resMeta").textContent = `${story.language_name} · ${story.style} · ${story.length_option} · ${story.word_count} words · ~${story.listening_time_minutes} min listen · generated in ${story.generation_time_seconds}s`;
  $("resText").textContent = story.story_text;
  const audioEl = $("resAudio");
  if (story.audio) {
    state.currentAudioId = story.audio.id;
    audioEl.src = story.audio.file_path;
    audioEl.classList.remove("hidden");
    $("downloadBtn").classList.remove("hidden");
    $("renarrateBtn").classList.remove("hidden");
  } else {
    state.currentAudioId = null;
    audioEl.removeAttribute("src");
    audioEl.classList.add("hidden");
    $("downloadBtn").classList.add("hidden");
    $("renarrateBtn").classList.remove("hidden");
  }
}

async function generate() {
  const btn = $("generateBtn");
  const payload = {
    prompt: $("prompt").value,
    language_code: $("language").value,
    style: $("style").value,
    length_option: $("length").value,
    synthesize: $("synthesize").checked,
  };
  if (!payload.prompt.trim()) { setStatus($("createStatus"), "Please enter a story idea.", "error"); return; }
  btn.disabled = true; showProgress("createProgress", true);
  setStatus($("createStatus"), "Writing your story and preparing narration… this can take a minute on first run.");
  try {
    const story = await api("/api/stories/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    renderResult(story);
    setStatus($("createStatus"), story.audio ? "Story and narration ready." : "Story ready. Press “Regenerate narration” for audio.", "ok");
    toast("StoryVox finished your story");
  } catch (e) { setStatus($("createStatus"), e.message, "error"); }
  finally { btn.disabled = false; showProgress("createProgress", false); }
}

async function renarrate() {
  if (!state.currentStory) return;
  setStatus($("createStatus"), "Creating fresh narration…");
  showProgress("createProgress", true);
  $("renarrateBtn").disabled = true;
  try {
    const audio = await api(`/api/stories/${state.currentStory.id}/synthesize`, { method: "POST" });
    state.currentStory.audio = { ...audio, file_path: `/api/audio/${audio.id}` };
    renderResult(state.currentStory);
    setStatus($("createStatus"), "Fresh narration ready.", "ok");
  } catch (e) { setStatus($("createStatus"), e.message, "error"); }
  finally { showProgress("createProgress", false); $("renarrateBtn").disabled = false; }
}

async function loadHistory() {
  const list = $("historyList");
  list.innerHTML = "<p class='muted'>Loading history…</p>";
  try {
    const items = await api("/api/stories?limit=100");
    if (!items.length) {
      list.innerHTML = "<div class='empty'><div class='empty-icon'>🗂️</div><p>No stories yet. Create your first story to see it here.</p></div>";
      return;
    }
    list.innerHTML = "";
    items.forEach((s) => {
      const div = document.createElement("div");
      div.className = "history-item";
      div.innerHTML = `<h4></h4><div class="meta">${s.language_name} · ${s.style} · ${s.word_count} words · ${new Date(s.created_at).toLocaleString()} · ${s.has_audio ? "audio available" : "no audio"}</div><div class="btnrow"></div>`;
      div.querySelector("h4").textContent = s.title;
      const row = div.querySelector(".btnrow");
      const view = document.createElement("button"); view.className = "secondary"; view.textContent = "View";
      view.onclick = async () => { const full = await api(`/api/stories/${s.id}`); renderResult(full); document.querySelector('[data-tab="creator"]').click(); };
      const dl = document.createElement("button"); dl.className = "secondary"; dl.textContent = "Download"; dl.disabled = !s.audio_id;
      dl.onclick = () => { window.location.href = `/api/audio/${s.audio_id}`; };
      const del = document.createElement("button"); del.className = "secondary"; del.textContent = "Delete";
      del.onclick = async () => { if (!confirm("Delete this story and its audio?")) return; await api(`/api/stories/${s.id}`, { method: "DELETE" }); toast("Deleted"); loadHistory(); };
      row.append(view, dl, del);
      if (s.audio_id) {
        const audio = document.createElement("audio"); audio.controls = true; audio.src = `/api/audio/${s.audio_id}`; audio.style.marginTop = "10px";
        div.appendChild(audio);
      }
      list.appendChild(div);
    });
  } catch (e) { list.innerHTML = `<p class='status error'>${e.message}</p>`; }
}

function metricCard(k, v) {
  const val = (v === null || v === undefined || v === "") ? "—" : v;
  return `<div class="metric"><div class="k">${k}</div><div class="v">${val}</div></div>`;
}

async function loadEvaluations() {
  try {
    const rows = await api("/api/evaluations");
    if (!rows.length) {
      $("evalCards").innerHTML = metricCard("Status", "Not run yet") ;
      $("evalTableWrap").innerHTML = "<p class='muted'>Evaluation has not been run yet. Press “Run evaluation” to compute real metrics.</p>";
      return;
    }
    renderEval(rows[0].metrics_json || rows[0].metrics || rows[0]);
  } catch (e) { setStatus($("evalStatus"), e.message, "error"); }
}

function renderEval(m) {
  const avg = m.averages || {};
  $("evalCards").innerHTML =
    metricCard("Samples", m.sample_count) +
    metricCard("WER", avg.wer) +
    metricCard("CER", avg.cer) +
    metricCard("Topic similarity", avg.prompt_story_similarity) +
    metricCard("Story latency (s)", avg.story_time_s) +
    metricCard("TTS latency (s)", avg.tts_time_s) +
    metricCard("RTF", avg.rtf);
  const samples = m.samples || [];
  if (!samples.length) { $("evalTableWrap").innerHTML = ""; return; }
  const cols = ["prompt", "language_code", "story_time_s", "tts_time_s", "audio_duration_s", "rtf", "wer", "cer", "prompt_story_similarity"];
  let html = "<table class='eval'><tr>" + cols.map((c) => `<th>${c}</th>`).join("") + "</tr>";
  samples.forEach((r) => { html += "<tr>" + cols.map((c) => `<td>${(r[c] === undefined || r[c] === null) ? "—" : String(r[c]).slice(0, 90)}</td>`).join("") + "</tr>"; });
  html += "</table>";
  const when = m.created_at ? `<p class='muted'>Computed at ${m.created_at} · story model ${m.story_model || ""} · ASR ${m.asr_model || ""}</p>` : "";
  $("evalTableWrap").innerHTML = when + html;
}

async function runEval() {
  const btn = $("runEval");
  btn.disabled = true; showProgress("evalProgress", true);
  setStatus($("evalStatus"), "Running measurable evaluation… speech and transcription can take several minutes.");
  try {
    const n = Math.max(1, Math.min(30, parseInt($("evalSamples").value || "5", 10)));
    const out = await api("/api/evaluations/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ samples: n }) });
    renderEval(out.metrics);
    setStatus($("evalStatus"), "Evaluation complete. Results saved under data/evaluations.", "ok");
  } catch (e) { setStatus($("evalStatus"), e.message, "error"); }
  finally { btn.disabled = false; showProgress("evalProgress", false); }
}

$("generateBtn").addEventListener("click", generate);
$("renarrateBtn").addEventListener("click", renarrate);
$("downloadBtn").addEventListener("click", () => { if (state.currentAudioId) window.location.href = `/api/audio/${state.currentAudioId}`; });
$("refreshHistory").addEventListener("click", loadHistory);
$("runEval").addEventListener("click", runEval);
initMeta().catch((e) => setStatus($("createStatus"), "Could not load languages: " + e.message, "error"));
