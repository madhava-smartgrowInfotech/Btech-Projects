import axios from 'axios'
import { useCallback, useEffect, useState } from 'react'

const api = axios.create({ baseURL: '/api', timeout: 180000 })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('ts_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem('ts_token')) {
      localStorage.removeItem('ts_token')
      localStorage.removeItem('ts_user')
      if (!window.location.pathname.startsWith('/login')) window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export function errorMessage(err) {
  const d = err?.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  if (d) return d
  if (err?.code === 'ECONNABORTED') return 'The request timed out.'
  if (!err?.response) return 'Cannot reach the TaxSentinel API. Is the backend running on its port?'
  return err.message || 'Something went wrong'
}

// GET a path and keep loading / error / data state; reload() refetches.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const load = useCallback(() => {
    if (!path) return
    setState((s) => ({ ...s, loading: true, error: null }))
    api
      .get(path)
      .then((r) => setState({ data: r.data, error: null, loading: false }))
      .catch((e) => setState({ data: null, error: errorMessage(e), loading: false }))
  }, [path])
  useEffect(() => { load() }, [load])
  return { ...state, reload: load }
}

export default api
