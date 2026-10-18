// Thin fetch client for the FastAPI backend. In dev/preview Vite proxies /api to the backend port.
const BASE = import.meta.env.VITE_API_URL || ''
const TOKEN_KEY = 'churniq-token'

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

async function request(method, path, { body, form, raw, auth = true } = {}) {
  const headers = {}
  if (auth && token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError('Cannot reach the API. Is the backend running on port 8314?', 0)
  }
  if (raw && res.ok) return res
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  if ([502, 503, 504].includes(res.status)) throw new ApiError('Cannot reach the API. Is the backend running on port 8314?', 0)
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
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== '' && s.set(k, v))
  const out = s.toString()
  return out ? `?${out}` : ''
}

export const api = {
  health: () => request('GET', '/api/health', { auth: false }),
  login: (email, password) => request('POST', '/api/auth/login', { body: { email, password }, auth: false }),
  me: () => get('/api/auth/me'),
  state: () => get('/api/state'),

  loadSample: () => request('POST', '/api/data/sample'),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('POST', '/api/data/upload', { form })
  },
  preview: (rows = 15) => get(`/api/data/preview${q({ rows })}`),
  dataConfig: () => get('/api/data/config'),
  saveConfig: (cfg) => request('PUT', '/api/data/config', { body: cfg }),
  quality: () => get('/api/data/quality'),
  prepare: () => request('POST', '/api/data/prepare'),

  eda: (filters, numeric) => get(`/api/eda${q({ filters: JSON.stringify(filters || {}), numeric })}`),
  dashboard: () => get('/api/dashboard'),

  train: (body) => request('POST', '/api/models/train', { body }),
  results: () => get('/api/models/results'),
  saveModel: (name) => request('POST', '/api/models/save', { body: { name } }),
  evaluation: () => get('/api/evaluation'),

  thresholds: () => get('/api/risk/thresholds'),
  saveThresholds: (t) => request('PUT', '/api/risk/thresholds', { body: t }),
  risk: () => get('/api/risk'),

  customers: (search = '', limit = 100) => get(`/api/customers${q({ search, limit })}`),
  customer: (id) => get(`/api/customers/${encodeURIComponent(id)}`),
  xaiGlobal: () => get('/api/xai/global'),
  xaiLocal: (id) => get(`/api/xai/local/${encodeURIComponent(id)}`),

  whatifSchema: (id) => get(`/api/whatif/schema${q({ customer_id: id })}`),
  whatif: (customer_id, changes) => request('POST', '/api/whatif', { body: { customer_id, changes } }),

  retention: (risk, limit) => get(`/api/retention${q({ risk, limit })}`),

  batchTemplate: async () => (await request('GET', '/api/batch/template', { raw: true })).blob(),
  batch: (file, includeDrivers) => {
    const form = new FormData()
    form.append('file', file)
    form.append('include_drivers', includeDrivers ? 'true' : 'false')
    return request('POST', '/api/batch/predict', { form })
  },

  monitoring: () => get('/api/monitoring'),
  drift: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('POST', '/api/monitoring/drift', { form })
  },
}
