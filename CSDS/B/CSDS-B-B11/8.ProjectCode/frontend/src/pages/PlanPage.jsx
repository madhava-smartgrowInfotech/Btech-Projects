import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BookOpen, Loader2, RefreshCw, Repeat, Sparkles } from 'lucide-react'
import api, { errorMessage, today } from '../api'
import { Disclaimer, ErrorBox, MEALS, Modal, Spinner, label } from '../components/ui'

export default function PlanPage() {
  const [params, setParams] = useSearchParams()
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [dayIdx, setDayIdx] = useState(0)
  const [swap, setSwap] = useState(null)      // {day, meal, index}
  const [recipe, setRecipe] = useState(null)  // item
  const started = useRef(false)

  const generate = async () => {
    setGenerating(true)
    setError('')
    try {
      const { data } = await api.post('/plans', {})
      setPlan(data)
      setDayIdx(0)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setGenerating(false)
    }
  }

  useEffect(() => {
    if (started.current) return
    started.current = true
    api.get('/plans/latest')
      .then(({ data }) => {
        setPlan(data.plan)
        if (data.plan) {
          const i = data.plan.days.findIndex((d) => d.date === today())
          if (i >= 0) setDayIdx(i)
        }
        if (params.get('generate') || !data.plan) {
          setParams({}, { replace: true })
          if (params.get('generate')) generate()
        }
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  const day = plan?.days[dayIdx]
  const t = plan?.targets

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Weekly plan</h1>
          {plan && <p className="text-sm text-slate-500">Optimised for {t.kcal} kcal/day - {plan.unique_dishes} different dishes - solved in {plan.solve_seconds}s</p>}
        </div>
        <button className="btn-primary" onClick={generate} disabled={generating}>
          {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : plan ? <RefreshCw className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
          {generating ? 'Optimising your week...' : plan ? 'Generate a new week' : 'Generate my plan'}
        </button>
      </div>
      <ErrorBox message={error} />
      {generating && !plan && <Spinner label="Optimising 7 days of meals against your targets..." />}
      {!plan && !generating && !error && <div className="card p-8 text-center text-slate-600">No plan yet. Generate one to get started.</div>}

      {plan && (
        <>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {plan.days.map((d, i) => (
              <button key={d.date} onClick={() => setDayIdx(i)}
                className={`rounded-xl px-3 py-2 text-sm whitespace-nowrap border ${i === dayIdx ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}`}>
                <div className="font-medium">{d.weekday.slice(0, 3)}</div>
                <div className={`text-xs ${i === dayIdx ? 'text-emerald-100' : 'text-slate-500'}`}>{Math.round(d.totals.kcal)} kcal</div>
              </button>
            ))}
          </div>

          <DayTotals day={day} t={t} />
          {day.note && <p className="text-xs text-amber-700">{day.note}</p>}

          <div className="grid gap-4 md:grid-cols-2">
            {MEALS.map((m) => (
              <div key={m} className="card p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-slate-700">{label(m)}</h3>
                  <span className="text-xs text-slate-500">{Math.round(day.meals[m].reduce((s, it) => s + it.kcal, 0))} kcal</span>
                </div>
                <div className="divide-y divide-slate-100">
                  {day.meals[m].map((it, idx) => (
                    <div key={`${it.food_id}-${idx}`} className="py-2 flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-800 truncate">{it.name}</div>
                        <div className="text-xs text-slate-500">
                          {Math.round(it.grams)} g ({it.servings} serving) - {Math.round(it.kcal)} kcal - P {it.protein} / C {it.carbs} / F {it.fat} g
                          {it.swapped_from && <span className="text-emerald-700"> - swapped from {it.swapped_from}</span>}
                        </div>
                      </div>
                      <button className="btn-ghost !px-2 !py-1 text-xs" title="Swap dish" onClick={() => setSwap({ day: dayIdx + 1, meal: m, index: idx })}><Repeat className="h-3.5 w-3.5" />Swap</button>
                      <button className="btn-ghost !px-2 !py-1 text-xs" title="Recipe" onClick={() => setRecipe(it)}><BookOpen className="h-3.5 w-3.5" />Recipe</button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
      {swap && <SwapModal plan={plan} target={swap} onClose={() => setSwap(null)} onDone={(p) => { setPlan(p); setSwap(null) }} />}
      {recipe && <RecipeModal item={recipe} onClose={() => setRecipe(null)} />}
      <Disclaimer />
    </div>
  )
}

function DayTotals({ day, t }) {
  const tt = day.totals
  const dev = ((tt.kcal - t.kcal) / t.kcal) * 100
  const cell = (k, v, target, unit, cap) => (
    <div className="rounded-xl bg-white border border-slate-200 px-3 py-2">
      <div className="text-xs text-slate-500">{k}</div>
      <div className="text-sm font-semibold text-slate-800">{Math.round(v)}{unit}</div>
      <div className="text-xs text-slate-400">{cap ? 'max ' : 'target '}{Math.round(target)}{unit}</div>
    </div>
  )
  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-2">
      <div className={`rounded-xl px-3 py-2 ${Math.abs(dev) <= 5 ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
        <div className="text-xs text-slate-500">Calories</div>
        <div className="text-sm font-semibold text-slate-800">{Math.round(tt.kcal)}</div>
        <div className="text-xs text-slate-500">{dev >= 0 ? '+' : ''}{dev.toFixed(1)}% vs {t.kcal}</div>
      </div>
      {cell('Protein', tt.protein, t.protein_g, ' g')}
      {cell('Carbs', tt.carbs, t.carbs_g, ' g')}
      {cell('Fat', tt.fat, t.fat_g, ' g')}
      {cell('Fibre', tt.fibre, t.fibre_g, ' g')}
      {cell('Sodium', tt.sodium, t.sodium_max_mg, ' mg', true)}
      {t.gl_max ? cell('Glycaemic load', tt.gl, t.gl_max, '', true) : cell('Free sugar', tt.sugar, t.sugar_max_g, ' g', true)}
    </div>
  )
}

function SwapModal({ plan, target, onClose, onDone }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(null)

  useEffect(() => {
    api.get(`/plans/${plan.id}/swap-options`, { params: target })
      .then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)))
  }, [])

  const choose = async (o) => {
    setBusy(o.food_id)
    setError('')
    try {
      const { data: p } = await api.post(`/plans/${plan.id}/swap`, { ...target, food_id: o.food_id, grams: o.grams })
      onDone(p)
    } catch (e) {
      setError(errorMessage(e))
      setBusy(null)
    }
  }

  return (
    <Modal title="Swap dish" onClose={onClose} wide>
      <ErrorBox message={error} />
      {!data && !error && <Spinner label="Finding nutritionally similar dishes..." />}
      {data && (
        <>
          <p className="text-sm text-slate-600 mb-3">
            Replacing <strong>{data.original.name}</strong> ({Math.round(data.original.grams)} g, {Math.round(data.original.kcal)} kcal).
            Alternatives come from the same nutrient cluster, with portions adjusted to match calories. Every option is checked against your allergies and daily limits.
          </p>
          {data.options.length === 0 && <p className="text-sm text-slate-500">No safe alternatives found for this dish.</p>}
          <div className="space-y-2">
            {data.options.map((o) => (
              <div key={o.food_id} className="flex items-center gap-3 rounded-xl border border-slate-200 p-3">
                <div className="flex-1">
                  <div className="text-sm font-medium text-slate-800">{o.name}
                    {o.same_cluster && <span className="chip bg-emerald-100 text-emerald-700 ml-2">closest match</span>}
                    <span className="chip bg-slate-100 text-slate-600 ml-1">{label(o.cuisine)}</span>
                  </div>
                  <div className="text-xs text-slate-500">{Math.round(o.grams)} g - {Math.round(o.kcal)} kcal ({o.kcal_diff >= 0 ? '+' : ''}{Math.round(o.kcal_diff)}) - P {o.protein} / C {o.carbs} / F {o.fat} g - similarity {o.similarity}</div>
                </div>
                <button className="btn-primary !py-1.5" disabled={busy !== null} onClick={() => choose(o)}>
                  {busy === o.food_id && <Loader2 className="h-4 w-4 animate-spin" />}Use this
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  )
}

function RecipeModal({ item, onClose }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const load = () => {
    setError('')
    setData(null)
    api.get(`/recipes/${item.food_id}`, { params: { grams: item.grams } })
      .then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)))
  }
  useEffect(load, [])

  return (
    <Modal title={`Recipe - ${item.name}`} onClose={onClose} wide>
      <ErrorBox message={error} onRetry={load} />
      {!data && !error && <Spinner label="Writing a recipe for your diet and allergies..." />}
      {data && (
        <div className="space-y-4 text-sm">
          <div className="flex flex-wrap gap-2">
            <span className="chip bg-emerald-100 text-emerald-700">1 portion - {Math.round(data.grams)} g</span>
            <span className="chip bg-slate-100 text-slate-700">{Math.round(data.nutrients.kcal)} kcal</span>
            {data.prep_minutes != null && <span className="chip bg-slate-100 text-slate-700">Prep {data.prep_minutes} min</span>}
            {data.cook_minutes != null && <span className="chip bg-slate-100 text-slate-700">Cook {data.cook_minutes} min</span>}
          </div>
          {data.warnings?.map((w) => <ErrorBox key={w} message={w} />)}
          <div>
            <h4 className="font-semibold text-slate-700 mb-1">Ingredients</h4>
            <ul className="list-disc pl-5 text-slate-700">{data.ingredients.map((i, k) => <li key={k}>{i.quantity} {i.item}</li>)}</ul>
          </div>
          <div>
            <h4 className="font-semibold text-slate-700 mb-1">Steps</h4>
            <ol className="list-decimal pl-5 space-y-1 text-slate-700">{data.steps.map((s, k) => <li key={k}>{s}</li>)}</ol>
          </div>
          {data.health_tips?.length > 0 && (
            <div>
              <h4 className="font-semibold text-slate-700 mb-1">Health tips</h4>
              <ul className="list-disc pl-5 text-slate-600">{data.health_tips.map((s, k) => <li key={k}>{s}</li>)}</ul>
            </div>
          )}
          <p className="text-xs text-slate-400">Recipe steps are AI-generated ({data.model}) and checked against your allergies and diet. Nutrition values come from the food database.</p>
        </div>
      )}
    </Modal>
  )
}
