import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Activity, Building2, CalendarClock, Clock, GitBranch, Radio, Siren, Users } from 'lucide-react'
import api, { errMsg, todayStr } from '../api'
import MapView from '../components/MapView'
import useQueueSocket from '../components/useQueueSocket'
import { ErrorBox, SEVERITY_COLOR, SeverityBar, Spinner, Stat } from '../components/ui'

const loadColor = (p) => (p >= 90 ? '#dc2626' : p >= 70 ? '#f97316' : p >= 40 ? '#f59e0b' : '#10b981')

export default function Dashboard() {
  const [date, setDate] = useState(todayStr())
  const [d, setD] = useState(null)
  const [error, setError] = useState('')
  const timer = useRef(null)

  const load = useCallback(() => {
    api
      .get('/dashboard', { params: { date } })
      .then((r) => {
        setD(r.data)
        setError('')
      })
      .catch((e) => setError(errMsg(e)))
  }, [date])
  useEffect(load, [load])
  // live: refresh (debounced) whenever any hospital queue changes
  const live = useQueueSocket(0, () => {
    clearTimeout(timer.current)
    timer.current = setTimeout(load, 800)
  })

  const markers = useMemo(
    () =>
      (d?.hospitals || []).map((h) => ({
        id: h.id,
        lat: h.lat,
        lon: h.lon,
        color: loadColor(h.load_pct),
        radius: 6 + Math.min(10, h.booked / 20),
        label: `${h.name}: ${h.load_pct}% load, ${h.waiting} waiting`,
      })),
    [d],
  )

  if (!d) return error ? <ErrorBox error={error} onRetry={load} /> : <Spinner />
  const t = d.totals
  const maxLoad = Math.max(100, ...d.hospitals.map((h) => h.load_pct))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-bold flex-1">District dashboard - Hyderabad</h1>
        <span className={`inline-flex items-center gap-1 text-xs ${live ? 'text-emerald-600' : 'text-slate-400'}`}>
          <Radio className="h-3.5 w-3.5" /> {live ? 'Live' : 'Offline'}
        </span>
        <input type="date" className="input !w-auto" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>
      <ErrorBox error={error} onRetry={load} />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Stat label="Hospitals" value={t.hospitals} icon={Building2} sub={`${t.capacity} OP slots/day`} />
        <Stat label="Bookings" value={t.bookings} icon={Users} sub={`${Math.round((100 * t.bookings) / Math.max(t.capacity, 1))}% of capacity`} />
        <Stat label="Waiting now" value={t.waiting} icon={Activity} sub={`${t.done} seen, ${t.no_show} no-show`} />
        <Stat label="Avg wait" value={`${t.avg_wait_min} min`} icon={Clock} sub="across hospitals with a queue" />
        <Stat label="Emergencies" value={t.emergencies} icon={Siren} tone="text-red-600" />
        <Stat label="Moved to later day" value={t.moved_next_day} icon={CalendarClock} sub="requested this date, day was full" />
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card p-4">
          <div className="text-sm font-semibold mb-2">Load across hospitals</div>
          <MapView markers={markers} height={380} />
          <div className="flex gap-3 text-xs text-slate-500 mt-2">
            {[['< 40%', 0], ['40-70%', 50], ['70-90%', 80], ['90%+', 95]].map(([l, p]) => (
              <span key={l} className="flex items-center gap-1">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: loadColor(p) }} /> {l}
              </span>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <div className="card p-4">
            <div className="text-sm font-semibold">Severity mix</div>
            <SeverityBar mix={d.severity} height="h-4" />
            {['critical', 'severe', 'moderate', 'mild'].map((l) => (
              <div key={l} className="flex items-center gap-2 text-sm py-0.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: SEVERITY_COLOR[l] }} />
                <span className="capitalize flex-1">{l}</span>
                <b>{d.severity[l]}</b>
              </div>
            ))}
          </div>
          <div className="card p-4">
            <div className="text-sm font-semibold flex items-center gap-2">
              <GitBranch className="h-4 w-4" /> Referrals
            </div>
            {Object.keys(d.referrals).length === 0 && <div className="text-sm text-slate-400 mt-1">None yet</div>}
            {Object.entries(d.referrals).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm py-0.5 capitalize">
                <span>{k.replace('_', ' ')}</span>
                <b>{v}</b>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 text-sm font-semibold">Hospitals by load</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
              <tr>
                <th className="px-3 py-2 text-left">Hospital</th>
                <th className="px-3 py-2 text-left w-1/4">Load</th>
                <th className="px-3 py-2 text-right">Booked</th>
                <th className="px-3 py-2 text-right">Waiting</th>
                <th className="px-3 py-2 text-right">Avg / max wait</th>
                <th className="px-3 py-2 text-right">Emerg.</th>
                <th className="px-3 py-2 text-left w-32 hidden md:table-cell">Severity</th>
              </tr>
            </thead>
            <tbody>
              {d.hospitals.map((h) => (
                <tr key={h.id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-medium">{h.name}</td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded bg-slate-100">
                        <div className="h-2 rounded" style={{ width: `${(100 * h.load_pct) / maxLoad}%`, background: loadColor(h.load_pct) }} />
                      </div>
                      <span className="text-xs w-12 text-right">{h.load_pct}%</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-right">
                    {h.booked}/{h.op_limit}
                  </td>
                  <td className="px-3 py-2 text-right">{h.waiting}</td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    {h.avg_wait_min} / {h.max_wait_min} min
                  </td>
                  <td className="px-3 py-2 text-right">
                    {h.emergencies}/{h.emergency_quota}
                  </td>
                  <td className="px-3 py-2 hidden md:table-cell">
                    <SeverityBar mix={h.severity} height="h-2" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-xs text-slate-400">Queues include clearly labelled sample patients generated at start-up so the network shows realistic load.</p>
    </div>
  )
}
