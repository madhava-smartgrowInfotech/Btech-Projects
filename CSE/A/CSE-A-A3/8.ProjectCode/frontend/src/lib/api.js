const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, options)
  } catch {
    throw new ApiError('Cannot reach the prediction API. Start the backend (run.bat) and try again.', 0)
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, res.status)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  diseases: () => request('/api/diseases'),
  disease: (key) => request(`/api/diseases/${key}`),
  sample: (key, outcome) => request(`/api/diseases/${key}/sample${outcome === undefined ? '' : `?outcome=${outcome}`}`),
  predict: (key, values) =>
    request(`/api/predict/${key}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ values }) }),
  report: () => request('/api/report'),
  datasets: () => request('/api/datasets'),
}
