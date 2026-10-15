import axios from 'axios'
import { logEvent } from './lib/activity'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((config) => {
  config.meta = { t: performance.now() }
  let token = null
  try { token = localStorage.getItem('sb_token') } catch { /* storage blocked */ }
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

const route = (c) => `${(c.method || 'get').toUpperCase()} ${String(c.url).split('?')[0]}`

api.interceptors.response.use(
  (r) => {
    if (!r.config.silent) logEvent('api', `${route(r.config)} ${r.status} ${Math.round(performance.now() - r.config.meta.t)}ms`)
    return r
  },
  (err) => {
    const cfg = err.config
    if (cfg && !cfg.silent) logEvent('error', `${route(cfg)} ${err.response?.status ?? 'network error'}`)
    if (err.response?.status === 401 && cfg && !cfg.url.startsWith('/auth/')) {
      try { localStorage.removeItem('sb_token'); localStorage.removeItem('sb_user') } catch { /* ignore */ }
      window.dispatchEvent(new Event('sb:unauthorized'))
    }
    return Promise.reject(err)
  },
)

/** Plain message for any request error. */
export function errorMessage(err) {
  const d = err?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ')
  if (typeof d === 'string') return d
  if (err?.code === 'ERR_NETWORK') return 'Cannot reach the SignBridge server.'
  if (err?.code === 'ECONNABORTED') return 'The server took too long to answer.'
  return err?.message || 'Something went wrong'
}

/** { message, hint } - what failed and what to do about it. */
export function describeError(err) {
  const status = err?.response?.status
  const message = errorMessage(err)
  let hint = 'Try again in a moment.'
  if (err?.code === 'ERR_NETWORK') hint = 'Start the backend with run.bat (port 8205) and retry.'
  else if (status === 401) hint = 'Sign in again to continue.'
  else if (status === 503) hint = 'The offline speech model is still loading. Wait a few seconds and retry.'
  else if (status === 413) hint = 'Send a shorter clip.'
  else if (status && status >= 500) hint = 'Check the backend window for the error and retry.'
  else if (status && status >= 400) hint = 'Check the input and retry.'
  return { message, hint }
}

export const errorText = errorMessage
export default api
