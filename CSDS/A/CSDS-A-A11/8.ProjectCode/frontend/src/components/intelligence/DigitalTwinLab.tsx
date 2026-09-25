import { useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  CheckCircle2,
  CircleSlash,
  FlaskConical,
  PauseCircle,
  RotateCcw,
  Rocket,
} from 'lucide-react'
import { AGENT_COLORS, CHART_COLORS, ChartFrame, ChartTooltip, axisProps } from './ChartFrame'
import { AnimatedNumber } from '@/components/bits/AnimatedNumber'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from '@/components/ui/toast'
import { Tooltip } from '@/components/ui/tooltip'
import { ErrorState, EmptyState } from '@/components/common/States'
import { api, queryKeys } from '@/lib/api'
import { useSimulationHistory } from '@/hooks/useQueries'
import { EASE_EXPO, cn, formatPrice, formatSigned, normalizeWeights, relativeTime } from '@/lib/utils'
import type { AgentWeights, SimulationRun } from '@/lib/types'

const AGENTS: Array<{ key: keyof AgentWeights; label: string; hint: string }> = [
  {
    key: 'collaborative',
    label: 'Collaborative',
    hint: 'Neighbourhood signal from shoppers with overlapping histories.',
  },
  {
    key: 'content',
    label: 'Content',
    hint: 'Attribute and description similarity to what the shopper engaged with.',
  },
  {
    key: 'trending',
    label: 'Trending',
    hint: 'Short-horizon catalog momentum across views, adds and orders.',
  },
  {
    key: 'diversity',
    label: 'Diversity',
    hint: 'Penalises near-duplicates so the rail keeps breadth.',
  },
]

const DEFAULT_WEIGHTS: AgentWeights = {
  collaborative: 0.4,
  content: 0.3,
  trending: 0.2,
  diversity: 0.1,
}

const PRESETS: Array<{ name: string; weights: AgentWeights }> = [
  { name: 'Balanced', weights: DEFAULT_WEIGHTS },
  {
    name: 'Discovery-led',
    weights: { collaborative: 0.2, content: 0.25, trending: 0.2, diversity: 0.35 },
  },
  {
    name: 'Momentum',
    weights: { collaborative: 0.25, content: 0.15, trending: 0.5, diversity: 0.1 },
  },
  {
    name: 'Taste-matched',
    weights: { collaborative: 0.45, content: 0.4, trending: 0.1, diversity: 0.05 },
  },
]

const METRICS: Array<{
  key: keyof SimulationRun['baseline']
  label: string
  kind: 'pct' | 'currency'
}> = [
  { key: 'ctr', label: 'Click-through', kind: 'pct' },
  { key: 'conversion_rate', label: 'Conversion', kind: 'pct' },
  { key: 'avg_order_value', label: 'Avg order value', kind: 'currency' },
  { key: 'catalog_coverage', label: 'Catalog coverage', kind: 'pct' },
  { key: 'diversity_index', label: 'Diversity index', kind: 'pct' },
]

const VERDICT_META = {
  deploy: { label: 'Deploy', variant: 'success' as const, icon: CheckCircle2 },
  hold: { label: 'Hold', variant: 'warning' as const, icon: PauseCircle },
  reject: { label: 'Reject', variant: 'danger' as const, icon: CircleSlash },
}

function MetricCompare({
  label,
  baseline,
  candidate,
  kind,
  index,
}: {
  label: string
  baseline: number
  candidate: number
  kind: 'pct' | 'currency'
  index: number
}) {
  const delta = baseline === 0 ? 0 : ((candidate - baseline) / baseline) * 100
  const positive = delta >= 0
  const scale = kind === 'pct' ? (candidate <= 1 ? 100 : 1) : 1

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: EASE_EXPO, delay: index * 0.06 }}
      className="panel-inset p-4"
    >
      <p className="text-[11px] uppercase tracking-[0.16em] text-ink-500">{label}</p>
      <p className="mt-2.5 text-[26px] font-medium leading-none tracking-tight text-ink-100">
        {kind === 'currency' ? (
          <AnimatedNumber value={candidate} decimals={2} prefix="$" />
        ) : (
          <AnimatedNumber value={candidate} scale={scale} decimals={2} suffix="%" />
        )}
      </p>
      <div className="mt-3 flex items-center justify-between gap-2">
        <span className="text-[11.5px] text-ink-500">
          base{' '}
          <span className="num text-ink-400">
            {kind === 'currency'
              ? formatPrice(baseline)
              : `${(baseline <= 1 ? baseline * 100 : baseline).toFixed(2)}%`}
          </span>
        </span>
        <span
          className={cn(
            'num rounded-full px-2 py-0.5 text-[11px] font-medium',
            positive ? 'bg-teal-400/10 text-teal-400' : 'bg-rose-500/10 text-rose-400',
          )}
        >
          {formatSigned(delta)}
        </span>
      </div>
    </motion.div>
  )
}

