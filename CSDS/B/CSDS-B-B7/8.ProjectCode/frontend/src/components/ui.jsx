import { AlertTriangle, Loader2 } from 'lucide-react'

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
      </div>
      {children && <div className="flex flex-wrap gap-2 items-center">{children}</div>}
    </div>
  )
}

export function Loading({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-sm py-10 justify-center">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  )
}

export function ErrorBox({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 mb-4">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <div className="flex-1">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="underline font-medium cursor-pointer">
          Retry
        </button>
      )}
    </div>
  )
}

export function Kpi({ label, value, sub, tone = 'slate', icon: Icon }) {
  const tones = {
    slate: 'text-slate-900',
    red: 'text-red-700',
    amber: 'text-amber-700',
    teal: 'text-teal-700',
  }
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between text-xs font-medium text-slate-500 uppercase tracking-wide">
        {label} {Icon && <Icon size={16} className="text-slate-400" />}
      </div>
      <div className={`text-2xl font-semibold mt-2 ${tones[tone]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

export function Badge({ children, tone = 'slate' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700',
    red: 'bg-red-100 text-red-800',
    amber: 'bg-amber-100 text-amber-800',
    teal: 'bg-teal-100 text-teal-800',
    blue: 'bg-sky-100 text-sky-800',
  }
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>
}

export const pct = (x, d = 0) => `${(x * 100).toFixed(d)}%`

export function AlertList({ alerts, empty = 'No capacity warnings in the forecast window.' }) {
  if (!alerts?.length) return <p className="text-sm text-slate-500">{empty}</p>
  return (
    <ul className="space-y-2">
      {alerts.map((a, i) => (
        <li
          key={i}
          className={`flex gap-2 rounded-lg p-2.5 text-sm ${
            a.level === 'critical' ? 'bg-red-50 text-red-900' : 'bg-amber-50 text-amber-900'
          }`}
        >
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>
            <strong className="uppercase text-xs mr-1">{a.level === 'critical' ? 'Over capacity' : 'Early warning'}</strong>
            {a.message}
          </span>
        </li>
      ))}
    </ul>
  )
}
