// Thin client for the Flask API. Vite proxies /api to the backend (see vite.config.js).
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options) {
  let res
  try {
    res = await fetch(path, options)
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
  if (!res.ok) throw new ApiError(body?.message || body?.error || `Request failed (${res.status}).`, res.status)
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
}
