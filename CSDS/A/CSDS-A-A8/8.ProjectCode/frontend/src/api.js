import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('biosight_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      localStorage.removeItem('biosight_token')
      localStorage.removeItem('biosight_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorText(err) {
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  if (err?.code === 'ERR_NETWORK') return 'Cannot reach the BioSight API - is the backend running on port 8108?'
  return err?.message || 'Something went wrong'
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem('biosight_user'))
  } catch {
    return null
  }
}

export function setSession(data) {
  localStorage.setItem('biosight_token', data.token)
  localStorage.setItem('biosight_user', JSON.stringify(data.user))
}

export function clearSession() {
  localStorage.removeItem('biosight_token')
  localStorage.removeItem('biosight_user')
}

export default api
