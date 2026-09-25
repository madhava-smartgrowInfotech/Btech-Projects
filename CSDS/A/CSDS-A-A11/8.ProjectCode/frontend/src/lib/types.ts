export type Product = {
  id: string | number
  slug: string
  name: string
  category: string
  subcategory?: string | null
  price: number
  compare_at_price?: number | null
  currency?: string
  description?: string
  short_description?: string
  image_seed?: string | number
  colorway?: string
  rating?: number
  review_count?: number
  stock?: number
  tags?: string[]
  attributes?: Record<string, string | number | boolean>
  created_at?: string
  related_ids?: Array<string | number>
}

export type Category = {
  id: string | number
  name: string
  slug: string
  product_count: number
}

export type Paged<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type Review = {
  id: string | number
  user_name: string
  rating: number
  title?: string
  body: string
  created_at: string
  helpful_count?: number
}

export type Persona = {
  id: string
  name: string
  segment: string
  avatar_seed?: string | number
  blurb?: string
}

export type AgentWeights = {
  collaborative: number
  content: number
  trending: number
  diversity: number
}

export type RecommendationItem = {
  product: Product
  rec_id: string
  score: number
  reason: string
  agents: {
    collaborative: number
    content: number
    trending: number
    diversity_bonus: number
  }
  confidence: number
}

export type RecommendationResponse = {
  strategy: { name: string; weights: AgentWeights }
  items: RecommendationItem[]
}

export type Explanation = {
  rec_id: string
  product: Product
  headline: string
  agent_breakdown: Array<{
    agent: 'collaborative' | 'content' | 'trending'
    weight: number
    raw_score: number
    contribution: number
    narrative: string
  }>
  similar_because: Array<{ product: Product; similarity: number; shared_signal: string }>
  audience_fit: { segment: string; percentile: number }
}

export type EventType =
  | 'view'
  | 'click'
  | 'search'
  | 'add_to_cart'
  | 'purchase'
  | 'rating'
  | 'review'

export type TrackEvent = {
  session_id: string
  user_id?: string
  product_id?: string | number
  type: EventType
  query?: string
  value?: number
  rec_id?: string
  source_agent?: string
}

export type FeedbackAction = 'click' | 'add_to_cart' | 'purchase' | 'dismiss' | 'ignore'

export type FeedbackResponse = {
  ok: boolean
  updated_weights: AgentWeights
  learning_step: number
}

export type WeightsHistoryPoint = {
  step: number
  timestamp: string
  weights: AgentWeights
  trigger_action: string
}

export type SimMetrics = {
  ctr: number
  conversion_rate: number
  avg_order_value: number
  catalog_coverage: number
  diversity_index: number
}

export type SimulationRun = {
  run_id: string
  name: string
  weights: AgentWeights
  baseline: SimMetrics
  candidate: SimMetrics
  lift: { ctr_pct: number; conversion_pct: number; revenue_pct: number }
  timeline: Array<{ round: number; baseline_ctr: number; candidate_ctr: number }>
  segment_breakdown: Array<{ segment: string; baseline_ctr: number; candidate_ctr: number }>
  verdict: 'deploy' | 'hold' | 'reject'
  narrative: string
}

export type SimulationHistoryEntry = {
  run_id: string
  name: string
  weights: AgentWeights
  verdict: 'deploy' | 'hold' | 'reject'
  lift: { ctr_pct: number; conversion_pct: number; revenue_pct: number }
  created_at: string
}

export type TrafficSnapshot = {
  rps: number
  p50_latency_ms: number
  p99_latency_ms: number
  queue_length: number
  cache_hit_rate: number
  active_workers: number
  autoscale_target: number
  status: 'nominal' | 'elevated' | 'critical'
  updated_at: string
}

export type LoadProfile = 'steady' | 'flash_sale' | 'spike'
