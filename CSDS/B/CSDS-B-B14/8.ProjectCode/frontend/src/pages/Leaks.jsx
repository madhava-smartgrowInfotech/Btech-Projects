import { useCallback, useEffect, useState } from 'react'
import { Loader2, ShieldAlert, Wrench, Zap } from 'lucide-react'
import api, { errorText } from '../api'
import useApi from '../useApi'
import { useAuth } from '../auth.jsx'
import { Badge, ErrorBox, Loading, PageHeader, fmt, timeAgo } from '../components/ui.jsx'
import NetworkMap from '../components/NetworkMap.jsx'
import { BarChart, LineChart } from '../components/Charts.jsx'

const TYPE_TONE = { night_flow: 'amber', burst: 'rose', suspected_theft: 'violet', unusual_pattern: 'slate' }

function LeakPanel() {
  const { user } = useAuth()
  const net = useApi('/network')
  const pipes = useApi('/leaks/pipes')
  const events = useApi('/leaks/events')
  const [pipe, setPipe] = useState('P53')
  const [size, setSize] = useState(12)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const canInject = user?.role === 'engineer'
  const onPipeClick = useCallback((p) => setPipe(p), [])

  async function inject() {
    setBusy('inject')
    setError('')
    try {
      const r = await api.post('/leaks/inject', { pipe, leak_lps: size })
      setResult(r.data)
      net.reload()
      events.reload()
    } catch (e) {
      setError(errorText(e))
    } finally {
      setBusy('')
    }
  }

  async function repair() {
    setBusy('repair')
    setError('')
    try {
      await api.post('/leaks/clear')
      setResult(null)
      net.reload()
      events.reload()
    } catch (e) {
      setError(errorText(e))
    } finally {
      setBusy('')
    }
  }

  const suspects = result?.ranking || net.data?.suspects || []
  return (
    <div className="space-y-6">
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="card p-5 space-y-4 h-fit">
          <h2 className="font-semibold text-slate-800">Leak scenario on the twin</h2>
          <p className="text-xs text-slate-500">
            Choose a pipe (or click one on the map) and a leak size. The twin simulates what the 16 pressure loggers and 5 zone inlet meters would report in
            the 03:00 minimum-night-flow window; the detector then decides whether there is a leak and ranks the likely pipes.
          </p>
          <div>
            <label className="label">Pipe</label>
            <select className="input" value={pipe} onChange={(e) => setPipe(e.target.value)}>
              {pipes.data?.map((p) => (
                <option key={p.pipe} value={p.pipe}>{p.pipe} ({p.zone})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Leak size: {size} L/s</label>
            <input type="range" min="2" max="30" step="1" value={size} onChange={(e) => setSize(Number(e.target.value))} className="w-full" />
          </div>
          <ErrorBox error={error || pipes.error} />
          {!canInject && <div className="text-xs text-amber-700 bg-amber-50 rounded-lg p-2">Leak scenarios are run by the engineer role.</div>}
          <div className="flex gap-2">
            <button className="btn-danger flex-1" onClick={inject} disabled={!canInject || !!busy}>
              {busy === 'inject' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />} Inject leak
            </button>
            <button className="btn-secondary" onClick={repair} disabled={!canInject || !!busy} title="Repair all injected leaks">
              {busy === 'repair' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />} Repair all
            </button>
          </div>
          {result && (
            <div className={`rounded-lg p-3 ${result.detected ? 'bg-rose-50 border border-rose-200' : 'bg-emerald-50 border border-emerald-200'}`}>
              <div className="flex items-center gap-2 font-semibold text-slate-800">
                <ShieldAlert className={`w-4 h-4 ${result.detected ? 'text-rose-600' : 'text-emerald-600'}`} />
                {result.detected ? 'Leak detected - alert raised' : 'No leak detected'}
              </div>
              <div className="text-sm text-slate-600 mt-1">Leak probability {(result.leak_probability * 100).toFixed(1)}%</div>
              <div className="text-sm text-slate-600">
                Injected pipe {result.event.pipe} ranked <b>#{result.true_rank ?? '-'}</b> of {pipes.data?.length}
              </div>
            </div>
          )}
        </div>
        <div className="card p-4 lg:col-span-2">
          <ErrorBox error={net.error} onRetry={net.reload} />
          {net.data ? (
            <NetworkMap nodes={net.data.nodes} links={net.data.links} suspects={suspects} activeLeaks={net.data.active_leaks}
              onPipeClick={onPipeClick} selectedPipe={pipe} height={440} />
          ) : (
            !net.error && <Loading />
          )}
          <div className="text-xs text-slate-500 mt-2">Numbered pipes are the ranked leak suspects (1 = most likely). The selected pipe is drawn in black.</div>
        </div>
      </div>

      {result && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="card overflow-x-auto">
            <div className="p-4 pb-2 font-semibold text-slate-800">Likely leak locations</div>
            <table className="w-full">
              <thead><tr><th className="th">Rank</th><th className="th">Pipe</th><th className="th">Zone</th><th className="th">Match</th><th className="th">Est. size</th></tr></thead>
              <tbody>
                {result.ranking.map((r, i) => (
                  <tr key={r.pipe} className={r.pipe === result.event.pipe ? 'bg-emerald-50' : ''}>
                    <td className="td font-semibold">#{i + 1}</td>
                    <td className="td">{r.pipe} {r.pipe === result.event.pipe && <Badge tone="emerald">injected</Badge>}</td>
                    <td className="td">{r.zone}</td>
                    <td className="td">{(r.score * 100).toFixed(1)}%</td>
                    <td className="td">{r.estimated_lps} L/s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card p-4">
            <div className="font-semibold text-slate-800">Zone inlet residuals (observed - twin expectation)</div>
            <BarChart categories={Object.keys(result.zone_inflow_residual_lps)} yUnit="L/s" height={200}
              series={[{ name: 'Extra inflow (L/s)', color: '#e11d48', values: Object.values(result.zone_inflow_residual_lps).map((v) => Math.max(0, v)) }]} />
          </div>
        </div>
      )}

      <div className="card overflow-x-auto">
        <div className="p-4 pb-2 font-semibold text-slate-800">Leak scenarios run</div>
        <ErrorBox error={events.error} onRetry={events.reload} />
        {events.data?.length === 0 && <div className="px-4 pb-4 text-sm text-slate-500">No scenarios yet.</div>}
        {events.data?.length > 0 && (
          <table className="w-full">
            <thead><tr><th className="th">When</th><th className="th">Pipe</th><th className="th">Size</th><th className="th">Detected</th><th className="th">Top suspect</th><th className="th">Rank of true pipe</th><th className="th">State</th></tr></thead>
            <tbody>
              {events.data.map((e) => (
                <tr key={e.id}>
                  <td className="td text-xs text-slate-500">{timeAgo(e.created_at)}</td>
                  <td className="td">{e.pipe} ({e.zone})</td>
                  <td className="td">{e.leak_lps} L/s</td>
                  <td className="td"><Badge tone={e.detected ? 'rose' : 'slate'}>{e.detected ? `yes ${(e.probability * 100).toFixed(0)}%` : 'no'}</Badge></td>
                  <td className="td">{e.top_pipe}</td>
                  <td className="td">#{e.true_rank ?? '-'}</td>
                  <td className="td">{e.active ? <Badge tone="amber">active</Badge> : <Badge>repaired</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function MeterDetail({ id }) {
  const { data, loading, error, reload } = useApi(`/anomalies/meter/${id}`)
  if (loading) return <Loading />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  const hourly = data.hourly
  const labels = hourly.map((h) => h.ts.slice(5, 10) + (h.ts.endsWith('00:00') ? '' : ''))
  const days = data.daily.slice(-14)
  return (
    <div className="space-y-4">
      <div>
        <div className="text-sm font-medium text-slate-700 mb-1">Hourly readings - last 14 days (m3/h)</div>
        <LineChart labels={labels} height={200} yUnit="m3/h" series={[{ name: `Meter ${id}`, color: '#0284c7', values: hourly.map((h) => h.m3) }]} />
      </div>
      <div>
        <div className="text-sm font-medium text-slate-700 mb-1">Daily total and IsolationForest verdict</div>
        <BarChart categories={days.map((d) => d.date.slice(5))} yUnit="m3" height={180}
          series={[{ name: 'Daily total (red = anomalous)', color: '#0284c7', colors: days.map((d) => (d.anomaly ? '#e11d48' : '#0284c7')), values: days.map((d) => d.total) }]} />
      </div>
    </div>
  )
}

function AnomalyPanel() {
  const { data, loading, error, reload } = useApi('/anomalies')
  const [sel, setSel] = useState(null)
  useEffect(() => {
    if (data?.meters?.length && !sel) setSel((data.meters.find((m) => m.type === 'night_flow') || data.meters[0]).meter_id)
  }, [data, sel])
  if (loading) return <Loading text="Scoring customer meters..." />
  if (error) return <ErrorBox error={error} onRetry={reload} />
  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="card overflow-x-auto">
        <div className="p-4 pb-2">
          <div className="font-semibold text-slate-800">Flagged meters</div>
          <div className="text-xs text-slate-500">
            {data.summary.flagged} of {data.summary.meters} meters abnormal in the last 7 days (data to {data.summary.data_until}). Click a row for detail.
          </div>
        </div>
        <table className="w-full">
          <thead><tr><th className="th">Meter</th><th className="th">Zone</th><th className="th">Pattern</th><th className="th">Days</th><th className="th">Since</th><th className="th">Score</th></tr></thead>
          <tbody>
            {data.meters.map((m) => (
              <tr key={m.meter_id} onClick={() => setSel(m.meter_id)} className={`cursor-pointer hover:bg-slate-50 ${sel === m.meter_id ? 'bg-sky-50' : ''}`}>
                <td className="td font-medium">{m.meter_id}<div className="text-[11px] text-slate-400">{m.customer_type}</div></td>
                <td className="td">{m.zone}</td>
                <td className="td"><Badge tone={TYPE_TONE[m.type]}>{m.type.replace('_', ' ')}</Badge></td>
                <td className="td">{m.anomalous_days}</td>
                <td className="td text-xs">{m.since}</td>
                <td className="td">{m.score.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card p-4">
        {sel ? (
          <>
            {(() => {
              const m = data.meters.find((x) => x.meter_id === sel)
              return m ? (
                <div className="mb-3">
                  <div className="font-semibold text-slate-800">Meter {m.meter_id} - {m.type.replace('_', ' ')}</div>
                  <div className="text-sm text-slate-600">{m.description}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    Night flow {fmt(m.night_flow_m3h * 1000)} L/h (baseline {fmt(m.baseline_night_m3h * 1000)} L/h) - daily use {fmt(m.day_total_m3, 2)} m3 (baseline {fmt(m.baseline_total_m3, 2)} m3)
                  </div>
                </div>
              ) : null
            })()}
            <MeterDetail id={sel} />
          </>
        ) : (
          <div className="text-sm text-slate-500">Select a meter.</div>
        )}
      </div>
    </div>
  )
}

export default function Leaks() {
  const [tab, setTab] = useState('leaks')
  return (
    <div>
      <PageHeader title="Leaks and anomalies" subtitle="Model-based leak detection on the twin and IsolationForest on customer meters">
        <div className="flex rounded-lg border border-slate-300 overflow-hidden text-sm">
          {[['leaks', 'Leak detection'], ['meters', 'Abnormal consumption']].map(([t, l]) => (
            <button key={t} onClick={() => setTab(t)} className={`px-3 py-1.5 ${tab === t ? 'bg-sky-600 text-white' : 'bg-white text-slate-700'}`}>
              {l}
            </button>
          ))}
        </div>
      </PageHeader>
      {tab === 'leaks' ? <LeakPanel /> : <AnomalyPanel />}
    </div>
  )
}
