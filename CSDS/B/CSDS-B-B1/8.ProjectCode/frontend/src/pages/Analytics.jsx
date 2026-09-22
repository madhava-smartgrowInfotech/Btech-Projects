import { Brain, Flame, Map as MapIcon, Pencil, RefreshCw, Save, Table2, Timer, TrendingUp, X } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { CircleMarker, MapContainer, Tooltip } from 'react-leaflet'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Meter, Sparkline } from '../components/Charts.jsx'
import { BaseTiles, CITY_CENTER } from '../components/MapPicker.jsx'
import { CHART, days, ErrorBox, Loading, pct, PRIORITY_STYLE, Spinner, Stat } from '../components/ui.jsx'
import { RetrainPanel } from './ComplaintDetail.jsx'

function Card({ title, icon: Icon, right, children, className = '' }) {
  return (
    <section className={`card p-5 ${className}`}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Icon className="h-4 w-4 text-brand-700" /> {title}
        </h2>
        {right}
      </div>
      {children}
    </section>
  )
}

function HotspotMap({ data, showPoints }) {
  const max = Math.max(...data.wards.map((w) => w.total), 1)
  const step = (v) => CHART.seq[Math.min(CHART.seq.length - 1, Math.floor((v / max) * (CHART.seq.length - 1) + 0.0001))]
  return (
    <div className="h-[420px] overflow-hidden rounded-lg border border-slate-200">
      <MapContainer center={CITY_CENTER} zoom={11} className="h-full w-full" scrollWheelZoom={false}>
        <BaseTiles />
        {!showPoints &&
          data.wards.map((w) => (
            <CircleMarker
              key={w.ward}
              center={[w.lat, w.lng]}
              radius={6 + 22 * Math.sqrt(w.total / max)}
              pathOptions={{ color: '#fff', weight: 2, fillColor: step(w.total), fillOpacity: 0.85 }}
            >
              <Tooltip>
                <b>{w.ward}</b>
                <br />
                {w.total} complaints · {w.open} open · {w.critical_or_high} high/critical
                <br />
                Most common: {w.top_category} ({w.top_count})
              </Tooltip>
            </CircleMarker>
          ))}
        {showPoints &&
          data.points.map((p) => (
            <CircleMarker key={p.id} center={[p.lat, p.lng]} radius={5} pathOptions={{ color: '#fff', weight: 1.5, fillColor: PRIORITY_STYLE[p.priority]?.color, fillOpacity: 1 }}>
              <Tooltip>
                <b>{p.tracking_id}</b> · {p.priority}
                <br />
                {p.category} · {p.status}
              </Tooltip>
            </CircleMarker>
          ))}
      </MapContainer>
    </div>
  )
}

