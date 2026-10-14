import { useEffect, useMemo, useRef, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Tooltip as RTooltip, XAxis, YAxis } from 'recharts'
import { Activity, Building2, CalendarClock, Clock, GitBranch, Siren, Users } from 'lucide-react'
import api, { todayStr } from '../api'
import MapView from '../components/MapView'
import SeverityMix from '../components/SeverityMix'
import useQueueSocket from '../components/useQueueSocket'
import ActivityLog from '../components/ui/ActivityLog'
import { PageHeader } from '../components/ui/AppShell'
import { Input } from '../components/ui/controls'
import { Card, KeyValueList, StatCard, StatusDot } from '../components/ui/display'
import { ErrorState, ProgressBar, Skeleton } from '../components/ui/feedback'
import { ChartFrame, MonoTooltip, useChartTheme } from '../components/ui/charts'
import Table from '../components/ui/Table'
import { loadHex, statusLabel } from '../format'
import useApi from '../lib/useApi'

const toneFor = (pct) => (pct >= 90 ? 'alert' : pct >= 70 ? 'hot' : pct >= 40 ? 'warn' : 'ok')

export default function Dashboard() {
  const [date, setDate] = useState(todayStr())
  const dash = useApi(() => api.get('/dashboard', { params: { date } }).then((r) => r.data), [date])
  const d = dash.data
  const { axis, grid, animate } = useChartTheme()

  // live: any hospital queue change refreshes the dashboard, debounced
  const timer = useRef(null)
  const live = useQueueSocket(0, () => {
    clearTimeout(timer.current)
    timer.current = setTimeout(dash.reload, 800)
  })
  useEffect(() => () => clearTimeout(timer.current), [])

  const markers = useMemo(
    () =>
      (d?.hospitals || []).map((h) => ({
        id: h.id,
        lat: h.lat,
        lon: h.lon,
        color: loadHex(h.load_pct),
        radius: 6 + Math.min(10, h.booked / 20),
        label: `${h.name}: ${h.load_pct}% load, ${h.waiting} waiting`,
      })),
    [d],
  )
  const chartData = useMemo(
    () =>
      (d?.hospitals || []).slice(0, 12).map((h) => ({
        name: h.name.length > 26 ? `${h.name.slice(0, 25)}…` : h.name,
        load: h.load_pct,
        color: loadHex(h.load_pct),
      })),
    [d],
  )

  if (!d) {
    return (
      <div className="space-y-5">
        {dash.error ? <ErrorState error={dash.error} onRetry={dash.reload} /> : <Skeleton className="h-96 w-full" />}
      </div>
    )
  }
  const t = d.totals

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="admin - district"
        title="District dashboard - Hyderabad"
        subtitle="Load, waiting times and severity mix across every hospital. Updates as queues change."
        actions={
          <>
            <Input label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-40" />
            <StatusDot tone={live ? 'ok' : 'warn'} label={live ? 'live' : 'offline'} blink={live} />
          </>
        }
      />
      {dash.error && <ErrorState error={dash.error} onRetry={dash.reload} />}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatCard live label="Hospitals" value={t.hospitals} icon={Building2} sub={`${t.capacity} OP slots/day`} />
        <StatCard label="Bookings" value={t.bookings} icon={Users} sub={`${Math.round((100 * t.bookings) / Math.max(t.capacity, 1))}% of capacity`} />
        <StatCard label="Waiting now" value={t.waiting} icon={Activity} sub={`${t.done} seen, ${t.no_show} no-show`} />
        <StatCard label="Avg wait" value={t.avg_wait_min} format={(v) => `${v.toFixed(1)} min`} icon={Clock} sub="hospitals with a queue" />
        <StatCard label="Emergencies" value={t.emergencies} icon={Siren} tone="alert" />
        <StatCard label="Moved to later day" value={t.moved_next_day} icon={CalendarClock} sub="day was full" />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="Hospital map" eyebrow="marker size = bookings, colour = load" className="lg:col-span-2" bodyClass="p-4">
          <MapView markers={markers} height={380} />
          <div className="mt-3 flex flex-wrap gap-4 font-mono text-[10px] uppercase tracking-wider text-muted">
            {[
              ['< 40%', 'var(--ok)'],
              ['40-70%', 'var(--warn)'],
              ['70-90%', 'var(--hot)'],
              ['90%+', 'var(--alert)'],
            ].map(([l, c]) => (
              <span key={l} className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: c }} aria-hidden="true" /> {l}
              </span>
            ))}
          </div>
        </Card>

        <div className="space-y-5">
          <Card title="Severity mix" eyebrow="bookings today">
            <SeverityMix counts={d.severity} />
          </Card>
          <Card title="Referrals" eyebrow="by status" action={<GitBranch size={14} className="text-dim" aria-hidden="true" />}>
            {Object.keys(d.referrals).length === 0 ? (
              <p className="text-sm text-muted">No referrals yet.</p>
            ) : (
              <KeyValueList items={Object.entries(d.referrals).map(([k, v]) => [statusLabel(k), v])} />
            )}
          </Card>
        </div>
      </div>

      <Card title="Load by hospital" eyebrow={`top ${chartData.length} by load`} bodyClass="p-4">
        <ChartFrame height={Math.max(160, chartData.length * 30 + 24)} crosshair={false} label="Bar chart of load percentage per hospital">
          {({ width, height }) => (
            <BarChart width={width} height={height} data={chartData} layout="vertical" margin={{ top: 4, right: 28, bottom: 4, left: 4 }}>
              <CartesianGrid horizontal={false} stroke={grid.stroke} />
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis type="category" dataKey="name" width={170} {...axis} />
              <RTooltip cursor={{ fill: 'var(--panel-2)' }} content={<MonoTooltip valueFormat={(v) => `${v}%`} />} />
              <Bar dataKey="load" name="Load" radius={[0, 3, 3, 0]} isAnimationActive={animate}>
                {chartData.map((c) => (
                  <Cell key={c.name} fill={c.color} />
                ))}
              </Bar>
            </BarChart>
          )}
        </ChartFrame>
      </Card>

      <Card title="Hospitals by load" eyebrow="sort any column" bodyClass="p-4">
        <Table
          caption="Hospitals by load"
          rows={d.hospitals}
          rowKey={(h) => h.id}
          loading={dash.loading}
          pageSize={10}
          initialSort={{ key: 'load_pct', dir: 'desc' }}
          columns={[
            { key: 'name', label: 'Hospital', sortable: true, render: (h) => <span className="font-medium text-fg">{h.name}</span> },
            {
              key: 'load_pct',
              label: 'Load',
              sortable: true,
              className: 'min-w-44',
              render: (h) => (
                <div className="flex items-center gap-2">
                  <div className="flex-1">
                    <ProgressBar value={h.load_pct} tone={toneFor(h.load_pct)} segments={14} />
                  </div>
                  <span className="w-12 text-right font-mono text-xs tabular-nums">{h.load_pct}%</span>
                </div>
              ),
            },
            { key: 'booked', label: 'Booked', align: 'right', sortable: true, render: (h) => <span className="font-mono text-xs tabular-nums">{h.booked}/{h.op_limit}</span> },
            { key: 'waiting', label: 'Waiting', align: 'right', sortable: true, render: (h) => <span className="font-mono text-xs tabular-nums">{h.waiting}</span> },
            { key: 'avg_wait_min', label: 'Avg / max wait', align: 'right', render: (h) => <span className="whitespace-nowrap font-mono text-xs">{h.avg_wait_min} / {h.max_wait_min} min</span> },
            { key: 'emergencies', label: 'Emerg.', align: 'right', render: (h) => <span className="font-mono text-xs">{h.emergencies}/{h.emergency_quota}</span> },
            { key: 'severity', label: 'Severity', className: 'hidden w-44 md:table-cell', render: (h) => <SeverityMix counts={h.severity} showLegend={false} height="h-2" /> },
          ]}
          cards={(h) => (
            <div className="panel p-3">
              <div className="flex items-baseline justify-between gap-2">
                <span className="truncate font-medium text-fg">{h.name}</span>
                <span className="font-mono text-xs tabular-nums">{h.load_pct}%</span>
              </div>
              <div className="mt-2">
                <ProgressBar value={h.load_pct} tone={toneFor(h.load_pct)} segments={20} />
              </div>
              <div className="mt-2 font-mono text-[11px] text-muted">
                booked {h.booked}/{h.op_limit} - waiting {h.waiting} - wait {h.avg_wait_min} min
              </div>
            </div>
          )}
        />
        <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.1em] text-dim">
          Queues include clearly labelled sample patients generated at start-up so the network shows realistic load.
        </p>
      </Card>

      <ActivityLog height={220} title="dashboard.log" />
    </div>
  )
}
