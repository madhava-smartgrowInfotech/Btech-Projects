import { useEffect, useState } from 'react'
import { AlertTriangle, Camera, Loader2, Plus, Search, Trash2, Wheat } from 'lucide-react'
import api, { errorMessage, today } from '../api'
import { ErrorBox, MEALS, ProgressBar, Spinner, label } from '../components/ui'

export default function FoodLog() {
  const [date, setDate] = useState(today())
  const [meal, setMeal] = useState(defaultMeal())
  const [tab, setTab] = useState('search')
  const [day, setDay] = useState(null)
  const [error, setError] = useState('')
  const [flash, setFlash] = useState('')

  const load = () => {
    setError('')
    api.get('/logs', { params: { date } }).then((r) => setDay(r.data)).catch((e) => setError(errorMessage(e)))
  }
  useEffect(load, [date])

  const added = (entry) => {
    setFlash(`Logged ${entry.name} (${Math.round(entry.kcal)} kcal) to ${entry.meal}.`)
    setTimeout(() => setFlash(''), 4000)
    load()
  }
  const remove = async (id) => {
    try { await api.delete(`/logs/${id}`); load() } catch (e) { setError(errorMessage(e)) }
  }

  const tabs = [
    { id: 'search', label: 'Search dishes', icon: Search },
    { id: 'usda', label: 'Ingredients (USDA)', icon: Wheat },
    { id: 'photo', label: 'Log by photo', icon: Camera },
  ]

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">Food log</h1>
        <div className="flex gap-2 items-end">
          <div><label className="label">Date</label><input type="date" className="input" value={date} max={today()} onChange={(e) => setDate(e.target.value)} /></div>
          <div><label className="label">Meal</label>
            <select className="input" value={meal} onChange={(e) => setMeal(e.target.value)}>{MEALS.map((m) => <option key={m} value={m}>{label(m)}</option>)}</select>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-5">
        <div className="lg:col-span-3 card p-5">
          <div className="flex gap-1 mb-4 overflow-x-auto">
            {tabs.map(({ id, label: l, icon: Icon }) => (
              <button key={id} onClick={() => setTab(id)} className={`flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${tab === id ? 'bg-emerald-50 text-emerald-700 font-medium' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon className="h-4 w-4" />{l}
              </button>
            ))}
          </div>
          {flash && <div className="mb-3 rounded-xl bg-emerald-50 border border-emerald-200 p-2 text-sm text-emerald-800">{flash}</div>}
          {tab === 'search' && <DishSearch date={date} meal={meal} onAdded={added} />}
          {tab === 'usda' && <UsdaSearch date={date} meal={meal} onAdded={added} />}
          {tab === 'photo' && <PhotoLog date={date} meal={meal} onAdded={added} />}
        </div>

        <div className="lg:col-span-2 space-y-4">
          <ErrorBox message={error} onRetry={load} />
          {!day && !error && <Spinner />}
          {day && (
            <>
              <div className="card p-5 space-y-3">
                <h2 className="font-semibold text-slate-700">Totals for {date === today() ? 'today' : date}</h2>
                <ProgressBar label="Calories" value={day.totals.kcal} target={day.targets.kcal} unit="kcal" />
                <ProgressBar label="Protein" value={day.totals.protein} target={day.targets.protein} />
                <ProgressBar label="Carbs" value={day.totals.carbs} target={day.targets.carbs} />
                <ProgressBar label="Fat" value={day.totals.fat} target={day.targets.fat} />
                <ProgressBar label="Sodium" value={day.totals.sodium} target={day.targets.sodium} unit="mg" cap />
              </div>
              <div className="card p-5">
                <h2 className="font-semibold text-slate-700 mb-2">Entries</h2>
                {day.entries.length === 0 && <p className="text-sm text-slate-500">Nothing logged yet.</p>}
                {MEALS.map((m) => {
                  const items = day.entries.filter((e) => e.meal === m)
                  if (!items.length) return null
                  return (
                    <div key={m} className="mb-3">
                      <div className="text-xs font-semibold uppercase text-slate-400 mb-1">{m}</div>
                      {items.map((e) => (
                        <div key={e.id} className="flex items-center gap-2 py-1 text-sm">
                          <div className="flex-1">
                            {e.name} <span className="text-slate-400">- {Math.round(e.grams)} g, {Math.round(e.kcal)} kcal</span>
                            {e.source !== 'database' && <span className="chip bg-sky-100 text-sky-700 ml-1">{e.source}</span>}
                          </div>
                          <button className="p-1 text-slate-400 hover:text-red-600" title="Delete" onClick={() => remove(e.id)}><Trash2 className="h-4 w-4" /></button>
                        </div>
                      ))}
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function defaultMeal() {
  const h = new Date().getHours()
  return h < 11 ? 'breakfast' : h < 16 ? 'lunch' : h < 19 ? 'snack' : 'dinner'
}

function FoodRow({ food, grams, setGrams, onAdd, busy, per100 }) {
  const n = per100 || food.per_100g
  const g = Number(grams) || 0
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 p-3">
      <div className="flex-1 min-w-[180px]">
        <div className="text-sm font-medium text-slate-800">{food.name}</div>
        <div className="text-xs text-slate-500">{Math.round(n.kcal * g / 100)} kcal - P {(n.protein * g / 100).toFixed(1)} / C {(n.carbs * g / 100).toFixed(1)} / F {(n.fat * g / 100).toFixed(1)} g</div>
        {food.warnings?.length > 0 && <div className="text-xs text-amber-700 flex items-center gap-1 mt-0.5"><AlertTriangle className="h-3 w-3" />{food.warnings.join('; ')}</div>}
      </div>
      <div className="flex items-center gap-1">
        <input className="input !w-20 !py-1" type="number" min="1" value={grams} onChange={(e) => setGrams(e.target.value)} />
        <span className="text-xs text-slate-500">g</span>
      </div>
      <button className="btn-primary !py-1.5" disabled={busy || g <= 0} onClick={onAdd}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}Log</button>
    </div>
  )
}

function DishSearch({ date, meal, onAdded }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState(null)
  const [grams, setGrams] = useState({})
  const [busy, setBusy] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const search = async (e) => {
    e?.preventDefault()
    if (!q.trim()) return
    setLoading(true); setError('')
    try {
      const { data } = await api.get('/foods/search', { params: { q } })
      setResults(data.results)
      setGrams(Object.fromEntries(data.results.map((f) => [f.food_id, f.serving_g])))
    } catch (err) { setError(errorMessage(err)) } finally { setLoading(false) }
  }
  const add = async (f) => {
    setBusy(f.food_id); setError('')
    try {
      const { data } = await api.post('/logs', { date, meal, food_id: f.food_id, grams: Number(grams[f.food_id]) })
      onAdded(data)
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(null) }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={search} className="flex gap-2">
        <input className="input" placeholder="Search Indian dishes, e.g. idli, rajma, paneer" value={q} onChange={(e) => setQ(e.target.value)} />
        <button className="btn-primary" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}Search</button>
      </form>
      <ErrorBox message={error} />
      {results && results.length === 0 && <p className="text-sm text-slate-500">No dishes found. Try another name, or search raw ingredients in the USDA tab.</p>}
      {results?.map((f) => (
        <FoodRow key={f.food_id} food={f} grams={grams[f.food_id]} setGrams={(v) => setGrams({ ...grams, [f.food_id]: v })} busy={busy === f.food_id} onAdd={() => add(f)} />
      ))}
    </div>
  )
}

function UsdaSearch({ date, meal, onAdded }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState(null)
  const [grams, setGrams] = useState({})
  const [busy, setBusy] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const search = async (e) => {
    e?.preventDefault()
    if (!q.trim()) return
    setLoading(true); setError('')
    try {
      const { data } = await api.get('/foods/usda', { params: { q } })
      setResults(data.results)
      setGrams(Object.fromEntries(data.results.map((f) => [f.fdc_id, 100])))
    } catch (err) { setError(errorMessage(err)) } finally { setLoading(false) }
  }
  const add = async (f) => {
    setBusy(f.fdc_id); setError('')
    try {
      const { data } = await api.post('/logs', { date, meal, fdc_id: f.fdc_id, grams: Number(grams[f.fdc_id]), source: 'usda' })
      onAdded(data)
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(null) }
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">Look up raw ingredients (fruit, nuts, milk, grains) in USDA FoodData Central.</p>
      <form onSubmit={search} className="flex gap-2">
        <input className="input" placeholder="e.g. banana raw, almonds, whole milk" value={q} onChange={(e) => setQ(e.target.value)} />
        <button className="btn-primary" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}Search</button>
      </form>
      <ErrorBox message={error} />
      {results && results.length === 0 && <p className="text-sm text-slate-500">No ingredients found.</p>}
      {results?.map((f) => (
        <FoodRow key={f.fdc_id} food={f} per100={f.per_100g} grams={grams[f.fdc_id]} setGrams={(v) => setGrams({ ...grams, [f.fdc_id]: v })} busy={busy === f.fdc_id} onAdd={() => add(f)} />
      ))}
    </div>
  )
}

function PhotoLog({ date, meal, onAdded }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [result, setResult] = useState(null)
  const [grams, setGrams] = useState({})
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState('')

  const pick = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f); setResult(null); setError('')
    setPreview(URL.createObjectURL(f))
  }
  const analyse = async () => {
    setLoading(true); setError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await api.post('/logs/photo', fd)
      setResult(data)
      const g = {}
      data.items.forEach((it) => it.matches.forEach((m) => { g[m.food_id] = m.grams }))
      setGrams(g)
    } catch (err) { setError(errorMessage(err)) } finally { setLoading(false) }
  }
  const confirm = async (m) => {
    setBusy(m.food_id); setError('')
    try {
      const { data } = await api.post('/logs', { date, meal, food_id: m.food_id, grams: Number(grams[m.food_id]), source: 'photo' })
      onAdded(data)
    } catch (err) { setError(errorMessage(err)) } finally { setBusy(null) }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="btn-ghost cursor-pointer"><Camera className="h-4 w-4" />Choose or take a photo
          <input type="file" accept="image/*" capture="environment" className="hidden" onChange={pick} />
        </label>
        <button className="btn-primary" disabled={!file || loading} onClick={analyse}>{loading && <Loader2 className="h-4 w-4 animate-spin" />}{loading ? 'Recognising...' : 'Recognise dish'}</button>
      </div>
      {preview && <img src={preview} alt="Meal preview" className="max-h-56 rounded-xl border border-slate-200" />}
      <ErrorBox message={error} />
      {result && result.items.length === 0 && <p className="text-sm text-slate-500">No food was recognised in this photo. Try a clearer, closer shot.</p>}
      {result?.items.map((it, k) => (
        <div key={k} className="rounded-xl bg-slate-50 border border-slate-200 p-3 space-y-2">
          <div className="text-sm">
            Detected <strong>{it.detected}</strong>
            {it.confidence != null && <span className="text-slate-500"> ({Math.round(it.confidence * 100)}% confident)</span>}
            {it.estimated_grams && <span className="text-slate-500">, about {Math.round(it.estimated_grams)} g</span>}
          </div>
          {it.description && <div className="text-xs text-slate-500">{it.description}</div>}
          <div className="text-xs font-medium text-slate-600">Confirm the closest match from the database (adjust grams if needed):</div>
          {it.matches.length === 0 && <p className="text-xs text-slate-500">No database match. Use the search tab instead.</p>}
          {it.matches.map((m) => (
            <FoodRow key={m.food_id} food={m} grams={grams[m.food_id]} setGrams={(v) => setGrams({ ...grams, [m.food_id]: v })} busy={busy === m.food_id} onAdd={() => confirm(m)} />
          ))}
        </div>
      ))}
    </div>
  )
}
