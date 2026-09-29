import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem('cw_token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      localStorage.removeItem('cw_token')
      localStorage.removeItem('cw_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export const errMsg = (e) => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ')
  if (e?.code === 'ERR_NETWORK') return 'Cannot reach the CareWatch server - is the backend running?'
  return e?.message || 'Something went wrong'
}

export const token = () => localStorage.getItem('cw_token') || ''

export const ACTIVITY_COLORS = {
  walking: '#0ea5e9',
  standing: '#22c55e',
  sitting: '#a855f7',
  lying: '#f97316',
  drinking: '#14b8a6',
  picking_up: '#eab308',
  away: '#cbd5e1',
}

export const label = (a) => (a || '').replace('_', ' ')

export const fmtDuration = (s) => {
  s = Math.round(s || 0)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h) return `${h}h ${m}m`
  if (m) return `${m}m ${sec}s`
  return `${sec}s`
}

export default api
