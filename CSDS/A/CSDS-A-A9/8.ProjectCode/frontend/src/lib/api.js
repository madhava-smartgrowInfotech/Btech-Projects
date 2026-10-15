// Thin client for the existing ForgetSafe JSON API (certified_unlearning/web.py).
// In dev, Vite proxies /api to the Python server on port 8109.
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body } = {}) {
  let res
  try {
    res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Could not reach the API server.', 0)
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) throw new ApiError(data?.error || `Request failed (${res.status})`, res.status)
  return data
}

export const api = {
  health: () => request('/api/health'),
  state: () => request('/api/state'),
  train: () => request('/api/train', { method: 'POST' }),
  newSession: () => request('/api/session', { method: 'POST' }),
  unlearn: (client_id) => request('/api/unlearn', { method: 'POST', body: { client_id } }),
  generate: (seed) => request('/api/generate', { method: 'POST', body: { seed } }),
  verifyAudit: () => request('/api/audit/verify', { method: 'POST' }),
  latestCertificate: () => request('/api/certificate/latest'),
}
