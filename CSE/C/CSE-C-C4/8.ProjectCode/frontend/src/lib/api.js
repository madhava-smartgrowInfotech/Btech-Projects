// Thin client for the QuantPulse FastAPI backend. Same-origin /api (Vite proxies it in dev).
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, { timeout = 30000, signal } = {}) {
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort(), timeout)
  signal?.addEventListener('abort', () => ctl.abort())
  try {
    const res = await fetch(`/api${path}`, { signal: ctl.signal, headers: { Accept: 'application/json' } })
    if (!res.ok) {
      let detail = res.statusText
      try {
        const body = await res.json()
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
      } catch {
        /* non-JSON error body */
      }
      throw new ApiError(detail || `Request failed (${res.status})`, res.status)
    }
    return await res.json()
  } catch (e) {
    if (e instanceof ApiError) throw e
    if (signal?.aborted) throw e
    if (e.name === 'AbortError') throw new ApiError('The API took too long to answer.', 0)
    throw new ApiError('Could not reach the QuantPulse API.', 0)
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  health: (o) => request('/health', o),
  tickers: (o) => request('/tickers', o),
  metrics: (o) => request('/metrics', o),
  tickerMetrics: (t, o) => request(`/metrics/${encodeURIComponent(t)}`, o),
  forecast: (t, horizon = 'short', o) => request(`/forecast/${encodeURIComponent(t)}?horizon=${horizon}`, o),
  history: (t, days = 120, o) => request(`/history/${encodeURIComponent(t)}?days=${days}`, o),
  // FinBERT loads on the first call (and downloads on a cold cache), so allow a long wait.
  sentiment: (t, o) => request(`/sentiment/${encodeURIComponent(t)}`, { timeout: 240000, ...o }),
}
