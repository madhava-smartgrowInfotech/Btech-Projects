import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, Loader2 } from 'lucide-react'
import api, { errMsg } from '../api'

export function useFetch(url, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(!!url)
  const [error, setError] = useState('')
  const load = useCallback(
    async (quiet = false) => {
      if (!url) return
      if (!quiet) setLoading(true)
      try {
        const r = await api.get(url)
        setData(r.data)
        setError('')
      } catch (e) {
        setError(errMsg(e))
      } finally {
        setLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [url, ...deps],
  )
  useEffect(() => {
    load()
  }, [load])
  return { data, setData, loading, error, reload: load }
}

export function useAction() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const run = async (fn) => {
    setBusy(true)
    setError('')
    try {
      return await fn()
    } catch (e) {
      setError(errMsg(e))
      return undefined
    } finally {
      setBusy(false)
    }
  }
  return { busy, error, setError, run }
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
    <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm px-4 py-3 flex items-start gap-2">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <div className="flex-1 whitespace-pre-wrap">{error}</div>
      {onRetry && (
        <button className="underline font-medium" onClick={() => onRetry()}>
          Retry
        </button>
      )}
    </div>
  )
}

export function Loadable({ loading, error, onRetry, children }) {
  if (loading) return <Spinner />
  if (error) return <ErrorBox error={error} onRetry={onRetry} />
  return children
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="text-slate-500 text-sm mt-1">{subtitle}</p>}
      </div>
      <div className="flex gap-2 flex-wrap">{children}</div>
    </div>
  )
}

export function Stat({ label, value, hint, icon: Icon, tone = 'indigo' }) {
  const tones = {
    indigo: 'bg-indigo-50 text-indigo-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
    sky: 'bg-sky-50 text-sky-600',
    slate: 'bg-slate-100 text-slate-600',
  }
  return (
    <div className="card p-4 flex items-center gap-3">
      {Icon && (
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${tones[tone]}`}>
          <Icon className="w-5 h-5" />
        </div>
      )}
      <div className="min-w-0">
        <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{label}</div>
        <div className="text-xl font-bold text-slate-900">{value}</div>
        {hint && <div className="text-xs text-slate-400 truncate">{hint}</div>}
      </div>
    </div>
  )
}

export function Bar({ value, max = 100, tone = 'bg-indigo-500', label, right }) {
  const pct = Math.max(0, Math.min(100, (100 * (value || 0)) / (max || 1)))
  return (
    <div>
      {(label || right !== undefined) && (
        <div className="flex justify-between text-xs text-slate-600 mb-1">
          <span className="truncate pr-2">{label}</span>
          <span className="font-semibold">{right !== undefined ? right : value}</span>
        </div>
      )}
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

const VERDICT_TONE = {
  Accepted: 'bg-emerald-100 text-emerald-700',
  'Wrong Answer': 'bg-rose-100 text-rose-700',
  'Time Limit Exceeded': 'bg-amber-100 text-amber-700',
  'Runtime Error': 'bg-purple-100 text-purple-700',
  'Compile Error': 'bg-slate-200 text-slate-700',
}

export function Verdict({ v }) {
  return <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${VERDICT_TONE[v] || 'bg-slate-100'}`}>{v}</span>
}

export function Badge({ children, tone = 'slate' }) {
  const t = {
    slate: 'bg-slate-100 text-slate-700',
    indigo: 'bg-indigo-100 text-indigo-700',
    emerald: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-800',
    rose: 'bg-rose-100 text-rose-700',
    sky: 'bg-sky-100 text-sky-700',
  }
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${t[tone]}`}>{children}</span>
}

export function DiffBadge({ d }) {
  return <Badge tone={d === 'Easy' ? 'emerald' : d === 'Medium' ? 'amber' : 'rose'}>{d}</Badge>
}

export function SampleTag({ show }) {
  if (!show) return null
  return <Badge tone="amber">sample data</Badge>
}

export function Empty({ children }) {
  return <div className="text-center text-sm text-slate-400 py-8">{children}</div>
}

export const fmtDate = (s) => (s ? new Date(s.endsWith('Z') ? s : s + 'Z').toLocaleString() : '')
