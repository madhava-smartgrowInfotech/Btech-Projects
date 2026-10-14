// Thin client for the PhishGuard API (proxied to the backend on :8103 by Vite).
const BASE = import.meta.env.VITE_API_BASE || ''

export class ApiError extends Error {
  constructor(message, { status = 0, network = false } = {}) {
    super(message)
    this.status = status
    this.network = network
  }
}

const UNREACHABLE =
  'Cannot reach the PhishGuard backend on port 8103. Start it with run.bat (or python backend/server.py) and try again.'

async function request(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError(UNREACHABLE, { network: true })
  }
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }
  if (!res.ok) {
    if ((res.status === 502 || res.status === 504 || res.status === 500) && !data) {
      throw new ApiError(UNREACHABLE, { status: res.status, network: true })
    }
    const msg =
      data?.error ||
      (res.status >= 500
        ? `The backend failed while handling ${path} (HTTP ${res.status}).`
        : `Request failed (HTTP ${res.status}).`)
    throw new ApiError(msg, { status: res.status })
  }
  if (data === null) {
    throw new ApiError(`Unexpected response from ${path}. Is the backend on port 8103 running?`, { status: res.status })
  }
  return data
}

const qs = (params) => {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') s.set(k, v)
  })
  const str = s.toString()
  return str ? `?${str}` : ''
}

export const api = {
  // original endpoints (phishguard/webapp.py)
  check: (url, opts) => request(`/api/check${qs({ url })}`, opts),
  report: (payload) => request('/api/report', { method: 'POST', body: payload }),
  stats: (opts) => request('/api/stats', opts),
  sync: () => request('/api/sync', { method: 'POST' }),
  // the existing background-retrain route used by the old Models page; it answers with a redirect
  async startRetrain() {
    let res
    try {
      res = await fetch(BASE + '/retrain', { method: 'POST', redirect: 'manual' })
    } catch {
      throw new ApiError(UNREACHABLE, { network: true })
    }
    if (res.type === 'opaqueredirect' || res.ok || (res.status >= 300 && res.status < 400)) return true
    throw new ApiError(`Could not start retraining (HTTP ${res.status}).`, { status: res.status })
  },
  // additive read-only endpoints (backend/server.py)
  health: () => request('/api/health'),
  config: () => request('/api/config'),
  checks: (limit = 20, opts) => request(`/api/checks${qs({ limit })}`, opts),
  intel: (limit = 200, status, opts) => request(`/api/intel${qs({ limit, status })}`, opts),
  lookup: (url, opts) => request(`/api/intel/lookup${qs({ url })}`, opts),
}
