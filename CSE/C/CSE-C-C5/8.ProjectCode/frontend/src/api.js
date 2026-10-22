import axios from 'axios'
import { logEvent } from './lib/activity'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((cfg) => {
  cfg.meta = { t0: performance.now() }
  return cfg
})

api.interceptors.response.use(
  (res) => {
    if (!res.config.silent) {
      logEvent('api', `${res.config.method.toUpperCase()} ${res.config.url} ${res.status} ${Math.round(performance.now() - res.config.meta.t0)}ms`)
    }
    return res
  },
  (err) => {
    if (!err.config?.silent) {
      logEvent('error', `${err.config?.method?.toUpperCase() ?? 'REQ'} ${err.config?.url ?? ''} ${err.response?.status ?? 'network error'}`)
    }
    return Promise.reject(err)
  },
)

// { message, hint } for ErrorState: says what failed and what to do.
export function describeError(e) {
  if (!e.response) {
    return { message: 'Could not reach the placement API.', hint: 'Start the backend (run.bat, or uvicorn backend.main:app --port 8405) and retry.' }
  }
  const d = e.response.data?.detail
  const message = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ') : `Request failed (${e.response.status})`
  const hint = e.response.status >= 500 ? 'The server hit an error - check the backend console, then retry.' : e.response.status === 503 ? 'Model or data files are missing - see docs/03_HOW_TO_RUN.md.' : 'Check the values you entered and try again.'
  return { message, hint }
}

export const errorMessage = (e) => describeError(e).message

export default api
