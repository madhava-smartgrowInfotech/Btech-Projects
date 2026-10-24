// Thin fetch client for the BotGraph API. In dev/preview Vite proxies /api to the backend port.
const BASE = import.meta.env.VITE_API_URL || ''
const TOKEN_KEY = 'botgraph-token'

let token = null
let onUnauthorized = () => {}

try {
  token = localStorage.getItem(TOKEN_KEY)
} catch {
  /* storage blocked */
}

export function setToken(t) {
  token = t
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* storage blocked */
  }
}
export const getToken = () => token
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

function detailText(d) {
  if (!d) return ''
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((e) => (e.loc ? `${e.loc.slice(1).join('.')}: ${e.msg}` : e.msg || String(e))).join('; ')
  return JSON.stringify(d)
}

async function request(method, path, { body, auth = true } = {}) {
  const headers = {}
  if (auth && token) headers.Authorization = `Bearer ${token}`
  let payload
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError('Cannot reach the API. Is the backend running on port 8309?', 0)
  }
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  if ([502, 503, 504].includes(res.status)) throw new ApiError('Cannot reach the API. Is the backend running on port 8309?', 0)
  if (!res.ok) {
    if (res.status === 401 && auth && path !== '/api/auth/login') onUnauthorized()
    const msg = detailText(data?.detail) || (res.status >= 500 ? 'The server hit an error.' : `Request failed (${res.status}).`)
    throw new ApiError(msg, res.status)
  }
  return data
}

const get = (p) => request('GET', p)
const q = (params) => {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && v !== false && s.set(k, v))
  const out = s.toString()
  return out ? `?${out}` : ''
}

export const api = {
  health: () => request('GET', '/api/health', { auth: false }),
  login: (email, password) => request('POST', '/api/auth/login', { body: { email, password }, auth: false }),
  me: () => get('/api/auth/me'),

  overview: () => get('/api/overview'),
  graph: () => get('/api/graph/summary'),

  accounts: (params) => get(`/api/accounts${q(params)}`),
  account: (id) => get(`/api/accounts/${id}`),
  neighbourhood: (id, limit = 40) => get(`/api/accounts/${id}/neighbourhood${q({ limit })}`),

  clusters: () => get('/api/clusters'),
  cluster: (id) => get(`/api/clusters/${encodeURIComponent(id)}`),

  queue: (params) => get(`/api/queue${q(params)}`),
  decide: (target_type, target_id, decision, note = '') => request('POST', '/api/queue/decisions', { body: { target_type, target_id: String(target_id), decision, note } }),
  undo: (id) => request('DELETE', `/api/queue/decisions/${id}`),
  decisions: () => get('/api/decisions'),

  models: () => get('/api/models'),
  scalability: () => get('/api/models/scalability'),
  retrain: () => request('POST', '/api/models/retrain'),
  retrainStatus: () => get('/api/models/retrain/status'),
}
