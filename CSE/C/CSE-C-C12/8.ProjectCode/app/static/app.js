// CareLens AI shared frontend helpers
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const r = await fetch('/api/auth/me');
    const login = document.getElementById('nav-login');
    if (login) login.textContent = r.ok ? 'Assistant' : 'Sign in';
    if (login && r.ok) login.href = '/dashboard';
  } catch (e) { /* offline */ }
});
