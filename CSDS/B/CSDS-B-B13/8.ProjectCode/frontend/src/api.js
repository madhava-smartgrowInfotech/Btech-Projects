import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('apisentry_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('apisentry_token')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// FastAPI returns `detail` as a string for our errors and as a list for validation errors.
export const errMsg = (e) => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  if (!e?.response && e?.message) return `Cannot reach the API (${e.message}). Is the backend running on port 8213?`
  return e?.message || 'Something went wrong'
}

export default api
