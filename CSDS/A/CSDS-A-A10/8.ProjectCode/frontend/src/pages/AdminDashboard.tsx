import { useEffect, useState } from 'react'
import * as ProgressPrimitive from '@radix-ui/react-progress'
import { motion } from 'framer-motion'
import { Activity, AlertTriangle, BedDouble, Clock, Users } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { AppShell } from '@/components/layout/AppShell'
import { AnimatedNumber } from '@/components/ui/AnimatedNumber'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useLiveSocket } from '@/hooks/useLiveSocket'
import { getDepartmentLoad, getKpis } from '@/lib/api'
import { CHART_CATEGORICAL, CHART_GRID, CHART_MUTED } from '@/lib/chartColors'
import { cn } from '@/lib/utils'
import type { DepartmentLoad, KpiSummary } from '@/types'

function StatTile({
  icon: Icon,
  label,
  value,
  suffix = '',
  decimals = 0,
  accent,
  tone = 'default',
}: {
  icon: any
  label: string
  value: number
  suffix?: string
  decimals?: number
  accent: string
  tone?: 'default' | 'warning'
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
          style={{ background: `${accent}1a`, color: accent }}
        >
          <Icon size={19} />
        </div>
        <div>
          <p className={cn('font-display text-2xl font-bold', tone === 'warning' ? 'text-amber-400' : 'text-white')}>
            <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />
          </p>
          <p className="text-xs text-ink-400">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function OccupancyBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-xs">
        <span className="text-ink-300">{label}</span>
        <span className="font-semibold text-white">{pct.toFixed(0)}%</span>
      </div>
      <ProgressPrimitive.Root
        value={Math.round(pct)}
        max={100}
        className="h-2 overflow-hidden rounded-full bg-ink-900"
      >
        <ProgressPrimitive.Indicator
          className="h-full rounded-full transition-transform duration-700 ease-out"
          style={{ transform: `translateX(-${100 - pct}%)`, background: color }}
        />
      </ProgressPrimitive.Root>
    </div>
  )
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-white/10 bg-ink-900 px-3 py-2 text-xs shadow-xl">
      <p className="mb-1 font-medium text-ink-200">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.fill }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}

export default function AdminDashboard() {
  const [kpis, setKpis] = useState<KpiSummary | null>(null)
  const [load, setLoad] = useState<DepartmentLoad[]>([])

  async function refresh() {
    const [k, l] = await Promise.all([getKpis(), getDepartmentLoad()])
    setKpis(k)
    setLoad(l)
  }

  useEffect(() => {
    refresh()
    const poll = setInterval(refresh, 20000)
    return () => clearInterval(poll)
  }, [])

  useLiveSocket((evt) => {
    if (['visit_created', 'visit_updated', 'bed_updated'].includes(evt.event)) refresh()
  })

  if (!kpis) return null

  return (
    <AppShell title="Command Center" subtitle="Hospital-wide live operations overview">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile icon={Users} label="Patients today" value={kpis.patients_today} accent={CHART_CATEGORICAL[0]} />
        <StatTile icon={Activity} label="Active visits" value={kpis.active_visits} accent={CHART_CATEGORICAL[2]} />
        <StatTile
          icon={Clock}
          label="Avg. predicted wait"
          value={kpis.avg_wait_minutes}
          suffix=" min"
          decimals={1}
          accent={CHART_CATEGORICAL[3]}
        />
        <StatTile
          icon={AlertTriangle}
          label="Critical cases active"
          value={kpis.critical_cases}
          accent="#d03b3b"
          tone={kpis.critical_cases > 0 ? 'warning' : 'default'}
        />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Department load</CardTitle>
            <span className="text-xs text-ink-500">Waiting vs. in progress</span>
          </CardHeader>
          <CardContent className="h-80 pt-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={load} margin={{ top: 12, right: 8, left: -18, bottom: 0 }} barGap={4}>
                <CartesianGrid stroke={CHART_GRID} vertical={false} />
                <XAxis dataKey="code" stroke={CHART_MUTED} fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke={CHART_MUTED} fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="waiting" name="Waiting" fill={CHART_CATEGORICAL[0]} radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Bar dataKey="in_progress" name="In progress" fill={CHART_CATEGORICAL[2]} radius={[4, 4, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bed capacity</CardTitle>
            <BedDouble size={16} className="text-ink-500" />
          </CardHeader>
          <CardContent className="space-y-5">
            <OccupancyBar label="Hospital-wide beds" pct={kpis.bed_occupancy_pct} color={CHART_CATEGORICAL[0]} />
            <OccupancyBar label="ICU beds" pct={kpis.icu_occupancy_pct} color="#d03b3b" />
            <div className="grid grid-cols-2 gap-3 pt-2">
              {load.map((d, i) => (
                <motion.div
                  key={d.code}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="rounded-lg border border-white/8 bg-ink-950/40 p-2.5 text-center"
                >
                  <p className="text-[10px] text-ink-500">{d.code}</p>
                  <p className="text-sm font-semibold text-white">{d.avg_wait_minutes}m</p>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  )
}
