import type {
  Category,
  Explanation,
  FeedbackAction,
  FeedbackResponse,
  Paged,
  Persona,
  Product,
  RecommendationResponse,
  Review,
  SimulationHistoryEntry,
  SimulationRun,
  TrackEvent,
  TrafficSnapshot,
  AgentWeights,
  LoadProfile,
  WeightsHistoryPoint,
} from './types'

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'
).replace(/\/$/, '')

export const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws/traffic'

export class ApiError extends Error {
  status: number
  offline: boolean
  constructor(message: string, status: number, offline = false) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.offline = offline
  }
}

type QueryValue = string | number | boolean | undefined | null

function buildQuery(params: Record<string, QueryValue> = {}) {
  const usp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    usp.set(key, String(value))
  }
  const qs = usp.toString()
  return qs ? `?${qs}` : ''
}

async function request<T>(
  path: string,
  init: RequestInit & { timeoutMs?: number } = {},
): Promise<T> {
  const { timeoutMs = 12000, ...rest } = init
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(rest.body ? { 'Content-Type': 'application/json' } : {}),
        ...(rest.headers ?? {}),
      },
    })
  } catch (err) {
    clearTimeout(timer)
    const aborted = err instanceof DOMException && err.name === 'AbortError'
    throw new ApiError(
      aborted ? 'The service took too long to respond.' : 'Cannot reach the Nuvara service.',
      0,
      true,
    )
  }
  clearTimeout(timer)

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`
    try {
      const body = await res.json()
      if (body && typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, res.status)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

/** Fire-and-forget POST used for telemetry — never throws into the UI. */
async function beacon<T>(path: string, body: unknown): Promise<T | null> {
  try {
    return await request<T>(path, { method: 'POST', body: JSON.stringify(body), timeoutMs: 6000 })
  } catch {
    return null
  }
}

export const api = {
  /* ---------- catalog ---------- */
  categories: () => request<Category[]>('/categories'),

  products: (params: {
    category?: string
    q?: string
    sort?: string
    page?: number
    page_size?: number
  }) => request<Paged<Product>>(`/products${buildQuery(params)}`),

  product: (id: string | number) => request<Product>(`/products/${encodeURIComponent(String(id))}`),

  reviews: (id: string | number, page = 1) =>
    request<{ items: Review[]; total: number }>(
      `/products/${encodeURIComponent(String(id))}/reviews${buildQuery({ page })}`,
    ),

  /* ---------- identity ---------- */
  personas: () => request<Persona[]>('/users/demo-personas'),

  /* ---------- behaviour ---------- */
  trackEvent: (event: TrackEvent) => beacon<{ ok: boolean; event_id: string }>('/events', event),

  /* ---------- recommendations ---------- */
  recommendations: (params: {
    user_id?: string
    session_id: string
    context: 'home' | 'product' | 'cart' | 'search'
    product_id?: string | number
    limit?: number
  }) => request<RecommendationResponse>(`/recommendations${buildQuery(params)}`),

  explain: (recId: string) =>
    request<Explanation>(`/recommendations/${encodeURIComponent(recId)}/explain`),

  /* ---------- feedback loop ---------- */
  feedback: (body: {
    session_id: string
    user_id?: string
    rec_id: string
    action: FeedbackAction
  }) => beacon<FeedbackResponse>('/feedback', body),

  weightsHistory: (limit = 50) =>
    request<WeightsHistoryPoint[]>(`/feedback/weights-history${buildQuery({ limit })}`),

  /* ---------- digital twin ---------- */
  simulate: (body: {
    name: string
    weights: AgentWeights
    population_size?: number
    rounds?: number
  }) => request<SimulationRun>('/simulate', { method: 'POST', body: JSON.stringify(body), timeoutMs: 45000 }),

  simulateHistory: (limit = 20) =>
    request<SimulationHistoryEntry[]>(`/simulate/history${buildQuery({ limit })}`),

  deployRun: (runId: string) =>
    request<{ ok: boolean; live_weights: AgentWeights }>(
      `/simulate/${encodeURIComponent(runId)}/deploy`,
      { method: 'POST' },
    ),

  /* ---------- traffic ---------- */
  traffic: () => request<TrafficSnapshot>('/traffic/live', { timeoutMs: 6000 }),

  loadTest: (body: { profile: LoadProfile; duration_s: number }) =>
    request<{ ok: boolean; test_id: string }>('/traffic/load-test', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}

export const queryKeys = {
  categories: ['categories'] as const,
  products: (params: Record<string, unknown>) => ['products', params] as const,
  product: (id: string | number) => ['product', String(id)] as const,
  reviews: (id: string | number, page: number) => ['reviews', String(id), page] as const,
  personas: ['personas'] as const,
  recommendations: (params: Record<string, unknown>) => ['recommendations', params] as const,
  explain: (recId: string) => ['explain', recId] as const,
  weightsHistory: ['weights-history'] as const,
  simulateHistory: ['simulate-history'] as const,
  traffic: ['traffic-live'] as const,
}
