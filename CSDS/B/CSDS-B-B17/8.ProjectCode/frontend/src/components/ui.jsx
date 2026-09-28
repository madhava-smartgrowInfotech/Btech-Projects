import { AlertTriangle, Loader2 } from 'lucide-react'

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
      <div className="flex-1 break-words">{error}</div>
      {onRetry && (
        <button className="font-medium underline" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export const EMOTION_COLOR = {
  angry: '#dc2626',
  frustrated: '#f97316',
  concerned: '#eab308',
  neutral: '#94a3b8',
  satisfied: '#22c55e',
  relieved: '#0d9488',
}

export function EmotionBadge({ emotion }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-white"
      style={{ background: EMOTION_COLOR[emotion] || '#64748b' }}
    >
      {emotion}
    </span>
  )
}

export function StatusBadge({ status, stage }) {
  const style = {
    done: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    processing: 'bg-indigo-100 text-indigo-800',
    queued: 'bg-slate-100 text-slate-700',
  }[status]
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>
      {(status === 'processing' || status === 'queued') && <Loader2 className="h-3 w-3 animate-spin" />}
      {status === 'processing' && stage ? stage : status}
    </span>
  )
}

export function SampleBadge() {
  return (
    <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-800">
      Sample
    </span>
  )
}

export function ScorePill({ score }) {
  if (score == null) return <span className="text-slate-400">-</span>
  const c = score >= 80 ? 'bg-green-100 text-green-800' : score >= 60 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${c}`}>{Math.round(score)}</span>
}

export function SentimentValue({ value }) {
  if (value == null) return <span className="text-slate-400">-</span>
  const c = value >= 0.15 ? 'text-green-700' : value <= -0.15 ? 'text-red-700' : 'text-slate-600'
  return <span className={`font-medium ${c}`}>{value > 0 ? '+' : ''}{value.toFixed(2)}</span>
}

export function Stat({ label, value, sub }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value ?? '-'}</div>
      {sub && <div className="text-xs text-slate-500">{sub}</div>}
    </div>
  )
}

export function Empty({ children }) {
  return <div className="rounded-lg border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">{children}</div>
}
