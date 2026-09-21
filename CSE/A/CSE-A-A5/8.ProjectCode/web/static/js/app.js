// CipherGuard Shield frontend logic
const qs = s => document.querySelector(s);

// Tab switching
document.querySelectorAll('.nav-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    qs('#tab-'+btn.dataset.tab).classList.add('active');
    if(btn.dataset.tab==='alerts') refreshAlerts();
    if(btn.dataset.tab==='performance') loadMetrics();
  });
});

function showResult(el, text, ok=true){
  el.classList.remove('hidden');
  el.className = 'result ' + (ok ? 'ok' : 'err');
  el.textContent = text;
}

// Engine status
async function checkHealth(){
  try{
    const r = await fetch('/api/health');
    const j = await r.json();
    const badge = qs('#engineStatus');
    if(j.engine_loaded){
      badge.textContent = 'Engine: Ready';
      badge.className='badge ok';
    } else {
      badge.textContent = 'Engine: Training...';
      badge.className='badge';
    }
  }catch{
    qs('#engineStatus').textContent='Engine: Offline';
    qs('#engineStatus').className='badge err';
  }
}
checkHealth();
setInterval(checkHealth, 5000);

// Live log
let liveLog = [];
let chartCounts=null, chartConfidence=null;

function pushLive(entry){
  liveLog.unshift(entry);
  if(liveLog.length>200) liveLog.pop();
  renderLive();
  updateCharts();
}

