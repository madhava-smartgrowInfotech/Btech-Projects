// Thin client for the Flask API. Vite proxies /api to the backend (see vite.config.js).
const BASE = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, opts = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, opts)
  } catch {
    throw new ApiError('Cannot reach the API server.', 0)
  }
  let body = null
  try {
    body = await res.json()
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) throw new ApiError(body?.error || `Request failed (${res.status})`, res.status)
  return body
}

const post = (path, data) =>
  request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data ?? {}) })

export const api = {
  health: () => request('/api/health'),
  datasetInfo: () => request('/api/dataset_info'),
  datasetStats: () => request('/api/dataset_stats'),
  generateDataset: (n_fraud, n_legit) => post('/api/generate_dataset', { n_fraud, n_legit }),
  preprocess: (method, top_k) => post('/api/preprocess', { method, top_k }),
  featureImportance: () => request('/api/feature_importance'),
  train: (modes, epochs, n_hidden) => post('/api/train', { modes, epochs, n_hidden }),
  trainStatus: () => request('/api/train_status'),
  modelHistory: () => request('/api/model_history'),
  comparison: () => request('/api/comparison'),
  qubo: (mode) => request(`/api/qubo?mode=${encodeURIComponent(mode)}`),
  predictSingle: (payload) => post('/api/predict_single', payload),
  predictBatch: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('/api/predict_batch', { method: 'POST', body: fd })
  },
  exportUrl: `${BASE}/api/export_predictions`,
  sampleUrl: `${BASE}/api/sample_batch`,
}
