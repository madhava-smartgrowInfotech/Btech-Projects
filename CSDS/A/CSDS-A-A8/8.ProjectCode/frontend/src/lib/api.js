// Thin fetch client for the BioSight API. The Vite dev server proxies /api to port 8108.
const TOKEN_KEY = 'bs-token'
const USER_KEY = 'bs-user'

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const read = (k) => {
  try {
    return localStorage.getItem(k)
  } catch {
    return null
  }
}

export const getToken = () => read(TOKEN_KEY)

export function getUser() {
  try {
    return JSON.parse(read(USER_KEY))
  } catch {
    return null
  }
}

export function setSession({ token, user }) {
  try {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch {
    /* storage blocked - session lasts until reload */
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  } catch {
    /* ignore */
  }
}

function detailText(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg || String(d)).join('; ')
  return ''
}

async function request(path, { method = 'GET', json, form, auth = true } = {}) {
  const headers = {}
  let body
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (form) {
    body = form
  }
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body })
  } catch {
    throw new ApiError('Cannot reach the BioSight API. Check that the backend is running on port 8108 (run.bat starts it).')
  }
  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = null
    }
  }
  if (!res.ok) {
    if (res.status === 401 && auth && token) {
      clearSession()
      window.dispatchEvent(new Event('bs-unauthorized'))
    }
    throw new ApiError(detailText(data?.detail) || `Request failed (HTTP ${res.status})`, res.status)
  }
  return data
}

export const api = {
  get: (path, opts) => request(path, opts),
  post: (path, json, opts) => request(path, { ...opts, method: 'POST', json }),
  upload: (path, form) => request(path, { method: 'POST', form }),
}

export const sampleUrl = (name) => `/api/mri/samples/${encodeURIComponent(name)}`
export const plotUrl = (name) => `/api/metrics/plot/${name}`
