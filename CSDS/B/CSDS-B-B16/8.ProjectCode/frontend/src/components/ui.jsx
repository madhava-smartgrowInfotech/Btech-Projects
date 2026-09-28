import { AlertTriangle, Loader2, ShieldAlert } from 'lucide-react'

export function Spinner({ text = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 py-6 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" /> {text}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">{error}</div>
      {onRetry && (
        <button className="font-medium underline" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export const STAGE_STYLE = {
  Low: 'bg-green-100 text-green-800 border-green-300',
  Moderate: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  High: 'bg-orange-100 text-orange-800 border-orange-300',
  'Very high': 'bg-red-100 text-red-800 border-red-300',
}

export function StageBadge({ stage }) {
  if (!stage) return <span className="text-xs text-slate-400">Pending</span>
  return <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STAGE_STYLE[stage]}`}>{stage}</span>
}

export function ProbBar({ value, threshold }) {
  const v = Math.round((value ?? 0) * 100)
  const color = v >= 75 ? 'bg-red-500' : v >= 50 ? 'bg-orange-500' : v >= 30 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="relative h-3 w-full overflow-hidden rounded-full bg-slate-200">
      <div className={`h-full ${color}`} style={{ width: `${v}%` }} />
      {threshold != null && (
        <div className="absolute top-0 h-full w-0.5 bg-slate-800" style={{ left: `${threshold * 100}%` }} title="Decision threshold" />
      )}
    </div>
  )
}

export function Disclaimer() {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-100 px-4 py-3 text-xs text-slate-600">
      <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
      RetinaGuard is a clinical decision-support aid. Results must be reviewed by a qualified professional and are not a
      final diagnosis.
    </div>
  )
}

export function Figure({ src, caption, className = '' }) {
  return (
    <figure className={className}>
      {src ? (
        <img src={src} alt={caption} className="aspect-square w-full rounded-lg bg-black object-cover" />
      ) : (
        <div className="aspect-square w-full rounded-lg bg-slate-200" />
      )}
      <figcaption className="mt-1 text-center text-xs text-slate-500">{caption}</figcaption>
    </figure>
  )
}
