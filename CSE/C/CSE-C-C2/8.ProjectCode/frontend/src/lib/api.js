// Thin fetch wrapper for the StoryVox FastAPI backend. Errors carry the backend's `detail` message.
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(path, options)
  } catch {
    throw new ApiError('Could not reach the StoryVox server.', 0)
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join('; ') : data.detail
    throw new ApiError(detail || `Request failed (${res.status})`, res.status)
  }
  return data
}

const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const api = {
  health: () => request('/api/health'),
  languages: () => request('/api/languages'),
  meta: () => request('/api/meta'),
  generate: (payload) => request('/api/stories/generate', json('POST', payload)),
  synthesize: (id) => request(`/api/stories/${id}/synthesize`, { method: 'POST' }),
  stories: (limit = 100) => request(`/api/stories?limit=${limit}`),
  story: (id) => request(`/api/stories/${id}`),
  deleteStory: (id) => request(`/api/stories/${id}`, { method: 'DELETE' }),
  evaluations: () => request('/api/evaluations'),
  runEvaluation: (payload) => request('/api/evaluations/run', json('POST', payload)),
}

export const audioUrl = (id) => `/api/audio/${id}`
