import { AlertOctagon, ArrowRight, FileText, IndianRupee, Network, Play, Users } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, Tooltip, XAxis, YAxis } from 'recharts'
import api, { describeError, useApi } from '../api'
import { ChainItem, TaxpayerLink } from '../components/domain/blocks'
import { CountUp, Stagger } from '../components/motion'
import ActivityLog from '../components/ui/ActivityLog'
import { PageHeader } from '../components/ui/AppShell'
import { ChartFrame, ChartLegend, MonoTooltip, useChartTheme } from '../components/ui/charts'
import { Button, Input } from '../components/ui/controls'
import { Card, PatternTag, RiskBadge, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, ProgressBar, Skeleton, useToast } from '../components/ui/feedback'
import { Stepper } from '../components/ui/nav'
import Table from '../components/ui/Table'
import { inr, lastDelta, monthLabel, num, pct, riskTone, stamp } from '../format'
import { logEvent } from '../lib/activity'

const STAGES = [
  { id: 'generate', label: 'Generate' }, { id: 'features', label: 'Features' }, { id: 'train', label: 'Train JEPA' },
  { id: 'score', label: 'Score' }, { id: 'graph', label: 'Rings' }, { id: 'invoices', label: 'Invoices' },
  { id: 'risk', label: 'Risk' }, { id: 'evidence', label: 'Evidence' },
]
let historyLogged = false

