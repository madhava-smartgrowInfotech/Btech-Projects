import axios from 'axios'
import { readStore, writeStore } from './lib/storage'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = readStore('cs_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.includes('/auth/login')) {
      writeStore('cs_token', null)
      writeStore('cs_user', null)
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorText(err) {
  const d = err?.response?.data
  if (typeof d?.detail === 'string') return d.detail
  if (Array.isArray(d?.detail)) return d.detail.map((x) => `${x.loc?.slice(-1)[0]}: ${x.msg}`).join('; ')
  if (err?.message === 'Network Error' || err?.code === 'ERR_NETWORK') return 'Cannot reach the CallSense server. Is the backend running?'
  return err?.message || 'Something went wrong'
}

export const audioUrl = (id) => `/api/calls/${id}/audio?token=${encodeURIComponent(readStore('cs_token') || '')}`

export default api
