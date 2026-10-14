import { readStore, writeStore } from './storage'

const TOKEN_KEY = 'am.token'
const DEVICE_KEY = 'am.device'

let memoryDevice = null
let memoryToken = null

/** A persistent per-browser id; the backend mixes it into the device fingerprint the JWT is bound to. */
export function deviceId() {
  let id = readStore(DEVICE_KEY) || memoryDevice
  if (!id) {
    id = (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`
    memoryDevice = id
    writeStore(DEVICE_KEY, id)
  }
  return id
}

export const getToken = () => readStore(TOKEN_KEY) || memoryToken
export const setToken = (t) => {
  memoryToken = t
  writeStore(TOKEN_KEY, t)
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

let onUnauthorized = null
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

function describe(status, data) {
  if (data && typeof data.detail === 'string') return data.detail
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ')
  }
  if (status >= 500) return 'The server hit an error. Check that the backend is running and try again.'
  return `Request failed (${status}).`
}

/**
 * fetch wrapper: JSON or FormData bodies, bearer token, device id, readable errors.
 * `raw: true` returns the Response (used for file downloads).
 */
export async function api(path, { method = 'GET', body, form, raw = false, signal, auth = true } = {}) {
  const headers = { 'X-Device-Id': deviceId() }
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(path, { method, headers, body: payload, signal })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError('Cannot reach the Attendance Magic API. Start the backend (run.bat) and retry.', 0)
  }
  if (raw && res.ok) return res
  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: res.status >= 500 ? null : text.slice(0, 200) }
    }
  }
  if (!res.ok) {
    if (res.status === 401 && auth && token && onUnauthorized) onUnauthorized(describe(res.status, data))
    throw new ApiError(describe(res.status, data), res.status, data)
  }
  return data
}

/** Download a file from an authenticated endpoint. Returns the saved file name. */
export async function download(path, fallbackName) {
  const res = await api(path, { raw: true })
  const cd = res.headers.get('Content-Disposition') || ''
  const m = cd.match(/filename="?([^";]+)"?/)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = m ? m[1] : fallbackName
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
  return a.download
}

/** Session link in the same shape as the Streamlit link (`/?session=TOKEN`), pointing at this frontend. */
export const sessionLink = (token) => `${window.location.origin}/?session=${encodeURIComponent(token)}`
