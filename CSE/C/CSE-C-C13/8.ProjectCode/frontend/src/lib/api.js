// Thin fetch client for the CipherVault API. The token lives in sessionStorage (cleared when the tab closes).
const TOKEN_KEY = 'cv_token'

export const getToken = () => {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}
export const setToken = (t) => {
  try {
    if (t) sessionStorage.setItem(TOKEN_KEY, t)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage blocked - session lasts until reload */
  }
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn
}

function detailOf(body, status) {
  const d = body && typeof body === 'object' ? body.detail : null
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) return d.map((x) => x.msg || '').filter(Boolean).join('; ')
  if (status === 0) return 'Cannot reach the server. Check that the backend is running on port 8413.'
  return `Request failed (${status})`
}

export async function request(path, { method = 'GET', json, form, raw = false, auth = true } = {}) {
  const headers = {}
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`
  let body
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (form) body = form
  let res
  try {
    res = await fetch(path, { method, headers, body })
  } catch {
    throw new ApiError(detailOf(null, 0), 0)
  }
  if (raw && res.ok) return res
  const ct = res.headers.get('content-type') || ''
  let data = null
  try {
    data = ct.includes('json') ? await res.json() : await res.text()
  } catch {
    data = null
  }
  if (!res.ok) {
    if (res.status === 401 && auth && token) onUnauthorized()
    throw new ApiError(detailOf(data, res.status), res.status)
  }
  return data
}

export const api = {
  config: () => request('/api/config', { auth: false }),
  health: () => request('/api/health', { auth: false }),
  register: (payload) => request('/api/auth/register', { method: 'POST', json: payload, auth: false }),
  login: (email, password) => request('/api/auth/login', { method: 'POST', json: { email, password }, auth: false }),
  me: () => request('/api/auth/me'),
  keyBundle: () => request('/api/auth/key-bundle'),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  users: (q = '') => request(`/api/users?q=${encodeURIComponent(q)}`),
  files: () => request('/api/files'),
  shared: () => request('/api/files/shared'),
  file: (id) => request(`/api/files/${id}`),
  upload: (form) => request('/api/files/upload', { method: 'POST', form }),
  updateFile: (id, form) => request(`/api/files/${id}`, { method: 'PUT', form }),
  remove: (id) => request(`/api/files/${id}`, { method: 'DELETE' }),
  download: (id) => request(`/api/files/${id}/download`, { raw: true }),
  share: (id, payload) => request(`/api/files/${id}/share`, { method: 'POST', json: payload }),
  permissions: (id) => request(`/api/files/${id}/permissions`),
  changeRole: (id, uid, role) => request(`/api/files/${id}/permissions/${uid}`, { method: 'PUT', json: { role } }),
  revoke: (id, uid) => request(`/api/files/${id}/permissions/${uid}`, { method: 'DELETE' }),
  audit: (limit = 100) => request(`/api/audit?limit=${limit}`),
  fileAudit: (id) => request(`/api/audit/file/${id}`),
  verifyChain: () => request('/api/audit/verify'),
}
