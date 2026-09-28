import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('rg_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('rg_token')
      localStorage.removeItem('rg_user')
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorText(err) {
  const d = err?.response?.data
  if (d instanceof Blob) return 'Request failed'
  if (typeof d?.detail === 'string') return d.detail
  if (Array.isArray(d?.detail)) return d.detail.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ')
  if (err?.message === 'Network Error') return 'Cannot reach the RetinaGuard server. Is the backend running?'
  return err?.message || 'Something went wrong'
}

export const pct = (p) => (p == null ? '-' : `${Math.round(p * 100)}%`)

export default api
