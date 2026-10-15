import { useState } from 'react'
import { AlertTriangle, CalendarX, Clock, Eye, Footprints, RefreshCw, ShieldAlert } from 'lucide-react'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, Input, PageHeader, Skeleton, StatCard, Table } from '../components/ui'
import { ChartCard, DonutChart } from '../components/charts'
import { Stagger } from '../components/motion'
import ActivityTimeline from '../components/care/ActivityTimeline'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { activityColor, clock, duration, humanize, localDay, ALERT_STATUS } from '../lib/format'

export default function Report() {
  const [day, setDay] = useState(localDay())
  const report = useAsync(() => api.get('/reports/daily', { params: { day } }), [day])
  const days = useAsync(() => api.get('/reports/days'), [])
  const d = report.data

  const from = new Date(`${day}T00:00:00`)
  const to = new Date(from.getTime() + 24 * 3600 * 1000)
  const totals = d ? Object.entries(d.totals) : []
  const donut = totals.map(([k, v]) => ({ name: humanize(k), value: v, color: activityColor(k) }))

  const columns = [
    {
      key: 'activity',
      label: 'Activity',
      sortValue: ([k]) => k,
      render: ([k]) => (
        <span className="cap">
          <span className="legend"><i style={{ background: activityColor(k) }} /></span>
          {humanize(k)}
        </span>
      ),
    },
    { key: 'time', label: 'Time', num: true, sortValue: ([, v]) => v, render: ([, v]) => duration(v) },
    {
      key: 'share',
      label: 'Share of monitored time',
      num: true,
      sortValue: ([, v]) => v,
      render: ([, v]) => `${d.monitored_seconds ? Math.round((v / d.monitored_seconds) * 100) : 0}%`,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Daily report"
        description="Time spent per activity, plus long-inactivity warnings and falls."
        actions={
          <>
            <Input label="Day" labelHidden type="date" value={day} max={localDay()} onChange={(e) => e.target.value && setDay(e.target.value)} />
            <Button icon={RefreshCw} onClick={() => { report.reload(); days.reload({ quiet: true }) }} loading={report.loading && !!d}>
              Refresh
            </Button>
          </>
        }
      />

      {days.data?.length > 0 && (
        <div className="chip-row" style={{ marginBottom: 18 }}>
          <span className="faint">Days with data:</span>
          {days.data.slice(0, 10).map((x) => (
            <button key={x} type="button" className="chip" aria-pressed={x === day} onClick={() => setDay(x)}>
              {x}
            </button>
          ))}
        </div>
      )}

      {report.error && !d ? (
        <ErrorState title="Couldn't load the report" error={report.error} onRetry={report.reload} />
      ) : (
        <>
          <Stagger className="grid grid-4" gap={0.06}>
            <StatCard label="Monitored" icon={Clock} value={d ? duration(d.monitored_seconds) : undefined} loading={!d} />
            <StatCard label="Person in view" icon={Eye} value={d ? duration(d.present_seconds) : undefined} loading={!d} />
            <StatCard label="Active (walk, drink, pick up)" icon={Footprints} tone="info" value={d ? duration(d.active_seconds) : undefined} loading={!d} />
            <StatCard
              label="Inactivity warnings"
              icon={AlertTriangle}
              tone={d?.warnings.length ? 'warn' : undefined}
              value={d ? d.warnings.length : undefined}
              delta={d ? `over ${d.inactivity_threshold_minutes} min without moving` : undefined}
              loading={!d}
            />
          </Stagger>

          {!d ? (
            <Skeleton height={260} style={{ marginTop: 18 }} />
          ) : d.monitored_seconds === 0 ? (
            <Card className="mt">
              <EmptyState icon={CalendarX} title="No monitoring data for this day" actions={days.data?.length ? <Button onClick={() => setDay(days.data[0])}>Jump to {days.data[0]}</Button> : null}>
                {days.data?.length
                  ? 'Pick a day with data above, or start the live monitor to record today.'
                  : 'Start the live monitor and activity will be recorded here.'}
              </EmptyState>
            </Card>
          ) : (
            <>
              <Card className="mt">
                <CardHeader title="Timeline" subtitle={day} />
                <div className="card-body">
                  <ActivityTimeline segments={d.timeline} from={from} to={to} ticks={8} />
                </div>
              </Card>

              <div className="grid grid-2 mt">
                <ChartCard title="Time per activity" subtitle="Share of monitored time" height={260}>
                  <DonutChart data={donut} centerValue={duration(d.monitored_seconds)} centerLabel="monitored" />
                </ChartCard>
                <Card>
                  <CardHeader title="Breakdown" />
                  <Table columns={columns} rows={totals} rowKey={([k]) => k} pageSize={8} cards={false} caption="Time per activity" initialSort={{ key: 'time', dir: 'desc' }} />
                </Card>
              </div>

              <Card className="mt">
                <CardHeader title="Warnings and falls" />
                <div className="card-body stack" style={{ gap: 10 }}>
                  {d.warnings.length === 0 && d.falls.length === 0 && (
                    <div className="notice safe">No warnings - no long inactivity and no falls on this day.</div>
                  )}
                  {d.warnings.map((w) => (
                    <div key={`w${w.id}`} className="notice warn">
                      <AlertTriangle size={18} aria-hidden="true" />
                      <div>
                        Long inactivity: no movement for <strong>{w.minutes} min</strong>
                        {w.activity && ` while ${humanize(w.activity)}`}, from {clock(w.started_at)}
                        {!w.ended_at && ' (ongoing)'}
                      </div>
                    </div>
                  ))}
                  {d.falls.map((f) => {
                    const s = ALERT_STATUS[f.status] || { label: f.status, tone: 'neutral' }
                    return (
                      <div key={`f${f.id}`} className="notice danger">
                        <ShieldAlert size={18} aria-hidden="true" />
                        <div>
                          Fall at {clock(f.detected_at)} <Badge tone={s.tone}>{s.label}</Badge>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  )
}
