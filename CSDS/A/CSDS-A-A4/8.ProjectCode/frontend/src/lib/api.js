// Thin client for the HubOptima FastAPI layer (proxied to :8104 by Vite).
export class ApiError extends Error {
  constructor(message, status, path) {
    super(message)
    this.status = status
    this.path = path
  }
}

async function request(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(path, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError('Could not reach the HubOptima API. Is the backend running on port 8104?', 0, path)
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* empty or non-JSON body */
  }
  if (!res.ok) {
    const detail =
      data?.error ||
      (Array.isArray(data?.detail) ? data.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join('; ') : data?.detail)
    const fallback = res.status >= 500 ? `The API failed (${res.status}). Check that the backend is running on port 8104.` : `Request failed (${res.status})`
    throw new ApiError(detail || fallback, res.status, path)
  }
  return data
}

export const api = {
  health: (o) => request('/api/health', o),
  summary: (o) => request('/api/summary', o),
  regions: (o) => request('/api/regions', o),
  options: (o) => request('/api/options', o),
  forecast: (o) => request('/api/forecast', o),
  forecastMetrics: (o) => request('/api/forecast/metrics', o),
  compare: (o) => request('/api/compare', o),
  scalability: (o) => request('/api/scalability', o),
  rolling: (o) => request('/api/rolling', o),
  jobs: (o) => request('/api/jobs', o),
  train: () => request('/api/train', { method: 'POST' }),
  optimize: (body) => request('/api/optimize', { method: 'POST', body }),
  runCompare: (body) => request('/api/compare/run', { method: 'POST', body }),
  runRolling: (body) => request('/api/rolling/run', { method: 'POST', body }),
}
