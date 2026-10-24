// Thin client for the LabLens API (proxied to the backend on :8308 by Vite).
const BASE = import.meta.env.VITE_API_BASE || ''
const TOKEN_KEY = 'll-token'

export class ApiError extends Error {
  constructor(message, { status = 0, network = false } = {}) {
    super(message)
    this.status = status
    this.network = network
  }
}

const UNREACHABLE = 'Cannot reach the LabLens backend on port 8308. Start it with run.bat (or python -m uvicorn backend.main:app --port 8308) and try again.'

export const token = {
  get() {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(value) {
    try {
      value ? localStorage.setItem(TOKEN_KEY, value) : localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* storage unavailable - the session lasts until reload */
    }
  },
}

function failure(res, data, path) {
  if (res.status === 401 && path !== '/api/auth/login') {
    token.set(null)
    window.dispatchEvent(new Event('ll-unauthorized'))
  }
  const detail = typeof data?.detail === 'string' ? data.detail : null
  if (detail) return new ApiError(detail, { status: res.status })
  if (res.status === 502 || res.status === 504 || (res.status === 500 && !data)) return new ApiError(UNREACHABLE, { status: res.status, network: true })
  if (res.status === 422) return new ApiError('The request was not valid. Check the values and try again.', { status: 422 })
  return new ApiError(res.status >= 500 ? `The backend failed while handling ${path} (HTTP ${res.status}).` : `Request failed (HTTP ${res.status}).`, { status: res.status })
}

async function request(path, { method = 'GET', body, signal } = {}) {
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  const t = token.get()
  if (t) headers.Authorization = `Bearer ${t}`
  let res
  try {
    res = await fetch(BASE + path, { method, signal, headers, body: body ? JSON.stringify(body) : undefined })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError(UNREACHABLE, { network: true })
  }
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }
  if (!res.ok) throw failure(res, data, path)
  if (data === null) throw new ApiError(`Unexpected response from ${path}. Is the backend on port 8308 running?`, { status: res.status })
  return data
}

// Multipart upload with real byte progress (fetch cannot report upload progress).
function upload(path, form, { onProgress } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', BASE + path)
    const t = token.get()
    if (t) xhr.setRequestHeader('Authorization', `Bearer ${t}`)
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress?.(e.loaded / e.total)
    xhr.onerror = () => reject(new ApiError(UNREACHABLE, { network: true }))
    xhr.onload = () => {
      let data = null
      try {
        data = JSON.parse(xhr.responseText)
      } catch {
        data = null
      }
      if (xhr.status >= 200 && xhr.status < 300 && data) resolve(data)
      else reject(failure({ status: xhr.status }, data, path))
    }
    xhr.send(form)
  })
}

const qs = (params) => {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') s.set(k, v)
  })
  const str = s.toString()
  return str ? `?${str}` : ''
}

export const api = {
  config: () => request('/api/config'),
  login: (email, password) => request('/api/auth/login', { method: 'POST', body: { email, password } }),
  me: () => request('/api/auth/me'),
  dashboard: () => request('/api/dashboard'),
  reports: () => request('/api/reports'),
  report: (id) => request(`/api/reports/${id}`),
  deleteReport: (id) => request(`/api/reports/${id}`, { method: 'DELETE' }),
  uploadReport: (file, useLlm, onProgress) => {
    const form = new FormData()
    form.append('file', file)
    form.append('use_llm', useLlm ? 'true' : 'false')
    return upload('/api/reports', form, { onProgress })
  },
  tests: () => request('/api/tests'),
  trends: (test) => request(`/api/trends${qs({ test })}`),
  compare: (a, b) => request(`/api/compare${qs({ a, b })}`),
  insights: () => request('/api/insights'),
  seedDemo: () => request('/api/demo/seed', { method: 'POST' }),
}
