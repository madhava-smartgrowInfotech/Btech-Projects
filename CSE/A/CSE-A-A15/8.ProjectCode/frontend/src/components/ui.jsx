import { useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { blobUrl } from '../api'

export function Spinner({ text }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" /> {text}
    </span>
  )
}

export function ErrorBox({ children }) {
  if (!children) return null
  return (
    <div role="alert" className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{children}</span>
    </div>
  )
}

export function Notice({ children }) {
  if (!children) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-brand-100 bg-brand-50 p-3 text-sm text-brand-700">
      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{children}</span>
    </div>
  )
}

export function PageHead({ title, sub, icon: Icon }) {
  return (
    <div className="mb-6">
      <h1 className="flex items-center gap-2">
        {Icon && <Icon className="h-6 w-6 text-brand-600" />} {title}
      </h1>
      {sub && <p className="mt-1 max-w-3xl text-sm text-slate-500">{sub}</p>}
    </div>
  )
}

export function Stat({ label, value, hint, tone }) {
  const color = tone === 'good' ? 'text-brand-700' : tone === 'bad' ? 'text-red-600' : 'text-ink-900'
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${color}`}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

export function Badge({ tone = 'gray', children }) {
  const map = {
    good: 'bg-brand-50 text-brand-700 border-brand-100',
    bad: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-slate-100 text-slate-600 border-slate-200',
  }
  return <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${map[tone]}`}>{children}</span>
}

export function HashLine({ label, value, ok }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 break-all rounded-md border px-2 py-1.5 font-mono text-xs ${
        ok === false ? 'border-red-200 bg-red-50' : ok ? 'border-brand-100 bg-brand-50' : 'border-slate-200 bg-slate-50'}`}>
        {value}
      </div>
    </div>
  )
}

/** <img> for endpoints that need the Authorization header. */
export function AuthImage({ path, alt, className = '' }) {
  const [src, setSrc] = useState(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let url
    let live = true
    setSrc(null)
    setFailed(false)
    blobUrl(path)
      .then((u) => {
        url = u
        if (live) setSrc(u)
      })
      .catch(() => live && setFailed(true))
    return () => {
      live = false
      if (url) URL.revokeObjectURL(url)
    }
  }, [path])
  if (failed) return <div className="p-4 text-sm text-red-600">Could not load image.</div>
  if (!src) return <div className="p-4"><Spinner text="Loading image..." /></div>
  return <img src={src} alt={alt} className={className} />
}

export function Timings({ items }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {items.map(([k, v]) => (
        <Stat key={k} label={k} value={v} />
      ))}
    </div>
  )
}
