import { useState } from 'react'
import { Star, ThumbsUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState, ErrorState } from '@/components/common/States'
import { useReviews } from '@/hooks/useQueries'
import { cn, relativeTime } from '@/lib/utils'
import type { Review } from '@/lib/types'

function Stars({ value, className }: { value: number; className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-0.5', className)} aria-label={`${value} out of 5`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={cn(
            'h-3.5 w-3.5',
            i < Math.round(value) ? 'fill-amber-400 text-amber-400' : 'text-ink-700',
          )}
        />
      ))}
    </span>
  )
}

export function ReviewList({ productId }: { productId?: string | number }) {
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState<Review[][]>([])
  const { data, isLoading, isError, error, refetch, isFetching } = useReviews(productId, page)

  // Accumulate pages so "Load more" appends instead of replacing.
  const current = data?.items ?? []
  const all = page === 1 ? current : [...pages.flat(), ...current]
  const total = data?.total ?? 0
  const hasMore = all.length < total

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="panel space-y-3 p-5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} compact />

  if (all.length === 0) {
    return (
      <EmptyState
        title="No reviews yet"
        description="Be the first to say how this piece works in your space."
      />
    )
  }

  return (
    <div className="space-y-4">
      {all.map((review) => (
        <article key={String(review.id)} className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-3">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-white/[0.06] text-[11px] font-medium text-ink-300">
                {review.user_name?.slice(0, 2).toUpperCase()}
              </span>
              <div>
                <p className="text-[13px] font-medium text-ink-100">{review.user_name}</p>
                <p className="text-[11px] text-ink-500">{relativeTime(review.created_at)}</p>
              </div>
            </div>
            <Stars value={review.rating} />
          </div>

          {review.title && (
            <h4 className="mt-4 text-[14px] font-medium tracking-tight text-ink-100">
              {review.title}
            </h4>
          )}
          <p className="mt-2 text-[13.5px] leading-relaxed text-ink-400">{review.body}</p>

          {typeof review.helpful_count === 'number' && review.helpful_count > 0 && (
            <p className="mt-4 inline-flex items-center gap-1.5 text-[11.5px] text-ink-500">
              <ThumbsUp className="h-3 w-3" />
              {review.helpful_count} found this helpful
            </p>
          )}
        </article>
      ))}

      {hasMore && (
        <div className="pt-2">
          <Button
            variant="secondary"
            size="sm"
            disabled={isFetching}
            onClick={() => {
              setPages((prev) => [...prev, current])
              setPage((p) => p + 1)
            }}
          >
            {isFetching ? 'Loading…' : `Load more reviews (${total - all.length} left)`}
          </Button>
        </div>
      )}
    </div>
  )
}
