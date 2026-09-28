import { useCallback, useEffect, useState } from 'react'
import { CheckCircle2, FlaskConical, Info, Loader2, UserPlus, Wand2 } from 'lucide-react'
import api, { errorMessage } from '../api'
import { Badge, ErrorBox, Loading, PageHeader, pct } from '../components/ui'

const CONDITIONS = [
  ['dialysisrenalendstage', 'End-stage renal disease'],
  ['asthma', 'Asthma'],
  ['irondef', 'Iron deficiency'],
  ['pneum', 'Pneumonia'],
  ['substancedependence', 'Substance dependence'],
  ['psychologicaldisordermajor', 'Major psychological disorder'],
  ['depress', 'Depression'],
  ['psychother', 'Other psychological disorder'],
  ['fibrosisandother', 'Fibrosis'],
  ['malnutrition', 'Malnutrition'],
  ['hemo', 'Blood disorder'],
]
const MEASURES = [
  ['hematocrit', 'Hematocrit (g/dL)', 0.1],
  ['neutrophils', 'Neutrophils (cells/uL)', 0.1],
  ['sodium', 'Sodium (mmol/L)', 0.1],
  ['glucose', 'Glucose (mg/dL)', 0.1],
  ['bloodureanitro', 'Blood urea nitrogen (mg/dL)', 0.1],
  ['creatinine', 'Creatinine (mg/dL)', 0.01],
  ['bmi', 'BMI', 0.1],
  ['pulse', 'Pulse (bpm)', 1],
  ['respiration', 'Respiration', 0.1],
  ['secondarydiagnosisnonicd9', 'Secondary diagnoses', 1],
]
const EMPTY = {
  patient_ref: '', facility: 'A', ward: 'General', gender: 'F', rcount: 0,
  ...Object.fromEntries(CONDITIONS.map(([k]) => [k, 0])),
  hematocrit: 12, neutrophils: 9.5, sodium: 137.9, glucose: 142, bloodureanitro: 12, creatinine: 1.1,
  bmi: 29.8, pulse: 73, respiration: 6.5, secondarydiagnosisnonicd9: 1,
}

