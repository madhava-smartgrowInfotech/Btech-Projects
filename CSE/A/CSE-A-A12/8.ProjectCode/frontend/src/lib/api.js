// Thin fetch wrapper for the FastAPI backend (proxied to /api by Vite).
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

const UNAUTH_EVENT = 'pd:unauthorized'

async function parse(res) {
  const body = await res.json().catch(() => null)
  if (res.ok) return body
  if (res.status === 401) window.dispatchEvent(new Event(UNAUTH_EVENT))
  const detail = body?.detail
  const msg =
    typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d) => d.msg).join('; ') : `Request failed (${res.status}).`
  throw new ApiError(msg, res.status)
}

async function request(path, opts = {}) {
  let res
  try {
    res = await fetch(path, { credentials: 'same-origin', ...opts })
  } catch {
    throw new ApiError('Cannot reach the API server.', 0)
  }
  return parse(res)
}

const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const onUnauthorized = (fn) => {
  window.addEventListener(UNAUTH_EVENT, fn)
  return () => window.removeEventListener(UNAUTH_EVENT, fn)
}

export const api = {
  health: () => request('/api/health'),
  me: () => request('/api/auth/me'),
  login: (email, password) => request('/api/auth/login', json('POST', { email, password })),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  stats: () => request('/api/stats'),
  predictions: (limit = 200) => request(`/api/predictions?limit=${limit}`),
  prediction: (id) => request(`/api/predictions/${id}`),
  remove: (id) => request(`/api/predictions/${id}`, { method: 'DELETE' }),

  /** Multipart upload with real progress. onProgress(0..1) covers the upload only. */
  predict(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/predict')
      xhr.withCredentials = true
      xhr.upload.onprogress = (e) => e.lengthComputable && onProgress?.(e.loaded / e.total)
      xhr.onerror = () => reject(new ApiError('Cannot reach the API server.', 0))
      xhr.onload = () => {
        let body = null
        try {
          body = JSON.parse(xhr.responseText)
        } catch {
          /* non-JSON error body */
        }
        if (xhr.status >= 200 && xhr.status < 300) return resolve(body)
        if (xhr.status === 401) window.dispatchEvent(new Event(UNAUTH_EVENT))
        const d = body?.detail
        reject(new ApiError(typeof d === 'string' ? d : `Analysis failed (${xhr.status}).`, xhr.status))
      }
      const form = new FormData()
      form.append('xray_image', file)
      xhr.send(form)
    })
  },
}
