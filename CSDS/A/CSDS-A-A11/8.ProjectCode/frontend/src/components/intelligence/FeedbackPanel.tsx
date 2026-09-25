import { useMemo } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip as RTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Activity, MousePointerClick, ShoppingCart, Sparkles, Wallet } from 'lucide-react'
import { AGENT_COLORS, CHART_COLORS, ChartFrame, ChartTooltip, axisProps } from './ChartFrame'
import { AnimatedNumber } from '@/components/bits/AnimatedNumber'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState, ErrorState } from '@/components/common/States'
import { useWeightsHistory } from '@/hooks/useQueries'
import { useActivity } from '@/store/activity'
import { EASE_EXPO, cn, relativeTime } from '@/lib/utils'
import type { AgentWeights } from '@/lib/types'

const AGENT_ORDER: Array<keyof AgentWeights> = [
  'collaborative',
  'content',
  'trending',
  'diversity',
]

const ACTION_META: Record<string, { icon: typeof Activity; label: string; tint: string }> = {
  click: { icon: MousePointerClick, label: 'Click', tint: 'text-cobalt-300' },
  add_to_cart: { icon: ShoppingCart, label: 'Added to bag', tint: 'text-amber-300' },
  purchase: { icon: Wallet, label: 'Purchase', tint: 'text-teal-400' },
  dismiss: { icon: Activity, label: 'Dismissed', tint: 'text-rose-400' },
  ignore: { icon: Activity, label: 'Ignored', tint: 'text-ink-400' },
}

