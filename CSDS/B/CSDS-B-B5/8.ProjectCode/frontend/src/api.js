import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sb_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      localStorage.removeItem('sb_token')
      localStorage.removeItem('sb_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorText(err) {
  const d = err?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ')
  if (typeof d === 'string') return d
  if (err?.code === 'ERR_NETWORK') return 'Cannot reach the SignBridge server. Is it running?'
  return err?.message || 'Something went wrong'
}

export default api
