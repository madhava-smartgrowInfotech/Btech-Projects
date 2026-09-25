import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { ProductCard } from './ProductCard'
import { ExplainDrawer } from './ExplainDrawer'
import { Rail } from '@/components/common/Rail'
import { SectionHeading } from '@/components/common/SectionHeading'
import { RailSkeleton } from '@/components/common/Skeletons'
import { EmptyState, ErrorState } from '@/components/common/States'
import { Badge } from '@/components/ui/badge'
import { useRecommendations } from '@/hooks/useQueries'
import { useTracking } from '@/hooks/useTracking'
import { useSession } from '@/store/session'
import { EASE_EXPO } from '@/lib/utils'
import type { RecommendationItem } from '@/lib/types'

type Props = {
  context: 'home' | 'product' | 'cart' | 'search'
  productId?: string | number
  eyebrow?: string
  title: string
  description?: string
  limit?: number
  surface: string
  showStrategy?: boolean
  emptyHint?: string
}

const AGENT_LABEL: Record<string, string> = {
  collaborative: 'collaborative',
  content: 'content',
  trending: 'trending',
  diversity: 'diversity',
}

export function RecommendationRail({
  context,
  productId,
  eyebrow,
  title,
  description,
  limit = 8,
  surface,
  showStrategy = false,
  emptyHint,
}: Props) {
  const persona = useSession((s) => s.persona)
  const { data, isLoading, isError, error, refetch, isFetching } = useRecommendations({
    context,
    productId,
    limit,
  })
  const { signal } = useTracking()
  const [explainRecId, setExplainRecId] = useState<string | undefined>()

  const items: RecommendationItem[] = data?.items ?? []

  return (
    <section className="container py-16 sm:py-20">
      <SectionHeading
        eyebrow={eyebrow}
        title={title}
        description={description}
        action={
          showStrategy && data?.strategy ? (
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="accent">
                <Sparkles className="h-3 w-3" />
                {data.strategy.name}
              </Badge>
              {Object.entries(data.strategy.weights).map(([key, value]) => (
                <Badge key={key} variant="outline" className="num">
                  {AGENT_LABEL[key] ?? key} {Number(value).toFixed(2)}
                </Badge>
              ))}
            </div>
          ) : undefined
        }
      />

      <div className="relative mt-10">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div key="loading" exit={{ opacity: 0 }}>
              <RailSkeleton count={4} />
            </motion.div>
          ) : isError ? (
            <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <ErrorState error={error} onRetry={() => void refetch()} />
            </motion.div>
          ) : items.length === 0 ? (
            <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <EmptyState
                title="No picks yet"
                description={
                  emptyHint ??
                  'Browse a few products and the recommendation agents will start shaping this rail.'
                }
              />
            </motion.div>
          ) : (
            <motion.div
              key={`${persona?.id ?? 'guest'}-${items.length}`}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.55, ease: EASE_EXPO }}
            >
              <Rail>
                {items.map((item) => (
                  <ProductCard
                    key={item.rec_id}
                    product={item.product}
                    recId={item.rec_id}
                    reason={item.reason}
                    confidence={item.confidence}
                    onOpen={() =>
                      void signal({
                        action: 'click',
                        recId: item.rec_id,
                        product: item.product,
                        surface,
                      })
                    }
                    onWhy={() => setExplainRecId(item.rec_id)}
                  />
                ))}
              </Rail>
            </motion.div>
          )}
        </AnimatePresence>

        {isFetching && !isLoading && (
          <span className="pointer-events-none absolute -top-9 left-0 inline-flex items-center gap-2 text-[11px] text-amber-300/80">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
            Re-ranking for {persona?.name ?? 'this session'}…
          </span>
        )}
      </div>

      <ExplainDrawer
        recId={explainRecId}
        open={Boolean(explainRecId)}
        onOpenChange={(open) => !open && setExplainRecId(undefined)}
      />
    </section>
  )
}
