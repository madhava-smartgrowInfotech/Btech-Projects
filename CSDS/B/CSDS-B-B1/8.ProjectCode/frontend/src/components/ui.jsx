import { AlertTriangle, ArrowDown, ArrowUp, CheckCircle2, CircleAlert, Clock, Flame, LoaderCircle, Minus, XCircle } from 'lucide-react'

// Status palette (reserved for state, never for series) - always paired with an icon + label
export const STATUS_COLORS = { good: '#0ca30c', warning: '#fab219', serious: '#ec835a', critical: '#d03b3b' }
export const PRIORITY_STYLE = {
  Low: { color: '#94a3b8', icon: ArrowDown },
  Medium: { color: STATUS_COLORS.warning, icon: Minus },
  High: { color: STATUS_COLORS.serious, icon: ArrowUp },
  Critical: { color: STATUS_COLORS.critical, icon: Flame },
}
// Chart colors (validated reference palette)
export const CHART = {
  blue: '#2a78d6',
  red: '#e34948',
  grid: '#e1e0d9',
  axis: '#c3c2b7',
  muted: '#898781',
  seq: ['#b7d3f6', '#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281'],
}

export function Spinner({ className = 'h-4 w-4' }) {
  return <LoaderCircle className={`${className} animate-spin`} aria-hidden="true" />
}

export function Loading({ label = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-slate-500" role="status">
      <Spinner /> {label}
    </div>
  )
}

export function ErrorBox({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
      <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="flex-1">{message}</span>
      {onRetry && (
        <button className="font-medium underline" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function PriorityBadge({ priority }) {
  const s = PRIORITY_STYLE[priority]
  if (!s) return null
  const Icon = s.icon
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs font-semibold text-slate-800">
      <Icon className="h-3.5 w-3.5" style={{ color: s.color }} strokeWidth={2.5} aria-hidden="true" />
      {priority}
    </span>
  )
}

const STATUS_ICON = {
  Submitted: { icon: Clock, color: '#64748b' },
  Assigned: { icon: CheckCircle2, color: CHART.blue },
  'In Progress': { icon: LoaderCircle, color: STATUS_COLORS.warning },
  Resolved: { icon: CheckCircle2, color: STATUS_COLORS.good },
  Rejected: { icon: XCircle, color: '#64748b' },
}

export function StatusBadge({ status }) {
  const s = STATUS_ICON[status] || STATUS_ICON.Submitted
  const Icon = s.icon
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      <Icon className="h-3.5 w-3.5" style={{ color: s.color }} aria-hidden="true" />
      {status}
    </span>
  )
}

export function SampleBadge({ show }) {
  if (!show) return null
  return (
    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500" title="Sample data generated for demonstration">
      Sample
    </span>
  )
}

export function SlaFlag({ risk, breached }) {
  if (!risk && !breached) return null
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-700" title={breached ? 'Open longer than the SLA' : 'Expected time is longer than the SLA'}>
      <AlertTriangle className="h-3.5 w-3.5" style={{ color: breached ? STATUS_COLORS.critical : STATUS_COLORS.serious }} aria-hidden="true" />
      {breached ? 'SLA breached' : 'SLA risk'}
    </span>
  )
}

export function Stat({ label, value, sub }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900">{value ?? '-'}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
    </div>
  )
}

export function Empty({ children }) {
  return <div className="py-12 text-center text-sm text-slate-500">{children}</div>
}

export const fmtDate = (s) =>
  s ? new Date(s).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'
export const fmtDay = (s) => (s ? new Date(s).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : '-')
export const pct = (v) => (v === null || v === undefined ? '-' : `${Math.round(v * 1000) / 10}%`)
export const days = (v) => (v === null || v === undefined ? '-' : v < 1 ? `${Math.round(v * 24)} h` : `${Math.round(v * 10) / 10} d`)

export function timeAgo(s) {
  const d = (Date.now() - new Date(s).getTime()) / 1000
  if (d < 60) return 'just now'
  if (d < 3600) return `${Math.floor(d / 60)} min ago`
  if (d < 86400) return `${Math.floor(d / 3600)} h ago`
  return `${Math.floor(d / 86400)} d ago`
}
