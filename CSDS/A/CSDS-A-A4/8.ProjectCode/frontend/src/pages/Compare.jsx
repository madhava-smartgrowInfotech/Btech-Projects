import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { BarChart3, Gauge, Layers, Play, Scale, Timer } from 'lucide-react'
import { BarCompare, ChartLegend, GroupedBars } from '../components/charts'
import { Stagger } from '../components/motion'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Input,
  KeyValueList,
  PageHeader,
  PageSkeleton,
  ProgressBar,
  Select,
  Table,
  Tabs,
  useToast,
} from '../components/ui'
import { api } from '../lib/api'
import { celebrate } from '../lib/confetti'
import { fmtINR, fmtInt, fmtPct, fmtSigned, monthLabel } from '../lib/format'
import { softSpring } from '../lib/motion'
import { useChartTheme } from '../lib/palette'
import { getOptions } from '../lib/shared'
import { useApi, usePoll } from '../lib/useApi'

const SHORT = {
  proposed: 'RF + matheuristic',
  exact_mip: 'RF + exact MIP',
  greedy: 'RF + greedy',
  kmeans: 'RF + k-means',
  largest: 'Largest markets',
  fixed_avg: 'Hist. avg + matheuristic',
}

function Since({ from }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  return <span className="num">{Math.max(0, Math.round(now / 1000 - from))} s</span>
}