function Reasons({ result }) {
  const max = Math.max(...result.reasons.map((r) => Math.abs(r.impact_days)), 0.1)
  return (
    <div>
      <div className="text-xs text-slate-500 mb-2">
        Starting from the average stay of {result.baseline_days} days, each factor adds (red) or removes (green) days:
      </div>
      <ul className="space-y-1.5">
        {result.reasons.map((r) => (
          <li key={r.feature} className="grid grid-cols-[1fr_auto] sm:grid-cols-[210px_1fr_60px] items-center gap-2 text-sm">
            <span className="text-slate-700 truncate" title={r.label}>
              {r.label} <span className="text-slate-400">= {Number.isInteger(r.value) ? r.value : r.value.toFixed(1)}</span>
            </span>
            <div className="hidden sm:flex h-4 bg-slate-100 rounded relative">
              <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-300" />
              <div
                className={`absolute top-0 bottom-0 rounded ${r.impact_days > 0 ? 'bg-red-400 left-1/2' : 'bg-emerald-400 right-1/2'}`}
                style={{ width: `${(Math.abs(r.impact_days) / max) * 50}%` }}
              />
            </div>
            <span className={`text-right font-medium ${r.impact_days > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
              {r.impact_days > 0 ? '+' : ''}
              {r.impact_days.toFixed(2)} d
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Admissions() {
  const [form, setForm] = useState(EMPTY)
  const [sampleNote, setSampleNote] = useState('')
  const [result, setResult] = useState(null)
  const [admitted, setAdmitted] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [list, setList] = useState(null)
  const [listError, setListError] = useState('')

  const loadList = useCallback(async () => {
    setListError('')
    try {
      const { data } = await api.get('/admissions')
      setList(data)
    } catch (err) {
      setListError(errorMessage(err))
    }
  }, [])
  useEffect(() => {
    loadList()
  }, [loadList])

  const set = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }))
    setResult(null)
    setAdmitted(null)
  }

  const loadSample = async (profile) => {
    setBusy('sample')
    setError('')
    try {
      const { data } = await api.get('/admissions/sample', { params: { profile } })
      setForm(data.sample)
      setSampleNote(data.source)
      setResult(null)
      setAdmitted(null)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const payload = () => ({ ...form, rcount: Number(form.rcount), secondarydiagnosisnonicd9: Number(form.secondarydiagnosisnonicd9) })

  const predict = async () => {
    setBusy('predict')
    setError('')
    try {
      const { data } = await api.post('/admissions/predict', payload())
      setResult(data)
      setAdmitted(null)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const admit = async () => {
    setBusy('admit')
    setError('')
    try {
      const { data } = await api.post('/admissions', payload())
      setResult({ ...data.prediction, disclaimer: data.disclaimer })
      setAdmitted(data)
      loadList()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  return (
    <div>
      <PageHeader title="Admissions and predictions" subtitle="Predict length of stay at admission and see the factors behind it">
        <button className="btn-secondary" onClick={() => loadSample('long')} disabled={!!busy}>
          <Wand2 size={16} /> Sample long stay
        </button>
        <button className="btn-secondary" onClick={() => loadSample('short')} disabled={!!busy}>
          <Wand2 size={16} /> Sample short stay
        </button>
      </PageHeader>
      <ErrorBox message={error} />

      <div className="grid lg:grid-cols-5 gap-6">
        <div className="card p-5 lg:col-span-3 space-y-5">
          {sampleNote && (
            <div className="flex items-center gap-2 text-xs text-sky-800 bg-sky-50 rounded-lg p-2">
              <FlaskConical size={14} /> Sample data: {sampleNote}
            </div>
          )}
          <section>
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Admission</h2>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="col-span-2 sm:col-span-1">
                <label className="label">Patient ref</label>
                <input className="input" value={form.patient_ref} onChange={(e) => set('patient_ref', e.target.value)} placeholder="auto" />
              </div>
              <div>
                <label className="label">Facility</label>
                <select className="input" value={form.facility} onChange={(e) => set('facility', e.target.value)}>
                  {['A', 'B', 'C', 'D', 'E'].map((f) => <option key={f} value={f}>Facility {f}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Ward</label>
                <select className="input" value={form.ward} onChange={(e) => set('ward', e.target.value)}>
                  {['General', 'Surgical', 'Maternity', 'Paediatric', 'ICU'].map((w) => <option key={w}>{w}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Sex</label>
                <select className="input" value={form.gender} onChange={(e) => set('gender', e.target.value)}>
                  <option value="F">Female</option>
                  <option value="M">Male</option>
                </select>
              </div>
              <div>
                <label className="label">Readmissions (180 d)</label>
                <select className="input" value={form.rcount} onChange={(e) => set('rcount', Number(e.target.value))}>
                  {[0, 1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n === 5 ? '5+' : n}</option>)}
                </select>
              </div>
            </div>
          </section>
          <section>
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Conditions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {CONDITIONS.map(([k, label]) => (
                <label key={k} className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" className="accent-teal-700 h-4 w-4" checked={!!form[k]} onChange={(e) => set(k, e.target.checked ? 1 : 0)} />
                  {label}
                </label>
              ))}
            </div>
          </section>
          <section>
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Labs and vitals</h2>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {MEASURES.map(([k, label, step]) => (
                <div key={k}>
                  <label className="label truncate" title={label}>{label}</label>
                  <input className="input" type="number" step={step} value={form[k]} onChange={(e) => set(k, e.target.value === '' ? '' : Number(e.target.value))} />
                </div>
              ))}
            </div>
          </section>
          <div className="flex flex-wrap gap-2 pt-1">
            <button className="btn-secondary" onClick={predict} disabled={!!busy}>
              {busy === 'predict' ? <Loader2 size={16} className="animate-spin" /> : <Info size={16} />} Predict stay
            </button>
            <button className="btn-primary" onClick={admit} disabled={!!busy}>
              {busy === 'admit' ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />} Admit patient
            </button>
          </div>
        </div>

        <div className="card p-5 lg:col-span-2">
          <h2 className="font-semibold text-slate-900 mb-3">Prediction</h2>
          {busy === 'predict' || busy === 'admit' ? (
            <Loading label="Running the model..." />
          ) : !result ? (
            <p className="text-sm text-slate-500">Fill the form or load a sample, then press Predict stay or Admit patient.</p>
          ) : (
            <div className="space-y-4">
              {admitted && (
                <div className="flex items-center gap-2 rounded-lg bg-teal-50 text-teal-900 text-sm p-2.5">
                  <CheckCircle2 size={16} /> {admitted.patient_ref} admitted to Facility {admitted.facility} {admitted.ward}. Forecasts now include this patient.
                </div>
              )}
              <div className="flex items-end gap-3">
                <div className="text-4xl font-bold text-slate-900">{result.predicted_days}</div>
                <div className="pb-1 text-slate-500">days expected</div>
                <div className="pb-1 ml-auto">
                  <Badge tone={result.long_stay ? 'red' : 'teal'}>{result.long_stay ? 'Long stay' : 'Short stay'}</Badge>
                </div>
              </div>
              <div className="text-sm text-slate-600">
                Likely range {result.range_days[0]}-{result.range_days[1]} days (80%). Probability of a long stay (over{' '}
                {result.long_stay_threshold_days} days): <strong>{pct(result.long_stay_probability)}</strong>.
              </div>
              <Reasons result={result} />
              <p className="text-xs text-slate-500 border-t border-slate-100 pt-3">{result.disclaimer}</p>
            </div>
          )}
        </div>
      </div>

      <div className="card mt-6 overflow-x-auto">
        <h2 className="font-semibold text-slate-900 px-5 pt-5 pb-2">Admitted in HospiSense</h2>
        <ErrorBox message={listError} onRetry={loadList} />
        {!list ? (
          !listError && <Loading />
        ) : list.length === 0 ? (
          <p className="text-sm text-slate-500 px-5 pb-5">No admissions recorded yet.</p>
        ) : (
          <table className="w-full min-w-[640px]">
            <thead>
              <tr>
                <th className="th">Patient</th>
                <th className="th">Date</th>
                <th className="th">Facility / ward</th>
                <th className="th">Predicted stay</th>
                <th className="th">Class</th>
                <th className="th">Top factor</th>
                <th className="th">By</th>
              </tr>
            </thead>
            <tbody>
              {list.map((a) => (
                <tr key={a.id}>
                  <td className="td font-medium">{a.patient_ref}</td>
                  <td className="td">{a.admit_date}</td>
                  <td className="td">{a.facility} / {a.ward}</td>
                  <td className="td">{a.predicted_days} d</td>
                  <td className="td"><Badge tone={a.long_stay ? 'red' : 'teal'}>{a.long_stay ? 'Long' : 'Short'}</Badge></td>
                  <td className="td">{a.prediction.reasons[0]?.label} ({a.prediction.reasons[0]?.impact_days > 0 ? '+' : ''}{a.prediction.reasons[0]?.impact_days} d)</td>
                  <td className="td text-xs">{a.created_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
