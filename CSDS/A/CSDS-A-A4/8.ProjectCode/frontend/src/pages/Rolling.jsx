import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowLeftRight, CalendarClock, IndianRupee, PackageCheck, Play, RefreshCcw, ShieldCheck, Table2, Timer, Waypoints } from 'lucide-react'
import { BarLine, ChartLegend, LineCompare } from '../components/charts'
import { Stagger } from '../components/motion'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Input,
  PageHeader,
  PageSkeleton,
  ProgressBar,
  StatCard,
  Table,
  Tabs,
  Timeline,
  useToast,
} from '../components/ui'
import { api } from '../lib/api'
import { celebrate } from '../lib/confetti'
import { fmtCompact, fmtINR, fmtInt, fmtPct, fmtSigned, monthLabel } from '../lib/format'
import { softSpring } from '../lib/motion'
import { useChartTheme } from '../lib/palette'
import { useApi, usePoll } from '../lib/useApi'

function Since({ from }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  return <span className="num">{Math.max(0, Math.round(now / 1000 - from))} s</span>
}

export default function Rolling() {
  const toast = useToast()
  const t = useChartTheme()
  const [months, setMonths] = useState('6')
  const [monthsErr, setMonthsErr] = useState(null)
  const [job, setJob] = useState(null)
  const [jobError, setJobError] = useState(null)
  const [view, setView] = useState('timeline')
  const { data, error, loading, reload } = useApi(async (o) => {
    const [ro, jobs] = await Promise.all([api.rolling(o), api.jobs(o)])
    return { ro, jobs }
  })

  useEffect(() => {
    if (data?.jobs.rolling.running) setJob(data.jobs.rolling)
  }, [data])

  usePoll(
    () => api.jobs().then((j) => j.rolling),
    !!job?.running,
    async (st) => {
      setJob(null)
      if (st.error) {
        setJobError(st.error)
        toast({ kind: 'error', title: 'Rolling re-optimisation failed', message: st.error })
        return
      }
      await reload({ quiet: true })
      toast({ kind: 'success', title: 'Rolling re-optimisation finished', message: 'Adaptive and static plans scored month by month.' })
      celebrate('rolling')
    },
  )

  const start = async () => {
    const n = Number(months)
    if (!Number.isInteger(n) || n < 2 || n > 12) {
      setMonthsErr('Between 2 and 12 months')
      return
    }
    setMonthsErr(null)
    setJobError(null)
    try {
      await api.runRolling({ n_months: n })
      setJob({ running: true, started_at: Date.now() / 1000 })
      toast({ kind: 'info', title: `Simulating the last ${n} months`, message: 'Each month: re-forecast, re-plan, score. This takes about 5 s per month.' })
    } catch (e) {
      toast({ kind: 'error', title: 'Could not start the simulation', message: e.message })
    }
  }

  const header = (
    <PageHeader
      eyebrow="Objective 5 · Adapting to change"
      icon={RefreshCcw}
      title="Re-optimising as demand changes"
      lead="Each month the forecaster is re-run with the data available at that time and the matheuristic re-plans the network; the plan is scored on realised demand. A static plan, fixed once on the historical average (the traditional assumption), is scored on the same months."
    />
  )

  if (loading)
    return (
      <>
        {header}
        <PageSkeleton />
      </>
    )
  if (error)
    return (
      <>
        {header}
        <ErrorState title="Could not load the rolling-horizon results" error={error} onRetry={reload} />
      </>
    )

  const ro = data.ro && data.ro.timeline ? data.ro : null
  const running = !!job?.running

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}

      <Card title="Run the rolling horizon" subtitle="Simulates the most recent months of history" hover={false}>
        <form
          className="row"
          style={{ alignItems: 'flex-end', '--gap': '16px' }}
          onSubmit={(e) => {
            e.preventDefault()
            start()
          }}
          noValidate
        >
          <div style={{ flex: '1 1 180px', maxWidth: 240 }}>
            <Input label="Months to simulate" type="number" min={2} max={12} value={months} onChange={(e) => setMonths(e.target.value)} error={monthsErr} hint="2 – 12" disabled={running} />
          </div>
          <Button type="submit" icon={Play} loading={running} disabled={running} style={{ marginBottom: 26 }}>
            {running ? 'Running…' : 'Run rolling horizon'}
          </Button>
        </form>
        <AnimatePresence>
          {running && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={softSpring} style={{ overflow: 'hidden' }}>
              <div style={{ paddingTop: 16 }}>
                <div className="row between small" style={{ marginBottom: 8 }}>
                  <span>Re-forecasting and re-planning month by month… you can leave this page.</span>
                  <span className="muted">
                    <Timer size={14} aria-hidden="true" style={{ verticalAlign: -2, marginRight: 4 }} />
                    <Since from={job.started_at} />
                  </span>
                </div>
                <ProgressBar indeterminate label="Rolling re-optimisation running" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {jobError && !running && (
          <div style={{ marginTop: 18 }}>
            <ErrorState compact title="The last run failed" error={jobError} hint="Try fewer months, then run it again." />
          </div>
        )}
      </Card>

      {!ro ? (
        <EmptyState icon={RefreshCcw} title="No rolling-horizon results yet" message="Run the simulation to compare month-by-month re-optimisation with a static plan." action={<Button icon={Play} onClick={start} disabled={running}>Run rolling horizon</Button>} />
      ) : (
        <RollingResults ro={ro} t={t} view={view} setView={setView} />
      )}
    </div>
  )
}