export default function Compare() {
  const toast = useToast()
  const t = useChartTheme()
  const [tab, setTab] = useState('comparison')
  const [period, setPeriod] = useState(null)
  const [limit, setLimit] = useState('30')
  const [job, setJob] = useState(null) // {running, kind, started_at}
  const [jobError, setJobError] = useState(null)
  const { data, error, loading, reload } = useApi(async (o) => {
    const [cmp, scal, options, jobs] = await Promise.all([api.compare(o), api.scalability(o), getOptions(), api.jobs(o)])
    return { cmp, scal, options, jobs }
  })

  useEffect(() => {
    if (!data) return
    if (!period) setPeriod(data.options.default_eval_period)
    if (data.jobs.compare.running) setJob(data.jobs.compare)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  usePoll(
    () => api.jobs().then((j) => j.compare),
    !!job?.running,
    async (st) => {
      const kind = job?.kind || st.kind
      setJob(null)
      if (st.error) {
        setJobError(st.error)
        toast({ kind: 'error', title: `The ${kind} job failed`, message: st.error })
        return
      }
      await reload({ quiet: true })
      setTab(kind === 'scalability' ? 'scalability' : 'comparison')
      toast({ kind: 'success', title: kind === 'scalability' ? 'Scalability benchmark finished' : 'Comparison finished', message: 'Results updated below.' })
      celebrate(kind)
    },
  )

  const start = async (scalability) => {
    const lim = Number(limit)
    if (!(lim >= 5 && lim <= 300)) {
      toast({ kind: 'error', title: 'Check the time limit', message: 'Exact MIP time limit must be between 5 and 300 seconds.' })
      return
    }
    setJobError(null)
    try {
      const r = await api.runCompare({ period, exact_limit: lim, scalability })
      setJob({ running: true, kind: r.started, started_at: Date.now() / 1000 })
      toast({ kind: 'info', title: scalability ? 'Scalability benchmark started' : `Comparison started for ${monthLabel(r.period)}`, message: 'Running in the background - this can take a minute.' })
    } catch (e) {
      toast({ kind: 'error', title: 'Could not start the job', message: e.message })
    }
  }

  const header = (
    <PageHeader
      eyebrow="Objective 6 · Evaluation"
      icon={BarChart3}
      title="Proposed vs traditional methods"
      lead="Every method plans the same month and is scored on the demand that actually occurred: the full exact MIP (time-limited), a greedy heuristic, k-means clustering, a managerial “largest markets” rule and a fixed historical-average demand plan."
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
        <ErrorState title="Could not load comparison results" error={error} onRetry={reload} />
      </>
    )

  const { cmp, scal, options } = data
  const hasCmp = cmp && cmp.methods
  const methods = hasCmp ? Object.entries(cmp.methods).map(([key, m]) => ({ key, ...m })) : []
  const running = !!job?.running

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}

      <Card title="Run an evaluation" subtitle="Jobs run in the background on the API; results replace the saved ones in results/" hover={false}>
        <div className="row" style={{ alignItems: 'flex-end', '--gap': '16px' }}>
          <div style={{ flex: '1 1 200px', maxWidth: 260 }}>
            <Select label="Evaluation month" value={period || ''} onChange={(e) => setPeriod(e.target.value)} options={options.eval_periods.map((p) => ({ value: p, label: monthLabel(p) }))} disabled={running} />
          </div>
          <div style={{ flex: '1 1 160px', maxWidth: 220 }}>
            <Input label="Exact MIP time limit (s)" type="number" min={5} max={300} value={limit} onChange={(e) => setLimit(e.target.value)} disabled={running} />
          </div>
          <div className="row">
            <Button icon={Play} onClick={() => start(false)} disabled={running} loading={running && job.kind === 'comparison'}>
              Run comparison
            </Button>
            <Button variant="secondary" icon={Layers} onClick={() => start(true)} disabled={running} loading={running && job.kind === 'scalability'}>
              Run scalability benchmark
            </Button>
          </div>
        </div>
        <AnimatePresence>
          {running && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={softSpring} style={{ overflow: 'hidden' }}>
              <div style={{ paddingTop: 18 }}>
                <div className="row between small" style={{ marginBottom: 8 }}>
                  <span>
                    Running the {job.kind} job… you can leave this page; it keeps going.
                  </span>
                  <span className="muted">
                    <Timer size={14} aria-hidden="true" style={{ verticalAlign: -2, marginRight: 4 }} />
                    <Since from={job.started_at} />
                  </span>
                </div>
                <ProgressBar indeterminate label={`${job.kind} running`} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {jobError && !running && (
          <div style={{ marginTop: 18 }}>
            <ErrorState compact title="The last job failed" error={jobError} hint="Try a longer time limit or another month, then run it again." />
          </div>
        )}
      </Card>

      <Tabs
        name="compare"
        value={tab}
        onChange={setTab}
        label="Result views"
        tabs={[
          { id: 'comparison', label: 'Method comparison', icon: Scale },
          { id: 'scalability', label: 'Scalability', icon: Gauge },
        ]}
      />

      {tab === 'comparison' &&
        (hasCmp ? (
          <motion.div className="stack" style={{ '--gap': '22px' }} key="cmp" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={softSpring}>
            <Stagger className="grid-kpi">
              <Stagger.Item>
                <Card tint="lavender">
                  <span className="stat-label">Proposed hubs</span>
                  <div style={{ fontWeight: 700, marginTop: 8 }}>{cmp.methods.proposed?.hub_cities.join(', ')}</div>
                </Card>
              </Stagger.Item>
              <Stagger.Item>
                <Card tint="mint">
                  <span className="stat-label">Cheapest alternative vs proposed</span>
                  <div className="stat-value">
                    {fmtSigned(Math.min(...methods.filter((m) => m.key !== 'proposed').map((m) => m.cost_vs_proposed_pct)))}
                  </div>
                </Card>
              </Stagger.Item>
              <Stagger.Item>
                <Card tint="sky">
                  <KeyValueList
                    items={[
                      ['Forecast demand', fmtInt(cmp.forecast_total_demand)],
                      ['Realised demand', fmtInt(cmp.realized_total_demand)],
                      ['p · capacity · SLA', `${cmp.params.n_hubs} · ${cmp.params.capacity_factor} · ${cmp.params.sla_hours} h`],
                    ]}
                  />
                </Card>
              </Stagger.Item>
            </Stagger>

            <Card title="All methods, scored on realised demand" hover={false}>
              <Table
                caption="Method comparison"
                rows={methods}
                rowKey={(r) => r.key}
                pageSize={0}
                highlight={(r) => r.key === 'proposed'}
                cardTitle={(r) => r.label}
                columns={[
                  { key: 'label', label: 'Method', wrap: true },
                  { key: 'hub_cities', label: 'Hubs', wrap: true, sortable: false, render: (r) => <span className="small muted">{r.hub_cities.join(', ')}</span> },
                  { key: 'total_cost', label: 'Operating cost', numeric: true, render: (r) => fmtINR(r.total_cost) },
                  {
                    key: 'cost_vs_proposed_pct',
                    label: 'vs proposed',
                    numeric: true,
                    render: (r) => <Badge tone={r.cost_vs_proposed_pct > 0.005 ? 'rose' : r.cost_vs_proposed_pct < -0.005 ? 'mint' : 'neutral'}>{fmtSigned(r.cost_vs_proposed_pct)}</Badge>,
                  },
                  { key: 'avg_delivery_hours', label: 'Avg delivery', numeric: true, render: (r) => `${r.avg_delivery_hours} h` },
                  { key: 'fulfilment_rate', label: 'Fulfilment', numeric: true, render: (r) => fmtPct(r.fulfilment_rate) },
                  { key: 'reliability_sla', label: 'SLA reliability', numeric: true, render: (r) => fmtPct(r.reliability_sla) },
                  { key: 'overloaded_hubs', label: 'Overloaded', numeric: true, render: (r) => (r.overloaded_hubs ? <Badge tone="peach">{r.overloaded_hubs}</Badge> : 0) },
                  { key: 'seconds', label: 'Solve time', numeric: true, render: (r) => `${r.seconds} s` },
                ]}
              />
            </Card>

            <div className="grid-2">
              <Card title="Operating cost" subtitle="Per month, lower is better">
                <BarCompare
                  horizontal
                  height={320}
                  yWidth={160}
                  name="Operating cost"
                  data={methods.map((m) => ({ name: SHORT[m.key] || m.label, value: m.total_cost, highlight: m.key === 'proposed' }))}
                  valueFormat={(v) => fmtINR(v)}
                  label="Bar chart of operating cost by method"
                />
              </Card>
              <Card title="Fulfilment rate" subtitle="Share of realised orders served, higher is better">
                <BarCompare
                  horizontal
                  height={320}
                  yWidth={160}
                  name="Fulfilment"
                  color={t.mint}
                  data={methods.map((m) => ({ name: SHORT[m.key] || m.label, value: +(m.fulfilment_rate * 100).toFixed(1), highlight: m.key === 'proposed' }))}
                  valueFormat={(v) => `${v}%`}
                  label="Bar chart of fulfilment rate by method"
                />
              </Card>
            </div>
          </motion.div>
        ) : (
          <EmptyState icon={Scale} title="No comparison results yet" message="Run a comparison for an evaluation month to score every method on realised demand." action={<Button icon={Play} onClick={() => start(false)} disabled={running}>Run comparison</Button>} />
        ))}

      {tab === 'scalability' &&
        (scal?.length ? (
          <motion.div className="grid-2" key="scal" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={softSpring}>
            <Card title="Exact MIP vs matheuristic" subtitle="Every region is split into nearby demand points; the exact MIP stops at its time limit">
              <ChartLegend
                items={[
                  { label: 'Matheuristic', color: t.lavender },
                  { label: 'Exact MIP', color: t.peach },
                ]}
              />
              <GroupedBars
                height={300}
                data={scal.map((s) => ({ x: `${s.nodes} nodes`, mh: s.matheuristic_seconds, ex: s.exact_seconds ?? null }))}
                series={[
                  { key: 'mh', name: 'Matheuristic', color: t.lavender },
                  { key: 'ex', name: 'Exact MIP', color: t.peach },
                ]}
                valueFormat={(v) => `${v} s`}
                label="Grouped bar chart of solve time by network size"
              />
            </Card>
            <Card title="Benchmark runs" hover={false}>
              <Table
                caption="Scalability benchmark"
                rows={scal}
                rowKey={(r, i) => `${r.nodes}-${i}`}
                pageSize={0}
                cardTitle={(r) => `${r.nodes} demand points`}
                columns={[
                  { key: 'nodes', label: 'Demand points', numeric: true },
                  { key: 'binary_vars', label: 'Binary vars', numeric: true, render: (r) => fmtInt(r.binary_vars) },
                  { key: 'matheuristic_seconds', label: 'Matheuristic', numeric: true, render: (r) => `${r.matheuristic_seconds} s` },
                  { key: 'exact_seconds', label: 'Exact MIP', numeric: true, render: (r) => (r.exact_seconds != null ? `${r.exact_seconds} s` : '–') },
                  { key: 'exact_status', label: 'Exact status', render: (r) => <Badge tone={r.exact_status === 'Optimal' ? 'mint' : 'peach'}>{r.exact_status || '–'}</Badge> },
                  { key: 'matheuristic_gap_pct', label: 'Gap', numeric: true, render: (r) => (r.matheuristic_gap_pct != null ? `${r.matheuristic_gap_pct}%` : '–') },
                ]}
              />
            </Card>
          </motion.div>
        ) : (
          <EmptyState icon={Gauge} title="No benchmark yet" message="Run the scalability benchmark to time the exact MIP and the matheuristic on networks of 90, 180 and 270 demand points." action={<Button icon={Layers} onClick={() => start(true)} disabled={running}>Run scalability benchmark</Button>} />
        ))}
    </div>
  )
}
