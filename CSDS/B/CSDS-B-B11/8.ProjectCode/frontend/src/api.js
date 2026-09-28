import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 120000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ns_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      localStorage.removeItem('ns_token')
      localStorage.removeItem('ns_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export function errorMessage(err) {
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ')
  if (err?.code === 'ECONNABORTED') return 'The request timed out. Please try again.'
  if (!err?.response) return 'Cannot reach the NutriSense server. Is the backend running?'
  return 'Something went wrong. Please try again.'
}

export const today = () => {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export default api
