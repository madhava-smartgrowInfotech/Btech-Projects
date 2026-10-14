import axios from 'axios'
import { logEvent } from './lib/activity'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mq_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  config.metadata = { t0: performance.now() }
  return config
})

// Every call is recorded in the terminal log (method, path, status, time). Bodies are never logged.
function record(cfg, status, failed = false) {
  const ms = Math.round(performance.now() - (cfg?.metadata?.t0 ?? performance.now()))
  logEvent(failed ? 'error' : 'api', `${(cfg?.method || 'get').toUpperCase()} ${cfg?.url} -> ${status} (${ms} ms)`)
}

api.interceptors.response.use(
  (r) => {
    record(r.config, r.status)
    return r
  },
  (err) => {
    record(err.config, err.response?.status ?? 'network error', true)
    if (err.response?.status === 401 && localStorage.getItem('mq_token')) {
      localStorage.removeItem('mq_token')
      localStorage.removeItem('mq_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

/** { message, hint } for the ErrorState component, from any axios error */
export function describeError(e) {
  const status = e?.response?.status
  const detail = e?.response?.data?.detail
  const text = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((x) => x.msg).join(', ') : null
  if (!e?.response) {
    return {
      message: e?.code === 'ECONNABORTED' ? 'The server took too long to respond' : 'Cannot reach the server',
      hint: 'Check that the API is running on port 8215, then retry.',
    }
  }
  if (status === 401) return { message: text || 'Your session has ended', hint: 'Log in again to continue.' }
  if (status === 403) return { message: text || 'Your account cannot do this', hint: 'Use the account for that hospital or the district admin.' }
  if (status === 404) return { message: text || 'Not found', hint: 'It may have been removed. Go back and try again.' }
  if (status === 409 || status === 422) return { message: text || 'That request cannot be completed', hint: 'Change the highlighted input and try again.' }
  return {
    message: text || 'Something went wrong on the server',
    hint: status >= 500 ? 'Retry in a moment. If it keeps failing, check the API window.' : undefined,
  }
}

/** one-line message for toasts and inline text */
export const errMsg = (e) => describeError(e).message

export function wsUrl(hospitalId) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/ws/hospital/${hospitalId}`
}

export const todayStr = () => {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export const dateInDays = (n) => {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export default api
