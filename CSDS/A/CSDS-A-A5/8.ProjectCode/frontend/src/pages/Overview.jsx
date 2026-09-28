import { AlertOctagon, FileText, IndianRupee, Loader2, Network, Play, Users } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage, useApi } from '../api'
import { Button, Card, ErrorBox, Loading, PageHeader, PatternTag, RiskBadge, Stat } from '../components/ui'
import { inr, num, pct, riskColor } from '../format'

function Generator({ onDone }) {
  const [seed, setSeed] = useState(42)
  const [n, setN] = useState(600)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const timer = useRef(null)
  const watching = useRef(false) // only refresh the dashboard after a run we saw in progress

  const poll = () => {
    api.get('/pipeline/status')
      .then(({ data }) => {
        setStatus(data)
        if (data.running) {
          watching.current = true
          timer.current = setTimeout(poll, 1000)
        } else if (watching.current) {
          watching.current = false
          if (data.stage === 'failed') setError(data.error || 'Generation failed')
          else onDone()
        }
      })
      .catch((e) => setError(errorMessage(e)))
  }
  useEffect(() => {
    poll()
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function start(e) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/pipeline/run', { seed: Number(seed), taxpayers: Number(n) })
      poll()
    } catch (err) {
      setError(errorMessage(err))
    }
  }
  const running = status?.running
  return (
    <Card title="Generate GST ecosystem">
      <form onSubmit={start} className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="text-slate-600">Seed</span>
          <input type="number" min="0" value={seed} onChange={(e) => setSeed(e.target.value)} disabled={running}
            className="mt-1 block w-28 rounded-lg border border-slate-300 px-2.5 py-1.5" />
        </label>
        <label className="text-sm">
          <span className="text-slate-600">Taxpayers</span>
          <input type="number" min="150" max="1500" step="50" value={n} onChange={(e) => setN(e.target.value)} disabled={running}
            className="mt-1 block w-28 rounded-lg border border-slate-300 px-2.5 py-1.5" />
        </label>
        <Button disabled={running}>
          {running ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          {running ? 'Running…' : 'Generate & analyse'}
        </Button>
        <p className="text-xs text-slate-500 basis-full sm:basis-auto sm:flex-1">
          Creates taxpayers, invoices and returns with injected fraud, retrains the JEPA encoder on them and re-runs the whole analysis (about 20-40 s).
        </p>
      </form>
      {running && (
        <div className="mt-4">
          <div className="flex justify-between text-xs text-slate-600 mb-1"><span>{status.message}</span><span>{status.progress}%</span></div>
          <div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-indigo-600 transition-all" style={{ width: `${status.progress}%` }} /></div>
        </div>
      )}
      {status?.current && !running && (
        <p className="mt-3 text-xs text-slate-500">
          Current ecosystem: seed {status.current.seed}, {status.current.taxpayers} taxpayers ({status.current.dataset}),
          analysed {new Date(status.current.generated_at * 1000).toLocaleString()}.
        </p>
      )}
      <div className="mt-3"><ErrorBox error={error} /></div>
    </Card>
  )
}

export default function Overview() {
  const { data, error, loading, reload } = useApi('/overview')
  return (
    <div className="space-y-5">
      <PageHeader title="Overview" subtitle="Current GST ecosystem, what was flagged and where to look first" />
      <Generator onDone={reload} />
      {loading && !data && <Loading />}
      <ErrorBox error={error} onRetry={reload} />
      {data && <Dashboard d={data} />}
    </div>
  )
}

function Dashboard({ d }) {
  const s = d.stats
  const maxH = Math.max(...d.risk_histogram)
  return (
    <>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat icon={Users} label="Taxpayers" value={num(s.taxpayers)} sub={`${num(s.returns)} monthly returns`} />
        <Stat icon={FileText} label="Invoices" value={num(s.invoices)} sub={`${num(s.flagged_invoices)} anomalous`} tone="indigo" />
        <Stat icon={AlertOctagon} label="Flagged taxpayers" value={num(s.flagged)} sub={`${pct(s.flagged / s.taxpayers, 1)} of the ecosystem`} tone="red" />
        <Stat icon={IndianRupee} label="ITC at risk (flagged)" value={inr(s.itc_at_risk)} sub={`of ${inr(s.itc_claimed)} claimed`} tone="amber" />
      </div>
      <div className="grid lg:grid-cols-3 gap-5">
        <Card title="Highest-risk taxpayers" className="lg:col-span-2"
          action={<Link to="/app/taxpayers" className="text-xs text-indigo-600 hover:underline">Full ranking</Link>}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-slate-500"><th className="pb-2">#</th><th className="pb-2">Taxpayer</th><th className="pb-2">Patterns</th><th className="pb-2 text-right">ITC at risk</th><th className="pb-2 text-right">Risk</th></tr></thead>
              <tbody>
                {d.top_taxpayers.map((t) => (
                  <tr key={t.gstin} className="border-t border-slate-100">
                    <td className="py-2 text-slate-400">{t.rank}</td>
                    <td className="py-2"><Link to={`/app/taxpayers/${t.gstin}`} className="font-medium text-slate-800 hover:text-indigo-600">{t.legal_name}</Link><div className="text-xs text-slate-400 font-mono">{t.gstin}</div></td>
                    <td className="py-2"><div className="flex flex-wrap gap-1">{t.patterns.map((p) => <PatternTag key={p} p={p} />)}</div></td>
                    <td className="py-2 text-right">{inr(t.itc_at_risk)}</td>
                    <td className="py-2 text-right"><RiskBadge risk={t.risk} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <div className="space-y-5">
          <Card title="Flagged by pattern">
            <div className="space-y-2">
              {Object.entries(s.pattern_counts).sort((a, b) => b[1] - a[1]).map(([p, c]) => (
                <Link key={p} to={`/app/taxpayers?pattern=${p}`} className="flex items-center justify-between hover:bg-slate-50 rounded px-1">
                  <PatternTag p={p} /><span className="font-semibold text-slate-800">{c}</span>
                </Link>
              ))}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-center text-xs">
              <Link to="/app/graph" className="rounded-lg bg-purple-50 p-2 hover:bg-purple-100"><div className="text-lg font-semibold text-purple-700">{s.rings}</div>trade loops</Link>
              <Link to="/app/graph" className="rounded-lg bg-red-50 p-2 hover:bg-red-100"><div className="text-lg font-semibold text-red-700">{s.suspicious_clusters}</div>shell clusters</Link>
            </div>
          </Card>
          <Card title="Risk distribution">
            <div className="flex items-end gap-1 h-24">
              {d.risk_histogram.map((h, i) => (
                <div key={i} className="flex-1 rounded-t" title={`${(i / 10).toFixed(1)}-${((i + 1) / 10).toFixed(1)}: ${h}`}
                  style={{ height: `${Math.max(3, (Math.log1p(h) / Math.log1p(maxH)) * 100)}%`, background: riskColor(i / 10 + 0.05) }} />
              ))}
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-1"><span>0</span><span>risk (log count)</span><span>1</span></div>
          </Card>
        </div>
      </div>
      <div className="grid lg:grid-cols-3 gap-5">
        <Card title="Top invoice chains" className="lg:col-span-2" action={<Link to="/app/graph" className="text-xs text-indigo-600 hover:underline">All chains</Link>}>
          <div className="space-y-2">
            {d.top_chains.map((c) => (
              <Link key={c.id} to={`/app/chains/${c.id}`} className="block rounded-lg border border-slate-200 p-3 hover:border-indigo-300">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2"><Network size={15} className="text-slate-400" /><span className="font-medium text-sm">{c.id}</span>
                    <PatternTag p={c.type === 'circular_trading' ? 'circular_trading' : 'shell_entity'} /></div>
                  <RiskBadge risk={c.score} />
                </div>
                <div className="mt-1 text-xs text-slate-500">{c.summary} · {inr(c.value)} · ITC {inr(c.itc)}</div>
                <div className="mt-1 text-xs text-slate-600 truncate">{c.path.map((p) => p.legal_name).join(' → ')}</div>
              </Link>
            ))}
          </div>
        </Card>
        <Card title="Detection vs rule baseline">
          <div className="space-y-3 text-sm">
            <div>
              <div className="text-xs text-slate-500">Precision@{d.headline.k} (top {d.headline.k} ranked)</div>
              <div className="flex items-baseline gap-3"><span className="text-2xl font-semibold text-indigo-700">{pct(d.headline.model_precision_at_k)}</span><span className="text-slate-500">rules {pct(d.headline.baseline_precision_at_k)}</span></div>
            </div>
            <div>
              <div className="text-xs text-slate-500">F1 at the flag threshold</div>
              <div className="flex items-baseline gap-3"><span className="text-2xl font-semibold text-indigo-700">{d.headline.model_f1.toFixed(2)}</span><span className="text-slate-500">rules {d.headline.baseline_f1.toFixed(2)}</span></div>
            </div>
            <p className="text-xs text-slate-400">Measured against the fraud labels injected by the generator (sample data).</p>
            <Link to="/app/performance" className="text-xs text-indigo-600 hover:underline">Full evaluation →</Link>
          </div>
        </Card>
      </div>
    </>
  )
}
