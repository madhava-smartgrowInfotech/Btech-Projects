import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import api, { ACTIVITY_COLORS, errMsg, fmtDuration, label } from '../api.js'
import Timeline from '../components/Timeline.jsx'
import { ErrorBox, PageTitle, Spinner, Stat, StatusBadge } from '../components/ui.jsx'

const today = () => new Date().toLocaleDateString('en-CA')

export default function Report() {
  const [day, setDay] = useState(today())
  const [data, setData] = useState(null)
  const [days, setDays] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try {
      const [r, d] = await Promise.all([api.get('/reports/daily', { params: { day } }), api.get('/reports/days')])
      setData(r.data); setDays(d.data)
    } catch (e) { setError(errMsg(e)) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [day])

  const from = new Date(`${day}T00:00:00`)
  const to = new Date(from.getTime() + 24 * 3600 * 1000)
  const totals = data ? Object.entries(data.totals) : []
  const max = Math.max(1, ...totals.map(([, v]) => v))

  return (
    <div>
      <PageTitle title="Daily report" subtitle="Time spent per activity and long-inactivity warnings">
        <input type="date" className="input w-44" value={day} max={today()} onChange={(e) => setDay(e.target.value)} />
        <button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /></button>
      </PageTitle>
      {days.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4 text-xs">
          <span className="text-slate-500 mr-1">Days with data:</span>
          {days.slice(0, 10).map((d) => (
            <button key={d} onClick={() => setDay(d)} className={`rounded-full px-2 py-0.5 border ${d === day ? 'bg-teal-600 text-white border-teal-600' : 'border-slate-300 text-slate-600'}`}>{d}</button>
          ))}
        </div>
      )}
      <ErrorBox error={error} onRetry={load} />
      {!data ? (loading ? <Spinner /> : null) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Monitored" value={fmtDuration(data.monitored_seconds)} />
            <Stat label="Person in view" value={fmtDuration(data.present_seconds)} />
            <Stat label="Active (walk, drink, pick up)" value={fmtDuration(data.active_seconds)} />
            <Stat label="Inactivity warnings" value={data.warnings.length} hint={`over ${data.inactivity_threshold_minutes} min without moving`} />
          </div>
          {data.monitored_seconds === 0 ? (
            <div className="card p-10 text-center text-slate-500">No monitoring data for this day.</div>
          ) : (
            <>
              <div className="card p-5">
                <h2 className="font-semibold text-slate-900 mb-3">Timeline</h2>
                <Timeline segments={data.timeline} from={from} to={to} ticks={8} />
              </div>
              <div className="grid lg:grid-cols-2 gap-4">
                <div className="card p-5">
                  <h2 className="font-semibold text-slate-900 mb-3">Time per activity</h2>
                  <div className="space-y-2">
                    {totals.map(([k, v]) => (
                      <div key={k} className="flex items-center gap-3 text-sm">
                        <span className="w-24 capitalize text-slate-600">{label(k)}</span>
                        <div className="flex-1 h-4 rounded bg-slate-100"><div className="h-4 rounded" style={{ width: `${(v / max) * 100}%`, background: ACTIVITY_COLORS[k] || '#94a3b8' }} /></div>
                        <span className="w-20 text-right tabular-nums">{fmtDuration(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="card p-5">
                  <h2 className="font-semibold text-slate-900 mb-3">Warnings and falls</h2>
                  {data.warnings.length === 0 && data.falls.length === 0 && <p className="text-sm text-slate-500">No warnings - no long inactivity and no falls.</p>}
                  <ul className="space-y-2 text-sm">
                    {data.warnings.map((w) => (
                      <li key={w.id} className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-amber-900">
                        <AlertTriangle className="w-4 h-4 mt-0.5" />
                        <span>Long inactivity: no movement for <b>{w.minutes} min</b>{w.activity && ` while ${label(w.activity)}`}, from {new Date(w.started_at).toLocaleTimeString()}{!w.ended_at && ' (ongoing)'}</span>
                      </li>
                    ))}
                    {data.falls.map((f) => (
                      <li key={f.id} className="flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-red-900">
                        <AlertTriangle className="w-4 h-4" /> Fall at {new Date(f.detected_at).toLocaleTimeString()} <StatusBadge status={f.status} />
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
