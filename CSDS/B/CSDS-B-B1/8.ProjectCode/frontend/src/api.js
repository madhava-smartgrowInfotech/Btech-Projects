import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 180000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cp_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('cp_token')
      localStorage.removeItem('cp_user')
      if (!location.pathname.startsWith('/login')) location.assign('/login')
    }
    return Promise.reject(err)
  },
)

export function errorMessage(err) {
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ')
  if (err?.code === 'ERR_NETWORK') return 'Cannot reach the CivicPulse server. Is the backend running?'
  return err?.message || 'Something went wrong'
}

export default api
