import { readStore, writeStore } from './storage'

const TOKEN_KEY = 'am.token'

export const getToken = () => readStore(TOKEN_KEY)
export const setToken = (t) => writeStore(TOKEN_KEY, t)

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

async function request(path, { method = 'GET', body, form, raw } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError('Cannot reach the ATHENA API.', 0)
  }
  if (!res.ok) {
    let detail = null
    try {
      detail = (await res.json()).detail
    } catch {
      /* not json */
    }
    const msg =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => `${(d.loc || []).slice(-1)[0]}: ${d.msg}`).join('; ')
          : `Request failed (${res.status}).`
    if (res.status === 401 && token && path !== '/auth/login') window.dispatchEvent(new Event('athena:unauthorized'))
    throw new ApiError(msg, res.status, detail)
  }
  return raw ? res : res.json()
}

export const api = {
  login: (email, password) => request('/auth/login', { method: 'POST', body: { email, password } }),
  me: () => request('/auth/me'),
  publicStats: () => request('/public/stats'),
  samples: () => request('/samples'),
  sampleFile: async (name) => {
    const res = await request(`/samples/${encodeURIComponent(name)}`, { raw: true })
    const blob = await res.blob()
    return new File([blob], name, { type: blob.type })
  },
  extract: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/reports/extract', { method: 'POST', form })
  },
  createPatient: (payload) => request('/patients', { method: 'POST', body: payload }),
  patients: () => request('/patients'),
  patient: (id) => request(`/patients/${id}`),
  override: (id, priority, reason) => request(`/patients/${id}/override`, { method: 'POST', body: { priority, reason } }),
  metrics: () => request('/metrics'),
  downloadSummary: async (id) => {
    const res = await request(`/patients/${id}/summary.pdf`, { raw: true })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `athena-triage-${id}.pdf`
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 2000)
  },
}
