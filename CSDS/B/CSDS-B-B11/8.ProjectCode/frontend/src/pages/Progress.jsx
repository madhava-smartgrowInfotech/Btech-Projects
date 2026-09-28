import { useEffect, useState } from 'react'
import { Calculator, Loader2, Plus, Trash2 } from 'lucide-react'
import api, { errorMessage, today } from '../api'
import { BarChart, LineChart } from '../components/Charts'
import { ErrorBox, Spinner } from '../components/ui'

export default function Progress() {
  const [data, setData] = useState(null)
  const [days, setDays] = useState(30)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ date: today(), weight_kg: '' })
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')

  const load = () => {
    setError('')
    api.get('/progress', { params: { days } }).then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)))
  }
  useEffect(load, [days])

  const addWeight = async (e) => {
    e.preventDefault()
    setBusy(true); setError(''); setNotice('')
    try {
      const { data: r } = await api.post('/weights', { date: form.date, weight_kg: Number(form.weight_kg) })
      if (r.recalculated) setNotice(`Weekly recalculation: target ${r.recalculated.old_target_kcal} -> ${r.recalculated.new_target_kcal} kcal/day. ${r.recalculated.reason}`)
      setForm({ ...form, weight_kg: '' })
      load()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }
  const recalc = async () => {
    setBusy(true); setError(''); setNotice('')
    try {
      const { data: r } = await api.post('/progress/recalculate')
      setNotice(`Target ${r.old_target_kcal} -> ${r.new_target_kcal} kcal/day. ${r.reason}`)
      load()
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) }
  }
  const del = async (id) => {
    try { await api.delete(`/weights/${id}`); load() } catch (e) { setError(errorMessage(e)) }
  }

  if (!data && !error) return <Spinner />

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">Progress</h1>
        <select className="input !w-auto" value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={14}>Last 14 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option>
        </select>
      </div>
      <ErrorBox message={error} onRetry={load} />
      {notice && <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-800">{notice}</div>}
      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Tile k="Current target" v={`${data.current_target} kcal`} />
            <Tile k="Adherence score (7 days)" v={`${data.adherence.score}/100`} sub={`${data.adherence.days_logged} of ${data.adherence.window_days} days logged`} />
            <Tile k="Weight trend (2 weeks)" v={data.trend_kg_week == null ? '-' : `${data.trend_kg_week > 0 ? '+' : ''}${data.trend_kg_week} kg/wk`} sub={`Goal ${data.goal_rate_kg_week > 0 ? '+' : ''}${data.goal_rate_kg_week} kg/wk`} />
            <Tile k="Latest weight" v={data.weights.length ? `${data.weights[data.weights.length - 1].weight_kg} kg` : '-'} />
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <div className="card p-5 lg:col-span-2">
              <h2 className="font-semibold text-slate-700 mb-2">Weight</h2>
              <LineChart points={data.weights.map((w) => ({ x: w.date, y: w.weight_kg }))} />
            </div>
            <div className="card p-5">
              <h2 className="font-semibold text-slate-700 mb-3">Log weight</h2>
              <form onSubmit={addWeight} className="space-y-3">
                <div><label className="label">Date</label><input type="date" className="input" max={today()} value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required /></div>
                <div><label className="label">Weight (kg)</label><input type="number" step="0.1" min="30" max="250" className="input" value={form.weight_kg} onChange={(e) => setForm({ ...form, weight_kg: e.target.value })} required /></div>
                <button className="btn-primary w-full" disabled={busy}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}Save weight</button>
              </form>
              <button className="btn-ghost w-full mt-2" disabled={busy} onClick={recalc}><Calculator className="h-4 w-4" />Recalculate target now</button>
              <p className="text-xs text-slate-500 mt-2">Your target is recalculated automatically once a week of new weights is logged, using your real weight trend.</p>
              <div className="mt-3 max-h-40 overflow-y-auto text-sm divide-y divide-slate-100">
                {[...data.weights].reverse().map((w) => (
                  <div key={w.id} className="flex justify-between items-center py-1">
                    <span className="text-slate-600">{w.date}</span>
                    <span className="flex items-center gap-2">{w.weight_kg} kg<button className="text-slate-400 hover:text-red-600" title="Delete" onClick={() => del(w.id)}><Trash2 className="h-3.5 w-3.5" /></button></span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card p-5">
            <div className="flex flex-wrap justify-between items-center mb-2 gap-2">
              <h2 className="font-semibold text-slate-700">Calories eaten vs target</h2>
              <div className="flex gap-3 text-xs text-slate-500">
                <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-emerald-500" />within 10%</span>
                <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-amber-500" />off target</span>
                <span className="flex items-center gap-1"><span className="w-4 border-t-2 border-dashed border-slate-900" />target</span>
              </div>
            </div>
            <BarChart data={data.intake.map((d) => ({ x: d.date, value: d.kcal, target: d.target }))} />
          </div>

          <div className="card p-5">
            <h2 className="font-semibold text-slate-700 mb-2">Target history</h2>
            <div className="divide-y divide-slate-100 text-sm">
              {[...data.target_history].reverse().map((h, i) => (
                <div key={i} className="py-2 flex gap-3">
                  <div className="w-24 shrink-0 text-slate-500">{h.date}</div>
                  <div className="w-24 shrink-0 font-semibold text-slate-800">{Math.round(h.kcal)} kcal</div>
                  <div className="text-slate-600">{h.reason}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function Tile({ k, v, sub }) {
  return (
    <div className="card p-4">
      <div className="text-xs text-slate-500">{k}</div>
      <div className="text-2xl font-semibold text-slate-800 mt-1">{v}</div>
      {sub && <div className="text-xs text-slate-500">{sub}</div>}
    </div>
  )
}
