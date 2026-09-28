import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react'
import { riskColor } from '../format'

export function Card({ title, action, children, className = '' }) {
  return (
    <section className={`bg-white rounded-xl border border-slate-200 shadow-sm ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between gap-2 px-4 py-3 border-b border-slate-100">
          <h2 className="font-semibold text-slate-800 text-sm">{title}</h2>
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}

export function Stat({ label, value, sub, icon: Icon, tone = 'slate' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700', red: 'bg-red-50 text-red-600', indigo: 'bg-indigo-50 text-indigo-600',
    amber: 'bg-amber-50 text-amber-600', green: 'bg-emerald-50 text-emerald-600',
  }
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex items-start gap-3">
      {Icon && <div className={`p-2 rounded-lg ${tones[tone]}`}><Icon size={18} /></div>}
      <div className="min-w-0">
        <div className="text-xs text-slate-500">{label}</div>
        <div className="text-xl font-semibold text-slate-900 truncate">{value}</div>
        {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
      </div>
    </div>
  )
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-slate-500 text-sm">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
      <div className="flex-1 break-words">{error}</div>
      {onRetry && (
        <button onClick={onRetry} className="flex items-center gap-1 text-red-700 hover:underline shrink-0">
          <RefreshCw size={14} /> Retry
        </button>
      )}
    </div>
  )
}

export function RiskBadge({ risk }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-sm font-semibold" style={{ color: riskColor(risk) }}>
      <span className="w-2 h-2 rounded-full" style={{ background: riskColor(risk) }} />
      {risk.toFixed(2)}
    </span>
  )
}

export function ScoreBar({ value, label }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        <span>{label}</span><span className="font-mono">{value.toFixed(2)}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${Math.max(2, value * 100)}%`, background: riskColor(value) }} />
      </div>
    </div>
  )
}

const PATTERN_STYLE = {
  circular_trading: 'bg-purple-50 text-purple-700 border-purple-200',
  shell_entity: 'bg-red-50 text-red-700 border-red-200',
  fake_invoices: 'bg-orange-50 text-orange-700 border-orange-200',
  itc_spike: 'bg-amber-50 text-amber-800 border-amber-200',
  behaviour_anomaly: 'bg-sky-50 text-sky-700 border-sky-200',
}
export const PATTERN_LABELS = {
  circular_trading: 'Circular trading', shell_entity: 'Shell entity', fake_invoices: 'Fake invoices',
  itc_spike: 'ITC spike', behaviour_anomaly: 'Unusual behaviour',
}

export function PatternTag({ p }) {
  return (
    <span className={`inline-block text-[11px] px-1.5 py-0.5 rounded border whitespace-nowrap ${PATTERN_STYLE[p] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
      {PATTERN_LABELS[p] || p}
    </span>
  )
}

export function Button({ children, variant = 'primary', className = '', ...props }) {
  const v = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300',
    secondary: 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 disabled:text-slate-400',
  }
  return (
    <button className={`inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${v[variant]} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Severity({ s }) {
  const c = { high: 'bg-red-100 text-red-700', medium: 'bg-amber-100 text-amber-800', low: 'bg-slate-100 text-slate-600' }
  return <span className={`text-[11px] px-1.5 py-0.5 rounded font-medium uppercase ${c[s]}`}>{s}</span>
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}
