import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowUpRight, Gauge, Layers, TrendingUp, Users } from 'lucide-react'
import { Dialog, DialogDescription, DialogTitle, SheetContent } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ErrorState } from '@/components/common/States'
import { ProductArt } from '@/components/bits/ProductArt'
import { AnimatedNumber } from '@/components/bits/AnimatedNumber'
import { useExplanation } from '@/hooks/useQueries'
import { EASE_EXPO, cn, formatPrice } from '@/lib/utils'

const AGENT_META: Record<
  string,
  { label: string; blurb: string; color: string; icon: typeof Users }
> = {
  collaborative: {
    label: 'Collaborative',
    blurb: 'Shoppers with overlapping behaviour',
    color: '#E5A54B',
    icon: Users,
  },
  content: {
    label: 'Content',
    blurb: 'Attribute and description similarity',
    color: '#6B93FF',
    icon: Layers,
  },
  trending: {
    label: 'Trending',
    blurb: 'Short-horizon catalog momentum',
    color: '#4FD1C5',
    icon: TrendingUp,
  },
}

function pct(value: number) {
  return Math.max(0, Math.min(100, value <= 1 ? value * 100 : value))
}

export function ExplainDrawer({
  recId,
  open,
  onOpenChange,
}: {
  recId?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { data, isLoading, isError, error, refetch } = useExplanation(recId, open)

  const totalContribution =
    data?.agent_breakdown.reduce((sum, a) => sum + Math.abs(a.contribution), 0) ?? 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <SheetContent aria-describedby={undefined}>
        <div className="flex items-center gap-2 border-b border-white/[0.06] px-6 py-5">
          <Gauge className="h-4 w-4 text-amber-300" />
          <DialogTitle className="text-[13px] font-medium uppercase tracking-[0.18em] text-ink-300">
            Why this was surfaced
          </DialogTitle>
        </div>

        <div data-lenis-prevent className="flex-1 overflow-y-auto px-6 py-6">
          {isLoading && (
            <div className="space-y-5">
              <Skeleton className="h-28 w-full rounded-2xl" />
              <Skeleton className="h-4 w-3/4" />
              <div className="space-y-3 pt-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-xl" />
                ))}
              </div>
            </div>
          )}

          {isError && (
            <ErrorState
              error={error}
              onRetry={() => void refetch()}
              title="Explanation unavailable"
            />
          )}

          {data && (
            <div className="space-y-8">
              {/* subject */}
              <div className="flex gap-4">
                <ProductArt
                  seed={data.product.image_seed ?? data.product.slug}
                  name={data.product.name}
                  className="h-24 w-24 shrink-0 rounded-xl"
                />
                <div className="min-w-0">
                  <p className="eyebrow">{data.product.category}</p>
                  <h3 className="mt-1 text-[17px] font-medium tracking-tight text-ink-100">
                    {data.product.name}
                  </h3>
                  <p className="mt-1 text-[13px] text-ink-400">
                    {formatPrice(data.product.price, data.product.currency)}
                  </p>
                  <Link
                    to={`/product/${data.product.slug}`}
                    onClick={() => onOpenChange(false)}
                    className="mt-2 inline-flex items-center gap-1 text-[12px] text-amber-300 hover:text-amber-200"
                  >
                    View product
                    <ArrowUpRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>

              <DialogDescription className="rounded-xl border border-amber-400/15 bg-amber-400/[0.06] p-4 text-[14px] leading-relaxed text-amber-100/90">
                {data.headline}
              </DialogDescription>

              {/* agent contributions */}
              <section>
                <p className="eyebrow mb-4">Agent contribution</p>
                <div className="space-y-4">
                  {data.agent_breakdown.map((agent, index) => {
                    const meta = AGENT_META[agent.agent] ?? {
                      label: agent.agent,
                      blurb: '',
                      color: '#98A1AE',
                      icon: Layers,
                    }
                    const Icon = meta.icon
                    const share =
                      totalContribution > 0
                        ? (Math.abs(agent.contribution) / totalContribution) * 100
                        : 0
                    return (
                      <div key={agent.agent} className="panel-inset p-4">
                        <div className="flex items-center justify-between gap-3">
                          <span className="flex items-center gap-2">
                            <span
                              className="grid h-7 w-7 place-items-center rounded-lg"
                              style={{ background: `${meta.color}1F`, color: meta.color }}
                            >
                              <Icon className="h-3.5 w-3.5" />
                            </span>
                            <span>
                              <span className="block text-[13px] font-medium text-ink-100">
                                {meta.label}
                              </span>
                              <span className="block text-[11px] text-ink-500">{meta.blurb}</span>
                            </span>
                          </span>
                          <span className="text-right">
                            <AnimatedNumber
                              value={share}
                              decimals={1}
                              suffix="%"
                              className="text-[15px] font-medium text-ink-100"
                            />
                            <span className="block text-[10.5px] text-ink-500">of the score</span>
                          </span>
                        </div>

                        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${share}%` }}
                            transition={{ duration: 0.95, ease: EASE_EXPO, delay: 0.08 * index }}
                            className="h-full rounded-full"
                            style={{ background: meta.color }}
                          />
                        </div>

                        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-ink-500">
                          <span>
                            weight <span className="num text-ink-300">{agent.weight.toFixed(2)}</span>
                          </span>
                          <span>
                            raw <span className="num text-ink-300">{agent.raw_score.toFixed(3)}</span>
                          </span>
                          <span>
                            contribution{' '}
                            <span className="num text-ink-300">{agent.contribution.toFixed(3)}</span>
                          </span>
                        </div>

                        {agent.narrative && (
                          <p className="mt-2.5 text-[12.5px] leading-relaxed text-ink-400">
                            {agent.narrative}
                          </p>
                        )}
                      </div>
                    )
                  })}
                </div>
              </section>

              {/* similar because */}
              {data.similar_because.length > 0 && (
                <section>
                  <p className="eyebrow mb-4">Similar because</p>
                  <ul className="space-y-2.5">
                    {data.similar_because.map((entry) => (
                      <li
                        key={String(entry.product.id)}
                        className="panel-inset flex items-center gap-3 p-3"
                      >
                        <ProductArt
                          seed={entry.product.image_seed ?? entry.product.slug}
                          name={entry.product.name}
                          className="h-12 w-12 shrink-0 rounded-lg"
                        />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[13px] font-medium text-ink-100">
                            {entry.product.name}
                          </p>
                          <p className="truncate text-[11.5px] text-ink-500">
                            {entry.shared_signal}
                          </p>
                        </div>
                        <Badge variant="cobalt" className="shrink-0">
                          {pct(entry.similarity).toFixed(0)}% match
                        </Badge>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* audience fit */}
              {data.audience_fit && (
                <section>
                  <p className="eyebrow mb-4">Audience fit</p>
                  <div className="panel-inset p-4">
                    <div className="flex items-baseline justify-between">
                      <span className="text-[13px] text-ink-300">
                        {data.audience_fit.segment}
                      </span>
                      <span className="text-[13px] text-ink-400">
                        top{' '}
                        <AnimatedNumber
                          value={100 - pct(data.audience_fit.percentile)}
                          decimals={0}
                          suffix="%"
                          className="font-medium text-ink-100"
                        />
                      </span>
                    </div>
                    <div className="relative mt-3 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct(data.audience_fit.percentile)}%` }}
                        transition={{ duration: 1, ease: EASE_EXPO }}
                        className={cn('h-full rounded-full bg-gradient-to-r from-cobalt-500 to-teal-400')}
                      />
                    </div>
                    <p className="mt-2.5 text-[12px] leading-relaxed text-ink-500">
                      Ranked in the {pct(data.audience_fit.percentile).toFixed(0)}th percentile of
                      affinity for this segment.
                    </p>
                  </div>
                </section>
              )}
            </div>
          )}
        </div>
      </SheetContent>
    </Dialog>
  )
}
