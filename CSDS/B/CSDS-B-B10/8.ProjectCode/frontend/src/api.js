import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('sc_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      localStorage.removeItem('sc_token')
      localStorage.removeItem('sc_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errMsg(e) {
  const d = e?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  return d || e?.message || 'Something went wrong'
}

export function wsUrl(path) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api${path}${path.includes('?') ? '&' : '?'}token=${localStorage.getItem('sc_token')}`
}

export async function download(url, filename) {
  const r = await api.get(url, { responseType: 'blob' })
  const href = URL.createObjectURL(r.data)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  a.click()
  URL.revokeObjectURL(href)
}

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
