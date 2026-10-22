// Thin fetch client for the VeriVision Flask API (proxied by Vite, see vite.config.js).
const TOKEN_KEY = 'verivision-token'

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

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
    /* storage blocked */
  }
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn
}

async function request(path, { method = 'GET', body, auth = false, signal, allowStatus = [] } = {}) {
  const headers = {}
  if (auth || getToken()) {
    const t = getToken()
    if (t) headers.Authorization = `Bearer ${t}`
  }
  let init = { method, headers, signal }
  if (body instanceof FormData) init.body = body
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(path, init)
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Cannot reach the VeriVision API.', 0)
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok && !allowStatus.includes(res.status)) {
    if (res.status === 401 && auth) onUnauthorized()
    throw new ApiError(data?.error || data?.message || `Request failed (${res.status}).`, res.status, data)
  }
  return data
}

export const api = {
  // /health answers 503 with a JSON body when the models are not ready - that is data, not a failure.
  health: (signal) => request('/health', { allowStatus: [503], signal }),
  config: (signal) => request('/api/config', { signal }),
  insights: (signal) => request('/api/insights', { signal }),
  login: (email, password) => request('/api/auth/login', { method: 'POST', body: { email, password } }),
  me: () => request('/api/auth/me', { auth: true }),
  analyze: (file, signal) => {
    const fd = new FormData()
    fd.append('image', file)
    return request('/api/analyze', { method: 'POST', body: fd, auth: true, signal })
  },
}