export function DigitalTwinLab() {
  const qc = useQueryClient()
  const [raw, setRaw] = useState<AgentWeights>(DEFAULT_WEIGHTS)
  const [name, setName] = useState('Candidate strategy')
  const [population, setPopulation] = useState(2000)
  const [rounds, setRounds] = useState(12)
  const [run, setRun] = useState<SimulationRun | null>(null)

  const history = useSimulationHistory(20)

  const normalized = useMemo(
    () => normalizeWeights(raw as unknown as Record<string, number>) as unknown as AgentWeights,
    [raw],
  )

  const simulate = useMutation({
    mutationFn: () =>
      api.simulate({
        name: name.trim() || 'Candidate strategy',
        weights: normalized,
        population_size: population,
        rounds,
      }),
    onSuccess: (data) => {
      setRun(data)
      void qc.invalidateQueries({ queryKey: queryKeys.simulateHistory })
      toast({
        title: `Simulation complete — ${VERDICT_META[data.verdict]?.label ?? data.verdict}`,
        description: `CTR lift ${formatSigned(data.lift.ctr_pct)} across ${rounds} rounds.`,
        tone: data.verdict === 'deploy' ? 'success' : data.verdict === 'hold' ? 'warning' : 'error',
      })
    },
    onError: (error: Error) => {
      toast({ title: 'Simulation failed', description: error.message, tone: 'error' })
    },
  })

  const deploy = useMutation({
    mutationFn: (runId: string) => api.deployRun(runId),
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: queryKeys.weightsHistory })
      void qc.invalidateQueries({ queryKey: queryKeys.simulateHistory })
      toast({
        title: 'Strategy deployed',
        description: `Live weights now ${Object.entries(data.live_weights)
          .map(([k, v]) => `${k.slice(0, 4)} ${Number(v).toFixed(2)}`)
          .join(' · ')}`,
        tone: 'success',
      })
    },
    onError: (error: Error) => {
      toast({ title: 'Deploy failed', description: error.message, tone: 'error' })
    },
  })

  const timelineData = useMemo(
    () =>
      (run?.timeline ?? []).map((point) => ({
        round: point.round,
        baseline: point.baseline_ctr <= 1 ? point.baseline_ctr * 100 : point.baseline_ctr,
        candidate: point.candidate_ctr <= 1 ? point.candidate_ctr * 100 : point.candidate_ctr,
      })),
    [run],
  )

  const segmentData = useMemo(
    () =>
      (run?.segment_breakdown ?? []).map((row) => ({
        segment: row.segment,
        baseline: row.baseline_ctr <= 1 ? row.baseline_ctr * 100 : row.baseline_ctr,
        candidate: row.candidate_ctr <= 1 ? row.candidate_ctr * 100 : row.candidate_ctr,
      })),
    [run],
  )

  const Verdict = run ? (VERDICT_META[run.verdict] ?? VERDICT_META.hold) : null

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
      {/* ---------- control column ---------- */}
      <div className="space-y-6">
        <ChartFrame
          eyebrow="Candidate strategy"
          title="Weight the ensemble"
          description="Weights are auto-normalised to sum to 1.00 before the run is dispatched."
          action={
            <Tooltip content="Reset to the balanced baseline">
              <button
                onClick={() => setRaw(DEFAULT_WEIGHTS)}
                className="grid h-8 w-8 place-items-center rounded-full border border-white/[0.08] text-ink-400 transition-colors hover:text-ink-100"
                aria-label="Reset weights"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
            </Tooltip>
          }
        >
          <div className="space-y-6">
            {AGENTS.map((agent) => (
              <div key={agent.key}>
                <div className="flex items-center justify-between gap-3">
                  <Tooltip content={agent.hint}>
                    <span className="flex cursor-help items-center gap-2 text-[13px] text-ink-200">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ background: AGENT_COLORS[agent.key] }}
                      />
                      {agent.label}
                    </span>
                  </Tooltip>
                  <span className="num text-[13px] text-ink-100">
                    {normalized[agent.key].toFixed(2)}
                  </span>
                </div>
                <Slider
                  value={[raw[agent.key]]}
                  min={0}
                  max={1}
                  step={0.01}
                  onValueChange={([value]) =>
                    setRaw((prev) => ({ ...prev, [agent.key]: value }))
                  }
                  className="mt-2"
                />
              </div>
            ))}

            <div className="flex flex-wrap gap-2 border-t border-white/[0.06] pt-5">
              {PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => {
                    setRaw(preset.weights)
                    setName(preset.name)
                  }}
                  className="rounded-full border border-white/[0.09] px-3 py-1.5 text-[11.5px] text-ink-400 transition-colors duration-300 ease-expo hover:border-amber-400/35 hover:text-amber-200"
                >
                  {preset.name}
                </button>
              ))}
            </div>

            <div className="space-y-4 border-t border-white/[0.06] pt-5">
              <label className="block">
                <span className="eyebrow">Run label</span>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-2 h-10 text-[13px]"
                  placeholder="Candidate strategy"
                />
              </label>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="eyebrow">Population</span>
                    <span className="num text-[12px] text-ink-200">
                      {population.toLocaleString()}
                    </span>
                  </div>
                  <Slider
                    value={[population]}
                    min={250}
                    max={10000}
                    step={250}
                    onValueChange={([value]) => setPopulation(value)}
                    className="mt-2"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <span className="eyebrow">Rounds</span>
                    <span className="num text-[12px] text-ink-200">{rounds}</span>
                  </div>
                  <Slider
                    value={[rounds]}
                    min={4}
                    max={40}
                    step={1}
                    onValueChange={([value]) => setRounds(value)}
                    className="mt-2"
                  />
                </div>
              </div>
            </div>

            <Button
              className="w-full"
              onClick={() => simulate.mutate()}
              disabled={simulate.isPending}
            >
              <FlaskConical className={cn('h-4 w-4', simulate.isPending && 'animate-pulse')} />
              {simulate.isPending ? 'Running the twin…' : 'Run simulation'}
            </Button>
          </div>
        </ChartFrame>

        <ChartFrame
          eyebrow="History"
          title="Previous runs"
          description="Every dispatched candidate, with its verdict and measured lift."
          bodyClassName="p-0 sm:p-0"
        >
          {history.isLoading && (
            <div className="space-y-3 p-5">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full rounded-xl" />
              ))}
            </div>
          )}
          {history.isError && (
            <div className="p-5">
              <ErrorState
                error={history.error}
                onRetry={() => void history.refetch()}
                compact
                title="History unavailable"
              />
            </div>
          )}
          {history.data && history.data.length === 0 && (
            <div className="p-5">
              <EmptyState
                title="No runs recorded"
                description="Dispatch a candidate strategy to start the log."
              />
            </div>
          )}
          {history.data && history.data.length > 0 && (
            <ul className="max-h-[360px] divide-y divide-white/[0.05] overflow-y-auto" data-lenis-prevent>
              {history.data.map((entry) => {
                const meta = VERDICT_META[entry.verdict] ?? VERDICT_META.hold
                return (
                  <li key={entry.run_id} className="px-5 py-3.5">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-medium text-ink-100">
                          {entry.name}
                        </p>
                        <p className="mt-0.5 text-[11px] text-ink-500">
                          {relativeTime(entry.created_at)} · CTR {formatSigned(entry.lift.ctr_pct)}
                        </p>
                      </div>
                      <Badge variant={meta.variant} className="shrink-0">
                        {meta.label}
                      </Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {Object.entries(entry.weights).map(([key, value]) => (
                        <span
                          key={key}
                          className="num rounded-full bg-white/[0.04] px-2 py-0.5 text-[10px] text-ink-500"
                        >
                          {key.slice(0, 4)} {Number(value).toFixed(2)}
                        </span>
                      ))}
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </ChartFrame>
      </div>

      {/* ---------- results column ---------- */}
      <div className="space-y-6">
        {simulate.isError && (
          <ErrorState
            error={simulate.error}
            onRetry={() => simulate.mutate()}
            title="The twin could not be reached"
          />
        )}

        {!run && !simulate.isPending && !simulate.isError && (
          <div className="panel flex min-h-[420px] flex-col items-center justify-center gap-4 p-10 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-full border border-white/[0.08] bg-white/[0.02] text-amber-300">
              <FlaskConical className="h-5 w-5" />
            </span>
            <div className="max-w-md">
              <p className="text-[16px] font-medium tracking-tight text-ink-100">
                Nothing simulated yet
              </p>
              <p className="mt-2 text-[13.5px] leading-relaxed text-ink-400">
                Set the ensemble weights, then run the twin. A synthetic population shops the
                catalog under both the live strategy and your candidate, and the deltas land here.
              </p>
            </div>
          </div>
        )}

        {simulate.isPending && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-[118px] rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-[300px] w-full rounded-2xl" />
          </div>
        )}

        {run && !simulate.isPending && (
          <>
            {/* verdict */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: EASE_EXPO }}
              className="panel flex flex-col gap-5 p-6 lg:flex-row lg:items-center lg:justify-between"
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-3">
                  {Verdict && (
                    <Badge variant={Verdict.variant} className="px-3 py-1.5 text-[12px]">
                      <Verdict.icon className="h-3.5 w-3.5" />
                      {Verdict.label}
                    </Badge>
                  )}
                  <h3 className="text-[18px] font-medium tracking-tight text-ink-100">
                    {run.name}
                  </h3>
                  <span className="num text-[11px] text-ink-600">{run.run_id}</span>
                </div>
                <p className="mt-3 max-w-2xl text-[13.5px] leading-relaxed text-ink-400">
                  {run.narrative}
                </p>
                <div className="mt-4 flex flex-wrap gap-4">
                  {(
                    [
                      ['CTR', run.lift.ctr_pct],
                      ['Conversion', run.lift.conversion_pct],
                      ['Revenue', run.lift.revenue_pct],
                    ] as const
                  ).map(([label, value]) => (
                    <div key={label}>
                      <p className="text-[10.5px] uppercase tracking-[0.16em] text-ink-500">
                        {label} lift
                      </p>
                      <p
                        className={cn(
                          'mt-1 text-[20px] font-medium tracking-tight',
                          value >= 0 ? 'text-teal-400' : 'text-rose-400',
                        )}
                      >
                        <AnimatedNumber
                          value={value}
                          decimals={1}
                          prefix={value > 0 ? '+' : ''}
                          suffix="%"
                        />
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <Button
                size="lg"
                variant={run.verdict === 'deploy' ? 'primary' : 'secondary'}
                onClick={() => deploy.mutate(run.run_id)}
                disabled={deploy.isPending}
                className="shrink-0"
              >
                <Rocket className="h-4 w-4" />
                {deploy.isPending ? 'Deploying…' : 'Deploy strategy'}
              </Button>
            </motion.div>

            {/* metric cards */}
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-5">
              {METRICS.map((metric, i) => (
                <MetricCompare
                  key={metric.key}
                  label={metric.label}
                  baseline={run.baseline[metric.key]}
                  candidate={run.candidate[metric.key]}
                  kind={metric.kind}
                  index={i}
                />
              ))}
            </div>

            {/* timeline */}
            <ChartFrame
              eyebrow="Round by round"
              title="Click-through, baseline vs candidate"
              description="Each round is one simulated shopping session across the synthetic population."
            >
              <div className="h-[290px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timelineData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                    <defs>
                      <linearGradient id="candidateFade" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={CHART_COLORS.amber} stopOpacity={0.3} />
                        <stop offset="100%" stopColor={CHART_COLORS.amber} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
                    <XAxis dataKey="round" {...axisProps} />
                    <YAxis {...axisProps} width={46} tickFormatter={(v) => `${Number(v).toFixed(1)}%`} />
                    <RTooltip
                      cursor={{ stroke: 'rgba(255,255,255,0.12)' }}
                      content={
                        <ChartTooltip
                          formatter={(value) => `${value.toFixed(2)}%`}
                          labelFormatter={(label) => `Round ${label}`}
                        />
                      }
                    />
                    <Legend
                      iconType="circle"
                      iconSize={7}
                      wrapperStyle={{ fontSize: 11, color: CHART_COLORS.axis, paddingTop: 8 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="baseline"
                      name="Baseline"
                      stroke={CHART_COLORS.slate}
                      strokeWidth={1.6}
                      strokeDasharray="4 4"
                      dot={false}
                      animationDuration={900}
                    />
                    <Line
                      type="monotone"
                      dataKey="candidate"
                      name="Candidate"
                      stroke={CHART_COLORS.amber}
                      strokeWidth={2.2}
                      dot={false}
                      animationDuration={1100}
                      fill="url(#candidateFade)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </ChartFrame>

            {/* segments */}
            <ChartFrame
              eyebrow="Segments"
              title="Where the lift actually lands"
              description="A strategy that only wins on one segment rarely survives contact with live traffic."
            >
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={segmentData}
                    margin={{ top: 8, right: 8, left: -18, bottom: 0 }}
                    barGap={4}
                  >
                    <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
                    <XAxis dataKey="segment" {...axisProps} interval={0} angle={-12} dy={8} />
                    <YAxis {...axisProps} width={46} tickFormatter={(v) => `${Number(v).toFixed(1)}%`} />
                    <RTooltip
                      cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                      content={<ChartTooltip formatter={(value) => `${value.toFixed(2)}%`} />}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={7}
                      wrapperStyle={{ fontSize: 11, color: CHART_COLORS.axis, paddingTop: 8 }}
                    />
                    <Bar
                      dataKey="baseline"
                      name="Baseline"
                      fill={CHART_COLORS.slate}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={26}
                      animationDuration={900}
                    />
                    <Bar
                      dataKey="candidate"
                      name="Candidate"
                      fill={CHART_COLORS.amber}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={26}
                      animationDuration={1100}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartFrame>
          </>
        )}
      </div>
    </div>
  )
}