function renderLive(){
  const tbody = qs('#liveTable tbody');
  tbody.innerHTML='';
  liveLog.slice(0,50).forEach(e=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>${e.time}</td><td style="color:${e.label==='attack'?'#f87171':'#4ade80'}">${e.label}</td><td>${(e.confidence*100).toFixed(1)}%</td><td>${e.proto}/${e.service}/${e.state}</td><td>${(e.xgb*100).toFixed(1)}% / ${(e.cnn*100).toFixed(1)}%</td><td class="sev-${e.severity}">${e.severity}</td>`;
    tbody.appendChild(tr);
  });
  qs('#liveStats').textContent=`Total scored: ${liveLog.length} | Attacks: ${liveLog.filter(x=>x.label==='attack').length} | Normal: ${liveLog.filter(x=>x.label==='normal').length}`;
}

function updateCharts(){
  const attacks = liveLog.filter(x=>x.label==='attack').length;
  const normals = liveLog.filter(x=>x.label==='normal').length;
  if(!chartCounts){
    const ctx = qs('#chartCounts').getContext('2d');
    chartCounts = new Chart(ctx,{type:'doughnut', data:{labels:['Attack','Normal'], datasets:[{data:[attacks,normals], backgroundColor:['#ef4444','#22c55e']}]}, options:{responsive:true, plugins:{title:{display:true,text:'Attack vs Normal (live)'}}}});
  } else {
    chartCounts.data.datasets[0].data=[attacks,normals];
    chartCounts.update();
  }
  // Confidence histogram (0-0.5,0.5-0.7,0.7-0.85,0.85-1)
  const bins=[0,0,0,0];
  liveLog.forEach(e=>{
    const c=e.confidence;
    if(c<0.5) bins[0]++; else if(c<0.7) bins[1]++; else if(c<0.85) bins[2]++; else bins[3]++;
  });
  if(!chartConfidence){
    const ctx2=qs('#chartConfidence').getContext('2d');
    chartConfidence=new Chart(ctx2,{type:'bar', data:{labels:['<50%','50-70%','70-85%','85-100%'], datasets:[{label:'Records', data:bins, backgroundColor:'#0ea5e9'}]}, options:{responsive:true, plugins:{title:{display:true,text:'Confidence distribution'}}}});
  } else {
    chartConfidence.data.datasets[0].data=bins;
    chartConfidence.update();
  }
}

qs('#btnClearLog').addEventListener('click',()=>{liveLog=[];renderLive();updateCharts();});

// Single scoring
qs('#btnScore').addEventListener('click', async()=>{
  const rec={
    proto: qs('#f_proto').value,
    service: qs('#f_service').value,
    state: qs('#f_state').value,
    dur: parseFloat(qs('#f_dur').value)||0,
    sbytes: parseInt(qs('#f_sbytes').value)||0,
    dbytes: parseInt(qs('#f_dbytes').value)||0,
    rate: parseFloat(qs('#f_rate').value)||0,
    spkts: parseInt(qs('#f_spkts').value)||0,
    dpkts: parseInt(qs('#f_dpkts').value)||0,
    sload: parseFloat(qs('#f_sload').value)||0,
    dload: parseFloat(qs('#f_dload').value)||0,
    ct_srv_src: parseInt(qs('#f_ct_srv_src').value)||0,
    ct_dst_ltm: parseInt(qs('#f_ct_dst_ltm').value)||0,
    ct_src_ltm: parseInt(qs('#f_ct_src_ltm').value)||0,
    ct_srv_dst: parseInt(qs('#f_ct_srv_dst').value)||0,
  };
  // Fill remaining with defaults so backend has full schema
  const full={...rec};
  // set reasonable defaults for unspecified
  const defaults={sttl:62,dttl:62,sloss:0,dloss:0,sinpkt:50,dinpkt:50,sjit:5,djit:5,swin:255,stcpb:1000000,dtcpb:1000000,dwin:255,tcprtt:0.02,synack:0.01,ackdat:0.01,smean:100,dmean:100,trans_depth:1,response_body_len:200,ct_state_ttl:2,ct_src_dport_ltm:2,ct_dst_sport_ltm:2,ct_dst_src_ltm:2,is_ftp_login:0,ct_ftp_cmd:0,ct_flw_http_mthd:1,is_sm_ips_ports:0};
  Object.assign(full, defaults, rec);
  try{
    const r=await fetch('/api/ids/score',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(full)});
    const j=await r.json();
    if(!r.ok) throw new Error(j.detail || 'scoring failed');
    const txt=`[${j.label.toUpperCase()}] confidence ${(j.confidence*100).toFixed(1)}% (severity: ${j.severity})\nXGB ${(j.xgb_score*100).toFixed(1)}% | CNN ${(j.cnn_score*100).toFixed(1)}%`;
    showResult(qs('#singleResult'), txt, j.label==='normal');
    pushLive({time:new Date().toLocaleTimeString(), label:j.label, confidence:j.confidence, proto:full.proto, service:full.service, state:full.state, xgb:j.xgb_score, cnn:j.cnn_score, severity:j.severity});
  }catch(e){ showResult(qs('#singleResult'), 'Error: '+e.message, false); }
});

qs('#btnSimNormal').addEventListener('click',()=>{
  qs('#f_proto').value='tcp'; qs('#f_service').value='http'; qs('#f_state').value='CON';
  qs('#f_dur').value='0.3'; qs('#f_sbytes').value='900'; qs('#f_dbytes').value='700'; qs('#f_rate').value='12000';
  qs('#f_spkts').value='7'; qs('#f_dpkts').value='5'; qs('#f_ct_srv_src').value='1'; qs('#f_ct_dst_ltm').value='1';
  qs('#btnScore').click();
});
qs('#btnSimAttack').addEventListener('click',()=>{
  qs('#f_proto').value='tcp'; qs('#f_service').value='ftp'; qs('#f_state').value='RST';
  qs('#f_dur').value='3.5'; qs('#f_sbytes').value='85000'; qs('#f_dbytes').value='1200'; qs('#f_rate').value='95000';
  qs('#f_spkts').value='35'; qs('#f_dpkts').value='4'; qs('#f_ct_srv_src').value='12'; qs('#f_ct_dst_ltm').value='15';
  qs('#btnScore').click();
});

// Batch upload
qs('#btnUpload').addEventListener('click', async()=>{
  const file=qs('#csvFile').files[0];
  if(!file){ showResult(qs('#batchResult'),'Please select a CSV file',false); return; }
  const fd=new FormData(); fd.append('file', file);
  showResult(qs('#batchResult'),'Uploading and scoring...', true);
  try{
    const r=await fetch('/api/ids/score-batch',{method:'POST', body: fd});
    const j=await r.json();
    if(!r.ok) throw new Error(j.detail || 'batch failed');
    showResult(qs('#batchResult'), `Scored ${j.total} rows: ${j.attack_count} attacks, ${j.normal_count} normal\nFirst 5: ` + j.results.slice(0,5).map(x=>`${x.label}(${(x.confidence*100).toFixed(0)}%)`).join(', '), true);
    // Push to live log (cap)
    j.results.slice(0,50).forEach(x=>{
      // fake proto/service for display
      pushLive({time:new Date().toLocaleTimeString(), label:x.label, confidence:x.confidence, proto:'-', service:'-', state:'-', xgb:x.xgb_score, cnn:x.cnn_score, severity: x.label==='attack' ? (x.confidence>=0.85?'critical':x.confidence>=0.7?'high':'medium') : 'low'});
    });
  }catch(e){ showResult(qs('#batchResult'),'Error: '+e.message,false); }
});

// SecureChannel
let lastEnc=null;
qs('#btnEncrypt').addEventListener('click', async()=>{
  const pt=qs('#plainText').value;
  if(!pt){ showResult(qs('#encResult'),'Enter plaintext',false); return; }
  try{
    const r=await fetch('/api/crypto/encrypt',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({plaintext: pt})});
    const j=await r.json();
    if(!r.ok) throw new Error(j.detail || 'encrypt failed');
    lastEnc=j;
    showResult(qs('#encResult'), `Encrypted via ${j.algorithm} + ${j.key_exchange}\nCiphertext: ${j.ciphertext.slice(0,80)}...\nNonce: ${j.nonce}\nTag: ${j.tag}\nEphemeral Public: ${j.ephemeral_public.slice(0,40)}...`, true);
    qs('#dec_ct').value=j.ciphertext; qs('#dec_nonce').value=j.nonce; qs('#dec_tag').value=j.tag; qs('#dec_eph').value=j.ephemeral_public;
    qs('#decryptPanel').classList.remove('hidden'); qs('#decryptPlaceholder').classList.add('hidden');
    qs('#decResult').classList.add('hidden');
  }catch(e){ showResult(qs('#encResult'),'Error: '+e.message,false); }
});
qs('#btnEncryptFile').addEventListener('click', async()=>{
  const file=qs('#encFile').files[0];
  if(!file){ showResult(qs('#encFileResult'),'Select a file',false); return; }
  const fd=new FormData(); fd.append('file', file);
  try{
    const r=await fetch('/api/crypto/encrypt-file',{method:'POST', body: fd});
    const j=await r.json();
    if(!r.ok) throw new Error(j.detail || 'encrypt failed');
    lastEnc=j;
    showResult(qs('#encFileResult'), `File ${j.filename} encrypted (${j.original_size} -> ${j.encrypted_size} bytes)\nCiphertext: ${j.ciphertext.slice(0,80)}...\nNonce: ${j.nonce}\nTag: ${j.tag}`, true);
    qs('#dec_ct').value=j.ciphertext; qs('#dec_nonce').value=j.nonce; qs('#dec_tag').value=j.tag; qs('#dec_eph').value=j.ephemeral_public;
    qs('#decryptPanel').classList.remove('hidden'); qs('#decryptPlaceholder').classList.add('hidden');
  }catch(e){ showResult(qs('#encFileResult'),'Error: '+e.message,false); }
});
qs('#btnDecrypt').addEventListener('click', async()=>{
  try{
    const r=await fetch('/api/crypto/decrypt',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ciphertext: qs('#dec_ct').value, nonce: qs('#dec_nonce').value, tag: qs('#dec_tag').value, ephemeral_public: qs('#dec_eph').value})});
    const j=await r.json();
    if(!r.ok) throw new Error(j.detail || 'decrypt failed');
    showResult(qs('#decResult'), `Decrypted & Verified ✅\nPlaintext: ${j.plaintext}`, true);
  }catch(e){ showResult(qs('#decResult'),'Decryption failed: '+e.message,false); }
});
qs('#btnTamper').addEventListener('click', async()=>{
  // flip last char of ciphertext
  let ct=qs('#dec_ct').value;
  if(ct.length>4){
    const arr=ct.split(''); arr[5]= arr[5]==='A'?'B':'A'; ct=arr.join('');
    qs('#dec_ct').value=ct;
  }
  qs('#btnDecrypt').click();
});

// Alerts
async function refreshAlerts(){
  try{
    const r=await fetch('/api/alerts?limit=100');
    const j=await r.json();
    qs('#alertCount').textContent=`${j.total} alert(s)`;
    const tbody=qs('#alertsTable tbody');
    tbody.innerHTML='';
    j.alerts.forEach(a=>{
      const tr=document.createElement('tr');
      tr.innerHTML=`<td>${a.timestamp}</td><td class="sev-${a.severity}">${a.severity}</td><td>${(a.confidence*100).toFixed(1)}%</td><td>${JSON.stringify(a.features)}</td><td>XGB ${(a.scores.xgb*100).toFixed(1)}% / CNN ${(a.scores.cnn*100).toFixed(1)}%</td>`;
      tbody.appendChild(tr);
    });
  }catch{}
}
qs('#btnRefreshAlerts').addEventListener('click', refreshAlerts);
qs('#btnClearAlerts').addEventListener('click', async()=>{
  await fetch('/api/alerts',{method:'DELETE'});
  refreshAlerts();
});

// Metrics
let chartMetrics=null, chartCM=null;
async function loadMetrics(){
  try{
    const r=await fetch('/api/metrics');
    const j=await r.json();
    if(!r.ok) throw new Error(j.detail || 'no metrics');
    qs('#metricsPanel').innerHTML=`
      <p><b>Data mode:</b> ${j.data_mode}</p>
      <p><b>Dataset:</b> ${j.dataset_rows} rows (train ${j.splits.train} / val ${j.splits.val} / test ${j.splits.test})</p>
      <table class="table"><tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Accuracy</td><td>${(j.accuracy*100).toFixed(2)}%</td></tr>
        <tr><td>Precision</td><td>${(j.precision*100).toFixed(2)}%</td></tr>
        <tr><td>Recall</td><td>${(j.recall*100).toFixed(2)}%</td></tr>
        <tr><td>F1</td><td>${(j.f1*100).toFixed(2)}%</td></tr>
        <tr><td>ROC-AUC</td><td>${j.roc_auc.toFixed(4)}</td></tr>
        <tr><td>XGBoost alone</td><td>${(j.xgb_accuracy*100).toFixed(2)}%</td></tr>
        <tr><td>1D CNN alone</td><td>${(j.cnn_accuracy*100).toFixed(2)}%</td></tr>
      </table>
      <p class="muted">Stacking: Logistic Regression coef ${JSON.stringify(j.meta_coef)} intercept ${JSON.stringify(j.meta_intercept)}</p>
      <p class="muted">Technology: ${j.technology.model_a} + ${j.technology.model_b} + ${j.technology.fusion} | ${j.technology.dataset} | ${j.technology.crypto}</p>
      <p class="muted">Confusion matrix: [[${j.confusion_matrix[0]}],[${j.confusion_matrix[1]}]]</p>
    `;
    // Charts
    const ctx = qs('#chartMetrics').getContext('2d');
    if(chartMetrics) chartMetrics.destroy();
    chartMetrics=new Chart(ctx,{type:'bar', data:{labels:['Accuracy','Precision','Recall','F1','ROC-AUC'], datasets:[{label:'Score', data:[j.accuracy,j.precision,j.recall,j.f1,j.roc_auc], backgroundColor:['#0ea5e9','#22c55e','#f59e0b','#8b5cf6','#06b6d4']}]}, options:{responsive:true, scales:{y:{min:0,max:1}}, plugins:{title:{display:true,text:'Test Metrics'}}}});
    const ctx2=qs('#chartCM').getContext('2d');
    if(chartCM) chartCM.destroy();
    chartCM=new Chart(ctx2,{type:'bar', data:{labels:['TN','FP','FN','TP'], datasets:[{label:'Count', data:[j.confusion_matrix[0][0], j.confusion_matrix[0][1], j.confusion_matrix[1][0], j.confusion_matrix[1][1]], backgroundColor:['#22c55e','#ef4444','#f59e0b','#0ea5e9']}]}, options:{responsive:true, plugins:{title:{display:true,text:'Confusion Matrix (Test)'}}}});
  }catch(e){
    qs('#metricsPanel').textContent='Metrics not available yet. Engine may still be training — wait 1-2 minutes and refresh. Error: '+e.message;
  }
}