export function FeedbackPanel() {
  const history = useWeightsHistory(60)
  const entries = useActivity((s) => s.entries)
  const clearActivity = useActivity((s) => s.clear)

  const points = history.data ?? []
  const latest = points.length > 0 ? points[points.length - 1] : undefined

  const liveWeights: AgentWeights | undefined =
    latest?.weights ?? entries.find((e) => e.weights)?.weights

  const donutData = useMemo(
    () =>
      liveWeights
        ? AGENT_ORDER.map((key) => ({
            name: key,
            value: Number(liveWeights[key] ?? 0),
          }))
        : [],
    [liveWeights],
  )

  const lineData = useMemo(
    () =>
      points.map((point) => ({
        step: point.step,
        collaborative: point.weights.collaborative,
        content: point.weights.content,
        trending: point.weights.trending,
        diversity: point.weights.diversity,
        trigger: point.trigger_action,
      })),
    [points],
  )

  const drift = useMemo(() => {
    if (points.length < 2) return null
    const first = points[0].weights
    const last = points[points.length - 1].weights
    return AGENT_ORDER.map((key) => ({
      key,
      delta: Number(last[key] ?? 0) - Number(first[key] ?? 0),
    }))
  }, [points])

  return (
    <div className="grid gap-6 xl:grid-cols-[400px_1fr]">
      <div className="space-y-6">
        <ChartFrame
          eyebrow="Live orchestrator"
          title="Current agent weights"
          description="The weighting the live ranker is using right now, after every reinforcement applied so far."
          action={
            latest ? (
              <Badge variant="accent" className="num">
                step {latest.step}
              </Badge>
            ) : undefined
          }
        >
          {history.isLoading && <Skeleton className="h-[240px] w-full rounded-xl" />}

          {history.isError && (
            <ErrorState
              error={history.error}
              onRetry={() => void history.refetch()}
              compact
              title="Weights unavailable"
            />
          )}

          {!history.isLoading && !history.isError && donutData.length === 0 && (
            <EmptyState
              title="No weights recorded yet"
              description="Interact with a recommended product on the storefront to produce the first learning step."
            />
          )}

          {donutData.length > 0 && (
            <div className="space-y-5">
              <div className="relative h-[210px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={donutData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius="62%"
                      outerRadius="92%"
                      paddingAngle={3}
                      stroke="none"
                      animationDuration={900}
                    >
                      {donutData.map((entry) => (
                        <Cell key={entry.name} fill={AGENT_COLORS[entry.name] ?? CHART_COLORS.slate} />
                      ))}
                    </Pie>
                    <RTooltip
                      content={<ChartTooltip formatter={(value) => value.toFixed(3)} />}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 grid place-items-center">
                  <div className="text-center">
                    <p className="eyebrow">Steps</p>
                    <p className="mt-1 text-[26px] font-medium tracking-tight text-ink-100">
                      <AnimatedNumber value={latest?.step ?? points.length} />
                    </p>
                  </div>
                </div>
              </div>

              <ul className="space-y-2.5">
                {donutData.map((entry) => {
                  const change = drift?.find((d) => d.key === entry.name)?.delta ?? 0
                  return (
                    <li key={entry.name} className="flex items-center gap-3">
                      <span
                        className="h-2 w-2 shrink-0 rounded-full"
                        style={{ background: AGENT_COLORS[entry.name] }}
                      />
                      <span className="flex-1 text-[12.5px] capitalize text-ink-300">
                        {entry.name}
                      </span>
                      <span className="num text-[12.5px] text-ink-100">
                        {entry.value.toFixed(3)}
                      </span>
                      {drift && (
                        <span
                          className={cn(
                            'num w-14 text-right text-[11px]',
                            change > 0.0005
                              ? 'text-teal-400'
                              : change < -0.0005
                                ? 'text-rose-400'
                                : 'text-ink-600',
                          )}
                        >
                          {change >= 0 ? '+' : ''}
                          {change.toFixed(3)}
                        </span>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
        </ChartFrame>

        <ChartFrame
          eyebrow="This session"
          title="Signals you have sent"
          description="Reinforcement emitted from this browser — clicks, bag adds and purchases on recommended items."
          action={
            entries.length > 0 ? (
              <Button variant="ghost" size="sm" onClick={clearActivity}>
                Clear
              </Button>
            ) : undefined
          }
          bodyClassName="p-0 sm:p-0"
        >
          {entries.length === 0 ? (
            <div className="p-5">
              <EmptyState
                title="No signals yet"
                description="Open a recommended product from any rail — the reinforcement lands here immediately."
                icon={<Sparkles className="h-4 w-4" />}
              />
            </div>
          ) : (
            <ul
              data-lenis-prevent
              className="max-h-[340px] divide-y divide-white/[0.05] overflow-y-auto"
            >
              <AnimatePresence initial={false}>
                {entries.map((entry) => {
                  const meta = ACTION_META[entry.action] ?? ACTION_META.click
                  const Icon = meta.icon
                  return (
                    <motion.li
                      key={entry.id}
                      layout
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.45, ease: EASE_EXPO }}
                      className="flex items-start gap-3 px-5 py-3.5"
                    >
                      <span
                        className={cn(
                          'mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-white/[0.05]',
                          meta.tint,
                        )}
                      >
                        <Icon className="h-3.5 w-3.5" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-[12.5px] text-ink-200">
                          <span className="text-ink-400">{meta.label}</span> · {entry.label}
                        </p>
                        <p className="mt-0.5 truncate text-[11px] text-ink-500">
                          {entry.surface} · {relativeTime(entry.at)}
                          {typeof entry.learningStep === 'number' && (
                            <> · step {entry.learningStep}</>
                          )}
                        </p>
                      </div>
                      {!entry.acknowledged && (
                        <Badge variant="outline" className="shrink-0 text-[10px]">
                          queued
                        </Badge>
                      )}
                    </motion.li>
                  )
                })}
              </AnimatePresence>
            </ul>
          )}
        </ChartFrame>
      </div>

      <ChartFrame
        eyebrow="Learning trace"
        title="How the weights moved"
        description="Every reinforcement nudges the ensemble. This is the full online-update trace, newest step on the right."
        className="h-fit"
      >
        {history.isLoading && <Skeleton className="h-[420px] w-full rounded-xl" />}

        {history.isError && (
          <ErrorState
            error={history.error}
            onRetry={() => void history.refetch()}
            title="Learning history unavailable"
          />
        )}

        {!history.isLoading && !history.isError && lineData.length === 0 && (
          <EmptyState
            title="The trace starts with your first signal"
            description="Click a recommended product on the storefront, then come back — the update will be plotted here."
          />
        )}

        {lineData.length > 0 && (
          <>
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineData} margin={{ top: 8, right: 12, left: -14, bottom: 0 }}>
                  <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
                  <XAxis dataKey="step" {...axisProps} />
                  <YAxis
                    {...axisProps}
                    width={44}
                    domain={[0, 'auto']}
                    tickFormatter={(v) => Number(v).toFixed(2)}
                  />
                  <RTooltip
                    cursor={{ stroke: 'rgba(255,255,255,0.12)' }}
                    content={
                      <ChartTooltip
                        formatter={(value) => value.toFixed(3)}
                        labelFormatter={(label) => `Step ${label}`}
                      />
                    }
                  />
                  <Legend
                    iconType="circle"
                    iconSize={7}
                    wrapperStyle={{ fontSize: 11, color: CHART_COLORS.axis, paddingTop: 10 }}
                  />
                  {AGENT_ORDER.map((key) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      name={key}
                      stroke={AGENT_COLORS[key]}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 3.5 }}
                      animationDuration={1000}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {latest && (
              <p className="mt-5 border-t border-white/[0.06] pt-4 text-[12.5px] leading-relaxed text-ink-500">
                Last update triggered by{' '}
                <span className="text-ink-200">{latest.trigger_action.replace(/_/g, ' ')}</span> at{' '}
                {relativeTime(latest.timestamp)} — {points.length} steps recorded.
              </p>
            )}
          </>
        )}
      </ChartFrame>
    </div>
  )
}
