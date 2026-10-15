import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 300000 })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('pv_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      localStorage.removeItem('pv_token')
      localStorage.removeItem('pv_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export async function errorMessage(err) {
  let detail = err?.response?.data?.detail
  if (err?.response?.data instanceof Blob) {
    try {
      detail = JSON.parse(await err.response.data.text()).detail
    } catch {
      detail = null
    }
  }
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ')
  return detail || err?.message || 'Something went wrong'
}

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem('pv_user'))
  } catch {
    return null
  }
}

export default api
