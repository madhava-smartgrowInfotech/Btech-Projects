import { useQuery } from '@tanstack/react-query'
import { api, queryKeys } from '@/lib/api'
import { useSession } from '@/store/session'
import type { Product } from '@/lib/types'

export function useCategories() {
  return useQuery({
    queryKey: queryKeys.categories,
    queryFn: api.categories,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePersonas() {
  return useQuery({
    queryKey: queryKeys.personas,
    queryFn: api.personas,
    staleTime: 10 * 60 * 1000,
  })
}

export function useProducts(params: {
  category?: string
  q?: string
  sort?: string
  page?: number
  page_size?: number
}) {
  return useQuery({
    queryKey: queryKeys.products(params),
    queryFn: () => api.products(params),
    placeholderData: (prev) => prev,
  })
}

export function useProduct(idOrSlug?: string) {
  return useQuery({
    queryKey: queryKeys.product(idOrSlug ?? ''),
    queryFn: () => api.product(idOrSlug as string),
    enabled: Boolean(idOrSlug),
  })
}

export function useReviews(productId?: string | number, page = 1) {
  return useQuery({
    queryKey: queryKeys.reviews(productId ?? '', page),
    queryFn: () => api.reviews(productId as string | number, page),
    enabled: Boolean(productId),
  })
}

/**
 * Recommendations are keyed on the active persona, so switching personas
 * immediately refetches every rail on screen.
 */
export function useRecommendations(opts: {
  context: 'home' | 'product' | 'cart' | 'search'
  productId?: string | number
  limit?: number
  enabled?: boolean
}) {
  const sessionId = useSession((s) => s.sessionId)
  const userId = useSession((s) => s.userId)
  const params = {
    session_id: sessionId,
    user_id: userId,
    context: opts.context,
    product_id: opts.productId,
    limit: opts.limit ?? 12,
  }
  return useQuery({
    queryKey: queryKeys.recommendations(params),
    queryFn: () => api.recommendations(params),
    enabled: opts.enabled ?? true,
    staleTime: 30 * 1000,
  })
}

export function useExplanation(recId?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.explain(recId ?? ''),
    queryFn: () => api.explain(recId as string),
    enabled: Boolean(recId) && enabled,
    staleTime: 5 * 60 * 1000,
  })
}

export function useWeightsHistory(limit = 50) {
  return useQuery({
    queryKey: queryKeys.weightsHistory,
    queryFn: () => api.weightsHistory(limit),
    refetchInterval: 15 * 1000,
  })
}

export function useSimulationHistory(limit = 20) {
  return useQuery({
    queryKey: queryKeys.simulateHistory,
    queryFn: () => api.simulateHistory(limit),
  })
}

/** Convenience: pick a handful of products for a rail without a full grid query. */
export function useProductRail(params: { category?: string; sort?: string; limit?: number }) {
  const query = useProducts({
    category: params.category,
    sort: params.sort,
    page: 1,
    page_size: params.limit ?? 8,
  })
  const items: Product[] = query.data?.items ?? []
  return { ...query, items }
}
