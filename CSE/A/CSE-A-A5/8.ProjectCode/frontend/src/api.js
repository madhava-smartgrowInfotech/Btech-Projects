import axios from 'axios'
import { logEvent } from './lib/activity'

// In dev and `vite preview` the /api prefix is proxied to the FastAPI backend (see vite.config.js).
const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((cfg) => {
  cfg.meta = { t0: performance.now() }
  return cfg
})
api.interceptors.response.use(
  (res) => {
    if (!res.config.silent) logEvent('api', `${res.config.method.toUpperCase()} ${res.config.url} -> ${res.status} (${Math.round(performance.now() - res.config.meta.t0)} ms)`)
    return res
  },
  (err) => {
    if (!err.config?.silent) logEvent('error', `${err.config?.method?.toUpperCase() ?? 'REQ'} ${err.config?.url ?? ''} -> ${err.response?.status ?? 'no response'}`)
    return Promise.reject(err)
  },
)

// Turns any thrown error into { message, hint } for <ErrorState>.
export function describeError(err) {
  if (!err.response) {
    return { message: 'Cannot reach the CipherGuard API.', hint: 'Start the backend with run.bat (it listens on port 8305), then retry.' }
  }
  const { status, data } = err.response
  const detail = typeof data?.detail === 'string' ? data.detail : Array.isArray(data?.detail) ? data.detail.map((d) => d.msg).join('; ') : null
  if (status === 503) return { message: detail || 'The IDS engine is not ready.', hint: 'Train the model (python -m cipherguard.ids.train) and restart the backend.' }
  if (status === 404) return { message: detail || 'Not found.', hint: 'The report may not exist yet. Train the model first.' }
  if (status === 413) return { message: 'The upload is too large.', hint: 'Use a smaller file.' }
  if (status >= 500) return { message: detail || 'The server hit an error.', hint: 'Check the backend console for the traceback.' }
  return { message: detail || `Request failed (${status}).`, hint: null }
}

export const errorMessage = (err) => describeError(err).message

export default api
