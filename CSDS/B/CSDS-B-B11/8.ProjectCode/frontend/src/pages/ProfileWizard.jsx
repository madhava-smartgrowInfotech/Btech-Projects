import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import api, { errorMessage } from '../api'
import { useAuth } from '../auth'
import { Disclaimer, ErrorBox, Spinner, label } from '../components/ui'

const EMPTY = { age: '', gender: 'female', height_cm: '', weight_kg: '', activity: 'moderate', diet_type: 'vegetarian',
  cuisine: 'both', allergies: [], conditions: [], goal: 'maintain' }

const ACTIVITY_HELP = { sedentary: 'Desk job, little exercise', light: 'Exercise 1-3 days/week', moderate: 'Exercise 3-5 days/week',
  active: 'Hard exercise 6-7 days/week', very_active: 'Physical job plus training' }
const STEPS = ['Body', 'Food preferences', 'Health and goal']

function Choice({ options, value, onChange, multi, help }) {
  const selected = (o) => (multi ? value.includes(o) : value === o)
  const toggle = (o) => (multi ? onChange(selected(o) ? value.filter((x) => x !== o) : [...value, o]) : onChange(o))
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button type="button" key={o} onClick={() => toggle(o)}
          className={`rounded-xl border px-3 py-2 text-sm text-left ${selected(o) ? 'border-emerald-500 bg-emerald-50 text-emerald-800' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'}`}>
          <div className="font-medium flex items-center gap-1">{selected(o) && <Check className="h-3.5 w-3.5" />}{label(o)}</div>
          {help?.[o] && <div className="text-xs text-slate-500">{help[o]}</div>}
        </button>
      ))}
    </div>
  )
}

