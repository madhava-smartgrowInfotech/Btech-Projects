import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Activity,
  Cpu,
  Database,
  Gauge,
  Layers,
  RefreshCw,
  Timer,
  Waves,
  Zap,
} from 'lucide-react'
import { CHART_COLORS, ChartFrame, ChartTooltip, axisProps } from './ChartFrame'
import { AnimatedNumber } from '@/components/bits/AnimatedNumber'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/toast'
import { EmptyState } from '@/components/common/States'
import { api } from '@/lib/api'
import { useTrafficStream, type ConnectionMode } from '@/hooks/useTrafficStream'
import { EASE_EXPO, cn } from '@/lib/utils'
import type { LoadProfile } from '@/lib/types'

const PROFILES: Array<{
  id: LoadProfile
  label: string
  detail: string
  duration: number
  icon: typeof Waves
}> = [
  { id: 'steady', label: 'Steady state', detail: 'Baseline weekday traffic', duration: 45, icon: Waves },
  { id: 'flash_sale', label: 'Flash sale', detail: 'Sustained 6× surge', duration: 60, icon: Zap },
  { id: 'spike', label: 'Spike', detail: 'Instant burst, no ramp', duration: 30, icon: Activity },
]

const STATUS_META = {
  nominal: { label: 'Nominal', variant: 'success' as const, dot: 'bg-teal-400' },
  elevated: { label: 'Elevated', variant: 'warning' as const, dot: 'bg-amber-400' },
  critical: { label: 'Critical', variant: 'danger' as const, dot: 'bg-rose-400' },
}

const CONNECTION_META: Record<ConnectionMode, { label: string; tint: string; dot: string }> = {
  connecting: { label: 'Connecting', tint: 'text-ink-400', dot: 'bg-ink-400' },
  live: { label: 'Live socket', tint: 'text-teal-400', dot: 'bg-teal-400' },
  polling: { label: 'Polling fallback', tint: 'text-amber-300', dot: 'bg-amber-400' },
  offline: { label: 'Telemetry offline', tint: 'text-rose-400', dot: 'bg-rose-400' },
}

function MetricTile({
  label,
  value,
  decimals = 0,
  suffix = '',
  icon: Icon,
  accent,
  index,
  hint,
}: {
  label: string
  value: number
  decimals?: number
  suffix?: string
  icon: typeof Gauge
  accent: string
  index: number
  hint?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: EASE_EXPO, delay: index * 0.05 }}
      className="panel-inset p-4"
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] uppercase tracking-[0.16em] text-ink-500">{label}</p>
        <Icon className="h-3.5 w-3.5" style={{ color: accent }} />
      </div>
      <p className="mt-2.5 text-[26px] font-medium leading-none tracking-tight text-ink-100">
        <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />
      </p>
      {hint && <p className="mt-2 text-[11px] text-ink-500">{hint}</p>}
    </motion.div>
  )
}