function SlaTable({ rows, isAdmin, depts, onSaved }) {
  const [edit, setEdit] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function save(name) {
    const d = depts.find((x) => x.name === name)
    setBusy(true)
    setError('')
    try {
      await api.put(`/departments/${d.id}`, { sla_days: Number(edit.value) })
      setEdit(null)
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="py-2 font-medium">Department</th>
              <th className="py-2 font-medium">SLA</th>
              <th className="w-56 py-2 font-medium">Resolved within SLA</th>
              <th className="py-2 text-right font-medium">Resolved</th>
              <th className="py-2 text-right font-medium">Avg days</th>
              <th className="py-2 text-right font-medium">Open</th>
              <th className="py-2 text-right font-medium">Open past SLA</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {rows.map((r) => (
              <tr key={r.department} className="border-t border-slate-100">
                <td className="py-2 font-medium text-slate-800">{r.department}</td>
                <td className="py-2">
                  {edit?.name === r.department ? (
                    <span className="flex items-center gap-1">
                      <input type="number" min="1" max="90" className="input w-16 px-2 py-1" value={edit.value} onChange={(e) => setEdit({ ...edit, value: e.target.value })} aria-label="SLA days" />
                      <button className="btn-primary px-2 py-1" onClick={() => save(r.department)} disabled={busy} title="Save">
                        {busy ? <Spinner className="h-3.5 w-3.5" /> : <Save className="h-3.5 w-3.5" />}
                      </button>
                      <button className="btn-secondary px-2 py-1" onClick={() => setEdit(null)} title="Cancel">
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5">
                      {r.sla_days} d
                      {isAdmin && (
                        <button className="text-slate-400 hover:text-slate-700" onClick={() => setEdit({ name: r.department, value: r.sla_days })} title="Edit SLA">
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </span>
                  )}
                </td>
                <td className="py-2">
                  <Meter value={r.compliance} label={`${r.within_sla} of ${r.resolved} resolved within ${r.sla_days} days`} />
                </td>
                <td className="py-2 text-right">{r.resolved}</td>
                <td className="py-2 text-right">{r.avg_days ?? '-'}</td>
                <td className="py-2 text-right">{r.open}</td>
                <td className="py-2 text-right font-semibold text-slate-900">{r.open_breached}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ErrorBox message={error} />
      {!isAdmin && <p className="mt-2 text-xs text-slate-500">Administrators can edit SLA days.</p>}
    </div>
  )
}

function Trends({ data }) {
  const [table, setTable] = useState(false)
  const top = data.series.slice(0, 8)
  const rest = data.series.slice(8)
  const other = rest.length ? [{ category: `Other (${rest.length} categories)`, counts: data.weeks.map((_, i) => rest.reduce((a, s) => a + s.counts[i], 0)) }] : []
  const all = [...top, ...other]
  return (
    <Card
      title="Category trends (complaints per 7 days, last 12 weeks)"
      icon={TrendingUp}
      right={
        <button className="btn-secondary px-2.5 py-1 text-xs" onClick={() => setTable(!table)}>
          <Table2 className="h-3.5 w-3.5" /> {table ? 'Charts' : 'Table'}
        </button>
      }
    >
      {table ? (
        <div className="overflow-x-auto">
          <table className="w-full text-xs tabular-nums">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="py-1 pr-3 font-medium">Category</th>
                {data.weeks.map((w) => (
                  <th key={w} className="py-1 pr-2 text-right font-medium">
                    {new Date(w).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.series.map((s) => (
                <tr key={s.category} className="border-t border-slate-100">
                  <td className="whitespace-nowrap py-1 pr-3 text-slate-700">{s.category}</td>
                  {s.counts.map((c, i) => (
                    <td key={i} className="py-1 pr-2 text-right">
                      {c}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {all.map((s) => (
            <Sparkline key={s.category} title={s.category} weeks={data.weeks} counts={s.counts} />
          ))}
        </div>
      )}
    </Card>
  )
}

function ModelCard({ m }) {
  if (!m) return null
  const rows = [
    ['Category', m.category],
    ['Department', m.department],
    ['Priority', m.priority],
  ]
  const r = m.resolution
  return (
    <Card title={`Model performance on held-out data (v${m.version})`} icon={Brain}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-sm tabular-nums">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="py-1 font-medium">Task</th>
              <th className="py-1 text-right font-medium">Accuracy</th>
              <th className="py-1 text-right font-medium">Macro-F1</th>
              <th className="py-1 text-right font-medium">English</th>
              <th className="py-1 text-right font-medium">Hindi</th>
              <th className="py-1 text-right font-medium">Hinglish</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k} className="border-t border-slate-100">
                <td className="py-1.5 text-slate-800">{k}</td>
                <td className="py-1.5 text-right font-semibold">{pct(v.test.accuracy)}</td>
                <td className="py-1.5 text-right">{v.test.macro_f1.toFixed(3)}</td>
                <td className="py-1.5 text-right">{pct(v.by_language.English)}</td>
                <td className="py-1.5 text-right">{pct(v.by_language.Hindi)}</td>
                <td className="py-1.5 text-right">{pct(v.by_language.Hinglish)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {r && (
        <p className="mt-3 text-xs leading-relaxed text-slate-600">
          <b className="text-slate-800">Resolution time</b> (NYC 311, {r.rows_test.toLocaleString()} held-out requests): typical error {r.median_abs_error_days} days vs{' '}
          {r.baseline_category_median_median_abs_error_days ?? '-'} for a per-category median; mean error {r.mae_days} vs {r.baseline_category_median_mae_days} days; SLA-breach flag correct{' '}
          {pct(r.sla_breach_flag_accuracy)}.
        </p>
      )}
    </Card>
  )
}

export default function Analytics() {
  const { user } = useAuth()
  const [win, setWin] = useState(30)
  const [category, setCategory] = useState('')
  const [points, setPoints] = useState(false)
  const [state, setState] = useState({})
  const [meta, setMeta] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setError('')
      const [summary, hotspots, sla, trends, model] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/analytics/hotspots', { params: { days: win, category } }),
        api.get('/analytics/sla'),
        api.get('/analytics/trends', { params: { weeks: 12 } }),
        api.get('/model/metrics'),
      ])
      setState({ summary: summary.data, hotspots: hotspots.data, sla: sla.data, trends: trends.data, model: model.data })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [win, category])

  useEffect(() => {
    load()
    const t = setInterval(load, 20000) // live dashboard
    return () => clearInterval(t)
  }, [load])
  const loadMeta = useCallback(() => api.get('/meta').then((r) => setMeta(r.data)).catch(() => {}), [])
  useEffect(() => {
    loadMeta()
  }, [loadMeta])

  const { summary: s, hotspots, sla, trends, model } = state
  if (!s && error) return <ErrorBox message={error} onRetry={load} />
  if (!s) return <Loading label="Loading analytics..." />
  const acc = s.ai_acceptance.department

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Hotspots & analytics</h1>
          <p className="mt-1 text-sm text-slate-600">Live from every complaint in the system · refreshes every 20 seconds · updated {new Date(s.updated_at).toLocaleTimeString()}</p>
        </div>
        <button className="btn-secondary" onClick={load} disabled={loading}>
          {loading ? <Spinner /> : <RefreshCw className="h-4 w-4" />} Refresh
        </button>
      </div>
      <ErrorBox message={error} onRetry={load} />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
        <Stat label="Open complaints" value={s.open.toLocaleString()} sub={`${s.filed_last_24h} filed in 24 h`} />
        <Link to="/queue" className="block">
          <Stat label="Awaiting review" value={s.awaiting_review} sub="Open the triage queue" />
        </Link>
        <Stat label="Resolved within SLA" value={pct(s.sla_compliance)} sub="All resolved complaints" />
        <Stat label="Open past SLA" value={s.open_sla_breached} sub="Need escalation" />
        <Stat label="Avg resolution" value={days(s.avg_resolution_days)} sub={`${s.resolved_last_30d} resolved in 30 d`} />
        <Stat label="AI department accepted" value={pct(acc.rate)} sub={`${acc.accepted} of ${acc.reviewed} officer reviews`} />
        <Stat label="Time estimate error" value={days(s.time_estimate_mae_days)} sub="Mean, on resolved complaints" />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <Card
          title="Hotspot map"
          icon={MapIcon}
          right={
            <div className="flex flex-wrap gap-2">
              <select className="input w-auto py-1 text-xs" value={win} onChange={(e) => setWin(Number(e.target.value))} aria-label="Time window">
                {[7, 30, 90].map((d) => (
                  <option key={d} value={d}>
                    Last {d} days
                  </option>
                ))}
              </select>
              <select className="input w-auto py-1 text-xs" value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
                <option value="">All categories</option>
                {meta?.categories.map((c) => (
                  <option key={c.name}>{c.name}</option>
                ))}
              </select>
              <div className="flex rounded-lg border border-slate-300 p-0.5 text-xs">
                {[
                  [false, 'Wards'],
                  [true, 'Complaints'],
                ].map(([v, l]) => (
                  <button key={l} onClick={() => setPoints(v)} className={`rounded-md px-2 py-0.5 ${points === v ? 'bg-slate-800 text-white' : 'text-slate-600'}`}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
          }
        >
          {hotspots && <HotspotMap data={hotspots} showPoints={points} />}
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-600">
            {points ? (
              Object.entries(PRIORITY_STYLE).map(([p, st]) => (
                <span key={p} className="inline-flex items-center gap-1">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: st.color }} /> {p}
                </span>
              ))
            ) : (
              <span className="inline-flex items-center gap-1.5">
                Fewer
                {CHART.seq.map((c) => (
                  <span key={c} className="h-2.5 w-4" style={{ background: c }} />
                ))}
                More complaints (circle size and shade)
              </span>
            )}
            <span className="ml-auto text-slate-400">{hotspots?.points.length} complaints in window</span>
          </div>
        </Card>

        <Card title="Recurring issues" icon={Flame}>
          <p className="-mt-1 mb-2 text-xs text-slate-500">Same category reported 3+ times in one ward in the last {win} days.</p>
          {hotspots?.recurring.length ? (
            <table className="w-full text-sm tabular-nums">
              <thead>
                <tr className="text-left text-xs text-slate-500">
                  <th className="py-1 font-medium">Ward</th>
                  <th className="py-1 font-medium">Issue</th>
                  <th className="py-1 text-right font-medium">Reports</th>
                  <th className="py-1 text-right font-medium">Open</th>
                </tr>
              </thead>
              <tbody>
                {hotspots.recurring.slice(0, 12).map((r) => (
                  <tr key={r.ward + r.category} className="border-t border-slate-100">
                    <td className="py-1.5 text-slate-800">{r.ward}</td>
                    <td className="py-1.5 text-slate-600">{r.category}</td>
                    <td className="py-1.5 text-right font-semibold">{r.count}</td>
                    <td className="py-1.5 text-right">{r.open}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="py-6 text-center text-sm text-slate-500">No recurring issues in this window.</p>
          )}
        </Card>
      </div>

      <Card title="SLA compliance by department" icon={Timer}>
        {sla && <SlaTable rows={sla} isAdmin={user.role === 'admin'} depts={meta?.departments || []} onSaved={() => { load(); loadMeta() }} />}
      </Card>

      {trends && <Trends data={trends} />}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <ModelCard m={model?.current} />
        <RetrainPanel />
      </div>
    </div>
  )
}
