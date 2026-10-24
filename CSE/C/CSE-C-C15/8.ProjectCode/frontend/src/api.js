import axios from 'axios'
import { logEvent } from './lib/activity'

// Same-origin: Vite proxies /api to the Flask backend (port in the project .env).
const api = axios.create({ baseURL: '/api', timeout: 15000 })

api.interceptors.request.use((cfg) => {
  cfg.metadata = { t0: performance.now() }
  return cfg
})
api.interceptors.response.use(
  (res) => {
    if (!res.config.silent) {
      logEvent('api', `${res.config.method.toUpperCase()} /api${res.config.url} -> ${res.status} (${Math.round(performance.now() - res.config.metadata.t0)} ms)`)
    }
    return res
  },
  (err) => {
    if (!err.config?.silent) logEvent('error', `${err.config?.method?.toUpperCase() || 'GET'} /api${err.config?.url || ''} failed: ${errorMessage(err)}`)
    return Promise.reject(err)
  },
)

// A short, human sentence for any failure.
export function errorMessage(err) {
  if (err?.response?.data?.error) return String(err.response.data.error)
  if (err?.code === 'ECONNABORTED') return 'The request timed out.'
  if (err?.response) return `The server answered ${err.response.status}.`
  if (err?.request) return 'The SentinelFlow API is not reachable.'
  return err?.message || 'Something went wrong.'
}

// { message, hint } for <ErrorState/>
export function describeError(err) {
  const status = err?.response?.status
  let hint = 'Check the request and try again.'
  if (!err?.response) hint = 'Start the backend with run.bat (it listens on the BACKEND_PORT from .env), then retry.'
  else if (status === 409) hint = 'Stop the running session first, then start a new one.'
  else if (status === 500) hint = 'The backend reported an internal error; see its console output.'
  return { message: errorMessage(err), hint }
}

export default api
