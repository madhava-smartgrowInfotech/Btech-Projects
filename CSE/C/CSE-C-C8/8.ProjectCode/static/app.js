const $ = (id) => document.getElementById(id);
function go(v){ document.querySelectorAll('#nav button').forEach(b=>b.classList.toggle('active', b.dataset.view===v));
  ['dashboard','analyze','reviewers','model','history','about'].forEach(x=>$('view-'+x).classList.toggle('hidden', x!==v));
  if(v==='reviewers') loadReviewers(); if(v==='model') loadMetrics(); if(v==='history') loadHistory(); if(v==='dashboard') loadDash(); }
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>go(b.dataset.view));
const esc = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const badge = (t,cls)=>`<span class="badge ${cls||''}">${esc(t)}</span>`;

async function api(path, opts){ const r = await fetch(path, opts); if(!r.ok){ let m=r.statusText; try{ m=(await r.json()).detail||m;}catch(e){} throw new Error(m);} return r.json(); }

async function loadDash(){ try{
  const h = await api('/api/health'); $('kpi-reviewers').textContent = h.reviewer_count;
  $('kpi-model').textContent = h.model_loaded ? 'trained model loaded' : 'model not trained';
  $('kpi-model').className = 'badge ' + (h.model_loaded?'ok':'warn');
  const list = await api('/api/analyses'); $('kpi-analyses').textContent = list.length;
  $('recent').innerHTML = list.length ? `<table><tr><th>File</th><th>Date</th><th>Assessment</th><th>Top reviewer</th><th></th></tr>${list.slice(0,5).map(a=>`<tr><td>${esc(a.filename)}</td><td>${esc(a.created_at.slice(0,16).replace('T',' '))}</td><td>${esc((a.overall_assessment||'').slice(0,80))}</td><td>${esc(a.top_reviewer||'–')}</td><td><button class="btn small ghost" onclick="openAnalysis(${a.id})">Open</button></td></tr>`).join('')}</table>` : '<p class="muted">No analyses yet — upload a paper to begin.</p>';
 }catch(e){ $('recent').innerHTML = `<div class="err">${esc(e.message)}</div>`; } }

async function openAnalysis(id){ const r = await api('/api/analyses/'+id); renderResult(r); go('analyze'); window.scrollTo(0,0); }

