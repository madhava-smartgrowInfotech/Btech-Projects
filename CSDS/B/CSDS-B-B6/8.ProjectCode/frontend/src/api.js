import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('uh_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401 && !e.config.url.includes('/auth/login')) {
      localStorage.removeItem('uh_token')
      localStorage.removeItem('uh_user')
      window.location.href = '/login'
    }
    return Promise.reject(e)
  },
)

export function errMsg(e) {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ')
  if (e?.code === 'ERR_NETWORK') return 'Cannot reach the UniHealth server. Is it running?'
  return e?.message || 'Something went wrong'
}

export async function downloadBundle(personId) {
  const r = await api.get(`/records/${personId}/bundle`, { responseType: 'blob' })
  const url = URL.createObjectURL(r.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `unihealth-${personId}.fhir.json`
  a.click()
  URL.revokeObjectURL(url)
}

export const CATEGORIES = ['encounters', 'conditions', 'medications', 'labs', 'allergies']
export const HOSPITALS = { A: 'Northbridge General Hospital', B: 'Riverside Medical Center', C: 'Lakeview Clinic' }

export default api
