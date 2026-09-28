import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 180000 })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('tt_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem('tt_token')) {
      localStorage.removeItem('tt_token')
      localStorage.removeItem('tt_user')
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errMsg(e) {
  if (e && !e.isAxiosError) return e.message || 'Something went wrong'
  const d = e?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  if (d) return d
  if (e?.code === 'ECONNABORTED') return 'The request timed out - please try again'
  if (!e?.response) return 'Cannot reach the TalentTrack API - is the backend running on port 8209?'
  return e.message || 'Something went wrong'
}

export default api
