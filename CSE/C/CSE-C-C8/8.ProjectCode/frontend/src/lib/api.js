// Thin client for the PeerScope FastAPI backend. Every call throws an Error whose message is safe to show.
export const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8408').replace(/\/$/, '')

async function request(path, opts = {}) {
  let res
  try {
    res = await fetch(`${API}${path}`, opts)
  } catch (e) {
    if (e?.name === 'AbortError') throw e
    const err = new Error(`Cannot reach the PeerScope backend at ${API}. Start it with run.bat (or uvicorn app.main:app --port 8408) and try again.`)
    err.offline = true
    throw err
  }
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') msg = body.detail
      else if (Array.isArray(body.detail)) msg = body.detail.map((d) => d.msg).join('; ')
    } catch {
      /* non-JSON error body */
    }
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return res
}

const json = async (path, opts) => (await request(path, opts)).json()
const send = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const api = {
  health: () => json('/api/health'),
  metrics: () => json('/api/model/metrics'),
  reviewers: () => json('/api/reviewers'),
  createReviewer: (r) => json('/api/reviewers', send('POST', r)),
  updateReviewer: (id, r) => json(`/api/reviewers/${id}`, send('PUT', r)),
  deleteReviewer: (id) => json(`/api/reviewers/${id}`, { method: 'DELETE' }),
  importReviewers: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return json('/api/reviewers/import', { method: 'POST', body: fd })
  },
  analyze: (file, opts, signal) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('active_only', String(opts.activeOnly))
    fd.append('min_score', String(opts.minScore || 0))
    fd.append('topic', opts.topic || '')
    fd.append('method', opts.method || '')
    return json('/api/analyze', { method: 'POST', body: fd, signal })
  },
  analyses: () => json('/api/analyses'),
  analysis: (id) => json(`/api/analyses/${id}`),
}

export const exportPath = (id, format) => `/api/analyses/${id}/export?format=${format}`
export const REVIEWERS_CSV = '/api/reviewers/export/csv'

// Download through fetch so a failure shows a toast instead of a blank tab with JSON in it.
export async function download(path, fallbackName) {
  const res = await request(path)
  const blob = await res.blob()
  const cd = res.headers.get('Content-Disposition') || ''
  const name = (cd.match(/filename=([^;]+)/) || [])[1] || fallbackName
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}
