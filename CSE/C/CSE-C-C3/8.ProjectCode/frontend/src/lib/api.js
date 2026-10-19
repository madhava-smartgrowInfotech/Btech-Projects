const TOKEN_KEY = 'parksure_token'

export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}
export const setToken = (t) => {
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage unavailable - session lasts for this tab only */
  }
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn
}

// FastAPI returns {detail: "text"} or, for validation, {detail: [{loc, msg}]}.
function message(data, status) {
  const d = data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d))
    return d
      .map((x) => `${(x.loc || []).filter((p) => p !== 'body').join('.') || 'input'}: ${String(x.msg || '').replace(/^Value error, /, '')}`)
      .join('; ')
  if (status === 0) return 'Cannot reach the ParkSure server. Make sure the backend is running on port 8403.'
  return `Request failed (${status})`
}

export async function api(path, { method = 'GET', body, auth = true, signal } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, signal })
  } catch (e) {
    if (e?.name === 'AbortError') throw e
    const err = new Error(message(null, 0))
    err.status = 0
    throw err
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(message(data, res.status))
    err.status = res.status
    if (res.status === 401 && auth && token) onUnauthorized()
    throw err
  }
  return data
}

const q = (o) => new URLSearchParams(o).toString()

export const Api = {
  login: (email, password) => api('/auth/login', { method: 'POST', body: { email, password }, auth: false }),
  register: (name, email, password) => api('/auth/register', { method: 'POST', body: { name, email, password }, auth: false }),
  me: () => api('/auth/me'),
  locations: () => api('/locations', { auth: false }),
  createLocation: (b) => api('/locations', { method: 'POST', body: b }),
  updateLocation: (id, b) => api(`/locations/${id}`, { method: 'PUT', body: b }),
  deleteLocation: (id) => api(`/locations/${id}`, { method: 'DELETE' }),
  search: (start, end) => api(`/search?${q({ start_time: start, end_time: end })}`, { auth: false }),
  reserve: (b) => api('/reservations', { method: 'POST', body: b }),
  reservations: () => api('/reservations'),
  act: (id, op) => api(`/reservations/${id}/${op}`, { method: 'POST' }),
  trust: () => api('/trust'),
  confirmPayment: (rid) => api(`/payments/${rid}/confirm`, { method: 'POST' }),
  adminOverview: () => api('/admin/overview'),
  adminUsers: () => api('/admin/users'),
  adminBookings: () => api('/admin/bookings'),
  adminResetBuffers: () => api('/admin/reset-buffers', { method: 'POST' }),
  adminInsights: (days) => api(`/admin/insights?${q({ window_days: days })}`),
}
