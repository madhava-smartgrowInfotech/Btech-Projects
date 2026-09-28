import { useState } from 'react'
import { CheckCircle2, FlaskConical, Loader2, XCircle } from 'lucide-react'
import api, { errorText } from '../api'
import useApi from '../useApi'
import { Badge, ErrorBox, Loading, PageHeader, fmt, timeAgo } from '../components/ui.jsx'

const FIELDS = [
  ['ph', 'pH', ''],
  ['Hardness', 'Hardness', 'mg/L'],
  ['Solids', 'Total dissolved solids', 'mg/L'],
  ['Chloramines', 'Chloramines', 'mg/L'],
  ['Sulfate', 'Sulfate', 'mg/L'],
  ['Conductivity', 'Conductivity', 'uS/cm'],
  ['Organic_carbon', 'Organic carbon', 'mg/L'],
  ['Trihalomethanes', 'Trihalomethanes', 'ug/L'],
  ['Turbidity', 'Turbidity', 'NTU'],
]
const MEMBER_LABELS = { random_forest: 'Random Forest', xgboost: 'XGBoost', gradient_boosting: 'Gradient Boosting', decision_tree: 'Decision Tree' }

function ShapBars({ reasons }) {
  const max = Math.max(...reasons.map((r) => Math.abs(r.shap)), 0.001)
  return (
    <div className="space-y-1.5">
      {reasons.map((r) => (
        <div key={r.parameter} className="grid grid-cols-[140px_1fr_60px] items-center gap-2 text-xs">
          <div className="text-slate-600 truncate" title={r.label}>{r.label}</div>
          <div className="relative h-4 bg-slate-100 rounded">
            <div className="absolute top-0 bottom-0 left-1/2 w-px bg-slate-300" />
            <div
              className={`absolute top-0 bottom-0 rounded ${r.shap >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`}
              style={r.shap >= 0 ? { left: '50%', width: `${(r.shap / max) * 50}%` } : { right: '50%', width: `${(-r.shap / max) * 50}%` }}
            />
          </div>
          <div className={`text-right font-mono ${r.shap >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>{r.shap > 0 ? '+' : ''}{r.shap.toFixed(3)}</div>
        </div>
      ))}
      <div className="flex justify-between text-[11px] text-slate-400 pl-[148px] pr-[68px]">
        <span>towards not potable</span>
        <span>towards potable</span>
      </div>
    </div>
  )
}

export default function Quality() {
  const samples = useApi('/quality/samples')
  const history = useApi('/quality/history')
  const [name, setName] = useState('Lab sample')
  const [values, setValues] = useState(Object.fromEntries(FIELDS.map(([k]) => [k, ''])))
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function loadPreset(s) {
    setName(s.name)
    setValues(Object.fromEntries(FIELDS.map(([k]) => [k, String(s.values[k])])))
    setResult(null)
  }

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { sample_name: name || 'Lab sample' }
      for (const [k] of FIELDS) body[k] = values[k] === '' ? null : Number(values[k])
      if (FIELDS.every(([k]) => body[k] == null)) throw new Error('Enter at least one parameter')
      const r = await api.post('/quality/predict', body)
      setResult(r.data)
      history.reload()
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageHeader title="Water-quality check" subtitle="Stacked ensemble (Random Forest, XGBoost, Gradient Boosting, Decision Tree) with SHAP explanations and guideline checks" />
      <div className="grid lg:grid-cols-5 gap-6">
        <form onSubmit={submit} className="card p-5 lg:col-span-2 space-y-4 h-fit">
          <div>
            <div className="label">Load a recorded lab sample</div>
            {samples.loading && <Loading />}
            <ErrorBox error={samples.error} onRetry={samples.reload} />
            <div className="flex flex-wrap gap-2">
              {samples.data?.map((s) => (
                <button type="button" key={s.name} className="btn-secondary !px-3 !py-1.5 text-xs" onClick={() => loadPreset(s)}>
                  {s.name}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label" htmlFor="sname">Sample name</label>
            <input id="sname" className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            {FIELDS.map(([k, label, unit]) => (
              <div key={k}>
                <label className="label" htmlFor={k}>
                  {label} {unit && <span className="text-slate-400">({unit})</span>}
                </label>
                <input id={k} className="input" type="number" step="any" value={values[k]} placeholder="not measured"
                  onChange={(e) => setValues({ ...values, [k]: e.target.value })} />
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500">Leave a field empty if it was not measured - the model imputes it from the training median.</p>
          <ErrorBox error={error} />
          <button className="btn-primary w-full" disabled={busy}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />} Check potability
          </button>
        </form>

        <div className="lg:col-span-3 space-y-6">
          {busy && <div className="card p-5"><Loading text="Running the ensemble and SHAP explanation..." /></div>}
          {!busy && !result && (
            <div className="card p-8 text-center text-sm text-slate-500">Enter a lab sample or load a recorded one, then run the check.</div>
          )}
          {result && !busy && (
            <>
              <div className={`card p-5 border-l-4 ${result.potable ? 'border-l-emerald-500' : 'border-l-rose-500'}`}>
                <div className="flex items-center gap-4">
                  {result.potable ? <CheckCircle2 className="w-10 h-10 text-emerald-600" /> : <XCircle className="w-10 h-10 text-rose-600" />}
                  <div>
                    <div className="text-2xl font-semibold text-slate-900">
                      {result.label}, {Math.round(result.confidence * 100)}%
                    </div>
                    <div className="text-sm text-slate-500">
                      Ensemble probability of potable water: {(result.probability_potable * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
                  {Object.entries(result.members).map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-slate-50 p-2">
                      <div className="text-[11px] text-slate-500">{MEMBER_LABELS[k]}</div>
                      <div className="text-sm font-medium text-slate-800">{(v * 100).toFixed(0)}% potable</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card p-5">
                <h2 className="font-semibold text-slate-800">Why - SHAP contribution of each parameter</h2>
                <p className="text-xs text-slate-500 mb-3">Exact Shapley values over the whole ensemble; baseline potable probability {(result.base_value * 100).toFixed(1)}%.</p>
                <ShapBars reasons={result.reasons} />
              </div>
              <div className="card overflow-x-auto">
                <div className="p-4 pb-2 font-semibold text-slate-800">Guideline limits</div>
                <table className="w-full">
                  <thead><tr><th className="th">Parameter</th><th className="th">Value</th><th className="th">Limit</th><th className="th">Source</th><th className="th">Status</th></tr></thead>
                  <tbody>
                    {result.limits.map((l) => (
                      <tr key={l.parameter}>
                        <td className="td">{l.label}</td>
                        <td className="td font-mono">{l.value == null ? '-' : fmt(l.value, 2)} {l.unit}</td>
                        <td className="td">{l.limit} {l.unit}</td>
                        <td className="td text-xs text-slate-500">{l.source}</td>
                        <td className="td">
                          <Badge tone={l.status === 'ok' ? 'emerald' : l.status === 'exceeds' ? 'rose' : 'slate'}>
                            {l.status === 'exceeds' ? 'outside limit' : l.status === 'ok' ? 'within limit' : 'not measured'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          <div className="card overflow-x-auto">
            <div className="p-4 pb-2 font-semibold text-slate-800">Recent checks</div>
            <ErrorBox error={history.error} onRetry={history.reload} />
            {history.loading && !history.data && <Loading />}
            {history.data?.length === 0 && <div className="px-4 pb-4 text-sm text-slate-500">No checks yet.</div>}
            {history.data?.length > 0 && (
              <table className="w-full">
                <thead><tr><th className="th">Sample</th><th className="th">Result</th><th className="th">Limits exceeded</th><th className="th">When</th></tr></thead>
                <tbody>
                  {history.data.map((h) => (
                    <tr key={h.id}>
                      <td className="td">{h.sample_name}</td>
                      <td className="td"><Badge tone={h.potable ? 'emerald' : 'rose'}>{h.potable ? 'Potable' : 'Not potable'} {Math.round(h.confidence * 100)}%</Badge></td>
                      <td className="td">{h.exceeded}</td>
                      <td className="td text-xs text-slate-500">{timeAgo(h.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
