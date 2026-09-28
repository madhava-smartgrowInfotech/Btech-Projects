import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { CheckCircle2, FileText, HeartPulse, Loader2, ScanEye, TriangleAlert } from 'lucide-react'
import api, { errorText, pct } from '../api.js'
import ClinicalForm, { EMPTY_CLINICAL } from '../components/ClinicalForm.jsx'
import { Disclaimer, ErrorBox, Figure, ProbBar, STAGE_STYLE, Spinner } from '../components/ui.jsx'

const STEP_CAPTIONS = { original: '1. Original (cropped)', green: '2. Green channel', clahe: '3. CLAHE enhanced', resized: '4. Resized 256 + normalised' }
const BAND_CAPTIONS = { LL: 'LL - approximation', LH: 'LH - horizontal detail', HL: 'HL - vertical detail', HH: 'HH - diagonal detail' }

function WaveletView({ wavelet }) {
  const [level, setLevel] = useState('2')
  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">Haar wavelet sub-bands</h2>
        <div className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
          {['1', '2'].map((l) => (
            <button key={l} onClick={() => setLevel(l)} className={`rounded-md px-3 py-1 ${level === l ? 'bg-white font-medium shadow-sm' : 'text-slate-600'}`}>
              Level {l}
            </button>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {['LL', 'LH', 'HL', 'HH'].map((b) => (
          <Figure key={b} src={wavelet[`${level}_${b}`]} caption={BAND_CAPTIONS[b]} />
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Detail bands (LH, HL, HH) highlight vessel edges and small lesions; all 8 sub-bands from both levels are stacked as the LeNet input.
      </p>
    </div>
  )
}

export default function Result() {
  const { id } = useParams()
  const location = useLocation()
  const [s, setS] = useState(null)
  const [error, setError] = useState('')
  const [clinical, setClinical] = useState(EMPTY_CLINICAL)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState(location.state?.clinicalError || '')
  const [editing, setEditing] = useState(false)

  const load = () => {
    setError('')
    api.get(`/screenings/${id}`)
      .then(({ data }) => {
        setS(data)
        setClinical(data.clinical ? { ...EMPTY_CLINICAL, ...data.clinical } : { ...EMPTY_CLINICAL, age: data.patient.age, sex: data.patient.sex === 'Female' ? 0 : 1 })
      })
      .catch((e) => setError(errorText(e)))
  }
  useEffect(load, [id])

  const saveClinical = async (e) => {
    e.preventDefault()
    setSaving(true)
    setFormError('')
    try {
      const { data } = await api.post(`/screenings/${id}/clinical`, clinical)
      setS(data)
      setEditing(false)
    } catch (err) {
      setFormError(errorText(err))
    } finally {
      setSaving(false)
    }
  }

  if (error) return <ErrorBox error={error} onRetry={load} />
  if (!s) return <Spinner text="Loading screening..." />
  const r = s.retina || {}
  const st = s.stage_detail
  const q = s.quality || {}

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Screening #{s.id}</h1>
          <p className="text-sm text-slate-500">
            <Link className="text-teal-700 hover:underline" to={`/patients/${s.patient.id}`}>{s.patient.name}</Link> ({s.patient.code}, {s.patient.age}, {s.patient.sex})
            {' '}- {s.eye} eye - {new Date(s.created_at).toLocaleString()} - by {s.screened_by}
          </p>
        </div>
        {st && (
          <Link to={`/screenings/${s.id}/report`} className="btn-primary">
            <FileText className="h-4 w-4" /> Screening report
          </Link>
        )}
      </div>

      {st && (
        <div className={`rounded-xl border-2 p-5 ${STAGE_STYLE[st.stage]}`}>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="text-sm font-medium uppercase tracking-wide">Overall risk stage</div>
            <div className="text-xs">Score {st.score}/6</div>
          </div>
          <div className="mt-1 text-3xl font-bold">{st.stage}</div>
          <ul className="mt-2 space-y-0.5 text-sm">{st.reasons.map((x) => <li key={x}>{x}</li>)}</ul>
          <div className="mt-4 rounded-lg bg-white/70 p-4 text-slate-800">
            <div className="mb-1 text-sm font-semibold">Recommendations</div>
            <ul className="list-disc space-y-1 pl-5 text-sm">{st.recommendations.map((x) => <li key={x}>{x}</li>)}</ul>
          </div>
        </div>
      )}

      <div className={`flex items-start gap-2 rounded-lg border px-4 py-3 text-sm ${q.passed ? 'border-green-200 bg-green-50 text-green-800' : 'border-amber-200 bg-amber-50 text-amber-800'}`}>
        {q.passed ? <CheckCircle2 className="mt-0.5 h-4 w-4" /> : <TriangleAlert className="mt-0.5 h-4 w-4" />}
        <div>
          <b>Image quality {q.passed ? 'passed' : 'check failed'}</b> - sharpness {q.sharpness} (min {q.thresholds?.sharpness_min}), brightness {q.brightness}
          {' '}(range {q.thresholds?.brightness_range?.join('-')}), clipped {(q.clipped_fraction * 100).toFixed(1)}%.
          {!q.passed && <div>{q.issues?.join(' ')} Results may be less reliable; consider retaking the photo.</div>}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 font-semibold">Preprocessing steps</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {Object.entries(STEP_CAPTIONS).map(([k, c]) => <Figure key={k} src={s.images.steps[k]} caption={c} />)}
        </div>
      </div>

      <WaveletView wavelet={s.images.wavelet} />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card space-y-4">
          <h2 className="flex items-center gap-2 font-semibold"><ScanEye className="h-5 w-5 text-teal-700" /> Hypertensive retinopathy (LeNet)</h2>
          <div>
            <div className="mb-1 flex items-baseline justify-between">
              <span className={`text-lg font-bold ${r.positive ? 'text-red-700' : 'text-green-700'}`}>{r.label}</span>
              <span className="text-2xl font-bold">{pct(r.probability)}</span>
            </div>
            <ProbBar value={r.probability} threshold={r.threshold} />
            <p className="mt-1 text-xs text-slate-500">Black marker = decision threshold ({pct(r.threshold)}).</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Figure src={s.images.heatmap} caption="Grad-CAM heatmap" />
            <Figure src={s.images.vessels} caption="Frangi vessel map" />
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg bg-slate-50 p-3"><div className="text-xs text-slate-500">Vessel density</div><div className="font-semibold">{((r.vessels?.vessel_density || 0) * 100).toFixed(1)}%</div></div>
            <div className="rounded-lg bg-slate-50 p-3"><div className="text-xs text-slate-500">Mean vessel width</div><div className="font-semibold">{r.vessels?.mean_vessel_width_px?.toFixed(1)} px</div></div>
          </div>
        </div>

        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-semibold"><HeartPulse className="h-5 w-5 text-rose-600" /> Heart-disease risk (Random Forest)</h2>
            {s.heart && !editing && <button className="text-sm text-teal-700 hover:underline" onClick={() => setEditing(true)}>Edit clinical data</button>}
          </div>
          {s.heart && !editing ? (
            <>
              <div>
                <div className="mb-1 flex items-baseline justify-between">
                  <span className="text-lg font-bold">Heart-disease risk</span>
                  <span className="text-2xl font-bold">{pct(s.heart.probability)}</span>
                </div>
                <ProbBar value={s.heart.probability} />
              </div>
              <div>
                <div className="mb-2 text-sm font-medium">Top factors (SHAP)</div>
                <div className="space-y-2">
                  {(() => {
                    const max = Math.max(...s.heart.factors.map((f) => Math.abs(f.impact)), 1e-6)
                    return s.heart.factors.map((f) => (
                      <div key={f.feature} className="text-sm">
                        <div className="flex justify-between"><span>{f.label} <span className="text-slate-400">= {f.display ?? f.value}</span></span>
                          <span className={f.impact > 0 ? 'text-red-600' : 'text-green-700'}>{f.impact > 0 ? '+' : ''}{f.impact.toFixed(3)}</span></div>
                        <div className="h-2 rounded bg-slate-100">
                          <div className={`h-2 rounded ${f.impact > 0 ? 'bg-red-400' : 'bg-green-500'}`} style={{ width: `${(Math.abs(f.impact) / max) * 100}%` }} />
                        </div>
                      </div>
                    ))
                  })()}
                </div>
                <p className="mt-2 text-xs text-slate-500">Red raises risk, green lowers it (SHAP contribution to the predicted probability).</p>
              </div>
            </>
          ) : (
            <form onSubmit={saveClinical} className="space-y-4">
              <p className="text-sm text-slate-500">Enter the clinical parameters to get the heart-disease risk and the combined stage.</p>
              <ClinicalForm value={clinical} onChange={setClinical} disabled={saving} />
              <ErrorBox error={formError} />
              <div className="flex gap-2">
                <button className="btn-primary" disabled={saving}>{saving && <Loader2 className="h-4 w-4 animate-spin" />} Score risk</button>
                {editing && <button type="button" className="btn-secondary" onClick={() => setEditing(false)}>Cancel</button>}
              </div>
            </form>
          )}
        </div>
      </div>
      <Disclaimer />
    </div>
  )
}