export function TrafficCenter() {
  const { snapshot, series, mode, attempts, lastError, reconnectNow } = useTrafficStream(true)
  const [activeProfile, setActiveProfile] = useState<LoadProfile | null>(null)

  const loadTest = useMutation({
    mutationFn: (profile: { profile: LoadProfile; duration_s: number }) => api.loadTest(profile),
    onSuccess: (_data, variables) => {
      setActiveProfile(variables.profile)
      window.setTimeout(() => setActiveProfile(null), variables.duration_s * 1000)
      toast({
        title: `${variables.profile.replace('_', ' ')} profile dispatched`,
        description: `Driving synthetic load for ${variables.duration_s}s — watch the dashboard react.`,
        tone: 'success',
      })
    },
    onError: (error: Error) => {
      toast({ title: 'Could not start load test', description: error.message, tone: 'error' })
    },
  })

  const status = snapshot ? (STATUS_META[snapshot.status] ?? STATUS_META.nominal) : null
  const connection = CONNECTION_META[mode]
  const cacheHit = snapshot
    ? snapshot.cache_hit_rate <= 1
      ? snapshot.cache_hit_rate * 100
      : snapshot.cache_hit_rate
    : 0

  return (
    <div className="space-y-6">
      {/* status bar */}
      <div className="panel flex flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-6">
        <div className="flex flex-wrap items-center gap-4">
          <span className="relative flex items-center gap-2.5">
            <span className="relative flex h-2 w-2">
              <span
                className={cn(
                  'absolute inline-flex h-full w-full rounded-full opacity-70',
                  connection.dot,
                  mode === 'live' && 'animate-pulse-ring',
                )}
              />
              <span className={cn('relative inline-flex h-2 w-2 rounded-full', connection.dot)} />
            </span>
            <span className={cn('text-[12.5px] font-medium', connection.tint)}>
              {connection.label}
            </span>
          </span>

          {attempts > 0 && mode !== 'live' && (
            <span className="text-[11.5px] text-ink-500">
              reconnect attempt {attempts} · exponential backoff
            </span>
          )}

          {status && (
            <Badge variant={status.variant} className="px-3 py-1.5">
              <span className={cn('h-1.5 w-1.5 rounded-full', status.dot)} />
              {status.label}
            </Badge>
          )}

          {snapshot && (
            <span className="num text-[11.5px] text-ink-600">
              autoscale target {snapshot.autoscale_target}
            </span>
          )}
        </div>

        <Button variant="secondary" size="sm" onClick={reconnectNow}>
          <RefreshCw className="h-3.5 w-3.5" />
          Reconnect
        </Button>
      </div>

      {/* metrics */}
      {snapshot ? (
        <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-6">
          <MetricTile
            index={0}
            label="Requests/s"
            value={snapshot.rps}
            decimals={0}
            icon={Gauge}
            accent={CHART_COLORS.amber}
          />
          <MetricTile
            index={1}
            label="p50 latency"
            value={snapshot.p50_latency_ms}
            decimals={0}
            suffix="ms"
            icon={Timer}
            accent={CHART_COLORS.cobalt}
          />
          <MetricTile
            index={2}
            label="p99 latency"
            value={snapshot.p99_latency_ms}
            decimals={0}
            suffix="ms"
            icon={Timer}
            accent={CHART_COLORS.rose}
          />
          <MetricTile
            index={3}
            label="Queue depth"
            value={snapshot.queue_length}
            decimals={0}
            icon={Layers}
            accent={CHART_COLORS.teal}
          />
          <MetricTile
            index={4}
            label="Cache hits"
            value={cacheHit}
            decimals={1}
            suffix="%"
            icon={Database}
            accent={CHART_COLORS.teal}
          />
          <MetricTile
            index={5}
            label="Workers"
            value={snapshot.active_workers}
            decimals={0}
            icon={Cpu}
            accent={CHART_COLORS.amber}
            hint={`target ${snapshot.autoscale_target}`}
          />
        </div>
      ) : (
        <EmptyState
          title={mode === 'offline' ? 'Telemetry offline' : 'Waiting for the first snapshot'}
          description={
            mode === 'offline'
              ? lastError ??
                'Neither the socket nor the REST snapshot is responding. The console keeps retrying in the background.'
              : 'The stream publishes roughly one snapshot per second.'
          }
          icon={<Activity className="h-4 w-4" />}
        />
      )}

      {/* load profiles */}
      <ChartFrame
        eyebrow="Load generator"
        title="Drive synthetic traffic"
        description="Each profile runs server-side and moves the numbers above in real time."
      >
        <div className="grid gap-3 sm:grid-cols-3">
          {PROFILES.map((profile) => {
            const Icon = profile.icon
            const running = activeProfile === profile.id
            return (
              <button
                key={profile.id}
                onClick={() =>
                  loadTest.mutate({ profile: profile.id, duration_s: profile.duration })
                }
                disabled={loadTest.isPending}
                className={cn(
                  'group relative overflow-hidden rounded-xl border p-4 text-left transition-all duration-400 ease-expo disabled:opacity-60',
                  running
                    ? 'border-amber-400/45 bg-amber-400/[0.08]'
                    : 'border-white/[0.08] bg-white/[0.02] hover:border-white/20',
                )}
              >
                <div className="flex items-center justify-between">
                  <Icon
                    className={cn('h-4 w-4', running ? 'text-amber-300' : 'text-ink-400')}
                  />
                  {running && (
                    <span className="flex items-center gap-1.5 text-[10.5px] text-amber-300">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
                      running
                    </span>
                  )}
                </div>
                <p className="mt-3 text-[13.5px] font-medium text-ink-100">{profile.label}</p>
                <p className="mt-1 text-[11.5px] text-ink-500">{profile.detail}</p>
                <p className="mt-2 text-[11px] text-ink-600">{profile.duration}s run</p>
              </button>
            )
          })}
        </div>
      </ChartFrame>

      {/* charts */}
      <div className="grid gap-6 xl:grid-cols-2">
        <ChartFrame
          eyebrow="Throughput"
          title="Requests per second"
          description="Rolling window of the last minute of telemetry."
        >
          {series.length < 2 ? (
            <div className="grid h-[260px] place-items-center text-[12.5px] text-ink-500">
              Collecting samples…
            </div>
          ) : (
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rpsFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={CHART_COLORS.amber} stopOpacity={0.42} />
                      <stop offset="100%" stopColor={CHART_COLORS.amber} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
                  <XAxis dataKey="label" {...axisProps} minTickGap={36} />
                  <YAxis {...axisProps} width={48} />
                  <RTooltip
                    cursor={{ stroke: 'rgba(255,255,255,0.12)' }}
                    content={<ChartTooltip formatter={(value) => value.toFixed(0)} />}
                  />
                  <Area
                    type="monotone"
                    dataKey="rps"
                    name="req/s"
                    stroke={CHART_COLORS.amber}
                    strokeWidth={2}
                    fill="url(#rpsFill)"
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </ChartFrame>

        <ChartFrame
          eyebrow="Latency"
          title="p50 vs p99 response time"
          description="Tail latency is the first thing to move when the queue backs up."
        >
          {series.length < 2 ? (
            <div className="grid h-[260px] place-items-center text-[12.5px] text-ink-500">
              Collecting samples…
            </div>
          ) : (
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={series} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
                  <XAxis dataKey="label" {...axisProps} minTickGap={36} />
                  <YAxis {...axisProps} width={48} unit="ms" />
                  <RTooltip
                    cursor={{ stroke: 'rgba(255,255,255,0.12)' }}
                    content={<ChartTooltip formatter={(value) => `${value.toFixed(0)}ms`} />}
                  />
                  <Line
                    type="monotone"
                    dataKey="p50_latency_ms"
                    name="p50"
                    stroke={CHART_COLORS.cobalt}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="p99_latency_ms"
                    name="p99"
                    stroke={CHART_COLORS.rose}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </ChartFrame>
      </div>
    </div>
  )
}
