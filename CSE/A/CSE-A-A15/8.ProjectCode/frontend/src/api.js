import axios from 'axios'
import { logEvent } from './lib/activity'

const api = axios.create({ baseURL: '/api' })

export const getToken = () => localStorage.getItem('cv_token')
export const getUser = () => localStorage.getItem('cv_user')
export function setSession(token, username) {
  localStorage.setItem('cv_token', token)
  localStorage.setItem('cv_user', username)
}
export function clearSession() {
  localStorage.removeItem('cv_token')
  localStorage.removeItem('cv_user')
}

api.interceptors.request.use((cfg) => {
  const t = getToken()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  cfg.metadata = { start: performance.now() }
  return cfg
})

// Every call shows up in the activity log, except polling marked `silent`. Only method, path and status are logged.
const label = (cfg) => `${(cfg.method || 'get').toUpperCase()} ${cfg.url}`

api.interceptors.response.use(
  (r) => {
    if (!r.config.silent) {
      const ms = Math.round(performance.now() - (r.config.metadata?.start ?? performance.now()))
      logEvent('api', `${label(r.config)} · ${r.status} · ${ms} ms`)
    }
    return r
  },
  (err) => {
    const cfg = err.config || {}
    if (!cfg.silent) logEvent('error', `${label(cfg)} · ${err.response ? err.response.status : 'no response'}`)
    if (err.response?.status === 401 && !cfg.url?.startsWith('/auth/')) {
      clearSession()
      window.location.assign('/login')
    }
    return Promise.reject(err)
  },
)

/** What failed and what to do next, for any failed request. */
export function describeError(err) {
  if (!err?.response) return { message: 'Cannot reach the server.', hint: 'Start the backend (run.bat) and try again.' }
  const { status, data } = err.response
  const d = data?.detail
  const detail = typeof d === 'string' ? d : Array.isArray(d) ? d.map((x) => x.msg).join('; ') : null
  const hint = status === 404 ? 'It may have been deleted. Refresh the list and pick another.'
    : status === 413 ? 'Choose a file under 25 MB.'
    : status === 400 ? 'Check the inputs above and try again.'
    : status >= 500 ? 'The server hit an error. The backend window has the traceback.'
    : null
  return { message: detail || `Request failed (${status}).`, hint }
}

export const errText = (err) => describeError(err).message

export async function blobUrl(path) {
  const r = await api.get(path, { responseType: 'blob' })
  return URL.createObjectURL(r.data)
}

export async function download(path, filename) {
  const url = await blobUrl(path)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export function saveText(text, filename) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain' }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export const fmtBytes = (n) =>
  n == null ? '-' : n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KiB` : `${(n / 1048576).toFixed(2)} MiB`

export const fmtMs = (n) => (n == null ? '-' : n < 1000 ? `${n.toFixed(n < 10 ? 2 : 1)} ms` : `${(n / 1000).toFixed(2)} s`)

export default api