function RollingResults({ ro, t, view, setView }) {
  const a = ro.adaptive_avg
  const s = ro.static_avg
  const costDelta = ((a.total_cost - s.total_cost) / s.total_cost) * 100
  const tl = ro.timeline
  return (
    <motion.div className="stack" style={{ '--gap': '22px' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Stagger className="grid-kpi">
        <Stagger.Item>
          <StatCard
            label="Avg fulfilment · adaptive"
            value={a.fulfilment_rate * 100}
            format={(v) => `${v.toFixed(1)}%`}
            icon={PackageCheck}
            tone="mint"
            delta={{ value: (a.fulfilment_rate - s.fulfilment_rate) * 100, text: `${((a.fulfilment_rate - s.fulfilment_rate) * 100).toFixed(1)} pts`, label: `vs ${fmtPct(s.fulfilment_rate)} static` }}
          />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard
            label="Avg SLA reliability · adaptive"
            value={a.reliability_sla * 100}
            format={(v) => `${v.toFixed(1)}%`}
            icon={ShieldCheck}
            tone="sky"
            delta={{ value: (a.reliability_sla - s.reliability_sla) * 100, text: `${((a.reliability_sla - s.reliability_sla) * 100).toFixed(1)} pts`, label: `vs ${fmtPct(s.reliability_sla)} static` }}
          />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard
            label="Avg operating cost vs static"
            value={costDelta}
            format={(v) => fmtSigned(v, 1)}
            icon={IndianRupee}
            tone="peach"
            delta={{ value: costDelta, text: fmtINR(a.total_cost), good: 'down', label: `vs ${fmtINR(s.total_cost)}` }}
          />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Hub openings across the horizon" value={ro.hub_changes} icon={ArrowLeftRight} tone="lavender" foot={`${ro.periods.length} months · ${monthLabel(ro.periods[0])} – ${monthLabel(ro.periods.at(-1))}`} />
        </Stagger.Item>
      </Stagger>

      <Card tint="lavender" hover={false}>
        <div className="row" style={{ '--gap': '10px' }}>
          <strong>Static plan hubs (fixed on the historical average):</strong>
          {ro.static_hubs.map((h) => (
            <Badge key={h} tone="neutral">
              {h}
            </Badge>
          ))}
        </div>
      </Card>

      <div className="grid-2">
        <Card title="Fulfilment rate by month" subtitle="Adaptive re-planning vs one static plan">
          <ChartLegend
            items={[
              { label: 'Adaptive', color: t.mint },
              { label: 'Static', color: t.rose },
            ]}
          />
          <LineCompare
            data={tl.map((x) => ({ x: x.period, adaptive: +(x.adaptive.fulfilment_rate * 100).toFixed(2), static: +(x.static.fulfilment_rate * 100).toFixed(2) }))}
            series={[
              { key: 'adaptive', name: 'Adaptive', color: t.mint },
              { key: 'static', name: 'Static', color: t.rose, dashed: true },
            ]}
            valueFormat={(v) => `${v}%`}
            xFormat={monthLabel}
            label="Line chart of monthly fulfilment rate, adaptive versus static"
          />
        </Card>
        <Card title="Realised demand vs forecast" subtitle="Network total per month">
          <ChartLegend
            items={[
              { label: 'Realised', color: t.sky },
              { label: 'Forecast', color: t.peach },
            ]}
          />
          <BarLine
            data={tl.map((x) => ({ x: x.period, realised: x.realized_total, forecast: x.forecast_total }))}
            bar={{ key: 'realised', name: 'Realised', color: t.sky }}
            line={{ key: 'forecast', name: 'Forecast', color: t.peach }}
            valueFormat={fmtCompact}
            xFormat={monthLabel}
            label="Bar and line chart of realised demand versus forecast per month"
          />
        </Card>
      </div>

      <Card
        title="Month by month"
        hover={false}
        actions={
          <Tabs
            name="rolling"
            value={view}
            onChange={setView}
            label="Monthly view"
            tabs={[
              { id: 'timeline', label: 'Timeline', icon: CalendarClock },
              { id: 'table', label: 'Table', icon: Table2 },
            ]}
          />
        }
      >
        {view === 'timeline' ? (
          <Timeline
            items={tl.map((x, i) => ({
              id: x.period,
              icon: Waypoints,
              tone: x.opened.length || x.closed.length ? 'peach' : 'mint',
              title: (
                <>
                  {monthLabel(x.period, true)}
                  {i === 0 && <Badge tone="neutral">initial plan</Badge>}
                  {x.opened.map((c) => (
                    <Badge key={`o${c}`} tone="mint">
                      +{c}
                    </Badge>
                  ))}
                  {x.closed.map((c) => (
                    <Badge key={`c${c}`} tone="rose">
                      −{c}
                    </Badge>
                  ))}
                </>
              ),
              meta: `Forecast ${fmtInt(x.forecast_total)} · realised ${fmtInt(x.realized_total)} (${x.forecast_error_pct}% error) · solved in ${x.solve_seconds} s`,
              extra: (
                <div className="small" style={{ color: 'var(--text-2)' }}>
                  <div>Hubs: {x.hub_cities.join(', ')}</div>
                  <div style={{ marginTop: 4 }}>
                    Adaptive <b>{fmtINR(x.adaptive.total_cost)}</b> · {fmtPct(x.adaptive.fulfilment_rate)} fulfilled &nbsp;|&nbsp; Static <b>{fmtINR(x.static.total_cost)}</b> · {fmtPct(x.static.fulfilment_rate)} fulfilled
                  </div>
                </div>
              ),
            }))}
          />
        ) : (
          <Table
            caption="Rolling re-optimisation per month"
            rows={tl}
            rowKey={(r) => r.period}
            pageSize={0}
            cardTitle={(r) => monthLabel(r.period, true)}
            columns={[
              { key: 'period', label: 'Month', render: (r) => monthLabel(r.period) },
              { key: 'forecast_total', label: 'Forecast', numeric: true, render: (r) => fmtInt(r.forecast_total) },
              { key: 'realized_total', label: 'Realised', numeric: true, render: (r) => fmtInt(r.realized_total) },
              { key: 'forecast_error_pct', label: 'Error', numeric: true, render: (r) => `${r.forecast_error_pct}%` },
              { key: 'hub_cities', label: 'Hubs', wrap: true, sortable: false, render: (r) => <span className="small muted">{r.hub_cities.join(', ')}</span> },
              {
                key: 'changes',
                label: 'Changes',
                sortable: false,
                render: (r) => (
                  <span className="row" style={{ '--gap': '4px' }}>
                    {r.opened.map((c) => (
                      <Badge key={c} tone="mint">
                        +{c}
                      </Badge>
                    ))}
                    {r.closed.map((c) => (
                      <Badge key={c} tone="rose">
                        −{c}
                      </Badge>
                    ))}
                    {!r.opened.length && !r.closed.length && '–'}
                  </span>
                ),
              },
              { key: 'ac', label: 'Adaptive cost', numeric: true, sortValue: (r) => r.adaptive.total_cost, render: (r) => fmtINR(r.adaptive.total_cost) },
              { key: 'af', label: 'Adaptive fulfil', numeric: true, sortValue: (r) => r.adaptive.fulfilment_rate, render: (r) => fmtPct(r.adaptive.fulfilment_rate) },
              { key: 'sc', label: 'Static cost', numeric: true, sortValue: (r) => r.static.total_cost, render: (r) => fmtINR(r.static.total_cost) },
              { key: 'sf', label: 'Static fulfil', numeric: true, sortValue: (r) => r.static.fulfilment_rate, render: (r) => fmtPct(r.static.fulfilment_rate) },
            ]}
          />
        )}
      </Card>
    </motion.div>
  )
}
