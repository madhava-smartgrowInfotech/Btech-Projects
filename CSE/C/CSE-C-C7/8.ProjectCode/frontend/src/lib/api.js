/* Thin fetch wrapper. The Vite dev/preview server proxies /api to the FastAPI backend,
   so the HttpOnly lpq_token cookie is same-origin. */

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** FastAPI sends `detail` as a string, or as a list of {loc, msg} for 422 validation errors. */
function detailText(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : null
        return field && field !== 'body' ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return null
}

export async function api(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') throw e
    throw new ApiError('Could not reach the LearnPathIQ API.', 0)
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith('/api/auth/')) window.dispatchEvent(new Event('lpq:unauthorized'))
    throw new ApiError(detailText(data.detail) || `Request failed (${res.status})`, res.status)
  }
  return data
}

export const get = (path, opts) => api(path, opts)
export const post = (path, body) => api(path, { method: 'POST', body: body ?? {} })
export const put = (path, body) => api(path, { method: 'PUT', body })

/** Log a learning event; feeds the recommender's behavioural features. */
export const track = (course_id, event_type, value = 1.0) => post('/api/interactions', { course_id, event_type, value })
