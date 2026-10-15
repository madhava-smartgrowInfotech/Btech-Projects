// Thin client for the PlastiScan FastAPI layer (proxied to :8114 by Vite in dev/preview).

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options) {
  let res
  try {
    res = await fetch(`/api${path}`, options)
  } catch {
    throw new ApiError('Could not reach the PlastiScan API.', 0)
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => d.msg).join(' ')
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, res.status)
  }
  return res.json()
}

export const api = {
  health: () => request('/health'),
  reloadModel: () => request('/model/reload', { method: 'POST' }),
  detect: ({ file, conf, preprocess }) => {
    const body = new FormData()
    body.append('file', file)
    body.append('conf', String(conf))
    body.append('preprocess', String(preprocess))
    return request('/detect', { method: 'POST', body })
  },
  history: () => request('/history'),
  clearHistory: () => request('/history', { method: 'DELETE' }),
  evaluation: () => request('/evaluation'),
}
