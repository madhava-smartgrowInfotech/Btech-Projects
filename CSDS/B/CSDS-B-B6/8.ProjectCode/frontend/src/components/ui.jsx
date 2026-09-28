import { useCallback, useEffect, useState } from 'react'
import { AlertCircle, Loader2 } from 'lucide-react'
import { errMsg } from '../api'

export function Card({ title, icon: Icon, actions, children, className = '' }) {
  return (
    <section className={`bg-white rounded-xl border border-slate-200 shadow-sm ${className}`}>
      {(title || actions) && (
        <header className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-slate-100">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2">
            {Icon && <Icon className="w-4 h-4 text-teal-600" />} {title}
          </h2>
          <div className="flex flex-wrap gap-2">{actions}</div>
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}

const VARIANTS = {
  primary: 'bg-teal-600 hover:bg-teal-700 text-white',
  secondary: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300',
  danger: 'bg-rose-600 hover:bg-rose-700 text-white',
  ghost: 'text-teal-700 hover:bg-teal-50',
}

export function Button({ variant = 'primary', loading, children, className = '', ...props }) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  )
}

export function Spinner({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-sm py-6 justify-center">
      <Loader2 className="w-4 h-4 animate-spin" /> {label}
    </div>
  )
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="flex-1">{typeof error === 'string' ? error : errMsg(error)}</div>
      {onRetry && <button className="underline" onClick={onRetry}>Retry</button>}
    </div>
  )
}

const BADGE = {
  slate: 'bg-slate-100 text-slate-700', teal: 'bg-teal-100 text-teal-800', blue: 'bg-sky-100 text-sky-800',
  amber: 'bg-amber-100 text-amber-800', rose: 'bg-rose-100 text-rose-800', violet: 'bg-violet-100 text-violet-800',
  green: 'bg-emerald-100 text-emerald-800',
}

export function Badge({ color = 'slate', children }) {
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${BADGE[color]}`}>{children}</span>
}

export const CATEGORY_COLOR = { encounters: 'blue', conditions: 'amber', medications: 'violet', labs: 'teal', allergies: 'rose' }
export const HOSPITAL_COLOR = { A: 'blue', B: 'green', C: 'violet' }

export function Input({ label, className = '', ...props }) {
  return (
    <label className={`block text-sm ${className}`}>
      {label && <span className="block mb-1 font-medium text-slate-700">{label}</span>}
      <input {...props} className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500" />
    </label>
  )
}

export function Select({ label, children, className = '', ...props }) {
  return (
    <label className={`block text-sm ${className}`}>
      {label && <span className="block mb-1 font-medium text-slate-700">{label}</span>}
      <select {...props} className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500">
        {children}
      </select>
    </label>
  )
}

/** Run an async loader with loading and error state. */
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      setState({ data: await fn(), loading: false, error: null })
    } catch (e) {
      setState({ data: null, loading: false, error: e })
    }
  }, deps)
  useEffect(() => { run() }, [run])
  return { ...state, reload: run, setData: (data) => setState((s) => ({ ...s, data })) }
}

export function fmtDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function Disclaimer({ children }) {
  return (
    <p className="text-xs text-slate-500 border-t border-slate-100 pt-2 mt-3">
      {children || 'Decision support only - not a diagnosis. Always confirm with a qualified clinician.'}
    </p>
  )
}

/** Minimal markdown renderer for assistant answers (headings, bullets, bold). */
export function RichText({ text }) {
  const bold = (s) => s.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    p.startsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : p)
  return (
    <div className="space-y-1.5 text-sm text-slate-800 leading-relaxed">
      {text.split('\n').map((line, i) => {
        const t = line.trim()
        if (!t) return null
        if (t.startsWith('#')) return <h4 key={i} className="font-semibold text-slate-900 pt-2">{bold(t.replace(/^#+\s*/, ''))}</h4>
        if (/^[-*•]\s+/.test(t)) return <div key={i} className="flex gap-2 pl-2"><span className="text-teal-600">•</span><span>{bold(t.replace(/^[-*•]\s+/, ''))}</span></div>
        return <p key={i}>{bold(t)}</p>
      })}
    </div>
  )
}
