// Small fetch wrapper for the SkillVerse API. Requests go to /api (proxied to the backend by Vite).
const BASE = import.meta.env.VITE_API_URL || '/api'
const KEY = 'sv-token'

export const tokenStore = {
  get() {
    try {
      return localStorage.getItem(KEY)
    } catch {
      return null
    }
  },
  set(t) {
    try {
      if (t) localStorage.setItem(KEY, t)
      else localStorage.removeItem(KEY)
    } catch {
      /* storage unavailable - the session just won't survive a reload */
    }
  },
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function detailText(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ')
  return JSON.stringify(detail)
}

async function request(method, path, body) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch {
    throw new ApiError('Cannot reach the SkillVerse server. Check that the backend is running on port 8203, then try again.', 0)
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* empty or non-JSON body */
  }
  if (!res.ok) {
    if (res.status === 401 && token) onUnauthorized()
    throw new ApiError(detailText(data?.detail) || `Request failed (${res.status}).`, res.status)
  }
  return data
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b = {}) => request('POST', p, b),
  put: (p, b = {}) => request('PUT', p, b),
  del: (p) => request('DELETE', p),
}
