// Thin fetch wrapper for the FinSight Flask API (proxied by Vite in dev / preview).
export class ApiError extends Error {
  constructor(message, status, errors = []) {
    super(message)
    this.status = status
    this.errors = errors
  }
}

async function request(path, options) {
  let res
  try {
    res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options })
  } catch {
    throw new ApiError('Could not reach the FinSight API.', 0)
  }
  let body = null
  try {
    body = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) {
    const errors = body?.errors || []
    throw new ApiError(errors[0] || `Request failed (${res.status}).`, res.status, errors)
  }
  return body
}

const post = (path, data) => request(path, { method: 'POST', body: JSON.stringify(data) })

export const api = {
  health: () => request('/health'),
  options: () => request('/api/options'),
  dashboard: () => request('/api/dashboard'),
  explain: () => request('/api/explain'),
  performance: () => request('/api/performance'),
  forecast: () => request('/api/forecast'),
  predict: (data) => post('/api/predict', data).then((r) => r.result),
  whatif: (data) => post('/api/whatif', data).then((r) => r.result),
}
