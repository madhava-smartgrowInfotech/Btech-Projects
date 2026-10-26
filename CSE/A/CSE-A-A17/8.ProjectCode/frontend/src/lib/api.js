export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

function describe(status, data) {
  if (data && typeof data.detail === 'string') return data.detail
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ')
  }
  if (status >= 500) return 'The server hit an error. Check the backend console and try again.'
  return `Request failed (${status}).`
}

/** fetch wrapper: JSON or FormData bodies, readable errors, status 0 when the API is unreachable. */
export async function api(path, { method = 'GET', body, form, signal } = {}) {
  const headers = {}
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
    throw new ApiError('Cannot reach the TrendCast API. Start the backend (run.bat) and retry.', 0)
  }
  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: res.status >= 500 ? null : text.slice(0, 200) }
    }
  }
  if (!res.ok) throw new ApiError(describe(res.status, data), res.status, data)
  return data
}
