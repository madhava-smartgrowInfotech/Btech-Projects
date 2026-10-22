// Thin fetch wrapper for the FastAPI backend. Auth is an httponly cookie set by /api/auth/*.
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function detailText(detail) {
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  return typeof detail === 'string' ? detail : ''
}

export async function api(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(`/api${path}`, {
      method,
      credentials: 'same-origin',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Cannot reach the CareLens API.', 0)
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* empty or non-JSON body */
  }
  if (res.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event('cl:unauthorized'))
  if (!res.ok) throw new ApiError(detailText(data?.detail) || `Request failed (${res.status}).`, res.status)
  return data
}

export const authApi = {
  me: () => api('/auth/me'),
  login: (email, password) => api('/auth/login', { method: 'POST', body: { email, password } }),
  register: (email, password) => api('/auth/register', { method: 'POST', body: { email, password } }),
  logout: () => api('/auth/logout', { method: 'POST' }),
}
export const chatApi = { ask: (query, signal) => api('/chat', { method: 'POST', body: { query }, signal }) }
export const historyApi = {
  list: (search = '') => api(`/history${search ? `?search=${encodeURIComponent(search)}` : ''}`),
  get: (id) => api(`/history/${id}`),
  remove: (id) => api(`/history/${id}`, { method: 'DELETE' }),
}
export const aboutApi = { metrics: () => api('/about/metrics') }
