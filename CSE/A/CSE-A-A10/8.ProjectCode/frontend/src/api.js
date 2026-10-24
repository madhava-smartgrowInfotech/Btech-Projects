import axios from 'axios'
import { logEvent } from './lib/activity'

const TOKEN_KEY = 'fs_token'
export const getToken = () => {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export const setToken = (t) => {
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) } catch { /* private mode */ }
}

const api = axios.create({ baseURL: '/api', timeout: 180000 })

api.interceptors.request.use((cfg) => {
  const t = getToken()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  cfg.meta = { start: performance.now() }
  return cfg
})

api.interceptors.response.use(
  (res) => {
    if (!res.config.silent) logEvent('api', `${res.config.method?.toUpperCase()} ${res.config.url} -> ${res.status} (${Math.round(performance.now() - res.config.meta.start)} ms)`)
    return res
  },
  (err) => {
    const c = err.config || {}
    if (!c.silent) logEvent('error', `${c.method?.toUpperCase()} ${c.url} -> ${err.response?.status || 'no response'}`)
    if (err.response?.status === 401 && !String(c.url).includes('/auth/login')) {
      setToken(null)
      window.dispatchEvent(new Event('fs:unauthorized'))
    }
    return Promise.reject(err)
  },
)

// { message, hint } that always says what failed and what to do about it.
export function describeError(e) {
  const d = e?.response?.data?.detail
  if (d && typeof d === 'object' && d.message) return { message: d.message, hint: d.hint || '', status: e.response.status }
  if (typeof d === 'string') return { message: d, hint: '', status: e.response?.status }
  if (e?.code === 'ECONNABORTED') return { message: 'The request took too long.', hint: 'The simulator may be busy - try again in a moment.' }
  if (!e?.response) return { message: 'Cannot reach the FlowSense API.', hint: 'Start the backend (run.bat) and check that port 8310 is free, then retry.' }
  return { message: `The server answered ${e.response.status}.`, hint: 'Retry; if it keeps failing, check the backend window for the error.', status: e.response.status }
}
export const errorMessage = (e) => describeError(e).message

export default api
