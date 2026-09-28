import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mq_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem('mq_token')) {
      localStorage.removeItem('mq_token')
      localStorage.removeItem('mq_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errMsg(e) {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ')
  if (e?.code === 'ERR_NETWORK') return 'Cannot reach the server - is the backend running?'
  return e?.message || 'Something went wrong'
}

export function wsUrl(hospitalId) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/ws/hospital/${hospitalId}`
}

export const todayStr = () => {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export default api
