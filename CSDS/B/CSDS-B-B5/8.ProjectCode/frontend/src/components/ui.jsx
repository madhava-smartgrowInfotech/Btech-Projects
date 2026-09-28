import { AlertCircle, Loader2 } from 'lucide-react'

export function Spinner({ label = 'Loading...' }) {
  return <div className="flex items-center gap-2 text-slate-500 text-sm py-6 justify-center"><Loader2 size={16} className="animate-spin" /> {label}</div>
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm px-3 py-2">
      <AlertCircle size={16} className="mt-0.5 shrink-0" />
      <span className="flex-1">{error}</span>
      {onRetry && <button className="underline" onClick={onRetry}>Retry</button>}
    </div>
  )
}

export function ConfidenceBar({ label, value }) {
  const pct = Math.round(value * 100)
  const color = value > 0.7 ? 'bg-emerald-500' : value > 0.4 ? 'bg-amber-500' : 'bg-slate-400'
  return (
    <div className="text-xs">
      <div className="flex justify-between"><span className="font-medium">{label.replaceAll('_', ' ')}</span><span className="text-slate-500">{pct}%</span></div>
      <div className="h-1.5 bg-slate-100 rounded-full mt-1"><div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} /></div>
    </div>
  )
}

export function Stat({ label, value, hint }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-2xl font-semibold text-slate-900 mt-1">{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  )
}
