import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, Flame, NotebookPen, Scale } from 'lucide-react'
import api, { errorMessage, today } from '../api'
import { Disclaimer, ErrorBox, MEALS, ProgressBar, Spinner, label } from '../components/ui'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  const load = () => {
    setError('')
    Promise.all([api.get('/targets'), api.get('/logs', { params: { date: today() } }), api.get('/plans/latest'), api.get('/progress', { params: { days: 7 } })])
      .then(([t, l, p, pr]) => setData({ targets: t.data, log: l.data, plan: p.data.plan, progress: pr.data }))
      .catch((e) => setError(errorMessage(e)))
  }
  useEffect(load, [])

  if (error) return <ErrorBox message={error} onRetry={load} />
  if (!data) return <Spinner />
  const { targets: t, log, plan, progress } = data
  const planToday = plan?.days.find((d) => d.date === today())
  const remaining = Math.round(t.kcal - log.totals.kcal)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Today</h1>
          <p className="text-sm text-slate-500">{new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}</p>
        </div>
        <div className="flex gap-2">
          <Link to="/log" className="btn-primary"><NotebookPen className="h-4 w-4" />Log food</Link>
          <Link to="/plan" className="btn-ghost"><CalendarDays className="h-4 w-4" />Weekly plan</Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile icon={Flame} k="Daily target" v={`${t.kcal} kcal`} sub={`Maintenance ${t.tdee} kcal`} />
        <Tile icon={Flame} k="Remaining today" v={`${remaining} kcal`} sub={`${Math.round(log.totals.kcal)} kcal eaten`} accent={remaining < 0 ? 'text-amber-600' : 'text-emerald-700'} />
        <Tile icon={Scale} k="BMI" v={t.bmi} sub={`${t.bmi_category} - BMR ${t.bmr} kcal`} />
        <Tile icon={CalendarDays} k="Adherence (7 days)" v={`${progress.adherence.score}/100`} sub={`${progress.adherence.days_logged} of 7 days logged`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="card p-5 lg:col-span-2 space-y-3">
          <h2 className="font-semibold text-slate-700">Today's intake vs target</h2>
          <ProgressBar label="Calories" value={log.totals.kcal} target={t.kcal} unit="kcal" />
          <ProgressBar label="Protein" value={log.totals.protein} target={t.protein_g} />
          <ProgressBar label="Carbs" value={log.totals.carbs} target={t.carbs_g} />
          <ProgressBar label="Fat" value={log.totals.fat} target={t.fat_g} />
          <ProgressBar label="Fibre" value={log.totals.fibre} target={t.fibre_g} />
          <ProgressBar label="Sodium" value={log.totals.sodium} target={t.sodium_max_mg} unit="mg" cap />
          <ProgressBar label="Free sugar" value={log.totals.sugar} target={t.sugar_max_g} cap />
          <div className="text-xs text-slate-500 pt-2">Macro split {t.macros_pct.protein}% protein / {t.macros_pct.carbs}% carbs / {t.macros_pct.fat}% fat{t.gl_max ? ` - glycaemic load cap ${t.gl_max}/day` : ''}</div>
        </div>

        <div className="card p-5 lg:col-span-3">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-700">Today's plan</h2>
            {planToday && <span className="text-xs text-slate-500">{Math.round(planToday.totals.kcal)} kcal planned</span>}
          </div>
          {!planToday ? (
            <div className="text-sm text-slate-600 py-6 text-center">
              {plan ? 'Your current plan does not cover today.' : 'You have no meal plan yet.'}
              <div className="mt-3"><Link className="btn-primary" to="/plan?generate=1">Generate a 7-day plan</Link></div>
            </div>
          ) : (
            <div className="space-y-3">
              {MEALS.map((m) => (
                <div key={m} className="flex gap-3">
                  <div className="w-20 shrink-0 text-xs font-semibold uppercase text-slate-400 pt-0.5">{m}</div>
                  <div className="flex-1 text-sm text-slate-700">
                    {planToday.meals[m].map((it) => <div key={it.food_id}>{it.name} <span className="text-slate-400">- {Math.round(it.grams)} g, {Math.round(it.kcal)} kcal</span></div>)}
                  </div>
                </div>
              ))}
            </div>
          )}
          {log.entries.length > 0 && (
            <div className="mt-5 border-t border-slate-100 pt-3">
              <h3 className="text-sm font-semibold text-slate-600 mb-2">Logged today</h3>
              <div className="flex flex-wrap gap-2">
                {log.entries.map((e) => <span key={e.id} className="chip bg-slate-100 text-slate-700">{label(e.meal)}: {e.name} ({Math.round(e.kcal)} kcal)</span>)}
              </div>
            </div>
          )}
        </div>
      </div>
      {t.notes.length > 0 && (
        <div className="card p-5">
          <h2 className="font-semibold text-slate-700 mb-2">How your target is set</h2>
          <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">{t.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </div>
      )}
      <Disclaimer text={t.disclaimer} />
    </div>
  )
}

function Tile({ icon: Icon, k, v, sub, accent = 'text-slate-800' }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-xs text-slate-500"><Icon className="h-4 w-4" />{k}</div>
      <div className={`text-2xl font-semibold mt-1 ${accent}`}>{v}</div>
      <div className="text-xs text-slate-500">{sub}</div>
    </div>
  )
}
