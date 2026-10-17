// Thin client for the Flask API. Vite proxies /api to the backend (see vite.config.js).
import { readStore, writeStore } from './storage'

export class ApiError extends Error {
  constructor(message, status, field) {
    super(message)
    this.status = status
    this.field = field
  }
}

const TOKEN_KEY = 'resqai.token'
let token = readStore(TOKEN_KEY)
let onUnauthorized = () => {}

export const getToken = () => token
export function setToken(t) {
  token = t || null
  writeStore(TOKEN_KEY, token || '')
}
/** AuthProvider registers a callback so any 401 on a protected call signs the user out. */
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(path, { ...options, headers })
  } catch {
    throw new ApiError('Could not reach the ResQAI API.', 0)
  }
  let body = null
  try {
    body = await res.json()
  } catch {
    /* non-JSON body */
  }
  // The dev proxy answers 5xx with an empty body when Flask is down; treat that as "unreachable".
  if (!res.ok && body === null && res.status >= 500) throw new ApiError('Could not reach the ResQAI API.', 0)
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith('/api/auth/login') && !path.startsWith('/api/auth/register')) onUnauthorized()
    throw new ApiError(body?.message || body?.error || `Request failed (${res.status}).`, res.status, body?.field)
  }
  return body
}

const post = (path, payload) =>
  request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })

export const api = {
  health: () => request('/api/health'),
  simulate: (scenario = 'random') => request(`/api/simulate?scenario=${encodeURIComponent(scenario)}`),
  predict: (reading) => post('/api/predict', reading),
  hospitals: ({ lat, lon, k = 5 } = {}) => {
    const q = new URLSearchParams({ k })
    if (lat !== undefined && lon !== undefined) {
      q.set('lat', lat)
      q.set('lon', lon)
    }
    return request(`/api/hospitals?${q}`)
  },
  emergency: (payload) => post('/api/emergency', payload),
  login: (email, password) => post('/api/auth/login', { email, password }),
  register: (name, email, password) => post('/api/auth/register', { name, email, password }),
  me: () => request('/api/auth/me'),
}
