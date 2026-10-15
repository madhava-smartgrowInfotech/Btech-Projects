// Thin fetch wrapper around the CareWatch API. The Vite dev server proxies /api to the backend.
const TOKEN_KEY = 'cw_token'
const USER_KEY = 'cw_user'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}
export const saveSession = (token, user) => {
  try {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch {
    /* storage blocked - the session lasts until reload */
  }
}
export const clearSession = () => {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  } catch {
    /* nothing stored */
  }
}
export const savedUser = () => {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    return null
  }
}

function detailMessage(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
  return ''
}

async function request(method, path, { body, params, signal } = {}) {
  const qs = params
    ? `?${new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null)).toString()}`
    : ''
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  let res
  try {
    res = await fetch(`/api${path}${qs}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal })
  } catch (e) {
    if (e?.name === 'AbortError') throw e
    throw new ApiError('Cannot reach the CareWatch server. Is the backend running on port 8208?', 0)
  }
  if (!res.ok) {
    let msg = ''
    try {
      msg = detailMessage((await res.json()).detail)
    } catch {
      /* non-JSON error body */
    }
    if (res.status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/register')) {
      window.dispatchEvent(new Event('cw:unauthorized'))
    }
    throw new ApiError(msg || `Request failed (${res.status})`, res.status)
  }
  return res.json()
}

export const api = {
  get: (path, opts) => request('GET', path, opts),
  post: (path, body, opts) => request('POST', path, { ...opts, body: body ?? {} }),
  put: (path, body, opts) => request('PUT', path, { ...opts, body }),
  del: (path, opts) => request('DELETE', path, opts),
}

// <img> tags cannot send headers, so the backend also accepts ?token=
export const authedUrl = (path, extra = '') => `/api${path}?token=${encodeURIComponent(getToken())}${extra}`
