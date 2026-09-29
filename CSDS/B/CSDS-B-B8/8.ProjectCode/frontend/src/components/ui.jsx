import { AlertCircle, Loader2 } from 'lucide-react'
import { ACTIVITY_COLORS, label } from '../api.js'

export function Spinner({ text = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-sm py-6 justify-center">
      <Loader2 className="w-4 h-4 animate-spin" /> {text}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
      <span className="flex-1">{error}</span>
      {onRetry && <button className="underline" onClick={onRetry}>Retry</button>}
    </div>
  )
}

export function PageTitle({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
      </div>
      <div className="flex gap-2">{children}</div>
    </div>
  )
}

export function ActivityBadge({ activity }) {
  const c = ACTIVITY_COLORS[activity] || '#64748b'
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium capitalize"
      style={{ background: c + '22', color: c }}>
      <span className="w-2 h-2 rounded-full" style={{ background: c }} />
      {label(activity)}
    </span>
  )
}

const STATUS = {
  pending: 'bg-amber-100 text-amber-800',
  sending: 'bg-sky-100 text-sky-800',
  sent: 'bg-red-100 text-red-800',
  undelivered: 'bg-slate-200 text-slate-700',
  cancelled: 'bg-green-100 text-green-800',
}

export function StatusBadge({ status }) {
  const text = status === 'cancelled' ? "I'm OK - cancelled" : status
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS[status] || ''}`}>{text}</span>
}

export function Stat({ label: l, value, hint }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{l}</div>
      <div className="text-2xl font-semibold text-slate-900 mt-1">{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  )
}
