import axios from 'axios'

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
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      clearSession()
      window.location.assign('/login')
    }
    return Promise.reject(err)
  },
)

/** Human-readable message from any failed request (also decodes blob error bodies). */
export function errText(err) {
  const d = err?.response?.data
  if (d?.detail) return typeof d.detail === 'string' ? d.detail : d.detail.map((x) => x.msg).join('; ')
  if (err?.response) return `Request failed (${err.response.status})`
  return 'Cannot reach the server. Is the backend running?'
}

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
