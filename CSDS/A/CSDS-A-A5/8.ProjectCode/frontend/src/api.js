import axios from 'axios'
import { useCallback, useEffect, useRef, useState } from 'react'
import { logEvent } from './lib/activity'

const api = axios.create({ baseURL: '/api', timeout: 180000 })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('ts_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  cfg.metadata = { start: performance.now() }
  return cfg
})

// Every non-silent call is traced into the activity log.
function trace(cfg, status) {
  if (!cfg || cfg.silent) return
  const ms = Math.round(performance.now() - (cfg.metadata?.start ?? performance.now()))
  const url = (cfg.url || '').length > 72 ? `${cfg.url.slice(0, 72)}…` : cfg.url
  logEvent(status && status < 400 ? 'api' : 'error', `${(cfg.method || 'get').toUpperCase()} /api${url} ${status || 'ERR'} ${ms}ms`)
}

api.interceptors.response.use(
  (r) => {
    trace(r.config, r.status)
    return r
  },
  (err) => {
    trace(err.config, err.response?.status)
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

// What failed + what to do about it
export function describeError(err) {
  const status = err?.response?.status
  const message = errorMessage(err)
  let hint = 'Retry. If it keeps failing, check the API window for errors.'
  if (!err?.response) hint = 'Start the API with run.bat (port 8105), then retry.'
  else if (status === 503) hint = 'The analysis is still loading after start-up. Wait a few seconds and retry.'
  else if (status === 404) hint = 'It is not in the current ecosystem - a new generation may have replaced it. Go back to the ranking.'
  else if (status === 409) hint = 'Wait for the running generation to finish.'
  else if (status === 502) hint = 'Check GEMINI_API_KEY in .env, or wait a minute if the free-tier quota is exhausted.'
  else if (status === 422) hint = 'Correct the highlighted values and submit again.'
  return { status, message, hint }
}

// GET a path and keep loading / error / data state; reload() refetches and keeps the old data visible.
export function useApi(path, { silent = false } = {}) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path })
  const alive = useRef(true)
  useEffect(() => {
    alive.current = true
    return () => { alive.current = false }
  }, [])
  const load = useCallback(() => {
    if (!path) return
    setState((s) => ({ ...s, loading: true, error: null }))
    api
      .get(path, { silent })
      .then((r) => alive.current && setState({ data: r.data, error: null, loading: false }))
      .catch((e) => alive.current && setState({ data: null, error: describeError(e), loading: false }))
  }, [path, silent])
  useEffect(() => { load() }, [load])
  return { ...state, reload: load }
}

export default api
