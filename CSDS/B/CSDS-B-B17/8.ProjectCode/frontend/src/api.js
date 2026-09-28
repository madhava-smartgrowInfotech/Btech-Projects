import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cs_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('cs_token')
      localStorage.removeItem('cs_user')
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorText(err) {
  const d = err?.response?.data
  if (typeof d?.detail === 'string') return d.detail
  if (Array.isArray(d?.detail)) return d.detail.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ')
  if (err?.message === 'Network Error') return 'Cannot reach the CallSense server. Is the backend running?'
  return err?.message || 'Something went wrong'
}

export const currentUser = () => JSON.parse(localStorage.getItem('cs_user') || '{}')
export const audioUrl = (id) => `/api/calls/${id}/audio?token=${encodeURIComponent(localStorage.getItem('cs_token') || '')}`

export const fmtTime = (t) => {
  if (t == null) return '-'
  const s = Math.max(0, Math.round(t))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}
export const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) : '-')
export const label = (s) => (s ? s.replaceAll('_', ' ') : '-')

export default api
