// theme + upload preview + toast + i18n glue
function toggleTheme(){document.documentElement.classList.toggle('dark');localStorage.setItem('av-theme',document.documentElement.classList.contains('dark')?'d':'l');}
if(localStorage.getItem('av-theme')==='d')document.documentElement.classList.add('dark');
function previewFile(inp){const f=inp.files&&inp.files[0];if(!f)return;const img=document.getElementById('prev');if(img){img.src=URL.createObjectURL(f);img.classList.remove('hidden');}const m=document.getElementById('fileMeta');if(m)m.textContent=`${f.name} • ${(f.size/1024).toFixed(1)} KB`;}
function toast(msg){const t=document.createElement('div');t.className='fixed bottom-5 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl shadow-xl z-50';t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),2200);}
function setLang(v){try{applyLang(v);}catch(e){}localStorage.setItem('av-lang',v);}
document.addEventListener('DOMContentLoaded',()=>{const s=document.getElementById('langSel');const v=localStorage.getItem('av-lang')||'en';if(s)s.value=v;try{applyLang(v);}catch(e){}});
