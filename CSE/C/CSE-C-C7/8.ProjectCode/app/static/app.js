async function api(path, opts={}) {
  const r = await fetch(path, { headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', ...opts });
  const t = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(t.detail || 'Request failed');
  return t;
}
function toast(msg) { const el = document.getElementById('toast'); if (!el) return alert(msg); el.textContent = msg; el.style.display = 'block'; setTimeout(() => el.style.display = 'none', 2600); }
async function track(course_id, event_type, value=1.0) {
  try { await api('/api/interactions', { method: 'POST', body: JSON.stringify({ course_id, event_type, value }) }); } catch (e) {}
}
async function refreshNav() {
  try { const m = await api('/api/me'); const nav = document.getElementById('navlinks'); if (!nav) return;
    if (m.user) nav.innerHTML = `<a href="/dashboard">Dashboard</a><a href="/recommendations">Recommendations</a><a href="/path">Learning path</a><a href="/insights">Insights</a><a href="/activity">Activity</a><a href="/analytics">Analytics</a><a href="/onboarding">Profile</a><button class="btn sm light" onclick="logout()">Logout (${m.user.name.split(' ')[0]})</button>`;
    else nav.innerHTML = `<a href="/recommendations">Courses</a><a href="/analytics">Analytics</a><a href="/login">Sign In</a><a class="btn sm" href="/register">Get Started</a>`;
  } catch (e) {}
}
async function logout() { await api('/api/auth/logout', { method: 'POST' }); location.href = '/'; }
document.addEventListener('DOMContentLoaded', refreshNav);
