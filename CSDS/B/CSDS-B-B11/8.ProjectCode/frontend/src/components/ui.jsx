import { AlertTriangle, Loader2, X } from 'lucide-react'

export function Spinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500 py-6 justify-center">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  )
}

export function ErrorBox({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
      <div className="flex-1">{message}</div>
      {onRetry && <button className="underline" onClick={onRetry}>Retry</button>}
    </div>
  )
}

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" onClick={onClose}>
      <div className={`card w-full ${wide ? 'max-w-3xl' : 'max-w-xl'} max-h-[90vh] overflow-y-auto`} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3 sticky top-0 bg-white rounded-t-2xl">
          <h3 className="font-semibold text-slate-800">{title}</h3>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-slate-100" aria-label="Close"><X className="h-5 w-5" /></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

export function ProgressBar({ label, value, target, unit = 'g', cap = false }) {
  const pct = target ? Math.min(100, (value / target) * 100) : 0
  const over = value > target
  const color = cap ? (over ? 'bg-red-500' : 'bg-sky-500') : over && value > target * 1.1 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-600 mb-1">
        <span className="font-medium">{label}</span>
        <span>{Math.round(value)} / {Math.round(target)} {unit}{cap ? ' max' : ''}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function Disclaimer({ text }) {
  return (
    <p className="text-xs text-slate-500 border-t border-slate-200 pt-3 mt-6">
      <strong>Health disclaimer:</strong> {text || 'NutriSense gives general nutrition guidance, not medical advice. If you have a medical condition, are pregnant or take medication, check your plan with a doctor or registered dietitian.'}
    </p>
  )
}

export const label = (s) => (s || '').replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())

export const MEALS = ['breakfast', 'lunch', 'snack', 'dinner']