// upload
const drop=$('drop'), fileIn=$('file'); let chosen=null;
drop.onclick=()=>fileIn.click();
drop.ondragover=e=>{e.preventDefault();drop.style.borderColor='#0b5cab';};
drop.ondrop=e=>{e.preventDefault(); if(e.dataTransfer.files[0]){chosen=e.dataTransfer.files[0];$('fname').textContent=chosen.name+` (${(chosen.size/1048576).toFixed(2)} MB)`;}};
fileIn.onchange=()=>{ if(fileIn.files[0]){chosen=fileIn.files[0];$('fname').textContent=chosen.name+` (${(chosen.size/1048576).toFixed(2)} MB)`;}};
$('btn-analyze').onclick=async()=>{
  if(!chosen){$('amsg').innerHTML='<div class="err">Choose a PDF file first.</div>';return;}
  $('amsg').innerHTML=''; $('prog').style.width='25%';
  const fd=new FormData(); fd.append('file',chosen);
  fd.append('active_only',$('f-active').checked); fd.append('min_score',$('f-min').value||'0');
  fd.append('topic',$('f-topic').value||''); fd.append('method',$('f-method').value||'');
  $('prog').style.width='60%';
  try{ const r=await (await fetch('/api/analyze',{method:'POST',body:fd})).json();
    if(r.detail) throw new Error(r.detail);
    $('prog').style.width='100%'; renderResult(r); loadDash();
    setTimeout(()=>$('prog').style.width='0',800);
  }catch(e){ $('prog').style.width='0'; $('amsg').innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};

function li(arr){ return (arr||[]).map(x=>`<li>${esc(x)}</li>`).join(''); }
function renderResult(r){
  const f=r.features||{}, ml=r.ml_decision_signal||{}, rev=r.review||{}, lit=r.literature||{}, q=r.review_quality||{};
  const cov=rev.coverage||{};
  const covBars=Object.entries(cov).map(([k,v])=>`<div style="margin:6px 0"><div class="row" style="justify-content:space-between"><b>${esc(k)}</b><span>${v}%</span></div><div class="bar"><i style="width:${v}%"></i></div></div>`).join('');
  const revs=(r.reviewers||[]).map(v=>`<div class="rev"><div class="row" style="justify-content:space-between"><div><b>#${v.rank} ${esc(v.display_name)}</b> <span class="muted">${esc(v.affiliation||'')}</span> ${badge(v.match_strength, v.score>=65?'ok':v.score>=45?'':'warn')}</div><div class="score">${v.score}</div></div>
    <p class="muted">${esc(v.expertise||'')}</p>
    <div class="row">${(v.matching_topics||[]).map(t=>badge(t)).join(' ')} ${(v.matching_methods||[]).map(t=>badge(t)).join(' ')}</div>
    <p>Availability: ${v.availability.current_load}/${v.availability.maximum_load} · Conflict: ${v.conflict.conflicted?'<b style="color:#b91c1c">Yes — '+esc(v.conflict.reason||'')+'</b>':'<span style="color:#15803d">None detected</span>'}</p>
    <details><summary>Audit Details — score breakdown</summary>
      <table><tr><th>Signal</th><th>Value</th></tr>
      <tr><td>Expertise similarity (cosine)</td><td>${v.breakdown.expertise_similarity}</td></tr>
      <tr><td>Topic/keyword overlap</td><td>${v.breakdown.keyword_score}</td></tr>
      <tr><td>Method overlap</td><td>${v.breakdown.method_score}</td></tr>
      <tr><td>Availability</td><td>${v.breakdown.availability_score}</td></tr>
      <tr><td>Conflict penalty</td><td>${v.breakdown.conflict_penalty}</td></tr>
      <tr><td><b>Final score (0–100)</b></td><td><b>${v.score}</b></td></tr></table>
      <p class="muted">${esc(v.explanation||'')}</p></details></div>`).join('') || '<p class="muted">No reviewers matched the current filters.</p>';
  const litHtml = lit.literature_retrieval_status==='ok'
    ? `<table><tr><th>Title</th><th>Year</th><th>Source</th><th>Relevance</th></tr>${(lit.works||[]).map(w=>`<tr><td>${esc(w.title)}</td><td>${w.year??'–'}</td><td>${esc(w.source||'')}</td><td>${w.relevance}</td></tr>`).join('')}</table><p class="muted">Source: OpenAlex · query: “${esc(lit.query||'')}”. Supporting context only — not proof of novelty.</p>`
    : `<div class="note">Related-literature retrieval unavailable (${esc(lit.error||'offline')}). Analysis continued with local content.</div>`;
  $('result').innerHTML = `
  <div class="card" style="margin-top:16px"><h3>1 · Paper Overview</h3>
    <p><b>${esc((r.paper||{}).title||'')}</b> ${badge((r.paper||{}).page_count+' pages')}</p>
    <p class="muted">${esc((r.paper||{}).paper_summary||'')}</p>
    <details><summary>Extracted document preview (first pages)</summary>${((r.paper||{}).pages_preview||[]).map(p=>`<p class="muted"><b>p.${p.page}</b> — ${esc((p.text||'').slice(0,500))}…</p>`).join('')}</details>
    <details><summary>Detected sections & features</summary><p class="muted">Sections: ${esc((f.detected_sections||[]).join(', ')||'none')} · Missing: ${esc((f.missing_sections||[]).join(', ')||'none')} · Words: ${f.word_count} · References: ${f.reference_count} · Keywords: ${esc((f.keywords||[]).join(', '))}</p></details></div>
  <div class="card"><h3>2 · Preliminary Assessment</h3>
    <p>${esc(r.overall_assessment||'')}</p>
    <div class="grid g3"><div>${badge('Historical decision signal: '+(ml.label||'n/a'), ml.status==='ok'?'':'warn')}<p class="muted">confidence ${ml.confidence??'–'} · ${esc(ml.note||'')}</p></div>
    <div>${badge('Structural score: '+(f.overall_structural??'–'))}<p class="muted">structure ${f.structure_completeness} · evidence ${f.evidence_coverage} · method ${f.method_clarity_signal} · presentation ${f.presentation_signal}</p></div>
    <div>${badge('AI review: '+(rev.llm_status||rev.source||'n/a'), rev.llm_status==='ok'?'ok':'warn')}<p class="muted">${esc(rev.llm_note||'Local review synthesis.')}</p></div></div>
    ${rev.ai_synthesis?`<details open><summary>AI synthesis (local model${rev.llm_model?' · '+esc(rev.llm_model):''})</summary><p>${esc(rev.ai_synthesis).replace(/\n/g,'<br>')}</p></details>`:''}
    ${r.warning?`<div class="note">${esc(r.warning)}</div>`:''}
    <div class="note">PeerScope provides AI-assisted analysis and reviewer matching for decision support. Final editorial judgment remains with a qualified human.</div></div>
  <div class="grid g2"><div class="card"><h3>3 · Strengths (${(rev.strengths||[]).length})</h3><ul class="clean">${li(rev.strengths)}</ul></div>
  <div class="card"><h3>4 · Major Concerns (${(rev.major_concerns||[]).length})</h3><ul class="clean">${li(rev.major_concerns)}</ul></div></div>
  <div class="grid g2"><div class="card"><h3>5 · Minor Concerns (${(rev.minor_concerns||[]).length})</h3><ul class="clean">${li(rev.minor_concerns)}</ul></div>
  <div class="card"><h3>6 · Actionable Recommendations (${(rev.recommendations||[]).length})</h3><ul class="clean">${li(rev.recommendations)}</ul></div></div>
  <div class="card"><h3>7 · Review Coverage</h3>${covBars}<p class="muted">Derived from generated content & detected evidence (strengths ${q.num_strengths}, major ${q.num_major}, minor ${q.num_minor}, recommendations ${q.num_recommendations}, evidence refs ${q.num_evidence_refs}).</p></div>
  <div class="card"><h3>8 · Related Literature</h3>${litHtml}</div>
  <div class="card"><h3>9 · Recommended Reviewers</h3>${revs}</div>
  <div class="card"><h3>10 · Audit Details & Export</h3>
    <p class="muted">Matching weights: expertise 0.55 · keyword 0.20 · method 0.15 · availability 0.10 · conflict penalty 0.60 (see About). Literature status: ${esc(lit.literature_retrieval_status||'')}.</p>
    <div class="row">${r.analysis_id?`<a class="btn small ghost" href="/api/analyses/${r.analysis_id}/export?format=json">Export JSON</a><a class="btn small ghost" href="/api/analyses/${r.analysis_id}/export?format=pdf">Export PDF</a>`:'<span class="muted">Save via Analyze to enable export.</span>'}</div></div>`;
}

// reviewers
let editing=null;
async function loadReviewers(){ try{ const rows=await api('/api/reviewers');
  $('rev-list').innerHTML = rows.length? `<table><tr><th>Name</th><th>Affiliation</th><th>Topics</th><th>Load</th><th>Status</th><th></th></tr>${rows.map(r=>`<tr><td><b>${esc(r.display_name)}</b></td><td>${esc(r.affiliation||'')}</td><td>${esc(r.research_topics||'')}</td><td>${r.current_load}/${r.maximum_load}</td><td>${r.is_active?badge('active','ok'):badge('inactive','warn')}</td><td class="row"><button class="btn small ghost" onclick="editRev(${r.id})">Edit</button><button class="btn small ghost" onclick="toggleRev(${r.id})">${r.is_active?'Deactivate':'Activate'}</button><button class="btn small danger" onclick="delRev(${r.id})">Delete</button></td></tr>`).join('')}</table>`:'<p class="muted">No reviewers yet.</p>';
  window._revs=Object.fromEntries(rows.map(r=>[r.id,r]));
 }catch(e){ $('rev-list').innerHTML=`<div class="err">${esc(e.message)}</div>`; } }
async function editRev(id){ const r=window._revs[id]; editing=id; $('rev-form-title').textContent='Edit reviewer'; $('rev-form-card').classList.remove('hidden');
  $('r-id').value=r.id; $('r-name').value=r.display_name; $('r-aff').value=r.affiliation||''; $('r-exp').value=r.expertise_description||'';
  $('r-topics').value=r.research_topics||''; $('r-methods').value=r.methods||''; $('r-kw').value=r.keywords||''; $('r-pubs').value=r.publication_titles||'';
  $('r-load').value=r.current_load; $('r-max').value=r.maximum_load; $('r-active').value=String(r.is_active); $('r-conf').value=r.conflict_terms||''; window.scrollTo(0,document.body.scrollHeight); }
async function toggleRev(id){ const r=window._revs[id]; await api('/api/reviewers/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...r,is_active:!r.is_active})}); loadReviewers(); }
async function delRev(id){ if(!confirm('Delete this reviewer?'))return; await api('/api/reviewers/'+id,{method:'DELETE'}); loadReviewers(); }
$('btn-new').onclick=()=>{ editing=null; $('rev-form-title').textContent='Add reviewer'; $('rev-form-card').classList.remove('hidden'); ['r-id','r-name','r-aff','r-exp','r-topics','r-methods','r-kw','r-pubs','r-conf'].forEach(i=>$(i).value=''); $('r-load').value=0; $('r-max').value=5; };
$('r-cancel').onclick=()=>$('rev-form-card').classList.add('hidden');
$('r-save').onclick=async()=>{ const body={display_name:$('r-name').value.trim(),affiliation:$('r-aff').value,expertise_description:$('r-exp').value,research_topics:$('r-topics').value,methods:$('r-methods').value,keywords:$('r-kw').value,publication_titles:$('r-pubs').value,current_load:+$('r-load').value||0,maximum_load:+$('r-max').value||5,is_active:$('r-active').value==='true',conflict_terms:$('r-conf').value};
  if(!body.display_name){alert('Display name is required');return;}
  try{ if(editing){await api('/api/reviewers/'+editing,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});} else {await api('/api/reviewers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});} $('rev-form-card').classList.add('hidden'); loadReviewers(); }catch(e){alert(e.message);} };
$('btn-exp').onclick=()=>{ window.location='/api/reviewers/export/csv'; };
$('btn-imp-btn').onclick=()=>$('btn-imp').click();
$('btn-imp').onchange=async()=>{ const f=$('btn-imp').files[0]; if(!f)return; const fd=new FormData(); fd.append('file',f);
  try{ const r=await (await fetch('/api/reviewers/import',{method:'POST',body:fd})).json(); alert('Imported '+(r.imported??0)+' reviewers'); loadReviewers(); }catch(e){alert('Import failed: '+e.message);} };

async function loadMetrics(){ try{ const m=await api('/api/model/metrics');
  if(m.status==='missing'){ $('metrics').innerHTML=`<div class="note">${esc(m.note||'No metrics yet.')}</div>`; return; }
  const cm=(m.confusion_matrix||[]).map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('');
  $('metrics').innerHTML=`<div class="grid g4">
    <div><div class="muted">Accuracy</div><div class="kpi">${m.accuracy}</div></div>
    <div><div class="muted">Precision (macro)</div><div class="kpi">${m.precision_macro}</div></div>
    <div><div class="muted">Recall (macro)</div><div class="kpi">${m.recall_macro}</div></div>
    <div><div class="muted">F1 (macro)</div><div class="kpi">${m.f1_macro}</div></div></div>
    <p>ROC-AUC: <b>${m.roc_auc??'n/a'}</b> · Test samples: <b>${m.test_samples}</b> · Rows: ${m.dataset_rows} · Seed: ${m.random_seed}</p>
    <p class="muted">Model: ${esc(m.model_type||'')} · Features: ${esc(m.features||'')} · Source: ${esc(m.dataset_source||'')}${m.synthetic_fallback?' (synthetic fallback — clearly labeled; not presented as a public benchmark result)':''} · Trained: ${esc(m.trained_at||'')}</p>
    <p class="muted">Class distribution: ${esc(JSON.stringify(m.class_distribution||{}))} · Labels: ${esc((m.labels||[]).join(', '))}</p>
    <h3>Confusion matrix</h3><table class="cm"><tr><th></th>${(m.labels||[]).map(l=>`<th>${esc(l)}</th>`).join('')}</tr>${cm}</table>`;
 }catch(e){ $('metrics').innerHTML=`<div class="err">${esc(e.message)}</div>`; } }

async function loadHistory(){ try{ const list=await api('/api/analyses');
  $('hist').innerHTML=list.length?`<table><tr><th>ID</th><th>File</th><th>Date</th><th>Concerns</th><th>Recommendations</th><th>Top reviewer</th><th></th><th></th></tr>${list.map(a=>`<tr><td>${a.id}</td><td>${esc(a.filename)}</td><td>${esc(a.created_at.slice(0,16).replace('T',' '))}</td><td>${a.concern_count}</td><td>${a.recommendation_count}</td><td>${esc(a.top_reviewer||'–')}</td><td><button class="btn small ghost" onclick="openAnalysis(${a.id})">Open</button></td><td><a class="btn small ghost" href="/api/analyses/${a.id}/export?format=json">JSON</a> <a class="btn small ghost" href="/api/analyses/${a.id}/export?format=pdf">PDF</a></td></tr>`).join('')}</table>`:'<p class="muted">No analyses yet.</p>';
 }catch(e){ $('hist').innerHTML=`<div class="err">${esc(e.message)}</div>`; } }

loadDash();
