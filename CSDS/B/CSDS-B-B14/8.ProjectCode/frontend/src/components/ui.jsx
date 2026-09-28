import { AlertTriangle, Loader2 } from 'lucide-react'

export function Loading({ text = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-sm py-8 justify-center">
      <Loader2 className="w-4 h-4 animate-spin" /> {text}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="flex-1">{error}</div>
      {onRetry && (
        <button className="underline font-medium" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  )
}

const TONES = {
  sky: 'bg-sky-50 text-sky-600',
  rose: 'bg-rose-50 text-rose-600',
  amber: 'bg-amber-50 text-amber-600',
  emerald: 'bg-emerald-50 text-emerald-600',
  violet: 'bg-violet-50 text-violet-600',
}

export function Kpi({ icon: Icon, label, value, unit, hint, tone = 'sky' }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className={`rounded-lg p-2 ${TONES[tone]}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      </div>
      <div className="mt-3 text-2xl font-semibold text-slate-900">
        {value ?? '-'}
        {unit && <span className="text-sm font-normal text-slate-500 ml-1">{unit}</span>}
      </div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  )
}

const BADGE = {
  slate: 'bg-slate-100 text-slate-700',
  rose: 'bg-rose-100 text-rose-700',
  amber: 'bg-amber-100 text-amber-800',
  emerald: 'bg-emerald-100 text-emerald-700',
  sky: 'bg-sky-100 text-sky-700',
  violet: 'bg-violet-100 text-violet-700',
}

export function Badge({ children, tone = 'slate' }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ${BADGE[tone]}`}>{children}</span>
}

export const ZONE_COLORS = { Z1: '#0284c7', Z2: '#7c3aed', Z3: '#d97706', Z4: '#059669', Z5: '#db2777', SRC: '#475569' }

export function pressureColor(p) {
  if (p == null) return '#94a3b8'
  if (p < 20) return '#e11d48'
  if (p < 28) return '#f59e0b'
  if (p < 45) return '#10b981'
  return '#0284c7'
}

export function fmt(n, d = 0) {
  if (n == null || Number.isNaN(n)) return '-'
  return Number(n).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d })
}

export function severityTone(s) {
  return s === 'high' ? 'rose' : s === 'medium' ? 'amber' : 'slate'
}

export function dayLabel(iso) {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })
}

export function timeAgo(iso) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)} min ago`
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`
  return new Date(iso).toLocaleDateString('en-IN')
}
