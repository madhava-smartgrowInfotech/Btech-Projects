import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Dices, Loader2, Upload } from 'lucide-react'
import api, { errMsg } from '../api'

export function Spinner({ label = 'Working...' }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </span>
  )
}

export function ErrorBox({ error }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /> <span>{error}</span>
    </div>
  )
}

export function Stat({ label, value, sub, good }) {
  const tone = good === undefined ? 'text-slate-900' : good ? 'text-emerald-600' : 'text-rose-600'
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${tone}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
    </div>
  )
}

export function Figure({ src, caption, pixel = true }) {
  if (!src) return null
  return (
    <figure className="flex flex-col items-center">
      <img src={src} alt={caption} className={`w-full rounded-lg border border-slate-200 bg-slate-100 object-contain ${pixel ? 'pixel' : ''}`} />
      <figcaption className="mt-1 text-xs text-slate-500">{caption}</figcaption>
    </figure>
  )
}

export const fmt = (v, d = 4) => (v === 'inf' ? '∞' : typeof v === 'number' ? v.toFixed(d) : v ?? '-')

/** Pick a committed sample image or upload one. value = {kind, name} | {file} */
export function SourcePicker({ value, onChange }) {
  const [samples, setSamples] = useState([])
  const [err, setErr] = useState('')
  useEffect(() => {
    api.get('/samples').then((r) => {
      setSamples(r.data)
      if (!value && r.data.length) onChange({ kind: r.data[0].kind, name: r.data[0].name })
    }).catch((e) => setErr(errMsg(e)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const selected = value?.kind ? `${value.kind}/${value.name}` : ''
  const preview = useMemo(() => (value?.file ? URL.createObjectURL(value.file) : null), [value?.file])
  return (
    <div className="space-y-2">
      <label className="label">Image</label>
      <select className="input" value={selected} onChange={(e) => {
        const [kind, ...rest] = e.target.value.split('/')
        onChange({ kind, name: rest.join('/') })
      }}>
        {value?.file && <option value="">Uploaded: {value.file.name}</option>}
        <optgroup label="Drone imagery (VisDrone sample)">
          {samples.filter((s) => s.kind === 'visdrone').map((s) => <option key={s.name} value={`visdrone/${s.name}`}>{s.name}</option>)}
        </optgroup>
        <optgroup label="Standard test images (USC-SIPI)">
          {samples.filter((s) => s.kind === 'sipi').map((s) => <option key={s.name} value={`sipi/${s.name}`}>{s.name}</option>)}
        </optgroup>
      </select>
      <label className="btn-secondary w-full cursor-pointer">
        <Upload className="h-4 w-4" /> Upload your own image
        <input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files[0] && onChange({ file: e.target.files[0] })} />
      </label>
      {value?.kind && (
        <img src={`/api/samples/file/${value.kind}/${encodeURIComponent(value.name)}`} alt="" className="h-32 w-full rounded-lg border object-cover" />
      )}
      {preview && <img src={preview} alt="" className="h-32 w-full rounded-lg border object-cover" />}
      <ErrorBox error={err} />
    </div>
  )
}

export function KeyInput({ value, onChange, label = '256-bit key (hex)', allowEmpty = false }) {
  const [busy, setBusy] = useState(false)
  const gen = async () => {
    setBusy(true)
    try { onChange((await api.get('/keys/new')).data.key) } finally { setBusy(false) }
  }
  const bad = value && !/^[0-9a-fA-F]{64}$/.test(value)
  return (
    <div>
      <label className="label">{label}</label>
      <div className="flex gap-2">
        <input className={`input font-mono text-xs ${bad ? 'border-rose-400' : ''}`} value={value}
          placeholder={allowEmpty ? 'leave empty to generate a random key' : '64 hex characters'}
          onChange={(e) => onChange(e.target.value.trim())} />
        <button type="button" className="btn-secondary px-3" onClick={gen} disabled={busy} title="Generate a random key">
          <Dices className="h-4 w-4" />
        </button>
      </div>
      {bad && <p className="mt-1 text-xs text-rose-600">Key must be exactly 64 hexadecimal characters.</p>}
    </div>
  )
}

const COLORS = { r: '#ef4444', g: '#22c55e', b: '#3b82f6', gray: '#475569' }

/** 256-bin histogram drawn as SVG polylines, one per channel. */
export function Histogram({ data, title }) {
  if (!data) return null
  const chans = Object.keys(data)
  const max = Math.max(...chans.flatMap((c) => data[c]))
  const W = 256, H = 100
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-slate-600">{title}</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-28 w-full rounded border border-slate-200 bg-white" preserveAspectRatio="none">
        {chans.map((c) => (
          <polyline key={c} fill="none" stroke={COLORS[c]} strokeWidth="1" strokeOpacity="0.8"
            points={data[c].map((v, i) => `${i},${H - (v / max) * (H - 4)}`).join(' ')} />
        ))}
      </svg>
    </div>
  )
}

/** Adjacent-pixel scatter plot (x = pixel, y = neighbour). */
export function Scatter({ points, title }) {
  if (!points) return null
  return (
    <div>
      <div className="mb-1 text-xs font-medium text-slate-600">{title}</div>
      <svg viewBox="0 0 256 256" className="aspect-square w-full rounded border border-slate-200 bg-white">
        {points.map(([x, y], i) => <circle key={i} cx={x} cy={255 - y} r="1.4" fill="#0284c7" fillOpacity="0.6" />)}
      </svg>
    </div>
  )
}

export function Bars({ rows, valueKey, label, unit }) {
  const max = Math.max(...rows.map((r) => r[valueKey]))
  return (
    <div>
      <div className="mb-2 text-sm font-medium text-slate-700">{label}</div>
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.algorithm} className="flex items-center gap-2 text-sm">
            <div className="w-28 shrink-0 text-slate-600">{r.algorithm}</div>
            <div className="h-5 flex-1 rounded bg-slate-100">
              <div className={`h-5 rounded ${r.algorithm === 'SkyCipher' ? 'bg-sky-500' : 'bg-slate-400'}`}
                style={{ width: `${Math.max(1, (r[valueKey] / max) * 100)}%` }} />
            </div>
            <div className="w-24 shrink-0 text-right font-mono text-xs">{r[valueKey].toFixed(2)} {unit}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
