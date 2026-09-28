import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 120000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hs_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('hs_token')
      localStorage.removeItem('hs_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorMessage(err) {
  const d = err?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ')
  if (d) return d
  if (err?.code === 'ERR_NETWORK') return 'Cannot reach the HospiSense server. Is the backend running?'
  return err?.message || 'Something went wrong'
}

export default api
