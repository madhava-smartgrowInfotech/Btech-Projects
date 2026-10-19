/* ParkSure shared frontend helpers */
const api = async (path, opts = {}) => {
  const t = localStorage.getItem("parksure_token");
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(path, { ...opts, headers: h });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const stars = (n) => "★".repeat(Math.round(n)) + "☆".repeat(5 - Math.round(n));
function navState() {
  const t = localStorage.getItem("parksure_token");
  const slot = document.getElementById("navLinks");
  if (!slot) return;
  slot.innerHTML = t
    ? `<a href="/dashboard">My bookings</a><a href="/admin">Admin</a><a href="#" id="logout">Log out</a>`
    : `<a href="/login">Log in</a><a class="btn small" href="/login">Get started</a>`;
  const lo = document.getElementById("logout");
  if (lo) lo.onclick = (e) => { e.preventDefault(); localStorage.removeItem("parksure_token"); location.href = "/"; };
}
document.addEventListener("DOMContentLoaded", navState);
