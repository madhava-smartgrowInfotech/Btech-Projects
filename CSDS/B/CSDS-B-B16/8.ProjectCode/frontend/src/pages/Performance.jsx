import { useEffect, useState } from 'react'
import api, { errorText } from '../api.js'
import { ErrorBox, Spinner } from '../components/ui.jsx'

const TILES = [
  ['accuracy', 'Accuracy'],
  ['sensitivity', 'Sensitivity'],
  ['specificity', 'Specificity'],
  ['f1', 'F1 score'],
  ['roc_auc', 'ROC-AUC'],
]

function Roc({ curve, auc }) {
  const pts = curve.fpr.map((x, i) => `${20 + x * 200},${220 - curve.tpr[i] * 200}`).join(' ')
  return (
    <svg viewBox="0 0 240 250" className="w-full max-w-xs" role="img" aria-label={`ROC curve, AUC ${auc}`}>
      <rect x="20" y="20" width="200" height="200" fill="#f8fafc" stroke="#cbd5e1" />
      {[0.25, 0.5, 0.75].map((g) => (
        <g key={g} stroke="#e2e8f0">
          <line x1={20 + g * 200} y1="20" x2={20 + g * 200} y2="220" />
          <line x1="20" y1={220 - g * 200} x2="220" y2={220 - g * 200} />
        </g>
      ))}
      <line x1="20" y1="220" x2="220" y2="20" stroke="#94a3b8" strokeDasharray="4 4" />
      <polyline points={pts} fill="none" stroke="#0f766e" strokeWidth="2.5" />
      <text x="120" y="240" textAnchor="middle" fontSize="10" fill="#64748b">False positive rate</text>
      <text x="8" y="120" textAnchor="middle" fontSize="10" fill="#64748b" transform="rotate(-90 8 120)">True positive rate</text>
      <text x="210" y="210" textAnchor="end" fontSize="11" fontWeight="600" fill="#0f766e">AUC {auc.toFixed(3)}</text>
    </svg>
  )
}

function Confusion({ cm, labels }) {
  const cell = (v, good) => (
    <div className={`flex aspect-[3/2] flex-col items-center justify-center rounded-lg text-lg font-bold ${good ? 'bg-teal-100 text-teal-900' : 'bg-rose-50 text-rose-800'}`}>{v}</div>
  )
  return (
    <div className="w-full max-w-xs text-xs">
      <div className="mb-1 grid grid-cols-[70px_1fr_1fr] gap-1 text-center text-slate-500">
        <div />
        <div>Pred. {labels[0]}</div>
        <div>Pred. {labels[1]}</div>
      </div>
      <div className="grid grid-cols-[70px_1fr_1fr] items-center gap-1">
        <div className="text-right text-slate-500">True {labels[0]}</div>
        {cell(cm.tn, true)}
        {cell(cm.fp, false)}
        <div className="text-right text-slate-500">True {labels[1]}</div>
        {cell(cm.fn, false)}
        {cell(cm.tp, true)}
      </div>
    </div>
  )
}

function ModelCard({ title, m, labels }) {
  const t = m.test
  return (
    <div className="card space-y-5">
      <div>
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-slate-500">{m.model} - {m.dataset}</p>
        <p className="text-xs text-slate-500">
          Held-out test set: {t.n} cases. Split: {Object.entries(m.split).map(([k, v]) => `${k} ${v}`).join(', ')}. Decision threshold {t.threshold}.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {TILES.map(([k, l]) => (
          <div key={k} className="rounded-lg bg-slate-50 p-3 text-center">
            <div className="text-xs text-slate-500">{l}</div>
            <div className="text-xl font-bold text-slate-900">{(t[k] * 100).toFixed(1)}%</div>
          </div>
        ))}
      </div>
      <div className="grid items-center gap-6 sm:grid-cols-2">
        <div>
          <div className="mb-2 text-sm font-medium">Confusion matrix</div>
          <Confusion cm={t.confusion_matrix} labels={labels} />
        </div>
        <div>
          <div className="mb-2 text-sm font-medium">ROC curve</div>
          <Roc curve={t.roc_curve} auc={t.roc_auc} />
        </div>
      </div>
      {m.notes && <p className="text-xs text-slate-500">{m.notes}</p>}
    </div>
  )
}

export default function Performance() {
  const [m, setM] = useState(null)
  const [error, setError] = useState('')
  const load = () => {
    setError('')
    api.get('/metrics').then(({ data }) => setM(data)).catch((e) => setError(errorText(e)))
  }
  useEffect(load, [])
  if (error) return <ErrorBox error={error} onRetry={load} />
  if (!m) return <Spinner />
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Model performance</h1>
        <p className="text-sm text-slate-500">
          Measured on held-out test data never used for training{m.generated_at ? ` - evaluated ${new Date(m.generated_at).toLocaleString()}` : ''}.
        </p>
      </div>
      {m.retina && <ModelCard title="Hypertensive retinopathy - LeNet on Haar wavelets" m={m.retina} labels={['normal', 'HR']} />}
      {m.heart && <ModelCard title="Heart-disease risk - Random Forest" m={m.heart} labels={['no CAD', 'CAD']} />}
    </div>
  )
}
