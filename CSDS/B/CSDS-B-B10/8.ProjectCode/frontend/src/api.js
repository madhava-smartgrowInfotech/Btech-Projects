import axios from 'axios'
import { logEvent } from './lib/activity'

// Same-origin: Vite proxies /api to the backend (port 8210, see .env).
const api = axios.create({ baseURL: '/api' })

function token() {
  try {
    return localStorage.getItem('sc_token')
  } catch {
    return null
  }
}

api.interceptors.request.use((cfg) => {
  const t = token()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

// Every call is written to the activity log unless it is marked { silent: true } (background polling).
api.interceptors.response.use(
  (r) => {
    if (!r.config.silent) logEvent('api', `${r.config.method.toUpperCase()} ${r.config.url} · ${r.status}`)
    return r
  },
  (err) => {
    const cfg = err.config || {}
    const status = err.response?.status
    if (status === 401 && token() && !cfg.url?.startsWith('/auth/')) window.dispatchEvent(new Event('sc:signed-out'))
    if (!cfg.silent) logEvent('error', `${cfg.method?.toUpperCase() || 'GET'} ${cfg.url} · ${status || 'no response'}`)
    return Promise.reject(err)
  },
)

// Short message from an axios error (FastAPI puts the reason in `detail`).
export function errorMessage(e) {
  if (!e?.response) return 'Cannot reach the API. Is the backend running? run.bat starts it on port 8210.'
  const d = e.response.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  if (typeof d === 'string') return d
  return `Request failed (HTTP ${e.response.status})`
}

// { message, hint } shape for <ErrorState />
export function describeError(e, title) {
  const message = errorMessage(e)
  let hint = null
  if (!e?.response) hint = 'Start the backend (run.bat), then try again.'
  else if (e.response.status === 401) hint = 'Your session ended. Sign in again.'
  else if (e.response.status >= 500) hint = 'The server failed on this request. Try again, or check the API window.'
  return { message: title ? `${title}: ${message}` : message, hint }
}

export function wsUrl(path) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const sep = path.includes('?') ? '&' : '?'
  return `${proto}://${window.location.host}/api${path}${sep}token=${encodeURIComponent(token() || '')}`
}

export async function download(url, filename) {
  const r = await api.get(url, { responseType: 'blob' })
  const href = URL.createObjectURL(r.data)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(href), 1000)
}

// Source of an image: { file } | { kind, name } (sample) | { jobId } (saved studio job)
export function sourceForm(src, key) {
  const fd = new FormData()
  if (src.file) fd.append('file', src.file)
  else if (src.jobId) fd.append('job_id', src.jobId)
  else if (src.kind) {
    fd.append('sample_kind', src.kind)
    fd.append('sample_name', src.name)
  }
  if (key) fd.append('key', key)
  return fd
}

export default api
