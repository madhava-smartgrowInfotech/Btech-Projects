import { AlertTriangle, Loader2 } from 'lucide-react'

export function Spinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500 py-6 justify-center">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
      <div className="flex-1">{error}</div>
      {onRetry && (
        <button className="underline font-medium" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export const SEVERITY_STYLE = {
  mild: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  moderate: 'bg-amber-100 text-amber-800 border-amber-200',
  severe: 'bg-orange-100 text-orange-800 border-orange-300',
  critical: 'bg-red-100 text-red-800 border-red-300',
}
export const SEVERITY_COLOR = { mild: '#10b981', moderate: '#f59e0b', severe: '#f97316', critical: '#dc2626' }

export function SeverityBadge({ level, large }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border font-semibold capitalize ${SEVERITY_STYLE[level] || 'bg-slate-100'} ${
        large ? 'px-4 py-1 text-lg' : 'px-2 py-0.5 text-xs'
      }`}
    >
      {level}
    </span>
  )
}

export function Stat({ label, value, sub, icon: Icon, tone = 'text-slate-900' }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
        {Icon && <Icon className="h-4 w-4 text-slate-400" />}
      </div>
      <div className={`mt-1 text-2xl font-bold ${tone}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  )
}

export function StatusPill({ status }) {
  const style = {
    waiting: 'bg-sky-100 text-sky-800',
    called: 'bg-teal-600 text-white',
    done: 'bg-slate-200 text-slate-700',
    no_show: 'bg-rose-100 text-rose-700',
    referred: 'bg-violet-100 text-violet-800',
    pending_consent: 'bg-amber-100 text-amber-800',
    sent: 'bg-sky-100 text-sky-800',
    accepted: 'bg-teal-100 text-teal-800',
    completed: 'bg-emerald-100 text-emerald-800',
    declined: 'bg-rose-100 text-rose-700',
  }[status]
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${style || 'bg-slate-100'}`}>
      {status.replace('_', ' ')}
    </span>
  )
}

export function Disclaimer({ text }) {
  return (
    <p className="text-xs text-slate-500 border-l-2 border-slate-300 pl-2">
      {text ||
        'Decision support only - this is not a diagnosis. A qualified clinician confirms severity at the hospital. In an emergency call 108.'}
    </p>
  )
}

export function SeverityBar({ mix, height = 'h-3' }) {
  const levels = ['critical', 'severe', 'moderate', 'mild']
  const total = levels.reduce((s, l) => s + (mix[l] || 0), 0) || 1
  return (
    <div className={`flex w-full ${height} rounded-full overflow-hidden bg-slate-100 my-2`}>
      {levels.map((l) =>
        mix[l] ? <div key={l} title={`${l}: ${mix[l]}`} style={{ width: `${(100 * mix[l]) / total}%`, background: SEVERITY_COLOR[l] }} /> : null,
      )}
    </div>
  )
}