export default function ProfileWizard() {
  const nav = useNavigate()
  const { markProfile } = useAuth()
  const [form, setForm] = useState(EMPTY)
  const [options, setOptions] = useState(null)
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    Promise.all([api.get('/profile/options'), api.get('/profile')])
      .then(([o, p]) => { setOptions(o.data); if (p.data.profile) setForm({ ...EMPTY, ...p.data.profile }) })
      .catch((e) => setError(errorMessage(e)))
  }, [])

  const set = (k) => (v) => setForm({ ...form, [k]: v })
  const bodyValid = form.age >= 18 && form.age <= 90 && form.height_cm >= 120 && form.height_cm <= 230 && form.weight_kg >= 30 && form.weight_kg <= 250

  const save = async () => {
    setBusy(true)
    setError('')
    try {
      const { data } = await api.put('/profile', { ...form, age: Number(form.age), height_cm: Number(form.height_cm), weight_kg: Number(form.weight_kg) })
      markProfile()
      setResult(data.targets)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  if (!options && !error) return <Spinner />

  if (result) {
    return (
      <div className="max-w-2xl mx-auto card p-6">
        <h1 className="text-xl font-semibold text-slate-800">Your daily targets</h1>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <Stat k="BMI" v={`${result.bmi}`} sub={result.bmi_category} />
          <Stat k="BMR" v={`${result.bmr}`} sub="kcal at rest" />
          <Stat k="Maintenance" v={`${result.tdee}`} sub="kcal/day" />
          <Stat k="Target" v={`${result.kcal}`} sub="kcal/day" strong />
        </div>
        <div className="grid grid-cols-3 gap-3 mt-3">
          <Stat k="Protein" v={`${result.protein_g} g`} sub={`${result.macros_pct.protein}%`} />
          <Stat k="Carbs" v={`${result.carbs_g} g`} sub={`${result.macros_pct.carbs}%`} />
          <Stat k="Fat" v={`${result.fat_g} g`} sub={`${result.macros_pct.fat}%`} />
        </div>
        <ul className="mt-4 text-sm text-slate-600 list-disc pl-5 space-y-1">{result.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        <div className="mt-6 flex gap-2">
          <button className="btn-primary" onClick={() => nav('/plan?generate=1')}>Generate my weekly plan</button>
          <button className="btn-ghost" onClick={() => nav('/dashboard')}>Go to dashboard</button>
        </div>
        <Disclaimer text={result.disclaimer} />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-semibold text-slate-800">Your profile</h1>
      <div className="flex gap-2 mt-4 mb-4">
        {STEPS.map((s, i) => (
          <div key={s} className={`flex-1 rounded-full h-1.5 ${i <= step ? 'bg-emerald-500' : 'bg-slate-200'}`} title={s} />
        ))}
      </div>
      <div className="card p-6 space-y-5">
        <h2 className="font-semibold text-slate-700">Step {step + 1} of 3 - {STEPS[step]}</h2>
        {step === 0 && (
          <>
            <div className="grid grid-cols-3 gap-3">
              <div><label className="label">Age</label><input className="input" type="number" value={form.age} onChange={(e) => set('age')(e.target.value)} /></div>
              <div><label className="label">Height (cm)</label><input className="input" type="number" value={form.height_cm} onChange={(e) => set('height_cm')(e.target.value)} /></div>
              <div><label className="label">Weight (kg)</label><input className="input" type="number" step="0.1" value={form.weight_kg} onChange={(e) => set('weight_kg')(e.target.value)} /></div>
            </div>
            <div><label className="label">Gender</label><Choice options={['female', 'male', 'other']} value={form.gender} onChange={set('gender')} /></div>
            <div><label className="label">Activity level</label><Choice options={options.activity} value={form.activity} onChange={set('activity')} help={ACTIVITY_HELP} /></div>
            {!bodyValid && (form.age || form.height_cm || form.weight_kg) && <p className="text-xs text-amber-700">Enter an age of 18-90, a height of 120-230 cm and a weight of 30-250 kg.</p>}
          </>
        )}
        {step === 1 && (
          <>
            <div><label className="label">Diet type</label><Choice options={options.diet_type} value={form.diet_type} onChange={set('diet_type')} /></div>
            <div><label className="label">Cuisine</label><Choice options={options.cuisine} value={form.cuisine} onChange={set('cuisine')}
              help={{ north: 'North Indian', south: 'South Indian', both: 'Mix of both' }} /></div>
            <div><label className="label">Allergies (these dishes are never suggested)</label><Choice multi options={options.allergies} value={form.allergies} onChange={set('allergies')} /></div>
          </>
        )}
        {step === 2 && (
          <>
            <div><label className="label">Health conditions</label><Choice multi options={options.conditions} value={form.conditions} onChange={set('conditions')} /></div>
            <div><label className="label">Goal</label><Choice options={options.goal} value={form.goal}
              onChange={set('goal')} help={{ lose: 'About 0.5 kg per week', maintain: 'Keep my weight', gain: 'About 0.25 kg per week' }} /></div>
          </>
        )}
        <ErrorBox message={error} />
        <div className="flex justify-between">
          <button className="btn-ghost" disabled={step === 0} onClick={() => setStep(step - 1)}><ChevronLeft className="h-4 w-4" />Back</button>
          {step < 2
            ? <button className="btn-primary" disabled={step === 0 && !bodyValid} onClick={() => setStep(step + 1)}>Next<ChevronRight className="h-4 w-4" /></button>
            : <button className="btn-primary" disabled={busy || !bodyValid} onClick={save}>{busy && <Loader2 className="h-4 w-4 animate-spin" />}Calculate my targets</button>}
        </div>
      </div>
      <Disclaimer />
    </div>
  )
}

function Stat({ k, v, sub, strong }) {
  return (
    <div className={`rounded-xl p-3 ${strong ? 'bg-emerald-600 text-white' : 'bg-slate-50 border border-slate-200'}`}>
      <div className={`text-xs ${strong ? 'text-emerald-100' : 'text-slate-500'}`}>{k}</div>
      <div className="text-xl font-semibold">{v}</div>
      <div className={`text-xs ${strong ? 'text-emerald-100' : 'text-slate-500'}`}>{sub}</div>
    </div>
  )
}