function Generator({ onDone }) {
  const [seed, setSeed] = useState('42')
  const [n, setN] = useState('600')
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const timer = useRef(null)
  const watching = useRef(false) // only refresh the dashboard after a run we saw in progress
  const lastMsg = useRef('')
  const toast = useToast()

  const poll = () => {
    api.get('/pipeline/status', { silent: true })
      .then(({ data }) => {
        setStatus(data)
        const msg = `[${data.stage}] ${data.progress}% ${data.message}`
        if (data.running && msg !== lastMsg.current) { logEvent('pipeline', msg); lastMsg.current = msg }
        if (data.running) {
          watching.current = true
          timer.current = setTimeout(poll, 1000)
        } else if (watching.current) {
          watching.current = false
          lastMsg.current = ''
          if (data.stage === 'failed') {
            setError({ message: data.error || 'Generation failed', hint: 'Check the API window for the traceback, then try again.' })
            logEvent('error', `generation failed: ${data.error}`)
            toast({ tone: 'alert', title: 'Generation failed', body: data.error })
          } else {
            logEvent('pipeline', `[done] ecosystem ${data.current?.run_key} ready · seed ${data.current?.seed} · ${data.current?.taxpayers} taxpayers`)
            toast({ tone: 'ok', title: 'Ecosystem analysed', body: `Seed ${data.current?.seed}, ${data.current?.taxpayers} taxpayers. Dashboard refreshed.` })
            window.dispatchEvent(new Event('ts:ecosystem'))
            onDone()
          }
        }
      })
      .catch((e) => setError(describeError(e)))
  }
  useEffect(() => {
    poll()
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const seedErr = seed === '' || +seed < 0 || +seed > 10000000 || !Number.isInteger(+seed) ? 'Whole number 0 - 10,000,000' : null
  const nErr = n === '' || +n < 150 || +n > 1500 || !Number.isInteger(+n) ? 'Between 150 and 1,500' : null

  async function start(e) {
    e.preventDefault()
    if (seedErr || nErr) return
    setError(null)
    setSubmitting(true)
    try {
      await api.post('/pipeline/run', { seed: Number(seed), taxpayers: Number(n) })
      logEvent('pipeline', `generation requested · seed ${seed} · ${n} taxpayers`)
      poll()
    } catch (err) {
      setError(describeError(err))
    } finally {
      setSubmitting(false)
    }
  }
  const running = !!status?.running
  return (
    <Card title="Generate & analyse" className="h-full" action={running && <span className="font-mono text-[11px] text-warn">running…</span>}>
      <form onSubmit={start} className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-start">
        <Input label="Seed" type="number" inputMode="numeric" min="0" max="10000000" value={seed} onChange={(e) => setSeed(e.target.value)} disabled={running} error={seedErr} />
        <Input label="Taxpayers" type="number" inputMode="numeric" min="150" max="1500" step="50" value={n} onChange={(e) => setN(e.target.value)} disabled={running} error={nErr} />
        <Button type="submit" size="lg" icon={Play} loading={running || submitting} disabled={!!seedErr || !!nErr} className="sm:mt-[22px]">
          {running ? 'Running…' : 'Generate & analyse'}
        </Button>
      </form>
      <p className="mt-3 text-xs text-muted">Creates taxpayers, invoices and returns with injected fraud, retrains the JEPA encoder on them and re-runs the whole analysis (about 20-40 s).</p>
      <div className="mt-4 space-y-3">
        <Stepper steps={STAGES} current={status?.stage} done={!running && !!status?.current && status?.stage !== 'failed'} failed={status?.stage === 'failed'} />
        {running && <ProgressBar value={status.progress} label={status.message} tone="warn" />}
      </div>
      {status?.current && !running && (
        <p className="mt-4 border-t border-line pt-3 font-mono text-[11px] text-muted">
          current: <span className="text-fg">{status.current.run_key}</span> · seed {status.current.seed} · {status.current.taxpayers} taxpayers · {status.current.dataset} · analysed {stamp(status.current.generated_at * 1000)}
        </p>
      )}
      {error && <div className="mt-3"><ErrorState error={error} title="Generation" compact /></div>}
    </Card>
  )
}

function Pulse({ months }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  return (
    <>
      <ChartFrame height={230} label="Monthly ITC available, claimed and claimed by flagged taxpayers">
        {({ width, height }) => (
          <ComposedChart width={width} height={height} data={months} margin={{ top: 8, right: 6, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id="pulseOk" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor={tokens.ok} stopOpacity={0.22} /><stop offset="100%" stopColor={tokens.ok} stopOpacity={0} /></linearGradient>
              <linearGradient id="pulseAlert" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor={tokens.alert} stopOpacity={0.3} /><stop offset="100%" stopColor={tokens.alert} stopOpacity={0} /></linearGradient>
            </defs>
            <CartesianGrid {...grid} />
            <XAxis dataKey="month" tickFormatter={monthLabel} {...axis} minTickGap={10} />
            <YAxis tickFormatter={inr} {...axis} width={72} />
            <Tooltip cursor={false} isAnimationActive={false} content={<MonoTooltip labelFormat={monthLabel} valueFormat={inr} />} />
            <Area type="monotone" dataKey="itc_claimed" name="ITC claimed (3B)" stroke={tokens.ok} strokeWidth={1.4} fill="url(#pulseOk)" isAnimationActive={animate} />
            <Line type="monotone" dataKey="itc_available" name="ITC available (2B)" stroke={tokens.muted} strokeWidth={1.2} strokeDasharray="4 3" dot={false} isAnimationActive={animate} />
            <Area type="monotone" dataKey="flagged_claimed" name="claimed by flagged" stroke={tokens.alert} strokeWidth={1.4} fill="url(#pulseAlert)" isAnimationActive={animate} />
          </ComposedChart>
        )}
      </ChartFrame>
      <ChartLegend items={[{ label: 'ITC claimed (3B)', color: 'var(--ok)' }, { label: 'ITC available (2B)', color: 'var(--muted)', line: true, dashed: true }, { label: 'claimed by flagged taxpayers', color: 'var(--alert)' }]} />
    </>
  )
}

function Histogram({ hist }) {
  const { tokens, axis, grid, animate } = useChartTheme()
  const rows = hist.map((c, i) => ({ bin: `${(i / 10).toFixed(1)}`, range: `${(i / 10).toFixed(1)}-${((i + 1) / 10).toFixed(1)}`, count: c, mid: i / 10 + 0.05 }))
  return (
    <ChartFrame height={170} label="Risk score distribution">
      {({ width, height }) => (
        <BarChart width={width} height={height} data={rows} margin={{ top: 6, right: 2, bottom: 0, left: 0 }}>
          <CartesianGrid {...grid} vertical={false} />
          <XAxis dataKey="bin" {...axis} interval={1} />
          <YAxis scale="sqrt" domain={[0, 'auto']} {...axis} width={34} />
          <Tooltip cursor={false} isAnimationActive={false} content={<MonoTooltip labelFormat={(l, p) => `risk ${p?.[0]?.payload?.range}`} valueFormat={(v) => `${v} taxpayers`} />} />
          <Bar dataKey="count" name="taxpayers" radius={[2, 2, 0, 0]} isAnimationActive={animate}>
            {rows.map((r) => <Cell key={r.bin} fill={tokens[riskTone(r.mid)]} />)}
          </Bar>
        </BarChart>
      )}
    </ChartFrame>
  )
}

function Headline({ h }) {
  const row = (label, model, base, f) => (
    <div>
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 flex items-baseline gap-3">
        <span className="font-mono text-3xl font-semibold text-ok"><CountUp value={model} format={f} /></span>
        <span className="font-mono text-sm text-dim">rules {f(base)}</span>
      </div>
      <div className="mt-2 space-y-1">
        {[['model', model, 'var(--ok)'], ['rules', base, 'var(--dim)']].map(([k, v, c]) => (
          <div key={k} className="flex items-center gap-2 font-mono text-[10px] uppercase text-dim">
            <span className="w-10">{k}</span>
            <div className="h-1.5 flex-1 bg-line-strong/60"><div className="h-full" style={{ width: `${v * 100}%`, background: c }} /></div>
          </div>
        ))}
      </div>
    </div>
  )
  return (
    <div className="space-y-5">
      {row(`Precision@${h.k} (top ${h.k} ranked)`, h.model_precision_at_k, h.baseline_precision_at_k, (v) => pct(v))}
      {row('F1 at the flag threshold', h.model_f1, h.baseline_f1, (v) => v.toFixed(2))}
      <p className="text-xs text-dim">Measured against the fraud labels injected by the generator (sample data).</p>
      <Link to="/app/performance" className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-ok hover:underline">Full evaluation <ArrowRight size={12} /></Link>
    </div>
  )
}

function Dashboard({ d, monthly }) {
  const s = d.stats
  const m = monthly?.months
  const patterns = Object.entries(s.pattern_counts).sort((a, b) => b[1] - a[1])
  const maxP = Math.max(1, ...patterns.map(([, c]) => c))
  const columns = [
    { key: 'rank', label: '#', render: (t) => <span className="font-mono text-xs text-dim">{String(t.rank).padStart(2, '0')}</span> },
    { key: 'legal_name', label: 'Taxpayer', render: (t) => <TaxpayerLink gstin={t.gstin} name={t.legal_name} /> },
    { key: 'patterns', label: 'Patterns', render: (t) => <div className="flex flex-wrap gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}</div> },
    { key: 'itc_at_risk', label: 'ITC at risk', align: 'right', render: (t) => <span className="whitespace-nowrap font-mono text-xs">{inr(t.itc_at_risk)}</span> },
    { key: 'risk', label: 'Risk', align: 'right', render: (t) => <RiskBadge risk={t.risk} /> },
  ]
  return (
    <>
      <Stagger className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} label="Taxpayers" value={s.taxpayers} format={num} sub={`${num(s.returns)} monthly returns`} spark={m} sparkKey="returns" sparkLabel="returns filed / month" live />
        <StatCard icon={FileText} label="Invoices" value={s.invoices} format={num} sub={`${num(s.flagged_invoices)} anomalous`} delta={lastDelta(m, 'invoices')} spark={m} sparkKey="invoices" sparkLabel="invoices / month" tone="cyan" />
        <StatCard icon={AlertOctagon} label="Flagged taxpayers" value={s.flagged} format={num} sub={`${pct(s.flagged / s.taxpayers, 1)} of the ecosystem`} spark={m} sparkKey="flagged_filers" sparkLabel="flagged filers / month" tone="alert" live />
        <StatCard icon={IndianRupee} label="ITC at risk (flagged)" value={s.itc_at_risk} format={inr} sub={`of ${inr(s.itc_claimed)} claimed`} delta={lastDelta(m, 'flagged_claimed')} spark={m} sparkKey="flagged_claimed" sparkLabel="ITC claimed by flagged / month" tone="warn" />
      </Stagger>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card title="Ecosystem pulse · monthly ITC" className="xl:col-span-2">
          {m ? <Pulse months={m} /> : <Skeleton className="h-[230px]" />}
        </Card>
        <Card title="Detection vs rule baseline"><Headline h={d.headline} /></Card>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card title="Highest-risk taxpayers" className="xl:col-span-2"
          action={<Link to="/app/taxpayers" className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-ok hover:underline">Full ranking <ArrowRight size={12} /></Link>}>
          <Table columns={columns} rows={d.top_taxpayers} rowKey={(t) => t.gstin} caption="Top eight taxpayers by risk"
            empty={<EmptyState title="No taxpayers ranked" body="Generate an ecosystem above to rank taxpayers." />}
            cards={(t) => (
              <div className="rounded-[6px] border border-line bg-panel-2 p-3">
                <div className="flex items-start justify-between gap-2"><TaxpayerLink gstin={t.gstin} name={t.legal_name} /><RiskBadge risk={t.risk} /></div>
                <div className="mt-2 flex flex-wrap items-center gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}<span className="ml-auto font-mono text-[11px] text-muted">{inr(t.itc_at_risk)}</span></div>
              </div>
            )} />
        </Card>
        <div className="space-y-5">
          <Card title="Flagged by pattern">
            <ul className="space-y-1">
              {patterns.map(([p, c]) => (
                <li key={p}>
                  <Link to={`/app/taxpayers?pattern=${p}`} className="group flex items-center gap-3 rounded-[4px] px-1.5 py-1.5 hover:bg-panel-2">
                    <span className="w-32 shrink-0"><PatternTag p={p} /></span>
                    <span className="h-1.5 flex-1 bg-line-strong/50"><span className="block h-full bg-ok/70 group-hover:bg-ok" style={{ width: `${(c / maxP) * 100}%` }} /></span>
                    <span className="w-8 text-right font-mono text-sm text-fg">{c}</span>
                  </Link>
                </li>
              ))}
            </ul>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <Link to="/app/graph" className="rounded-[6px] border border-info/30 bg-info/5 p-3 hover:border-info/60">
                <div className="font-mono text-2xl font-semibold text-info"><CountUp value={s.rings} /></div>
                <div className="font-mono text-[10px] uppercase tracking-wider text-muted">trade loops</div>
              </Link>
              <Link to="/app/graph" className="rounded-[6px] border border-alert/30 bg-alert/5 p-3 hover:border-alert/60">
                <div className="font-mono text-2xl font-semibold text-alert"><CountUp value={s.suspicious_clusters} /></div>
                <div className="font-mono text-[10px] uppercase tracking-wider text-muted">shell clusters</div>
              </Link>
            </div>
          </Card>
          <Card title="Risk distribution · sqrt scale"><Histogram hist={d.risk_histogram} /></Card>
        </div>
      </div>

      <Card title="Top invoice chains" action={<Link to="/app/graph" className="inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-ok hover:underline">All chains <ArrowRight size={12} /></Link>}>
        {d.top_chains.length ? (
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">{d.top_chains.map((c) => <ChainItem key={c.id} c={c} />)}</div>
        ) : <EmptyState icon={Network} title="No invoice chains" body="No circular or shell chains were found in this ecosystem." />}
      </Card>
    </>
  )
}

export default function Overview() {
  const { data, error, loading, reload } = useApi('/overview')
  const monthly = useApi('/overview/monthly')
  useEffect(() => {
    if (historyLogged) return
    historyLogged = true
    api.get('/pipeline/runs', { silent: true }).then((r) => {
      r.data.slice().reverse().forEach((x) => logEvent('history', `run #${x.id} · seed ${x.seed} · ${x.taxpayers} taxpayers · ${x.status}${x.flagged !== null && x.flagged !== undefined ? ` · ${x.flagged} flagged` : ''}`))
    }).catch(() => {})
  }, [])
  const refresh = () => { reload(); monthly.reload() }
  return (
    <div className="space-y-5">
      <PageHeader eyebrow="// control room" title="Overview"
        subtitle={data ? `Ecosystem ${data.run_key} · seed ${data.seed} · ${data.dataset} · analysed ${stamp(data.generated_at * 1000)}` : 'Current GST ecosystem, what was flagged and where to look first'} />
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-5">
        <div className="xl:col-span-3"><Generator onDone={refresh} /></div>
        <div className="xl:col-span-2"><ActivityLog height={238} /></div>
      </div>
      {error && <ErrorState error={error} onRetry={reload} title="Could not load the overview" />}
      {loading && !data && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-36" />)}</div>
          <Skeleton className="h-72" />
        </div>
      )}
      {data && <Dashboard d={data} monthly={monthly.data} />}
    </div>
  )
}
